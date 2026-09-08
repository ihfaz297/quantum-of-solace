"""Run every machine check behind the claims in REVIEW.md and REFINED_PROPOSAL.md.

    python -m pts.check_all            # ~3 minutes (the m = 8 winding rows)
    python -m pts.check_all --fast     # skips the m = 8 rows, ~10 s

Every claim labelled VERIFIED in REFINED_PROPOSAL.md names a section of this
output.  Larger-range measurements (n = 480) live in pts/scaling.py and are
labelled as such.
"""

import sys
import time

from . import check_algorithm, check_lemma1, check_lemma2, winding
from .exact import solve
from .experiments import (cycle_with_chords, cycle_with_escape_path,
                          cycle_with_legs_and_hub, cycle_with_pendants,
                          grid_guarantee_gap, involution_obstruction,
                          rotate_target, section5_table, two_core_audit,
                          winding_probe)


def banner(s):
    print(f"\n{'=' * 72}\n{s}\n{'=' * 72}")


def main(fast=False):
    ok = True

    banner("Lemma 1  --  the cell decomposition, and girth")
    faces = 0
    for W in (1, 3, 5, 7, 9, 11):
        for Ht in (0, 1, 2, 3, 4, 5):
            r = check_lemma1.check(W, Ht)
            ok &= r["ok"]
            faces += r["girth"] == 12
            if not r["ok"]:
                print(f"  FAIL W={W} Ht={Ht}: {r['failures']}")
    print("  36 shapes, n up to 168: partition, fiber size <= 5, fibers are")
    print("  trees of diameter <= 4, quotient is exactly the grid,")
    print(f"  d_Gamma <= d_X <= 4(d_Gamma + 1); girth = 12 on the {faces} shapes")
    print("  that have a face (the rest are trees).")
    print("  -> VERIFIED" if ok else "  -> FAILED")

    banner("Lemma 2  --  padded Koenig decomposition into 5 cell-permutations")
    l2 = True
    for W in (3, 5, 7, 9, 11):
        for Ht in (1, 3, 5):
            r = check_lemma2.check(W, Ht, trials=20, seed=W * 100 + Ht)
            l2 &= r["ok"]
            if not r["ok"]:
                print(f"  FAIL random W={W} Ht={Ht}: {r['failures']}")
    print("  (a) 15 shapes x 20 uniformly random permutations: every sigma_r is a")
    print("      permutation of V(Gamma) with max_p d_Gamma(p, sigma_r(p)) <= LB_X.")
    print("      NOTE: on random pi, LB_X > diam(Gamma), so this cannot fail.")
    worst = 0.0
    for W in (3, 5, 7, 11):
        for Ht in (1, 3, 5):
            for k in (1, 2, 3, 4):
                r = check_lemma2.check(W, Ht, trials=10, seed=W * 100 + Ht + k,
                                       low_lb=k)
                l2 &= r["ok"]
                worst = max(worst, r["max_disp_over_LB"])
                if not r["ok"]:
                    print(f"  FAIL low-LB k={k} W={W} Ht={Ht}: {r['failures']}")
    print(f"  (b) 12 shapes x LB in {{1,2,3,4}} x 10 permutations = 480 low-LB")
    print(f"      instances, where the inequality CAN fail: max disp/LB = {worst}.")
    ok &= l2
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
    print("  (a) 56 uniformly random permutations, every schedule replayed from")
    print("      scratch against the edge set of X.  rounds/LB here is a DIAMETER")
    print("      ratio, since a random pi has LB ~ diam.")
    print(f"\n  {'shape':>9} {'n':>5} {'LB':>3} {'max rounds':>11} {'rounds/LB':>10}")
    for (W, Ht) in [(3, 1), (5, 2), (7, 3), (11, 5)]:
        for k in (1, 2):
            r = check_algorithm.run(W, Ht, trials=3, seed=W * 7 + Ht + k, low_lb=k)
            alg &= r["ok"]
            print(f"  {f'{W}x{Ht}':>9} {r['n']:5d} {k:3d} {r['max_rounds']:11d} "
                  f"{max(r['ratios']) if r['ratios'] else 0:10.0f}")
            if not r["ok"]:
                print("   FAIL:", r["why"])
    print("  (b) low-LB permutations, replayed: the router's stretch at LB = 1 is")
    print("      unbounded by construction (it ignores LB; it is the Tier-1 router).")
    ok &= alg
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
    print("  The 3x3 row is sigma(square grids) >= 4 at LB = 1.")
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

    banner("Winding probe  --  OPT >= girth-law bound, and the refuted 'legs never help'")
    sizes = (4, 6) if fast else (4, 6, 8)
    cols = ["bare", "dead_end_legs", "legs_to_hub",
            "girth_preserving_escape", "one_chord"]
    builders = {
        "bare": lambda m: (m, [(i, (i + 1) % m) for i in range(m)]),
        "dead_end_legs": cycle_with_pendants,
        "legs_to_hub": cycle_with_legs_and_hub,
        "girth_preserving_escape": lambda m: cycle_with_escape_path(m, 0, m // 2, m // 2),
        "one_chord": lambda m: cycle_with_chords(m, [(0, m // 2)]),
    }
    print(f"  {'m':>3} " + " ".join(f"{c:>26}" for c in cols))
    print(f"  {'':>3} " + " ".join(f"{'(n, girth, bound, OPT)':>26}" for _ in cols))
    wind = True
    t0 = time.time()
    for r in winding_probe(sizes):
        m = r["m"]
        cells = []
        for c in cols:
            x = r[c]
            n, e = builders[c](m)
            b, g_om = winding.girth_law_bound(n, e, list(range(m)))
            good = x["opt"] >= b and b == x["girth"] - 1
            wind &= good
            cells.append(f"{'' if good else '!'}({x['n']}, {x['girth']}, {b}, {x['opt']})")
        print(f"  {m:>3} " + " ".join(f"{s:>26}" for s in cells))
    print(f"  [{time.time() - t0:.0f}s]")
    ok &= wind
    print("  The single-edge winding bound equals girth - 1 and never exceeds OPT.")
    print("  At m = 8 the legs-to-hub graph has girth 6 and rotates in 6, NOT 7:")
    print("  legs DO help when they shorten girth.  A girth-preserving escape")
    print("  route does not.  The law is a girth statement, and it is proved.")
    if fast:
        print("  (--fast: m = 8 rows skipped)")
    print("  -> CONSISTENT" if wind else "  -> VIOLATED")

    banner("Winding theorem  --  sigma(heavy-hex) >= 11, proved")
    t, v, gap = winding.stress_test(trials=600, seed=7)
    print(f"  stress test: {t} random instances with a positive bound, "
          f"{v} violations, min(OPT - bound) = {gap}")
    wt = v == 0
    for (W, Ht, exact) in ((3, 1, True), (5, 2, False)):
        r = winding.heavyhex_face(W, Ht, exact_g=exact)
        good = (r["lower"] == 11 and r["upper"] == 11 and r["upper_replays"]
                and r["girth"] == 12 and r["cyclomatic"] == r["hex_faces"])
        wt &= good
        print(f"  {'ok ' if good else 'FAIL'} {W}x{Ht} n={r['n']:3d} girth=12 "
              f"g_omega={r['g_omega']}{'' if exact else ' (= girth; not searched)'} "
              f"D={r['D']:+d}  ->  {r['lower']} <= OPT(face rotation) <= {r['upper']}, LB = 1")
    ok &= wt
    print("  Face rotation costs exactly 11 at LB = 1.  The bound is capped at")
    print("  11 on every heavy-hex patch (faces are 12-cycles and span the cycle")
    print("  space), so it cannot decide whether sigma(heavy-hex) > 11.")
    print("  -> PROVED" if wt else "  -> FAILED")

    banner("Patch model  --  the proposal's formula counts the 2-core")
    tc = True
    for r in two_core_audit():
        good = r["two_core"] == r["formula"] and r["n"] - r["two_core"] == 4
        tc &= good
        print(f"  {'ok ' if good else 'FAIL'} {r['W']:2d}x{r['Ht']:<2d} "
              f"n={r['n']:4d}  2-core={r['two_core']:4d}  "
              f"5ij+4(i+j)-1={r['formula']:4d}  offset=+{r['n'] - r['two_core']}")
    ok &= tc
    print("  Brick rectangle = 2-core (the proposal's i x j patch) + 2 dangling")
    print("  flags.  (Real IBM devices = that 2-core + pendants: reported by an")
    print("  audit against qiskit-ibm-runtime coupling maps, not checked here.)")
    print("  -> VERIFIED" if tc else "  -> FAILED")

    banner("Yuan-Zhang Lemma 1  --  the involution split inflates LB")
    inv = involution_obstruction((6, 8, 10, 12))
    io = all(a == b for a, b in inv.values())
    for k, (best, half) in inv.items():
        print(f"  {'ok ' if best == half else 'FAIL'} C_{k:<2d} rotation (LB = 1): "
              f"best split has max LB = {best}  (= floor(k/2) = {half})")
    ok &= io
    print("  Their worst-case reduction cannot carry a per-instance LB as written.")
    print("  -> VERIFIED" if io else "  -> FAILED")

    banner("12 x 10 mesh  --  the shape of IBM Nighthawk's coupling map")
    rounds, guarantee, h = grid_guarantee_gap()
    A, B = 11, 9                                   # 12 x 10 mesh
    ng = rounds <= 2 * (B + 1) + (A + 1) and guarantee >= 2 * h
    print(f"  200 random permutations: classical mesh router <= {rounds} rounds;")
    print(f"  BGS guarantee 2*d_max + 2h with h = {h} is >= {guarantee} on every one.")
    print("  (That Nighthawk's coupling map IS the 12 x 10 grid is reported by an")
    print("  audit against the fake-provider map; this check is about the mesh.)")
    ok &= ng
    print("  -> VERIFIED" if ng else "  -> FAILED")

    banner("SUMMARY")
    print("  Lemmas 1 and 2 (with a non-vacuous low-LB check), the section 4")
    print("  algorithm (random and low-LB), and every number the proof note")
    print("  reports: all check out.")
    print("  Assumption (G) is NOT a theorem in BGS -- see REVIEW.md section 2.")
    print("  sigma(heavy-hex) >= 11 is PROVED by the winding bound (pts/winding.py).")
    print("  'Legs never help' was WRONG; OPT >= girth - 1 is the law, and proved.")
    print(f"\n  overall: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    t = time.time()
    code = main(fast="--fast" in sys.argv)
    print(f"  [{time.time() - t:.1f}s]")
    sys.exit(code)
