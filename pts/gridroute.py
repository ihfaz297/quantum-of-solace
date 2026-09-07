"""Column-row-column routing of an arbitrary permutation on a rectangular mesh.

Classical three-phase scheme: a Koenig decomposition of the column-to-column
demand fixes which token of each source column travels in which row; then rows
carry tokens to their target columns and columns to their target rows.  Each
phase is odd-even transposition sort on disjoint paths, so the whole schedule
uses at most 2(B+1) + (A+1) rounds -- linear in the mesh diameter.
"""

from collections import defaultdict

from .koenig import decompose
from .pathsort import sort_rounds


def route(A, B, sigma):
    """Mesh on {0..A} x {0..B}; `sigma` maps (a, b) -> (a', b').

    Returns a list of rounds, each a list of mesh edges swapped simultaneously.
    """
    cols, rows = list(range(A + 1)), list(range(B + 1))
    cells = [(a, b) for a in cols for b in rows]
    dest = dict(sigma)

    # --- phase 1: pick, for each source column, which token rides in which row
    mult = defaultdict(int)
    bucket = defaultdict(list)
    for c in cells:
        a, a2 = c[0], dest[c][0]
        mult[(a, a2)] += 1
        bucket[(a, a2)].append(c)
    lanes = decompose(cols, mult, B + 1)          # lanes[k][a] = target column

    pool = {e: list(v) for e, v in bucket.items()}
    ride = {}                                     # cell -> row it rides in
    for k, lane in enumerate(lanes):
        for a, a2 in lane.items():
            ride[pool[(a, a2)].pop()] = k

    rounds = []

    def run_phase(paths, keyfns):
        """`paths` are vertex-disjoint; realise all of them in parallel."""
        per_path = []
        for path, keyfn in zip(paths, keyfns):
            key = [keyfn(occupant[v]) for v in path]
            per_path.append(sort_rounds(path, key))
            # re-place the occupants according to the realised permutation
            order = sorted(range(len(path)), key=lambda i: key[i])
            newocc = [occupant[path[i]] for i in order]
            for v, t in zip(path, newocc):
                occupant[v] = t
        for i in range(max((len(p) for p in per_path), default=0)):
            rnd = [e for p in per_path if i < len(p) for e in p[i]]
            if rnd:
                rounds.append(rnd)

    occupant = {c: c for c in cells}              # token identity = its origin

    col_paths = [[(a, b) for b in rows] for a in cols]
    run_phase(col_paths, [lambda t: ride[t]] * len(col_paths))

    row_paths = [[(a, b) for a in cols] for b in rows]
    run_phase(row_paths, [lambda t: dest[t][0]] * len(row_paths))

    run_phase(col_paths, [lambda t: dest[t][1]] * len(col_paths))

    assert all(occupant[dest[c]] == c for c in cells), "mesh routing failed"
    return rounds
