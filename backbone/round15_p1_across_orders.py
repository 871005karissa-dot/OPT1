"""Round 15: P1 on every published order, storage 30 days.

Same expected-profit function as round 14. The comparison is the 30-day
classification from round 12, which had rework off.
"""

from __future__ import annotations

import time

from backbone.ball_screw import MANUSCRIPT_SHARES, STATIONS
from backbone.evaluator import required_input, throughput
from backbone.round2_share_consistency import POLICY_I_ROWS
from backbone.round12_expected_across_orders import nearest
from backbone.round13_storage_days import AT_30_DAYS
from backbone.round14_expected_p1 import P1, breakpoints, ceiling, score


def main() -> None:
    shares = (float(MANUSCRIPT_SHARES[0]), float(MANUSCRIPT_SHARES[1]))
    limit = ceiling(P1)
    print(f"P1 ceiling {limit:.4f}   states = {8 * 7 * 8 * 9 * 7}")
    started = time.perf_counter()
    flips = 0
    for demand_pair, *_rest in POLICY_I_ROWS:
        demands = (float(demand_pair[0]), float(demand_pair[1]))
        onset = demands[0] / (throughput(STATIONS, P1) * shares[0])
        policy_ii = required_input(demands, shares, STATIONS, 2, P1)
        policy_i = required_input(demands, shares, STATIONS, 1, P1)
        points = [right - 1e-4 for right in breakpoints(limit - 1e-6, P1)[1:]]
        for extra in (onset, policy_ii, policy_i):
            if 0.0 < extra < limit:
                points.append(extra)
        best = None
        for raw_input in points:
            expected, reliability, counts, _mass = score(raw_input, demands, shares, P1)
            if best is None or expected > best[0]:
                best = (expected, raw_input, reliability, counts)
        expected, raw_input, reliability, counts = best
        kind = nearest(raw_input, onset, policy_ii, policy_i)
        previous = AT_30_DAYS[demand_pair]
        moved = previous != kind
        flips += int(moved)
        mark = f"  {previous} -> {kind}" if moved else f"  {kind}"
        print(
            f"  D {demand_pair}{mark}"
            f"  input {raw_input:.4f}  E {expected:.2f}"
            f"  R {reliability:.6f}  machines {counts}"
        )
    elapsed = time.perf_counter() - started
    print(f"flips from rework off: {flips} of {len(POLICY_I_ROWS)}   elapsed {elapsed:.1f}s")


if __name__ == "__main__":
    main()
