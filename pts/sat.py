"""Bounded model checking for parallel token swapping:
"is there a schedule of at most T rounds?"  ->  CNF  ->  CaDiCaL (python-sat).

Variables
    x[e][t]     edge e is in the matching of round t            t = 0 .. T-1
    p[k][v][t]  token k sits on vertex v after t rounds          t = 0 .. T

Clauses
    init    p[k][k][0];  -p[k][v][0] for v != k
    goal    p[target[v]][v][T]                (target[v] = token that must end on v)
    match   per vertex v and round t: at most one incident x[e][t]
    stay    p[k][v][t] and no incident edge fires  ->  p[k][v][t+1]
            (-p[k][v][t]  v  OR_{e incident to v} x[e][t]  v  p[k][v][t+1])
    move    p[k][u][t] and x[(u,v)][t]  ->  p[k][v][t+1]
    amo     per token k and time t: at most one v with p[k][v][t]

Soundness.  Layer 0 is fixed by `init`.  Given layer t and the matching
x[.][t], `stay`/`move` force each token's true successor position and `amo`
forbids any other, so layer t+1 is exactly the result of applying the matching.
Hence a model exists iff some sequence of matchings of length T realises the
target.  Every SAT answer is additionally *replayed* from the identity with
pts.exact.apply_matching, independently of the solver.  An UNSAT answer is the
solver's verdict; pass proof=True to have CaDiCaL emit a DRAT proof file.

    python -m pts.sat            # validate against the exact solver, certify the
                                 # heavy-hex face, run the n = 21 RQ1 instance
    python -m pts.sat --big      # also the n = 35 instance (may take long)
"""

import sys
import time
from collections import defaultdict, deque
from itertools import combinations

from pysat.solvers import Solver

from .exact import apply_matching, solve
from .heavyhex import HeavyHex
from .winding import face_ring


# --- encoding ---------------------------------------------------------------

class Encoding:
    def __init__(self, n, edges, target, T):
        self.n, self.T = n, T
        self.edges = [tuple(sorted(e)) for e in edges]
        self.target = list(target)
        self.nv = 0
        self.x = {}                                  # (e_index, t) -> var
        self.p = {}                                  # (k, v, t)     -> var
        self.clauses = []
        self._build()

    def _new(self):
        self.nv += 1
        return self.nv

    def _build(self):
        n, T, E = self.n, self.T, self.edges
        inc = defaultdict(list)                       # v -> [e_index]
        for i, (a, b) in enumerate(E):
            inc[a].append(i)
            inc[b].append(i)
        for i in range(len(E)):
            for t in range(T):
                self.x[(i, t)] = self._new()
        for k in range(n):
            for v in range(n):
                for t in range(T + 1):
                    self.p[(k, v, t)] = self._new()
        x, p, C = self.x, self.p, self.clauses

        # init
        for k in range(n):
            for v in range(n):
                C.append([p[(k, v, 0)]] if v == k else [-p[(k, v, 0)]])
        # goal
        for v in range(n):
            C.append([p[(self.target[v], v, T)]])
        # match: at most one incident edge per vertex per round
        for v in range(n):
            for t in range(T):
                for i, j in combinations(inc[v], 2):
                    C.append([-x[(i, t)], -x[(j, t)]])
        # stay / move
        for t in range(T):
            for k in range(n):
                for v in range(n):
                    C.append([-p[(k, v, t)]] + [x[(i, t)] for i in inc[v]]
                             + [p[(k, v, t + 1)]])
                for i, (a, b) in enumerate(E):
                    C.append([-p[(k, a, t)], -x[(i, t)], p[(k, b, t + 1)]])
                    C.append([-p[(k, b, t)], -x[(i, t)], p[(k, a, t + 1)]])
        # amo: one position per token per time
        for k in range(n):
            for t in range(T + 1):
                for v, w in combinations(range(n), 2):
                    C.append([-p[(k, v, t)], -p[(k, w, t)]])

    def schedule(self, model):
        pos = {abs(l): l > 0 for l in model}
        sched = []
        for t in range(self.T):
            sched.append(tuple(e for i, e in enumerate(self.edges)
                               if pos.get(self.x[(i, t)], False)))
        return sched

    def to_dimacs(self, path):
        with open(path, "w") as f:
            f.write(f"p cnf {self.nv} {len(self.clauses)}\n")
            for c in self.clauses:
                f.write(" ".join(map(str, c)) + " 0\n")


def replay(n, sched, target):
    state = tuple(range(n))
    for m in sched:
        seen = set()
        for a, b in m:
            if a in seen or b in seen:
                return False
            seen |= {a, b}
        state = apply_matching(state, m)
    return list(state) == list(target)


