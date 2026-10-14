# Member 2: Requirements (IDS + A*)

Project: 8-Puzzle with informed and uninformed search (AI Course, Assignment 1).
**Deadline: 23/10/2026.**

Member 1 has already pushed the shared code, BFS, DFS, the visualization, `main.py` and the tests.
Your job is **Iterative Deepening DFS** and **A\*** (with two heuristics), plus your part of the report.

---

## 1. Setup

```bash
git clone https://github.com/Omar-Assem1/eight-puzzle.git
cd eight-puzzle
git checkout -b ids-astar
pip install pytest
python main.py --state 1,2,5,3,4,0,6,7,8 --algo bfs     # check everything runs
```

## 2. Files you own

| File | What to do |
|---|---|
| `puzzle/ids.py` | Implement `ids(initial, max_limit=31)` |
| `puzzle/astar.py` | Implement `manhattan`, `euclidean`, and `astar(initial, heuristic)` |
| `tests/test_algorithms.py` | Add tests for IDS and A* (at the bottom of the file) |
| `main.py` | **Only** uncomment your imports and registry lines (see section 6) |
| `report/` | Your report sections (see section 7) |

**Do not edit** `state.py`, `result.py`, `bfs.py`, `dfs.py` or `visualize.py`. If you need a change there, ask Member 1.

## 3. The interface you must follow

Use the shared helpers from `puzzle/state.py` and `puzzle/result.py`:

```python
from puzzle.state import get_neighbors, is_goal, GOAL
from puzzle.result import SearchResult, reconstruct
```

- A state is a **tuple of 9 ints**, 0 is the blank: `(1, 2, 5, 3, 4, 0, 6, 7, 8)`.
- `get_neighbors(state)` returns a list of `(move_name, new_state)`.
- Every algorithm takes `initial` and **returns a `SearchResult`**:

| Field | Meaning |
|---|---|
| `solved` | `True` if the goal was reached |
| `path` | list of moves, e.g. `['Up', 'Left', 'Left']` |
| `states` | boards from the initial state to the goal (inclusive) |
| `cost` | number of moves (`len(path)`) |
| `nodes_expanded` | see the rule below |
| `search_depth` | depth of the goal node |
| `max_depth` | deepest node reached during the search |
| `running_time` | **do not set it**, `main.py` fills it in |

- `reconstruct(parents, goal_state)` rebuilds the path from a parent map `{state: (parent_state, move)}`. The root must be stored as `parents[initial] = (None, None)`.

**Counting rule (must be the same for all algorithms):** `nodes_expanded` goes up by 1 each time you take a node out of the frontier, it is not the goal, and you generate its children. The goal test is done when a node is popped.

## 4. Task A: Iterative Deepening DFS (`puzzle/ids.py`)

Run a depth-limited DFS with limit = 0, 1, 2, 3, ... until the goal is found.

Requirements:
- Signature: `ids(initial, max_limit=31)`. 31 is the maximum optimal depth of any solvable 8-puzzle state.
- Depth-limited DFS uses a stack (or recursion). Do not go deeper than the current limit.
- Avoid cycles by checking the **current path only**. Do not use one global visited set across iterations, because it makes IDS miss solutions.
- `nodes_expanded` is the **sum over all iterations**.
- `search_depth` is the depth where the goal was found. This is the optimal cost, because IDS is optimal for unit costs.
- `max_depth` is the deepest level reached.
- Return `solved=False` if no solution is found within `max_limit`.

Expected: cost **3** on `1,2,5,3,4,0,6,7,8`, and cost **28** on `--random --seed 7`.

## 5. Task B: A* (`puzzle/astar.py`)

### Heuristics
Sum over **all tiles except the blank (0)**, comparing each tile's current cell to its goal cell (row, col):

- **Manhattan:** `abs(r - gr) + abs(c - gc)`
- **Euclidean:** `sqrt((r - gr)**2 + (c - gc)**2)`

(The skeleton may already contain these. If the file is empty, write them.)

### Search
- `astar(initial, heuristic="manhattan")` where `heuristic` is `"manhattan"` or `"euclidean"`.
- Priority queue: `heapq`, ordered by `f = g + h`.
- Add a counter as a tie-breaker so heap entries never compare states: `(f, counter, g, state)`.
- Keep a `best_g` dict and a closed set, and a `parents` map for path reconstruction.
- Goal test when a node is popped. Skip nodes already in the closed set.
- Both heuristics are consistent here, so a closed set is safe.
- `search_depth` is the goal's `g`. `max_depth` is the largest `g` generated.

