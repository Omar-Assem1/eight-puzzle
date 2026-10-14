from puzzle.state import GOAL, get_neighbors, is_goal, is_solvable, parse_state, random_state


def test_goal():
    assert is_goal(GOAL)


def test_neighbors_corner_and_center():
    assert len(get_neighbors((0, 1, 2, 3, 4, 5, 6, 7, 8))) == 2   # blank in corner
    assert len(get_neighbors((1, 2, 3, 4, 0, 5, 6, 7, 8))) == 4   # blank in center


def test_assignment_example():
    start = parse_state("1,2,5,3,4,0,6,7,8")
    moves = dict(get_neighbors(start))
    assert moves["Up"] == (1, 2, 0, 3, 4, 5, 6, 7, 8)


def test_solvability():
    assert is_solvable(GOAL)
    assert not is_solvable((1, 0, 2, 3, 4, 5, 6, 8, 7))  # one swap -> odd parity
    assert is_solvable(random_state(1))