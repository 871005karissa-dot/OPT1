"""Round 19: time enumeration at the documented state counts, then past them.

Station tables stay as written. A larger visit count repeats the delivered-profit
body of one ball-screw evaluation, or adds a rectangular probability product.
Neither product is a new line.
"""

from __future__ import annotations

import time
import tracemalloc
from itertools import product

from backbone.ball_screw import (
    DEMAND,
    HOLDING_COST_PER_DAY,
    MANUFACTURING_COSTS,
    MANUSCRIPT_SHARES,
    MATERIAL_COST,
    PRICES,
    STATIONS as BALL,
    STORAGE_DAYS,
)
from backbone.evaluator import (
    capacity_state_count,
    expected_profit_two_grades,
    reliability_by_enumeration,
    throughput,
)
from backbone.jumper import STATIONS as JUMPER


def probability_product(width: int, axes: int) -> tuple[int, float, float, int]:
    states = width ** axes
    pmf = (1.0 / width,) * width
    ranges = (range(width),) * axes
    tracemalloc.start()
    started = time.perf_counter()
    total = 0.0
    for state in product(*ranges):
        probability = 1.0
        for index in state:
            probability *= pmf[index]
        total += probability
    elapsed = time.perf_counter() - started
    _current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return states, elapsed, total, peak


def one_expected(raw_input: float) -> tuple[float, float]:
    demands = (float(DEMAND[0]), float(DEMAND[1]))
    shares = (float(MANUSCRIPT_SHARES[0]), float(MANUSCRIPT_SHARES[1]))
    return expected_profit_two_grades(
        raw_input,
        demands,
        shares,
        BALL,
        PRICES,
        MATERIAL_COST,
        MANUFACTURING_COSTS,
        HOLDING_COST_PER_DAY,
        STORAGE_DAYS,
        2,
    )


def main() -> None:
    ball_states = capacity_state_count(BALL)
    jumper_states = capacity_state_count(JUMPER)
    print(f"ball-screw states = {ball_states}   jumper states = {jumper_states}")
    for label, stations in (("ball-screw", BALL), ("jumper", JUMPER)):
        required = tuple(0 for _ in stations)
        tracemalloc.start()
        started = time.perf_counter()
        total = reliability_by_enumeration(required, stations)
        elapsed = time.perf_counter() - started
        _current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print(
            f"  {label} probability sum {total:.6f}"
            f"  {elapsed:.4f}s  peak {peak} bytes"
        )

    onset = DEMAND[0] / (throughput(BALL) * MANUSCRIPT_SHARES[0])
    tracemalloc.start()
    started = time.perf_counter()
    expected, mass = one_expected(onset)
    one_elapsed = time.perf_counter() - started
    _current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(
        f"one delivered-profit sweep at input {onset:.4f}:"
        f" E {expected:.2f}  mass {mass:.6f}"
        f"  {one_elapsed:.2f}s  peak {peak} bytes"
    )
    for repeats, label in ((4, "1e5 visits"), (36, "1e6 visits")):
        visits = repeats * ball_states
        started = time.perf_counter()
        for _ in range(repeats):
            one_expected(onset)
        elapsed = time.perf_counter() - started
        print(
            f"  {label}: {visits} visits in {elapsed:.2f}s"
            f"  ({elapsed / visits * 1e6:.2f} us/visit)"
        )
    for width, axes in ((10, 5), (10, 6)):
        states, elapsed, total, peak = probability_product(width, axes)
        print(
            f"rectangular probability product {states} states"
            f"  sum {total:.6f}  {elapsed:.2f}s  peak {peak} bytes"
        )


if __name__ == "__main__":
    main()
