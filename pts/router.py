"""The five-phase heavy-hex router: cell quotient -> mesh route -> lift back.

Implements exactly the algorithm of section 4 of the proof note, with the
grid router of Assumption (G) instantiated by the classical O(diameter) mesh
router in `gridroute` (which is unconditional, but is not an approximation
relative to LB).
"""

from collections import defaultdict

from .check_lemma2 import cell_permutations, K
from .exact import solve_on
from .gridroute import route
from .pathsort import swap_endpoints


class Stats:
    def __init__(self):
        self.rounds = 0
        self.mesh_rounds = 0
        self.lift_cost = []          # X-rounds spent on each mesh round
        self.colours = []            # conflict-colouring classes per mesh round
        self.path_len = 0
        self.final_rounds = 0


def _greedy_colour(paths):
    """Colour paths so that same-coloured paths are vertex-disjoint."""
    colour = [None] * len(paths)
    order = sorted(range(len(paths)), key=lambda i: -len(paths[i]))
    for i in order:
        taken, si = set(), set(paths[i])
        for j, cj in enumerate(colour):
            if cj is not None and si & set(paths[j]):
                taken.add(cj)
        c = 0
        while c in taken:
            c += 1
        colour[i] = c
    return colour


def _apply(rnd, occ, pos):
    seen = set()
    for u, v in rnd:
        assert u not in seen and v not in seen, "round is not a matching"
        seen |= {u, v}
        occ[u], occ[v] = occ[v], occ[u]
        pos[occ[u]], pos[occ[v]] = u, v


def _lift(g, N, des, occ, pos, schedule, stats):
    """Realise one mesh matching N on X by exchanging designated tokens."""
    pairs = [(p, q) for p, q in N]
    paths = [g.shortest_path(pos[des[p]], pos[des[q]]) for p, q in pairs]
    stats.path_len = max([stats.path_len] + [len(p) for p in paths])
    colour = _greedy_colour(paths)
    stats.colours.append(max(colour) + 1 if colour else 0)

    before = len(schedule)
    for c in sorted(set(colour)):
        group = [paths[i] for i in range(len(paths)) if colour[i] == c]
        per = [swap_endpoints(p) for p in group]
        for i in range(max((len(x) for x in per), default=0)):
            rnd = [e for x in per if i < len(x) for e in x[i]]
            if rnd:
                _apply(rnd, occ, pos)
                schedule.append(rnd)
    for p, q in pairs:
        des[p], des[q] = des[q], des[p]
    stats.lift_cost.append(len(schedule) - before)


def solve(g, pi, dg=None):
    """Return (schedule, stats).  `pi` maps vertex -> target vertex."""
    sigmas, colour, _ = cell_permutations(g, pi)
    occ = {v: v for v in g.vertices}
    pos = {v: v for v in g.vertices}
    schedule, stats = [], Stats()

    for r in range(K):
        des = {}
        by_cell = defaultdict(list)
        for t in g.vertices:
            by_cell[g.phi[pos[t]]].append(t)
        for p in g.grid:
            here = by_cell[p]
            assert here, f"cell {p} emptied -- occupancy invariant broken"
            pick = [t for t in here if colour[t] == r]
            assert len(pick) <= 1, f"two colour-{r} tokens in cell {p}"
            des[p] = pick[0] if pick else here[0]

        mesh = route(g.A, g.B, sigmas[r])
        stats.mesh_rounds += len(mesh)
        for N in mesh:
            _lift(g, N, des, occ, pos, schedule, stats)

    # step 4: fix each cell internally, all cells in parallel
    per_cell = []
    for p in g.grid:
        cell = g.fiber[p]
        if all(pi[occ[v]] == v for v in cell):
            continue
        perm = {v: pi[occ[v]] for v in cell}
        assert sorted(perm.values()) == sorted(cell), \
            f"cell {p} residual is not internal -- a token is in the wrong cell"
        per_cell.append(solve_on(cell, g.induced_adj(cell), perm))
    for i in range(max((len(c) for c in per_cell), default=0)):
        rnd = [e for c in per_cell if i < len(c) for e in c[i]]
        if rnd:
            _apply(rnd, occ, pos)
            schedule.append(rnd)
            stats.final_rounds += 1

    stats.rounds = len(schedule)
    return schedule, stats


def replay(g, schedule, pi):
    """Independent check that `schedule` really realises `pi` on X."""
    edges = {tuple(sorted((u, v))) for u in g.vertices for v in g.adj[u]}
    occ = {v: v for v in g.vertices}
    for rnd in schedule:
        seen = set()
        for u, v in rnd:
            if tuple(sorted((u, v))) not in edges:
                return False, "round uses a non-edge"
            if u in seen or v in seen:
                return False, "round is not a matching"
            seen |= {u, v}
            occ[u], occ[v] = occ[v], occ[u]
    for v in g.vertices:
        if occ[pi[v]] != v:
            return False, f"token {v} ended on the wrong vertex"
    return True, "ok"
