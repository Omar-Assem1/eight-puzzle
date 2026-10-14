from puzzle.state import SIZE

LINE = "+" + "---+" * SIZE


def board_to_str(state, highlight=None):
    lines = [LINE]
    for r in range(SIZE):
        cells = []
        for c in range(SIZE):
            i = r * SIZE + c
            tile = state[i]
            if tile == 0:
                cells.append("   ")
            elif i == highlight:
                cells.append(f"({tile})")
            else:
                cells.append(f" {tile} ")
        lines.append("|" + "|".join(cells) + "|")
        lines.append(LINE)
    return "\n".join(lines)


def _moved_index(prev_state, move_state):
    return prev_state.index(0)


def path_summary(result):
    return " -> ".join(result.path) if result.path else "(already at goal)"


def print_solution(result, max_steps=None):

    if not result.solved:
        print("No solution found.")
        return

    total = len(result.path)
    print(f"Solution found: {total} moves")
    if total <= 40:
        print("Path:", path_summary(result))
    print()

    print("Step 0 (initial)")
    print(board_to_str(result.states[0]))

    steps = list(range(1, total + 1))
    skipped = False
    if max_steps is not None and total > max_steps:
        half = max_steps // 2
        steps = steps[:half] + steps[-half:]
        skipped = True

    prev_shown = 0
    for i in steps:
        if skipped and i - prev_shown > 1:
            print(f"\n   ... {i - prev_shown - 1} steps hidden ...")
        move = result.path[i - 1]
        prev, cur = result.states[i - 1], result.states[i]
        label = "(goal)" if i == total else ""
        print(f"\nStep {i}: blank moves {move} {label}".rstrip())
        print(board_to_str(cur, highlight=_moved_index(prev, cur)))
        prev_shown = i
    print()


def print_side_by_side(result, per_row=4):
    if not result.solved:
        print("No solution found.")
        return
    boards = result.states
    for start in range(0, len(boards), per_row):
        chunk = boards[start:start + per_row]
        blocks = [board_to_str(b).split("\n") for b in chunk]
        headers = [f"Step {start + k}".ljust(len(LINE) + 2) for k in range(len(chunk))]
        print("".join(headers))
        for row in range(len(blocks[0])):
            print("  ".join(block[row] for block in blocks))
        print()