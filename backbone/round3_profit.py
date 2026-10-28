"""Round 3: accounting profit on the manuscript grade shares.

Same stations and the same input function as round 2. One new function,
profit_two_grades. Targets are Table 8 at 30 days and Table 9 for D = (550, 350).
"""

from __future__ import annotations

from backbone.ball_screw import (
    HOLDING_COST_PER_DAY,
    MANUFACTURING_COSTS,
    MANUSCRIPT_SHARES,
    MATERIAL_COST,
    PRICES,
    STATIONS,
    STORAGE_DAYS,
)
from backbone.evaluator import profit_two_grades, required_input

# demand, Policy I profit, Policy II profit, as printed in Table 8.
TABLE_8 = (
    ((400, 500), 24649.3842, -1352.4431),
    ((450, 450), 24884.4466, 4647.5569),
    ((500, 400), 25119.5069, 10647.5569),
    ((500, 300), 22529.6324, 16131.1614),
    ((400, 400), 21999.5069, 4131.1614),
    ((550, 350), 25354.5727, 16647.5569),
    ((600, 300), 25589.6324, 22647.5569),
    ((650, 250), 25659.0908, 25659.0908),
    ((700, 200), 25555.9417, 25555.9417),
    ((750, 150), 25452.7969, 25452.7969),
    ((750, 337), 31025.6879, 30393.2152),
    ((750, 338), 31050.9808, 30338.3835),
    ((750, 339), 31076.2858, 30283.5497),
)

# storage days, Policy I profit. Policy II stays 16647.5569.
TABLE_9 = (
    (15, 29068.7542),
    (30, 25354.5727),
    (45, 21640.3912),
    (60, 17926.2097),
    (75, 14212.0281),
)


def main() -> None:
    shares = (float(MANUSCRIPT_SHARES[0]), float(MANUSCRIPT_SHARES[1]))
    print(f"Q = ({shares[0]:.10f}, {shares[1]:.10f})")
    print("Table 8, storage = 30 days")
    worst = 0.0
    for demand, published_i, published_ii in TABLE_8:
        demands = (float(demand[0]), float(demand[1]))
        gaps = []
        for policy, published in ((1, published_i), (2, published_ii)):
            raw_input = required_input(demands, shares, STATIONS, policy)
            result = profit_two_grades(
                raw_input,
                demands,
                shares,
                STATIONS,
                PRICES,
                MATERIAL_COST,
                MANUFACTURING_COSTS,
                HOLDING_COST_PER_DAY,
                STORAGE_DAYS,
                policy,
            )
            gap = result.profit - published
            gaps.append(gap)
            worst = max(worst, abs(gap))
        print(
            f"  {demand[0]:4},{demand[1]:<4}"
            f"  dProfit I {gaps[0]:9.4f}   II {gaps[1]:9.4f}"
        )
    print(f"  worst |dProfit| {worst:.4f}")
    print()

    demand = (550.0, 350.0)
    raw_i = required_input(demand, shares, STATIONS, 1)
    raw_ii = required_input(demand, shares, STATIONS, 2)
    print("Table 9, D = (550, 350)")
    for days, published in TABLE_9:
        result = profit_two_grades(
            raw_i,
            demand,
            shares,
            STATIONS,
            PRICES,
            MATERIAL_COST,
            MANUFACTURING_COSTS,
            HOLDING_COST_PER_DAY,
            float(days),
            1,
        )
        other = profit_two_grades(
            raw_ii,
            demand,
            shares,
            STATIONS,
            PRICES,
            MATERIAL_COST,
            MANUFACTURING_COSTS,
            HOLDING_COST_PER_DAY,
            float(days),
            2,
        )
        print(
            f"  {days:2} days  Policy I {result.profit:.4f} vs {published:.4f}"
            f"  d {result.profit - published:8.4f}"
            f"  Policy II {other.profit:.4f}"
        )


if __name__ == "__main__":
    main()
