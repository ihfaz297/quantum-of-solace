# Review of the heavy-hex approximation note

Scope: `heavy-hex-approximation-proof.md`, `fork.txt.txt`, and
`thesis-proposal-parallel-token-swapping.docx`. Every claim called *verified*
or *proved* below is checked by the code in [pts/](pts/); run
`python -m pts.check_all` (about three minutes; `--fast` for five seconds).

**Change log.** This is the second version. The first version, written before
a six-thread literature and audit sweep, was wrong in three places, and the
corrections are the most useful content here:

1. It said "legs never help, only chords do". **False** — `C_8` with legs to a
   hub rotates in 6, not 7. The law is `OPT >= girth - 1`, and it is now proved
   (section 6), which also promotes `sigma(heavy-hex) >= 11` from conjecture
   to theorem.
2. It said Tier 1, `rt(X) = Theta(diam X)`, was the thing to write up. It is a
   corollary of a 2025 paper that never uses the word "hex" (section 3).
3. It said the proposal's Section 3 characterisation of BGS was fine. It is
   wrong for grids (section 2), and the proposal's size formula, which I
   flagged as not matching IBM devices, is in fact exactly right for what it
   counts (section 7).

---

## 1. Verdict

The **method is sound and worth writing up**. The bounded-fiber quotient is the
right idea, it is correctly executed, and three independent audits could not
break Lemmas 1, 2 or 3 or the section 4 correctness argument. The five-phase
algorithm is implemented in [pts/router.py](pts/router.py) and replayed from
scratch on random and low-`LB` permutations up to n = 480 here (n = 2163 in
the audit), with the occupancy invariant never breaking.

The **headline theorem is overclaimed**, for one reason: Assumption (G) is not
a theorem in BGS, and may be false. `sigma(heavy-hex) < infinity` does not
follow (section 2).

What the thesis actually owns, as of this review:

| claim | status |
|---|---|
| Reduction theorem: heavy-hex PTS -> grid PTS with `LB_Gamma(sigma_r) <= LB_X(pi)` | **proved**, machine-verified; the per-instance transfer is **new** (section 3) |
| `rt(X) = Theta(diam X)` | proved here; **already a corollary of Yuan-Zhang 2025** (section 3) |
| `sigma(X) = O(h_Gamma)`, `h_Gamma` the short side of the quotient grid | **proved** via BGS Remark 14 (section 3) |
| `sigma(X) = O(1)` | **open**; equivalent-or-harder than BGS's open grid question (section 3) |
| `sigma(heavy-hex) >= 11` | **proved** by a new winding lower bound (section 6) |
| `sigma(heavy-hex) = 11`? | **open**; the winding bound provably cannot decide it (section 6) |

---

## 2. The one real error: Assumption (G)

The note assumes:

> **Assumption (G).** There is a constant `a` and a polynomial-time algorithm
> that routes any permutation `sigma` of an `R x C` grid graph in at most
> `a * LB_grid(sigma)` rounds.

and calls this "exactly Lemma 3 of the proposal, i.e. the BGS grid result".
It is not. From arXiv:2411.18581v2 (Bansal, Gunluk & Shapley), verified
verbatim by two audits against the extracted full text:

| what the note assumes | what BGS actually prove |
|---|---|
| `<= a * LB_grid(sigma)`, multiplicative in **LB** | **Thm 4(b):** for an `h x n` grid with `h <= n`, a solution of value `<= 2*OPT + 2h` — multiplicative in **OPT**, additive in the short side `h` |
| grid stretch factor is `O(1)` | **Remark 14** (a proved corollary of the Thm 4(b) proof): the same algorithm gives `<= 2*d_max + 2h`, so the stretch factor of `d_max` on grids "can be bounded by `O(h)`" |
| — | **Section 8:** "While we provide an upper bound for the stretch factor on grid graphs, pinning it down asymptotically remains an open question." Table 1's stretch column is an em-dash for grids and ladders |
| — | **Thm 5(b):** the stretch factor of `d_max` on `n`-cycles is between `n-1` and `n` |

