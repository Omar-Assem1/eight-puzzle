from collections import deque

from puzzle.result import SearchResult, reconstruct
from puzzle.state import get_neighbors, is_goal


def bfs(initial):
    frontier = deque([initial])
    visited = {initial}
    parents = {initial: (None, None)}
    depth = {initial: 0}

    nodes_expanded = 0
    max_depth = 0

    while frontier:
        state = frontier.popleft()

        # Goal test when the node is taken from the frontier.
        if is_goal(state):
            moves, states = reconstruct(parents, state)
            return SearchResult(
                solved=True,
                path=moves,
                states=states,
                cost=len(moves),
                nodes_expanded=nodes_expanded,
                search_depth=depth[state],
                max_depth=max_depth,
            )

        # Expand: generate all children of this node.
        nodes_expanded += 1
        for move, child in get_neighbors(state):
            if child not in visited:
                visited.add(child)
                parents[child] = (state, move)
                depth[child] = depth[state] + 1
                max_depth = max(max_depth, depth[child])
                frontier.append(child)

    return SearchResult(solved=False, nodes_expanded=nodes_expanded, max_depth=max_depth)