"""Round 20: sample expected profit inside each machine-count step.

Same delivered-profit function as round 11. Rework stays off. Nine interior
fractions plus the right edge used in round 11 are scored on D = (550, 350).
A step has an interior high point when some interior sample beats that edge.
"""

from __future__ import annotations

import time

from backbone.ball_screw import (
    DEMAND,
    HOLDING_COST_PER_DAY,
    MANUFACTURING_COSTS,
    MANUSCRIPT_SHARES,
    MATERIAL_COST,
    PRICES,
    STATIONS,
    STORAGE_DAYS,
)
from backbone.evaluator import (
    expected_profit_two_grades,
    reliability_from_machines,
    throughput,
)
from backbone.round11_expected_profit import breakpoints, feasible_limit, machine_counts

FRACS = (0.02, 0.14, 0.26, 0.38, 0.50, 0.62, 0.74, 0.86, 0.98)
FINE = tuple(i / 40.0 for i in range(1, 40))


def score(raw_input: float, demands, shares):
    expected, _mass = expected_profit_two_grades(
        raw_input,
        demands,
        shares,
        STATIONS,
        PRICES,
        MATERIAL_COST,
        MANUFACTURING_COSTS,
        HOLDING_COST_PER_DAY,
        STORAGE_DAYS,
        2,
    )
    counts = machine_counts(raw_input)
    reliability = 0.0 if counts is None else reliability_from_machines(counts, STATIONS)
    return expected, reliability, counts


def nondominated(rows: list[tuple]) -> list[tuple]:
    kept = []
    for row in rows:
        dominated = False
        for other in rows:
            if other is row:
                continue
            reliability_ok = other[1] >= row[1] - 1e-12
            profit_ok = other[2] >= row[2] - 1e-6
            stricter = other[1] > row[1] + 1e-12 or other[2] > row[2] + 1e-6
            if reliability_ok and profit_ok and stricter:
                dominated = True
                break
        if not dominated:
            kept.append(row)
    return kept


def main() -> None:
    demands = (float(DEMAND[0]), float(DEMAND[1]))
    shares = (float(MANUSCRIPT_SHARES[0]), float(MANUSCRIPT_SHARES[1]))
    ceiling = feasible_limit()
    edges = breakpoints(0.0, ceiling - 1e-6)
    onset = demands[0] / (throughput(STATIONS) * shares[0])
    print(f"D = {DEMAND}   states = {8 * 7 * 8 * 9 * 7}   ceiling {ceiling:.4f}")
    started = time.perf_counter()
    step_best = []
    placed = {"right": 0, "left": 0, "middle": 0}
    global_best = None
    calls = 0

    def consider(raw_input: float, right: float, best, edge_expected):
        nonlocal calls, global_best
        expected, reliability, counts = score(raw_input, demands, shares)
        calls += 1
        if abs(raw_input - (right - 1e-4)) < 1e-8:
            edge_expected = expected
        candidate = (raw_input, reliability, expected, counts, right)
        if best is None or expected > best[2]:
            best = candidate
        if global_best is None or expected > global_best[2]:
            global_best = candidate
        return best, edge_expected

    for left, right in zip(edges, edges[1:]):
        width = right - left
        if width <= 1e-8:
            continue
        points = [left + frac * width for frac in FRACS]
        points.append(right - 1e-4)
        if left < onset < right:
            points.append(onset)
        best = None
        edge_expected = None
        for raw_input in points:
            if left < raw_input < right:
                best, edge_expected = consider(raw_input, right, best, edge_expected)
        if best is None or edge_expected is None:
            continue
        if left + 0.05 * width < best[0] < right - 0.05 * width:
            fine_best = best
            fine_edge = edge_expected
            for frac in FINE:
                raw_input = left + frac * width
                fine_best, fine_edge = consider(raw_input, right, fine_best, fine_edge)
            best = fine_best
            edge_expected = fine_edge
        if best[0] >= right - 0.05 * width:
            place = "right"
        elif best[0] <= left + 0.05 * width:
            place = "left"
        else:
            place = "middle"
            print(
                f"  middle high on ({left:.4f}, {right:.4f}]"
                f"  sample {best[0]:.4f}  E {best[2]:.2f}  edge E {edge_expected:.2f}"
                f"  R {best[1]:.6f}  machines {best[3]}"
            )
        placed[place] += 1
        step_best.append(best)
    front = nondominated(step_best)
    elapsed = time.perf_counter() - started
    print(
        f"steps {len(step_best)}   samples {calls}"
        f"   right {placed['right']}   left {placed['left']}   middle {placed['middle']}"
        f"   elapsed {elapsed:.1f}s"
    )
    print(f"non-dominated steps {len(front)}")
    for raw_input, reliability, expected, counts, right in front:
        print(
            f"  input {raw_input:10.4f}  step-end {right:10.4f}"
            f"  R {reliability:.6f}  E {expected:10.2f}  machines {counts}"
        )
    if global_best is not None:
        raw_input, reliability, expected, counts, right = global_best
        print(
            f"highest sample {raw_input:.4f}  E {expected:.2f}"
            f"  R {reliability:.6f}  machines {counts}  step-end {right:.4f}"
        )
        print(f"grade-1 onset {onset:.4f}")


if __name__ == "__main__":
    main()
