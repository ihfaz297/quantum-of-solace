"""Odd-even transposition sort: any permutation of an m-path in <= m rounds."""


def sort_rounds(path, key):
    """`path` is a list of vertices; `key[token]` is the token's target index.

    `state[i]` is the token currently on `path[i]`.  Returns a list of rounds,
    each a list of edges (as vertex pairs) swapped simultaneously.
    """
    state = list(range(len(path)))          # token i starts on path[i]
    rounds = []
    for step in range(len(path)):
        rnd = []
        for j in range(step % 2, len(path) - 1, 2):
            if key[state[j]] > key[state[j + 1]]:
                state[j], state[j + 1] = state[j + 1], state[j]
                rnd.append((path[j], path[j + 1]))
        if rnd:
            rounds.append(rnd)
    assert [key[t] for t in state] == sorted(key[t] for t in state)
    return rounds


def swap_endpoints(path):
    """Rounds transposing the two endpoints of `path` and fixing the interior."""
    m = len(path)
    if m < 2:
        return []
    key = list(range(m))
    key[0], key[m - 1] = m - 1, 0
    return sort_rounds(path, key)
