"""Round 2: one grade-share vector across Tables 4 and 5.

The normal formula stays the default in evaluate(). This script only asks
whether the published inputs and excesses share one (Q1, Q2).
"""

from __future__ import annotations

import math

from backbone.ball_screw import STATIONS
from backbone.evaluator import (
    line_yield,
    machines_required,
    reliability_from_machines,
    required_input,
    workloads,
)

# (demand, input, reliability, O1-d1, O2-d2) as printed in Tables 4 and 5.
POLICY_I_ROWS = (
    ((400, 500), 2307.3693, 0.0000, 739.4459, 0.0),
    ((450, 450), 2076.6323, 0.0000, 575.5013, 0.0),
    ((500, 400), 1845.8954, 0.0625, 411.5567, 0.0),
    ((500, 300), 1384.4504, 0.8346, 183.6675, 0.0),
    ((400, 400), 1845.9339, 0.0625, 511.5567, 0.0),
    ((550, 350), 1615.1585, 0.6036, 247.6121, 0.0),
    ((600, 300), 1384.4216, 0.8346, 83.6675, 0.0),
    ((650, 250), 1316.2451, 0.9359, 0.0, 35.2264),
    ((700, 200), 1417.4947, 0.8346, 0.0, 107.1669),
    ((750, 150), 1518.7443, 0.6633, 0.0, 179.1073),
    ((750, 337), 1555.1669, 0.6633, 17.9865, 0.0),
    ((750, 338), 1559.7816, 0.6036, 20.2654, 0.0),
    ((750, 339), 1564.396, 0.6036, 22.5443, 0.0),
    ((750, 352), 1624.3880, 0.6036, 52.1699, 0.0),
    ((750, 353), 1629.0027, 0.3566, 54.4488, 0.0),
)
POLICY_II_ROWS = (
    ((400, 500), 1266.6672, 0.9486, 225.5170, -225.5170),
    ((450, 450), 1266.6672, 0.9486, 175.5170, -175.5170),
    ((500, 400), 1266.6672, 0.9486, 125.5170, -125.5170),
    ((500, 300), 1125.9264, 0.9655, 56.0151, -56.0151),
    ((400, 400), 1125.9264, 0.9655, 156.0151, -156.0151),
    ((550, 350), 1266.6672, 0.9486, 75.5170, -75.5170),
    ((600, 300), 1266.6672, 0.9486, 25.5170, -25.5170),
    ((650, 250), 1316.2451, 0.9359, 0.0, 35.2264),
    ((700, 200), 1417.4947, 0.8346, 0.0, 107.1669),
    ((750, 150), 1518.7443, 0.6633, 0.0, 179.1073),
    ((750, 337), 1529.8525, 0.6633, 5.4855, -5.48555),
    ((750, 338), 1531.2599, 0.6633, 6.1806, -6.18056),
    ((750, 339), 1532.6673, 0.6633, 6.8756, -6.87558),
    ((750, 352), 1550.9637, 0.6633, 15.9108, -15.9108),
    ((750, 353), 1552.3711, 0.6633, 16.6058, -16.6058),
)


def implied_shares(demand, raw_input, excess, theta: float) -> tuple[float, float]:
    output = tuple(demand[i] + excess[i] for i in range(2))
    scale = raw_input * theta
    return tuple(value / scale for value in output)


def reliability_of_input(raw_input: float) -> tuple[float, tuple[int, ...] | None]:
    loads = workloads(raw_input, STATIONS)
    required = []
    for load, station in zip(loads, STATIONS):
        count = machines_required(load, station)
        if count is None:
            return 0.0, None
        required.append(count)
    counts = tuple(required)
    return reliability_from_machines(counts, STATIONS), counts


def truncate_decimals(value: float, places: int) -> float:
    scale = 10**places
    return math.floor(value * scale + 1e-8) / scale


