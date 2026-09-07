"""Machine check of Lemma 2: pad the cell-demand multigraph to 5-regular,
split into five cell-permutations, and verify the displacement bound."""

import random
from collections import defaultdict

from .heavyhex import HeavyHex
from .koenig import decompose

K = 5


def cell_permutations(g, pi, dg=None):
    """pi maps vertex -> target vertex. Returns (sigmas, colour, padded)."""
    mult = defaultdict(int)
    owner = defaultdict(list)          # (p, q) -> tokens realising that edge
    for v in g.vertices:
        p, q = g.phi[v], g.phi[pi[v]]
        mult[(p, q)] += 1
        owner[(p, q)].append(v)
    padded = {}
    for p in g.grid:
        pad = K - len(g.fiber[p])
        if pad:
            mult[(p, p)] += pad
            padded[p] = pad

    sigmas = decompose(g.grid, mult, K)

    # Hand each token a colour consistent with the chosen matchings.
    pool = {e: list(ts) for e, ts in owner.items()}
    colour, designated = {}, []
    for r, s in enumerate(sigmas):
        assign = {}
        for p, q in s.items():
            ts = pool.get((p, q))
            if ts:
                t = ts.pop()
                colour[t] = r
                assign[p] = t
        designated.append(assign)
    return sigmas, colour, designated


def check(W, Ht, trials=20, seed=0, dg=None):
    g = HeavyHex(W, Ht)
    dgg = dg or g.grid_distances()
    dx = g.all_distances()
    rng = random.Random(seed)
    fails, worst = [], []

    for _ in range(trials):
        tgt = g.vertices[:]
        rng.shuffle(tgt)
        pi = dict(zip(g.vertices, tgt))
        lb = max(dx[v][pi[v]] for v in g.vertices)

        sigmas, colour, designated = cell_permutations(g, pi)

        if len(colour) != len(g.vertices):
            fails.append("some token received no colour")
        for r, s in enumerate(sigmas):
            if sorted(s.values()) != sorted(g.grid):
                fails.append(f"sigma_{r} is not a permutation of V(Gamma)")
            disp = max(dgg[p][q] for p, q in s.items())
            if disp > lb:
                fails.append(f"sigma_{r} displacement {disp} > LB_X {lb}")
            worst.append(disp / lb if lb else 0.0)
            # Lemma 2.2: the designated token really is routed to its target cell.
            for p, t in designated[r].items():
                if g.phi[t] != p or g.phi[pi[t]] != s[p]:
                    fails.append(f"token {t} mismatched with sigma_{r}")
        # every cell is designated in every phase, or is a padded fixed point
        for r, s in enumerate(sigmas):
            for p in g.grid:
                if p not in designated[r] and s[p] != p:
                    fails.append(f"cell {p} undesignated but sigma_{r} moves it")

    return {"W": W, "Ht": Ht, "n": len(g.vertices), "trials": trials,
            "max_disp_over_LB": round(max(worst), 3) if worst else 0.0,
            "ok": not fails, "failures": fails[:5]}


if __name__ == "__main__":
    ok = True
    for W in (3, 5, 7, 9, 11):
        for Ht in (1, 3, 5):
            r = check(W, Ht, trials=20, seed=W * 100 + Ht)
            print(f"{'ok ' if r['ok'] else 'FAIL'} W={W:2d} Ht={Ht} "
                  f"n={r['n']:4d} trials={r['trials']} "
                  f"max disp/LB={r['max_disp_over_LB']}")
            for f in r["failures"]:
                print("      ", f)
            ok &= r["ok"]
    print("\nLemma 2:", "VERIFIED" if ok else "FAILED")
