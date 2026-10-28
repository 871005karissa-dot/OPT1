"""Round 25: decide substitution and grade-2 rework after the capacity state.

Grade 2 is kept for the grade-2 order. Only the surplus returns to station 2,
and only what that station's remaining capacity can take. A fraction equal to
station 2's yield joins grade 1. Grade 1 fills a grade-2 gap only when grade 2
itself is short. The evaluator's fixed policies are not changed.
"""

from __future__ import annotations

import time

from backbone.ball_screw import (
    DEMAND,
    HOLDING_COST_PER_DAY,
    MANUFACTURING_COSTS,
    MANUSCRIPT_SHARES,
    MATERIAL_COST,
    PRICES,
    STATIONS,
    STORAGE_DAYS,
)
from backbone.evaluator import (
    binomial_pmf,
    expected_profit_two_grades,
    machines_required,
    reliability_from_machines,
    required_input,
    workloads,
)
from backbone.round2_share_consistency import POLICY_I_ROWS

Q1 = float(MANUSCRIPT_SHARES[0])
Q2 = float(MANUSCRIPT_SHARES[1])
YIELDS = tuple(station.yield_rate for station in STATIONS)
CAPACITIES = tuple(station.machine_capacity for station in STATIONS)
COUNTS = tuple(station.machine_count for station in STATIONS)
PMFS = tuple(binomial_pmf(station.machine_count, station.availability) for station in STATIONS)
UPGRADE = YIELDS[1]
PRICE_GAP = PRICES[0] - PRICES[1]
HOLD = HOLDING_COST_PER_DAY * STORAGE_DAYS


def release(demands, policy: int) -> float:
    return required_input(demands, (Q1, Q2), STATIONS, policy)


def load_reliability(raw_input: float) -> tuple[tuple[int, ...] | None, float]:
    loads = workloads(raw_input, STATIONS)
    required = []
    for load, station in zip(loads, STATIONS):
        count = machines_required(load, station)
        if count is None:
            return None, 0.0
        required.append(count)
    machines = tuple(required)
    return machines, reliability_from_machines(machines, STATIONS)


def sweep(raw_input: float, demands: tuple[float, float]):
    """One pass over 28224 states for the fixed policies and the state policy."""
    demand1, demand2 = demands
    same_profit = 0.0
    substitute_profit = 0.0
    state_profit = 0.0
    same_met = 0.0
    state_met = 0.0
    expected_sent = 0.0
    mass = 0.0
    ranges = [range(count + 1) for count in COUNTS]
    for n0 in ranges[0]:
        p0 = PMFS[0][n0]
        cap0 = n0 * CAPACITIES[0]
        for n1 in ranges[1]:
            p1 = p0 * PMFS[1][n1]
            cap1 = n1 * CAPACITIES[1]
            for n2 in ranges[2]:
                p2 = p1 * PMFS[2][n2]
                cap2 = n2 * CAPACITIES[2]
                for n3 in ranges[3]:
                    p3 = p2 * PMFS[3][n3]
                    cap3 = n3 * CAPACITIES[3]
                    for n4 in ranges[4]:
                        probability = p3 * PMFS[4][n4]
                        cap4 = n4 * CAPACITIES[4]
                        incoming = raw_input
                        load0 = incoming if incoming < cap0 else cap0
                        incoming = load0 * YIELDS[0]
                        load1 = incoming if incoming < cap1 else cap1
                        incoming = load1 * YIELDS[1]
                        load2 = incoming if incoming < cap2 else cap2
                        incoming = load2 * YIELDS[2]
                        load3 = incoming if incoming < cap3 else cap3
                        incoming = load3 * YIELDS[3]
                        load4 = incoming if incoming < cap4 else cap4
                        finished = load4 * YIELDS[4]
                        made1 = finished * Q1
                        made2 = finished * Q2
                        base_cost = (
                            load0 * MATERIAL_COST
                            + load0 * MANUFACTURING_COSTS[0]
                            + load1 * MANUFACTURING_COSTS[1]
                            + load2 * MANUFACTURING_COSTS[2]
                            + load3 * MANUFACTURING_COSTS[3]
                            + load4 * MANUFACTURING_COSTS[4]
                        )

                        sold1 = made1 if made1 < demand1 else demand1
                        sold2 = made2 if made2 < demand2 else demand2
                        excess1 = made1 - demand1
                        excess2 = made2 - demand2
                        held = (excess1 if excess1 > 0.0 else 0.0) + (excess2 if excess2 > 0.0 else 0.0)
                        same = (
                            sold1 * PRICES[0]
                            + sold2 * PRICES[1]
                            + (excess1 * PRICES[0] if excess1 > 0.0 else 0.0)
                            + (excess2 * PRICES[1] if excess2 > 0.0 else 0.0)
                            - base_cost
                            - held * HOLD
                        )

                        left1 = made1 - demand1
                        short2 = demand2 - made2
                        usable1 = left1 if left1 > 0.0 else 0.0
                        need2 = short2 if short2 > 0.0 else 0.0
                        substituted = usable1 if usable1 < need2 else need2
                        sub_excess1 = left1 - substituted
                        sub_excess2 = made2 - demand2 + substituted
                        sub_sold2 = demand2 if made2 + substituted > demand2 else made2 + substituted
                        sub_held = (sub_excess1 if sub_excess1 > 0.0 else 0.0) + (
                            sub_excess2 if sub_excess2 > 0.0 else 0.0
                        )
                        substitute = (
                            sold1 * PRICES[0]
                            + sub_sold2 * PRICES[1]
                            + (sub_excess1 * PRICES[0] if sub_excess1 > 0.0 else 0.0)
                            + (sub_excess2 * PRICES[1] if sub_excess2 > 0.0 else 0.0)
                            - base_cost
                            - sub_held * HOLD
                            - substituted * PRICE_GAP
                        )

                        keep2 = made2 if made2 < demand2 else demand2
                        unused2 = made2 - keep2
                        remain1 = cap1 - load1
                        if remain1 < 0.0:
                            remain1 = 0.0
                        sent = unused2 if unused2 < remain1 else remain1
                        upgraded = sent * UPGRADE
                        pool1 = made1 + upgraded
                        stay2 = made2 - sent
                        ship1 = pool1 if pool1 < demand1 else demand1
                        left_after = pool1 - ship1
                        still_short = demand2 - keep2
                        if still_short < 0.0:
                            still_short = 0.0
                        moved = left_after if left_after < still_short else still_short
                        ship2 = keep2 + moved
                        extra1 = left_after - moved
                        extra2 = stay2 - keep2
                        state_held = (extra1 if extra1 > 0.0 else 0.0) + (extra2 if extra2 > 0.0 else 0.0)
                        state = (
                            ship1 * PRICES[0]
                            + ship2 * PRICES[1]
                            + extra1 * PRICES[0]
                            + (extra2 * PRICES[1] if extra2 > 0.0 else 0.0)
                            - base_cost
                            - sent * MANUFACTURING_COSTS[1]
                            - state_held * HOLD
                            - moved * PRICE_GAP
                        )

                        same_profit += probability * same
                        substitute_profit += probability * substitute
                        state_profit += probability * state
                        if sold1 >= demand1 - 1e-6 and sold2 >= demand2 - 1e-6:
                            same_met += probability
                        if ship1 >= demand1 - 1e-6 and ship2 >= demand2 - 1e-6:
                            state_met += probability
                        expected_sent += probability * sent
                        mass += probability
    return {
        "mass": mass,
        "same_profit": same_profit,
        "substitute_profit": substitute_profit,
        "state_profit": state_profit,
        "same_met": same_met,
        "state_met": state_met,
        "expected_sent": expected_sent,
    }


