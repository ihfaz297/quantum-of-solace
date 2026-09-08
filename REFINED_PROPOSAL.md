# Parallel Token Swapping on Heavy-Hex Architectures

## An instance-wise reduction to the grid, a girth lower bound, and an empirical router

**Undergraduate Thesis Proposal — revised**

[Your name] · [Department] · [Date] · Proposed supervisor: [Name]

> **How to read this document.** Every mathematical claim carries one of five
> labels. **PROVED** — a written proof exists and has been independently
> checked. **VERIFIED** — machine-checked on the stated finite range by
> `python -m pts.check_all` in the accompanying repository (or by the named
> module), which is evidence, not proof. **NOT NEW** — proved here but already a
> corollary of published work, cited as such. **CONJECTURED** — supported by
> computation, unproved. **OPEN** — nobody knows, and the document names whose
> open problem it is. A result imported from the literature and used as a black
> box is marked **[cited]** with its theorem number. Facts established by an
> external audit rather than by the repository are marked **[audit]**. Nothing
> is stated more strongly than its label.

---

## 1. Summary

Quantum circuits must be compiled to hardware with limited qubit connectivity,
which requires inserting SWAP gates to bring interacting qubits into adjacency.
Because decoherence is a function of wall-clock time, the quantity that matters
most is SWAP *depth* — the number of parallel swap rounds — rather than total
SWAP count.

The abstract form of this subproblem is *parallel token swapping* (PTS): given a
graph and a target permutation, reach it in the fewest rounds, where each round
applies a matching of simultaneous swaps. Bansal, Günlük and Shapley (BGS, 2025)
give the first approximation guarantees for the topologies common in
superconducting hardware — constant-factor for cycles and subdivided stars, and
`2·OPT + 2h` for `h × n` grids, which is *not* constant-factor — and state in
print that IBM's heavy-hex lattice "requires further research".

This thesis attacks the heavy-hex case, and part of the attack is done. Since
the original proposal:

- **A reduction from heavy-hex PTS to grid PTS is PROVED and VERIFIED.** The
  heavy-hex graph maps onto a rectangular grid with fibers of at most five
  vertices, and — the part not in the literature — every derived grid instance
  has geodesic lower bound no larger than the original's. Any present or future
  grid algorithm therefore transfers to heavy-hex with constant-factor loss,
  *instance by instance*. The closest prior work (Yuan & Zhang, 2025) reduces
  heavy-hex to a grid only in the worst case, and provably cannot do better as
  written.
- **A lower bound is PROVED:** rotating one hexagonal face costs exactly 11
  rounds while every token moves distance 1, so the stretch factor of the
  geodesic bound on heavy-hex is at least 11. The proof is a short winding
  argument that generalises the known cycle bound to a cycle inside a lattice;
  it also proves that rotating *any* cycle by one costs at least `girth − 1` in
  *any* graph.
- **The core implementation exists** and passes a check suite that reproduces
  every number in this document — including a SAT encoder that certifies the
  face rotation a second way and settles the two candidate witnesses against
  `σ = 11` in about a second each: both cost exactly 11.

The original headline — a constant-factor approximation for heavy-hex — was
for a period believed proved. Its proof rested on a grid guarantee attributed
to BGS that BGS do not prove and leave open. The error was caught by reading
the paper at source; the argument was salvaged as the reduction above; and the
habit that came out of it — every claim labelled, every "verified" backed by
runnable code, every load-bearing citation read — is the method of this thesis
(section 13).

What remains is sharper than the original questions: is 11 tight? Is the
reduction tight? And the one question the thesis will *not* claim — a constant
bound on the stretch factor of heavy-hex — is downstream of a problem BGS leave
open for grids, and this document says so rather than aiming at it.

---

## 2. Problem statement

**Parallel token swapping (PTS).** Let `G = (V, E)` be a connected graph with a
distinct token on each vertex. A *round* applies a matching `M ⊆ E` and swaps
the tokens on the endpoints of every edge of `M` simultaneously. For a
permutation `π` of `V` (the token starting at `v` must finish at `π(v)`),
`OPT(G, π)` is the minimum number of rounds. The *routing number* is
`rt(G) = max_π OPT(G, π)`; trivially `rt(G) ≥ diam(G)`. The *geodesic lower
bound* is `LB_G(π) = max_v d_G(v, π(v))` — BGS write `d_max` — and
`OPT ≥ LB`. The *stretch factor* of a graph family `𝓕` is
`σ(𝓕) = sup{ OPT(G, π) / LB_G(π) : G ∈ 𝓕, π ≠ id }`. BGS Theorem 1 shows that
*no* function of the displacement vector has bounded stretch on general graphs,
which is why the question is necessarily family-specific.

**Heavy-hex.** A hexagonal lattice with an extra qubit subdivided onto every
edge: degrees 2 and 3, girth 12. Three models appear and are kept apart.

| model | definition | vertex count | status |
|---|---|---|---|
| **idealised `i × j` patch** | the 2-core of the brick rectangle below | `n = 5ij + 4(i+j) − 1` | VERIFIED as the 2-core count on 6 shapes (suite: "Patch model"); the original proposal's formula, correct for this object |
| **brick rectangle `X = S(H)`** | `H` = brick wall on `[0, 2i+1] × [0, j]` (all horizontal edges; vertical edges `(x,y)–(x,y+1)` iff `x + y` even); `S` subdivides every edge once | patch + 4 (two dangling boundary flags) | what the proofs and `pts/heavyhex.py` use; girth 12 whenever `i, j ≥ 1` — PROVED (every cycle of `X` is a subdivided cycle of `H`, and `H` has girth 6); VERIFIED on 25 shapes |
| **real devices** | idealised patch + pendant qubits (single leaves or paths of up to three) on degree-2 boundary branch vertices | Falcon-27 = `1×2` (21) + 6; Eagle-r3-127 = `3×6` (125) + 2; Heron-r1-133 = `3×6` + 8; Heron-r2/r3-156 = `3×7` (144) + 12 | **[audit]** by graph isomorphism against the `qiskit-ibm-runtime` fake-provider coupling maps; girth 12 on every one; Eagle-r1 is a *different* lattice |

The theorems below are stated and checked for the brick rectangle. Their
extension to the 2-core (delete two leaves) is expected to be routine. Their
extension to pendant paths is **not**: a path of length 3 hung on a boundary
cell raises that cell's fiber size to 8 and its diameter to 7, which changes
the padding constant, the phase count and the path bound. Both extensions are
labelled NOT WRITTEN and budgeted in section 6.

**The lattice IBM ships is no longer only heavy-hex.** IBM Nighthawk (120
qubits, December 2025) has a coupling map that is the `12 × 10` grid graph,
edge for edge **[audit]**. Eagle-127 is retired; the current fleet is Heron
(heavy-hex, 133/156) and Nighthawk (grid, 120). BGS's grid theorem applies to
Nighthawk directly — but at `h = 10` its additive term `2h = 20` equals the
diameter. On 200 random permutations of the `12 × 10` mesh the classical mesh
router never needed more than 32 rounds while BGS's guarantee `2·d_max + 2h`
was never below 48 (VERIFIED, suite: "12 x 10 mesh"). Nighthawk is a
measurement target for grid stretch, not a free theorem.

