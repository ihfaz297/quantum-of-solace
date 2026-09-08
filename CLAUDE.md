# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

An undergraduate thesis project on **parallel token swapping (PTS) on IBM heavy-hex
graphs**: given a graph with one token per vertex, reach a target permutation in
the fewest *rounds*, each round a matching of simultaneous swaps. The repository
holds the thesis documents and `pts/`, a pure-Python package whose job is to
machine-check every claim the documents make.

`REFINED_PROPOSAL.md` is the authoritative statement of what is proved, what is
verified, what is open, and why. `REVIEW.md` is the audit of the older proof note
`heavy-hex-approximation-proof.md` (which contains known errors — see REVIEW.md
§2, §4, §6 before trusting anything in it). `fork.txt.txt` is a superseded, wrong
proof attempt kept out of version control on purpose: **never `git add` it**.
`audit_girth.py` at the root is a leftover scratch script.

## Commands

Python 3.13, standard library only, except `pts/sat.py` which needs
`pip install python-sat` (CaDiCaL bindings). No build step.

```bash
python -m pts.check_all          # every machine check, ~3 min (the m = 8 winding rows dominate)
python -m pts.check_all --fast   # same minus the m = 8 rows, ~5-15 s
python -m pts.winding            # the winding lower bound: stress test + heavy-hex face
python -m pts.sat                # SAT encoder: validation vs exact, face certificate, RQ1 n=21
python -m pts.sat --big          # ... plus the n = 35 instance (~1 s)
python -m pts.scaling            # diameter and lifting-constant scaling to n = 480
python -m pts.check_lemma1       # or check_lemma2 / check_algorithm, individually
```

Run a single check from the shell:

```bash
python -c "from pts.check_lemma1 import check; print(check(11, 5))"
python -c "from pts.check_lemma2 import check; print(check(7, 3, trials=10, seed=1, low_lb=2))"
python -c "from pts.sat import check, rq1_instances; i = rq1_instances()[0]; print(check(i['n'], i['edges'], i['target'], 11)[:3])"
```

`check_all` exits non-zero on any failure and prints `overall: PASS/FAIL`. Its
output is block-buffered when redirected; set `PYTHONUNBUFFERED=1` to watch a
long run. `check_all` skips the SAT section (without failing) if `python-sat` is
absent.

## Architecture

**The graph model.** `heavyhex.HeavyHex(W, Ht)` builds `X = S(H)`: `H` is the
brick wall on `[0,W] x [0,Ht]` (all horizontal edges; vertical edges where
`x + y` is even), `S` subdivides every edge. `W` must be odd. Vertices are tuples
`('b', x, y)` (branch) and `('s', (p, q))` (subdivision of H-edge `p < q`). The
class also carries the **cell quotient** `phi: V(X) -> Gamma` onto the
`(A+1) x (B+1)` grid, `A = (W-1)/2`, `B = Ht`, with fibers of size 3-5.
The brick rectangle has exactly 4 more vertices than the "idealised `i x j`
patch" the thesis proposal counts (`5ij + 4(i+j) - 1` is the 2-core;
`sat.two_core` extracts it). Real IBM devices are that 2-core plus pendants.

**The reduction pipeline** (the thesis's Theorem A):
`heavyhex` (quotient) -> `check_lemma2.cell_permutations` (pad the cell-demand
multigraph to 5-regular, `koenig.decompose` into five grid permutations
`sigma_r`, each with `LB_Gamma(sigma_r) <= LB_X(pi)`) -> `gridroute.route`
(the classical Alon-Chung-Graham column-row-column mesh router; not a
contribution) -> `router.solve` (five phases; each mesh round is *lifted* to `X`
by `pathsort.swap_endpoints` along shortest paths, conflict-coloured greedily) ->
`router.replay` (re-simulates the schedule from the raw edge set, independent of
the router's bookkeeping). `router.Stats` records the measured constants
(`lift_cost` = `c3`, colours, path length) that the written proof leaves as `O(1)`.

**Exact solvers.** `exact.solve` is bidirectional BFS over token placements;
usable to `n ~ 13` at depth 6-7 (the `C_8` + hub instance takes ~90 s).
`sat.check` is bounded model checking ("schedule of `<= T` rounds?") via
CaDiCaL; `n = 35`, `T = 11` takes about a second. Every SAT answer is replayed
independently of the solver. Prefer `sat` for anything beyond `n = 12`.

**Lower bounds.** `winding.bound` implements the winding (cohomological)
theorem `OPT >= g_omega - max|Q_v|`; `winding.girth_law_bound` is its
single-edge specialisation `OPT(rotate a cycle) >= girth - 1`;
`winding.heavyhex_face` is the `sigma(heavy-hex) >= 11` instance. The bound is
provably capped at 11 on any heavy-hex patch (faces span the cycle space).

**Instance builders and probes** live in `experiments.py` (rotation targets,
cycles with pendants / hubs / chords / escape paths, grids, `girth`, the 2-core
audit, the Yuan-Zhang involution obstruction, the 12x10 mesh comparison).
`check_*.py` are the assertion layers over all of the above; `check_all.py`
sequences them and is what the documents' **VERIFIED** labels refer to.

## Conventions that bite

- **Two permutation conventions.** `router.solve(g, pi)` takes `pi[v] = target
  vertex of the token starting at v`. `exact.solve` and `sat.check` take
  `target[i] = token that must END on vertex i` (the inverse). `experiments.
  rotate_target` and `sat.rotation_target` produce the latter. Mixing them
  silently routes the inverse permutation.
- **Random permutations make Lemma 2's check vacuous** (their `LB` exceeds
  `diam(Gamma)`). Use `check_lemma2.low_lb_permutation` (compose `k` random
  matchings) for anything that must be able to fail. Same for router stretch:
  the router ignores `LB` by construction, so only low-`LB` instances show it.
- **Claim labels are load-bearing.** The documents use PROVED / VERIFIED / NOT
  NEW / CONJECTURED / OPEN, and every VERIFIED names a `check_all` section. Do
  not label something VERIFIED unless the suite actually runs it; facts from
  external audits are marked `[audit]`. When adding a check, make sure it *can*
  fail on the distribution it runs on.
- **Do not reintroduce "legs never help".** `C_8` with legs to a hub rotates in
  6, not 7 (girth drops to 6). The law is `OPT >= girth - 1`, and the winding
  probe must include `m = 8`.
- `girth()` returns `inf` for forests (`A = 0` or `B = 0` patches are trees).
- Literature facts that are easy to get wrong: BGS's grid bound is
  `2*OPT + 2h` (not constant-factor) and the grid stretch factor is open in
  their paper; `rt(heavy-hex) = Theta(diam)` is a corollary of Yuan & Zhang
  2025 ("brick wall" vocabulary); Alpert et al.'s "Theorem 27" is disputed —
  cite only their Theorem 4. Details and sources in REVIEW.md §2-3.

## Git

The owner sometimes commits and pushes from this working tree mid-session, so
run `git fetch && git status` before committing. `__pycache__/` is ignored.
Never stage `fork.txt.txt`.