def replay(label: str, rows, shares: tuple[float, float], policy: int, theta: float) -> None:
    print(label)
    worst_input = 0.0
    worst_excess = 0.0
    reliability_off = 0
    for demand, published_input, published_r, e1, e2 in rows:
        demands = (float(demand[0]), float(demand[1]))
        raw_input = required_input(demands, shares, STATIONS, policy)
        output_scale = raw_input * theta
        grade_output = tuple(output_scale * share for share in shares)
        excess = tuple(grade_output[i] - demands[i] for i in range(2))
        reliability, _counts = reliability_of_input(raw_input)
        input_gap = abs(raw_input - published_input)
        excess_gap = max(abs(excess[0] - e1), abs(excess[1] - e2))
        worst_input = max(worst_input, input_gap)
        worst_excess = max(worst_excess, excess_gap)
        truncated = truncate_decimals(reliability, 4)
        flag = "R" if abs(truncated - published_r) > 5e-5 else " "
        if flag == "R":
            reliability_off += 1
        print(
            f"  {demand[0]:4},{demand[1]:<4}"
            f"  I {raw_input:10.4f} vs {published_input:10.4f}  dI {input_gap:8.4f}"
            f"  excess ({excess[0]:9.4f}, {excess[1]:9.4f})"
            f"  R {reliability:.6f} trunc {truncated:.4f} vs {published_r:.4f} {flag}"
        )
    print(
        f"  worst |dI| {worst_input:.4f}   worst |dexcess| {worst_excess:.4f}"
        f"   truncated reliability off {reliability_off}/{len(rows)}"
    )
    print()


def plateau_for(reference: float) -> tuple[float, float] | None:
    """Largest input interval around `reference` with the same machine vector."""
    reliability, counts = reliability_of_input(reference)
    if counts is None:
        return None
    low = reference
    high = reference
    step = 0.0001
    probe = reference
    while probe > 0:
        probe -= step
        _reliability, found = reliability_of_input(probe)
        if found != counts:
            break
        low = probe
    probe = reference
    while True:
        probe += step
        _reliability, found = reliability_of_input(probe)
        if found != counts:
            break
        high = probe
        if probe > 5000:
            break
    return low, high


def main() -> None:
    theta = line_yield(STATIONS)
    anchor = implied_shares((550, 350), 1615.1585, (247.6121, 0.0), theta)
    print(f"line yield = {theta:.10f}")
    print(f"shares implied by D=(550, 350), I=1615.1585, excess=(247.6121, 0):")
    print(f"  Q = ({anchor[0]:.10f}, {anchor[1]:.10f})  sum = {sum(anchor):.10f}")
    print()

    print("implied shares on every printed row")
    spreads = []
    for label, rows in (("Policy I", POLICY_I_ROWS), ("Policy II", POLICY_II_ROWS)):
        q1_values = []
        q2_values = []
        print(label)
        for demand, raw_input, _reliability, e1, e2 in rows:
            q1, q2 = implied_shares(demand, raw_input, (e1, e2), theta)
            q1_values.append(q1)
            q2_values.append(q2)
            print(f"  {demand[0]:4},{demand[1]:<4}  Q1={q1:.8f}  Q2={q2:.8f}")
        spread = (max(q1_values) - min(q1_values), max(q2_values) - min(q2_values))
        spreads.append(spread)
        print(f"  spread Q1 {spread[0]:.3e}   Q2 {spread[1]:.3e}")
    print()

    replay("replay Policy I with the anchor shares", POLICY_I_ROWS, anchor, 1, theta)
    replay("replay Policy II with the anchor shares", POLICY_II_ROWS, anchor, 2, theta)

    printed_q2 = 0.2743
    print(f"inputs recomputed with the printed Q2 = {printed_q2}")
    for d1, d2 in ((500, 300), (400, 400)):
        recomputed = d2 / (theta * printed_q2)
        print(f"  ({d1}, {d2})  d2 / (yield * 0.2743) = {recomputed:.4f}")
    print()

    band = plateau_for(1615.1585)
    if band is not None:
        print(
            "input interval with the same machine vector as I=1615.1585:"
            f" ({band[0]:.4f}, {band[1]:.4f}]"
        )
        print("manuscript states that reliability 0.6036 holds on [1559, 1627]")


if __name__ == "__main__":
    main()
