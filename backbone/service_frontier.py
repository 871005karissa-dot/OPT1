"""Service-constrained research helpers; separate from the manuscript evaluator.

For known upgrade yield, a state either fulfils the whole order or does not.
Keep the profit-best action and the profit-best fulfilling action in each state.
The global randomized-policy frontier is then a fractional knapsack, sorted by
conditional profit sacrifice per additional unit of fulfilment probability.
Rounding its one boundary state up gives a feasible deterministic policy, not
a claim of deterministic optimality (the latter is a covering knapsack).
"""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import json
import sys

from backbone.recourse_lab import *

SERVICE_OUT = ROOT / "research" / "2026-10-28" / "service_rounds"


def action_pair(raw, demands, eta=0.2, setup_workload=0.0, allocate=False,
                coordinate_upstream=False, material_recovery_fraction=1.0):
    """Best action and best complete-delivery action in every capacity state.

Exact vertices for this fixed-release fluid model, with known eta, zero setup
cost, no minimum run size, and the same surplus-only single-return route.
"""
    if eta <= 0:
        raise ValueError("this helper requires positive known eta")
    upper = forward(raw).loads[:, 1]
    xs = forward_candidates(raw, demands, (eta,), setup_workload) if allocate else [upper]
    best = None
    serve = None
    found = np.zeros(len(PROB), dtype=bool)
    best_fraction = np.zeros(len(PROB))
    serve_fraction = np.zeros(len(PROB))
    count = 0
    for x in xs:
        fraction = np.where(np.abs(x-upper) < 1e-10, 0.0, fraction_for_work(x))
        flow = forward(raw, fraction)
        if coordinate_upstream:
            loads=flow.loads.copy()
            loads[:,0]=loads[:,1]/STATIONS[0].yield_rate
            flow=Flow(loads,flow.finished)
        material_charge=MATERIAL_COST*(1-material_recovery_fraction)*(raw-flow.loads[:,0])
        cap = available_returns(flow, demands, setup_workload)
        gap = np.maximum(demands[0]-flow.g1, 0.0)
        for r in np.sort(np.stack((np.zeros(len(PROB)), cap, np.minimum(cap, gap/eta))), axis=0):
            candidate = evaluate(flow, demands, r, eta)
            candidate["profit"]-=material_charge
            count += 1
            if best is None:
                best = {key: value.copy() for key, value in candidate.items()}
                serve = {key: value.copy() for key, value in candidate.items()}
            else:
                best, improve = pick(best, candidate)
                best_fraction = np.where(improve, fraction, best_fraction)
            improve_serve = candidate["met"] & (~found | (candidate["profit"] > serve["profit"]+1e-8))
            serve = {key: np.where(improve_serve, candidate[key], serve[key]) for key in serve}
            serve_fraction = np.where(improve_serve, fraction, serve_fraction)
            found |= candidate["met"]
    # Profit ties favour fulfilment. This costs nothing and closes zero-loss gaps.
    tie_serve = found & (serve["profit"] >= best["profit"]-1e-8)
    best = {key: np.where(tie_serve, serve[key], value) for key, value in best.items()}
    best_fraction = np.where(tie_serve, serve_fraction, best_fraction)
    assert np.all(best["profit"] >= serve["profit"]-1e-6)
    assert np.all(serve["met"][found])
    for action, fraction, valid in ((best,best_fraction,np.ones(len(PROB),dtype=bool)),
                                    (serve,serve_fraction,found)):
        flow = forward(raw, fraction)
        used = action["sent"]+setup_workload*(action["sent"]>EPS)
        assert np.all(used[valid] <= (CAPS[:,1]-flow.loads[:,1])[valid]+EPS)
    return best, serve, found, best_fraction, serve_fraction, count


def mixture_summary(best, serve, z):
    """z is probability of choosing the complete-delivery action, conditional on C."""
    mixed = {key: (1-z)*value+z*serve[key] for key,value in best.items()}
    result = summary(mixed)
    # A mixture of quantities must not be misread as a randomized activation event.
    result["activation_probability"] = mean((1-z)*(best["sent"]>EPS)+z*(serve["sent"]>EPS))
    return result