def show(label: str, demands, raw_input: float, result: dict, elapsed: float) -> None:
    machines, load_reliability_value = load_reliability(raw_input)
    print(
        f"{label} {demands[0]:.0f},{demands[1]:.0f}"
        f"  input {raw_input:.4f}  machines {machines}"
        f"  {elapsed:.2f}s"
    )
    print(
        f"  load R {load_reliability_value:.6f}"
        f"  same-grade met {result['same_met']:.6f}"
        f"  state met {result['state_met']:.6f}"
        f"  E[sent] {result['expected_sent']:.4f}"
    )
    print(
        f"  E same {result['same_profit']:.2f}"
        f"  E substitute {result['substitute_profit']:.2f}"
        f"  E state {result['state_profit']:.2f}"
    )


def main() -> None:
    print(f"upgrade yield {UPGRADE:.2f}   storage {STORAGE_DAYS:.0f}   states {8 * 7 * 8 * 9 * 7}")
    headline = (float(DEMAND[0]), float(DEMAND[1]))
    check_input = release(headline, 1)
    started = time.perf_counter()
    reference = expected_profit_two_grades(
        check_input,
        headline,
        (Q1, Q2),
        STATIONS,
        PRICES,
        MATERIAL_COST,
        MANUFACTURING_COSTS,
        HOLDING_COST_PER_DAY,
        STORAGE_DAYS,
        1,
    )
    result = sweep(check_input, headline)
    print(
        f"check Policy I expected profit {reference[0]:.2f}"
        f"  sweep same-grade {result['same_profit']:.2f}"
        f"  mass {result['mass']:.6f}"
        f"  {(time.perf_counter() - started):.2f}s"
    )
    print()
    for policy, name in ((1, "Policy I input"), (2, "Policy II input")):
        raw_input = release(headline, policy)
        started = time.perf_counter()
        result = sweep(raw_input, headline)
        show(name, headline, raw_input, result, time.perf_counter() - started)
    print()
    higher_met = 0
    higher_profit = 0
    sent_orders = 0
    for demand, *_rest in POLICY_I_ROWS:
        demands = (float(demand[0]), float(demand[1]))
        raw_input = release(demands, 1)
        started = time.perf_counter()
        result = sweep(raw_input, demands)
        show("I-input", demands, raw_input, result, time.perf_counter() - started)
        if result["state_met"] > result["same_met"] + 1e-6:
            higher_met += 1
        if result["state_profit"] > result["same_profit"] + 1e-2:
            higher_profit += 1
        if result["expected_sent"] > 1e-4:
            sent_orders += 1
    print()
    print(
        f"of {len(POLICY_I_ROWS)} orders at the Policy I input:"
        f"  state meets more often {higher_met}"
        f"  state profit higher {higher_profit}"
        f"  expected send positive {sent_orders}"
    )


if __name__ == "__main__":
    main()
