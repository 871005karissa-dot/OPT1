"""Round 4: inputs between Policy II and Policy I.

The manuscript treats a raw-material input between the two policy inputs as a
degree of downward substitution. Capacity states stay the same; only the
planned input moves, and reliability follows the existing machine steps.
"""

from __future__ import annotations

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
    machines_required,
    profit_two_grades,
    reliability_from_machines,
    required_input,
    workloads,
)


def input_between_policies(
    demands: tuple[float, float],
    shares: tuple[float, float],
    extent: float,
) -> float:
    """extent 0 uses the Policy II input. extent 1 uses the Policy I input."""
    if not 0.0 <= extent <= 1.0:
        raise ValueError("extent must lie between 0 and 1")
    low = required_input(demands, shares, STATIONS, 2)
    high = required_input(demands, shares, STATIONS, 1)
    return low + (high - low) * extent


def machine_counts(raw_input: float) -> tuple[int, ...] | None:
    counts = []
    for load, station in zip(workloads(raw_input, STATIONS), STATIONS):
        count = machines_required(load, station)
        if count is None:
            return None
        counts.append(count)
    return tuple(counts)


def reliability(raw_input: float) -> float:
    counts = machine_counts(raw_input)
    if counts is None:
        return 0.0
    return reliability_from_machines(counts, STATIONS)


def breakpoints(low: float, high: float) -> list[float]:
    """Inputs in (low, high) where the required machine count changes."""
    points = [low, high]
    passed_yield = 1.0
    for station in STATIONS:
        for previous in range(station.machine_count):
            boundary = previous * station.machine_capacity / passed_yield
            if low < boundary < high:
                points.append(boundary)
        passed_yield *= station.yield_rate
    points.sort()
    return points


def accounting(raw_input: float, demands: tuple[float, float], shares: tuple[float, float]):
    return profit_two_grades(
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


def main() -> None:
    demands = (float(DEMAND[0]), float(DEMAND[1]))
    shares = (float(MANUSCRIPT_SHARES[0]), float(MANUSCRIPT_SHARES[1]))
    low = input_between_policies(demands, shares, 0.0)
    high = input_between_policies(demands, shares, 1.0)
    print(f"D = {DEMAND}")
    print(f"Policy II input {low:.4f}    Policy I input {high:.4f}")
    ends = (
        ("extent 0", low, 2),
        ("extent 1", high, 1),
    )
    for label, raw_input, policy in ends:
        partial = accounting(raw_input, demands, shares)
        direct = profit_two_grades(
            raw_input,
            demands,
            shares,
            STATIONS,
            PRICES,
            MATERIAL_COST,
            MANUFACTURING_COSTS,
            HOLDING_COST_PER_DAY,
            STORAGE_DAYS,
            policy,
        )
        print(
            f"  {label}: partial profit {partial.profit:.4f}"
            f"  policy {policy} profit {direct.profit:.4f}"
            f"  reliability {reliability(raw_input):.6f}"
        )
    print()

    edges = breakpoints(low, high)
    print("reliability steps between the two inputs")
    rows = []
    for left, right in zip(edges, edges[1:]):
        sample = (left + right) / 2.0
        just_inside = right - 1e-6 if right - left > 1e-4 else sample
        step_profit = accounting(just_inside, demands, shares).profit
        step_reliability = reliability(sample)
        counts = machine_counts(sample)
        rows.append((left, right, step_reliability, step_profit, counts))
        print(
            f"  ({left:10.4f}, {right:10.4f}]"
            f"  R {step_reliability:.6f}"
            f"  profit at right {step_profit:10.4f}"
            f"  machines {counts}"
        )
    slope = (rows[-1][3] - rows[0][3]) / (high - low)
    print(f"profit change per unit input, end to end: {slope:.4f}")
    print(f"steps: {len(rows)}")

    front = []
    for row in rows:
        dominated = False
        for other in rows:
            if other is row:
                continue
            reliability_better = other[2] >= row[2] - 1e-12
            profit_better = other[3] >= row[3] - 1e-6
            strictly = other[2] > row[2] + 1e-12 or other[3] > row[3] + 1e-6
            if reliability_better and profit_better and strictly:
                dominated = True
                break
        if not dominated:
            front.append(row)
    print(f"non-dominated steps: {len(front)} of {len(rows)}")


if __name__ == "__main__":
    main()