def service_frontier(best, serve, found, targets):
    base_r = mean(best["met"])
    eligible = found & ~best["met"].astype(bool)
    indices = np.flatnonzero(eligible)
    losses = np.maximum(best["profit"]-serve["profit"], 0.0)
    # Cost/probability ratio = conditional loss, not p*loss.
    indices = indices[np.argsort(losses[indices], kind="stable")]
    masses = PROB[indices]
    cumulative = np.cumsum(masses)
    maximum = base_r+float(cumulative[-1] if len(cumulative) else 0.0)
    assert abs(maximum-mean(found)) < 1e-10
    rows = []
    for target in targets:
        target = float(target)
        row = {"target":target, "feasible":target <= maximum+1e-10}
        if not row["feasible"]:
            row["infeasibility_gap"] = target-maximum
            rows.append(row)
            continue
        required = max(0.0, min(target-base_r, maximum-base_r))
        z = np.zeros(len(PROB))
        boundary = None
        if required > 1e-14:
            j = min(int(np.searchsorted(cumulative, required, side="left")),len(indices)-1)
            z[indices[:j]] = 1.0
            before = float(cumulative[j-1]) if j else 0.0
            fraction = float(np.clip((required-before)/masses[j],0.0,1.0))
            z[indices[j]] = fraction
            boundary = int(indices[j])
        randomized = mixture_summary(best,serve,z)
        deterministic_z = z.copy()
        if boundary is not None:
            deterministic_z[boundary] = 1.0
        deterministic = mixture_summary(best,serve,deterministic_z)
        bound = (0.0 if boundary is None else
                 float(PROB[boundary]*losses[boundary]*(1-z[boundary])))
        multiplier = 0.0 if boundary is None else float(losses[boundary])
        # Independent Lagrangian certificate for the fractional covering optimum.
        dual_loss = multiplier*required+float(np.sum(masses*np.minimum(0.0,losses[indices]-multiplier)))
        actual_loss = mean(best["profit"])-randomized["expected_profit"]
        assert abs(actual_loss-dual_loss)<1e-7
        assert randomized["fulfilment_probability"] >= target-1e-9 or target <= base_r
        assert deterministic["fulfilment_probability"] >= target-1e-9 or target <= base_r
        assert abs(randomized["expected_profit"]-deterministic["expected_profit"]-bound)<1e-7
        row.update({"randomized_optimum":randomized,"deterministic_feasible":deterministic,
                    "deterministic_optimality_gap_upper_bound":bound,
                    "boundary_state":None if boundary is None else COUNTS[boundary].tolist(),
                    "boundary_state_probability":0.0 if boundary is None else float(PROB[boundary]),
                    "boundary_serve_probability":0.0 if boundary is None else float(z[boundary]),
                    "marginal_profit_sacrifice":multiplier,
                    "lagrangian_loss_lower_bound":dual_loss,
                    "primal_dual_loss_gap":actual_loss-dual_loss})
        rows.append(row)
    return {"profit_best":summary(best),"maximum_fulfilment_probability":maximum,
            "states_with_service_tradeoff":int(eligible.sum()),
            "probability_mass_with_service_tradeoff":float(PROB[eligible].sum()),"frontier":rows}


def save_service(number, payload, script, extra_sources=()):
    SERVICE_OUT.mkdir(parents=True,exist_ok=True)
    sources = [Path(__file__),Path(script),ROOT/"backbone"/"recourse_lab.py",
               ROOT/"backbone"/"ball_screw.py",ROOT/"backbone"/"evaluator.py",
               ROOT/"backbone"/"round2_share_consistency.py"]+[Path(p) for p in extra_sources]
    payload["provenance"]={"run_at_utc":datetime.now(timezone.utc).isoformat(),
        "python":sys.version,"numpy":np.__version__,"capacity_states":len(PROB),
        "probability_mass":float(PROB.sum()),
        "sha256":{str(p.relative_to(ROOT)):sha256(p.read_bytes()).hexdigest() for p in sources}}
    target=SERVICE_OUT/f"round{number}.json"
    target.write_text(json.dumps(payload,ensure_ascii=False,indent=2,allow_nan=False),encoding="utf-8")
    headline=payload.get("headline",{})
    compact={key:value for key,value in headline.items() if key not in ("anchor","anchors","rows")}
    print(json.dumps({"round":number,"result":str(target),"headline":compact},ensure_ascii=True))
