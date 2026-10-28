"""Round 12: where expected profit peaks on each published order.

Same function as round 11. Rework stays off. Each Table 4 demand is scored
at every machine-count boundary and at the input where grade-1 output equals
its own demand.
"""

from __future__ import annotations

import time

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
    expected_profit_two_grades,
    reliability_from_machines,
    required_input,
    throughput,
)
from backbone.round2_share_consistency import POLICY_I_ROWS
from backbone.round11_expected_profit import breakpoints, feasible_limit, machine_counts


def score(raw_input: float, demands: tuple[float, float], shares: tuple[float, float]) -> tuple[float, float, tuple[int, ...] | None]:
    expected, _mass = expected_profit_two_grades(
        raw_input,
        demands,
        shares,
        STATIONS,
        PRICES,
        MATERIAL_COST,
        MANUFACTURING_COSTS,
        HOLDING_COST_PER_DAY,
        STORAGE_DAYS,
        2,
    )
    counts = machine_counts(raw_input)
    reliability = 0.0 if counts is None else reliability_from_machines(counts, STATIONS)
    return expected, reliability, counts


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


def main() -> None:
    shares = (float(MANUSCRIPT_SHARES[0]), float(MANUSCRIPT_SHARES[1]))
    ceiling = feasible_limit()
    theta = throughput(STATIONS)
    print(f"states = {8 * 7 * 8 * 9 * 7}   feasible ceiling {ceiling:.4f}")
    started = time.perf_counter()
    counts = {"grade-1 filled": 0, "Policy I": 0, "Policy II": 0, "other": 0}
    for demand_pair, _published_input, _published_r, _excess1, _excess2 in POLICY_I_ROWS:
        demands = (float(demand_pair[0]), float(demand_pair[1]))
        onset = demands[0] / (theta * shares[0])
        policy_ii = required_input(demands, shares, STATIONS, 2)
        policy_i = required_input(demands, shares, STATIONS, 1)
        points = [right - 1e-4 for right in breakpoints(0.0, ceiling - 1e-6)[1:]]
        for extra in (onset, policy_ii, policy_i):
            if 0.0 < extra < ceiling:
                points.append(extra)
        best_input = points[0]
        best_expected, best_r, best_machines = score(best_input, demands, shares)
        for raw_input in points[1:]:
            expected, reliability, machines = score(raw_input, demands, shares)
            if expected > best_expected:
                best_input = raw_input
                best_expected = expected
                best_r = reliability
                best_machines = machines
        kind = nearest(best_input, onset, policy_ii, policy_i)
        counts[kind] += 1
        print(
            f"  D {demand_pair}"
            f"  best {best_input:10.4f}  {kind}"
            f"  E {best_expected:10.2f}"
            f"  R {best_r:.6f}"
            f"  machines {best_machines}"
            f"  onset {onset:.4f}  I {policy_i:.4f}  II {policy_ii:.4f}"
        )
    elapsed = time.perf_counter() - started
    print(
        "orders"
        f" {sum(counts.values())}"
        f"   grade-1 filled {counts['grade-1 filled']}"
        f"   Policy I {counts['Policy I']}"
        f"   Policy II {counts['Policy II']}"
        f"   other {counts['other']}"
        f"   elapsed {elapsed:.1f}s"
    )


if __name__ == "__main__":
    main()
