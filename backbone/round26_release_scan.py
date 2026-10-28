"""Round 26: choose the release quantity for the state-dependent rule.

Round 25 locked the release at the manuscript inputs. Here the release moves
from the smaller policy input up to the feasible ceiling. Surplus grade 2
appears only above the grade-2 onset. The state rule itself is unchanged.
"""

from __future__ import annotations

import time

from backbone.ball_screw import DEMAND, STATIONS
from backbone.evaluator import line_yield
from backbone.round11_expected_profit import breakpoints, feasible_limit
from backbone.round2_share_consistency import POLICY_I_ROWS
from backbone.round25_state_policy import Q1, Q2, release, sweep

SHARES_THROUGHPUT = line_yield(STATIONS)


def samples(demands: tuple[float, float], ceiling: float) -> list[float]:
    low = min(release(demands, 1), release(demands, 2))
    high = min(max(release(demands, 1), release(demands, 2), ceiling - 1e-4), ceiling - 1e-4)
    if high <= low:
        high = min(ceiling - 1e-4, low + 1.0)
    points = []
    for left, right in zip(breakpoints(low, high), breakpoints(low, high)[1:]):
        points.append(right - 1e-4 if right - left > 1e-3 else (left + right) / 2.0)
    for demand, share in ((demands[0], Q1), (demands[1], Q2)):
        onset = demand / (SHARES_THROUGHPUT * share)
        if low < onset < high:
            points.append(onset)
    points.append(low)
    points.sort()
    merged = [points[0]]
    for point in points[1:]:
        if point - merged[-1] > 1e-3:
            merged.append(point)
    return merged


def main() -> None:
    ceiling = feasible_limit()
    print(f"feasible ceiling {ceiling:.4f}   states {8 * 7 * 8 * 9 * 7}")
    headline = (float(DEMAND[0]), float(DEMAND[1]))
    print(f"D = {headline[0]:.0f},{headline[1]:.0f}")
    print(f"{'input':>10} {'sent':>8} {'same met':>10} {'state met':>10} {'E same':>10} {'E state':>10}")
    started = time.perf_counter()
    base = sweep(release(headline, 1), headline)
    base_met = base["same_met"]
    base_profit = base["same_profit"]
    print(
        f"Policy I same-grade reference  met {base_met:.6f}  E {base_profit:.2f}"
        f"  at input {release(headline, 1):.4f}"
    )
    best = None
    for raw_input in samples(headline, ceiling):
        result = sweep(raw_input, headline)
        print(
            f"{raw_input:10.4f} {result['expected_sent']:8.2f}"
            f" {result['same_met']:10.6f} {result['state_met']:10.6f}"
            f" {result['same_profit']:10.2f} {result['state_profit']:10.2f}"
        )
        if best is None or result["state_profit"] > best[0]:
            best = (result["state_profit"], result["state_met"], result["expected_sent"], raw_input)
    print(
        f"highest state profit {best[0]:.2f}  met {best[1]:.6f}"
        f"  sent {best[2]:.2f}  input {best[3]:.4f}"
    )
    print(f"headline elapsed {time.perf_counter() - started:.1f}s")
    print()
    both = 0
    profit_only = 0
    for demand, *_rest in POLICY_I_ROWS:
        demands = (float(demand[0]), float(demand[1]))
        reference = sweep(release(demands, 1), demands)
        ref_met = reference["same_met"]
        ref_profit = reference["same_profit"]
        winner = None
        for raw_input in samples(demands, ceiling):
            result = sweep(raw_input, demands)
            if winner is None or result["state_profit"] > winner["state_profit"]:
                winner = result
                winner["input"] = raw_input
        met_up = winner["state_met"] > ref_met + 1e-6
        profit_up = winner["state_profit"] > ref_profit + 1e-2
        if met_up and profit_up:
            both += 1
            mark = "both"
        elif profit_up:
            profit_only += 1
            mark = "profit"
        else:
            mark = "neither"
        print(
            f"{demand[0]:4},{demand[1]:<4}  {mark:7}"
            f"  ref met {ref_met:.6f} E {ref_profit:10.2f}"
            f"  best input {winner['input']:.4f}"
            f"  met {winner['state_met']:.6f} E {winner['state_profit']:10.2f}"
            f"  sent {winner['expected_sent']:.2f}"
        )
    print(f"orders with both higher: {both}   profit only: {profit_only} of {len(POLICY_I_ROWS)}")


if __name__ == "__main__":
    main()
