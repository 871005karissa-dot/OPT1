"""Isolated research evaluator for rounds 27 onward; the original evaluator is unchanged.

Capacity states are enumerated exactly. Quantities are fluid, grade shares are fixed,
and surplus grade 2 returns only to station 2 once. Unsuccessful returns are scrapped.
No scheduling/due-date feasibility is asserted by the aggregate workload model.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from itertools import product
from pathlib import Path
import json
import sys

import numpy as np

from backbone.ball_screw import (
    STATIONS, MANUSCRIPT_SHARES, PRICES, MATERIAL_COST, MANUFACTURING_COSTS,
)
from backbone.evaluator import binomial_pmf, required_input
from backbone.round2_share_consistency import POLICY_I_ROWS

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research" / "2026-10-28" / "six_rounds"
Q1, Q2 = map(float, MANUSCRIPT_SHARES)
COUNTS = np.array(list(product(*(range(s.machine_count + 1) for s in STATIONS))))
CAPS = COUNTS * np.array([s.machine_capacity for s in STATIONS])
PROB = np.ones(len(COUNTS))
for index, station in enumerate(STATIONS):
    PROB *= np.array(binomial_pmf(station.machine_count, station.availability))[COUNTS[:, index]]
ORDERS = [tuple(map(float, row[0])) for row in POLICY_I_ROWS]
EPS = 1e-6


@dataclass
class Flow:
    loads: np.ndarray
    finished: np.ndarray

    @property
    def g1(self):
        return self.finished * Q1

    @property
    def g2(self):
        return self.finished * Q2


def release(demands, policy=1):
    return required_input(demands, (Q1, Q2), STATIONS, policy)


def forward(raw_input, reserve_fraction=0.0):
    """Cap station-2 forward processing; unused capacity can serve returns later."""
    incoming = np.full(len(PROB), raw_input)
    loads = np.empty_like(CAPS, dtype=float)
    for index, station in enumerate(STATIONS):
        capacity = CAPS[:, index]
        if index == 1:
            capacity = capacity * (1.0 - np.asarray(reserve_fraction))
        loads[:, index] = np.minimum(incoming, capacity)
        incoming = loads[:, index] * station.yield_rate
    return Flow(loads, incoming)


def available_returns(flow, demands, setup_workload=0.0):
    return np.minimum(np.maximum(flow.g2 - demands[1], 0.0),
                      np.maximum(CAPS[:, 1] - flow.loads[:, 1] - setup_workload, 0.0))


def evaluate(flow, demands, sent=0.0, eta=0.97, allow_sub=True, ledger="cash",
             holding=30.0, setup_cost=0.0):
    """cash: actual sales plus future sales less costs; legacy adds a price-gap penalty."""
    sent = np.broadcast_to(np.asarray(sent), (len(PROB),))
    grade1 = flow.g1 + eta * sent
    grade2 = flow.g2 - sent
    substituted = np.minimum(np.maximum(grade1 - demands[0], 0.0),
                             np.maximum(demands[1] - grade2, 0.0)) if allow_sub else np.zeros(len(PROB))
    sold1 = np.minimum(grade1, demands[0])
    sold2 = np.minimum(grade2 + substituted, demands[1])
    extra1 = np.maximum(grade1 - demands[0] - substituted, 0.0)
    extra2 = np.maximum(grade2 + substituted - demands[1], 0.0)
    cost = flow.loads[:, 0] * MATERIAL_COST + np.sum(flow.loads * MANUFACTURING_COSTS, axis=1)
    profit = sold1 * PRICES[0] + sold2 * PRICES[1]
    profit += extra1 * (PRICES[0] - holding) + extra2 * (PRICES[1] - holding)
    profit -= cost + sent * MANUFACTURING_COSTS[1] + setup_cost * (sent > EPS)
    if ledger == "legacy":
        profit -= substituted * (PRICES[0] - PRICES[1])
    elif ledger != "cash":
        raise ValueError(ledger)
    return {"profit": profit, "met": (sold1 >= demands[0] - EPS) & (sold2 >= demands[1] - EPS),
            "sent": sent.copy(), "substituted": substituted,
            "short1": np.maximum(demands[0] - sold1, 0.0),
            "short2": np.maximum(demands[1] - sold2, 0.0)}


def mean(array):
    return float(np.sum(PROB * array))


def summary(action):
    return {"expected_profit": mean(action["profit"]), "fulfilment_probability": mean(action["met"]),
            "expected_rework": mean(action["sent"]), "activation_probability": mean(action["sent"] > EPS),
            "expected_substitution": mean(action["substituted"]),
            "expected_grade1_shortage": mean(action["short1"]), "expected_grade2_shortage": mean(action["short2"])}


def pick(best, candidate):
    improve = candidate["profit"] > best["profit"] + 1e-8
    return {key: np.where(improve, candidate[key], best[key]) for key in best}, improve


def optimize_returns(flow, demands, eta=0.97, setup_workload=0.0, setup_cost=0.0,
                     ledger="cash", holding=30.0):
    """Exact fluid optimum for fixed forward flow: endpoints and grade-1 fill kink."""
    cap = available_returns(flow, demands, setup_workload)
    gap = np.maximum(demands[0] - flow.g1, 0.0)
    knots = np.sort(np.stack((np.zeros(len(PROB)), cap,
                             np.minimum(cap, gap / eta) if eta > 0 else np.zeros(len(PROB)))), axis=0)
    best = evaluate(flow, demands, ledger=ledger, holding=holding)
    for r in knots:
        candidate = evaluate(flow, demands, r, eta, ledger=ledger, holding=holding, setup_cost=setup_cost)
        best, _ = pick(best, candidate)
    if np.any(best["sent"] + setup_workload * (best["sent"] > EPS) > CAPS[:, 1] - flow.loads[:, 1] + EPS):
        raise AssertionError("station-2 capacity exceeded")
    return best


def capacity_policy(raw_input, demands, fractions, eta=0.97, setup_workload=0.0,
                    ledger="cash", allow_rework=True):
    """Exact capacity-state evaluation, finite forward-allocation grid, exact return knots."""
    best = None
    chosen = np.zeros(len(PROB))
    fixed_rows = []
    for fraction in fractions:
        flow = forward(raw_input, fraction)
        action = (optimize_returns(flow, demands, eta, setup_workload, ledger=ledger)
                  if allow_rework else evaluate(flow, demands, ledger=ledger))
        fixed_rows.append({"fraction": float(fraction), **summary(action)})
        if best is None:
            best = action
            chosen[:] = fraction
        else:
            best, improved = pick(best, action)
            chosen = np.where(improved, fraction, chosen)
    return best, chosen, max(fixed_rows, key=lambda row: row["expected_profit"]), fixed_rows


def forward_candidates(raw_input, demands, eta_knots=(0.97,), setup_workload=0.0):
    """Vertices of the piecewise-linear (station-2 forward work x, return r) model.

