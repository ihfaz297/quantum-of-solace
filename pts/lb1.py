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
       If the rotation of C, composed with any transpositions of edges INSIDE
       R, has a schedule of T rounds using only edges of G[R], then composing
       it further with any matching M of edges outside R (the only other
       edges vertex-disjoint from C) costs at most max(T, 1): merge M into the
       first round -- it is vertex-disjoint from everything the schedule
       touches.  Likewise two cycles with disjoint regions schedule in
       parallel.  Two vertex-disjoint cycles of a plane graph are either
       nested or have disjoint closed regions, so a cycle system splits into
       its outermost cycles, and what a SAT instance must range over is one
       outermost cycle C together with EVERY LB = 1 permutation of G[interior
       of C] (nested cycles in either orientation, plus a matching).

So the whole LB = 1 slice is decided by one SAT call per (outermost cycle,
LB = 1 permutation of its interior), each run on the induced subgraph G[R],
each answered with a replayed schedule.  Every cycle of a 2-connected plane graph is the
boundary of a union of faces, which is how the cycles and their interiors are
enumerated here (checked against a brute-force DFS count).

Should a region instance be UNSAT at T on G[R], the same permutation is
re-solved on the whole patch; a SAT answer there would mean the schedule needs
to leave the region and the locality shortcut does not apply to that cycle
(this did not happen on any patch tried).

    python -m pts.lb1            # the 2 x 2 patch (n = 35) at T = 11
    python -m pts.lb1 7 2        # the 3 x 2 patch (n = 49)
    python -m pts.lb1 7 3 12     # the 3 x 3 patch (n = 68) at T = 12
    python -m pts.lb1 7 3 11 --log=results/lb1_7_3.jsonl   # resumable
"""

import json
import os
import sys
import time
from collections import Counter, defaultdict
from itertools import combinations

from .heavyhex import HeavyHex
from .sat import (brick_faces, check, lower_bound, rotation_target, two_core,
                  union_boundary)
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
    """All matchings, the empty one included, of the subgraph induced on vs."""
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


# --- one instance -----------------------------------------------------------

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


def region_instance(edges, cycle, interior, M, inner=()):
    """The permutation 'rotate cycle, rotate each inner cycle as oriented,
    transpose the edges of M' restricted to the induced subgraph on
    cycle + interior.  Returns (r, edges_R, target, pi, c) with target in the
    sat convention, pi in the router convention, c the cycle in local
    labels."""
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
    cycle (they carry omega = 0)."""
    a, b = c[0], c[1]
    omega = {ed: 0 for ed in e}
    if (a, b) in omega:
        omega[(a, b)] = 1
    else:
        omega[(b, a)] = -1
    bnd, D, maxQ, g = winding_bound(r, e, omega, pi)
    return bnd


# --- the enumeration --------------------------------------------------------

