"""Round76: compare plug-in mean-quality service with finite-batch service.

All profiles send maximal allowed returns, with automatic substitution; no
economic setup choice is compared. Points are fixed in advance: every source
order's mean-gradewise input and first service-maximizing integer input, plus
round73's four selected economic inputs (used as input anchors only).
Matched CE shares N=floor(normal output) and integer return capacity/counts;
only initial grades/eligible counts are replaced by means. Then separately
compare random initial quality with mean future successes vs binomial successes.
These are model comparisons, not claims that the source's own assumptions err.
"""
import gc
import time
from backbone.maximal_service_curve import *
from backbone.round58_integer_rework_success import brute


def mean_quality_service(raw,d,q1,q2,f,matched):
    flow=forward(raw)
    output=np.floor(flow.finished+1e-9) if matched else flow.finished
    high,low=q1*output,q2*output
    spare=np.maximum(CAPS[:,4]-flow.loads[:,4],0.)
    if matched:
        spare=np.floor(spare+1e-9)
    returns=np.minimum.reduce((f*low,np.maximum(low-d[1],0.),spare))
    if matched:
        returns=np.floor(returns+1e-9)
    high,low=high+.97*returns,low-returns
    sub=np.minimum(np.maximum(high-d[0],0.),np.maximum(d[1]-low,0.))
    return mean((high>=d[0]-EPS)&(low+sub>=d[1]-EPS))


def mean_success_service(solver,raw):
    flow=forward(raw)
    n=np.floor(flow.finished+1e-9).astype(int)
    spare=np.minimum(n,np.floor(np.maximum(CAPS[:,4]-flow.loads[:,4],0.)+1e-9).astype(int))
    groups,inverse=np.unique(np.stack((n,spare),axis=1),axis=0,return_inverse=True)
    weights=np.bincount(inverse,weights=PROB,minlength=len(groups))
    values=np.array([solver.conditional(int(nn),int(ll)) for nn,ll in groups])
    return float(weights@values)


def main():
    started=time.perf_counter()
    small=StochasticSetupFrontier(.5,.3,.25,(5,2),maximum=12)
    curves=MaximalServiceCurves(small)
    checks=[]
    for cap in (0,3,8):
        for mode in ("integer_mean","binomial"):
            independent=brute(12,.5,.3,.25,(5,2),cap,.97,12.4,mode)[1]
            actual=small.conditional(12,cap) if mode=="integer_mean" else float(curves.curve(12)[cap])
            checks.append(abs(actual-independent))
            assert checks[-1]<1e-10
    MaximalServiceCurves.curve.cache_clear()
    release_integer_caches(small)
    StochasticSetupFrontier.unbounded_return_law.cache_clear()
    del small,curves
    coverage=json.loads((SERVICE_OUT/"round71.json").read_text(encoding="utf-8"))
    economic=json.loads((SERVICE_OUT/"round73.json").read_text(encoding="utf-8"))
    params=json.loads((SERVICE_OUT/"round63.json").read_text(encoding="utf-8"))
    q1,q2=params["grade_shares"]
    f=params["eligible_fraction"]
    rows=[]
    for order in coverage["cases"]:
        d=tuple(order["demands"])
        solver=StochasticSetupFrontier(q1,q2,f,d)
        curves=MaximalServiceCurves(solver)
        points=[("mean_gradewise_input",order["mean_gradewise_input_anchor"]),
                ("first_maximal_service_integer_input",float(order["first_maximizing_input"]))]
        selected=next((x for x in economic["cases"] if tuple(x["demands"])==d),None)
        if selected is not None:
            points.append(("economic_input_anchor_maximal_returns_not_economic_policy",float(selected["proposed_feasible"]["input"])))
        for role,raw in points:
            fluid=mean_quality_service(raw,d,q1,q2,f,False)
            matched=mean_quality_service(raw,d,q1,q2,f,True)
            random_mean=mean_success_service(solver,raw)
            random_success=curves.evaluate(raw)
            if role=="first_maximal_service_integer_input":
                assert abs(random_success-order["max_with_candidate_repair"])<1e-9
            rows.append({"demands":d,"input_role":role,"input":raw,
                "fluid_mean_quality_mean_success":fluid,
                "matched_floor_integer_return_mean_quality":matched,
                "random_initial_quality_mean_success":random_mean,
                "random_initial_quality_random_success":random_success,
                "matched_CE_minus_finite_batch":matched-random_success,
                "fluid_CE_minus_finite_batch":fluid-random_success,
                "mean_future_minus_random_future":random_mean-random_success,
                "CE_says80_finite_batch_below80":bool(matched>=.8 and random_success<.8)})
        MaximalServiceCurves.curve.cache_clear()
        release_integer_caches(solver)
        StochasticSetupFrontier.unbounded_return_law.cache_clear()
        del solver,curves
        gc.collect()
    save_service(76,{"question":"Does replacing random class counts by their means preserve joint service claims across the source orders?",
        "assumptions":__doc__,"grade_shares":[q1,q2],"eligible_fraction":f,
        "headline":{"small_all_outcome_checks":len(checks),"max_small_error":max(checks),
                    "order_pairs":len(coverage["cases"]),"predefined_input_points":len(rows),
                    "largest_matched_CE_overestimate":max(x["matched_CE_minus_finite_batch"] for x in rows),
                    "largest_matched_CE_underestimate":min(x["matched_CE_minus_finite_batch"] for x in rows),
                    "false80_claim_points":sum(x["CE_says80_finite_batch_below80"] for x in rows),
                    "elapsed_seconds":time.perf_counter()-started},"rows":rows},__file__,
        (ROOT/"backbone"/"maximal_service_curve.py",ROOT/"backbone"/"stochastic_setup_frontier.py",
         ROOT/"backbone"/"integer_rework.py",ROOT/"backbone"/"round58_integer_rework_success.py",
         ROOT/"backbone"/"exact_quality_service.py",SERVICE_OUT/"round71.json",SERVICE_OUT/"round73.json",SERVICE_OUT/"round63.json"))


if __name__=="__main__":
    main()
