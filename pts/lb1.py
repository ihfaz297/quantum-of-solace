"""The LB = 1 slice of a heavy-hex patch, decided by SAT.

A permutation pi has LB(pi) = max_v d(v, pi(v)) = 1 exactly when every
non-trivial cycle of pi is a cycle of the graph traversed in one direction:
a 2-cycle is an edge transposition, a k-cycle (k >= 3) is a simple graph
cycle rotated by one step.  So the LB = 1 permutations are the vertex-disjoint
systems of oriented graph cycles and edges.  On a heavy-hex patch every graph
cycle has length >= 12 (girth 12), so any LB = 1 permutation that contains a
cycle costs OPT >= 11 by the girth law (winding.girth_law_bound), and any
permutation of edges alone costs exactly 1.

RQ1 on the LB = 1 slice therefore asks: does some cycle system cost >= 12?

Counting naively, the 2 x 2 patch has 14 simple cycles, 15 disjoint cycle
systems and 345,564 LB = 1 permutations once the leftover edge transpositions
are included -- days of SAT calls.  Two facts collapse this to a few dozen:

  (I)  OPT(pi) = OPT(pi^-1): reverse the schedule.  Reversing a cycle's
       orientation inverts the permutation, so orientation is irrelevant for a
       single cycle.
  (L)  Locality.  Let C be a cycle of a plane graph and R = C together with
       the vertices inside C.  Every neighbour of an interior vertex lies in R.
       If the rotation of C, composed with any LB = 1 permutation of the
       INSIDE of R, has a schedule of T rounds using only edges of G[R], then
       composing it further with any matching M of edges outside R (the only
       other edges vertex-disjoint from C) costs at most max(T, 1): merge M
       into the first round -- it is vertex-disjoint from everything the
       schedule touches.  Likewise two cycles with disjoint regions schedule
       in parallel.  Two vertex-disjoint cycles of a plane graph are either
       nested or have disjoint closed regions, so a cycle system splits into
       its outermost cycles, and what a SAT instance must range over is one
       outermost cycle C together with EVERY LB = 1 permutation of G[interior
       of C] (nested cycles in either orientation, plus a matching).

So the whole LB = 1 slice is decided by one SAT call per (outermost cycle,
LB = 1 permutation of its interior), each run on the induced subgraph G[R],
each answered with a replayed schedule.  Every cycle of a 2-connected plane
graph is the boundary of a union of faces, which is how the cycles and their
interiors are enumerated here (checked against a brute-force DFS count).

The per-cycle instance count is the number of LB = 1 permutations of the
interior: 34 in all on the 2 x 2 patch, 464 on 3 x 2, 6,687 on 4 x 2 and
about 90,000 on each of 3 x 3 and 5 x 2.  Nothing prunes it -- an 11-round
schedule for a large cycle needs every interior vertex (dropping any one makes
the 44-cycle of the 4 x 2 patch UNSAT) -- so the instances of one cycle are
solved by ONE incremental CaDiCaL instance: the interior permutation is a set
of selector variables fixed by assumptions per call, and learned clauses carry
over.  Every SAT answer is still replayed against the concrete target.

Should a region instance be UNSAT at T on G[R], the same permutation is
re-solved on the whole patch; a SAT answer there would mean the schedule needs
to leave the region and the locality shortcut does not apply to that cycle
(this did not happen on any patch tried).

    python -m pts.lb1                       # the 2 x 2 patch (n = 35) at T = 11
    python -m pts.lb1 7 2                   # the 3 x 2 patch (n = 49)
    python -m pts.lb1 7 3 11 --log=results/lb1_7_3.jsonl          # resumable
    python -m pts.lb1 7 3 11 --shard=2/6 --log=results/lb1_7_3.s2of6.jsonl
    # shards: cycles with index % 6 == 2; concatenate the shard logs into
    # results/lb1_7_3.jsonl and rerun without --shard for the full verdict
"""

import json
import os
import sys
import time
from collections import Counter, defaultdict
from itertools import combinations

from pysat.solvers import Solver

from .heavyhex import HeavyHex
from .sat import (Encoding, brick_faces, check, lower_bound, replay,
                  rotation_target, two_core, union_boundary)
