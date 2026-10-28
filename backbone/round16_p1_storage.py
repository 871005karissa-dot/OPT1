"""Round 16: P1 at the two storage periods in Table 9.

Same expected profit as round 14. Rework off is scored again so the comparison
does not depend on a copied label. Only a changed peak kind is printed, plus
D = (550, 350) at both settings.
"""

from __future__ import annotations

import time

from backbone.ball_screw import (
    MANUFACTURING_COSTS,
    MANUSCRIPT_SHARES,
    MATERIAL_COST,
    PRICES,
    STATIONS,
)
from backbone.evaluator import (
    expected_profit_two_grades,
    reliability_from_machines,
    required_input,
    throughput,
)
from backbone.round2_share_consistency import POLICY_I_ROWS
from backbone.round12_expected_across_orders import nearest
from backbone.round14_expected_p1 import P1, breakpoints, ceiling, machine_counts


def score(raw_input: float, demands, shares, storage_days: float, rework):
    expected, _mass = expected_profit_two_grades(
        raw_input,
        demands,
        shares,
        STATIONS,
        PRICES,
        MATERIAL_COST,
        MANUFACTURING_COSTS,
        1.0,
        storage_days,
        2,
        rework,
    )
    counts = machine_counts(raw_input, rework)
    reliability = 0.0 if counts is None else reliability_from_machines(counts, STATIONS)
    return expected, reliability, counts


def peak(demands, shares, storage_days: float, rework):
    limit = ceiling(rework)
    onset = demands[0] / (throughput(STATIONS, rework) * shares[0])
    policy_ii = required_input(demands, shares, STATIONS, 2, rework)
    policy_i = required_input(demands, shares, STATIONS, 1, rework)
    points = [right - 1e-4 for right in breakpoints(limit - 1e-6, rework)[1:]]
    for extra in (onset, policy_ii, policy_i):
        if 0.0 < extra < limit:
            points.append(extra)
    best = None
    for raw_input in points:
        expected, reliability, counts = score(raw_input, demands, shares, storage_days, rework)
        if best is None or expected > best[0]:
            best = (expected, raw_input, reliability, counts)
    expected, raw_input, reliability, counts = best
    kind = nearest(raw_input, onset, policy_ii, policy_i)
    return raw_input, expected, reliability, counts, kind


def main() -> None:
    shares = (float(MANUSCRIPT_SHARES[0]), float(MANUSCRIPT_SHARES[1]))
    orders = [((float(pair[0]), float(pair[1])), pair) for pair, *_rest in POLICY_I_ROWS]
    for storage_days in (15.0, 75.0):
        print(f"storage {storage_days:.0f} days")
        started = time.perf_counter()
        flips = 0
        for demands, label in orders:
            off = peak(demands, shares, storage_days, None)
            on = peak(demands, shares, storage_days, P1)
            moved = off[4] != on[4]
            flips += int(moved)
            show = moved or label == (550, 350)
            if not show:
                continue
            print(
                f"  D {label}"
                f"  off {off[4]} input {off[0]:.4f} E {off[1]:.2f} R {off[2]:.6f} {off[3]}"
            )
            print(
                f"    P1 {on[4]} input {on[0]:.4f} E {on[1]:.2f} R {on[2]:.6f} {on[3]}"
            )
        elapsed = time.perf_counter() - started
        print(f"  kind flips when P1 turns on: {flips} of {len(orders)}   elapsed {elapsed:.1f}s")


if __name__ == "__main__":
    main()
