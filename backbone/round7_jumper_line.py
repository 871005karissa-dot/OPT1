"""Round 7: jumper-cable stations, rework off.

The rework case gives six stations and the insertion-loss grades. It does not
give an order quantity. D = (550, 350) is the manuscript order, run here only
to see whether this line can hold it.
"""

from __future__ import annotations

from backbone.ball_screw import DEMAND, MANUSCRIPT_SHARES
from backbone.evaluator import (
    binomial_pmf,
    capacity_state_count,
    machines_required,
    reliability_from_machines,
    required_input,
    workloads,
)
from backbone.jumper import PUBLISHED_PMF, SCRAP_RATE, SHARES, STATIONS


def ceiling() -> float:
    unit = workloads(1.0, STATIONS)
    return min(
        station.max_capacity / load
        for station, load in zip(STATIONS, unit)
        if load > 0.0
    )


def reliability_at(raw_input: float) -> tuple[tuple[int, ...] | None, float]:
    loads = workloads(raw_input, STATIONS)
    counts = []
    for load, station in zip(loads, STATIONS):
        count = machines_required(load, station)
        if count is None:
            return None, 0.0
        counts.append(count)
    required = tuple(counts)
    return required, reliability_from_machines(required, STATIONS)


def close(left: float, right: float) -> str:
    return "match" if abs(left - right) <= 5e-5 else "diff"


def main() -> None:
    print(f"states = {capacity_state_count(STATIONS)}")
    print(f"insertion-loss shares Q = ({SHARES[0]:.6f}, {SHARES[1]:.6f})")
    print(f"share above 0.35 dB = {SCRAP_RATE:.6f}")
    limit = ceiling()
    print(f"largest feasible raw input = {limit:.4f}")
    machines, reliability = reliability_at(limit)
    print(f"at that input  machines {machines}  R {reliability:.6f}")
    print()
    print("binomial table, four decimals")
    for station in STATIONS:
        pmf = binomial_pmf(station.machine_count, station.availability)
        flags = [close(value, target) for value, target in zip(pmf, PUBLISHED_PMF[station.name])]
        verdict = "match" if all(flag == "match" for flag in flags) else "diff"
        print(f"  {station.name}: {verdict}")
    print()
    ball_shares = (float(MANUSCRIPT_SHARES[0]), float(MANUSCRIPT_SHARES[1]))
    for name, shares in (("insertion-loss shares", SHARES), ("ball-screw shares", ball_shares)):
        raw_input = required_input(DEMAND, shares, STATIONS, 1)
        _machines, reliability = reliability_at(raw_input)
        print(
            f"D = {DEMAND} Policy I with {name}:"
            f" input {raw_input:.4f}  R {reliability:.4f}"
        )


if __name__ == "__main__":
    main()
