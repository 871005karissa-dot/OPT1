"""Round 36: finite critical-release reduction for the current fluid recourse model.

Known eta>0, fixed setup workload, zero setup money cost, fixed grade shares,
processed-only raw cost, and station-2 forward/return decisions after C is known.
Use the complete piecewise-linear x/r vertex set. Critical I values are x/y1
and first-station saturation levels. On each remaining interval, action profit
branches are affine and their binary service labels are constant in its interior.
The optimized randomized service-constrained value is a supremum of affine
functions over an I-independent policy set, hence convex on that interval;
its maximum is attained at an interval endpoint. Endpoint feasible sets include
the one-sided limits. See the accompanying research proof and scope restrictions.
"""
import time
from backbone.service_frontier import *
from backbone.round35_release_service import compact_release,select_best,TARGETS


def critical_inputs(demands,eta,setup=350.):
    maximum=STATIONS[0].machine_count*STATIONS[0].machine_capacity
    y1=STATIONS[0].yield_rate
    points=forward_candidates(maximum,demands,(eta,),setup)
    values=np.concatenate([point/y1 for point in points]+[CAPS[:,0].astype(float),np.array([0.,maximum])])
    # Merge only numerical duplicates. Service classification tolerance is 1e-6.
    return np.unique(np.round(np.clip(values,0.,maximum),9)).tolist()


def objective_at(row,target=None,deterministic=False):
    if target is None:
        return row["unconstrained"]["expected_profit"]
    point=next(p for p in row["frontier"] if p["target"]==target)
    if not point["feasible"]:
        return None
    return point["deterministic_feasible" if deterministic else "randomized_optimum"]["expected_profit"]


def main():
    started=time.perf_counter()
    previous=json.loads((SERVICE_OUT/"round35.json").read_text(encoding="utf-8"))
    results=[]
    for case in previous["cases"]:
        d=tuple(case["demands"])
        eta=case["eta"]
        inputs=critical_inputs(d,eta)
        cache={raw:compact_release(raw,d,eta) for raw in inputs}
        rows=list(cache.values())
        maximum=rows[-1]["maximum_fulfilment_probability"]
        global_best=select_best(rows)
        randomized=[select_best(rows,a) for a in TARGETS]
        deterministic=[select_best(rows,a,True) for a in TARGETS]
        for earlier in case["rows"]:
            assert objective_at(global_best)>=objective_at(earlier)-1e-6
            for j,a in enumerate(TARGETS):
                old=objective_at(earlier,a)
                if old is not None:
                    assert randomized[j] is not None
                    assert randomized[j]["expected_profit"]>=old-1e-6
        # Probe interiors of the eight longest release intervals independently
        # of where a coarse grid happened to land; endpoints must dominate.
        intervals=sorted(zip(inputs,inputs[1:]),key=lambda ab:ab[1]-ab[0],reverse=True)[:8]
        probes=[]
        for left,right in intervals:
            mid=(left+right)/2
            middle=compact_release(mid,d,eta)
            worst_excess=0.
            for target in (None,)+TARGETS:
                vm=objective_at(middle,target)
                if vm is not None:
                    endpoints=[v for v in (objective_at(cache[left],target),objective_at(cache[right],target)) if v is not None]
                    assert endpoints,(d,eta,left,right,target)
                    excess=vm-max(endpoints)
                    worst_excess=max(worst_excess,excess)
                    assert excess<1e-6,(d,eta,left,right,target,excess)
            probes.append({"left":left,"midpoint":mid,"right":right,"max_endpoint_dominance_violation":worst_excess})
        for upper,lower in zip(randomized,deterministic):
            if upper is not None:
                lower["global_deterministic_profit_gap_bound"]=upper["expected_profit"]-lower["expected_profit"]
        results.append({"demands":d,"eta":eta,"setup_workload":350.,"critical_input_count":len(inputs),
            "critical_inputs":inputs,"absolute_service_ceiling":maximum,
            "best_unconstrained":global_best,"best_randomized":randomized,
            "best_deterministic_feasible":deterministic,"interior_probes":probes,"rows":rows,
            "gain_vs_round35_unconstrained_grid":objective_at(global_best)-objective_at(case["best_unconstrained_on_tested_set"])})
    save_service(36,{"question":"Can the continuous raw-release search be reduced to finitely many critical endpoints?",
        "assumptions":__doc__,"scope":"Analytic candidate reduction for this specific fluid model and randomized service policies; deterministic feasible policies carry a global profit gap bound from that randomized upper bound. No integer-unit, scheduling, unknown-yield, or general-network optimality claim.",
        "numerical_tolerances":{"duplicate_input_rounding_digits":9,"service_quantity_tolerance":EPS,"profit_check_tolerance":1e-6},
        "headline":{"elapsed_seconds":time.perf_counter()-started,"cases":len(results),
                    "critical_input_evaluations":sum(c["critical_input_count"] for c in results),
                    "interior_probes":sum(len(c["interior_probes"]) for c in results),
                    "earlier_grid_points_dominated":sum(c["total_tested_inputs"] for c in previous["cases"])},
        "cases":results},__file__,(ROOT/"backbone"/"round35_release_service.py",))


if __name__=="__main__":
    main()
