"""Round 39: coordinated stage-1 control with raw material committed ex ante.

Order I before observing C. Once C is known, choose normal stage-2 work x and
upgrade return r; stage-1 work is x/y1. Pay material price m for all I; unused
raw has hypothetical recovery v, so material net cost is (m-v)I+v*x/y1.
This changes recourse tradeoffs in x, unlike round37's action-independent charge.
Known eta=.97 and setup workload350 remain exploratory assumptions.
"""
import time
from backbone.service_frontier import *
from backbone.round35_release_service import select_best,TARGETS
from backbone.round36_critical_release import critical_inputs


def evaluate_release(raw,d,recovery):
    b,s,f,beta,_,_=action_pair(raw,d,.97,350.,True,True,recovery)
    result=service_frontier(b,s,f,TARGETS)
    return {"input":raw,"unconstrained":result["profit_best"],
            "maximum_fulfilment_probability":result["maximum_fulfilment_probability"],
            "frontier":result["frontier"],
            "expected_processed_raw":mean(forward(raw,beta).loads[:,1]/STATIONS[0].yield_rate)}


def main():
    started=time.perf_counter()
    results=[]
    maximum=STATIONS[0].machine_count*STATIONS[0].machine_capacity
    for d in ((550.,350.),(750.,150.)):
      for recovery in (0.,.5,1.):
        # Full recovery has the nested-set monotonicity proved/audited in round38.
        inputs=[maximum] if recovery==1. else critical_inputs(d,.97)
        rows=[evaluate_release(raw,d,recovery) for raw in inputs]
        best=select_best(rows)
        randomized=[select_best(rows,a) for a in TARGETS]
        deterministic=[select_best(rows,a,True) for a in TARGETS]
        for upper,lower in zip(randomized,deterministic):
            if upper is not None:
                lower["global_deterministic_profit_gap_bound"]=upper["expected_profit"]-lower["expected_profit"]
        results.append({"demands":d,"eta":.97,"raw_recovery_fraction":recovery,
            "input_candidates":len(rows),"free_raw_case_uses_sufficient_maximum_input":recovery==1.,
            "best_unconstrained":best,"best_randomized":randomized,
            "best_deterministic_feasible":deterministic,"rows":rows})
        print(json.dumps({"case_done":d,"recovery":recovery,"input_candidates":len(rows)},ensure_ascii=True),flush=True)
    save_service(39,{"question":"Does raw commitment restore an economic release decision after upstream processing is coordinated?",
        "assumptions":__doc__,"parameters_are_hypothetical":True,
        "critical_release_scope":"Round36 candidate geometry is unchanged because the revised material and stage-1 costs remain affine within the same flow regions. Full recovery uses monotonicity instead of redundant enumeration.",
        "headline":{"elapsed_seconds":time.perf_counter()-started,"cases":len(results),
                    "critical_input_evaluations":sum(c["input_candidates"] for c in results)},"cases":results},__file__,
        (ROOT/"backbone"/"round35_release_service.py",ROOT/"backbone"/"round36_critical_release.py"))


if __name__=="__main__":
    main()
