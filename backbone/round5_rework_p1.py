"""Round 5: turn on one rework path, P1=(2, 2, 1).

The path is the jumper-cable case's first path: station 2 reworks its own
yield loss once. The line, grades, and demand stay the ball-screw example.
P2 and P3 stay off. With the path omitted, the flow is the previous rounds.
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
    capacity_state_count,
    machines_required,
    profit_two_grades,
    reliability_from_machines,
    required_input,
    workloads,
)

P1 = ReworkPath(entry=2, detection=2, cycles=1)


def lower_vector(raw_input: float, rework: ReworkPath | None):
    loads = workloads(raw_input, STATIONS, rework)
    counts = []
    for load, station in zip(loads, STATIONS):
        count = machines_required(load, station)
        if count is None:
            return loads, None, None, 0.0
        counts.append(count)
    required = tuple(counts)
    vector = tuple(count * station.machine_capacity for count, station in zip(required, STATIONS))
    reliability = reliability_from_machines(required, STATIONS)
    return loads, required, vector, reliability


def main() -> None:
    demands = (float(DEMAND[0]), float(DEMAND[1]))
    shares = (float(MANUSCRIPT_SHARES[0]), float(MANUSCRIPT_SHARES[1]))
    print(f"D = {DEMAND}   states = {capacity_state_count(STATIONS)}")
    print(f"P1 = ({P1.entry}, {P1.detection}, {P1.cycles})")
    print()
    for policy in (1, 2):
        print(f"Policy {policy}")
        for label, path in (("off", None), ("P1", P1)):
            raw_input = required_input(demands, shares, STATIONS, policy, path)
            loads, machines, vector, reliability = lower_vector(raw_input, path)
            result = profit_two_grades(
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
                path,
            )
            shown = ", ".join(f"{load:.4f}" for load in loads)
            print(f"  {label}")
            print(f"    input {raw_input:.4f}   loads ({shown})")
            print(f"    LCV {vector}   machines {machines}   R {reliability:.6f}")
            print(f"    material {result.material:.4f}   manufacturing {result.manufacturing:.4f}")
            print(f"    profit {result.profit:.4f}")
        print()


if __name__ == "__main__":
    main()
