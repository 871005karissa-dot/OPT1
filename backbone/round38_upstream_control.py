"""Round 38: can stage 1 avoid processing material that stage 2 will not use?

Capacity is known before processing. Relax the old fixed first-station rule:
stage-1 processing = stage-2 forward work / stage-1 yield. Raw material is still
charged only when processed. Thus raw release is a free upper bound on available
input: increasing it cannot worsen the optimized profit or service frontier.
This is a model degeneracy audit, not a recommendation to release unlimited raw.
"""
import time
from backbone.service_frontier import *


def main():
    started=time.perf_counter()
    maximum=STATIONS[0].machine_count*STATIONS[0].machine_capacity
    cases=[]
    for d in ((550.,350.),(750.,150.)):
      for eta in (.2,.97):
        inputs=sorted(set([0.,700.,1000.,1200.,1400.,1600.,1800.,maximum,release(d)]))
        rows=[]
        previous=-float("inf")
        previous_service=-float("inf")
        for raw in inputs:
            b,s,f,beta,_,_=action_pair(raw,d,eta,350.,True,True)
            old_b,_,old_f,_,_,_=action_pair(raw,d,eta,350.,True)
            assert np.all(b["profit"]>=old_b["profit"]-1e-6)
            assert np.all(f==old_f)
            result=service_frontier(b,s,f,(.7,.85,.9,.95))
            assert result["profit_best"]["expected_profit"]>=previous-1e-6
            assert result["maximum_fulfilment_probability"]>=previous_service-1e-10
            previous=result["profit_best"]["expected_profit"]
            previous_service=result["maximum_fulfilment_probability"]
            flow=forward(raw,beta)
            minimum_stage1=flow.loads[:,1]/STATIONS[0].yield_rate
            assert np.all(minimum_stage1<=np.minimum(raw,CAPS[:,0])+EPS)
            rows.append({"input":raw,"fixed_stage1":summary(old_b),"coordinated":result,
                "expected_stage1_work":mean(minimum_stage1),
                "gain_vs_fixed_stage1":mean(b["profit"]-old_b["profit"])})
        cases.append({"demands":d,"eta":eta,"rows":rows})
    save_service(38,{"question":"Is an ex-ante raw-release optimization meaningful if upstream processing can be curtailed and unused raw is free?",
        "assumptions":__doc__,"parameter_is_hypothetical":True,
        "analytic_conclusion":"Feasible recourse sets are nested in I, with no I-dependent committed cost; constrained and unconstrained optimal values cannot decrease. I=max first-station capacity is sufficient for a maximum, possibly on a plateau. A meaningful finite release tradeoff needs a commitment/carrying cost or a different information/processing restriction.",
        "headline":{"elapsed_seconds":time.perf_counter()-started,"cases":len(cases),
                    "tested_inputs":sum(len(c["rows"]) for c in cases)},"cases":cases},__file__)


if __name__=="__main__":
    main()
