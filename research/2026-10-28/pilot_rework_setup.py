"""Exploratory setup-cost ablation of Round 25, using its existing accounting.

This is not a new calibrated case or a globally optimal production policy.
Forward production, grade-2 reservation, and downward substitution stay fixed.
Only the decision to activate the surplus-upgrade batch is varied by state.
Setup costs are illustrative USD per activated batch, not empirical estimates.
"""

from itertools import product
from pathlib import Path
from datetime import datetime, timezone
from hashlib import sha256
import json
import math
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backbone.ball_screw import (  # noqa: E402
    HOLDING_COST_PER_DAY, MANUFACTURING_COSTS, MATERIAL_COST, PRICES,
    STATIONS, STORAGE_DAYS,
)
from backbone.evaluator import profit_from_flow, realized_series_flow  # noqa: E402
from backbone.round2_share_consistency import POLICY_I_ROWS  # noqa: E402
from backbone.round25_state_policy import (  # noqa: E402
    CAPACITIES, COUNTS, PMFS, Q1, Q2, UPGRADE, release, sweep,
)


SETUP_COSTS = (0.0, 250.0, 1000.0, 3000.0, 10000.0)


def account(grades, loads, demands):
    return profit_from_flow(
        grades, loads, demands, PRICES, MATERIAL_COST, MANUFACTURING_COSTS,
        HOLDING_COST_PER_DAY, STORAGE_DAYS, 2, revenue_on_delivered=True,
    )


def met(grades, demands):
    sold1 = min(grades[0], demands[0])
    moved = min(max(grades[0] - demands[0], 0.0), max(demands[1] - grades[1], 0.0))
    sold2 = min(grades[1] + moved, demands[1])
    return sold1 >= demands[0] - 1e-6 and sold2 >= demands[1] - 1e-6


def run(demands):
    raw_input = release(demands, 1)
    records = [{"setup_cost": cost, "expected_profit": 0.0, "fulfilment_probability": 0.0,
                "activation_probability": 0.0, "expected_rework": 0.0} for cost in SETUP_COSTS]
    baseline_profit = baseline_met = mass = potential = 0.0
    negative_gross_gain_states = 0
    for state in product(*(range(count + 1) for count in COUNTS)):
        probability = math.prod(PMFS[i][n] for i, n in enumerate(state))
        capacities = tuple(n * CAPACITIES[i] for i, n in enumerate(state))
        loads, finished = realized_series_flow(raw_input, capacities, STATIONS)
        grades = (finished * Q1, finished * Q2)
        baseline = account(grades, loads, demands).profit
        baseline_success = met(grades, demands)
        sent = min(max(grades[1] - demands[1], 0.0), max(capacities[1] - loads[1], 0.0))
        modified = list(loads)
        modified[1] += sent
        upgraded_grades = (grades[0] + UPGRADE * sent, grades[1] - sent)
        upgraded = account(upgraded_grades, tuple(modified), demands).profit
        upgraded_success = met(upgraded_grades, demands)
        gain = upgraded - baseline
        if sent > 1e-8:
            potential += probability
            negative_gross_gain_states += gain < -1e-8
        for record in records:
            activate = sent > 1e-8 and gain > record["setup_cost"]
            value = upgraded - record["setup_cost"] if activate else baseline
            success = upgraded_success if activate else baseline_success
            record["expected_profit"] += probability * value
            record["fulfilment_probability"] += probability * success
            record["activation_probability"] += probability * activate
            record["expected_rework"] += probability * (sent if activate else 0.0)
        baseline_profit += probability * baseline
        baseline_met += probability * baseline_success
        mass += probability
    reference = sweep(raw_input, demands)
    assert abs(mass - 1.0) < 1e-10
    assert abs(reference["substitute_profit"] - baseline_profit) < 1e-6
    assert abs(reference["state_profit"] - records[0]["expected_profit"]) < 1e-6
    assert abs(reference["state_met"] - records[0]["fulfilment_probability"]) < 1e-10
    assert abs(reference["expected_sent"] - records[0]["expected_rework"]) < 1e-6
    assert negative_gross_gain_states == 0
    return {"demands": demands, "release": raw_input, "mass": mass,
            "no_upgrade_expected_profit": baseline_profit,
            "no_upgrade_fulfilment_probability": baseline_met,
            "potential_activation_probability": potential,
            "negative_gross_gain_states": negative_gross_gain_states, "results": records}


def main():
    holding = HOLDING_COST_PER_DAY * STORAGE_DAYS
    slopes = {
        "upgrade_fills_grade1_shortage": UPGRADE * PRICES[0] - (PRICES[1] - holding) - MANUFACTURING_COSTS[1],
        "upgrade_becomes_grade1_surplus": UPGRADE * (PRICES[0] - holding) - (PRICES[1] - holding) - MANUFACTURING_COSTS[1],
    }
    orders = [run(tuple(map(float, row[0]))) for row in POLICY_I_ROWS]
    project = Path(__file__).resolve().parents[2]
    dependencies = ("backbone/ball_screw.py", "backbone/evaluator.py",
                    "backbone/round2_share_consistency.py", "backbone/round25_state_policy.py")
    payload = {"scope": __doc__, "setup_costs_are_hypothetical": True,
               "run_at_utc": datetime.now(timezone.utc).isoformat(), "python_version": sys.version,
               "source_sha256": {name: sha256((project / name).read_bytes()).hexdigest() for name in dependencies},
               "pilot_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
               "upgrade_yield": UPGRADE, "holding_per_unit": holding,
               "marginal_gain_per_rework_input": slopes, "orders": orders}
    target = Path(__file__).with_name("pilot_rework_setup_results.json")
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"slopes": slopes, "orders_checked": len(orders),
                      "reference_checks": "All 15 orders reproduce Round 25 at setup cost zero"}))
    for order in orders:
        if order["demands"] in ((550.0, 350.0), (650.0, 250.0), (700.0, 200.0), (750.0, 150.0)):
            for record in order["results"]:
                if record["setup_cost"] in (0.0, 1000.0, 3000.0):
                    print(f"order={order['demands']} F={record['setup_cost']:.0f} "
                          f"profit={record['expected_profit']:.2f} "
                          f"met={record['fulfilment_probability']:.6f} "
                          f"activate={record['activation_probability']:.6f}")


if __name__ == "__main__":
    main()
