"""Round63: deterministic integer release + pre-success setup/service policy.

Keep round61's candidate final-station screw-diameter route and mandatory
downward substitution, iid KQC/item quality, stochastic integer repair success,
F=2000 and setup workload0. Compare processed-only vs fully committed raw cost
using the same conditional actions; cost difference is action-independent at I.
Exhaust I=0,...,2100. Perfect-unlimited single-feature service upper bounds may
screen inputs below all targets. For I>2100 all physical flows are identical
to2100; processed-only cost ties and full-commit cost increases. Thus2100
represents all larger integers for this specified fixed-forward policy class.
No continuous release, ex-ante randomized release, optional substitution,
adaptive forward control or calibrated factory optimality is asserted.
"""
from hashlib import sha256
import time
from backbone.stochastic_setup_frontier import *

TARGETS=(.7,.75,.8)
FEE=2000.


def summarize(rows):
    results=[]
    for material in ("processed_only","fully_committed"):
      for target in TARGETS:
        feasible=[]
        for row in rows:
            for policy in row.get("frontier",[]):
                if policy["target"]==target and policy["feasible"]:
                    shift=row["extra_full_commitment_cost"] if material=="fully_committed" else 0.
                    feasible.append((row,policy,shift))
        item={"material_basis":material,"target":target,"feasible":bool(feasible)}
        if feasible:
            ub=max(feasible,key=lambda x:x[1]["randomized_optimum"]["expected_profit"]-x[2])
            best=max(feasible,key=lambda x:x[1]["deterministic_feasible"]["expected_profit"]-x[2])
            upper=ub[1]["randomized_optimum"]["expected_profit"]-ub[2]
            lower=best[1]["deterministic_feasible"]["expected_profit"]-best[2]
            item.update({"best_randomized_policy_input":ub[0]["input"],"profit_upper_bound":upper,
                "best_deterministic_input":best[0]["input"],"feasible_profit":lower,
                "feasible_service":best[1]["deterministic_feasible"]["fulfilment_probability"],
                "global_deterministic_gap_upper_bound":max(0.,upper-lower),"boundary":best[1]["boundary"],
                "expected_rework":best[1]["deterministic_feasible"]["expected_rework"],
                "activation_probability":best[1]["deterministic_feasible"]["activation_probability"]})
        results.append(item)
    return results


def main():
    started=time.perf_counter()
    source=SERVICE_OUT/"round61.json"
    prior=json.loads(source.read_text(encoding="utf-8"))
    files=[Path(__file__),ROOT/"backbone"/"stochastic_setup_frontier.py",ROOT/"backbone"/"integer_rework.py",
           ROOT/"backbone"/"round59_repairability_ceiling.py",ROOT/"backbone"/"recourse_lab.py",
           ROOT/"backbone"/"exact_quality_service.py",ROOT/"backbone"/"exact_quality_economics.py",
           ROOT/"backbone"/"evaluator.py",ROOT/"backbone"/"ball_screw.py",source]
    signature={str(p.relative_to(ROOT)):sha256(p.read_bytes()).hexdigest() for p in files}
    checkpoint=SERVICE_OUT/"round63_progress.json"
    progress={"signature":signature,"rows":[],"status":"running"}
    if checkpoint.exists():
        saved=json.loads(checkpoint.read_text(encoding="utf-8"))
        if saved.get("signature")==signature:
            progress=saved
    def persist():
        temporary=checkpoint.with_suffix(".tmp")
        temporary.write_text(json.dumps(progress,indent=2,allow_nan=False),encoding="utf-8")
        temporary.replace(checkpoint)
    q1,q2=prior["grade_shares"]
    f=prior["eligible_fraction"]
    demands=tuple(prior["demands"])
    maximum=int(STATIONS[0].max_capacity)
    screen=NestedQualityBound(q1,q2,f,demands)
    by_n=np.array([screen.probability(n) for n in range(1601)])
    NestedQualityBound.probability.cache_clear()
    del screen
    solver=StochasticSetupFrontier(q1,q2,f,demands)
    rows=progress["rows"]
    assert [x["input"] for x in rows]==list(range(len(rows)))
    for raw in range(len(rows),maximum+1):
        flow=forward(float(raw))
        n=np.floor(flow.finished+1e-9).astype(int)
        upper=float(PROB@by_n[n])
        row={"input":raw,"perfect_unlimited_service_upper_bound":upper,
             "screened_below_all_targets":upper<min(TARGETS)-1e-12}
        if not row["screened_below_all_targets"]:
            states=solver.state_masses(float(raw),0.)
            solution=solve_setup_frontier(states,FEE,TARGETS)
            row.update({"extra_full_commitment_cost":MATERIAL_COST*(raw-mean(flow.loads[:,0])),
                        "maximum_service":solution["maximum_service"],"profit_best":solution["profit_best"],
                        "frontier":solution["frontier"],"observed_AR_states":len(states["mass"]),
                        "joint_mass_error":states["joint_mass_error"]})
        rows.append(row)
        if raw%50==0:
            persist()
            print(json.dumps({"last_input":raw,"screened":sum(x["screened_below_all_targets"] for x in rows),
                              "elapsed_seconds":time.perf_counter()-started}),flush=True)
    progress["status"]="complete"
    persist()
    save_service(63,{"question":"Which integer release supports a profitable service policy after matching the route and future-success timing?",
        "assumptions":__doc__,"grade_shares":[q1,q2],"eligible_fraction":f,"demands":demands,
        "setup_fee":FEE,"setup_workload":0.,"eta":.97,"return_station":5,
        "headline":{"integer_inputs":len(rows),"screened_inputs":sum(x["screened_below_all_targets"] for x in rows),
                    "evaluated_conditional_frontiers":sum(not x["screened_below_all_targets"] for x in rows),
                    "elapsed_seconds_this_execution":time.perf_counter()-started},
        "solutions":summarize(rows),"rows":rows},__file__,tuple(files[1:]))


if __name__=="__main__":
    main()
