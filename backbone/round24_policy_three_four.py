"""Round 24: Policy III and Policy IV against the manuscript policies.

Policy III opens P1 and sets the release quantity between the two P1 inputs.
Extent 0 is Policy II with P1. Extent 1 is Policy I with P1. Grade shares stay
the manuscript shares.

Policy IV sends every grade-2 unit back to station 2 once. A fraction equal to
station 2's yield becomes grade 1. The rest leaves grade 2. The forward pass
does not use P1. Grade-2 demand is then filled by grade 1.
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
    ReworkPath,
    line_yield,
    machines_required,
    profit_from_flow,
    profit_two_grades,
    reliability_from_machines,
    required_input,
    workloads,
)
from backbone.round2_share_consistency import POLICY_I_ROWS

P1 = ReworkPath(2, 2, 1)
UPGRADE = STATIONS[1].yield_rate
SHARES = (float(MANUSCRIPT_SHARES[0]), float(MANUSCRIPT_SHARES[1]))


def money(raw_input: float, demands, policy: int, rework):
    return profit_two_grades(
        raw_input,
        demands,
        SHARES,
        STATIONS,
        PRICES,
        MATERIAL_COST,
        MANUFACTURING_COSTS,
        HOLDING_COST_PER_DAY,
        STORAGE_DAYS,
        policy,
        rework,
    )


def covered(raw_input: float, rework, extra_station2: float = 0.0):
    loads = list(workloads(raw_input, STATIONS, rework))
    loads[1] += extra_station2
    counts = []
    for load, station in zip(loads, STATIONS):
        count = machines_required(load, station)
        if count is None:
            return tuple(loads), None, 0.0
        counts.append(count)
    required = tuple(counts)
    return tuple(loads), required, reliability_from_machines(required, STATIONS)


def release(demands, policy: int, rework) -> float:
    return required_input(demands, SHARES, STATIONS, policy, rework)


def boundaries(low: float, high: float, rework) -> list[float]:
    unit = workloads(1.0, STATIONS, rework)
    points = [low, high]
    for per_input, station in zip(unit, STATIONS):
        for count in range(station.machine_count + 1):
            boundary = count * station.machine_capacity / per_input
            if low + 1e-6 < boundary < high - 1e-6:
                points.append(boundary)
    points.sort()
    merged = [points[0]]
    for point in points[1:]:
        if point - merged[-1] > 1e-6:
            merged.append(point)
    return merged


def steps(demands, rework):
    low = release(demands, 2, rework)
    high = release(demands, 1, rework)
    rows = []
    for left, right in zip(boundaries(low, high, rework), boundaries(low, high, rework)[1:]):
        sample = (left + right) / 2.0
        probe = right - 1e-4 if right - left > 1e-3 else sample
        result = money(probe, demands, 2, rework)
        _loads, machines, reliability = covered(sample, rework)
        rows.append((left, right, reliability, result.profit, machines))
    return rows


def policy_iv(demands):
    """Grade-2 units return to station 2. Successes join grade 1."""
    throughput = line_yield(STATIONS)
    grade1, grade2 = SHARES
    kept = grade1 + UPGRADE * grade2
    raw_input = (demands[0] + demands[1]) / (throughput * kept)
    finished = raw_input * throughput
    sent = finished * grade2
    grades = (finished * kept, 0.0)
    loads, machines, reliability = covered(raw_input, None, sent)
    result = profit_from_flow(
        grades,
        loads,
        demands,
        PRICES,
        MATERIAL_COST,
        MANUFACTURING_COSTS,
        HOLDING_COST_PER_DAY,
        STORAGE_DAYS,
        2,
    )
    return raw_input, sent, result, machines, reliability


def main() -> None:
    demands = (float(DEMAND[0]), float(DEMAND[1]))
    print(f"D = {DEMAND}   storage {STORAGE_DAYS:.0f}   upgrade yield {UPGRADE:.2f}")
    print(f"shares {SHARES[0]:.6f}, {SHARES[1]:.6f}   states = {8 * 7 * 8 * 9 * 7}")
    print()
    print("manuscript policies and the same policies with P1")
    for label, policy, rework in (
        ("I", 1, None),
        ("II", 2, None),
        ("I+P1", 1, P1),
        ("II+P1", 2, P1),
    ):
        raw_input = release(demands, policy, rework)
        result = money(raw_input, demands, policy, rework)
        _loads, machines, reliability = covered(raw_input, rework)
        print(
            f"  {label:5} input {raw_input:.4f}"
            f"  profit {result.profit:.4f}"
            f"  R {reliability:.6f}"
            f"  machines {machines}"
        )

    print()
    print("Policy III: P1 on, input between II+P1 and I+P1")
    for left, right, reliability, profit, machines in steps(demands, P1):
        print(
            f"  ({left:10.4f}, {right:10.4f}]"
            f"  R {reliability:.6f}"
            f"  profit {profit:10.4f}"
            f"  machines {machines}"
        )
    print("same extents with rework off")
    for left, right, reliability, profit, machines in steps(demands, None):
        print(
            f"  ({left:10.4f}, {right:10.4f}]"
            f"  R {reliability:.6f}"
            f"  profit {profit:10.4f}"
            f"  machines {machines}"
        )

    print()
    raw_input, sent, result, machines, reliability = policy_iv(demands)
    loads, _machines, _reliability = covered(raw_input, None, sent)
    print("Policy IV: grade 2 returns to station 2")
    print(f"  input {raw_input:.4f}   grade-2 sent {sent:.4f}")
    print(f"  loads ({', '.join(f'{load:.4f}' for load in loads)})")
    print(
        f"  output grade1 {result.output[0]:.4f}  grade2 {result.output[1]:.4f}"
        f"  substituted {result.substituted_grade1_for_grade2:.4f}"
    )
    print(
        f"  material {result.material:.4f}  manufacturing {result.manufacturing:.4f}"
        f"  substitution {result.substitution_loss:.4f}"
        f"  inventory {result.inventory:.4f}"
    )
    print(f"  profit {result.profit:.4f}   R {reliability:.6f}   machines {machines}")

    print()
    print("fifteen orders: profit and reliability")
    print(f"  {'order':12} {'I':>18} {'II':>18} {'I+P1':>18} {'II+P1':>18} {'IV':>18}")
    for demand, *_rest in POLICY_I_ROWS:
        order = (float(demand[0]), float(demand[1]))
        cells = []
        for policy, rework in ((1, None), (2, None), (1, P1), (2, P1)):
            raw_input = release(order, policy, rework)
            profit = money(raw_input, order, policy, rework).profit
            _loads, _machines, reliability = covered(raw_input, rework)
            cells.append(f"{profit:9.2f} {reliability:.4f}")
        iv_input, _sent, iv_result, _machines, iv_reliability = policy_iv(order)
        cells.append(f"{iv_result.profit:9.2f} {iv_reliability:.4f}")
        print(f"  {demand[0]:4},{demand[1]:<4}   " + "  ".join(cells) + f"   IV input {iv_input:.2f}")


if __name__ == "__main__":
    main()
