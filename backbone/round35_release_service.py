"""Round 35: choose raw release before capacity is revealed, with a service floor.

Finite coarse grid plus local refinement over release; no global optimality
claim in the release dimension. Conditional recourse is exact for the specified
fluid model. Deterministic gap bounds apply at a fixed tested release only.
"""
import time
from backbone.service_frontier import *

TARGETS=(.70,.75,.85,.90,.95)


def compact_release(raw,demands,eta,targets=TARGETS):
    best,serve,found,_,_,_=action_pair(raw,demands,eta,350.,True)
    result=service_frontier(best,serve,found,targets)
    return {"input":raw,"unconstrained":result["profit_best"],
            "maximum_fulfilment_probability":result["maximum_fulfilment_probability"],
            "frontier":[{key:value for key,value in row.items() if key in
                ("target","feasible","infeasibility_gap","randomized_optimum","deterministic_feasible",
                 "deterministic_optimality_gap_upper_bound")} for row in result["frontier"]]}


def select_best(rows,target=None,deterministic=False):
    if target is None:
        return max(rows,key=lambda row:row["unconstrained"]["expected_profit"])
    key="deterministic_feasible" if deterministic else "randomized_optimum"
    candidates=[]
    for row in rows:
        point=next(p for p in row["frontier"] if p["target"]==target)
        if point["feasible"]:
            candidates.append({"input":row["input"],"target":target,**point[key],
                "conditional_deterministic_gap_bound":point["deterministic_optimality_gap_upper_bound"]})
    return max(candidates,key=lambda row:row["expected_profit"]) if candidates else None


def main():
    started=time.perf_counter()
    results=[]
    maximum=STATIONS[0].machine_count*STATIONS[0].machine_capacity
    for demands in ((550.,350.),(750.,150.)):
      for eta in (.2,.35,.97):
        baseline=release(demands)
        inputs=set(map(float,np.arange(0.,maximum+1.,50.)))
        inputs.update((baseline,release(demands,2)))
        cache={}
        def calculate(values):
            for raw in sorted(values):
                key=round(float(raw),9)
                if key not in cache:
                    cache[key]=compact_release(key,demands,eta)
        calculate(inputs)
        coarse=list(cache.values())
        selected=[select_best(coarse)]+[select_best(coarse,a) for a in TARGETS]
        finer=set()
        for row in selected:
            if row is not None:
                center=row["input"]
                finer.update(float(np.clip(center+delta,0.,maximum)) for delta in np.arange(-50.,51.,10.))
        calculate(finer)
        rows=sorted(cache.values(),key=lambda row:row["input"])
        ceilings=[row["maximum_fulfilment_probability"] for row in rows]
        assert np.all(np.diff(ceilings)>=-1e-9)
        results.append({"demands":demands,"eta":eta,"setup_workload":350.,
            "baseline_input":baseline,"baseline":cache[round(baseline,9)],
            "coarse_points":len(coarse),"total_tested_inputs":len(rows),
            "best_unconstrained_on_tested_set":select_best(rows),
            "best_randomized_on_tested_set":[select_best(rows,a) for a in TARGETS],
            "best_deterministic_feasible_on_tested_set":[select_best(rows,a,True) for a in TARGETS],
            "rows":rows})
    save_service(35,{"question":"Can ex-ante raw release overcome service infeasibility of a fixed release?",
        "assumptions":__doc__,"parameters_are_hypothetical":True,"service_targets":TARGETS,
        "input_search":{"range":[0.,maximum],"coarse_step":50.,"local_step":10.,
                        "global_release_optimality_proven":False},
        "headline":{"elapsed_seconds":time.perf_counter()-started,
                    "cases":len(results),"tested_inputs":sum(r["total_tested_inputs"] for r in results)},
        "cases":results},__file__)


if __name__=="__main__":
    main()
