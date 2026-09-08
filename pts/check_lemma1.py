"""Machine check of Lemma 1 (the cell decomposition) on brick rectangles."""

from collections import Counter

from .heavyhex import HeavyHex
from .experiments import girth


def check(W, Ht, verbose=False):
    g = HeavyHex(W, Ht)
    res = {"W": W, "Ht": Ht, "n": len(g.vertices), "cells": len(g.grid)}
    fails = []

    # 1a. phi partitions V(X) into non-empty fibers of size at most 5.
    if sum(len(f) for f in g.fiber.values()) != len(g.vertices):
        fails.append("fibers do not partition V(X)")
    sizes = Counter(len(f) for f in g.fiber.values())
    res["fiber_sizes"] = dict(sorted(sizes.items()))
    if min(sizes) < 1 or max(sizes) > 5:
        fails.append(f"fiber size out of [1,5]: {dict(sizes)}")

    # 1b. every fiber induces a connected subgraph of diameter at most 4.
    worst_diam = 0
    for p, f in g.fiber.items():
        adj = g.induced_adj(f)
        d0 = g.bfs(f[0], adj)
        if len(d0) != len(f):
            fails.append(f"fiber {p} is disconnected in X")
            continue
        diam = max(max(g.bfs(v, adj).values()) for v in f)
        worst_diam = max(worst_diam, diam)
        ne = sum(len(a) for a in adj.values()) // 2
        if ne != len(f) - 1:
            fails.append(f"fiber {p} induces a cycle, not a tree")
    res["max_fiber_diameter"] = worst_diam
    if worst_diam > 4:
        fails.append(f"fiber diameter {worst_diam} > 4")

    # 1c. the quotient graph is exactly the rectangular grid.
    got = g.quotient_edges()
    want = set()
    for (a, b) in g.grid:
        for q in ((a + 1, b), (a, b + 1)):
            if q in g.fiber:
                want.add(tuple(sorted(((a, b), q))))
    if got != want:
        fails.append(f"quotient != grid: extra {sorted(got - want)[:4]} "
                     f"missing {sorted(want - got)[:4]}")

    # 1d/1e. d_Gamma <= d_X  and  d_X <= 4 (d_Gamma + 1).
    dx = g.all_distances()
    dg = g.grid_distances()
    tight = 0
    worst_ratio = (0, 0)
    for u in g.vertices:
        du = dx[u]
        pu = g.phi[u]
        for v in g.vertices:
            a, b = du[v], dg[pu][g.phi[v]]
            if b > a:
                fails.append(f"d_Gamma > d_X at {u},{v}: {b} > {a}")
            if a > 4 * (b + 1):
                fails.append(f"d_X > 4(d_Gamma+1) at {u},{v}: {a} > {4*(b+1)}")
            if a == 4 * (b + 1):
                tight += 1
            if a - 4 * b > worst_ratio[0] - 4 * worst_ratio[1]:
                worst_ratio = (a, b)
    res["upper_bound_tight_pairs"] = tight
    res["worst_(d_X,d_Gamma)"] = worst_ratio
    # girth: every cycle of X is the subdivision of a cycle of H, and H has
    # girth 6, so girth(X) = 12 whenever there is a face at all.
    idx = g.index
    edges = {tuple(sorted((idx[u], idx[v]))) for u in g.vertices for v in g.adj[u]}
    gi = girth(len(g.vertices), edges)
    res["girth"] = gi
    has_face = g.A >= 1 and g.B >= 1
    if (has_face and gi != 12) or (not has_face and gi != float("inf")):
        fails.append(f"girth {gi} unexpected for A={g.A}, B={g.B}")
    res["ok"] = not fails
    res["failures"] = fails[:6]
    if verbose:
        print(res)
    return res


def sweep(shapes):
    rows = []
    for (W, Ht) in shapes:
        rows.append(check(W, Ht))
    return rows


if __name__ == "__main__":
    shapes = [(w, h) for w in (1, 3, 5, 7, 9, 11) for h in (0, 1, 2, 3, 4, 5)]
    ok = True
    for r in sweep(shapes):
        flag = "ok " if r["ok"] else "FAIL"
        print(f"{flag} W={r['W']:2d} Ht={r['Ht']} n={r['n']:4d} "
              f"cells={r['cells']:3d} sizes={r['fiber_sizes']} "
              f"maxdiam={r['max_fiber_diameter']} "
              f"tight={r['upper_bound_tight_pairs']:5d} "
              f"worst={r['worst_(d_X,d_Gamma)']}")
        if not r["ok"]:
            ok = False
            for f in r["failures"]:
                print("      ", f)
    print("\nLemma 1:", "VERIFIED on all shapes" if ok else "FAILED")
