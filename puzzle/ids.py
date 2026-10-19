from puzzle.result import SearchResult, reconstruct
from puzzle.state import get_neighbors, is_goal


def depth_limited_search(initial, limit, counters):
    parents = {initial: (None, None)}
    stack = [(initial, 0, None)]

    while stack:
        state, depth, children = stack.pop()

        if children is None:
            if depth > counters["max_depth"]:
                counters["max_depth"] = depth

            if is_goal(state):
                return state, parents

            if depth == limit:
                del parents[state]
                continue

            counters["expanded"] += 1
            children = iter(get_neighbors(state))

        advanced = False
        for move, child in children:
            if child in parents:
                continue

            parents[child] = (state, move)
            stack.append((state, depth, children))
            stack.append((child, depth + 1, None))
            advanced = True
            break

        if not advanced:
            del parents[state]

    return None, None


def ids(initial, max_limit=31):
    counters = {"expanded": 0, "max_depth": 0}

    for limit in range(max_limit + 1):
        goal, parents = depth_limited_search(initial, limit, counters)

        if goal is not None:
            moves, states = reconstruct(parents, goal)
            return SearchResult(
                solved=True,
                path=moves,
                states=states,
                cost=len(moves),
                nodes_expanded=counters["expanded"],
                search_depth=len(moves),
                max_depth=counters["max_depth"],
            )

    return SearchResult(
        solved=False,
        nodes_expanded=counters["expanded"],
        max_depth=counters["max_depth"],
    )