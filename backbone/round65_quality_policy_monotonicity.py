"""Round65: distinguish physical service capability from an endogenous profit policy.

Fixed normal flow/input, q2 and eligible-subclass probability. Increase q1 by
converting some originally defective items to grade1, leaving B/E unchanged
in a coupling. Maximal-return service is nondecreasing under that coupling.
With a setup fee, the profit-best policy can stop repairing when initial A
improves, because the fill-price benefit shrinks before the order is fully met.
A pointwise counterexample does not by itself prove a population reversal;
the finite-law parameter sweep reports whether one occurs in this case.
"""
import gc
import math
import time
from backbone.stochastic_setup_frontier import *


def direct_observed_example():
    rows=[]
    for a in (725,730):
        values=[]
        for r in range(31):
            expected=service=0.
            for y in range(r+1):
                p=math.comb(r,y)*.97**y*.03**(r-y)
                high,low=a+y,190-r
                cash=120*min(high,750)+60*min(low,150)+90*max(high-750,0)+30*max(low-150,0)-12.4*r-2000*(r>0)
                expected+=p*cash
                service+=p*(high>=750 and low>=150)
            values.append({"return":r,"net_revenue_before_normal_cost":expected,"conditional_service":service})
        best=max(values,key=lambda x:x["net_revenue_before_normal_cost"])
        rows.append({"A":a,"B":190,"eligible":30,"spare":30,"best":best,
                     "no_return":values[0],"all_return":values[-1]})
    assert rows[0]["best"]["return"]==30 and rows[1]["best"]["return"]==0
    assert rows[1]["best"]["net_revenue_before_normal_cost"]>rows[0]["best"]["net_revenue_before_normal_cost"]
    assert rows[1]["best"]["conditional_service"]<rows[0]["best"]["conditional_service"]
    return rows


def main():
    started=time.perf_counter()
    prior=json.loads((SERVICE_OUT/"round61.json").read_text(encoding="utf-8"))
    qnom,q2=prior["grade_shares"]
    qgrid=sorted(set((.59,.60,.61,.62,qnom,.63,.64,.65,.66)))
    rows=[]
    available_means=[]
    for q1 in qgrid:
        solver=StochasticSetupFrontier(q1,q2,prior["eligible_fraction"],tuple(prior["demands"]))
        states=solver.state_masses(prior["input"],0.)
        available_means.append(float(states["mass"]@states["R"]))
        for fee in (1000.,2000.,3000.):
            result=solve_setup_frontier(states,fee,(.75,))
            rows.append({"q1":q1,"q2":q2,"setup_fee":fee,"profit_best":result["profit_best"],
                         "maximum_service":result["maximum_service"],"target_75":result["frontier"][0]})
        release_integer_caches(solver)
        StochasticSetupFrontier.unbounded_return_law.cache_clear()
        del solver,states
        gc.collect()
    assert max(available_means)-min(available_means)<1e-8
    reversals=[]
    for fee in (1000.,2000.,3000.):
        subset=[x for x in rows if x["setup_fee"]==fee]
        for low,high in zip(subset,subset[1:]):
            assert high["maximum_service"]>=low["maximum_service"]-1e-10
            assert high["profit_best"]["expected_profit"]>=low["profit_best"]["expected_profit"]-1e-7
            if high["profit_best"]["fulfilment_probability"]<low["profit_best"]["fulfilment_probability"]-1e-8:
                reversals.append({"fee":fee,"lower_q1":low["q1"],"higher_q1":high["q1"],
                    "service_before":low["profit_best"]["fulfilment_probability"],
                    "service_after":high["profit_best"]["fulfilment_probability"]})
    save_service(65,{"question":"Can higher initial quality lower service under a reoptimized profit-only setup policy, despite improving capability?",
        "assumptions":__doc__,"fixed_input":prior["input"],"q2":q2,"eligible_fraction":prior["eligible_fraction"],
        "headline":{"quality_points":len(qgrid),"fee_quality_cases":len(rows),
                    "population_reversals_observed":len(reversals),
                    "max_change_in_available_rework_mean":max(available_means)-min(available_means),
                    "elapsed_seconds":time.perf_counter()-started},
        "pointwise_direct_all_action_example":direct_observed_example(),"population_reversals":reversals,"rows":rows},__file__,
        (ROOT/"backbone"/"stochastic_setup_frontier.py",ROOT/"backbone"/"integer_rework.py",
         ROOT/"backbone"/"exact_quality_service.py",ROOT/"backbone"/"exact_quality_economics.py",SERVICE_OUT/"round61.json"))


if __name__=="__main__":
    main()
