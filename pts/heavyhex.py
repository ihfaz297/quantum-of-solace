"""The brick-wall heavy-hex graph X = S(H) and the cell quotient of Lemma 1.

Vertices of X:
    ('b', x, y)            branch vertex, a vertex of H
    ('s', (p, q))          the subdivision vertex of the H-edge {p, q}, p < q

The cell map is uniform: every vertex is indexed by the lexicographically
smaller H-endpoint it is attached to, and phi(x, y) = (x // 2, y).
"""

from collections import deque


def h_edges(W, Ht):
    """Edges of the brick wall H on the rectangle [0, W] x [0, Ht].

    All horizontal edges; vertical edges (x, y)-(x, y+1) only when x + y is even.
    """
    out = []
    for y in range(Ht + 1):
        for x in range(W):
            out.append(((x, y), (x + 1, y)))
    for y in range(Ht):
        for x in range(W + 1):
            if (x + y) % 2 == 0:
                out.append(((x, y), (x, y + 1)))
    return out


class HeavyHex:
    """X = S(H) for H the brick wall on [0, W] x [0, Ht], with W odd."""

    def __init__(self, W, Ht):
        if W % 2 == 0:
            raise ValueError("W must be odd so that branch columns pair up")
        self.W, self.Ht = W, Ht

        self.branch = [("b", x, y) for y in range(Ht + 1) for x in range(W + 1)]
        self.hedges = h_edges(W, Ht)
        self.sub = [("s", e) for e in self.hedges]
        self.vertices = self.branch + self.sub
        self.index = {v: i for i, v in enumerate(self.vertices)}

        self.adj = {v: [] for v in self.vertices}
        for e in self.hedges:
            s = ("s", e)
            for p in e:
                b = ("b", p[0], p[1])
                self.adj[b].append(s)
                self.adj[s].append(b)

        # Grid Gamma and the cell map phi.
        self.A = (W - 1) // 2          # cells are indexed 0..A horizontally
        self.B = Ht                    # and 0..B vertically
        self.grid = [(a, b) for b in range(self.B + 1) for a in range(self.A + 1)]
        self.phi = {v: self._cell(v) for v in self.vertices}
        self.fiber = {p: [] for p in self.grid}
        for v in self.vertices:
            self.fiber[self.phi[v]].append(v)

    @staticmethod
    def _cell(v):
        if v[0] == "b":
            x, y = v[1], v[2]
        else:
            (x, y) = min(v[1])          # lower / left endpoint of the H-edge
        return (x // 2, y)

    # --- graph utilities -------------------------------------------------

    def bfs(self, src, adj=None):
        adj = adj if adj is not None else self.adj
        dist = {src: 0}
        dq = deque([src])
        while dq:
            u = dq.popleft()
            for w in adj[u]:
                if w not in dist:
                    dist[w] = dist[u] + 1
                    dq.append(w)
        return dist

    def all_distances(self):
        return {v: self.bfs(v) for v in self.vertices}

    def shortest_path(self, u, v):
        prev = {u: None}
        dq = deque([u])
        while dq:
            a = dq.popleft()
            if a == v:
                break
            for w in self.adj[a]:
                if w not in prev:
                    prev[w] = a
                    dq.append(w)
        if v not in prev:
            raise ValueError(f"no path {u} -> {v}")
        path = []
        cur = v
        while cur is not None:
            path.append(cur)
            cur = prev[cur]
        return path[::-1]

    def grid_adj(self):
        adj = {p: [] for p in self.grid}
        for (a, b) in self.grid:
            for (da, db) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                q = (a + da, b + db)
                if q in adj:
                    adj[(a, b)].append(q)
        return adj

    def grid_distances(self):
        # Gamma is a full rectangle, so the L1 distance is the graph distance,
        # but compute it by BFS anyway so the check is independent of that fact.
        gadj = self.grid_adj()
        return {p: self.bfs(p, gadj) for p in self.grid}

    def quotient_edges(self):
        """Images in Gamma of the edges of X, excluding loops."""
        out = set()
        for u in self.vertices:
            for v in self.adj[u]:
                p, q = self.phi[u], self.phi[v]
                if p != q:
                    out.add(tuple(sorted((p, q))))
        return out

    def induced_adj(self, subset):
        S = set(subset)
        return {v: [w for w in self.adj[v] if w in S] for v in S}

    def __repr__(self):
        return (f"HeavyHex(W={self.W}, Ht={self.Ht}) "
                f"|V(X)|={len(self.vertices)} |V(Gamma)|={len(self.grid)}")