Expected: cost **3** on the sample state with both heuristics, and cost **28** on seed 7. A\* must always find the same cost as BFS, and it should expand far fewer nodes.

## 6. Hooking into `main.py`

Uncomment these (and nothing else):

```python
from puzzle.ids import ids
from puzzle.astar import astar
```
```python
"ids": ids,
"astar-manhattan": lambda s: astar(s, "manhattan"),
"astar-euclidean": lambda s: astar(s, "euclidean"),
```

Check it:
```bash
python main.py --state 1,2,5,3,4,0,6,7,8 --algo all --no-trace
python main.py --random --seed 7 --algo all --no-trace
```

## 7. Tests

Add these at the bottom of `tests/test_algorithms.py` and add more of your own:

```python
from puzzle.ids import ids
from puzzle.astar import astar


def test_ids_optimal():
    r = ids(START)
    assert r.solved and r.cost == 3 and r.states[-1] == GOAL and _valid_path(r)


def test_astar_both_heuristics_optimal():
    for h in ("manhattan", "euclidean"):
        r = astar(START, h)
        assert r.solved and r.cost == 3 and r.states[-1] == GOAL and _valid_path(r)
```

Also test that A\* cost equals BFS cost on several random states (`random_state(seed)` for seeds 0 to 9).
Run everything with `python -m pytest -q`. All tests must pass before you open a pull request.

## 8. Report sections (yours)

1. **IDS:** explanation, data structures, why nodes expanded is summed across iterations, optimality, and the cost of repeated work.
2. **A\*:** explanation, data structures (priority queue, closed set, parent map), `f = g + h`.
3. **Heuristics comparison: Manhattan vs. Euclidean.** For each test state, report: path, cost, nodes expanded, search depth and running time. Then discuss:
   - Both heuristics are **admissible**, because they never overestimate the true cost.
   - Euclidean ≤ Manhattan on every state, so **Manhattan is the tighter (more informed) heuristic** and normally expands fewer nodes.
   - Whether the paths found were the same cost.
4. **Sample runs** with the step-by-step output from `main.py`.

Suggested comparison table (run each state several times, report a typical time):

| State | Heuristic | Cost | Nodes expanded | Depth | Time (s) |
|---|---|---|---|---|---|
| `1,2,5,3,4,0,6,7,8` | Manhattan | | | | |
| `1,2,5,3,4,0,6,7,8` | Euclidean | | | | |
| seed 7 | Manhattan | | | | |
| seed 7 | Euclidean | | | | |
| (add 2 more states) | | | | | |

Reference numbers from Member 1 for comparison (BFS): sample state has cost 3 and 10 expanded. Seed 7 has cost 28 and 179,170 expanded.

## 9. Git workflow

- Work only on your branch `ids-astar`.
- Commit one thing at a time: IDS, then A\*, then tests, then `main.py` hookup.
- Use clear messages, for example:
  ```
  git commit -m "Implement IDS" -m "Depth-limited DFS in a loop; nodes_expanded summed over iterations"
  ```
- Push and open a pull request into `main`:
  ```bash
  git push -u origin ids-astar
  ```
- Member 1 reviews and merges.

## 10. Definition of done

- [ ] `ids` and `astar` return a full `SearchResult` and follow the counting rule
- [ ] IDS and A\* (both heuristics) give the same cost as BFS on at least 10 random states
- [ ] `main.py` runs all five entries with `--algo all`
- [ ] `python -m pytest -q` passes
- [ ] Code is well commented (the assignment grades this)
- [ ] Your report sections are written, with the comparison table filled in
- [ ] Pull request opened by **20/10/2026**, leaving 3 days to merge and finish the combined report

## 11. Common mistakes

- Using a global visited set in IDS (it breaks the search).
- Forgetting the tie-breaker counter in `heapq`.
- Counting the blank tile in the heuristics. That overestimates and breaks admissibility.
- Resetting `nodes_expanded` on each IDS iteration instead of summing it.
- Setting `running_time` yourself (`main.py` does it).