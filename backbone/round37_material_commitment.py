"""Round 37: is material paid only when processed, or committed before capacity?

Sensitivity only, not a claim about the factory's procurement contract.
Commit I raw units ex ante, pay 20.7 each, and credit v for each unit that never
enters station 1. v/20.7 is hypothetical, with no carryover holding or future
procurement dynamics. The old processed-only convention equals full recovery.
At fixed I the extra charge is action-independent, so recourse and service loss
rankings are unchanged. Reoptimize I on the round-36 critical set.
"""
import copy
import time
from backbone.service_frontier import *
from backbone.round35_release_service import select_best,TARGETS


def unprocessed_raw(raw):
    return np.maximum(raw-CAPS[:,0],0.)


def repriced(row,recovery):
    result=copy.deepcopy(row)
    unused=mean(unprocessed_raw(row["input"]))
    charge=MATERIAL_COST*(1-recovery)*unused
    result["expected_unprocessed_raw"]=unused
    result["extra_material_commitment_charge"]=charge
    result["unconstrained"]["expected_profit"]-=charge
    for point in result["frontier"]:
        if point["feasible"]:
            for key in ("randomized_optimum","deterministic_feasible"):
                point[key]["expected_profit"]-=charge
    return result


def main():
    started=time.perf_counter()
    previous=json.loads((SERVICE_OUT/"round36.json").read_text(encoding="utf-8"))
    results=[]
    vector_error=0.
    for case in previous["cases"]:
      d=tuple(case["demands"])
      eta=case["eta"]
      for recovery in (0.,.5,1.):
        rows=[repriced(row,recovery) for row in case["rows"]]
        chosen=select_best(rows)
        unconstrained=chosen["unconstrained"]
        if recovery==1.:
            assert abs(unconstrained["expected_profit"]-case["best_unconstrained"]["unconstrained"]["expected_profit"])<1e-7
        # Recompute a selected vector to verify aggregate repricing independently.
        best,serve,found,_,_,_=action_pair(chosen["input"],d,eta,350.,True)
        state_charge=MATERIAL_COST*(1-recovery)*unprocessed_raw(chosen["input"])
        direct=mean(best["profit"]-state_charge)
        error=abs(direct-unconstrained["expected_profit"])
        vector_error=max(vector_error,error)
        assert error<1e-7
        assert abs(mean(best["met"])-unconstrained["fulfilment_probability"])<1e-10
        deterministic=[select_best(rows,a,True) for a in TARGETS]
        randomized=[select_best(rows,a) for a in TARGETS]
        for upper,lower in zip(randomized,deterministic):
            if upper is not None:
                lower["global_deterministic_profit_gap_bound"]=upper["expected_profit"]-lower["expected_profit"]
        results.append({"demands":d,"eta":eta,"raw_recovery_fraction":recovery,
            "raw_recovery_value":MATERIAL_COST*recovery,"service_ceiling_unchanged":case["absolute_service_ceiling"],
            "old_input":case["best_unconstrained"]["input"],"new_input":chosen["input"],
            "old_policy_under_this_convention":repriced(case["best_unconstrained"],recovery)["unconstrained"],
            "best_unconstrained":chosen,"best_randomized":randomized,
            "best_deterministic_feasible":deterministic,"rows":rows})
    save_service(37,{"question":"Do material commitment and recovery assumptions change the ex-ante release decision?",
        "assumptions":__doc__,"parameter_is_hypothetical":True,
        "critical_input_set_reused_from_round36":True,
        "headline":{"elapsed_seconds":time.perf_counter()-started,"cases":len(results),
            "cases_with_changed_release":sum(abs(c["new_input"]-c["old_input"])>1e-6 for c in results),
            "max_statewise_repricing_error":vector_error},"cases":results},__file__,
            (ROOT/"backbone"/"round35_release_service.py",ROOT/"backbone"/"round36_critical_release.py"))


if __name__=="__main__":
    main()
