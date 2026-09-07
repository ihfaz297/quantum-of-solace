"""End-to-end check: the five-phase algorithm really realises pi on X,
plus measurement of the constants the proof note leaves as `O(1)`."""

import random

from .heavyhex import HeavyHex
from .router import solve, replay


def run(W, Ht, trials=10, seed=0):
    g = HeavyHex(W, Ht)
    dx = g.all_distances()
    rng = random.Random(seed)
    out = {"W": W, "Ht": Ht, "n": len(g.vertices), "ok": True, "why": "ok",
           "ratios": [], "lift": 0, "colours": 0, "pathlen": 0, "final": 0}

    for _ in range(trials):
        tgt = g.vertices[:]
        rng.shuffle(tgt)
        pi = dict(zip(g.vertices, tgt))
        lb = max(dx[v][pi[v]] for v in g.vertices)

        sched, st = solve(g, pi)
        ok, why = replay(g, sched, pi)
        if not ok:
            out["ok"], out["why"] = False, why
            return out

        out["ratios"].append(st.rounds / lb if lb else 0.0)
        out["lift"] = max(out["lift"], max(st.lift_cost, default=0))
        out["colours"] = max(out["colours"], max(st.colours, default=0))
        out["pathlen"] = max(out["pathlen"], st.path_len)
        out["final"] = max(out["final"], st.final_rounds)
    return out


if __name__ == "__main__":
    ok = True
    print(f"{'':4} {'shape':>9} {'n':>5} {'rounds/LB':>18} "
          f"{'lift/mesh rnd':>13} {'colours':>8} {'|path|':>7} {'final':>6}")
    for (W, Ht) in [(3, 1), (3, 3), (5, 2), (5, 5), (7, 3), (9, 4), (11, 5)]:
        r = run(W, Ht, trials=8, seed=W * 31 + Ht)
        ok &= r["ok"]
        rs = r["ratios"]
        span = f"{min(rs):.2f}-{max(rs):.2f}" if rs else "-"
        print(f"{'ok ' if r['ok'] else 'FAIL':4} {f'{W}x{Ht}':>9} {r['n']:5d} "
              f"{span:>18} {r['lift']:13d} {r['colours']:8d} "
              f"{r['pathlen']:7d} {r['final']:6d}")
        if not r["ok"]:
            print("      ", r["why"])
    print("\nAlgorithm (correctness):", "VERIFIED" if ok else "FAILED")
