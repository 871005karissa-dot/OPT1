"""Round 9: add P3=(2, 6, 1) on top of P2.

P3 is the one return to station 2 of units that still exceed 0.35 dB after the
P2 pass. The comparison is P2 alone against P2 plus P3.
"""

from __future__ import annotations

from backbone.evaluator import (
    ReworkPath,
    capacity_state_count,
    machines_required,
    reliability_from_machines,
    workloads,
)
from backbone.jumper import SCRAP_RATE, STATIONS

P2 = ReworkPath(5, 6, 1)
P3 = ReworkPath(2, 6, 1)
BOTH = (P2, P3)


def ceiling(path) -> float:
    unit = workloads(1.0, STATIONS, path, SCRAP_RATE)
    return min(station.max_capacity / load for station, load in zip(STATIONS, unit))


def picture(raw_input: float, path):
    loads = workloads(raw_input, STATIONS, path, SCRAP_RATE)
    counts = []
    for load, station in zip(loads, STATIONS):
        count = machines_required(load, station)
        if count is None:
            return loads, None, 0.0
        counts.append(count)
    required = tuple(counts)
    return loads, required, reliability_from_machines(required, STATIONS)


def main() -> None:
    p2_limit = ceiling(P2)
    both_limit = ceiling(BOTH)
    common = 0.5 * min(p2_limit, both_limit)
    print(f"states = {capacity_state_count(STATIONS)}")
    print(f"feasible ceiling P2 {p2_limit:.4f}   P2+P3 {both_limit:.4f}")
    print(f"common input {common:.4f}")
    for label, path in (("P2", P2), ("P2+P3", BOTH)):
        loads, machines, reliability = picture(common, path)
        shown = ", ".join(f"{load:.4f}" for load in loads)
        print(f"  {label}: loads ({shown})")
        print(f"         machines {machines}   R {reliability:.6f}")
    span = min(p2_limit, both_limit)
    first = None
    for step in range(1, 4001):
        raw_input = span * step / 4000.0
        _loads, left_machines, left_r = picture(raw_input, P2)
        _loads, right_machines, right_r = picture(raw_input, BOTH)
        if left_machines != right_machines:
            first = (raw_input, left_machines, left_r, right_machines, right_r)
            break
    if first is None:
        print("machine vector unchanged on 4000 inputs up to the ceiling")
    else:
        raw_input, left_machines, left_r, right_machines, right_r = first
        print(
            f"first machine-vector change at input {raw_input:.4f}:"
            f" {left_machines} R {left_r:.6f} -> {right_machines} R {right_r:.6f}"
        )


if __name__ == "__main__":
    main()