from .winding import bound as winding_bound


# --- cycles and their interiors ---------------------------------------------

def face_union_cycles(g):
    """Every simple cycle of the 2-core of X, with the vertices it encloses,
    as (vertices, index, edges, [ {cycle, interior, faces} ])."""
    verts, idx, edges = two_core(g)
    faces = brick_faces(g)
    out = {}
    for k in range(1, len(faces) + 1):
        for sub in combinations(range(len(faces)), k):
            try:
                cyc, interior = union_boundary(g, [faces[i] for i in sub])
            except AssertionError:          # boundary is not a single cycle
                continue
            c = [idx[v] for v in cyc]
            key = frozenset(c)
            if key in out:
                continue
            out[key] = {"cycle": c, "interior": sorted(idx[v] for v in interior),
                        "faces": sub}
    return verts, idx, edges, list(out.values())


def count_simple_cycles(n, edges):
    """Brute-force count of simple cycles (length >= 3), for cross-checking."""
    adj = defaultdict(set)
    for a, b in edges:
        adj[a].add(b)
        adj[b].add(a)
    count = 0

    def dfs(start, v, length, seen):
        nonlocal count
        for w in adj[v]:
            if w == start and length >= 3:
                count += 1
            elif w > start and w not in seen:
                seen.add(w)
                dfs(start, w, length + 1, seen)
                seen.discard(w)

    for s in range(n):
        dfs(s, s, 1, {s})
    return count // 2                       # each cycle found in both directions


def matchings(vs, edges):
    """All matchings, the empty one included, of the subgraph induced on vs.
    Edges come out as (a, b) with a < b."""
    vset = set(vs)
    nb = defaultdict(list)
    for a, b in edges:
        if a in vset and b in vset:
            nb[a].append(b)
            nb[b].append(a)
    out = []

    def rec(rem, chosen):
        if not rem:
            out.append(list(chosen))
            return
        v, rest = rem[0], rem[1:]
        rec(rest, chosen)                       # v unmatched
        for w in nb[v]:
            if w in rest:
                chosen.append((v, w))
                rec([u for u in rest if u != w], chosen)
                chosen.pop()

    rec(sorted(vs), [])
    return out


def inner_systems(interior, cycles, edges):
    """Every LB = 1 permutation of G[interior]: a vertex-disjoint set of the
    cycles lying inside, each in either orientation, plus a matching of the
    vertices left over.  Yields (oriented_cycles, M)."""
    iset = set(interior)
    inner = [c["cycle"] for c in cycles if set(c["cycle"]) <= iset]

    def rec(i, chosen, used):
        yield list(chosen), used
        for j in range(i, len(inner)):
            cj = inner[j]
            if not (set(cj) & used):
                for orient in (cj, cj[::-1]):
                    chosen.append(orient)
                    yield from rec(j + 1, chosen, used | set(cj))
                    chosen.pop()

    for cycs, used in rec(0, [], set()):
        for M in matchings([v for v in interior if v not in used], edges):
            yield cycs, M


# --- one region, many interior permutations ---------------------------------

def region_instance(edges, cycle, interior, M, inner=()):
    """The permutation 'rotate cycle, rotate each inner cycle as oriented,
    transpose the edges of M' restricted to the induced subgraph on
    cycle + interior.  Returns (r, edges_R, target, pi, c) with target in the
    sat convention, pi in the router convention, c the cycle in local
    labels.  (Non-incremental path; RegionSolver is the fast one.)"""
    R = sorted(set(cycle) | set(interior))
    loc = {v: i for i, v in enumerate(R)}
    e = [(loc[a], loc[b]) for a, b in edges if a in loc and b in loc]
    c = [loc[v] for v in cycle]
    tgt = rotation_target(len(R), c)
    for cyc in inner:
        m = len(cyc)
        for j in range(m):
            tgt[loc[cyc[(j + 1) % m]]] = loc[cyc[j]]
    for a, b in M:
        tgt[loc[a]], tgt[loc[b]] = loc[b], loc[a]
    pi = [0] * len(R)
    for v, k in enumerate(tgt):
        pi[k] = v
    return len(R), e, tgt, pi, c