So `sigma(grid) = O(1)` is **open**, and it is open in the same paper the note
cites for it. Section 5 of the note already spotted the smell ("the stretch
factor of the *cycle* family is infinite ... so BGS's constant-factor
approximation for cycles cannot be relative to `LB`") and that instinct was
right; it just resolves the wrong way.

Three further facts from the paper, all load-bearing:

- **`2*OPT + 2h` is not a constant-factor approximation.** The additive term
  grows with the instance: at `OPT = O(1)` and large `h` the ratio is unbounded.
  BGS's cycle (`2*OPT` for even `n`, `2*OPT + 1` for odd), subdivided-star
  (`<= 5*OPT + 1`) and ladder (`2*OPT + 2`) bounds are genuinely
  constant-factor; the general grid bound is not. The thesis proposal's Section 3 sentence — "constant-factor
  approximations for cycles, subdivided stars, and grids" — is therefore wrong
  for grids. (The first version of this review said it was fine. It is not.)
- **BGS explicitly refute a prior O(1)-approximation claim on grids** (Section
  1.3): "the introduction of [1] claims that [9] provided an O(1)-approximation
  algorithm for the problem on grid graphs. However, this claim is incorrect
  since [9] considers a variant ... where one is allowed to rotate the tokens
  along a cycle in one step." [9] is Demaine, Fekete, Keldenich, Meijer &
  Scheffer, *Coordinated motion planning: reconfiguring a swarm of labeled
  robots with bounded stretch* (SoCG 2018 / SIAM J. Comput. 2019), who prove
  constant stretch on grids in a model that forbids swaps but rotates a whole
  cycle in one step. That is exactly the shape of Assumption (G), refuted in
  print by the people the note cites for it. Alpert et al., *Routing by
  matching on convex pieces of grid graphs* (Comp. Geom. 2022), pose the same
  question as their open Question 1 and point at Demaine et al. "with a
  slightly different routing setup". Two independent groups, same open problem.
- **Is (G) true at all?** Nobody knows. If `sigma(grid)` is unbounded, then
  `sigma(heavy-hex) < infinity` is not merely unproved but unreachable by the
  quotient route, and Tier 2's `O(h_Gamma)` is the honest ceiling of what this
  method can give. Put *that*, not the `>= 11` bound, at the centre of the risk
  section.

Citation hygiene: `h` is the SHORT side (`h <= n` is a hypothesis of Thm 4;
`h >= 3` appears in the Section 1.2 statement but the Section 6 proof does not
use it, and Thm 4(a) covers `h = 2` with `2*OPT + 2`). Thm 4(b) is stated for
the **full rectangle** `{1..h} x {1..n}`, so a staggered patch whose quotient
is a polyomino needs a separate argument. Remark numbering shifted between
arXiv v1 and v2 — cite "Remark 14 (v2)". The journal reference (Discrete
Applied Mathematics 377, 480-497, 2025, DOI 10.1016/j.dam.2025.08.005) is
Crossref-confirmed but the text behind the paywall was not compared to v2.

---

## 3. What survives, and what is actually new

The quotient is a *reduction*, and it is unaffected by any of the above. State
it that way and the note gets stronger, not weaker.

> **Reduction theorem (proved, verified).** Let `X = S(H)` on the brick
> rectangle `[0,W] x [0,Ht]` with `W` odd, and `Gamma` its quotient grid on
> `{0..(W-1)/2} x {0..Ht}`. Given any mesh router `A` using `f(sigma)` rounds
> on a permutation `sigma` of `Gamma`, there is a polynomial-time algorithm
> routing any permutation `pi` of `V(X)` in at most
>
> ```
> 5 * c3 * max_r f(sigma_r)  +  c4     rounds,
> ```
>
> where `sigma_1 ... sigma_5` are the cell-permutations of Lemma 2, each
> satisfying **`LB_Gamma(sigma_r) <= LB_X(pi)`**, and `c3`, `c4` are absolute
> constants (measured 14 and 5).

**The bold inequality is the contribution.** Everything else in this section
is a corollary of it plus a citation, and one of those corollaries turns out
to be already known.

**Tier 1 — `rt(X) = Theta(diam X)`, unconditional, but not new.** Plug in the
column-row-column mesh router ([pts/gridroute.py](pts/gridroute.py)), which is
Alon-Chung-Graham's product theorem `rt(G x H) <= 2 rt(G) + rt(H)` (1994; see
Alpert et al. 2022, Theorem 4 — two audits disagree on whether their "Theorem
27" exists, so only Theorem 4 is cited), and the reduction gives `O(A + B)`
rounds for every permutation; `A + B <= diam(X) <= 4(A + B + 1)` by Lemma 1;
`rt >= diam` is trivial.

But Pei Yuan & Shengyu Zhang, *Full Characterization of the Depth Overhead for
Quantum Circuit Compilation with Arbitrary Qubit Connectivity Constraint*,
Quantum 9, 1757 (2025), arXiv:2402.02403, **Theorem 9** bound the routing
number of `Brickwall^{b1,b2}` and write "in IBM's brick wall chips, b1 = 3 and
b2 = 5." Two audits re-extracted the PDF independently: the quote is verbatim.
`X`'s interior bricks are exactly their 12-cycle bricks (5 vertices per
horizontal side, 3 per vertical). With `rt >= diam`, their theorem already
gives `rt = Theta(diam)`. They never write "hex", "token swapping" or "stretch
factor"; BGS do not cite them and they do not cite BGS. The first version of
this review searched by the name the token-swapping literature uses and
missed them.

