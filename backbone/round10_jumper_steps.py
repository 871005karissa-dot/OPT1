"""Round 10: count reliability steps on the jumper line.

Rework off, P2 alone, and P2 plus P3. Each step is one machine vector.
The full capacity-state sum checks that enumeration still finishes.
"""

from __future__ import annotations

import time

from backbone.evaluator import (
    ReworkPath,
    machines_required,
    reliability_by_enumeration,
    workloads,
)
from backbone.jumper import SCRAP_RATE, STATIONS

P2 = ReworkPath(5, 6, 1)
P3 = ReworkPath(2, 6, 1)


def steps(path) -> tuple[float, int]:
    scrap = None if path is None else SCRAP_RATE
    unit = workloads(1.0, STATIONS, path, scrap)
    limit = min(station.max_capacity / load for station, load in zip(STATIONS, unit))
    cuts = [0.0, limit]
    for unit_load, station in zip(unit, STATIONS):
        if unit_load <= 0.0:
            continue
        for machines in range(1, station.machine_count + 1):
            cut = machines * station.machine_capacity / unit_load
            if 0.0 < cut < limit:
                cuts.append(cut)
    cuts.sort()
    distinct = []
    for left, right in zip(cuts, cuts[1:]):
        if right - left < 1e-8:
            continue
        sample = (left + right) / 2.0
        loads = workloads(sample, STATIONS, path, scrap)
        counts = tuple(
            machines_required(load, station) for load, station in zip(loads, STATIONS)
        )
        if not distinct or distinct[-1] != counts:
            distinct.append(counts)
    return limit, len(distinct)


def main() -> None:
    zeros = tuple(0 for _station in STATIONS)
    started = time.perf_counter()
    total = reliability_by_enumeration(zeros, STATIONS)
    elapsed = time.perf_counter() - started
    print(f"full state sum {total:.6f}   {elapsed:.4f} s")
    for label, path in (("off", None), ("P2", P2), ("P2+P3", (P2, P3))):
        limit, count = steps(path)
        print(f"  {label}: ceiling {limit:.4f}   reliability steps {count}")


if __name__ == "__main__":
    main()
