"""Round 34: can forward/return capacity allocation make a service target feasible?

Raw release remains fixed. Known eta and setup workload are hypothetical.
Compare identical service-policy classes with forward-first versus joint
station-2 allocation; show randomized bounds and deterministic feasibility.
"""
import time
from backbone.service_frontier import *


def main():
    started=time.perf_counter()
    rows=[]
    for eta in (.2,.35,.97):
      for demands in ORDERS:
        raw=release(demands)
        fixed_b,fixed_s,fixed_f,_,_,_=action_pair(raw,demands,eta,350.,False)
        best,serve,found,_,_,count=action_pair(raw,demands,eta,350.,True)
        reference,_,_=exact_capacity_policy(raw,demands,eta,350.)
        assert np.max(np.abs(best["profit"]-reference["profit"]))<1e-6
        assert np.all(best["profit"]>=fixed_b["profit"]-1e-6)
        assert np.all(found>=fixed_f)
        # Compare a common target set. An infeasible target remains explicit.
        targets=sorted(set([.7,.75,.8,.85,.9,.95,mean(fixed_b["met"]),mean(best["met"]),mean(found)]))
        fixed=service_frontier(fixed_b,fixed_s,fixed_f,targets)
        joint=service_frontier(best,serve,found,targets)
        for a,b in zip(fixed["frontier"],joint["frontier"]):
            if a["feasible"]:
                assert b["feasible"]
                assert b["randomized_optimum"]["expected_profit"]>=a["randomized_optimum"]["expected_profit"]-1e-6
        rows.append({"eta":eta,"demands":demands,"input":raw,"setup_workload":350.,
                     "candidate_pairs":count,"forward_first":fixed,"joint_allocation":joint,
                     "maximum_service_gain":joint["maximum_fulfilment_probability"]-fixed["maximum_fulfilment_probability"]})
    save_service(34,{"question":"Does a shared station-capacity decision improve the constrained service-profit frontier?",
        "assumptions":__doc__,"parameters_are_hypothetical":True,
        "optimality_scope":"Fixed release, fluid aggregate capacity, known eta; exact randomized frontier plus deterministic feasible bounds; no due-date schedule asserted.",
        "headline":{"rows":len(rows),"rows_with_service_ceiling_gain":sum(r["maximum_service_gain"]>1e-8 for r in rows),
                    "elapsed_seconds":time.perf_counter()-started,
                    "anchors":[r for r in rows if r["demands"]==(750.,150.)]},"rows":rows},__file__)


if __name__=="__main__":
    main()