Three precise caveats on the scoop, each of which matters for how the thesis
words it:

- *The identification is structural, not exact.* `HeavyHex(W, Ht)` is a
  brick-wall **patch**: it has two degree-1 pendant vertices and, with `W`
  odd, half-bricks at the ends. Routing number is not monotone under
  subgraphs, so Theorem 9 applies to `X` modulo a boundary argument that is
  probably a paragraph and has not been written. Defensible sentence: "heavy-hex
  patches are brick-wall patches in the sense of [YZ25], whose
  `Brickwall^{3,5}` is the boundary-free idealisation."
- *Constants: do not argue them.* YZ's implied constant, read off their proof,
  is several hundred times `diam`; this router's **measured** ratio is about 23
  and its **proved** constant is worse than theirs. Proved-vs-proved they win,
  measured-vs-implied this wins, neither is presentable.
- *Their reduction provably cannot be made instance-wise.* YZ's Lemma 1 first
  splits `pi = tau_1 . tau_2` into two involutions. For the rotation of `C_k`
  (`LB = 1`), the best decomposition has `max(LB(tau_1), LB(tau_2)) = floor(k/2)`
  — verified by enumeration for `k = 6, 8` this session, and by the audit for
  `k = 6..12`. Heavy-hex contains cycles of length `Theta(sqrt n)`, so their
  route inflates `LB` without bound. **`LB_Gamma(sigma_r) <= LB_X(pi)` is not
  obtainable from their machinery.** That is the novelty claim, and it now
  comes with a proof of why the closest prior work cannot have it.

**Tier 2 — `sigma(X) = O(h_Gamma)`, unconditional.** Plug in BGS Algorithm 6
with its Remark 14 bound `2*d_max + 2h`: rounds `<= 5*c3*(2*LB_X(pi) + 2*h_Gamma)
+ c4`, so `OPT_X(pi) = O(h_Gamma) * LB_X(pi)` for every `pi != id`, with
`h_Gamma = min((W+1)/2, Ht+1)` the short side of the quotient. This is a
genuine instance-wise guarantee for heavy-hex, parameterised by the short
side; nothing like it was known. Hypotheses to carry: Thm 4(b) is for full
rectangles (polyomino quotients of staggered patches need an extension), and
thin patches with short side 2 need Thm 4(a) instead. Do not merge Tiers 1 and
2 into one statement: for high-`LB` permutations Tier 1's diameter bound is the
better of the two, so the right statement is the minimum.

**Tier 3 — `sigma(grid) = O(1)  =>  sigma(heavy-hex) = O(1)`.** One-way. The
converse — a reduction from grid PTS to heavy-hex PTS — is not established,
so it is **not** correct to say RQ2 is "equivalent" to BGS's open problem
(the first version of this review did). It sits downstream of it.