Finished output is min(t*x,B). Add the forward-load kinks and all intersections
of r=0, r=grade2 surplus, r=C2-S-x, and each grade-1 fill line. Include the
normal-flow sales kinks for the r=0 branch. Extra candidates outside a region
are harmless because actual flow and feasibility are evaluated afterwards.
"""
    yields = [s.yield_rate for s in STATIONS]
    t = float(np.prod(yields[1:]))
    upper = forward(raw_input).loads[:,1]
    limit = np.minimum.reduce((CAPS[:,2]*np.prod(yields[2:]),
                               CAPS[:,3]*np.prod(yields[3:]), CAPS[:,4]*yields[4]))
    points = [upper, np.zeros(len(PROB))]
    factor = yields[1]
    for index in (2,3,4):
        points.append(CAPS[:,index]/factor)
        factor *= yields[index]
    for value in (demands[0]/(Q1*t), demands[1]/(Q2*t), sum(demands)/((Q1+Q2)*t)):
        points.append(np.full(len(PROB),value))
    etas = sorted(set(eta for eta in eta_knots if eta>0))
    for slope, intercept in ((t,np.zeros(len(PROB))), (0.0,limit)):
        lines = [(0.0,np.zeros(len(PROB))), (Q2*slope,Q2*intercept-demands[1]),
                 (-1.0,CAPS[:,1]-setup_workload)]
        lines += [(-Q1*slope/eta,(demands[0]-Q1*intercept)/eta) for eta in etas]
        for i,(m1,b1) in enumerate(lines):
            for m2,b2 in lines[i+1:]:
                if abs(m1-m2)>1e-12:
                    points.append((b2-b1)/(m1-m2))
    return [np.clip(point,0.0,upper) for point in points]


def fraction_for_work(x):
    return np.where(CAPS[:,1]>0,
                    1.0-np.divide(x,CAPS[:,1],out=np.zeros(len(PROB)),where=CAPS[:,1]>0),0.0)


def exact_capacity_policy(raw_input, demands, eta=0.97, setup_workload=0.0,
                          ledger="cash", allow_rework=True):
    best = None
    chosen = np.zeros(len(PROB))
    candidates = forward_candidates(raw_input,demands,(eta,),setup_workload)
    upper = forward(raw_input).loads[:,1]
    for x in candidates:
        fraction = np.where(np.abs(x-upper)<1e-10,0.0,fraction_for_work(x))
        flow = forward(raw_input,fraction)
        action = (optimize_returns(flow,demands,eta,setup_workload,ledger=ledger)
                  if allow_rework else evaluate(flow,demands,ledger=ledger))
        if best is None:
            best = action
            chosen[:] = fraction
        else:
            best, improved = pick(best,action)
            chosen = np.where(improved,fraction,chosen)
    return best,chosen,len(candidates)


def save(number, payload, script):
    OUT.mkdir(parents=True, exist_ok=True)
    files = [Path(__file__), Path(script), ROOT / "backbone" / "ball_screw.py",
             ROOT / "backbone" / "evaluator.py", ROOT / "backbone" / "round25_state_policy.py",
             ROOT / "backbone" / "round2_share_consistency.py"]
    payload["provenance"] = {
        "run_at_utc": datetime.now(timezone.utc).isoformat(), "python": sys.version,
        "numpy": np.__version__, "capacity_states": len(PROB), "probability_mass": float(PROB.sum()),
        "sha256": {str(path.relative_to(ROOT)): sha256(path.read_bytes()).hexdigest() for path in files},
    }
    target = OUT / f"round{number}.json"
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"round": number, "result": str(target), "headline": payload.get("headline")}, ensure_ascii=True))
