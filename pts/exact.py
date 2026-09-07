"""Exact parallel token swapping by breadth-first search over placements.

Only for tiny graphs: the state space is n!.  Used for the within-cell
permutations (n <= 5) and for small stretch-factor experiments.
"""

from collections import deque
from functools import lru_cache


def all_matchings(n, edges):
    """Every matching of the graph, as a tuple of edges (including the empty one)."""
    edges = list(edges)
    out = []

    def rec(i, used, cur):
        if i == len(edges):
            out.append(tuple(cur))
            return
        rec(i + 1, used, cur)
        a, b = edges[i]
        if not (used >> a & 1) and not (used >> b & 1):
            cur.append((a, b))
            rec(i + 1, used | 1 << a | 1 << b, cur)
            cur.pop()

    rec(0, 0, [])
    return out


def apply_matching(state, m):
    s = list(state)
    for a, b in m:
        s[a], s[b] = s[b], s[a]
    return tuple(s)


def solve(n, edges, target, matchings=None):
    """`target[i]` is the token that must end on vertex i.

    Bidirectional BFS.  Applying a matching is an involution, so the same move
    set generates the backward search.  Returns (rounds, schedule).
    """
    start = tuple(range(n))
    target = tuple(target)
    if start == target:
        return 0, []
    ms = [m for m in (matchings if matchings is not None
                      else all_matchings(n, edges)) if m]

    fwd = {start: None}          # state -> (parent, matching)
    bwd = {target: None}
    ffront, bfront = [start], [target]

    def expand(front, seen, other):
        nxt, hit = [], None
        for s in front:
            for m in ms:
                t = apply_matching(s, m)
                if t in seen:
                    continue
                seen[t] = (s, m)
                if t in other:
                    hit = t
                nxt.append(t)
        return nxt, hit

    def chain(seen, s):
        out = []
        while seen[s] is not None:
            s, m = seen[s]
            out.append(m)
        return out

    while True:
        if len(ffront) <= len(bfront):
            ffront, hit = expand(ffront, fwd, bwd)
        else:
            bfront, hit = expand(bfront, bwd, fwd)
        if hit is not None:
            sched = chain(fwd, hit)[::-1] + chain(bwd, hit)
            return len(sched), sched
        if not ffront or not bfront:
            raise ValueError("target unreachable")


def solve_on(vertices, adj, perm):
    """`perm` maps vertex -> target vertex.  Returns rounds as lists of vertex pairs."""
    idx = {v: i for i, v in enumerate(vertices)}
    edges = sorted({tuple(sorted((idx[u], idx[w])))
                    for u in vertices for w in adj[u] if w in idx})
    target = [None] * len(vertices)
    for v in vertices:
        target[idx[perm[v]]] = idx[v]       # token from v ends on perm[v]
    _, sched = solve(len(vertices), edges, target)
    return [[(vertices[a], vertices[b]) for a, b in m] for m in sched]


def solve_relaxed(n, edges, labeled, target_of, matchings=None, cap=12):
    """Lower bound on OPT when only `labeled` vertices carry tracked tokens.

    Unlabelled tokens are indistinguishable and unconstrained, so this is a
    relaxation of parallel token swapping: its optimum is <= the true OPT.
    `target_of[v]` is the vertex the token starting on `v` must reach.
    """
    BLANK = -1
    start = tuple(i if i in labeled else BLANK for i in range(n))
    goal = {}
    for v in labeled:
        goal[target_of[v]] = v

    def done(s):
        return all(s[u] == t for u, t in goal.items())

    ms = [m for m in (matchings if matchings is not None
                      else all_matchings(n, edges)) if m]
    if done(start):
        return 0
    seen = {start}
    frontier = [start]
    for depth in range(1, cap + 1):
        nxt = []
        for s in frontier:
            for m in ms:
                t = apply_matching(s, m)
                if t in seen:
                    continue
                seen.add(t)
                if done(t):
                    return depth
                nxt.append(t)
        frontier = nxt
        if not frontier:
            raise ValueError("target unreachable")
    return None            # > cap