**Two cheap extras the reduction gives for free.** (a) BGS Theorem 6 proves
the same bounds for the *colored* and *incomplete* variants (indistinguishable
tokens; empty positions). Lemma 2's Koenig padding is label-agnostic, so both
should transfer to heavy-hex directly — and the incomplete case is exactly
dead qubits on a real device. (b) An open problem worth posing in print:
*is `rt(G) = O(rt(H))` whenever `G` has a quotient onto `H` with fibers of
bounded size and bounded diameter?* No such theorem exists in the
routing-number literature (the audit checked ACG products, spanning-subgraph
monotonicity, Banerjee-Richards' `h`-connectivity bound, Alpert et al.'s
induced-subgraph lemma, and Yuan-Zhang's Theorem 8 edge-augmentation
transfer — none applies to heavy-hex). The reduction proves the heavy-hex
case; asking the general question is what gets a note cited.

---

## 4. Machine verification

The note says "*Verified computationally*" twice but shipped no code. It does
now, and the audit found one of the checks was vacuous as first written.

| claim | result |
|---|---|
| Lemma 1: `phi` partitions `V(X)`, fibers of size <= 5, each a tree of diameter <= 4, quotient **exactly** the grid, `d_Gamma <= d_X <= 4(d_Gamma+1)`, girth 12 | **verified**, 36 shapes to n = 168 here; audit extended to n = 583 |
| Lemma 2: padded demand multigraph is 5-regular, splits into 5 cell-permutations with `max_p d_Gamma(p, sigma_r(p)) <= LB_X(pi)` | **verified** on 480 low-`LB` instances (`LB in {1,2,3,4}`), where it can fail; the original 300-random-permutation check was **vacuous** (`LB_X` of a random `pi` exceeds `diam(Gamma)`, so the inequality could not fail) |
| Section 4 algorithm realises `pi` | **verified** by independent replay, random and low-`LB`, to n = 480 here, n = 2163 in the audit |
| Section 5 table (three rotation instances) | **reproduced exactly**: 3, 4, 5 |
| `OPT(C_m` rotate by one`) = m - 1` | **reproduced** for `m = 4..8` |
| winding theorem (section 6) | **proved**; stress-tested on 1178 random instances in the audit and 466 here, 0 violations, bound attained |
| `sigma(heavy-hex) >= 11` | **proved**: face rotation is `11 <= OPT <= 11` at `LB = 1`, both halves machine-checked |
| proposal formula `n = 5ij + 4(i+j) - 1` | **verified** as the 2-core count of the brick rectangle at every size |

Three gaps in the note's proofs, all one-line fixes and none affecting truth:

- **Lemma 1.2 needs its converse.** As stated it gives quotient `⊆` grid. The
  proof of Lemma 1.3 opens "adjacent cells are joined by an `X`-edge", which
  is quotient `⊇` grid, and is nowhere proved. Add "and every edge of `Gamma`
  is the image of an `X`-edge" to 1.2 (the code checks equality).
- **Lemma 1.3's proof derives `5*d_Gamma + 4`**, which does not imply the
  stated `4(d_Gamma + 1)`. The stated bound is true and tight (measured
  `max(d_X - 4*d_Gamma) = 4` on every shape); the proof needs one more line.
- **Lemma 3's conflict count is not even the right crude count** (the
  neighbourhood radius is 9, not 8, so the conflict radius is 18 or 19, not
  16). It does not matter — state "conflicts lie within `O(1)` grid distance,
  hence `O(1)` colours" and stop quoting a number.

---

## 5. The `O(1)` constants, measured

| quantity | proof's bound | measured (n <= 480) |
|---|---|---|
| `X`-path length per grid edge | <= 9 vertices | **9** — tight |
| conflict-graph colours | "1090" (see section 4) | **2** |
| `X`-rounds per grid round (`c3`) | "9810" | **<= 14**, pinned from n = 39 on; mean turns over near 8.8 |
| final within-cell phase (`c4`) | `O(1)` | **5** |
| `rounds / diam X`, random `pi` | — | plateaus near **23** (n = 16 to 480) |

