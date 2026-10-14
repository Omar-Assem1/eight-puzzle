from dataclasses import dataclass, field


@dataclass
class SearchResult:
    solved: bool = False
    path: list = field(default_factory=list)      # moves, e.g. ['Up', 'Left', ...]
    states: list = field(default_factory=list)    # boards from initial -> goal (inclusive)
    cost: int = 0                                 # number of moves in the path
    nodes_expanded: int = 0
    search_depth: int = 0                         # depth of the goal node found
    max_depth: int = 0                            # deepest node reached during search
    running_time: float = 0.0                     # seconds; filled in by main.run_algorithm


def reconstruct(parents, goal_state):

    moves, states = [], [goal_state]
    cur = goal_state
    while parents[cur][0] is not None:
        prev, move = parents[cur]
        moves.append(move)
        states.append(prev)
        cur = prev
    moves.reverse()
    states.reverse()
    return moves, states