**Scope caveat.** PTS fixes the target permutation. Full qubit routing does not
— the router chooses intermediate permutations subject to a sequence of gate
constraints, and choosing well is most of the practical problem. An
approximation bound for PTS on heavy-hex does not imply a bound on compiled
circuit depth, and a stretch-factor bound says only how well the geodesic bound
predicts the *optimum*, nothing about any practical router. Where PTS applies
exactly is between two consecutive layers of a circuit whose qubit assignment
is already fixed — a QAOA or Trotter layer structure, or a permutation gate in
a synthesised circuit. This thesis claims theory at the permutation level and
evidence at the circuit level, and will not conflate them: permutation routers
are compared with permutation routers on the same objective (RQ3a), and whether
a better permutation router moves compiled depth at all is asked separately, in
the pipeline, with the pipeline's confounders named (RQ3b).

---

## 3. Related work and the gap

**Sequential token swapping** (minimise swap *count*) is NP-hard and APX-hard,
with a general 4-approximation and an ETH lower bound (Miltzow et al., ESA
2016); inapproximability was improved to 14/13 with barriers against beating
the 4-approximation (Hiken & Wein, ESA 2025). None of this transfers to the
parallel problem; the thesis keeps the line sharp because three of the
most-cited papers in the area are sequential-only.

**Parallel token swapping** was introduced as "routing permutations via
matchings" by Alon, Chung and Graham (1994), who bounded any connected
`n`-vertex graph by `3n` rounds via a spanning tree (Zhang, 1999:
`(3/2)n + O(log n)`) and proved `rt(G □ G′) ≤ 2·rt(G) + rt(G′)` for Cartesian
products, whence `rt(mesh) = Θ(rows + cols)` (restated as Alpert et al. 2022,
Theorem 4). The column-row-column mesh router in `pts/gridroute.py` *is* that
classical construction and is not a contribution; its docstring says so. Li, Lu
and Yang (2010) proved `rt(C_n) = n − 1` by a forward/backward charging
argument; He, Valentin, Yin and Yu (2014) showed the rotation is essentially
the unique extremal permutation on even cycles. Alpert et al. extend
`rt = Θ(w + h)` to *convex* pieces of the square lattice; heavy-hex is not one.

**Hardness (corrected from the original).** Deciding `OPT ≤ k` is NP-complete
for every fixed `k ≥ 3` on bipartite graphs of maximum degree **4**, and for
every fixed `k ≥ 5` on bipartite graphs of maximum degree **3** (Kawahara,
Saitoh & Yoshinaka, JGAA 2019, Theorems 3 and 4; the `k ≥ 3` result
independently by Banerjee & Richards, FCT 2017); `k ≤ 2` is polynomial (Theorem
5). PTS is NP-complete on trees, even subdivided stars (Aichholzer et al., ESA
2022). The original proposal's "degree 3 and three rounds" conflated the two
theorems. Whether any reduction *embeds* into heavy-hex is open and is not the
cheap check the original budgeted: the degree-3 gadget contains a 10-cycle per
variable, which girth 12 forbids, and no bounded-degree planar hardness is known
for the uncoloured problem (KSY's only planar result is for the 3-coloured
variant). Nighthawk, with degree-4 vertices, is outside the degree-3 class.

**Bansal, Günlük & Shapley** (Discrete Applied Mathematics 377, 480–497, 2025;
arXiv:2411.18581). Statements from arXiv v2, which differs from v1 in Theorem
4(a)'s constant and in remark numbering; cite v2 or the journal.

| result (v2) | statement | constant-factor? |
|---|---|---|
| Thm 2 | cycles: `≤ 2·OPT` (even `n`), `≤ 2·OPT + 1` (odd) | yes |
| Thm 3 | subdivided stars with `h` branches: `≤ 4·OPT + min{OPT, h} + 1` | yes |
| Thm 4(a) | `2 × n` grids: `≤ 2·OPT + 2` | yes |
| Thm 4(b) | `h × n` grids, `h ≤ n` the short side: `≤ 2·OPT + 2h` | **no** — additive in the short side |
| Remark 14 | the same Algorithm 6 achieves `≤ 2·d_max + 2h`; grid stretch is `O(h)` | a proved corollary of the Thm 4(b) proof |
| Thm 5 | stretch of `d_max`: lines 2; `n`-cycles between `n − 1` and `n`; subdivided stars `Θ(h)` | — |
| Thm 1 | no function of the displacement vector has stretch better than `Ω(n)` on general graphs | — |
| Thm 6 | the same bounds for the *incomplete* variant on all three families and the *coloured* variant on stars and grids | — |
| §8 | "While we provide an upper bound for the stretch factor on grid graphs, pinning it down asymptotically remains an open question." Table 1 leaves the grid stretch column blank | **OPEN** |

Three consequences the original proposal did not draw. **First**, the original's
"constant-factor approximations for cycles, subdivided stars, and grids" is
wrong for grids: at `OPT = O(1)` and large `h` the ratio is unbounded.
**Second**, `h` is the *short* side; Thm 4(b) is printed with `h ≥ 3`, and this
thesis carries that hypothesis until the `h = 2` case is written out.
**Third**, Thm 4(b) is stated for the full rectangle; a polyomino quotient needs
a separate argument. Two more sentences of theirs carry weight: §1.1 (v2 only)
disclaims heavy-hex — designing algorithms for "more complex graph topologies
(including IBM's heavy hex ...) using algorithms for its subgraphs provided in
this paper requires further research" — and §1.3 refutes a prior claim that
Demaine et al. gave an `O(1)`-approximation on grids, "since [9] considers a
variant ... where one is allowed to rotate the tokens along a cycle in one
step". Their subdivided-star results do not apply to a hexagonal face (a
subdivided star has exactly one vertex of degree > 2; a face has six).

**Why the grid stretch question is open, and in which model it is solved.**
Demaine, Fekete, Keldenich, Meijer & Scheffer (SoCG 2018; SIAM J. Comput. 2019)
prove constant stretch on grid rectangles in a model that forbids adjacent
swaps and lets a whole cycle of agents rotate in one step. PTS embeds in that
model with `O(1)` loss but not conversely: rotating `C_m` costs one step there
and `m − 1` rounds here. Alpert et al. pose bounded stretch for routing by
matchings on grids as their open Question 1, noting the rectangle case "is
proved in [Demaine et al.] with a slightly different routing setup"; BGS pose
it in §8. Two independent groups, one open problem, and cycle rotation is the
obstruction in both — exactly the mechanism behind this thesis's lower bound.

**Yuan & Zhang** (Quantum 9, 1757, 2025; arXiv:2402.02403, v1 February 2024)
characterise compilation depth overhead by the routing number and prove
transfer theorems between architectures. Their Theorem 9 bounds `rt` of
"brick wall" graphs, `rt(Brickwall^{b1,b2}_{n1,n2}) = O((b1 + b2)(n1 + b2·n2))`,
and they write "in IBM's brick wall chips, b1 = 3 and b2 = 5" — heavy-hex,
though the words "hex", "token swapping" and "stretch" never appear. With
`rt ≥ diam` this gives `rt(heavy-hex) = Θ(diam)`, i.e. `Θ(√n)` at fixed aspect
ratio, for the boundary-free brick wall. **This is the closest prior work, and
the token-swapping and routing-number literatures do not cite each other**; the
first review of this project missed it by searching under one literature's
vocabulary. Three caveats govern the relationship:

- *Structural, not verbatim.* `X` is a brick-wall **patch** with flags and
  half-bricks; routing number is not monotone under subgraphs; Theorem 9
  applies to `X` modulo a boundary argument that has not been written.
