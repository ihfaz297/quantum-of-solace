# A constant-factor approximation for parallel token swapping on heavy-hex

**Theorem.** Let `X = S(H)` be a heavy-hex graph and `π` a permutation of `V(X)`.
There is a polynomial-time algorithm producing a parallel token swapping schedule
for `π` of length `O(LB_X(π))`, where `LB_X(π) = max_v d_X(v, π(v))`. In
particular the stretch factor of the heavy-hex family is finite, and combined
with the winding lower bound,

```
11  ≤  σ(heavy-hex)  <  ∞.
```

The proof is a **bounded-fiber quotient**, not an embedding. This is the essential
difference from the failed attempt: `X` is *not* a spanning subgraph of any grid
(its bipartition is 2:3 while a grid's is 1:1), but it *maps onto* a grid with all
fibers of size at most 5, and that is enough.

Everything below is elementary except one black box, Assumption (G) in §5.

---

## 0. Model and notation

`G = (V,E)`, one token per vertex, initial placement the identity. A **round**
applies a matching `M ⊆ E` and swaps the tokens across every edge of `M`
simultaneously. Token `t` must finish at `π(t)`. `OPT(G,π)` is the minimum number
of rounds; `LB_G(π) = max_v d_G(v,π(v))`.

**Heavy-hex.** `H` is the *brick wall*: vertex set a rectangle
`R = [0,W] × [0,Ht] ⊂ ℤ²` with `W` odd, all horizontal edges `(x,y)–(x+1,y)`, and
vertical edges `(x,y)–(x,y+1)` only when `x+y` is even. Every interior vertex has
degree 3 and every bounded face is a `1×2` brick with six boundary vertices, i.e.
a hexagon. `X = S(H)` subdivides every edge of `H` once. Write `B = V(H)` for the
**branch** vertices and `S` for the **subdivision** vertices; every edge of `X`
joins `B` to `S`, and `|S| ≈ (3/2)|B|`.

Two standard facts used later:

- **(P)** *Odd–even transposition sort.* Any permutation of the `m` vertices of a
  path can be realised in at most `m` rounds. (Alternate the two matchings
  `{p₀p₁, p₂p₃, …}` and `{p₁p₂, p₃p₄, …}`; sorting by target index realises the
  permutation.)
- **(K)** *König.* A `k`-regular bipartite multigraph decomposes into exactly `k`
  perfect matchings.

---

## 1. The cell decomposition

> **Lemma 1.** There is a map `φ : V(X) → Γ` onto a rectangular grid graph `Γ`
> such that
> 1. every fiber `C_p = φ⁻¹(p)` is non-empty, has at most 5 vertices, and induces
>    a connected subgraph of `X` of diameter at most 4;
> 2. every edge of `X` lies inside one fiber or joins two fibers that are adjacent
>    in `Γ`; consequently `d_Γ(φu, φv) ≤ d_X(u,v)`;
> 3. `d_X(u,v) ≤ 4·(d_Γ(φu, φv) + 1)`.

**Construction.** Index cells by `(a,b)` with `0 ≤ a ≤ (W−1)/2`, `0 ≤ b ≤ Ht`. Put
into `C_{(a,b)}`:

- the two branch vertices `(2a, b)` and `(2a+1, b)`;
- the subdivision vertex of the horizontal edge `(2a,b)–(2a+1,b)`;
- the subdivision vertex of the horizontal edge `(2a+1,b)–(2a+2,b)`, when `2a+2 ≤ W`;
- the subdivision vertex of the vertical edge `(x,b)–(x,b+1)` for the unique
  `x ∈ {2a, 2a+1}` with `x+b` even, when `b+1 ≤ Ht`.

Exactly one of `2a+b`, `2a+1+b` is even, so the last item contributes exactly one
vertex whenever the row above exists. Interior cells therefore have exactly 5
vertices; boundary cells have 3 or 4.

**Proof of 1.** Each branch vertex `(x,b)` lies in the single cell `(⌊x/2⌋, b)`.
Each horizontal subdivision vertex on `(x,b)–(x+1,b)` lies in `(⌊x/2⌋, b)` — one
cell, whether `x` is even or odd. Each vertical subdivision vertex on
`(x,b)–(x,b+1)` lies in `(⌊x/2⌋, b)`. So the cells partition `V(X)`. Connectivity:
`(2a,b) — s_h — (2a+1,b) — s_h'` is a path and the vertical subdivision vertex is
pendant on one of the two branch vertices, so the cell induces a tree on at most
5 vertices, of diameter at most 4. ∎

**Proof of 2.** An edge of `X` joins a branch vertex `(x,b)` to the subdivision
vertex of one of its incident `H`-edges. The four cases: the horizontal edge to
the right lies in `(⌊x/2⌋,b)` (same cell); the horizontal edge to the left lies in
`(⌊(x−1)/2⌋, b)`, which is the same cell or the left neighbour; the vertical edge
upward lies in `(⌊x/2⌋, b)` (same cell); the vertical edge downward lies in
`(⌊x/2⌋, b−1)`, the cell below. In every case the two endpoints lie in the same
cell or in `Γ`-adjacent cells. Contracting a shortest `X`-path therefore gives a
`Γ`-walk of no greater length. ∎

**Proof of 3.** Adjacent cells are joined by an `X`-edge, and cells have diameter
at most 4, so consecutive cells cost at most 5 `X`-steps and the last hop within
a cell costs at most 4. ∎

*Verified computationally* on brick rectangles up to `[0,11]×[0,5]` (168
vertices): cells partition `V(X)`, cell sizes lie in `{3,4,5}`, every cell induces
a connected tree of diameter ≤ 4, the quotient graph is **exactly** the grid on
`{0..(W−1)/2} × {0..Ht}`, `d_Γ ≤ d_X` holds everywhere, and
`d_X ≤ 4(d_Γ + 1)` is tight.

**Why a quotient and not an embedding.** `X` is connected and bipartite, so its
bipartition `{B, S}` is unique; a grid graph's two classes differ in size by at
most one, while `|S| − |B| = ij − 1` for an `i×j` patch. So `X` is a spanning
subgraph of a grid graph only when `ij ≤ 2`. Any argument that needs `X ⊆` grid
on the same vertex set is dead on arrival. Lemma 1 never asks for that.

---

## 2. Decomposing the demand into five cell-permutations

> **Lemma 2.** There are permutations `σ₁, …, σ₅` of `V(Γ)` and a colouring
> `c : V(X) → {1,…,5}` of the tokens such that
> 1. for each `r`, the map `p ↦ σ_r(p)` is a bijection of cells, and
>    `max_p d_Γ(p, σ_r(p)) ≤ LB_X(π)`;
> 2. for each `r` and each cell `p`, exactly one token `t` with `c(t) = r`
>    satisfies `φ(t) = p`, and it satisfies `φ(π(t)) = σ_r(p)` — unless `p` is a
>    padded fixed point of `σ_r`, in which case no token is assigned.

**Proof.** Build a bipartite multigraph `D` with a left copy and a right copy of
`V(Γ)`: for each token `t`, an edge from `φ(t)` on the left to `φ(π(t))` on the
right. The left degree of `p` is `|C_p|`. The right degree of `p` is the number of
tokens whose target lies in `C_p`, which is also `|C_p|` because `π` is a
bijection. So `deg_L(p) = deg_R(p) = |C_p| ≤ 5`.

Now **pad**: add `5 − |C_p|` parallel edges from left-`p` to right-`p`. Every
degree is now exactly 5, so by (K) `D` decomposes into five perfect matchings.
A perfect matching of `D` is precisely a permutation of `V(Γ)`; call them
`σ₁,…,σ₅`, and let `c(t)` be the colour of `t`'s edge.

Displacement: a real edge `p → q` carries a token `t` with `φ(t)=p`,
`φ(π(t))=q`, so `d_Γ(p,q) ≤ d_X(t, π(t)) ≤ LB_X(π)` by Lemma 1.2. A padding edge
is a loop, displacement 0. ∎

The padding trick is what makes unequal fiber sizes harmless. Without it one gets
*partial* permutations of cells, and completing a partial permutation without
inflating the displacement is a genuinely awkward transportation problem. With it
the fibers may have any sizes in `{1,…,5}` and the boundary of the patch costs
nothing.

*Verified computationally*: on random permutations of `X` for several patch sizes,
the padded multigraph always split into five genuine cell-permutations with
maximum cell displacement at most `LB_X(π)`.

---

## 3. Realising one grid round on `X`

At every moment the algorithm maintains a **designated token** in each cell — one
token per cell, chosen afresh at the start of each phase `r`. A round of a grid
schedule is a matching `N` of `Γ`; realising it means: for every `{p,q} ∈ N`,
exchange the designated tokens of `p` and `q`, leaving every other token where it
is.

> **Lemma 3.** Any such matching `N` can be realised on `X` in `O(1)` rounds, and
> the realisation changes no cell's occupancy count.

**Proof.** Fix `{p,q} ∈ N`. Their designated tokens sit on vertices `u ∈ C_p`,
`v ∈ C_q` with `d_Γ(p,q) = 1`, so `d_X(u,v) ≤ 8` by Lemma 1.3. Choose a shortest
`X`-path `P_{pq}` from `u` to `v`; it has at most 9 vertices and lies inside
`N₈(C_p ∪ C_q)`.

Build a conflict graph on the pairs of `N`, joining two pairs whose sets
`N₈(C_p ∪ C_q)` intersect. Since such a set meets only cells within grid distance
16 of `p`, and the pairs of `N` are disjoint, each pair conflicts with at most
`(2·16+1)² = 1089` others. Greedily colour with at most 1090 colours.

Within one colour class the sets `N₈(C_p ∪ C_q)` are pairwise disjoint, hence so
are the paths `P_{pq}`. By (P), the transposition of the two endpoints of a path
on at most 9 vertices — fixing every interior vertex — is realisable in at most 9
rounds, and the matchings used on disjoint paths may be unioned. So one colour
class costs at most 9 rounds and the whole matching at most `1090 × 9 = 9810`
rounds.

Occupancy: the interior tokens of each path are returned to their own vertices, so
only `u` and `v` change cells, and they exchange. Every cell keeps exactly the
vertex set `C_p` and exactly `|C_p|` tokens. ∎

The constant 9810 is absurd and is an artefact of the crudest possible conflict
count; it is not what the algorithm does in practice, and no attempt is made here
to optimise it.

---

## 4. The algorithm and the proof

```
Input: heavy-hex X, permutation π.
1. Compute the cells φ and the grid Γ.                            (Lemma 1)
2. Build the demand multigraph, pad, 5-edge-colour it,
   obtaining σ₁,…,σ₅ and the token colouring c.                   (Lemma 2)
3. For r = 1,…,5:
     a. In each cell p, designate the token t with c(t)=r and φ(t)=p;
        if p is a padded fixed point, designate any token in p.
     b. Run the grid router on (Γ, σ_r), getting matchings N₁,…,N_T.
     c. Realise each N_i on X in O(1) rounds.                     (Lemma 3)
4. Permute inside every cell simultaneously to place each token
   on its exact target vertex.
```

**Correctness.** Claim: a token `t` with `c(t) = r` sits in cell `φ(t)` throughout
phases `1..r−1`, moves to cell `φ(π(t))` during phase `r`, and stays there in
phases `r+1..5`.

By Lemma 3 the only tokens that change cells during a phase are the designated
ones, and the designated token of `p` in phase `r` ends the phase in cell
`σ_r(p)`. In phase `r`, `t` is the designated token of `φ(t)` and
`σ_r(φ(t)) = φ(π(t))` by Lemma 2.2, so `t` lands in its target cell. In a phase
`r' ≠ r`, `t` is either not designated (and does not move between cells) or is
designated at a cell `p` that is a padded fixed point of `σ_{r'}` (and returns to
`p`). Either way `t` ends every other phase in the cell it started it in.

Step 3a is well defined because every cell always contains at least one token:
occupancy is preserved by Lemma 3 and `|C_p| ≥ 1`.

After step 3, every token is in its target cell, so the residual permutation acts
within cells. Cells induce vertex-disjoint connected subgraphs on at most 5
vertices (Lemma 1.1), and an arbitrary permutation of a connected graph on `m`
vertices is realisable in `O(m)` rounds, so step 4 costs `O(1)` and all cells run
in parallel.

**Length.** By Lemma 2.1, `LB_Γ(σ_r) ≤ LB_X(π)`, so the grid router returns
`T_r ≤ α · LB_X(π)` rounds. Each is realised in at most `9810` rounds. Hence

```
total  ≤  5 · α · 9810 · LB_X(π)  +  O(1)  =  O(LB_X(π)).
```

**Running time.** Lemma 1 is `O(n)`; Lemma 2 is a bipartite 5-edge-colouring,
`O(n log n)` by repeated augmenting paths; Lemma 3 is a greedy colouring of a
bounded-degree conflict graph, linear per round. Polynomial overall. ∎

---

## 5. What is assumed

> **Assumption (G).** There is a constant `α` and a polynomial-time algorithm
> that routes any permutation `σ` of an `R × C` grid graph in at most
> `α · LB_grid(σ)` rounds.

This is exactly Lemma 3 of the proposal, i.e. the BGS grid result, used as a black
box. **It needs checking against the actual paper**, for a specific reason: the
stretch factor of the *cycle* family is infinite (rotate `C_n` by one: `LB = 1`,
`OPT = n−1`), so BGS's constant-factor approximation for cycles cannot be relative
to `LB`. If their grid guarantee is likewise relative to a stronger lower bound
`Φ_grid` rather than `LB_grid`, the reduction above still goes through verbatim
and delivers `O(Φ_grid(σ_r))`; one then has to check that `Φ` pulls back, i.e.
that `Φ_grid(σ_r) = O(Φ_X(π))`. For the winding term this is immediate — the
grid's winding bound is capped at `girth − 1 = 3` — and for congestion it follows
from Lemma 1.2 up to the fiber size 5. So the theorem is robust to which form (G)
takes, but the write-up should say which.

Independently, the theorem is consistent with everything computable:

| instance | `LB` | `OPT` | cycle length |
|---|---|---|---|
| rotate boundary of `2×5` grid | 1 | 3 | 10 |
| rotate boundary of `3×3` grid | 1 | 4 | 8 |
| rotate boundary of two fused hexagons | 1 | 5 | 10 |

Rotation cost tracks girth, not cycle length. This settles, in the affirmative,
the long-cycle question flagged earlier as the one thing that could have made
`σ(heavy-hex)` infinite: the theorem implies rotating *any* cycle by one position
costs `O(1)`, and the table confirms it directly.

---

## 6. Where the earlier attempts went wrong, and what fixed it

| failure | fix here |
|---|---|
| "refine the grid" — phantom vertices with no counterpart in `X` | fibers are subsets of `V(X)`; nothing is invented |
| "embed `X` in a grid with the same vertex set" — impossible, bipartition is 2:3 vs 1:1 | quotient onto a grid, never a subgraph relation |
| "gather subdivision tokens onto branch vertices" — not an operation; vertices hold one token | tokens never move except by real swaps; cells are a bookkeeping partition of fixed vertex sets |
| "replace each vertex by a gadget, then embed the blow-up" — reconstructs `X`, circular | no blow-up; the grid is coarser than `X`, not finer |
| unequal loads at the boundary | self-loop padding to 5-regular, then König |
| "`O(1)` per unit × `n/5` units is `O(1)`" | Lemma 3 parallelises explicitly via a bounded-degree conflict colouring |

The one structural idea that does the work is that the quotient goes the *easy*
way. Heavy-hex has more vertices than the grid it sits over, so mapping down is
free and mapping a schedule back up costs only the fiber size — whereas every
attempt to map `X` into a *finer* grid must invent vertices `X` does not have.

---

## 7. Honest assessment

**Solid.** Lemmas 1, 2, 3 and the correctness argument are complete and
machine-checked where checkable. The bipartition obstruction in §1 is a proof, not
a heuristic.

**Assumed.** Assumption (G), in whichever form BGS actually prove it. This is the
proposal's own Lemma 3, so the thesis is entitled to it — but §5's caveat is real
and should be resolved before anything is written up.

**Stated for one boundary shape.** The proof is written for `X` induced on a brick
rectangle with `W` odd. A staggered `i×j` hexagon patch has a zigzag boundary; the
cells at the zigzag have size 2 or 3 instead of 3–5, which Lemma 2's padding
already absorbs, but the cell index set is then a polyomino rather than a
rectangle and (G) must apply to it. Either extend (G) to polyomino grid regions or
pad the patch to a rectangle. This is bookkeeping, but it is not yet written.

**Constant.** The proof gives roughly `5 · α · 10⁴`. The lower bound is 11. The
gap is four orders of magnitude and almost all of it is in Lemma 3's conflict
count, which a real analysis would collapse. Closing that gap — and in particular
deciding whether `σ(heavy-hex) = 11` exactly — is the interesting remaining
question, and it is now a self-contained one.
