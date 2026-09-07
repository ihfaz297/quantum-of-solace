# Review of the heavy-hex approximation note

Scope: `heavy-hex-approximation-proof.md`, `fork.txt.txt`, and
`thesis-proposal-parallel-token-swapping.docx`. Every claim called *verified*
below is checked by the code in [pts/](pts/); run `python -m pts.check_all`.

---

## 1. Verdict

The **method is sound and worth writing up**. The bounded-fiber quotient is the
right idea, it is correctly executed, and I could not break Lemmas 1, 2 or 3.
The five-phase algorithm is implemented in [pts/router.py](pts/router.py) and
independently replayed on 56 random permutations across 7 patch sizes up to
n = 168: it always realises pi, every round is a genuine matching, and the
occupancy invariant never breaks.

The **headline theorem is overclaimed**, for one reason: Assumption (G) is not a
theorem in BGS. It is not a small gap. `sigma(heavy-hex) < infinity` does not
follow, and neither does anything in section 5 that depends on it.

Section 3 below is what you can claim instead. It is less than the note claims
but more than nothing, and one tier of it is unconditional.

---

## 2. The one real error: Assumption (G)

The note assumes:

> **Assumption (G).** There is a constant `a` and a polynomial-time algorithm
> that routes any permutation `sigma` of an `R x C` grid graph in at most
> `a * LB_grid(sigma)` rounds.

and calls this "exactly Lemma 3 of the proposal, i.e. the BGS grid result".
It is not. From arXiv:2411.18581v2 (Bansal, Gunluk & Shapley):

| what the note assumes | what BGS actually prove |
|---|---|
| `<= a * LB_grid(sigma)`, multiplicative in **LB** | **Thm 4(b):** for an `h x n` grid with `h <= n`, `h >= 3`, a solution of value `<= 2*OPT + 2h` — multiplicative in **OPT**, additive in `h` |
| grid stretch factor is `O(1)` | **Remark 14:** the stretch factor of `d_max` on grids "can be bounded by `O(h)`", and they note it is not fully characterised |
| — | **Thm 5(b):** the stretch factor of `d_max` on `n`-cycles is between `n-1` and `n` |

So `sigma(grid) = O(1)` is **open**, and it is open in the same paper the note
cites for it. Section 5 already spotted the smell — "the stretch factor of the
*cycle* family is infinite ... so BGS's constant-factor approximation for cycles
cannot be relative to `LB`" — and that instinct was exactly right. It just
resolves the wrong way: the grid guarantee is *also* not relative to `LB`.

Three consequences, all in sections 5 and 7:

- `11 <= sigma(heavy-hex) < infinity` — the upper half is unproven. (The
  lower half is also unproven, but section 6 finds real support for it.)
- "the theorem implies rotating *any* cycle by one position costs `O(1)`" —
  does not follow.
- "This settles, in the affirmative, the long-cycle question flagged earlier as
  the one thing that could have made `sigma(heavy-hex)` infinite" — it does not
  settle it. That question is still open, and it is now visibly the same
  question as `sigma(grid) = O(1)?`.

Section 5's fallback ("if their grid guarantee is relative to a stronger lower
bound `Phi_grid`, the reduction still goes through and delivers
`O(Phi_grid(sigma_r))`") does survive, and it is the right instinct — but `Phi`
here is `OPT_grid`, and `OPT_grid(sigma_r) = O(OPT_X(pi))` is not established.
Pulling `OPT` back through the quotient is a genuinely different problem from
pulling `LB` back, because the five `sigma_r` come from a Koenig decomposition
that no `X`-schedule need respect. **This is the gap to attack**, and it is a
good problem.

---

## 3. What survives

The quotient is a *reduction*, and it is unaffected by any of the above. State
it that way and the note gets stronger, not weaker.

> **Reduction theorem (verified).** Let `X = S(H)` on the brick rectangle
> `[0,W] x [0,Ht]` with `W` odd, and `Gamma` its quotient grid on
> `{0..(W-1)/2} x {0..Ht}`. Given any mesh router `A` using `f(sigma)` rounds on
> a permutation `sigma` of `Gamma`, there is a polynomial-time algorithm routing
> any permutation `pi` of `V(X)` in at most
>
> ```
> 5 * c3 * max_r f(sigma_r)  +  c4     rounds,
> ```
>
> where `sigma_1 ... sigma_5` are the cell-permutations of Lemma 2, each
> satisfying `LB_Gamma(sigma_r) <= LB_X(pi)`, and `c3`, `c4` are absolute
> constants.

Everything in the note's Lemmas 1-3 goes into proving this, and nothing is lost.
Then three tiers hang off it:

**Tier 1 — unconditional, no black box.** Instantiate `A` with the classical
column-row-column mesh router ([pts/gridroute.py](pts/gridroute.py)), which
routes any mesh permutation in `2(B+1) + (A+1)` rounds. This gives a heavy-hex
router using `O(A + B) = O(diam X)` rounds for *every* permutation, so

