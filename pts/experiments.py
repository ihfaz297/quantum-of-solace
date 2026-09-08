"""Small-instance experiments: the section 5 table, and the winding question."""

from .exact import all_matchings, solve, solve_relaxed
from .heavyhex import HeavyHex


def cycle_with_chords(m, chords):
    edges = [(i, (i + 1) % m) for i in range(m)]
    edges += [tuple(sorted(c)) for c in chords]
    return m, sorted(set(edges))


def rotate_target(m, n=None):
    """Token on i must reach i+1 (mod m); vertices >= m are fixed."""
    n = n or m
    tgt = list(range(n))
    for i in range(m):
        tgt[(i + 1) % m] = i
    return tgt


def grid_graph(R, C):
    verts = [(r, c) for r in range(R) for c in range(C)]
    idx = {v: i for i, v in enumerate(verts)}
    edges = []
    for (r, c) in verts:
        for (dr, dc) in ((1, 0), (0, 1)):
            w = (r + dr, c + dc)
            if w in idx:
                edges.append(tuple(sorted((idx[(r, c)], idx[w]))))
    return verts, idx, sorted(set(edges))


def grid_boundary_cycle(R, C):
    """Boundary vertices of an R x C grid in cyclic order."""
    top = [(0, c) for c in range(C)]
    right = [(r, C - 1) for r in range(1, R)]
    bottom = [(R - 1, c) for c in range(C - 2, -1, -1)]
    left = [(r, 0) for r in range(R - 2, 0, -1)]
    return top + right + bottom + left


def section5_table():
    rows = []

    for (R, C) in ((2, 5), (3, 3)):
        verts, idx, edges = grid_graph(R, C)
        ring = [idx[v] for v in grid_boundary_cycle(R, C)]
        tgt = list(range(len(verts)))
        for k in range(len(ring)):
            tgt[ring[(k + 1) % len(ring)]] = ring[k]
        opt, _ = solve(len(verts), edges, tgt)
        rows.append((f"rotate boundary of {R}x{C} grid", 1, opt, len(ring)))

    n, edges = cycle_with_chords(10, [(0, 5)])
    opt, _ = solve(n, edges, rotate_target(10))
    rows.append(("rotate boundary of two fused hexagons", 1, opt, 10))
    return rows


def bare_cycle_baseline():
    out = []
    for m in (6, 8, 10, 12):
        n, edges = cycle_with_chords(m, [])
        opt, _ = solve(n, edges, rotate_target(m))
        out.append((m, opt))
    return out


def cycle_with_pendants(m):
    """C_m with a pendant vertex hung off every other cycle vertex."""
    edges = [(i, (i + 1) % m) for i in range(m)]
    n = m
    for i in range(0, m, 2):
        edges.append((i, n))
        n += 1
    return n, sorted(edges)


def cycle_with_legs_and_hub(m):
    """C_m with a leg off every other vertex, all legs joined to one hub.

    Unlike a dead-end pendant this is a genuine escape route: a token can leave
    the cycle at one branch vertex and re-enter at another.
    """
    edges = [(i, (i + 1) % m) for i in range(m)]
    n, legs = m, []
    for i in range(0, m, 2):
        edges.append((i, n))
        legs.append(n)
        n += 1
    hub = n
    n += 1
    for l in legs:
        edges.append((l, hub))
    return n, sorted(edges)