Note the last row is a *diameter* measurement, not a stretch measurement:
random permutations have `LB ~ diam`. The implemented router has **unbounded
stretch by construction** — on a single adjacent transposition (`LB = 1`) it
uses 51, 207, 293, 357, 439 rounds on `3x1 ... 11x5`. That is expected (it is
the Tier 1 router, which ignores `LB`), and it is exactly why Tier 2 needs BGS
Algorithm 6 plugged in instead. Say it in the write-up before a referee does.

---

## 6. The lower bound: `sigma(heavy-hex) >= 11` is now a theorem

The note asserts `11 <= sigma(heavy-hex)` and proves it nowhere. The first
version of this review supported it with an experiment and a slogan — "legs
never help, only chords do" — that turned out to be **false**: the audit ran
`cycle_with_legs_and_hub(8)` from this repo's own `experiments.py` and got
`OPT = 6 < 7`, with a replayed witness schedule that genuinely routes tokens
out through the legs. The reason `m = 4, 6` looked safe is that those hub
graphs have girth `m`; from `m = 8` the hub creates a 6-cycle and girth drops.
The suite ran only `m = 4, 6` and so hid a refutation its own code could
produce. Fixed: [pts/check_all.py](pts/check_all.py) now runs `m = 8` and tests
the right predicate.

The right predicate is **`OPT(rotate a cycle by one) >= girth - 1`**, and it is
proved in [pts/winding.py](pts/winding.py):

> **Winding bound.** Let `omega : E -> Z` be antisymmetric on oriented edges.
> For each `v` pick a path `Q_v` from `v` to `pi(v)`; set `delta_v = omega(Q_v)`,
> `D = sum_v delta_v`, and `g_omega = min{ |C| : C a cycle with omega(C) != 0 }`.
> If `D != 0` then `OPT >= g_omega - max_v |Q_v|`.
>
> *Proof.* Let `P_v` be the walk token `v` takes in a `T`-round schedule;
> `|P_v| <= T`. Each round traverses every matched edge once in each direction,
> so `sum_v omega(P_v) = 0`, hence `sum_v omega(P_v . Q_v^{-1}) = -D != 0`, so
> some closed walk `P_v . Q_v^{-1}` has nonzero `omega`, so it contains a
> simple cycle with nonzero `omega`, of length `>= g_omega`. Then
> `|P_v| >= g_omega - |Q_v|`. QED.

For a hexagonal face of `X` take `omega` = signed crossings of a ray from a
point inside the face: `D = +-1`, `max |Q_v| = 1`, `g_omega >= girth(X) = 12`,
so `OPT >= 11`; the eleven adjacent transpositions along the face give
`OPT <= 11`. Both halves are replayed in code. Hence **face rotation costs
exactly 11 at `LB = 1`, and `sigma(heavy-hex) >= 11`, unconditionally.**

What to say about it, precisely:

- *Provenance.* At `G = C_n` it is exactly Li, Lu & Yang's Lemma 2.1 (SIAM J.
  Discrete Math. 24(4), 2010; `rt(C_n) = n - 1` is their Theorem 1.2) and the
  charging argument BGS re-derive for Theorem 5(b). The contribution is that
  it needs no product structure: LLY's only extension to a cycle inside a
  larger graph (Lemma 2.2) needs a Cartesian product `C_n x G`, which heavy-hex
  is not. Position it as "the LLY charging argument freed from the product
  structure", not as an unprecedented tool.
- *Novelty: plausible, not established.* The audit read a clean copy of
  Alon-Chung-Graham 1994 (it is not there) and BGS (not there). Not yet swept:
  sequential token swapping, coordinated motion planning, sorting networks on
  graphs, and heavy-hex-specific routing (arXiv:2306.05385). Do that sweep
  before calling it new.
- *What it is not.* It is not "the first bound to escape BGS Theorem 1's
  barrier" — every graph-aware bound (ACG's cut bounds, BGS's own
  subdivided-star argument) already does. The defensible narrower claim: it is
  the first bound in this literature sensitive to the homology class of the
  permutation, and the first that is non-trivial on an instance where
  `d_max`, every cut/congestion bound, and ACG's total-work bound
  `D/(2 mu(G))` are all simultaneously `O(1)`.
