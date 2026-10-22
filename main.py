import argparse
import time

from puzzle.state import parse_state, random_state, is_solvable
from puzzle.bfs import bfs
from puzzle.dfs import dfs
from puzzle.ids import ids
from puzzle.astar import astar
from puzzle.visualize import print_solution

ALGORITHMS = {
    "bfs": bfs,
    "dfs": dfs,
    "ids": ids,
    "astar-manhattan": lambda s: astar(s, "manhattan"),
    "astar-euclidean": lambda s: astar(s, "euclidean"),
}


def run_algorithm(name, initial):
    start = time.perf_counter()
    try:
        result = ALGORITHMS[name](initial)
    except NotImplementedError:
        return None
    result.running_time = time.perf_counter() - start
    return result


def main():
    p = argparse.ArgumentParser(description="8-puzzle solver")
    p.add_argument("--state", help="initial state, e.g. 1,2,5,3,4,0,6,7,8")
    p.add_argument("--random", action="store_true", help="use a random solvable state")
    p.add_argument("--seed", type=int, default=None)
    p.add_argument("--algo", default="all", choices=["all"] + list(ALGORITHMS))
    p.add_argument("--no-trace", action="store_true", help="skip step-by-step boards")
    p.add_argument("--max-steps", type=int, default=None,
                   help="only show first/last N steps of long paths")
    p.add_argument("--gui", action="store_true", help="open the graphical interface")
    p.add_argument("--port", type=int, default=8080, help="GUI port (default 8080)")
    args = p.parse_args()

    if args.gui:
        from gui import serve
        serve(args.port)
        return

    if args.state:
        initial = parse_state(args.state)
    elif args.random:
        initial = random_state(args.seed)
    else:
        p.error("provide --state or --random (or --gui)")

    if not is_solvable(initial):
        print(f"State {initial} is NOT solvable (odd inversion count).")
        return

    print(f"Initial state: {initial}\n")
    names = list(ALGORITHMS) if args.algo == "all" else [args.algo]
    rows = []
    for name in names:
        res = run_algorithm(name, initial)
        if res is None:
            print(f"[{name}] not implemented yet\n")
            continue
        print(f"===== {name} =====")
        if not args.no_trace:
            print_solution(res, max_steps=args.max_steps)
        rows.append((name, res))

    if rows:
        header = f"{'algorithm':<18}{'cost':>6}{'expanded':>10}{'depth':>7}{'max_depth':>11}{'time(s)':>10}"
        print(header)
        print("-" * len(header))
        for name, r in rows:
            print(f"{name:<18}{r.cost:>6}{r.nodes_expanded:>10}{r.search_depth:>7}{r.max_depth:>11}{r.running_time:>10.4f}")


if __name__ == "__main__":
    main()