def winding_probe(sizes=(4, 6)):
    """Rotate C_m by one, with and without access to the outside.

    A heavy-hex face is a cycle whose branch vertices carry legs pointing
    *outward*; it has no chord.  These instances separate the two effects.
    """
    out = []
    for m in sizes:
        bare, _ = solve(m, [(i, (i + 1) % m) for i in range(m)],
                        rotate_target(m))
        n1, e1 = cycle_with_pendants(m)
        pend, _ = solve(n1, e1, rotate_target(m, n1))
        n2, e2 = cycle_with_legs_and_hub(m)
        hub, _ = solve(n2, e2, rotate_target(m, n2))
        n3, e3 = cycle_with_chords(m, [(0, m // 2)])
        chord, _ = solve(n3, e3, rotate_target(m))
        out.append({"m": m, "bare": bare, "dead_end_legs": pend,
                    "legs_to_hub": hub, "one_chord": chord,
                    "girth_with_chord": min(m // 2 + 1, m)})
    return out


def heavyhex_face_lower_bound(W=3, Ht=1, track=6, cap=12):
    """Rotate one hexagonal face of X by one; relax all but `track` tokens."""
    g = HeavyHex(W, Ht)
    idx = g.index
    n = len(g.vertices)
    edges = sorted({tuple(sorted((idx[u], idx[v])))
                    for u in g.vertices for v in g.adj[u]})

    corners = [(0, 0), (1, 0), (2, 0), (2, 1), (1, 1), (0, 1)]
    ring = []
    for k, p in enumerate(corners):
        q = corners[(k + 1) % len(corners)]
        ring.append(idx[("b", p[0], p[1])])
        ring.append(idx[("s", tuple(sorted((p, q))))])

    tgt = list(range(n))
    for k in range(len(ring)):
        tgt[ring[(k + 1) % len(ring)]] = ring[k]

    deg2 = [v for v in ring if len(g.adj[g.vertices[v]]) == 2]
    labeled = set(deg2[:track])
    lb = solve_relaxed(n, edges, labeled, tgt, cap=cap)
    return {"n": n, "ring": len(ring), "tracked": sorted(labeled),
            "relaxed_lower_bound": lb, "cap": cap}


def patch_size_audit(shapes=((3, 1), (5, 2), (7, 3), (9, 4), (11, 5), (13, 6),
                             (3, 2), (11, 3))):
    """Brick rectangle vs the proposal's staggered-patch formula.

    The proposal states n = 5ij + 4(i+j) - 1 for an i x j patch of hexagons.
    The brick rectangle [0, 2i+1] x [0, j] carries exactly i*j hexagons, and its
    heavy-hex graph has exactly FOUR more vertices than that formula gives --
    a constant offset, not a growing one.  This is the precise content of the
    "stated for one boundary shape" caveat in section 7 of the proof note.
    """
    rows = []
    for (W, Ht) in shapes:
        g = HeavyHex(W, Ht)
        V, E = len(g.branch), len(g.hedges)
        faces = 2 - V + E - 1                  # Euler, minus the outer face
        i, j = (W - 1) // 2, Ht
        formula = 5 * i * j + 4 * (i + j) - 1
        rows.append({"W": W, "Ht": Ht, "i": i, "j": j, "hexagons": faces,
                     "n_brick": len(g.vertices), "n_formula": formula,
                     "offset": len(g.vertices) - formula})
    return rows


def device_size_check(targets=(27, 65, 127, 133, 156, 433, 1121), lim=40):
    """Which IBM device sizes the formula n = 5ij + 4(i+j) - 1 can produce."""
    out = {}
    for t in targets:
        out[t] = [(i, j) for i in range(1, lim) for j in range(1, lim)
                  if 5 * i * j + 4 * (i + j) - 1 == t]
    return out


# ---------------------------------------------------------------------------
# Girth, girth-preserving escapes, and the corrected winding probe.
#
# An earlier version of this file claimed "legs never help, only chords do".
# That is false: C_8 with legs joined to a hub rotates in 6 rounds, not 7,
# because the hub creates a 6-cycle and girth drops.  The law that survives --
# and that pts/winding.py proves -- is  OPT(rotate a cycle by one) >= girth - 1.
# ---------------------------------------------------------------------------

def girth(n, edges):
    """Length of the shortest cycle; inf if the graph is a forest."""
    from collections import deque
    adj = {i: [] for i in range(n)}
    for a, b in edges:
        adj[a].append(b)
        adj[b].append(a)
    best = float("inf")
    for s in range(n):
        dist, parent = {s: 0}, {s: None}
        dq = deque([s])
        while dq:
            v = dq.popleft()
            for u in adj[v]:
                if u not in dist:
                    dist[u] = dist[v] + 1
                    parent[u] = v
                    dq.append(u)
                elif parent[v] != u:
                    best = min(best, dist[v] + dist[u] + 1)
    return best


def cycle_with_escape_path(m, a, b, length):
    """C_m plus one internally-disjoint path of `length` edges joining cycle
    vertices a and b.  Girth is preserved iff length + d_cycle(a, b) >= m."""
    edges = [(i, (i + 1) % m) for i in range(m)]
    n, prev = m, a
    for _ in range(length - 1):
        edges.append((prev, n))
        prev = n
        n += 1
    edges.append((prev, b))
    return n, sorted(edges)


def winding_probe(sizes=(4, 6, 8)):
    """Rotate C_m by one inside five host graphs; report OPT against girth.

    The predicate that matters is OPT >= girth - 1 (proved in pts/winding.py),
    NOT OPT == m - 1.  The legs-to-hub row at m = 8 is the instance that
    refuted the earlier "legs never help" claim: girth drops to 6, OPT to 6.
    """
    out = []
    for m in sizes:
        base = [(i, (i + 1) % m) for i in range(m)]
        inst = {
            "bare": (m, base),
            "dead_end_legs": cycle_with_pendants(m),
            "legs_to_hub": cycle_with_legs_and_hub(m),
            "girth_preserving_escape": cycle_with_escape_path(m, 0, m // 2, m // 2),
            "one_chord": cycle_with_chords(m, [(0, m // 2)]),
        }
        row = {"m": m}
        for name, (n, e) in inst.items():
            opt, _ = solve(n, e, rotate_target(m, n))
            row[name] = {"n": n, "girth": girth(n, e), "opt": opt}
        out.append(row)
    return out


def two_core_size(g):
    """Vertices surviving repeated deletion of degree < 2 vertices."""
    adj = {v: set(ws) for v, ws in g.adj.items()}
    alive, changed = set(adj), True
    while changed:
        changed = False
        for v in list(alive):
            if len(adj[v] & alive) < 2:
                alive.discard(v)
                changed = True
    return len(alive)


def two_core_audit(shapes=((3, 1), (5, 2), (7, 3), (11, 5), (11, 3), (3, 10))):
    """The proposal's n = 5ij + 4(i+j) - 1 counts the 2-core of the brick
    rectangle exactly; the full rectangle carries 4 more vertices (two
    dangling flags).  Real IBM devices are this 2-core plus pendant qubits."""
    rows = []
    for (W, Ht) in shapes:
        g = HeavyHex(W, Ht)
        i, j = (W - 1) // 2, Ht
        rows.append({"W": W, "Ht": Ht, "n": len(g.vertices),
                     "two_core": two_core_size(g),
                     "formula": 5 * i * j + 4 * (i + j) - 1})
    return rows


# ---------------------------------------------------------------------------
# Two checks the refined proposal relies on and that the audits asked for.
# ---------------------------------------------------------------------------

def involution_obstruction(ks=(6, 8, 10, 12)):
    """Yuan-Zhang's Lemma 1 splits any permutation as pi = tau1 . tau2 with
    tau1, tau2 involutions.  For the rotation of C_k (LB = 1), the best split
    has max(LB(tau1), LB(tau2)) = floor(k/2): the split inflates the geodesic
    lower bound, so their reduction cannot be made instance-wise as written.
    Returns {k: (min over splits of max LB, floor(k/2))}."""
    def cyc(a, b, k):
        d = abs(a - b) % k
        return min(d, k - d)

    def involutions(k):
        out = []

        def rec(i, cur, used):
            if i == k:
                out.append(dict(cur))
                return
            if i in used:
                rec(i + 1, cur, used)
                return
            cur[i] = i
            used.add(i)
            rec(i + 1, cur, used)
            used.discard(i)
            del cur[i]
            for j in range(i + 1, k):
                if j not in used:
                    cur[i], cur[j] = j, i
                    used |= {i, j}
                    rec(i + 1, cur, used)
                    used -= {i, j}
                    del cur[i], cur[j]
        rec(0, {}, set())
        return out

    out = {}
    for k in ks:
        pi = {i: (i + 1) % k for i in range(k)}
        best = None
        for t2 in involutions(k):
            t1 = {i: pi[t2[i]] for i in range(k)}        # pi = t1 . t2
            if any(t1[t1[i]] != i for i in range(k)):
                continue
            m = max(max(cyc(i, t1[i], k) for i in range(k)),
                    max(cyc(i, t2[i], k) for i in range(k)))
            best = m if best is None else min(best, m)
        out[k] = (best, k // 2)
    return out


def grid_guarantee_gap(A=11, B=9, trials=200, seed=3):
    """On the (A+1) x (B+1) mesh -- 12 x 10 is the shape of IBM Nighthawk's
    coupling map -- compare the classical mesh router's rounds with BGS's
    guarantee 2*d_max + 2h, h the short side.  Returns
    (max rounds, min guarantee, h)."""
    import random
    from .gridroute import route
    rng = random.Random(seed)
    cells = [(a, b) for a in range(A + 1) for b in range(B + 1)]
    h = min(A + 1, B + 1)
    worst_rounds, best_guarantee = 0, None
    for _ in range(trials):
        tgt = cells[:]
        rng.shuffle(tgt)
        sigma = dict(zip(cells, tgt))
        lb = max(abs(p[0] - q[0]) + abs(p[1] - q[1]) for p, q in sigma.items())
        r = len(route(A, B, sigma))
        worst_rounds = max(worst_rounds, r)
        gval = 2 * lb + 2 * h
        best_guarantee = gval if best_guarantee is None else min(best_guarantee, gval)
    return worst_rounds, best_guarantee, h
