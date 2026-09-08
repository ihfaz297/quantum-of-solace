"""A winding (cohomological) lower bound for parallel token swapping.

THEOREM.  Let G be a graph and omega : E -> Z antisymmetric on oriented edges
(omega(b, a) = -omega(a, b)).  For a permutation pi choose, for every vertex v,
any path Q_v from v to pi(v); put delta_v = omega(Q_v), D = sum_v delta_v, and
g_omega = min{ |C| : C a simple cycle with omega(C) != 0 }.  If D != 0 then

        OPT(G, pi)  >=  g_omega - max_v |Q_v|.

PROOF.  Let P_v be the walk token v actually takes in an optimal schedule of T
rounds; |P_v| <= T since a token moves at most once per round.  In each round
every matched edge is traversed once in each direction, so sum_v omega(P_v) = 0,
hence sum_v omega(P_v . Q_v^{-1}) = -D != 0 and some closed walk P_v . Q_v^{-1}
has nonzero omega.  A closed walk with nonzero omega contains a simple cycle
with nonzero omega, of length >= g_omega, so |P_v| + |Q_v| >= g_omega.  QED.

Two corollaries and one limitation:

  * G = C_n, pi = rotate by one, omega = +1 on every edge in the cyclic
    direction: g_omega = n, |Q_v| = 1, so OPT >= n - 1.  This is Li-Lu-Yang's
    Lemma 2.1 (SIAM J. Discrete Math. 24(4), 2010) and the lower half of
    Bansal-Gunluk-Shapley Theorem 5(b).  The point of the general form is that
    it needs no product structure: it applies to a cycle sitting inside a
    lattice with legs leaving it.
  * Rotating one hexagonal face of heavy-hex X: D = +-1, max |Q_v| = 1,
    g_omega >= girth(X) = 12, so OPT >= 11; and the n-1 adjacent transpositions
    give 11.  Hence OPT = 11 at LB = 1 and sigma(heavy-hex) >= 11.
  * CEILING.  On a planar graph the bounded faces generate the cycle space, so
    an omega vanishing on every face is a coboundary and forces D = 0.  Thus
    D != 0 needs omega(F) != 0 for some face F, giving g_omega <= |F|.  On
    heavy-hex every face is a 12-cycle, so this bound can NEVER exceed 11.  It
    cannot decide whether sigma(heavy-hex) = 11 or more.

    python -m pts.winding
"""

import math
import random
from collections import deque
from itertools import combinations

from .exact import all_matchings, apply_matching, solve
from .experiments import girth
from .heavyhex import HeavyHex


# --- the bound ----------------------------------------------------------------

def _w(omega, a, b):
    if (a, b) in omega:
        return omega[(a, b)]
    return -omega[(b, a)]


def path_weight(omega, path):
    return sum(_w(omega, path[i], path[i + 1]) for i in range(len(path) - 1))


def bfs_path(adj, s, t):
    if s == t:
        return [s]
    par = {s: None}
    dq = deque([s])
    while dq:
        u = dq.popleft()
        for w in adj[u]:
            if w not in par:
                par[w] = u
                if w == t:
                    p = [t]
                    while par[p[-1]] is not None:
                        p.append(par[p[-1]])
                    return p[::-1]
                dq.append(w)
    raise ValueError("disconnected")


def min_nonzero_cycle(n, adj, omega):
    """g_omega by DFS over simple cycles.  Fine for small graphs only."""
    best = math.inf
    for s in range(n):
        stack = [(s, [s], 0)]
        while stack:
            v, path, acc = stack.pop()
            if len(path) >= best:
                continue
            for u in adj[v]:
                if u == s and len(path) >= 3:
                    if acc + _w(omega, v, u) != 0:
                        best = min(best, len(path))
                elif u > s and u not in path:
                    stack.append((u, path + [u], acc + _w(omega, v, u)))
    return best


def bound(n, edges, omega, pi, g_omega=None):
    """Return (bound, D, max|Q_v|, g_omega).  pi[v] = target vertex of the
    token starting at v.  If g_omega is not supplied it is computed by DFS."""
    adj = {i: [] for i in range(n)}
    for a, b in edges:
        adj[a].append(b)
        adj[b].append(a)
    Q = {v: bfs_path(adj, v, pi[v]) for v in range(n)}
    D = sum(path_weight(omega, Q[v]) for v in range(n))
    maxQ = max(len(Q[v]) - 1 for v in range(n))
    if g_omega is None:
        g_omega = min_nonzero_cycle(n, adj, omega)
    if D == 0 or g_omega == math.inf:
        return 0, D, maxQ, g_omega
    return max(0, g_omega - maxQ), D, maxQ, g_omega


