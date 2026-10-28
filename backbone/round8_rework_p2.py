"""Round 8: turn on P2=(5, 6, 1) on the jumper line.

Units whose insertion loss exceeds 0.35 dB return from station 6 to station 5
once. P1 and P3 stay off. The comparison input is half the smaller feasible
ceiling, because the rework case states no order quantity.
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


def ceiling(path: ReworkPath | None) -> float:
    scrap = None if path is None else SCRAP_RATE
    unit = workloads(1.0, STATIONS, path, scrap)
    return min(station.max_capacity / load for station, load in zip(STATIONS, unit))


def picture(raw_input: float, path: ReworkPath | None):
    scrap = None if path is None else SCRAP_RATE
    loads = workloads(raw_input, STATIONS, path, scrap)
    counts = []
    for load, station in zip(loads, STATIONS):
        count = machines_required(load, station)
        if count is None:
            return loads, None, 0.0
        counts.append(count)
    required = tuple(counts)
    return loads, required, reliability_from_machines(required, STATIONS)


def main() -> None:
    off_limit = ceiling(None)
    on_limit = ceiling(P2)
    common = 0.5 * min(off_limit, on_limit)
    print(f"states = {capacity_state_count(STATIONS)}")
    print(f"share above 0.35 dB = {SCRAP_RATE:.6f}")
    print(f"feasible ceiling off {off_limit:.4f}   P2 {on_limit:.4f}")
    print(f"common input {common:.4f}")
    for label, path in (("off", None), ("P2", P2)):
        loads, machines, reliability = picture(common, path)
        shown = ", ".join(f"{load:.4f}" for load in loads)
        print(f"  {label}: loads ({shown})")
        print(f"       machines {machines}   R {reliability:.6f}")
    span = min(off_limit, on_limit)
    first = None
    for step in range(1, 4001):
        raw_input = span * step / 4000.0
        _loads, off_machines, off_r = picture(raw_input, None)
        _loads, on_machines, on_r = picture(raw_input, P2)
        if off_machines != on_machines:
            first = (raw_input, off_machines, off_r, on_machines, on_r)
            break
    if first is None:
        print("machine vector unchanged on 4000 inputs up to the ceiling")
    else:
        raw_input, off_machines, off_r, on_machines, on_r = first
        print(
            f"first machine-vector change at input {raw_input:.4f}:"
            f" {off_machines} R {off_r:.6f} -> {on_machines} R {on_r:.6f}"
        )


if __name__ == "__main__":
    main()