def enumerate_patch(W, Ht, T=11, verbose=True, cross_check=True, max_region=None,
                    log=None):
    """Decide the LB = 1 slice of the 2-core of X(W, Ht) at T rounds.

    Returns a dict with per-cycle rows and the verdict.  `all_within_T` is
    True iff every (cycle, interior matching) instance has a replayed schedule
    of <= T rounds on its own region, which by (I) and (L) decides every
    LB = 1 permutation of the patch (and of the full brick rectangle, whose
    extra pendant vertices lie outside every region).  `max_region` restricts
    the run to cycles whose region has at most that many vertices (the suite's
    --fast mode); the verdict then covers only those cycles.  `log` names a
    JSON-lines file: one line per finished cycle, and cycles already in it
    are not recomputed (so an interrupted run resumes)."""
    g = HeavyHex(W, Ht)
    verts, idx, edges, cycles = face_union_cycles(g)
    n = len(verts)
    if cross_check:
        brute = count_simple_cycles(n, edges)
        assert brute == len(cycles), (brute, len(cycles))
    cycles.sort(key=lambda c: (len(c["cycle"]), c["faces"]))
    skipped = 0
    if max_region is not None:
        kept = [c for c in cycles
                if len(c["cycle"]) + len(c["interior"]) <= max_region]
        skipped = len(cycles) - len(kept)
        cycles = kept

    if verbose:
        print(f"  2-core of X({W},{Ht}): n = {n}, {len(edges)} edges, "
              f"{len(brick_faces(g))} faces, {len(cycles)} simple cycles "
              f"(lengths {dict(sorted(Counter(len(c['cycle']) for c in cycles).items()))})")
        print(f"  {'cycle':>5} {'faces':>14} {'|R|':>4} {'int':>4} {'inner':>5} "
              f"{'instances':>9} {'wind':>4} {'T':>3}  verdict {'max s':>7}")

    rows = []
    all_ok = True
    calls = 0
    total = 0.0
    done = {}
    if log and os.path.exists(log):
        with open(log, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    rec = json.loads(line)
                    done[tuple(rec["faces"])] = rec
    all_cycles = list(cycles)
    for cinfo in cycles:
        if tuple(cinfo["faces"]) in done:
            row = done[tuple(cinfo["faces"])]
            row["faces"] = tuple(row["faces"])
            rows.append(row)
            calls += row["calls"]
            total += row["secs"]
            all_ok &= row["sat"] == row["instances"]
            if verbose:
                print(f"  {row['length']:>5} {str(row['faces']):>14} {row['region']:>4} "
                      f"{row['interior']:>4} {row['inner_cycles']:>5} {row['instances']:>9} "
                      f"{row['winding']:>4} {T:>3}  "
                      f"{'all SAT' if row['sat'] == row['instances'] else 'NOT ALL SAT':12s} "
                      f"{row['max_secs']:7.2f}  (resumed)")
            continue
        t_cycle = time.perf_counter()
        calls_before = calls
        systems = list(inner_systems(cinfo["interior"], all_cycles, edges))
        n_inner = sum(1 for c in all_cycles
                      if set(c["cycle"]) <= set(cinfo["interior"]))
        worst = 0.0
        n_sat = 0
        n_escaped = 0
        wind_min = None
        for inner, M in systems:
            r, e, tgt, pi, c = region_instance(edges, cinfo["cycle"],
                                               cinfo["interior"], M, inner)
            assert lower_bound(r, e, tgt) == 1
            wb = single_edge_bound(r, e, pi, c)
            wind_min = wb if wind_min is None else min(wind_min, wb)
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
        row = {"length": len(cinfo["cycle"]), "faces": cinfo["faces"],
               "region": len(cinfo["cycle"]) + len(cinfo["interior"]),
               "interior": len(cinfo["interior"]), "inner_cycles": n_inner,
               "instances": len(systems), "winding": wind_min, "sat": n_sat,
               "escaped": n_escaped, "max_secs": worst,
               "calls": calls - calls_before,
               "secs": time.perf_counter() - t_cycle, "T": T}
        rows.append(row)
        if log:
            with open(log, "a", encoding="utf-8") as f:
                f.write(json.dumps(row) + "\n")
        if verbose:
            verdict = ("all SAT" if n_sat == len(systems) else
                       f"{len(systems) - n_sat} UNSAT on region, {n_escaped} SAT on patch")
            print(f"  {row['length']:>5} {str(row['faces']):>14} {row['region']:>4} "
                  f"{row['interior']:>4} {n_inner:>5} {row['instances']:>9} {wind_min:>4} "
                  f"{T:>3}  {verdict:12s} {worst:7.2f}")
    verdict = {"W": W, "Ht": Ht, "n": n, "cycles": len(cycles), "skipped": skipped,
               "T": T, "calls": calls, "seconds": total, "all_within_T": all_ok,
               "rows": rows}
    if verbose:
        print(f"  {calls} SAT calls, {total:.1f} s total"
              + (f"  ({skipped} larger cycles skipped)" if skipped else ""))
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


def main(argv):
    args = [a for a in argv[1:] if not a.startswith("--")]
    W = int(args[0]) if len(args) > 0 else 5
    Ht = int(args[1]) if len(args) > 1 else 2
    T = int(args[2]) if len(args) > 2 else 11
    log = None
    for a in argv[1:]:
        if a.startswith("--log="):
            log = a[len("--log="):]
    print(f"LB = 1 slice of the heavy-hex patch X({W},{Ht}) at T = {T}  "
          f"(CaDiCaL via python-sat)\n")
    t0 = time.perf_counter()
    v = enumerate_patch(W, Ht, T, log=log)
    print(f"\n  wall {time.perf_counter() - t0:.1f} s")
    print(f"\n  overall: {'ALL <= ' + str(T) if v['all_within_T'] else 'WITNESS ABOVE ' + str(T)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
