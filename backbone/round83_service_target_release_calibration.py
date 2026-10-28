"""Round83: translate service-estimation bias into minimal-release decisions.

Same finite-batch model and always-maximal-return action as79, not economics.
Targets(.75,.90,.95) were already used in71. Compare minimal integer release
under matched mean counts with minimal release under full random counts. Reuse
the full immutable79 grid, without another simulation or expensive integration.
"""
from backbone.service_frontier import *


def main():
    source=json.loads((SERVICE_OUT/"round79.json").read_text(encoding="utf-8"))
    rows=[]
    for case in source["cases"]:
        ce=np.array([x["matched_CE"] for x in case["points"]])
        truth=np.array([x["finite_batch"] for x in case["points"]])
        assert [x["input"] for x in case["points"]]==list(range(len(ce)))
        for target in (.75,.90,.95):
            approximate=np.flatnonzero(ce>=target)
            exact=np.flatnonzero(truth>=target)
            first_mean=int(approximate[0]) if len(approximate) else None
            first_true=int(exact[0]) if len(exact) else None
            actual_at_mean=float(truth[first_mean]) if first_mean is not None else None
            rows.append({"demands":case["demands"],"target":target,
                "mean_model_feasible":first_mean is not None,"full_model_feasible":first_true is not None,
                "minimal_mean_input":first_mean,"full_service_at_mean_input":actual_at_mean,
                "minimal_full_input":first_true,
                "full_service_at_minimal_full_input":float(truth[first_true]) if first_true is not None else None,
                "additional_input_needed":first_true-first_mean if first_true is not None and first_mean is not None else None,
                "target_violation_at_mean_choice":max(0.,target-actual_at_mean) if actual_at_mean is not None else None,
                "mean_choice_fails_target":bool(first_mean is not None and actual_at_mean<target)})
    feasible=[x for x in rows if x["minimal_mean_input"] is not None]
    witness=max(feasible,key=lambda x:x["target_violation_at_mean_choice"])
    save_service(83,{"question":"How much extra release is needed when a mean-count service recommendation is reevaluated under finite-batch quality?",
        "assumptions":__doc__,"headline":{"order_target_cases":len(rows),"mean_feasible_cases":len(feasible),
            "mean_minimal_choices_failing_true_target":sum(x["mean_choice_fails_target"] for x in rows),
            "model_feasibility_disagreements":sum(x["mean_model_feasible"]!=x["full_model_feasible"] for x in rows),
            "largest_service_target_shortfall":witness},"rows":rows},__file__,(SERVICE_OUT/"round79.json",))


if __name__=="__main__":
    main()
