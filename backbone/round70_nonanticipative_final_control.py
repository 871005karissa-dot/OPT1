"""Round70: does controlled normal work overcome the fixed-forward service limit?

An optional broader policy class, not a change to the frozen canonical model.
Only allow final normal work x to be selected after capacity is known but before
ANY initial quality or repair outcomes are observed. Earlier stations stay
greedy. Aggregate workloads only; no job-level schedule or profit claim.
For service, larger I expands x's feasible set, so I2100 covers all smaller
integer releases and larger ones have identical flows. iid/DM quality laws and
repair success probabilities stay unchanged. No setup workload, single route.
"""
import gc
import math
import time
from backbone.final_station_service_control import *
from backbone.batch_stochastic_setup import BatchStochasticSetup


def main():
    started=time.perf_counter()
    checks=[]
    for kappa in (None,10.):
        small=(StochasticSetupFrontier(.5,.3,.25,(5,2),maximum=18) if kappa is None else
               BatchStochasticSetup(.5,.3,.25,(5,2),kappa,maximum=18))
        curves=MaximalServiceCurves(small)
        control=FinalStationServiceControl(curves,18.)
        for capacity in (8,12,18):
          for offered in (4.2,7.7,11.7,17.1):
            upper=min(capacity,offered)
            result=control.optimize_one(capacity,upper)
            candidates={0.,upper,*map(float,range(int(upper)+1))}
            candidates.update(n/.95 for n in range(int(.95*upper)+1) if n/.95<=upper)
            independent=max(small.metrics(int(math.floor(.95*x+1e-9)),
                               min(int(math.floor(.95*x+1e-9)),int(math.floor(capacity-x+1e-9))))["service"]
                            for x in candidates)
            checks.append(abs(independent-result["controlled_service"]))
            assert checks[-1]<1e-10,(kappa,capacity,upper,result,independent)
        MaximalServiceCurves.curve.cache_clear()
        release_integer_caches(small)
        StochasticSetupFrontier.unbounded_return_law.cache_clear()
        del small,curves,control
        gc.collect()
    original=json.loads((SERVICE_OUT/"round63.json").read_text(encoding="utf-8"))
    batch=json.loads((SERVICE_OUT/"round67.json").read_text(encoding="utf-8"))
    bounds=json.loads((SERVICE_OUT/"round66.json").read_text(encoding="utf-8"))
    q1,q2=original["grade_shares"]
    f=original["eligible_fraction"]
    raw=float(STATIONS[0].max_capacity)
    upper=float(forward(raw).loads[:,4].max())
    rows=[]
    for kappa in (None,1000.,100.):
        solver=(StochasticSetupFrontier(q1,q2,f,(750,150)) if kappa is None else
                BatchStochasticSetup(q1,q2,f,(750,150),kappa))
        curves=MaximalServiceCurves(solver)
        control=FinalStationServiceControl(curves,upper)
        result=control.solve(raw)
        if kappa is None:
            fixed=max(x["maximum_service"] for x in original["rows"] if "maximum_service" in x)
            ideal=.8103915687705819
        else:
            fixed=next(x for x in batch["cases"] if x["kappa"]==kappa)["maximum"]["maximum_service"]
            ideal=next(x for x in bounds["rows"] if x["kappa"]==kappa)["perfect_unlimited_repair_upper_bound_all_inputs"]
        assert result["maximum_service_with_control"]>=fixed-1e-9
        assert result["maximum_service_with_control"]<=ideal+1e-9
        rows.append({"kappa":kappa,"fixed_forward_max_all_integer_inputs":fixed,
                     "perfect_unlimited_repair_upper_bound":ideal,**result})
        print(json.dumps({"kappa":kappa,"controlled_service":result["maximum_service_with_control"],
                          "fixed_service":fixed}),flush=True)
        MaximalServiceCurves.curve.cache_clear()
        release_integer_caches(solver)
        StochasticSetupFrontier.unbounded_return_law.cache_clear()
        del solver,curves,control
        gc.collect()
    save_service(70,{"question":"Does observing capacity before quality and controlling final normal work change the service feasibility conclusion?",
        "assumptions":__doc__,"finite_control_argument":__import__("backbone.final_station_service_control",fromlist=["__doc__"]).__doc__,
        "headline":{"small_continuous_breakpoint_checks":len(checks),"max_small_error":max(checks),
                    "quality_laws":len(rows),"elapsed_seconds":time.perf_counter()-started},"rows":rows},__file__,
        (ROOT/"backbone"/"final_station_service_control.py",ROOT/"backbone"/"maximal_service_curve.py",
         ROOT/"backbone"/"batch_stochastic_setup.py",ROOT/"backbone"/"stochastic_setup_frontier.py",
         ROOT/"backbone"/"integer_rework.py",ROOT/"backbone"/"exact_quality_service.py",
         ROOT/"backbone"/"exact_batch_quality.py",SERVICE_OUT/"round63.json",SERVICE_OUT/"round66.json",SERVICE_OUT/"round67.json"))


if __name__=="__main__":
    main()