def check(n, edges, target, T, solver="cadical195", proof=None):
    """Return (sat, schedule_or_None, seconds, stats).  A SAT schedule is
    replayed independently; a replay failure raises."""
    t0 = time.perf_counter()
    enc = Encoding(n, edges, target, T)
    kw = {"name": solver, "bootstrap_with": enc.clauses}
    if proof:
        kw["with_proof"] = True
    with Solver(**kw) as s:
        sat = s.solve()
        if sat:
            sched = enc.schedule(s.get_model())
            if not replay(n, sched, target):
                raise AssertionError("SAT model does not replay to the target")
        else:
            sched = None
            if proof:
                with open(proof, "w") as f:
                    f.write("\n".join(s.get_proof()))
        stats = s.accum_stats()
    return sat, sched, time.perf_counter() - t0, {"vars": enc.nv,
                                                   "clauses": len(enc.clauses),
                                                   **stats}


def lower_bound(n, edges, target):
    adj = defaultdict(list)
    for a, b in edges:
        adj[a].append(b)
        adj[b].append(a)
    lb = 0
    for v in range(n):
        k = target[v]                      # token k must reach v
        d = {k: 0}
        dq = deque([k])
        while dq and v not in d:
            u = dq.popleft()
            for w in adj[u]:
                if w not in d:
                    d[w] = d[u] + 1
                    dq.append(w)
        lb = max(lb, d[v])
    return lb


def min_rounds(n, edges, target, T_max, verbose=False):
    """Smallest T with a schedule, searching upward from the geodesic bound."""
    for T in range(lower_bound(n, edges, target), T_max + 1):
        sat, sched, secs, st = check(n, edges, target, T)
        if verbose:
            print(f"    T={T:2d}: {'SAT  ' if sat else 'UNSAT'} {secs:7.2f}s "
                  f"({st['vars']} vars, {st['clauses']} clauses)")
        if sat:
            return T, sched
    return None, None


# --- heavy-hex instances ----------------------------------------------------

def two_core(g):
    """(vertices, index, edges) of the 2-core of X: the i x j patch."""
    adj = {v: set(ws) for v, ws in g.adj.items()}
    alive, changed = set(adj), True
    while changed:
        changed = False
        for v in list(alive):
            if len(adj[v] & alive) < 2:
                alive.discard(v)
                changed = True
    verts = [v for v in g.vertices if v in alive]
    idx = {v: i for i, v in enumerate(verts)}
    edges = sorted({tuple(sorted((idx[u], idx[w])))
                    for u in verts for w in adj[u] if w in alive})
    return verts, idx, edges


def brick_faces(g):
    """Corner lists of every complete hexagonal face of the brick rectangle."""
    out = []
    for y0 in range(g.Ht):
        for x0 in range(g.W - 1):
            if (x0 + y0) % 2 == 0 and x0 + 2 <= g.W:
                out.append([(x0, y0), (x0 + 1, y0), (x0 + 2, y0),
                            (x0 + 2, y0 + 1), (x0 + 1, y0 + 1), (x0, y0 + 1)])
    return out


def union_boundary(g, faces):
    """Ordered X-vertex cycle bounding the union of the given faces, and the
    X-vertices interior to it."""
    edge_sets = []
    inside = set()
    for corners in faces:
        ring = face_ring(g, corners)
        inside |= set(ring)
        edge_sets.append({frozenset((ring[i], ring[(i + 1) % len(ring)]))
                          for i in range(len(ring))})
    boundary = set()
    for es in edge_sets:
        boundary ^= es                              # symmetric difference
    adj = defaultdict(list)
    for e in boundary:
        a, b = tuple(e)
        adj[a].append(b)
        adj[b].append(a)
    assert all(len(ws) == 2 for ws in adj.values()), "union boundary is not a cycle"
    start = next(iter(adj))
    cyc, prev, cur = [start], None, start
    while True:
        nxt = adj[cur][0] if adj[cur][0] != prev else adj[cur][1]
        if nxt == start:
            break
        cyc.append(nxt)
        prev, cur = cur, nxt
    interior = inside - set(cyc)
    return cyc, interior


def rotation_target(n, cyc):
    tgt = list(range(n))
    m = len(cyc)
    for j in range(m):
        tgt[cyc[(j + 1) % m]] = cyc[j]
    return tgt


def rq1_instances():
    """The two RQ1 witness instances, each on a genuine family member."""
    out = []

    g = HeavyHex(5, 1)                              # 2 x 1 patch, 2-core n = 21
    verts, idx, edges = two_core(g)
    faces = brick_faces(g)
    assert len(faces) == 2
    cyc, interior = union_boundary(g, faces)
    c = [idx[v] for v in cyc]
    out.append({"name": "20-cycle bounding two fused faces (2-core of 2x1 patch)",
                "n": len(verts), "edges": edges, "cycle": c,
                "target": rotation_target(len(verts), c),
                "interior": len(interior)})

    g = HeavyHex(5, 2)                              # 2 x 2 patch, 2-core n = 35
    verts, idx, edges = two_core(g)
    faces = brick_faces(g)
    assert len(faces) == 4
    # the three faces around the interior branch vertex (2, 1)
    tri = [f for f in faces if (2, 1) in f]
    assert len(tri) == 3
    cyc, interior = union_boundary(g, tri)
    c = [idx[v] for v in cyc]
    out.append({"name": "24-cycle around a branch vertex (2-core of 2x2 patch)",
                "n": len(verts), "edges": edges, "cycle": c,
                "target": rotation_target(len(verts), c),
                "interior": len(interior)})
    return out


