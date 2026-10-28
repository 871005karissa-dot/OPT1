"""Round 14: expected profit with P1 on, for D = (550, 350).

Realized flow now reworks station 2's yield loss once when P1 is passed.
The planned account is unchanged. Storage is 30 days. P2 and P3 stay off.
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
    ReworkPath,
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

P1 = ReworkPath(2, 2, 1)


def ceiling(rework: ReworkPath | None) -> float:
    units = workloads(1.0, STATIONS, rework)
    limit = float("inf")
    for unit, station in zip(units, STATIONS):
        limit = min(limit, station.max_capacity / unit)
    return limit


def breakpoints(high: float, rework: ReworkPath | None) -> list[float]:
    points = [0.0, high]
    units = workloads(1.0, STATIONS, rework)
    for unit, station in zip(units, STATIONS):
        for previous in range(station.machine_count):
            boundary = previous * station.machine_capacity / unit
            if 0.0 < boundary < high:
                points.append(boundary)
    points.sort()
    return points


def machine_counts(raw_input: float, rework: ReworkPath | None) -> tuple[int, ...] | None:
    counts = []
    for load, station in zip(workloads(raw_input, STATIONS, rework), STATIONS):
        count = machines_required(load, station)
        if count is None:
            return None
        counts.append(count)
    return tuple(counts)


def score(raw_input: float, demands, shares, rework: ReworkPath | None):
    expected, mass = expected_profit_two_grades(
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
        rework,
    )
    counts = machine_counts(raw_input, rework)
    reliability = 0.0 if counts is None else reliability_from_machines(counts, STATIONS)
    return expected, reliability, counts, mass


def main() -> None:
    demands = (float(DEMAND[0]), float(DEMAND[1]))
    shares = (float(MANUSCRIPT_SHARES[0]), float(MANUSCRIPT_SHARES[1]))
    full = tuple(station.max_capacity for station in STATIONS)
    print(f"D = {DEMAND}   states = {8 * 7 * 8 * 9 * 7}")
    for label, rework in (("off", None), ("P1", P1)):
        limit = ceiling(rework)
        onset = demands[0] / (throughput(STATIONS, rework) * shares[0])
        policy_ii = required_input(demands, shares, STATIONS, 2, rework)
        policy_i = required_input(demands, shares, STATIONS, 1, rework)
        print(
            f"{label}: ceiling {limit:.4f}"
            f"  onset {onset:.4f}  II {policy_ii:.4f}  I {policy_i:.4f}"
        )
        for name, raw_input, policy in (("II", policy_ii, 2), ("I", policy_i, 1)):
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
                rework,
            )
            loads, finished = realized_series_flow(raw_input, full, STATIONS, rework)
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
                f"  all up {name}: planned {planned.profit:.4f}"
                f"  delivered {delivered.profit:.4f}"
                f"  loads match {tuple(round(a - b, 6) for a, b in zip(loads, planned_loads(raw_input, rework))) == (0, 0, 0, 0, 0)}"
            )
        points = [right - 1e-4 for right in breakpoints(limit - 1e-6, rework)[1:]]
        for extra in (onset, policy_ii, policy_i):
            if 0.0 < extra < limit:
                points.append(extra)
        started = time.perf_counter()
        best = None
        for raw_input in points:
            expected, reliability, counts, mass = score(raw_input, demands, shares, rework)
            if best is None or expected > best[0]:
                best = (expected, raw_input, reliability, counts, mass)
        elapsed = time.perf_counter() - started
        expected, raw_input, reliability, counts, mass = best
        print(
            f"  peak input {raw_input:.4f}  E {expected:.2f}"
            f"  R {reliability:.6f}  machines {counts}"
            f"  mass {mass:.6f}  {elapsed:.2f}s"
        )


def planned_loads(raw_input: float, rework: ReworkPath | None) -> tuple[float, ...]:
    return workloads(raw_input, STATIONS, rework)


if __name__ == "__main__":
    main()