```
rt(X) = Theta(diam X) = Theta(sqrt n)   for square patches,
```

the lower bound being trivial. No assumption, no open problem. I have not found
this stated anywhere for heavy-hex, and it is strictly better than the `O(n)`
that follows from Alon-Chung-Graham or from Weidenfeller et al.'s
`n + sqrt(n) + 61`. **If you write up nothing else, write up this.**

**Tier 2 — conditional on BGS Remark 14.** Chaining
`OPT_Gamma(sigma_r) <= O(h) * LB_Gamma(sigma_r) <= O(h) * LB_X(pi)` through
Thm 4(b) gives `sigma(X) = O(h)`, `h` the short side of `Gamma`. A refinement of
Tier 1 for long thin patches and low-`LB` permutations.

**Tier 3 — the original claim, now correctly labelled.** `sigma(grid) = O(1)`
implies `sigma(heavy-hex) = O(1)`. Conditional on an open problem.

The reduction also means **any future grid result transfers to heavy-hex for
free**. That is a better selling point than a constant nobody can evaluate.

**The question worth asking next:** is there a reduction the *other* way, from
grid PTS to heavy-hex PTS? If yes, `sigma(heavy-hex) = Theta(sigma(grid))` and
RQ2 is *equivalent* to a problem BGS left open — which is important for the
thesis to know, and which turns a failure into a publishable theorem.

---

## 4. Machine verification

The note says "*Verified computationally*" twice but ships no code. It does now.

| claim | result |
|---|---|
| Lemma 1: `phi` partitions `V(X)`, fibers of size <= 5, each a tree of diameter <= 4, quotient **exactly** the grid, `d_Gamma <= d_X <= 4(d_Gamma+1)` | **verified**, 36 shapes, `W` odd in `1..11`, `Ht` in `0..5`, up to n = 168 |
| Lemma 2: padded demand multigraph is 5-regular, splits into 5 cell-permutations, `max_p d_Gamma(p, sigma_r(p)) <= LB_X(pi)` | **verified**, 300 random permutations, 15 shapes |
| Section 4 algorithm realises `pi` | **verified** by independent replay, 56 random permutations, 7 shapes |
| Section 5 table (three rotation instances) | **reproduced exactly**: 3, 4, 5 |
| `OPT(C_m` rotate by one`) = m - 1` | **reproduced** for `m = 5, 6` |
| winding probe: legs vs. chords (section 6) | legs never reduce rotation cost; one chord takes it to girth `- 1` |

The note's own reported numbers all check out. `n = 168` for `[0,11]x[0,5]` and
cell sizes `{3,4,5}` are right on the nose.

One detail: the stated bound `d_X <= 4(d_Gamma + 1)` is **true** (measured
`max(d_X - 4*d_Gamma) = 4` exactly, on every shape), but the proof given for it
derives `5*d_Gamma + 4`, which does not imply it. The bound is fine; the proof
of Lemma 1.3 needs one more line.

---

## 5. The `O(1)` constants, measured

Section 3 apologises for `1090 x 9 = 9810` and says a real analysis would
collapse it. It collapses by about **700x**:

| quantity | proof's bound | measured (n <= 168) |
|---|---|---|
| `X`-path length per grid edge | <= 9 vertices | **9** — the proof is tight here |
| conflict-graph colours | <= 1090 | **2** |
| `X`-rounds per grid round (`c3`) | <= 9810 | **<= 14** |
| final within-cell phase (`c4`) | `O(1)` | **5** |
| end-to-end `rounds / LB_X`, random `pi` | — | **plateaus at approx 20-25** |

The path-length bound being exactly tight is a good sign that Lemma 1.3 is the
right shape. The 1089 conflict count is the crudest possible estimate of a
quantity that is 2 in practice; do the real analysis and the constant becomes
presentable. Note the last row is *random* permutations, where `LB ~ diam` makes
life easy — it is evidence for Tier 1, not for `sigma(X) < infinity`.

---

## 6. Smaller corrections

**`sigma(heavy-hex) >= 11` is asserted, never proved — but it is well
supported, and section 5 reads the evidence backwards.** The bound appears in
the theorem statement and in section 7, attributed in `fork.txt.txt` to a
"winding bound (Theorem B)" that is not in either file. The natural argument is
girth`(X) = 12`, so rotating a shortest cycle costs 11 at `LB = 1`; the worry is
that the six branch vertices of a hexagonal face have legs leading out, so
tokens might escape and shortcut. I tested exactly that:

| rotate `C_m` by one | `m = 4` | `m = 6` |
|---|---|---|
| bare cycle | 3 | 5 |
| + a dead-end leg off every other vertex | 3 | 5 |
| + legs off every other vertex, all joined to a hub (a real escape route) | 3 | 5 |
| + one chord | 2 | 3 |

**Legs never help. Only chords do**, and then the cost is exactly
girth `- 1`. So section 5's slogan — "rotation cost tracks girth, not cycle
length" — is *right*, and it is right for a reason the note does not state:
legs do not shorten girth, chords do.

