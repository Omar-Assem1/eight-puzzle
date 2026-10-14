from puzzle.bfs import bfs
from puzzle.dfs import dfs
from puzzle.state import GOAL, parse_state, get_neighbors

START = parse_state("1,2,5,3,4,0,6,7,8")  # optimal cost = 3


def _valid_path(r):
    return all((m, b) in get_neighbors(a)
               for (a, b), m in zip(zip(r.states, r.states[1:]), r.path))


def test_bfs_optimal():
    r = bfs(START)
    assert r.solved and r.cost == 3 and r.states[-1] == GOAL and _valid_path(r)


def test_dfs_reaches_goal():
    r = dfs(START)
    assert r.solved and r.states[-1] == GOAL and _valid_path(r)
    assert r.cost >= 3  # DFS is not optimal