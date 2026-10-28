"""Round 18: open P1 on top of P2 and P3 on the jumper line.

Station 2 still reworks its own yield loss once. Units above 0.35 dB still
return through P2, then the residue through P3. Earlier ceilings are reprinted
so this combination can be compared with rounds 8, 9, and 17.
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

P1 = ReworkPath(2, 2, 1)
P2 = ReworkPath(5, 6, 1)
P3 = ReworkPath(2, 6, 1)
RETURNS = (P2, P3)
TRIPLE = (P1, P2, P3)

PRIOR = (
    ("off", None, 369.2280),
    ("P1", P1, 360.3279),
    ("P2", P2, 369.2280),
    ("P2+P3", RETURNS, 360.1286),
)


def ceiling(path) -> float:
    scrap = SCRAP_RATE if path not in (None, P1) else None
    unit = workloads(1.0, STATIONS, path, scrap)
    return min(station.max_capacity / load for station, load in zip(STATIONS, unit) if load > 0.0)


def picture(raw_input: float, path):
    scrap = SCRAP_RATE if path not in (None, P1) else None
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
    print(f"states = {capacity_state_count(STATIONS)}")
    for label, path, published in PRIOR:
        limit = ceiling(path)
        flag = "match" if abs(limit - published) <= 5e-4 else "diff"
        print(f"prior ceiling {label} {limit:.4f}  {flag} {published:.4f}")
    both_limit = ceiling(RETURNS)
    triple_limit = ceiling(TRIPLE)
    common = 0.5 * min(both_limit, triple_limit)
    print(f"feasible ceiling P2+P3 {both_limit:.4f}   P1+P2+P3 {triple_limit:.4f}")
    print(f"common input {common:.4f}")
    for label, path in (("P2+P3", RETURNS), ("P1+P2+P3", TRIPLE)):
        loads, machines, reliability = picture(common, path)
        shown = ", ".join(f"{load:.4f}" for load in loads)
        print(f"  {label}: loads ({shown})")
        print(f"           machines {machines}   R {reliability:.6f}")
    span = min(both_limit, triple_limit)
    first = None
    for step in range(1, 4001):
        raw_input = span * step / 4000.0
        _loads, left_machines, left_r = picture(raw_input, RETURNS)
        _loads, right_machines, right_r = picture(raw_input, TRIPLE)
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