- *Ceiling — state it as a limitation.* On a planar graph the bounded faces
  generate the cycle space, so an `omega` vanishing on every face is a
  coboundary and forces `D = 0`. Hence `D != 0` requires `omega(F) != 0` for
  some face, so `g_omega <= |F|`, and on heavy-hex (every face a 12-cycle;
  face count = cyclomatic number, checked) the bound can **never exceed 11**.
  It cannot decide whether `sigma(heavy-hex) = 11`.
- *Why that question is open.* The `3x3` grid boundary rotation costs 4, one
  more than its winding bound of 3 — an enclosing cycle can beat `girth - 1`.
  The heavy-hex analogues are the 20-cycle bounding two fused faces (n ~ 22)
  and the 24-cycle around a branch vertex (n ~ 28); both exist in
  `HeavyHex(5,2)`. If either exceeds 11, `sigma > 11`. These are exactly the
  instances BFS cannot reach and the SAT encoding is for (section 8).
- *On grids.* `sigma(grid family) >= 4` from the exhaustive `3x3` search (all
  229 `LB <= 1` permutations; max `OPT = 4`). `>= 3` is **not** new: `C_4` is
  the `2x2` grid, so BGS Theorem 5(b) gives it. Both are `O(1)` against BGS's
  asymptotic question.

The `>= girth - 1` law survived every adversarial probe the audit could
construct off the cycle-with-attachments family: `Q_3`, `K_{3,3}`, Petersen,
and girth-preserving escape paths at `m = 6, 8` — all exactly `girth - 1`.

**Section 5 of the note reads its own table backwards.** Its slogan "rotation
cost tracks girth, not cycle length" is right, but it used it to argue
rotations are *cheap* in heavy-hex. Girth 12 with chord-free faces makes them
maximally *expensive*: that is the `>= 11` lower bound, not evidence for a
finite upper bound. And none of the table's three rows is a heavy-hex graph;
the fused-hexagon row rotates in 5 because it has a chord (girth 6), a feature
`X` lacks.

**`fork.txt.txt`.** Superseded. Its Lemma 2 (brick wall `H` embeds in the
square grid with length-3 detours) is actually correct; its Lemma 1
("gather" four tokens onto one vertex) is not an operation. Section 6 of the
note attacks a claim about `X` that the file only makes about `H`. The
bipartition obstruction in section 1 is still correct and worth keeping.

---

## 7. The thesis proposal

The proposal is **not out of line** — it is unusually well built, and its
"Scope caveat" (PTS is not qubit routing) is the best paragraph in any of the
documents. The edits, grouped by section, with the finding behind each:

**Section 1-2, the object.**
- `n = 5ij + 4(i+j) - 1` is **correct**: it counts the 2-core of the brick
  rectangle (verified constructively; `pts/heavyhex.py` builds the full
  rectangle, which has exactly 4 more vertices — two dangling flags). Label it
  as the 2-core count. Every current IBM heavy-hex device is that 2-core plus
  pendant qubits, by graph isomorphism (audit): Falcon-27 = `1x2` patch + 6;
  Eagle-r3-127 = `3x6` patch (125) + 2; Heron-r1-133 = `3x6` + 8;
  Heron-r2/r3-156 = `3x7` patch (144) + 12. Pendants hang on degree-2 boundary
  branch vertices. Girth is 12 on every one. Eagle-r1 is a *different*
  lattice. Say how the pendants are handled — they are outside `S(H)`.
- "heavy-hex, the topology IBM ships" is now half true. **IBM Nighthawk
  (120 qubits, shipped Dec 2025) is exactly the `12 x 10` grid graph** (edge-set
  identity against the fake-provider coupling map). Eagle-127 is retired. BGS
  Thm 4(b) applies to Nighthawk verbatim — but with `h = 10` its additive term
  `2h = 20` equals the diameter, so the guarantee is near-vacuous at small
  `OPT`. Nighthawk also breaks "bipartite max-degree-3, a class containing
  heavy-hex" (it has degree-4 vertices).