# --- validation and the RQ1 runs -------------------------------------------

def validate():
    """SAT optimum == exact BFS optimum on the small instances of the suite."""
    from .experiments import (cycle_with_chords, cycle_with_escape_path,
                              cycle_with_legs_and_hub, cycle_with_pendants,
                              grid_boundary_cycle, grid_graph, rotate_target)
    cases = []
    for m in (4, 5, 6, 7):
        cases.append((f"C_{m}", m, [(i, (i + 1) % m) for i in range(m)],
                      rotate_target(m)))
    for m in (6, 8):
        n, e = cycle_with_legs_and_hub(m)
        cases.append((f"C_{m}+legs->hub", n, e, rotate_target(m, n)))
    n, e = cycle_with_pendants(6)
    cases.append(("C_6+pendants", n, e, rotate_target(6, n)))
    n, e = cycle_with_escape_path(8, 0, 4, 4)
    cases.append(("C_8+escape", n, e, rotate_target(8, n)))
    n, e = cycle_with_chords(6, [(0, 3)])
    cases.append(("C_6+chord", n, e, rotate_target(6)))
    n, e = cycle_with_chords(10, [(0, 5)])
    cases.append(("fused hexagons", n, e, rotate_target(10)))
    for (R, Cc) in ((2, 5), (3, 3)):
        verts, idx, edges = grid_graph(R, Cc)
        ring = [idx[v] for v in grid_boundary_cycle(R, Cc)]
        cases.append((f"{R}x{Cc} grid boundary", len(verts), edges,
                      rotation_target(len(verts), ring)))

    ok = True
    print(f"  {'instance':22s} {'n':>3} {'exact':>5} {'SAT':>4} {'time':>7}")
    for name, n, edges, tgt in cases:
        t0 = time.perf_counter()
        opt, _ = solve(n, edges, tgt)
        T, _ = min_rounds(n, edges, tgt, opt + 1)
        good = T == opt
        ok &= good
        print(f"  {'ok ' if good else 'FAIL'} {name:18s} {n:3d} {opt:5d} {T:4d} "
              f"{time.perf_counter() - t0:6.1f}s")
    return ok


def certify_face():
    """Second, solver-based certificate that a face rotation costs exactly 11."""
    g = HeavyHex(3, 1)
    idx = g.index
    n = len(g.vertices)
    edges = sorted({tuple(sorted((idx[u], idx[v])))
                    for u in g.vertices for v in g.adj[u]})
    ring = [idx[v] for v in face_ring(g, brick_faces(g)[0])]
    tgt = rotation_target(n, ring)
    res = {}
    for T in (10, 11):
        sat, sched, secs, st = check(n, edges, tgt, T)
        res[T] = (sat, secs)
        print(f"    X(3,1) face rotation, n={n}, T={T}: "
              f"{'SAT  ' if sat else 'UNSAT'} {secs:6.2f}s  "
              f"({st['vars']} vars, {st['clauses']} clauses)")
    return res[10][0] is False and res[11][0] is True


def main(big=False):
    print("Bounded model checking for PTS  (CaDiCaL via python-sat)\n")
    print("(1) validation against the exact solver")
    ok = validate()
    print("  ->", "AGREES" if ok else "MISMATCH")

    print("\n(2) the face rotation, certified twice (winding bound and SAT)")
    ok &= certify_face()
    print("  ->", "OPT = 11 CERTIFIED" if ok else "FAILED")

    print("\n(3) RQ1: does an enclosing cycle beat girth - 1 = 11 ?")
    insts = rq1_instances()
    for inst in insts if big else insts[:1]:
        print(f"  {inst['name']}: n={inst['n']}, cycle length={len(inst['cycle'])}, "
              f"interior vertices={inst['interior']}, LB=1")
        for T in (11, 12, 13):
            sat, sched, secs, st = check(inst["n"], inst["edges"], inst["target"], T)
            print(f"    T={T}: {'SAT  ' if sat else 'UNSAT'} {secs:8.2f}s  "
                  f"({st['vars']} vars, {st['clauses']} clauses)")
            if sat:
                print(f"    -> OPT = {T} for this instance"
                      + ("  (= girth - 1: does NOT beat 11)" if T == 11
                         else "  (BEATS 11: sigma(heavy-hex) > 11)"))
                break
    if not big:
        print("  (run with --big for the n = 35 instance)")
    print(f"\n  overall: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main(big="--big" in sys.argv))
