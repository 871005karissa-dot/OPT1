"""Round 21: move every station yield by 5 percent and rescore Table 4.

Same delivered-profit function as round 12. Rework stays off. A yield that
would reach 1 is held just below 1, and that station is printed. The comparison
is the peak kind at the manuscript yields.
"""

from __future__ import annotations

import time
from dataclasses import replace

from backbone.ball_screw import (
    HOLDING_COST_PER_DAY,
    MANUFACTURING_COSTS,
    MANUSCRIPT_SHARES,
    MATERIAL_COST,
    PRICES,
    STATIONS,
    STORAGE_DAYS,
)
from backbone.evaluator import (
    Workstation,
    expected_profit_two_grades,
    machines_required,
    reliability_from_machines,
    required_input,
    throughput,
    workloads,
)
from backbone.round2_share_consistency import POLICY_I_ROWS


def scaled(factor: float) -> tuple[tuple[Workstation, ...], tuple[str, ...]]:
    stations = []
    clamped = []
    for station in STATIONS:
        raw = station.yield_rate * factor
        if raw >= 1.0:
            clamped.append(station.name)
            raw = 1.0 - 1e-12
        stations.append(replace(station, yield_rate=raw))
    return tuple(stations), tuple(clamped)


def ceiling(stations: tuple[Workstation, ...]) -> float:
    unit = workloads(1.0, stations)
    return min(station.max_capacity / load for station, load in zip(stations, unit) if load > 0.0)


def boundaries(stations: tuple[Workstation, ...], high: float) -> list[float]:
    unit = workloads(1.0, stations)
    cuts = [0.0, high]
    for load, station in zip(unit, stations):
        if load <= 0.0:
            continue
        for machines in range(1, station.machine_count + 1):
            cut = machines * station.machine_capacity / load
            if 0.0 < cut < high:
                cuts.append(cut)
    cuts.sort()
    distinct = [cuts[0]]
    for cut in cuts[1:]:
        if cut - distinct[-1] > 1e-8:
            distinct.append(cut)
    return distinct


def score(raw_input: float, demands, shares, stations: tuple[Workstation, ...]):
    expected, _mass = expected_profit_two_grades(
        raw_input,
        demands,
        shares,
        stations,
        PRICES,
        MATERIAL_COST,
        MANUFACTURING_COSTS,
        HOLDING_COST_PER_DAY,
        STORAGE_DAYS,
        2,
    )
    counts = []
    for load, station in zip(workloads(raw_input, stations), stations):
        count = machines_required(load, station)
        if count is None:
            return expected, 0.0, None
        counts.append(count)
    required = tuple(counts)
    return expected, reliability_from_machines(required, stations), required


def nearest(raw_input: float, onset: float, policy_ii: float, policy_i: float) -> str:
    named = (
        ("grade-1 filled", onset),
        ("Policy II", policy_ii),
        ("Policy I", policy_i),
    )
    label, distance = min(
        ((name, abs(raw_input - point)) for name, point in named),
        key=lambda item: item[1],
    )
    if distance < 0.05:
        return label
    return "other"


def peaks(stations: tuple[Workstation, ...], shares: tuple[float, float]):
    limit = ceiling(stations)
    theta = throughput(stations)
    found = []
    for demand_pair, *_rest in POLICY_I_ROWS:
        demands = (float(demand_pair[0]), float(demand_pair[1]))
        onset = demands[0] / (theta * shares[0])
        policy_ii = required_input(demands, shares, stations, 2)
        policy_i = required_input(demands, shares, stations, 1)
        points = [right - 1e-4 for right in boundaries(stations, limit - 1e-6)[1:]]
        for extra in (onset, policy_ii, policy_i):
            if 0.0 < extra < limit:
                points.append(extra)
        best_input = points[0]
        best_expected, best_r, best_machines = score(best_input, demands, shares, stations)
        for raw_input in points[1:]:
            expected, reliability, machines = score(raw_input, demands, shares, stations)
            if expected > best_expected:
                best_input = raw_input
                best_expected = expected
                best_r = reliability
                best_machines = machines
        kind = nearest(best_input, onset, policy_ii, policy_i)
        found.append((demand_pair, kind, best_input, best_expected, best_r, best_machines))
    return found


def main() -> None:
    shares = (float(MANUSCRIPT_SHARES[0]), float(MANUSCRIPT_SHARES[1]))
    base_stations, _clamped = scaled(1.0)
    print(f"states = {8 * 7 * 8 * 9 * 7}")
    started = time.perf_counter()
    base = peaks(base_stations, shares)
    base_elapsed = time.perf_counter() - started
    base_counts: dict[str, int] = {}
    for _demand, kind, *_rest in base:
        base_counts[kind] = base_counts.get(kind, 0) + 1
    print(
        "manuscript yields"
        f"  grade-1 filled {base_counts.get('grade-1 filled', 0)}"
        f"  Policy I {base_counts.get('Policy I', 0)}"
        f"  Policy II {base_counts.get('Policy II', 0)}"
        f"  other {base_counts.get('other', 0)}"
        f"  elapsed {base_elapsed:.1f}s"
    )
    for factor in (0.95, 1.05):
        stations, clamped = scaled(factor)
        shown = ", ".join(f"{station.yield_rate:.6f}" for station in stations)
        print(f"factor {factor:.2f}  yields ({shown})  clamped {clamped or 'none'}")
        started = time.perf_counter()
        shifted = peaks(stations, shares)
        elapsed = time.perf_counter() - started
        flips = 0
        for before, after in zip(base, shifted):
            demand, kind, raw_input, expected, reliability, machines = after
            if kind != before[1]:
                flips += 1
                print(
                    f"  D {demand}  {before[1]} -> {kind}"
                    f"  input {raw_input:.4f}  E {expected:.2f}"
                    f"  R {reliability:.6f}  machines {machines}"
                )
        print(f"  flips {flips} of {len(base)}   elapsed {elapsed:.1f}s")


if __name__ == "__main__":
    main()
