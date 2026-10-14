from puzzle.result import SearchResult, reconstruct
from puzzle.state import get_neighbors, is_goal


def dfs(initial):
    stack = [(initial, None, None, 0)]
    visited = set()
    parents = {}

    nodes_expanded = 0
    max_depth = 0

    while stack:
        state, parent, move, depth = stack.pop()

        if state in visited:
            continue
        visited.add(state)
        parents[state] = (parent, move)
        max_depth = max(max_depth, depth)

        if is_goal(state):
            moves, states = reconstruct(parents, state)
            return SearchResult(
                solved=True,
                path=moves,
                states=states,
                cost=len(moves),
                nodes_expanded=nodes_expanded,
                search_depth=depth,
                max_depth=max_depth,
            )

        nodes_expanded += 1
        for child_move, child in reversed(get_neighbors(state)):
            if child not in visited:
                stack.append((child, state, child_move, depth + 1))

    return SearchResult(solved=False, nodes_expanded=nodes_expanded, max_depth=max_depth)