**Section 3, related work.**
- Fix the BGS sentence: constant-factor for cycles and subdivided stars;
  `2*OPT + 2h` for grids, additive in the short side, with the grid stretch
  factor left open (Section 8, verbatim above). Add their own heavy-hex
  disclaimer (v2 only): designing algorithms for "more complex graph
  topologies (including IBM's heavy hex ...) using algorithms for its
  subgraphs provided in this paper requires further research."
- Add Yuan & Zhang as closest prior work (worst-case routing number of
  brick walls), and the involution obstruction as the reason it is not
  instance-wise.
- Add Alon-Chung-Graham's product theorem (via Alpert et al. 2022, Thms 4
  and 27) for the mesh router; Li-Lu-Yang 2010 for `rt(C_n) = n - 1`;
  He-Valentin-Yin-Yu (arXiv:1404.1851) for extremality of the rotation.
- Fix the Weidenfeller gloss: `n + sqrt(n) + 61` is the number of SWAP layers
  a *fixed swap strategy* needs to reach full all-to-all connectivity —
  `Theta(n)`, near-optimal for that task, and neither a diameter bound nor a
  routing number. "Achieving full connectivity" is right; "a worst-case
  diameter bound" is not.
- Fix the hardness sentence: NP-complete for fixed `k >= 3` on bipartite
  max-degree-**4** graphs, and for fixed `k >= 5` on bipartite max-degree-**3**
  graphs (Kawahara, Saitoh & Yoshinaka, JGAA 23(1), 2019, Thms 3 and 4; Thm 3
  independently by Banerjee & Richards, arXiv:1706.09355, FCT 2017);
  `k <= 2` is in P. "Three rounds on degree 3" conflates the two.
- Add Demaine et al. 2018/19 and Alpert et al. 2022 as the two independent
  statements that bounded stretch for routing-by-matchings on grids is open,
  and the one-step-cycle-rotation model as the reason Demaine's constant
  stretch does not transfer.
- The "2025 benchmarking study" is Li, Zhou & Feng, *QKNOB*, IEEE TQE 6
  (2025). Its circuits are constructed, not random; devices retired; Qiskit
  0.33. Delete the inference "wins over SABRE come from exploiting structure"
  — the paper tests no structure-exploiting router, so it cannot speak to it.
  Add QUBIKOS (arXiv:2502.08839): LightSABRE is 63x off known optimal SWAP
  count — the strongest available motivation for guarantees.
- "SABRE is the Qiskit default": the shipped algorithm is LightSABRE
  (arXiv:2409.08368) since Qiskit 1.2, changed again in 2.5. TOQM is dead
  (archived 2024); drop it. rustworkx ships Miltzow's *sequential*
  4-approximation as `permutation.token_swapper`, so "no public
  implementation" needs the word *parallel*.

**Section 4, research questions.**
- RQ1: "We prove `sigma(heavy-hex) >= 11`; is it tight?" — and say the
  winding bound cannot answer that.
- RQ2: "Does heavy-hex PTS reduce to grid PTS preserving the per-instance
  geodesic lower bound?" — answered yes; the open half is whether the
  reduction is tight, and that sits downstream of BGS's open grid question.
- RQ3: split. As written it violates the Scope caveat (BGS routes a
  permutation, SABRE routes a circuit). RQ3a: permutation routers against
  permutation routers on measured rounds vs `LB` — `permutation.token_swapper`
  (sequential count objective; the only coupling-map-aware Qiskit baseline;
  `permutation.acg` and `permutation.kms` ignore the coupling map), the mesh
  router here, and exact optima on small instances. RQ3b: does a better
  permutation router move end-to-end compiled depth at all.

**Section 5, approach.**
- Phase 3 primary route: replace "unfolding" with the quotient. It works.
- Phase 2: embedding the NP-completeness reduction into heavy-hex is **not
  cheap**: planar hardness for uncoloured PTS is itself open (KSY's only
  planar result is for the 3-coloured variant), the degree-3 gadget contains
  a 10-cycle which girth-12 heavy-hex forbids. Move it out of the week-16
  path.
- Phase 1: the SAT encoding is for the enclosing-cycle instances (section 8),
  not for the face — the face is proved. Ship the router as a
  `permutation.<name>` HighLevelSynthesisPlugin under `qiskit.synthesis`, not
  only a bare TransformationPass. Pin `SabreSwap(trials=...)` (it defaults to
  CPU count) and `QISKIT_TRANSPILER_SEED`; publish a lockfile — Qiskit 2.0,
  pytket 2.0, mqt.qmap 3.0 and mqt.bench 2.0 all broke API in 2025.