# --- planar omega from ray crossings -----------------------------------------

def ray_omega(edges, pos, z):
    """Signed crossings of each edge with the horizontal ray from z (+x)."""
    out = {}
    for (a, b) in edges:
        (x1, y1), (x2, y2) = pos[a], pos[b]
        y1 -= z[1]
        y2 -= z[1]
        x1 -= z[0]
        x2 -= z[0]
        if (y1 > 0) == (y2 > 0):
            out[(a, b)] = 0
            continue
        t = -y1 / (y2 - y1)
        x = x1 + t * (x2 - x1)
        out[(a, b)] = 0 if x <= 0 else (1 if y2 > y1 else -1)
    return out


# --- adversarial stress test (ported from the audit) ---------------------------

def stress_test(trials=1500, seed=7):
    """Random connected graphs on 4..7 vertices, random integer omega in
    [-2, 2], random permutations; exact OPT by BFS.  Returns
    (instances_with_positive_bound, violations, min(OPT - bound))."""
    rng = random.Random(seed)
    tested = violations = 0
    best_gap = None
    for _ in range(trials):
        n = rng.randint(4, 7)
        all_e = list(combinations(range(n), 2))
        k = rng.randint(n - 1, min(len(all_e), n + 3))
        while True:
            edges = rng.sample(all_e, k)
            adj = {i: [] for i in range(n)}
            for a, b in edges:
                adj[a].append(b)
                adj[b].append(a)
            seen, st = {0}, [0]
            while st:
                u = st.pop()
                for x in adj[u]:
                    if x not in seen:
                        seen.add(x)
                        st.append(x)
            if len(seen) == n:
                break
        omega = {e: rng.randint(-2, 2) for e in edges}
        perm = list(range(n))
        rng.shuffle(perm)
        b, D, maxQ, g = bound(n, edges, omega, perm)
        if b <= 0:
            continue
        tgt = [None] * n
        for v in range(n):
            tgt[perm[v]] = v
        o, _ = solve(n, edges, tgt)
        tested += 1
        if o < b:
            violations += 1
        gap = o - b
        best_gap = gap if best_gap is None else min(best_gap, gap)
    return tested, violations, best_gap


# --- the heavy-hex face ------------------------------------------------------

def positions(g):
    pos = {}
    for v in g.vertices:
        if v[0] == "b":
            pos[v] = (float(v[1]), float(v[2]))
        else:
            (p, q) = v[1]
            pos[v] = ((p[0] + q[0]) / 2.0, (p[1] + q[1]) / 2.0)
    return pos


def face_ring(g, corners):
    """The 12-cycle of X bounding the H-face with the given six corners."""
    ring = []
    for k, p in enumerate(corners):
        q = corners[(k + 1) % len(corners)]
        ring.append(("b", p[0], p[1]))
        ring.append(("s", tuple(sorted((p, q)))))
    return ring


