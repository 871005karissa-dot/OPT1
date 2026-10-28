"""Round 13: whether Table 9's storage days move the expected-profit peak.

Same scorer as round 12. Only the holding period changes, to the ends of
Table 9: 15 days and 75 days.
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
from backbone.evaluator import expected_profit_two_grades, reliability_from_machines, required_input, throughput
from backbone.round2_share_consistency import POLICY_I_ROWS
from backbone.round11_expected_profit import breakpoints, feasible_limit, machine_counts
from backbone.round12_expected_across_orders import nearest

# Kind of the 30-day peak from round 12.
AT_30_DAYS = {
    (400, 500): "grade-1 filled",
    (450, 450): "grade-1 filled",
    (500, 400): "grade-1 filled",
    (500, 300): "Policy I",
    (400, 400): "grade-1 filled",
    (550, 350): "grade-1 filled",
    (600, 300): "Policy I",
    (650, 250): "grade-1 filled",
    (700, 200): "grade-1 filled",
    (750, 150): "grade-1 filled",
    (750, 337): "grade-1 filled",
    (750, 338): "grade-1 filled",
    (750, 339): "grade-1 filled",
    (750, 352): "grade-1 filled",
    (750, 353): "grade-1 filled",
}


def score(raw_input: float, demands: tuple[float, float], shares: tuple[float, float], storage_days: float):
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
    )
    counts = machine_counts(raw_input)
    reliability = 0.0 if counts is None else reliability_from_machines(counts, STATIONS)
    return expected, reliability, counts


def best_for(demands: tuple[float, float], shares: tuple[float, float], storage_days: float, ceiling: float, theta: float):
    onset = demands[0] / (theta * shares[0])
    policy_ii = required_input(demands, shares, STATIONS, 2)
    policy_i = required_input(demands, shares, STATIONS, 1)
    points = [right - 1e-4 for right in breakpoints(0.0, ceiling - 1e-6)[1:]]
    for extra in (onset, policy_ii, policy_i):
        if 0.0 < extra < ceiling:
            points.append(extra)
    best_input = None
    best_expected = None
    best_r = None
    for raw_input in points:
        expected, reliability, _machines = score(raw_input, demands, shares, storage_days)
        if best_expected is None or expected > best_expected:
            best_input = raw_input
            best_expected = expected
            best_r = reliability
    kind = nearest(best_input, onset, policy_ii, policy_i)
    return best_input, best_expected, best_r, kind


def main() -> None:
    shares = (float(MANUSCRIPT_SHARES[0]), float(MANUSCRIPT_SHARES[1]))
    ceiling = feasible_limit()
    theta = throughput(STATIONS)
    for storage_days in (15.0, 75.0):
        print(f"storage {storage_days:.0f} days")
        started = time.perf_counter()
        flips = 0
        for demand_pair, *_rest in POLICY_I_ROWS:
            demands = (float(demand_pair[0]), float(demand_pair[1]))
            best_input, best_expected, best_r, kind = best_for(demands, shares, storage_days, ceiling, theta)
            previous = AT_30_DAYS[demand_pair]
            moved = previous != kind
            flips += int(moved)
            if moved:
                print(
                    f"  D {demand_pair}  {previous} -> {kind}"
                    f"  input {best_input:.4f}  E {best_expected:.2f}  R {best_r:.6f}"
                )
        elapsed = time.perf_counter() - started
        print(f"  flips from 30 days: {flips} of {len(POLICY_I_ROWS)}   elapsed {elapsed:.1f}s")


if __name__ == "__main__":
    main()