- Phase 4: `optimization_level=3` measures resynthesis, not routing, and
  `ElidePermutations` can delete the very PermutationGates a PTS router emits.
  Report a routing-isolated setting and the end-to-end preset. Target Heron
  r2/r3 (156) and Nighthawk (120), not Eagle. Use Benchpress (Nation et al.,
  Nature Comput. Sci. 2025) as the harness or comparison point; MQT Bench v2
  ships no Nighthawk target, so build it from the fake-provider map. If any
  fidelity claim is made, compute a calibrated estimate; depth and count
  correlate poorly with measured success (arXiv:2607.03275).

**Section 6, decision gate.** "A proven stretch-factor bound for at least one
heavy-hex family" is already met (`>= 11`, and Tier 2's `O(h_Gamma)`). Reset
the gate to the live question: does the 20- or 24-cycle instance exceed 11
(SAT), or is there a matching upper bound?

**Section 8, success criteria.** Threshold: implementation, benchmark study,
independent verification of `rt(X) = Theta(diam)` reconciled with Yuan-Zhang.
Target: the reduction theorem with instance-wise `LB` transfer; the winding
bound with `sigma(heavy-hex) >= 11` and `sigma(grid) >= 4` as corollaries.
Out of scope, stated: `sigma(heavy-hex) = O(1)`.

**Section 9, risks.** Scooping: not "top risk" (the table is unranked), and the
evidence is that BGS has 0-1 citations across three indices and no follow-up.
But add the risk that actually bit: *the adjacent literature restates the
result in vocabulary the monitor does not cover.* Yuan-Zhang has 15 Semantic
Scholar citers including active routing groups, and there are 2026
routing-number papers for quantum hardware using quotient machinery. Fix the
monitor: "routing number", "routing via matchings", "permutation routing",
"brick wall" + routing, citations to *both* arXiv:2411.18581 and
arXiv:2402.02403, checked in OpenAlex, Semantic Scholar and OpenCitations
(they disagree by 5x on the same paper), plus one non-arXiv index.

**Section 10, supervisor.** Q4 (compute): see section 8 below. Add: AI-assisted
work must be disclosed per department policy — `fork.txt.txt` is an
AI-generated wrong proof, and the current note overclaimed by trusting a
citation unread. Both are lessons, and the second is now a habit: every claim
in the refined proposal carries a status.

---

## 8. Compute

No GPU. Nothing here is GPU-shaped: exact PTS is breadth-first search over
token placements, bounded by branching and memory, not arithmetic.

What actually decides the open question is a **SAT encoding** ("is there a
schedule of length `<= T`?"). It now exists (`pts/sat.py`, CaDiCaL via
`python-sat`), agrees with the exact solver on twelve instances, certifies the
face rotation a second way (`T = 10` UNSAT, `T = 11` SAT), and has settled the
two witnesses named above — run on genuine family members, since routing number
is not monotone under subgraphs: the 20-cycle in the 2-core of the `2x1` patch
(n = 21) and the 24-cycle in the 2-core of the `2x2` patch (n = 35) both rotate
in exactly 11, in 0.2 s and 1.1 s. Neither beats `girth - 1`. The "week" the
first version of this review budgeted for a feasibility estimate was a
misjudgement by three orders of magnitude. The live question is now the full
`LB = 1` enumeration over disjoint cycle systems on the `2x2` patch, one SAT
call each.

Two things that are cheaper than they look: (a) a permutation has `LB = 1`
iff it rotates a set of vertex-disjoint cycles and edges, so "max `OPT` over
`LB = 1`" is an enumeration over disjoint cycle systems (229 for the `3x3`
grid), not over `n!`; (b) the blank relaxation in `pts/exact.py`
(`solve_relaxed`) is *weak* on face instances — it returns roughly the number
of tracked tokens — so it is not a substitute for SAT there. The face itself
needs neither: it is proved.

Plain BFS dies near n = 12; bidirectional BFS ([pts/exact.py](pts/exact.py))
reaches n ~ 13 at depth 6-7 in a minute or two.