- *Worst-case only, provably.* Their first step (Lemma 1) splits any
  permutation into two involutions. For the rotation of `C_k` (`LB = 1`) the
  best split has `max(LB(τ₁), LB(τ₂)) = ⌊k/2⌋` — VERIFIED for `k = 6, 8, 10, 12`
  (suite: "Yuan-Zhang Lemma 1"). Heavy-hex contains cycles of length `Θ(√n)`,
  so their route inflates the geodesic bound without bound and cannot give a
  per-instance guarantee as written.
- *Constants are not argued.* Their implied constant, read off their proof, is
  several hundred times `diam`; this router's measured ratio is about 23 and
  its proved constant is worse than theirs. Neither is presentable.

**Heavy-hex-specific results are different objects.** Weidenfeller et al.
(Quantum 2022) show that a fixed swap strategy reaches full all-to-all
connectivity on heavy-hex within `n + √n + 61` SWAP layers — a swap-network
depth for one task, `Θ(n)`, neither a routing number nor a diameter bound (the
original proposal's gloss "a worst-case diameter bound" was wrong). Line-graph
qubit routing (Kattemölle & Hariharan, ACM TQC 2025) is a structure-exploiting
heuristic with an overhead bound, not an instance-wise guarantee. The honeycomb
interconnection-network literature (Stojmenović; `(ℓ,k)`-routing on plane
grids) is store-and-forward packet routing with queues and yields no bound in
the matching model; it is cited so a referee sees it was checked. Two 2026
papers (Courtney) compute routing numbers for neutral-atom architectures with
quotient-graph machinery: adjacent, active, not on heavy-hex.

**Practical routers and benchmarks.** Qiskit's default router is LightSABRE
(Zou et al., 2024), successor to SABRE (Li, Ding & Xie, ASPLOS 2019), with
further heuristic changes in Qiskit 2.5; `SabreSwap.trials` defaults to the CPU
count. Duostra, QMAP, tket and BQSKit are maintained; TOQM is archived and is
dropped; IBM ships an RL-based AIRouting pass. Qiskit and rustworkx ship
Miltzow et al.'s *sequential* 4-approximation as the
`permutation.token_swapper` synthesis plugin — the only shipped permutation
synthesiser that honours a coupling map (`permutation.acg` assumes all-to-all
connectivity, `permutation.kms` a line). No public implementation of any
*parallel* token swapping algorithm was found on GitHub, Zenodo, Semantic
Scholar, Crossref or OpenAlex as of September 2026 **[audit]**; those indices
lag. The benchmarking study the original alluded to is QKNOB (Li, Zhou & Feng,
IEEE TQE 2025): five general-purpose routers, on circuits *constructed* around
a known near-optimal transformation, on three retired devices, under Qiskit
0.33; SABRE best on all but one set, every tool more than four times the
built-in optimum on medium-depth circuits. It tests no structure-exploiting
router, so the original's inference that "wins over SABRE come from exploiting
structure" is withdrawn. QUBIKOS (Ping et al., 2025) reports LightSABRE a mean
63× off known-optimal SWAP *count*. Together these motivate routers with
guarantees; neither is a depth-optimal suite, because none exists. Benchpress
(Nation et al., Nature Comput. Sci. 2025) is the current reference harness and
covers heavy-hex targets.

**The gap.** None found, over the indices and vocabularies named above: (i) an
instance-wise approximation guarantee or a stretch-factor bound for PTS on
heavy-hex — the original's gap, confirmed, with BGS's own disclaimer as the
citable form; (ii) a lower bound on the stretch factor of any two-dimensional
lattice beyond what follows from cycles; (iii) a reduction that carries a
per-instance geodesic lower bound through a vertex-set-changing quotient. The
worst-case routing number of the idealised brick wall *is* known (Yuan–Zhang).
The per-instance statements are the gap, and section 4 fills two of them. All
three are universal negatives established by a method that missed Yuan–Zhang
once; confidence is moderate, and the thesis names its nearest neighbours
rather than asserting emptiness.

---

## 4. What is already established

Notation: `X` on the brick rectangle with `A = (W − 1)/2` and `B = Ht`; `Γ` the
`(A+1) × (B+1)` grid graph. Every VERIFIED range below names the suite section
that produces it.

### 4.1 The reduction

**Lemma 1 (bounded-fiber quotient) — PROVED; VERIFIED on 36 shapes to
`n = 168`.** Define `φ: V(X) → V(Γ)` by `φ(x, y) = (⌊x/2⌋, y)` on branch
vertices and `φ(s) = φ(lower-left endpoint of s's H-edge)` on subdivision
vertices. Then (1) each fiber has 3 to 5 vertices and induces a tree of
diameter `≤ 4`; (2) every edge of `X` lies inside a fiber or joins `Γ`-adjacent
fibers, **and every edge of `Γ` is the image of an `X`-edge** — the quotient is
exactly `Γ`; (3) `d_Γ(φu, φv) ≤ d_X(u, v) ≤ 4(d_Γ(φu, φv) + 1)`. Proof status:
the bold converse in (2) is immediate from the construction but is missing from
the written note, whose proof of (3) uses it; the written proof of (3) derives
`5·d_Γ + 4`, which suffices for every `O(1)` below, while the sharp form is
VERIFIED and tight (`max(d_X − 4·d_Γ) = 4` on every shape) and needs one more
line. Why a quotient and not an embedding — PROVED: `X` is bipartite with class
sizes differing by `AB − 1`, a grid's differ by at most one.

**Lemma 2 (five-fold König decomposition) — PROVED; VERIFIED on 480 low-`LB`
instances.** For any permutation `π` of `V(X)` there are permutations
`σ₁, …, σ₅` of `V(Γ)` and a 5-colouring of the tokens such that (1)
`max_p d_Γ(p, σ_r(p)) ≤ LB_X(π)` for every `r`, and (2) for each `r` and cell
`p`, exactly one colour-`r` token starts in `p` and is destined for cell
`σ_r(p)` — unless `p` is a padded fixed point of `σ_r`, in which case none is.
Proof: the cell-demand bipartite multigraph has both degrees `|C_p| ≤ 5` at
every cell; pad with self-loops to 5-regular; König gives five perfect
matchings; a real edge has `Γ`-displacement `≤ LB_X(π)` by Lemma 1(3), a loop
has 0. *Verification note:* the original check on uniformly random `π` was
vacuous — a random permutation has `LB_X` above `diam Γ`, so (1) could not
fail. The suite now checks (1) on permutations with `LB ∈ {1, 2, 3, 4}`, where
it can fail and does not (maximum displacement/`LB` exactly 1.0).

**Lemma 3 (simulating one grid round) — PROVED with an unquantified `O(1)`;
measured `c₃ ≤ 14`.** With one designated token per cell, any matching `N` of
`Γ` — exchange the designated tokens of `p` and `q` for every `{p, q} ∈ N`,
leave every other token in place — can be realised on `X` in `c₃ = O(1)` rounds
without changing any cell's token count. Designated tokens of adjacent cells
are at `X`-distance `≤ 9` by the proved form of Lemma 1(3) (`≤ 8`, measured);
pairs whose neighbourhoods intersect lie within `O(1)` grid distance, so the
conflict graph is greedily `O(1)`-colourable; within a colour class the paths
are disjoint and the endpoint transposition of a path on `≤ 10` vertices fixing
its interior takes `≤ 10` rounds of odd-even transposition sort. The note's
explicit constant (1,090 colours, 9,810 rounds) is **withdrawn** — not
derivable from its own argument — and the thesis analyses the constant
properly. Measured: 2 colours, paths of exactly 9 vertices, `c₃ ≤ 14` from
`n = 39` on, final within-cell phase `c₄ = 5` (suite: "Section 4 algorithm";
`pts/scaling.py` to `n = 480`).

> **Theorem A (reduction) — PROVED modulo the one-line repairs above; VERIFIED
> by independent replay on 56 random and 24 low-`LB` permutations to
> `n = 168` (suite), 36 random to `n = 480` (`pts/scaling.py`).** Let `𝒜` route
> any permutation `σ` of `Γ` in `f(σ)` rounds. Then there is a polynomial-time
> algorithm routing any permutation `π` of `V(X)` in at most
>
> ```
> 5 · c₃ · max_r f(σ_r) + c₄     rounds,
> ```
>
> where `σ₁ … σ₅` are the cell-permutations of Lemma 2, so that
> **`LB_Γ(σ_r) ≤ LB_X(π)` for every `r`.**

Five phases: in phase `r`, designate the colour-`r` token in each cell (any
token, if the cell is a padded fixed point of `σ_r`), run `𝒜` on `(Γ, σ_r)`,
realise each of its rounds by Lemma 3; then permute inside every cell in
parallel. Correctness rests on an invariant: a colour-`r` token stays in its
starting cell through every phase `r′ ≠ r` (it is either undesignated, or
designated at a cell with no colour-`r′` token — a padded fixed point of
`σ_{r′}`, to which it returns), moves to its target cell in phase `r`, and the
residual permutation after phase 5 acts within cells. The implementation
enforces the occupancy invariant by live assertions and replays every schedule
from scratch against the edge set.

The bold inequality is the contribution: a per-instance transfer of the
geodesic lower bound through a *non-product* quotient. Framed honestly, it is
Alon–Chung–Graham's product-theorem technique — a Hall/König lane assignment
followed by simulation — generalised from products, where the base graph
appears as disjoint copies and a base round costs one round, to quotients with
unequal fibers of size `≤ 5`, where a base round costs `O(1)` rounds and five
phases are needed. No published transfer tool reaches heavy-hex: ACG's product
theorem needs a product, spanning-subgraph monotonicity needs a subgraph with
small `rt`, Banerjee–Richards' bound needs high connectivity, Alpert et al.
need convexity, and Yuan–Zhang's Theorem 8 keeps the vertex set while their
Theorem 9 route loses the per-instance bound.

### 4.2 Three corollaries

**Corollary A1 — `rt(X) = Θ(diam X) = Θ(√n)` for square patches. PROVED here;
NOT NEW.** Instantiate `𝒜` with the classical mesh router,
`f ≤ 2(B+1) + (A+1)`; then `rt(X) = O(A + B)`, and `A + B ≤ diam X ≤ 4(A+B) + 4`
by Lemma 1(3), with `rt ≥ diam` trivial. The asymptotic content is a corollary
of Yuan–Zhang Theorem 9 for the boundary-free brick wall; the patch statement is
proved here by a different, lower-bound-preserving method, and the two will be
reconciled with a written boundary paragraph. The Tier-1 router ignores `LB`
by construction: on the `5 × 2` rectangle a permutation with `LB = 1` takes 253
rounds, and on `11 × 5` 608 (VERIFIED, suite: "Section 4 algorithm (b)"), which
is why Corollary A2 needs the `LB`-relative analysis.

**Corollary A2 — `σ(X) = O(h_Γ)`, `h_Γ = min(A+1, B+1)` the short side of the
quotient. PROVED, importing BGS Remark 14 [cited]; the five-phase composition
is immediate but is to be written out line by line.** Instantiate `𝒜` with BGS
Algorithm 6 on the full rectangle `Γ`, `h_Γ ≥ 3`, `f(σ) ≤ 2·LB_Γ(σ) + 2h_Γ`:
for every `π ≠ id`, `OPT_X(π) ≤ 5c₃(2·LB_X(π) + 2h_Γ) + c₄`, so
`OPT_X(π)/LB_X(π) ≤ 5c₃(2 + 2h_Γ) + c₄`. An instance-wise guarantee for
heavy-hex parameterised by the short side. Two remarks: (a) every heavy-hex
device *currently in IBM's fleet* (Heron) is a `3 × j` patch, whose quotient
has short side 4, so on that family the geodesic bound is within a fixed — if
large — constant of the optimum; Falcon (`1 × 2`, short side 2) falls under Thm
4(a) instead; the statement covers devices literally only after the 2-core and
pendant extensions. (b) Corollaries A1 and A2 are incomparable — the diameter
bound wins on high-`LB` permutations — so the thesis states their minimum.

**Corollary A3 — `σ(grid) = O(1) ⇒ σ(heavy-hex) = O(1)`. PROVED as an
implication; hypothesis OPEN** (BGS §8; Alpert et al. Question 1). One-way
only: the converse would need a reduction from grid PTS to heavy-hex PTS, which
is not established, so RQ2(c) is **not** equivalent to the grid problem — it
sits downstream of it. If instead `σ(grid)` is unbounded, Corollary A2 is the
ceiling of what the quotient route can give.

### 4.3 The lower bound

> **Theorem B (winding bound) — PROVED; VERIFIED (0 violations, bound attained)
> on 186 random instances in the suite, 466 in `python -m pts.winding`, and
> 1,178 in an independent audit.** Let `ω: E → ℤ` be antisymmetric on oriented
> edges. For each vertex `v` choose a path `Q_v` from `v` to `π(v)`; put
> `D = Σ_v ω(Q_v)` and `g_ω = min{ |C| : C a simple cycle with ω(C) ≠ 0 }`. If
> `D ≠ 0` then `OPT(G, π) ≥ g_ω − max_v |Q_v|`.
>
> *Proof.* Let `P_v` be the walk token `v` takes in a `T`-round schedule;
> `|P_v| ≤ T`. Each round traverses every matched edge once in each direction,
> so `Σ_v ω(P_v) = 0`, hence `Σ_v ω(P_v · Q_v⁻¹) = −D ≠ 0`. Some closed walk
> `P_v · Q_v⁻¹` therefore has `ω ≠ 0`. Its chain is an integer circulation,
> which decomposes into simple directed cycles of total length
> `≤ |P_v| + |Q_v|`; `ω` is additive on chains, so one of those cycles has
> `ω ≠ 0` and length `≥ g_ω`. Thus `T + |Q_v| ≥ g_ω`. ∎

At `G = C_n` this is Li–Lu–Yang's Lemma 2.1 and the charging argument BGS
re-derive for Theorem 5(b). The general form needs no product structure —
LLY's only extension to a cycle inside a larger graph (Lemma 2.2) needs a
Cartesian product, which heavy-hex is not. It is positioned as "the cycle
charging argument freed from the product structure". **Novelty: PLAUSIBLE, NOT
ESTABLISHED.** Absent from Alon–Chung–Graham (a clean copy was read), Li–Lu–Yang,
Banerjee–Richards, KSY, Aichholzer et al., BGS and Yuan–Zhang; not yet checked
against Jerrum (1985, winding vectors for *sequential* cyclic transpositions),
the circular-sorting literature, coordinated motion planning, and sorting
networks on graphs. The defensible narrow claim: the first bound in the
parallel routing-via-matchings literature sensitive to the homology class of
the permutation, and the first that is non-trivial on an instance where
`d_max`, every cut bound and ACG's total-work bound are all simultaneously
`O(1)`. It is *not* "the first to escape BGS Theorem 1's barrier" — every
graph-aware bound already does.

**Corollary B1 (girth law) — PROVED; VERIFIED on 15 host graphs (suite:
"Winding probe").** In any graph, rotating any cycle `C` by one costs at least
`girth − 1`. Take `ω = +1` on one edge `e` of `C` in the rotation direction and
0 elsewhere: `D = ±1`, `|Q_v| ≤ 1`, and `g_ω` is the shortest cycle through
`e`, `≥ girth`. This replaced an earlier slogan of this project — "legs never
help, only chords do, and the cost is exactly `girth − 1`" — that a larger
instance refuted: `C₈` with legs to a common hub rotates in 6, not 7, because
the hub creates a 6-cycle; the `m = 4, 6` probes behind the slogan were
girth-preserving by accident. The lower bound is the law; equality is not (the
`3 × 3` grid boundary rotation has girth 4 and `OPT` 4). Girth-preserving
escape routes tested (`m = 6, 8`) do not reduce cost.

**Corollary B2 — face rotation costs exactly 11 at `LB = 1`; `σ(heavy-hex) ≥
11`. PROVED; both halves VERIFIED on the `3 × 1` and `5 × 2` rectangles (suite:
"Winding theorem"), and `7 × 3` in `pts.winding`.** With `ω` the signed
crossings of a ray from a point inside a face: `D = ±1`, `max|Q_v| = 1`,
`g_ω ≥ girth = 12`, so `OPT ≥ 11`; eleven adjacent transpositions along the
face give `≤ 11`. It applies to every heavy-hex patch containing a complete
face — every Heron and Eagle device; not to Nighthawk, which has none.

**Corollary B3 — `σ(square grids) ≥ 4`. PROVED by exact computation.** The
`3 × 3` boundary rotation has `LB = 1` and `OPT = 4` (suite: "Section 5
table"); all 229 permutations of the `3 × 3` grid with `LB ≤ 1` have `OPT ≤ 4`
**[audit]**. `σ ≥ 3` was already BGS Theorem 5(b), since `C₄` is the `2 × 2`
grid. Both are constants against BGS's asymptotic question and are recorded as
first data points only.

**Corollary B4 (the two enclosing-cycle witnesses) — VERIFIED by SAT, schedules
replayed (suite: "SAT certificates").** The 20-cycle bounding two fused faces
(2-core of the `2 × 1` patch, `n = 21`, one interior vertex) and the 24-cycle
around a branch vertex (2-core of the `2 × 2` patch, `n = 35`, four interior
vertices) both rotate in exactly 11 rounds at `LB = 1`: `T = 11` is
satisfiable, in 0.2 s and 1.1 s respectively, and the face rotation on `X(3,1)`
is `UNSAT` at `T = 10` and `SAT` at `T = 11`. Neither enclosing cycle beats
`girth − 1`. `pts/sat.py` is a bounded-model-checking encoding (one Boolean
per edge per round, one per token-position per round; ~15,000 variables and
~300,000 clauses at `n = 35`) solved by CaDiCaL; it agrees with the exact BFS
solver on all twelve small instances of the suite.

**Limitation (ceiling) — PROVED.** On a planar graph the bounded faces generate
the cycle space, so an `ω` vanishing on every face is a coboundary and forces
`D = 0`; hence `D ≠ 0` requires `ω(F) ≠ 0` for some face `F`, and `g_ω ≤ |F|`.
On heavy-hex every face is a 12-cycle (face count equals cyclomatic number,
VERIFIED), so Theorem B never exceeds 11 there. **It cannot decide whether
`σ(heavy-hex) = 11`.** The `3 × 3` grid shows an enclosing cycle *can* beat
`girth − 1`.

### 4.4 Status ledger

| claim | status | where checked |
|---|---|---|
| Lemma 1 | PROVED; VERIFIED 36 shapes, `n ≤ 168` | suite "Lemma 1" |
| Lemma 2 | PROVED; VERIFIED 480 low-`LB` instances | suite "Lemma 2 (b)" |
| Lemma 3 | PROVED, `O(1)` unquantified; `c₃ ≤ 14` measured | suite "Section 4 algorithm"; `scaling.py` |
| Theorem A, `LB_Γ(σ_r) ≤ LB_X(π)` | PROVED (three one-line repairs owed); VERIFIED by replay | suite "Section 4 algorithm" |
| the transfer is new | supported: Yuan–Zhang's split inflates `LB` to `⌊k/2⌋` | suite "Yuan-Zhang Lemma 1" |
| `rt(X) = Θ(diam X)` | PROVED; NOT NEW (Yuan–Zhang Thm 9, modulo boundary) | — |
| `σ(X) = O(h_Γ)` | PROVED via BGS Remark 14 [cited]; composition to be written | — |
| `σ(grid) = O(1) ⇒ σ(heavy-hex) = O(1)` | PROVED as implication; hypothesis OPEN | — |
| Theorem B | PROVED; stress-tested, 0 violations | suite "Winding theorem"; `winding.py` |
| girth law | PROVED; VERIFIED 15 hosts | suite "Winding probe" |
| `σ(heavy-hex) ≥ 11` | PROVED | suite "Winding theorem" |
| the 20- and 24-cycle witnesses cost exactly 11 | VERIFIED by SAT, replayed | suite "SAT certificates" |
| `σ(heavy-hex) = 11` | OPEN (RQ1); Theorem B cannot decide it; the two named witnesses do not refute it | — |
| `σ(square grids) ≥ 4` | PROVED by computation | suite "Section 5 table" |
| `OPT_Γ(σ_r) = O(OPT_X(π))` | OPEN (RQ2b) | — |
| patch formula = 2-core count | VERIFIED 6 shapes | suite "Patch model" |
| devices = patch + pendants; Nighthawk = `12 × 10` grid | **[audit]** | not in suite |
| 2-core and pendant extensions | NOT WRITTEN | — |
| coloured / incomplete transfer | CONJECTURED | — |

---

## 5. Research questions

**RQ1 (lower bound).** `σ(heavy-hex) ≥ 11` is PROVED. Is it tight? Theorem B
cannot say. The two candidate witnesses named by the audit — the 20-cycle
bounding two fused faces and the 24-cycle around a branch vertex, the heavy-hex
analogue of the `3 × 3` grid's centre — have been run on genuine family members
(the 2-cores of the `2 × 1` and `2 × 2` patches, since routing number is not
monotone under subgraphs) and **both cost exactly 11** (Corollary B4). So the
obvious enclosing cycles do not refute `σ = 11`. What would settle the `LB = 1`
slice on a patch is the full enumeration: a permutation has `LB = 1` iff it
rotates a set of vertex-disjoint cycles and edges, in either orientation, and
each such system is one SAT call of about a second. That enumeration on the
`2 × 2` patch is the next experiment; its outcome is either a witness with
`OPT ≥ 12` (`σ > 11`) or the statement "`σ = 11` on the `LB = 1` slice of the
`2 × 2` patch", CONJECTURED for larger patches. An `LB = 2` instance with
`OPT ≥ 23` would also do it; that slice is not enumerable, and the thesis says
which slice each result covers.

**RQ2 (reduction).** (a) *Does heavy-hex PTS reduce to grid PTS preserving the
per-instance geodesic bound?* Yes — Theorem A. (b) *Is the reduction tight* —
`OPT_Γ(σ_r) = O(OPT_X(π))`? OPEN; a positive answer turns BGS's `2·OPT + 2h`
into `c·OPT + O(h)` on heavy-hex. (c) *Is there a reduction the other way?*
OPEN; it would make `σ(heavy-hex)` and `σ(grid)` finite or infinite together.
`σ(heavy-hex) = O(1)` itself is downstream of BGS's open grid question and is
not a target.

**RQ3a (permutation routers).** On the Heron-156 and Nighthawk-120 coupling
maps, and on smaller instances with exact optima, how do measured rounds
compare with `LB` and with `OPT` for the reduction-based router (with the mesh
router and with BGS Algorithm 6 inside), BGS Algorithm 6 directly on the grid,
and `permutation.token_swapper` (sequential count objective, stated as such)?
How far below their proved bounds do they run?

**RQ3b (compiled circuits).** Installed in the Qiskit pipeline as a
permutation-synthesis plugin, does a better permutation router change
end-to-end compiled depth, and by how much relative to what the routing stage
controls? *Design constraint:* a `permutation.*` plugin fires only on
`PermutationGate` objects, which generic benchmark circuits do not contain. The
RQ3b workload is therefore circuits where PTS applies exactly — QAOA and
Trotter layer structures with a fixed qubit assignment, and circuits with
synthesised permutation gates — and a null result on generic circuits is
reported as such, not hidden.

---

## 6. Approach

Thirty weeks, one student. Phases overlap; the empirical arm is never blocked
on the theory arm, and each arm has dated milestones.

**Phase 1 — Instruments (weeks 1–8).**

- *Done (`pts/sat.py`):* a SAT encoder for "is there a schedule of length
  `≤ T`?", validated against the exact BFS solver on twelve suite instances,
  with the two RQ1 witnesses decided (Corollary B4). The feasibility estimate
  the original plan budgeted a week for is: about one second at `n = 35`,
  `T = 11`. *Weeks 1–3:* the `LB = 1` enumerator over disjoint cycle systems
  (both orientations) driving the SAT encoder, run on the `2 × 2` patch; then
  `LB = 2` probes with a time cap.
- *Weeks 2–5:* BGS Algorithm 6 as a parallel router with its short-side
  orientation and an `LB`-relative test (`≤ 2·d_max + 2h`) in the suite.
  **Milestone M1, week 5:** that test passes.
- *Weeks 5–8:* BGS Algorithms 2–3 (cycles) and 4 (subdivided stars) with
  replay tests; the `LB = 1` enumerator (a permutation has `LB = 1` iff it
  rotates vertex-disjoint cycles and edges, in either orientation — an
  enumeration over cycle systems, not `n!`); one pinned environment (Qiskit
  2.5.x, mqt.qmap 3.x, pytket 2.x — all broke API in 2025) with coexistence
  confirmed by installation and a lockfile.

**Phase 2 — Write up what exists (weeks 3–14).**

- Add the converse to Lemma 1(2); prove the sharp form of 1(3); replace Lemma
  3's constant with an analysis aimed at the measured `c₃ = 14`; write the
  five-phase composition for Corollary A2 line by line; write the boundary
  paragraph reconciling A1 with Yuan–Zhang Theorem 9 and extract their implied
  constant.
- Extend Lemmas 1–3 to the 2-core (expected routine) and to pendant paths
  (fiber size and diameter grow; padding becomes `k`-regular with `k` phases —
  budgeted at three weeks, not an afternoon). **Milestone M2, week 12:** the
  router replays on the Heron-156 2-core with pendants through the suite.
- The novelty sweep for Theorem B (Jerrum 1985; circular sorting; ACG journal
  text; motion planning; sorting networks on graphs) through the library; the
  outcome goes in the note either way.
- A theory note — reduction, winding bound, corollaries, ceiling — ready for
  the supervisor by week 14.

**Phase 3 — RQ1 (weeks 3–16).** The `LB = 1` enumeration on the `2 × 2`
patch (every disjoint cycle system, both orientations, one SAT call each);
then the `3 × 2` patch if the count allows. Grids: `4 × 4` and `3 × 5` at
`LB ≤ 1` by SAT, to see whether grid stretch grows at small sizes — cheap and
informative for RQ2(c). `LB = 2` probes with a time cap. Then a proof attempt
in whichever direction the computation points: a general upper bound of 11 on
`LB = 1` rotations of chordless cycle systems, or a lower-bound argument above
Theorem B's ceiling if a witness appears.

**Decision gate — week 16** (section 7).

**Phase 4a — hard theory, if the gate admits it (weeks 16–24).** The
`OPT`-pullback (RQ2b) on a structured class first; the reverse reduction; the
general question "is `rt(G) = O(rt(H))` whenever `G` has a quotient onto `H`
with fibers of bounded size and diameter?" posed in print with the heavy-hex
case as evidence and Yuan–Zhang Theorem 8 as the same-vertex-set precedent.
Time-boxed to eight weeks.

**Phase 4b — otherwise (weeks 16–24).** The coloured and incomplete variants
through Lemma 2 (BGS Theorem 6; the padding is label-agnostic; the incomplete
case is dead qubits), written only if they come for free; then Phase 5
extended.

**Phase 5 — Empirical arm and writing (weeks 14–30).**

- *Weeks 14–18:* the router as a `permutation.<name>` HighLevelSynthesisPlugin
  under the `qiskit.synthesis` entry point. **Milestone M3, week 18:** a
  permutation round-trips through `transpile()` on a pinned stack.
- *Weeks 18–22:* RQ3a on the Heron-156 and Nighthawk-120 maps (Nighthawk's
  `Target` built from the fake-provider map; MQT Bench ships none).
- *Weeks 20–26:* RQ3b on the PTS-shaped workloads of section 5, plus
  Benchpress workloads for the null-result check, in two configurations both
  reported: routing-isolated (`optimization_level=1`, `ElidePermutations` off —
  it deletes exactly the gates a PTS router emits — `VF2PostLayout` disabled)
  and the end-to-end preset; `SabreSwap(trials=…)` pinned;
  `QISKIT_TRANSPILER_SEED` set; Pareto frontiers plus an absolute gap on a
  known-optimal suite; no fidelity claim without a calibrated estimate from the
  backend error map.
- *Weeks 22–30:* thesis writing; the theory chapters are the Phase 2 note,
  revised.

**Explicitly out of scope, stated now so they are not discovered at week 25:**
`σ(heavy-hex) = O(1)` (downstream of an open problem); embedding NP-hardness
into heavy-hex (section 3); improving either reduction's constant to something
competitive; Rust; a full routing pass manager; Eagle-class devices; any
fidelity claim without a calibrated estimate.

---

## 7. Decision gate (week 16)

The original gate — "a proven stretch-factor bound for at least one heavy-hex
family" — is met twice over (Corollaries A2 and B2) and no longer
discriminates. It is replaced by two binary, artefact-level criteria, one per
arm:

- **G1 (empirical arm).** Milestones M1 and M2 are green in the suite: BGS
  Algorithm 6 passes its `LB`-relative test, and the router replays on the
  Heron-156 2-core with pendants.
- **G2 (theory arm).** The `LB = 1` enumeration on the `2 × 2` patch has
  completed with a certificate for every cycle system (a replayed schedule, or
  an `UNSAT` verdict at `T = 11` with a DRAT proof), or has been documented
  infeasible with the count and the runtime figures.

Both hold → Phase 4a. G1 fails → all effort to G1 until it holds; Phase 4a is
dropped; Phase 5 proceeds. G1 holds, G2 fails → Phase 4b, with SAT left
running and reported whatever it returns. Every branch leaves the Threshold of
section 9 reachable. Neither criterion involves a judgment of proof quality;
each is a test that passes or does not.

---

## 8. Deliverables

1. **Theory note**: the reduction theorem with its repairs and its extension to
   device 2-cores; the winding bound, `σ(heavy-hex) ≥ 11`, the girth law,
   `σ(grid) ≥ 4`, the planar ceiling; the RQ1 outcome. Every claim labelled,
   every lemma machine-checked.
2. **Open-source package `pts`** (Python; Rust only if profiling demands it):
   heavy-hex construction and quotient; the reduction-based router with
   independent replay; BGS Algorithms 2–4 and 6 as parallel routers; exact
   solvers (BFS and SAT); the winding bound; the `LB = 1` enumerator; the check
   suite. Exposed to Qiskit as a `permutation.<name>` synthesis plugin. As far
   as five indices can tell, the first public implementation of any parallel
   token swapping algorithm.
3. **Computational results on RQ1**: enumerations and SAT certificates,
   instances and encodings archived.
4. **Comparative study** (RQ3a, RQ3b) with lockfile, seeds, version table,
   pass-manager configuration and absolute optimality gaps published.
5. **Thesis document.**

---

## 9. Success criteria

| level | criterion | status now |
|---|---|---|
| **Threshold** | Deliverables 1 and 2 minus the BGS algorithms; the theory note with Theorem A and `σ ≥ 11` as PROVED; `rt(X) = Θ(diam)` reconciled with Yuan–Zhang; documented negative results. | **Secured**: the router, exact solver, winding bound and check suite exist and pass; the reconciliation paragraph is owed. |
| **Threshold, second half** | BGS Algorithms 2–4 and 6 implemented and replayed; the comparative study (Deliverable 4). | **Not started.** Reachable by construction — it depends only on implementing published algorithms and running experiments — but not secured, and the original proposal's front-loading of it is kept for that reason. |
| **Target** | The reduction and Corollary A2 written for device 2-cores with pendants; the `LB = 1` slice of the `2 × 2` patch decided with certificates; an explicit constant for Lemma 3; the novelty sweep closed one way or the other. | Theorems proved for brick rectangles; the two named RQ1 witnesses decided (both 11); extensions, enumeration and constant outstanding. |
| **Stretch** | `σ(heavy-hex) = 11` for the `LB = 1` slice, or a witness above 11; the coloured/incomplete corollaries; the `OPT`-pullback on a class; the general bounded-fiber quotient theorem. | Not started; gated. |
| **Out of scope, stated** | `σ(heavy-hex) = O(1)`; NP-hardness embedded into heavy-hex; constant-competitiveness with Yuan–Zhang. | — |

---

## 10. Risks and what failure looks like

| risk | assessment | mitigation |
|---|---|---|
| Hard theory (RQ2b, reverse reduction) does not close | likely; may be equivalent to an open problem | gated; Target does not depend on it; eight-week box |
| The `LB = 1` enumeration is too large on the `2 × 2` patch | unknown until the cycle systems are counted; each call is ~1 s | count first; symmetry reduction (the patch's reflections); cap at the gate; if it stalls, RQ1 reverts to CONJECTURED on the evidence of the two witnesses, with the ceiling stated |
| Pendant extension is not routine | real; it changes fiber size, phase count and constants | three weeks budgeted; fallback is the theorems for brick rectangles with pendants handled by a trivial pre/post phase, stated as such |
| **Adjacent literature restates a result under different vocabulary** | *it happened once*: Yuan–Zhang say "brick wall", never "hex", and are uncited by BGS | monitor by *structure*: "routing number", "routing via matchings", "permutation routing", "brick wall" + routing; citations to *both* arXiv:2411.18581 and arXiv:2402.02403 in OpenAlex, Semantic Scholar and OpenCitations (they disagree by 5× on the same paper) plus one non-arXiv index; confirm Theorem 9 is in Yuan–Zhang v1 for the priority date |
| Scooped on RQ1/RQ2 exactly | moderate: BGS has 0–1 citations after 22 months and no follow-up, but Yuan–Zhang has 15 citers and 2026 routing-number papers use quotient machinery | theory note to the supervisor by week 14; preprint if the supervisor agrees (section 11) |
| Theorem B is not new | plausible: Jerrum 1985 and circular sorting unchecked | sweep before any note calls it new; the heavy-hex corollary is new regardless |
| **The empirical arm fails** (plugin never ships; benchmarks never run) | the largest engineering item and the least started | M1/M3 milestones; a pinned environment installed in week 3, not week 14; if it fails, the thesis is the theory note plus the package, which already meets the first half of Threshold |
| RQ3b measures nothing | likely on generic circuits, by design of the plugin hook | PTS-shaped workloads (section 5); the null result on generic circuits reported |
| Benchmark methodology criticised | known failure modes | same-problem baselines; both configurations; pinned trials, seed, lockfile; Benchpress; absolute gaps |
| IBM's lattice moves again | it already did (Nighthawk) | the reduction and harness are lattice-agnostic; the grid router deploys on Nighthawk directly |
| Supervision mismatch on combinatorics | real | section 11 |

**Falsification.** The PROVED claims have proofs, but the code can still be
asked to disagree: a SAT schedule of 10 rounds for a face rotation would refute
Theorem B; a device 2-core on which Lemma 2 or the router fails replay would
refute the 2-core extension; a published per-instance quotient reduction found
by the sweep would delete the novelty claim. In each case the document would
be corrected the way section 13 describes, and the thesis would still meet the
first half of Threshold.

---

## 11. Questions for my supervisor

1. Can you supervise a combinatorial proof, or should I seek a co-advisor from
   discrete mathematics? Section 4 is written so such a co-advisor can evaluate
   it on one read.
2. Does the department expect novelty in an undergraduate thesis, or is
   demonstrated research competence sufficient? Section 4 gives one result that
   is new (the instance-wise transfer), one proved but not new
   (`rt = Θ(diam)`), and one whose novelty is plausible but unchecked (the
   winding bound); how much weight should each carry?
3. Is the two-part week-16 gate acceptable as a formal checkpoint, and may the
   theory note be posted as a preprint before examination, given the
   adjacent-literature risk?
4. Compute: no GPU is needed (section 12). Is a machine available that can hold
   a SAT job for a day, with a few tens of GB of RAM, and may I install a
   solver on it?
5. Library access: I need the SIAM 1994 text of Alon–Chung–Graham and the
   Discrete Applied Mathematics text of BGS to confirm theorem numbering;
   arXiv versions are what has been read.
6. What is the department's policy on disclosing AI-assisted work (section
   13)?

---

## 12. Compute

No GPU is needed and none would help: exact PTS is breadth-first search over
token placements, bounded by branching and memory, not arithmetic. Plain BFS
dies near `n = 12`; the bidirectional solver in `pts/exact.py` reaches `n ≈ 13`
at depth 6–7 in a minute or two. The instances that decide RQ1 need **SAT
bounded model checking** (`pts/sat.py`, CaDiCaL via `python-sat`), and the
feasibility question is answered: `n = 35`, `T = 11` takes about a second on a
laptop, with ~15,000 variables and ~300,000 clauses. What scales is the
*number* of instances in the `LB = 1` enumeration, not any single one, and that
is a CPU-hours question, not a hardware one. Reproducibility comes from
determinism — CaDiCaL is deterministic for a fixed input, every `SAT` answer is
replayed independently of the solver, and `UNSAT` answers can carry a DRAT
proof — and from pinned versions and explicit seeds everywhere else. The blank
relaxation in `pts/exact.py` is weak on face instances and is not a substitute.
Everything runs on a laptop; the benchmark sweeps benefit from a few CPU-days
on a shared machine.

---

## 13. AI-assisted work and disclosure

Parts of the theory and all of the documents in this project were developed
with AI assistance, and the record is worth stating plainly. An early
AI-generated proof attempt (`fork.txt.txt`, kept out of version control) was
confidently wrong: its central step "gathers" four tokens onto one vertex,
which is not an operation of the model; one of its lemmas (the brick wall
embeds in the square grid with length-3 detours) is correct and is retained.
The subsequent proof note found the right mechanism — the bounded-fiber
quotient — and proved its lemmas correctly, then overclaimed its headline by
citing BGS for a guarantee they do not prove; the note flagged its own doubt
and did not check. A review of that note, also AI-assisted, was itself wrong
twice, caught by an adversarial audit: it asserted an empirical law that a
larger instance refutes, and it called a result novel that is a corollary of a
2025 paper written in different vocabulary.

Each error was caught the same way — reading the source, running the larger
instance, searching by structure — and those are now the rules of this thesis:
every claim carries a status label; every "verified" has runnable code behind
it, and a check that cannot fail is reported as such (Lemma 2's original test
was one); every load-bearing citation is marked read-at-source or not; negative
novelty claims name the indices and vocabularies they cover. The student is
responsible for every proof and every status judgment. Disclosure will follow
the department's policy, and this section will be reproduced in the thesis.

---

## 14. References

**[v]** — theorem statement read at source (arXiv or extended abstract) during
this revision; **[s]** — known through secondary sources or abstract only, to be
verified before citation in the thesis.

- Bansal, Günlük & Shapley. *Parallel token swapping for qubit routing.*
  Discrete Applied Mathematics 377, 480–497 (2025), DOI 10.1016/j.dam.2025.08.005;
  arXiv:2411.18581. **[v]** (v2; journal text not compared; v1 differs in Thm
  4(a) and remark numbering.)
- Yuan & Zhang. *Full characterization of the depth overhead for quantum circuit
  compilation with arbitrary qubit connectivity constraint.* Quantum 9, 1757
  (2025); arXiv:2402.02403. **[v]**
- Alon, Chung & Graham. *Routing permutations on graphs via matchings.* SIAM J.
  Discrete Math. 7(3), 513–530 (1994); STOC 1993. **[v]** for the extended
  abstract; SIAM theorem numbering **[s]**.
- Alpert, Barnes, Bell, Mauro, Nevo, Tucker & Yang. *Routing by matching on
  convex pieces of grid graphs.* Computational Geometry (2022);
  arXiv:2106.10751. **[v]** — Theorem 4; Section 6, Question 1.
- Li, Lu & Yang. *Routing numbers of cycles, complete bipartite graphs, and
  hypercubes.* SIAM J. Discrete Math. 24(4), 1482–1494 (2010). **[v]**
- Zhang. *Optimal bounds for matching routing on trees.* SIAM J. Discrete Math.
  12, 64–77 (1999). **[s]**
- He, Valentin, Yin & Yu. *Extremal permutations in routing cycles.*
  arXiv:1404.1851. **[v]**; journal reference to confirm.
- Jerrum. *The complexity of finding minimum-length generator sequences.*
  Theoretical Computer Science 36 (1985). **[s]** — to be read for the novelty
  sweep.
- Kawahara, Saitoh & Yoshinaka. *The time complexity of permutation routing via
  matching, token swapping and a variant.* J. Graph Algorithms Appl. 23(1),
  29–70 (2019); arXiv:1612.02948. **[v]** — Thms 3, 4, 5, 8.
- Banerjee & Richards. *New results on routing via matchings on graphs.* FCT
  2017; arXiv:1706.09355. **[v]**
- Aichholzer, Demaine, Korman, Lubiw, Lynch, Masárová, Rudoy, Vassilevska
  Williams & Wein. *Hardness of token swapping on trees.* ESA 2022;
  arXiv:2103.06707. **[v]**
- Miltzow, Narins, Okamoto, Rote, Thomas & Uno. *Approximation and hardness of
  token swapping.* ESA 2016; arXiv:1602.05150. **[v]** (sequential)
- Hiken & Wein. *Improved hardness-of-approximation for token swapping.* ESA
  2025, LIPIcs 351, 57:1–57:16. **[v]** (sequential)
- Demaine, Fekete, Keldenich, Meijer & Scheffer. *Coordinated motion planning:
  reconfiguring a swarm of labeled robots with bounded stretch.* SIAM J.
  Comput. 48(6), 1727–1762 (2019); arXiv:1801.01689. **[v]**
- Childs, Schoute & Unsal. *Circuit transformations for quantum
  architectures.* TQC 2019; arXiv:1902.09102. **[v]**
- Courtney. *Permutation routing on Ramanujan hypergraphs with applications to
  neutral atom quantum architectures.* arXiv:2605.02498 (2026). **[s]**
- Stojmenović. *Honeycomb networks: topological properties and communication
  algorithms.* IEEE Trans. Parallel Distrib. Syst. 8(10) (1997); and
  *(ℓ,k)-routing on plane grids*, arXiv:0803.2759. **[s]** (packet model)
- Weidenfeller, Valor, Gacon, Tornow, Bello, Woerner & Egger. *Scaling of the
  quantum approximate optimization algorithm on superconducting qubit based
  hardware.* Quantum 6, 870 (2022); arXiv:2202.03459. **[v]**
- Kattemölle & Hariharan. *Line-graph qubit routing: from kagome to heavy-hex
  and more.* ACM Trans. Quantum Comput. 6 (2025), DOI 10.1145/3733842;
  arXiv:2306.05385. **[s]**
- Li, Ding & Xie. *Tackling the qubit mapping problem for NISQ-era quantum
  devices.* ASPLOS 2019. **[s]**
- Zou, Treinish, Hartman, Ivrii & Lishman. *LightSABRE.* arXiv:2409.08368.
  **[s]**
- Li, Zhou & Feng. *Benchmarking quantum circuit transformation with QKNOB
  circuits.* IEEE Trans. Quantum Eng. 6, 1–15 (2025),
  DOI 10.1109/TQE.2025.3527399; arXiv:2301.08932. **[v]**
- Ping, Lin, Tan & Cong. *Assessing quantum layout synthesis tools via known
  optimal-SWAP cost benchmarks (QUBIKOS).* arXiv:2502.08839. **[v]** (abstract)
- Nation et al. *Benchmarking the performance of quantum computing software for
  quantum circuit creation, manipulation and compilation (Benchpress).* Nature
  Computational Science 5, 427–435 (2025). **[s]**
- Quetschlich, Burgholzer & Wille. *MQT Bench.* Quantum 7, 1062 (2023). **[s]**
- Li et al. *QASMBench.* ACM Trans. Quantum Comput. 4 (2023). **[s]**
- IBM Quantum. Processor-types documentation; `qiskit-ibm-runtime` fake-provider
  coupling maps (Falcon, Eagle r1/r3, Heron r1/r2/r3, Nighthawk r1). **[v]**
  via audit.
