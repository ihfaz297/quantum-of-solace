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
