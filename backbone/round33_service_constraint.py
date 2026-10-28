"""Round 33: profit versus a minimum joint order-fulfilment probability.

Known upgrade fraction eta=.2 is hypothetical and below the cash-profit fill
threshold. Capacity is observed, forward flow is fixed, surplus grade 2 may be
reworked. Randomization is explicitly permitted only for the frontier bound;
also report a deterministic feasible policy and its certified profit gap.
"""
import time
from backbone.service_frontier import *


def main():
    started=time.perf_counter()
    rows=[]
    for demands in ORDERS:
        raw=release(demands)
        best,serve,found,_,_,count=action_pair(raw,demands,eta=.2)
        r0=mean(best["met"])
        rmax=mean(found)
        targets=sorted(set([r0,r0+.5*(rmax-r0),rmax,.75,.85,.90,.95]))
        result=service_frontier(best,serve,found,targets)
        assert mean(best["sent"])<1e-8
        rows.append({"demands":demands,"input":raw,"candidate_pairs":count,**result})
    active=[row for row in rows if row["probability_mass_with_service_tradeoff"]>1e-8]
    save_service(33,{"question":"What is sacrificed when whole-order service is a constraint rather than just a reported outcome?",
        "assumptions":__doc__,"eta":.2,"setup_workload":0.,"parameter_is_hypothetical":True,
        "policy_class":"Exact randomized state-contingent frontier; deterministic feasible rounding plus upper bound on its optimality gap. Not a deterministic greedy optimality claim.",
        "headline":{"orders_with_tradeoff":len(active),"elapsed_seconds":time.perf_counter()-started,
                    "anchor":next(row for row in rows if row["demands"]==(750.,150.))},"rows":rows},__file__)


if __name__=="__main__":
    main()
