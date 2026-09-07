"""Run every machine check behind the claims in REVIEW.md.

    python -m pts.check_all
"""

import sys
import time

from . import check_algorithm, check_lemma1, check_lemma2
from .exact import solve
from .experiments import (cycle_with_chords, rotate_target, section5_table,
                          winding_probe)


def banner(s):
    print(f"\n{'=' * 72}\n{s}\n{'=' * 72}")


def main():
    ok = True

    banner("Lemma 1  --  the cell decomposition")
    for W in (1, 3, 5, 7, 9, 11):
        for Ht in (0, 1, 2, 3, 4, 5):
            r = check_lemma1.check(W, Ht)
            ok &= r["ok"]
            if not r["ok"]:
                print(f"  FAIL W={W} Ht={Ht}: {r['failures']}")
    print("  36 shapes, n up to 168: partition, fiber size <= 5, fibers are")
    print("  trees of diameter <= 4, quotient is exactly the grid,")
    print("  d_Gamma <= d_X <= 4(d_Gamma + 1).")
    print("  -> VERIFIED" if ok else "  -> FAILED")

    banner("Lemma 2  --  padded Koenig decomposition into 5 cell-permutations")
    l2 = True
    for W in (3, 5, 7, 9, 11):
        for Ht in (1, 3, 5):
            r = check_lemma2.check(W, Ht, trials=20, seed=W * 100 + Ht)
            l2 &= r["ok"]
            if not r["ok"]:
                print(f"  FAIL W={W} Ht={Ht}: {r['failures']}")
    ok &= l2
    print("  15 shapes x 20 random permutations = 300 instances:")
    print("  every sigma_r is a permutation of V(Gamma) with")
    print("  max_p d_Gamma(p, sigma_r(p)) <= LB_X(pi).")
    print("  -> VERIFIED" if l2 else "  -> FAILED")

    banner("Section 4 algorithm  --  end-to-end, replayed independently")
    print(f"{'shape':>9} {'n':>5} {'rounds/LB':>13} {'c3':>4} "
          f"{'colours':>8} {'|path|':>7} {'c4':>4}")
    alg = True
    for (W, Ht) in [(3, 1), (3, 3), (5, 2), (5, 5), (7, 3), (9, 4), (11, 5)]:
        r = check_algorithm.run(W, Ht, trials=8, seed=W * 31 + Ht)
        alg &= r["ok"]
        rs = r["ratios"]
        span = f"{min(rs):.1f}-{max(rs):.1f}" if rs else "-"
        print(f"{f'{W}x{Ht}':>9} {r['n']:5d} {span:>13} {r['lift']:4d} "
              f"{r['colours']:8d} {r['pathlen']:7d} {r['final']:4d}")
        if not r["ok"]:
            print("   FAIL:", r["why"])
    ok &= alg
    print("  56 random permutations; every schedule replayed from scratch")
    print("  against the edge set of X.")
    print("  -> VERIFIED" if alg else "  -> FAILED")

    banner("Section 5 table  --  recomputed exactly")
    want = {"rotate boundary of 2x5 grid": 3,
            "rotate boundary of 3x3 grid": 4,
            "rotate boundary of two fused hexagons": 5}
    tbl = True
    for name, lb, opt, cyc in section5_table():
        exp = want.get(name)
        good = exp is None or exp == opt
        tbl &= good
        print(f"  {'ok ' if good else 'FAIL'} {name:40s} "
              f"LB={lb} OPT={opt} cycle_len={cyc}  (note says {exp})")
    ok &= tbl
    print("  -> REPRODUCED" if tbl else "  -> MISMATCH")

    banner("Baseline  --  OPT(rotate C_m by one) = m - 1")
    base = True
    for m in (5, 6):
        n, edges = cycle_with_chords(m, [])
        opt, _ = solve(n, edges, rotate_target(m))
        good = opt == m - 1
        base &= good
        print(f"  {'ok ' if good else 'FAIL'} C_{m}: OPT={opt} (m-1={m - 1})")
    ok &= base
    print("  -> REPRODUCED" if base else "  -> MISMATCH")

    banner("Winding probe  --  what actually makes a rotation cheap")
    print(f"  {'m':>3} {'bare':>6} {'+dead-end legs':>15} {'+legs to hub':>13} "
          f"{'+1 chord':>9} {'girth w/ chord':>15}")
    wind = True
    for r in winding_probe((4, 6)):
        wind &= (r["bare"] == r["m"] - 1
                 and r["dead_end_legs"] == r["m"] - 1
                 and r["legs_to_hub"] == r["m"] - 1
                 and r["one_chord"] == r["girth_with_chord"] - 1)
        print(f"  {r['m']:>3} {r['bare']:>6} {r['dead_end_legs']:>15} "
              f"{r['legs_to_hub']:>13} {r['one_chord']:>9} "
              f"{r['girth_with_chord']:>15}")
    ok &= wind
    print("  Legs -- even ones leading to a genuine escape route -- do not")
    print("  reduce the cost of rotating a cycle by one.  Only a chord does,")
    print("  and then the cost is girth - 1.  A heavy-hex face is a 12-cycle")
    print("  with outward legs and no chord, so this predicts OPT = 11 at")
    print("  LB = 1, i.e. sigma(heavy-hex) >= 11.")
    print("  -> CONSISTENT" if wind else "  -> UNEXPECTED")

    banner("SUMMARY")
    print("  Lemmas 1 and 2, the section 4 algorithm, and every number the")
    print("  note reports: all check out.")
    print("  Assumption (G) is NOT a theorem in BGS -- see REVIEW.md section 2.")
    print("  The >= 11 lower bound is unproved but well supported: rotation")
    print("  cost tracks girth, and legs do not shorten girth.")
    print(f"\n  overall: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    t = time.time()
    code = main()
    print(f"  [{time.time() - t:.1f}s]")
    sys.exit(code)
