"""Round 11: delivered profit averaged over the capacity states.

The planned account from round 3 is unchanged. This round books revenue on
units the realized flow sells, then averages that profit over all 28224
machine-count states. Rework stays off.
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
    machines_required,
    profit_from_flow,
    profit_two_grades,
    realized_series_flow,
    reliability_from_machines,
    required_input,
    throughput,
    workloads,
)


def feasible_limit() -> float:
    passed_yield = 1.0
    limit = float("inf")
    for station in STATIONS:
        limit = min(limit, station.max_capacity / passed_yield)
        passed_yield *= station.yield_rate
    return limit


def breakpoints(low: float, high: float) -> list[float]:
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


def machine_counts(raw_input: float) -> tuple[int, ...] | None:
    counts = []
    for load, station in zip(workloads(raw_input, STATIONS), STATIONS):
        count = machines_required(load, station)
        if count is None:
            return None
        counts.append(count)
    return tuple(counts)


def main() -> None:
    demands = (float(DEMAND[0]), float(DEMAND[1]))
    shares = (float(MANUSCRIPT_SHARES[0]), float(MANUSCRIPT_SHARES[1]))
    low = required_input(demands, shares, STATIONS, 2)
    high = required_input(demands, shares, STATIONS, 1)
    ceiling = feasible_limit()
    print(f"D = {DEMAND}")
    print(f"states = {8 * 7 * 8 * 9 * 7}")
    print(f"Policy II input {low:.4f}   Policy I input {high:.4f}   feasible ceiling {ceiling:.4f}")

    full_capacity = tuple(station.max_capacity for station in STATIONS)
    for label, raw_input, policy in (("Policy II", low, 2), ("Policy I", high, 1)):
        planned = profit_two_grades(
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
        loads, finished = realized_series_flow(raw_input, full_capacity, STATIONS)
        grades = (finished * shares[0], finished * shares[1])
        delivered = profit_from_flow(
            grades,
            loads,
            demands,
            PRICES,
            MATERIAL_COST,
            MANUFACTURING_COSTS,
            HOLDING_COST_PER_DAY,
            STORAGE_DAYS,
            policy,
            revenue_on_delivered=True,
        )
        print(
            f"  {label} all machines up: planned {planned.profit:.4f}"
            f"  delivered {delivered.profit:.4f}"
        )

    edges = breakpoints(0.0, ceiling - 1e-6)
    print()
    print("expected delivered profit from the first machine up to the ceiling, policy 2")
    started = time.perf_counter()
    rows = []
    for left, right in zip(edges, edges[1:]):
        sample = right - 1e-4
        expected, mass = expected_profit_two_grades(
            sample,
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
        planned = profit_two_grades(
            sample,
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
        counts = machine_counts(sample)
        reliability = 0.0 if counts is None else reliability_from_machines(counts, STATIONS)
        rows.append((right, reliability, planned.profit, expected, counts, mass))
        mark = ""
        if abs(right - low) < 0.05 or abs(right - high) < 0.05:
            mark = "  <-- policy input"
        print(
            f"  input {right:10.4f}"
            f"  R {reliability:.6f}"
            f"  planned {planned.profit:10.2f}"
            f"  expected {expected:10.2f}"
            f"  machines {counts}{mark}"
        )
    elapsed = time.perf_counter() - started
    best = max(rows, key=lambda row: row[3])
    decreases = sum(1 for earlier, later in zip(rows, rows[1:]) if later[3] < earlier[3] - 1e-6)
    print(f"steps {len(rows)}   probability mass {rows[0][5]:.6f}   elapsed {elapsed:.2f}s")
    print(f"steps where expected profit falls: {decreases}")
    print(
        f"highest step-edge expected profit {best[3]:.2f} at input {best[0]:.4f}"
        f"  R {best[1]:.6f}"
    )
    onset = demands[0] / (throughput(STATIONS) * shares[0])
    for label, raw_input in (
        ("grade-1 output reaches 550", onset),
        ("Policy II", low),
        ("Policy I", high),
    ):
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
        print(
            f"  {label}: input {raw_input:.4f}"
            f"  R {reliability:.6f}"
            f"  expected {expected:.2f}"
            f"  machines {counts}"
        )


if __name__ == "__main__":
    main()
