"""Tests for all five search runs.  Run with:  python -m pytest -q"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import math

import pytest

from puzzle.astar import astar, euclidean, manhattan
from puzzle.bfs import bfs
from puzzle.dfs import dfs
from puzzle.ids import ids
from puzzle.state import GOAL, get_neighbors, is_solvable, parse_state, random_state

START = (1, 2, 5, 3, 4, 0, 6, 7, 8)       # the sample state from the lab sheet


def _valid_path(r):
    """Every consecutive pair of boards must differ by one legal blank move."""
    for (a, b), move in zip(zip(r.states, r.states[1:]), r.path):
        if (move, b) not in get_neighbors(a):
            return False
    return len(r.states) == len(r.path) + 1


# ---------------------------------------------------------------- shared ----
def test_bfs_sample():
    r = bfs(START)
    assert r.solved and r.cost == 3 and r.nodes_expanded == 10 and _valid_path(r)


def test_dfs_solves():
    r = dfs(START)
    assert r.solved and r.states[-1] == GOAL and _valid_path(r)


def test_already_goal():
    for algo in (bfs, dfs, ids, lambda s: astar(s, "manhattan"), lambda s: astar(s, "euclidean")):
        r = algo(GOAL)
        assert r.solved and r.cost == 0 and r.path == [] and r.nodes_expanded == 0


# ------------------------------------------------------------------- IDS ----
def test_ids_optimal():
    r = ids(START)
    assert r.solved and r.cost == 3 and r.states[-1] == GOAL and _valid_path(r)


def test_ids_nodes_summed_over_iterations():
    # limit 0: root is not goal, depth==limit => 0 expansions.  Sum must exceed a
    # single DFS run, and be at least the number of expansions of the last pass.
    r = ids(START)
    assert r.nodes_expanded == 8 and r.search_depth == 3


def test_ids_unsolvable_returns_false():
    bad = (1, 0, 2, 3, 4, 5, 6, 8, 7)      # odd permutation => unsolvable
    assert not is_solvable(bad)
    assert not ids(bad, max_limit=6).solved


# ------------------------------------------------------------------- A* -----
def test_astar_both_heuristics_optimal():
    for h in ("manhattan", "euclidean"):
        r = astar(START, h)
        assert r.solved and r.cost == 3 and r.states[-1] == GOAL and _valid_path(r)


def test_astar_rejects_unknown_heuristic():
    with pytest.raises(ValueError):
        astar(START, "hamming")


def test_heuristic_values():
    assert manhattan(GOAL) == 0 and euclidean(GOAL) == 0
    assert manhattan(START) == 3                       # 3 tiles each 1 away
    assert math.isclose(euclidean(START), 3.0)
    # Only tile 1 is displaced (1 step).  If the blank were wrongly counted it
    # would add another 1 and the value would be 2.
    assert manhattan((1, 0, 2, 3, 4, 5, 6, 7, 8)) == 1


def test_euclidean_never_exceeds_manhattan():
    for seed in range(50):
        s = random_state(seed)
        assert euclidean(s) <= manhattan(s) + 1e-9


def test_heuristics_admissible_against_bfs():
    # h(start) must never exceed the true optimal cost found by BFS.
    for seed in range(10):
        s = random_state(seed)
        true_cost = bfs(s).cost
        assert manhattan(s) <= true_cost
        assert euclidean(s) <= true_cost + 1e-9


@pytest.mark.parametrize("seed", range(10))
def test_all_optimal_algorithms_agree_with_bfs(seed):
    s = random_state(seed)
    # keep IDS tests quick: skip the (rare) very deep boards for IDS only
    best = bfs(s)
    for h in ("manhattan", "euclidean"):
        r = astar(s, h)
        assert r.solved and r.cost == best.cost and _valid_path(r)
        assert r.states[-1] == GOAL
    if best.cost <= 20:
        r = ids(s)
        assert r.solved and r.cost == best.cost and _valid_path(r)


def test_manhattan_expands_no_more_than_euclidean_on_average():
    man = eu = 0
    for seed in range(10):
        s = random_state(seed)
        man += astar(s, "manhattan").nodes_expanded
        eu += astar(s, "euclidean").nodes_expanded
    assert man <= eu


def test_astar_fewer_nodes_than_bfs():
    s = random_state(7)
    assert astar(s, "manhattan").nodes_expanded < bfs(s).nodes_expanded


def test_parse_state_validation():
    assert parse_state("1,2,5,3,4,0,6,7,8") == START
    with pytest.raises(ValueError):
        parse_state("1,1,2,3,4,5,6,7,8")