def single_edge_bound(r, e, pi, c):
    """The winding bound with omega = +1 on the cycle edge c[0]-c[1]: this is
    the girth law, and it is unaffected by transpositions of edges off the
    cycle (they carry omega = 0) and by rotations of inner cycles (their
    tokens move along edges with omega = 0)."""
    a, b = c[0], c[1]
    omega = {ed: 0 for ed in e}
    if (a, b) in omega:
        omega[(a, b)] = 1
    else:
        omega[(b, a)] = -1
    bnd, D, maxQ, g = winding_bound(r, e, omega, pi)
    return bnd


class RegionSolver:
    """One CaDiCaL instance for one cycle's region.  The rotation of the cycle
    is a fixed goal; every *component* of an interior permutation -- an
    interior edge (transposition) or an oriented inner cycle (rotation) --
    gets a selector variable, and the goal for an interior vertex reads
    "if the selected component containing me says token k ends here, then k
    ends here; if none is selected, I keep my own token".  A call fixes the
    selectors by assumptions, so learned clauses are shared across the whole
    interior enumeration.  SAT answers are replayed against the concrete
    target, independently of the solver."""

    def __init__(self, edges, cycle, interior, inner_cycles, T,
                 solver="cadical195"):
        self.R = sorted(set(cycle) | set(interior))
        self.loc = {v: i for i, v in enumerate(self.R)}
        loc = self.loc
        self.r = len(self.R)
        self.e = [(loc[a], loc[b]) for a, b in edges if a in loc and b in loc]
        self.c = [loc[v] for v in cycle]
        self.T = T
        self.base = rotation_target(self.r, self.c)      # cycle goal
        interior_local = {loc[v] for v in interior}

        self.enc = Encoding(self.r, self.e, None, T)
        p = self.enc.p
        clauses = list(self.enc.clauses)
        # fixed goal on the cycle
        for v in self.c:
            clauses.append([p[(self.base[v], v, T)]])

        # components
        self.comp = {}                                   # key -> (var, pred)
        by_vertex = defaultdict(list)
        for a, b in self.e:
            if a in interior_local and b in interior_local:
                var = self.enc._new()
                self.comp[("edge", (a, b))] = (var, {a: b, b: a})
        for cyc in inner_cycles:
            for orient in (cyc, cyc[::-1]):
                lc = [loc[v] for v in orient]
                m = len(lc)
                pred = {lc[(j + 1) % m]: lc[j] for j in range(m)}
                var = self.enc._new()
                self.comp[("cycle", tuple(orient))] = (var, pred)
        for key, (var, pred) in self.comp.items():
            for v in pred:
                by_vertex[v].append((var, pred[v]))
        for v in interior_local:
            opts = by_vertex[v]
            for var, k in opts:
                clauses.append([-var, p[(k, v, T)]])
            clauses.append([var for var, _ in opts] + [p[(v, v, T)]])
            for (v1, _), (v2, _) in combinations(opts, 2):
                clauses.append([-v1, -v2])
        self.nv = self.enc.nv
        self.n_clauses = len(clauses)
        self.solver = Solver(name=solver, bootstrap_with=clauses)
        self.all_vars = [var for var, _ in self.comp.values()]

    def target_for(self, keys):
        tgt = list(self.base)
        for key in keys:
            for v, k in self.comp[key][1].items():
                tgt[v] = k
        return tgt

    def solve(self, keys):
        """keys: component keys (in global labels) that are selected.
        Returns (sat, schedule_or_None, seconds)."""
        t0 = time.perf_counter()
        on = {self.comp[k][0] for k in keys}
        assumptions = [v if v in on else -v for v in self.all_vars]
        sat = self.solver.solve(assumptions=assumptions)
        sched = None
        if sat:
            sched = self.enc.schedule(self.solver.get_model())
            if not replay(self.r, sched, self.target_for(keys)):
                raise AssertionError("SAT model does not replay to the target")
        return sat, sched, time.perf_counter() - t0

    def close(self):
        self.solver.delete()


def system_keys(loc, inner, M):
    """Component keys for one (inner cycles, matching) system."""
    keys = [("cycle", tuple(cyc)) for cyc in inner]
    keys += [("edge", (loc[a], loc[b])) for a, b in M]
    return keys


