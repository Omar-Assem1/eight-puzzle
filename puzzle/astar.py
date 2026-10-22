import heapq
import math
from itertools import count

from puzzle.result import SearchResult, reconstruct
from puzzle.state import GOAL, SIZE, get_neighbors, is_goal


GOAL_POS = {tile: divmod(index, SIZE) for index, tile in enumerate(GOAL)}


def manhattan(state):
    total = 0
    for index, tile in enumerate(state):
        if tile == 0:
            continue
        r, c = divmod(index, SIZE)
        gr, gc = GOAL_POS[tile]
        total += abs(r - gr) + abs(c - gc)
    return total


def euclidean(state):
    total = 0.0
    for index, tile in enumerate(state):
        if tile == 0:
            continue
        r, c = divmod(index, SIZE)
        gr, gc = GOAL_POS[tile]
        total += math.sqrt((r - gr) ** 2 + (c - gc) ** 2)
    return total


HEURISTICS = {"manhattan": manhattan, "euclidean": euclidean}


def astar(initial, heuristic="manhattan"):
    if heuristic not in HEURISTICS:
        raise ValueError(
            f"unknown heuristic {heuristic!r}; use one of {list(HEURISTICS)}"
        )

    h = HEURISTICS[heuristic]

    tie = count()
    frontier = [(h(initial), next(tie), 0, initial)]
    best_g = {initial: 0}
    parents = {initial: (None, None)}
    closed = set()

    nodes_expanded = 0
    max_depth = 0

    while frontier:
        f, _, g, state = heapq.heappop(frontier)

        if state in closed:
            continue
        closed.add(state)

        if is_goal(state):
            moves, states = reconstruct(parents, state)
            return SearchResult(
                solved=True,
                path=moves,
                states=states,
                cost=len(moves),
                nodes_expanded=nodes_expanded,
                search_depth=g,
                max_depth=max_depth,
            )

        nodes_expanded += 1

        for move, child in get_neighbors(state):
            if child in closed:
                continue

            new_g = g + 1

            if new_g < best_g.get(child, float("inf")):
                best_g[child] = new_g
                parents[child] = (state, move)
                max_depth = max(max_depth, new_g)
                heapq.heappush(
                    frontier,
                    (new_g + h(child), next(tie), new_g, child),
                )

    return SearchResult(
        solved=False,
        nodes_expanded=nodes_expanded,
        max_depth=max_depth,
    )