def heavyhex_face(W=3, Ht=1, exact_g=True):
    """Rotate the face with corners (0,0),(1,0),(2,0),(2,1),(1,1),(0,1).

    Returns a dict with the winding bound, the trivial upper schedule (the 11
    adjacent transpositions, replayed on X), girth, and the cycle-space check
    behind the ceiling remark.
    """
    g = HeavyHex(W, Ht)
    idx = g.index
    n = len(g.vertices)
    edges = sorted({tuple(sorted((idx[u], idx[v])))
                    for u in g.vertices for v in g.adj[u]})
    adj = {i: [] for i in range(n)}
    for a, b in edges:
        adj[a].append(b)
        adj[b].append(a)

    corners = [(0, 0), (1, 0), (2, 0), (2, 1), (1, 1), (0, 1)]
    ring = [idx[v] for v in face_ring(g, corners)]
    m = len(ring)
    pi = list(range(n))
    for k in range(m):
        pi[ring[k]] = ring[(k + 1) % m]

    pos = {idx[v]: p for v, p in positions(g).items()}
    z = (sum(pos[v][0] for v in ring) / m + 1e-3,
         sum(pos[v][1] for v in ring) / m + 7e-4)
    omega = ray_omega(edges, pos, z)

    gi = girth(n, edges)
    g_om = min_nonzero_cycle(n, adj, omega) if exact_g else None
    b, D, maxQ, g_used = bound(n, edges, omega, pi, g_omega=g_om if exact_g else gi)

    # Upper bound: m - 1 adjacent transpositions along the ring, one per round.
    state = tuple(range(n))
    sched = []
    for k in range(m - 1, 0, -1):
        mt = ((ring[k - 1], ring[k]),)
        state = apply_matching(state, mt)
        sched.append(mt)
    realised = {state[v]: v for v in range(n)}          # token -> final vertex
    upper_ok = all(realised[v] == pi[v] for v in range(n))

    # Ceiling: bounded faces = cyclomatic number, so faces generate the cycle space.
    faces = len(edges) - n + 1
    return {"W": W, "Ht": Ht, "n": n, "ring": m, "girth": gi,
            "g_omega": g_used, "D": D, "maxQ": maxQ, "lower": b,
            "upper": len(sched), "upper_replays": upper_ok,
            "cyclomatic": faces, "hex_faces": g.A * g.B,
            "LB": 1}


def main():
    print("Winding lower bound  --  OPT >= g_omega - max|Q_v| when D != 0\n")
    t, v, gap = stress_test()
    print(f"  stress test: {t} random instances with a positive bound, "
          f"{v} violations, min(OPT - bound) = {gap}")
    ok = v == 0

    print("\n  rotate C_m by one, m = 4..8: bound m-1 vs exact OPT")
    for m in range(4, 9):
        edges = [(i, (i + 1) % m) for i in range(m)]
        omega = {e: 1 for e in edges}                # +1 in the cyclic direction
        pi = [(i + 1) % m for i in range(m)]
        b, D, maxQ, g = bound(m, edges, omega, pi)
        tgt = [None] * m
        for i in range(m):
            tgt[pi[i]] = i
        o, _ = solve(m, edges, tgt)
        ok &= (b == m - 1 == o)
        print(f"    C_{m}: g_omega={g} D={D} bound={b} OPT={o}")

    print("\n  heavy-hex face rotation (LB = 1):")
    for (W, Ht, exact) in ((3, 1, True), (5, 2, False), (7, 3, False)):
        r = heavyhex_face(W, Ht, exact_g=exact)
        ok &= (r["lower"] == 11 and r["upper"] == 11 and r["upper_replays"]
               and r["girth"] == 12 and r["cyclomatic"] == r["hex_faces"])
        print(f"    {W}x{Ht} n={r['n']:3d} girth={r['girth']} "
              f"g_omega={r['g_omega']}{'' if exact else ' (=girth, not searched)'} "
              f"D={r['D']:+d} |Q|<={r['maxQ']}  ->  {r['lower']} <= OPT <= {r['upper']}"
              f"  (upper schedule replays: {r['upper_replays']}; "
              f"faces={r['hex_faces']} = cyclomatic={r['cyclomatic']})")
    print("\n  => OPT = 11 exactly at LB = 1:  sigma(heavy-hex) >= 11.  PROVED.")
    print("  => every face is a 12-cycle and faces span the cycle space, so this")
    print("     bound is capped at 11 on any heavy-hex patch: it cannot show > 11.")
    print(f"\n  overall: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())


# --- the girth law with a single-edge omega -----------------------------------

def girth_law_bound(n, edges, cycle):
    """Rotate `cycle` by one (token at cycle[k] -> cycle[k+1]).  Take omega = +1
    on the edge cycle[0]-cycle[1] in the direction of rotation and 0 elsewhere.
    Then D = 1, |Q_v| <= 1, and g_omega is the shortest cycle through that
    edge, so OPT >= g_omega - 1 >= girth - 1.  Returns (bound, g_omega)."""
    a, b = cycle[0], cycle[1]
    omega = {e: 0 for e in edges}
    if (a, b) in omega:
        omega[(a, b)] = 1
    else:
        omega[(b, a)] = -1
    pi = list(range(n))
    m = len(cycle)
    for k in range(m):
        pi[cycle[k]] = cycle[(k + 1) % m]
    bnd, D, maxQ, g = bound(n, edges, omega, pi)
    return bnd, g