But the note then uses that slogan to conclude rotations are *cheap* in
heavy-hex, which is backwards. `X` has girth 12 and its faces have **no chords**
— the legs point outward. Girth 12 makes face rotations *expensive*: it is the
`>= 11` lower bound, not evidence for a finite upper bound. The sentence "This
settles, in the affirmative, the long-cycle question ... that could have made
`sigma(heavy-hex)` infinite" is therefore doubly wrong: it does not follow from
(G), and the data it cites points the other way.

The reason section 5's table misled: **none of its three rows is a heavy-hex
graph, and the one hexagonal row has a chord.** Two rows are square grids; the
third is the *unsubdivided* fused-hexagon graph, which is `C_10` plus the chord
`{0,5}` (the shared edge) — girth 6, rotates in 5 = girth `- 1`, exactly as the
table above predicts. It rotates cheaply *because of the chord*, a feature `X`
does not have. Replace those three rows with leg-only instances and the table
supports `>= 11` instead of undercutting it.

Proving it needs the six degree-2 subdivision vertices on a face to block
shortcuts. That now looks like a real theorem rather than a hopeful one, and it
is the most promising short paper in the pile.

**`fork.txt.txt` is superseded, but section 6's table mis-attributes its
failure.** Its Lemma 2 is actually *correct* — `H` really is the square grid on
`Z^2` minus the odd-parity vertical edges, and the length-3 detour
`(x,y) -> (x+1,y) -> (x+1,y+1) -> (x,y+1)` really does lie in `H`, since
`(x+1)+y` is even exactly when `x+y` is odd. The fatal step is Lemma 1's
"gathering", which asks a branch vertex to hold four tokens — as section 6 says.
But the row "*embed `X` in a grid with the same vertex set — impossible,
bipartition is 2:3 vs 1:1*" attacks a claim `fork.txt.txt` never makes about
`X`; it makes it about `H`, where it is true. The bipartition obstruction in
section 1 is still correct and still worth keeping — just not as a refutation of
that file.

**Provenance.** `fork.txt.txt` is a chat transcript, and it contains a
confident, detailed, wrong proof. The current note is much better but overclaims
in exactly the place where it accepted a citation without opening the paper. For
an undergraduate thesis both facts matter: check your department's disclosure
rules, and treat "verified computationally" as meaning code someone else can
run.

---

## 7. The thesis proposal

The proposal itself is **not out of line** — it is unusually well built. The
"Scope caveat" (PTS is not qubit routing) is exactly the distinction most papers
in this area blur, the week-16 gate with binary criteria is good practice, and
securing the threshold deliverable first is the right instinct. Four changes:

1. **Section 5, Phase 3.** Replace "primary route (unfolding)" with the
   quotient. It is better and it already works. Keep the backup route.
2. **Section 4, RQ2.** Reframe: *"Does heavy-hex PTS reduce to grid PTS, and is
   the reduction tight?"* That question is answerable — half of it is answered
   above — whereas "does heavy-hex admit a constant-factor approximation" is
   very likely equivalent to a problem BGS left open. Do not aim an
   undergraduate thesis at that without saying so out loud.
3. **Section 6, decision gate.** Tier 1 (`rt(X) = Theta(diam X)`) is done and
   unconditional. That already clears the week-16 gate's "proven stretch-factor
   bound for at least one heavy-hex family" if the gate is worded as a
   routing-number bound. The criteria should be rewritten now that the landscape
   is clearer.
4. **Section 8, success criteria.** Move "constant-factor approximation" from
   *Stretch* to *out of scope, with the reduction as the deliverable instead*.
   Add the reduction theorem at *Target*.

Section 11 references are accurate. Section 3's characterisation of BGS ("give
the first constant-factor approximations for cycles, subdivided stars, and
grids, and analyze stretch-factor tightness") is correct as written — the
proposal never made the mistake the proof note made.

---

## 8. Compute

No GPU. Nothing here is GPU-shaped: the exhaustive solver is a breadth-first
search over token placements, bounded by branching and memory, not arithmetic.
What actually helps, in order:

1. **A SAT solver** (`python-sat`, or Kissat via CNF) for "is there a schedule of
   length T?" as bounded model checking. This is the standard way exact PTS is
   computed at n = 20-40, and it is the single highest-leverage tool for Phase 1.
2. **Symmetry reduction and the blank relaxation** already in
   [pts/exact.py](pts/exact.py) (`solve_relaxed`): tracking only the tokens you
   care about and leaving the rest indistinguishable gives a rigorous lower
   bound on OPT at a fraction of the state space.
3. **A compiled inner loop** (Rust/PyO3, as the proposal already contemplates)
   for the benchmark sweeps.

Plain BFS runs out at about n = 12 in Python. Bidirectional BFS
([pts/exact.py](pts/exact.py)) gets you to n = 10-12 comfortably at depth <= 6.
For the hexagonal face question (n = 16, depth ~11) you need the SAT encoding.
