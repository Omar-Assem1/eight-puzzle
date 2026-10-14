import random

GOAL = (0, 1, 2, 3, 4, 5, 6, 7, 8)
SIZE = 3

# Direction the BLANK moves, as (row delta, col delta). Fixed order = deterministic runs.
MOVES = {
    "Up": (-1, 0),
    "Down": (1, 0),
    "Left": (0, -1),
    "Right": (0, 1),
}


def parse_state(text):
    """'1,2,5,3,4,0,6,7,8' -> tuple. Validates it is a permutation of 0..8."""
    state = tuple(int(x) for x in text.replace(" ", "").split(",") if x != "")
    if sorted(state) != list(range(SIZE * SIZE)):
        raise ValueError("State must contain each of 0..8 exactly once.")
    return state


def is_goal(state):
    return state == GOAL


def get_neighbors(state):
    blank = state.index(0)
    row, col = divmod(blank, SIZE)
    result = []
    for name, (dr, dc) in MOVES.items():
        r, c = row + dr, col + dc
        if 0 <= r < SIZE and 0 <= c < SIZE:
            target = r * SIZE + c
            board = list(state)
            board[blank], board[target] = board[target], board[blank]
            result.append((name, tuple(board)))
    return result


def is_solvable(state):
    tiles = [t for t in state if t != 0]
    inversions = sum(
        1 for i in range(len(tiles)) for j in range(i + 1, len(tiles)) if tiles[i] > tiles[j]
    )
    return inversions % 2 == 0


def random_state(seed=None):
    rng = random.Random(seed)
    while True:
        tiles = list(range(SIZE * SIZE))
        rng.shuffle(tiles)
        state = tuple(tiles)
        if is_solvable(state):
            return state