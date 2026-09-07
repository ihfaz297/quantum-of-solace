"""Decomposition of a k-regular bipartite multigraph into k perfect matchings.

Hall's condition holds for the *support* of a regular bipartite multigraph, so
repeatedly extracting a perfect matching of the support and decrementing
multiplicities leaves a (k-1)-regular multigraph. Matching is Hopcroft-Karp.
"""

from collections import defaultdict, deque


def _hopcroft_karp(left, adj):
    INF = float("inf")
    match_l = {u: None for u in left}
    match_r = {}
    for u in left:                       # greedy warm start
        for v in adj[u]:
            if v not in match_r:
                match_l[u], match_r[v] = v, u
                break

    while True:
        dist = {}
        dq = deque()
        for u in left:
            if match_l[u] is None:
                dist[u] = 0
                dq.append(u)
        found = False
        while dq:
            u = dq.popleft()
            for v in adj[u]:
                w = match_r.get(v)
                if w is None:
                    found = True
                elif w not in dist:
                    dist[w] = dist[u] + 1
                    dq.append(w)
        if not found:
            return match_l

        def aug(u):
            for v in adj[u]:
                w = match_r.get(v)
                if w is None or (dist.get(w) == dist[u] + 1 and aug(w)):
                    match_l[u], match_r[v] = v, u
                    return True
            dist[u] = INF
            return False

        for u in left:
            if match_l[u] is None:
                aug(u)


def decompose(nodes, mult, k):
    """`mult[(u, v)]` is the multiplicity of the edge left-u -- right-v.

    Returns a list of k dicts, each a bijection `nodes -> nodes`.
    """
    mult = dict(mult)
    matchings = []
    for _ in range(k):
        adj = defaultdict(list)
        for (u, v), m in mult.items():
            if m > 0:
                adj[u].append(v)
        m = _hopcroft_karp(nodes, adj)
        if any(v is None for v in m.values()):
            raise AssertionError("no perfect matching in a regular multigraph")
        for u, v in m.items():
            mult[(u, v)] -= 1
        matchings.append(dict(m))
    if any(v != 0 for v in mult.values()):
        raise AssertionError("residual edges after k rounds")
    return matchings