# --- the enumeration --------------------------------------------------------

def enumerate_patch(W, Ht, T=11, verbose=True, cross_check=True, max_region=None,
                    log=None, shard=None, incremental=True):
    """Decide the LB = 1 slice of the 2-core of X(W, Ht) at T rounds.

    Returns a dict with per-cycle rows and the verdict.  `all_within_T` is
    True iff every (cycle, interior permutation) instance has a replayed
    schedule of <= T rounds on its own region, which by (I) and (L) decides
    every LB = 1 permutation of the patch (and of the full brick rectangle,
    whose extra pendant vertices lie outside every region).  `max_region`
    restricts the run to cycles whose region has at most that many vertices
    (the suite's --fast mode); `shard=(i, k)` to cycles with index % k == i;
    the verdict is then partial.  `log` names a JSON-lines file: one line per
    finished cycle, and cycles already in it are not recomputed (so an
    interrupted run resumes)."""
    g = HeavyHex(W, Ht)
    verts, idx, edges, cycles = face_union_cycles(g)
    n = len(verts)
    if cross_check:
        brute = count_simple_cycles(n, edges)
        assert brute == len(cycles), (brute, len(cycles))
    cycles.sort(key=lambda c: (len(c["cycle"]), c["faces"]))
    all_cycles = list(cycles)
    skipped = 0
    if max_region is not None:
        kept = [c for c in cycles
                if len(c["cycle"]) + len(c["interior"]) <= max_region]
        skipped += len(cycles) - len(kept)
        cycles = kept
    if shard is not None:
        i, k = shard
        kept = [c for j, c in enumerate(cycles) if j % k == i]
        skipped += len(cycles) - len(kept)
        cycles = kept

    if verbose:
        print(f"  2-core of X({W},{Ht}): n = {n}, {len(edges)} edges, "
              f"{len(brick_faces(g))} faces, {len(all_cycles)} simple cycles "
              f"(lengths {dict(sorted(Counter(len(c['cycle']) for c in all_cycles).items()))})"
              + (f"; this run: {len(cycles)} of them" if skipped else ""))
        print(f"  {'cycle':>5} {'faces':>18} {'|R|':>4} {'int':>4} {'inner':>5} "
              f"{'instances':>9} {'wind':>4} {'T':>3}  verdict {'max s':>6} {'total s':>8}")

    done = {}
    if log and os.path.exists(log):
        with open(log, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    rec = json.loads(line)
                    done[tuple(rec["faces"])] = rec

    rows = []
    all_ok = True
    calls = 0
    total = 0.0
    for cinfo in cycles:
        if tuple(cinfo["faces"]) in done:
            row = done[tuple(cinfo["faces"])]
            row["faces"] = tuple(row["faces"])
            rows.append(row)
            calls += row["calls"]
            total += row["secs"]
            all_ok &= row["sat"] == row["instances"]
            if verbose:
                _print_row(row, T, resumed=True)
            continue

        t_cycle = time.perf_counter()
        calls_before = calls
        interior = cinfo["interior"]
        iset = set(interior)
        inner_cycles = [c["cycle"] for c in all_cycles if set(c["cycle"]) <= iset]
        systems = list(inner_systems(interior, all_cycles, edges))
        worst = 0.0
        n_sat = 0
        n_escaped = 0

        # the winding bound is the same for every instance of this cycle
        r, e, tgt, pi, c = region_instance(edges, cinfo["cycle"], interior, [])
        wind = single_edge_bound(r, e, pi, c)

        rs = RegionSolver(edges, cinfo["cycle"], interior, inner_cycles, T) \
            if incremental else None
        for inner, M in systems:
            if incremental:
                keys = system_keys(rs.loc, inner, M)
                tgt_local = rs.target_for(keys)
                assert lower_bound(rs.r, rs.e, tgt_local) == 1
                sat, sched, secs = rs.solve(keys)
            else:
                r, e, tgt, pi, c = region_instance(edges, cinfo["cycle"],
                                                   interior, M, inner)
                assert lower_bound(r, e, tgt) == 1
                sat, sched, secs, st = check(r, e, tgt, T)
            calls += 1
            total += secs
            worst = max(worst, secs)
            if sat:
                n_sat += 1
                continue
            # locality fallback: the same permutation on the whole 2-core
            tgt_full = rotation_target(n, cinfo["cycle"])
            for cyc in inner:
                m = len(cyc)
                for j in range(m):
                    tgt_full[cyc[(j + 1) % m]] = cyc[j]
            for a, b in M:
                tgt_full[a], tgt_full[b] = b, a
            sat2, sched2, secs2, st2 = check(n, edges, tgt_full, T)
            calls += 1
            total += secs2
            worst = max(worst, secs2)
            if sat2:
                n_escaped += 1
            all_ok = False
        if rs is not None:
            rs.close()

        row = {"length": len(cinfo["cycle"]), "faces": cinfo["faces"],
               "region": len(cinfo["cycle"]) + len(interior),
               "interior": len(interior), "inner_cycles": len(inner_cycles),
               "instances": len(systems), "winding": wind, "sat": n_sat,
               "escaped": n_escaped, "max_secs": worst,
               "calls": calls - calls_before,
               "secs": time.perf_counter() - t_cycle, "T": T,
               "mode": "incremental" if incremental else "separate"}
        rows.append(row)
        if log:
            with open(log, "a", encoding="utf-8") as f:
                f.write(json.dumps(row) + "\n")
        if verbose:
            _print_row(row, T)

    verdict = {"W": W, "Ht": Ht, "n": n, "cycles": len(cycles), "skipped": skipped,
               "T": T, "calls": calls, "seconds": total, "all_within_T": all_ok,
               "rows": rows}
    if verbose:
        print(f"  {calls} SAT calls, {total:.1f} s solving"
              + (f"  ({skipped} cycles not in this run)" if skipped else ""))
        if all_ok and skipped:
            print(f"  -> every instance run costs <= {T}; verdict partial")
        elif all_ok:
            print(f"  -> every LB = 1 permutation of X({W},{Ht}) costs <= {T}; "
                  f"those containing a cycle cost exactly "
                  f"{min(r['winding'] for r in rows)}..{T} "
                  f"(winding bound .. SAT), edge-only ones cost 1")
        else:
            print(f"  -> some LB = 1 permutation of X({W},{Ht}) costs > {T} on its "
                  f"region; see rows")
    return verdict


def _print_row(row, T, resumed=False):
    ok = row["sat"] == row["instances"]
    verdict = "all SAT" if ok else (
        f"{row['instances'] - row['sat']} UNSAT on region, "
        f"{row['escaped']} SAT on patch")
    print(f"  {row['length']:>5} {str(row['faces']):>18} {row['region']:>4} "
          f"{row['interior']:>4} {row['inner_cycles']:>5} {row['instances']:>9} "
          f"{row['winding']:>4} {T:>3}  {verdict:8s} {row['max_secs']:6.2f} "
          f"{row['secs']:8.1f}" + ("  (resumed)" if resumed else ""))


def main(argv):
    args = [a for a in argv[1:] if not a.startswith("--")]
    W = int(args[0]) if len(args) > 0 else 5
    Ht = int(args[1]) if len(args) > 1 else 2
    T = int(args[2]) if len(args) > 2 else 11
    log = None
    shard = None
    incremental = True
    for a in argv[1:]:
        if a.startswith("--log="):
            log = a[len("--log="):]
        elif a.startswith("--shard="):
            i, k = a[len("--shard="):].split("/")
            shard = (int(i), int(k))
        elif a == "--separate":
            incremental = False
    print(f"LB = 1 slice of the heavy-hex patch X({W},{Ht}) at T = {T}  "
          f"(CaDiCaL via python-sat, "
          f"{'incremental' if incremental else 'one solver per instance'}"
          + (f", shard {shard[0]}/{shard[1]}" if shard else "") + ")\n")
    t0 = time.perf_counter()
    v = enumerate_patch(W, Ht, T, log=log, shard=shard, incremental=incremental)
    print(f"\n  wall {time.perf_counter() - t0:.1f} s")
    print(f"\n  overall: "
          f"{'ALL <= ' + str(T) if v['all_within_T'] else 'WITNESS ABOVE ' + str(T)}"
          + (" (partial run)" if v["skipped"] else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
