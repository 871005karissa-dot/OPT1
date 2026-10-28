"""Round68: restore75% by reoptimizing integer release and setup policy.

Use round67's full service-feasibility scan for kappa1000/100. F2000, fully
committed raw material, single final-station candidate, same mean quality and
iid future successes. Evaluate all service-feasible integer inputs except a
larger input with identical (N,integer-spare) in EVERY capacity state. Such an
input has the same recourse law and no lower normal/committed cost, so is
dominated by its smallest representative. Not continuous or mixed release.
"""
import gc
import time
from backbone.batch_stochastic_setup import *


def physical_conditions(raw):
    flow=forward(float(raw))
    n=np.floor(flow.finished+1e-9).astype(np.int32)
    spare=np.minimum(n,np.floor(np.maximum(CAPS[:,4]-flow.loads[:,4],0.)+1e-9).astype(np.int32))
    matrix=np.stack((n,spare),axis=1)
    cost=raw*MATERIAL_COST+mean(np.sum(flow.loads*MANUFACTURING_COSTS,axis=1))
    return matrix,sha256(matrix.tobytes()).hexdigest(),cost


def main():
    started=time.perf_counter()
    scan=json.loads((SERVICE_OUT/"round67.json").read_text(encoding="utf-8"))
    prior=json.loads((SERVICE_OUT/"round63.json").read_text(encoding="utf-8"))
    files=[Path(__file__),ROOT/"backbone"/"batch_stochastic_setup.py",ROOT/"backbone"/"stochastic_setup_frontier.py",
           ROOT/"backbone"/"integer_rework.py",ROOT/"backbone"/"exact_batch_quality.py",
           ROOT/"backbone"/"recourse_lab.py",ROOT/"backbone"/"ball_screw.py",ROOT/"backbone"/"evaluator.py",
           SERVICE_OUT/"round67.json",SERVICE_OUT/"round63.json"]
    signature={str(p.relative_to(ROOT)):sha256(p.read_bytes()).hexdigest() for p in files}
    path=SERVICE_OUT/"round68_progress.json"
    progress={"signature":signature,"cases":{},"status":"running"}
    if path.exists():
        saved=json.loads(path.read_text(encoding="utf-8"))
        if saved.get("signature")==signature:
            progress=saved
    def persist():
        temp=path.with_suffix(".tmp")
        temp.write_text(json.dumps(progress,indent=2,allow_nan=False),encoding="utf-8")
        temp.replace(path)
    cases=[]
    q1,q2=prior["grade_shares"]
    for source in scan["cases"]:
        kappa=source["kappa"]
        key=str(kappa)
        rows=progress["cases"].setdefault(key,[])
        feasible_inputs=source["feasible_inputs"]
        assert [x["input"] for x in rows]==feasible_inputs[:len(rows)]
        representatives={x["physical_signature"]:x["input"] for x in rows if not x["dominated_by_identical_conditions"]}
        solver=BatchStochasticSetup(q1,q2,prior["eligible_fraction"],tuple(prior["demands"]),kappa)
        scan_lookup={x["input"]:x["maximum_service"] for x in source["rows"]}
        for raw in feasible_inputs[len(rows):]:
            conditions,key_physical,normal_cost=physical_conditions(raw)
            row={"input":raw,"physical_signature":key_physical,"normal_and_committed_material_cost":normal_cost,
                 "maximum_service":scan_lookup[raw],"dominated_by_identical_conditions":key_physical in representatives}
            if row["dominated_by_identical_conditions"]:
                earlier=representatives[key_physical]
                earlier_conditions,_,earlier_cost=physical_conditions(earlier)
                assert np.array_equal(earlier_conditions,conditions) and earlier_cost<=normal_cost+1e-8
                row["dominating_input"]=earlier
            else:
                representatives[key_physical]=raw
                states=solver.state_masses(float(raw),0.)
                flow=forward(float(raw))
                states["base_profit"]-=MATERIAL_COST*(raw-mean(flow.loads[:,0]))
                solution=solve_setup_frontier(states,2000.,(.75,))
                discrepancy=abs(solution["maximum_service"]-scan_lookup[raw])
                assert discrepancy<1e-9,(kappa,raw,discrepancy)
                result=solution["frontier"][0]
                assert result["feasible"],(kappa,raw,solution["maximum_service"])
                row.update({"frontier":result,"service_curve_discrepancy":discrepancy})
            rows.append(row)
            if len(rows)%25==0:
                persist()
                print(json.dumps({"kappa":kappa,"last_input":raw,"processed_feasible_inputs":len(rows),
                                  "elapsed_seconds":time.perf_counter()-started}),flush=True)
        persist()
        evaluated=[x for x in rows if not x["dominated_by_identical_conditions"]]
        upper=max(evaluated,key=lambda x:x["frontier"]["randomized_optimum"]["expected_profit"])
        best=max(evaluated,key=lambda x:x["frontier"]["deterministic_feasible"]["expected_profit"])
        upper_profit=upper["frontier"]["randomized_optimum"]["expected_profit"]
        feasible_profit=best["frontier"]["deterministic_feasible"]["expected_profit"]
        cases.append({"kappa":kappa,"best_randomized_policy_input":upper["input"],"profit_upper_bound":upper_profit,
            "best_deterministic_input":best["input"],"feasible_policy":best["frontier"]["deterministic_feasible"],
            "global_deterministic_gap_upper_bound":max(0.,upper_profit-feasible_profit),"boundary":best["frontier"]["boundary"],
            "feasible_inputs":len(rows),"evaluated_representatives":len(evaluated),
            "dominated_duplicates":len(rows)-len(evaluated),"rows":rows})
        release_integer_caches(solver)
        StochasticSetupFrontier.unbounded_return_law.cache_clear()
        del solver
        gc.collect()
    progress["status"]="complete"
    persist()
    save_service(68,{"question":"What is the cost of restoring75% service after fitting a different initial batch-quality law?",
        "assumptions":__doc__,"iid_reference":next(x for x in prior["solutions"] if x["material_basis"]=="fully_committed" and x["target"]==.75),
        "headline":{"kappa_cases":len(cases),"service_feasible_inputs":sum(x["feasible_inputs"] for x in cases),
                    "conditional_frontiers_evaluated":sum(x["evaluated_representatives"] for x in cases),
                    "dominated_duplicates":sum(x["dominated_duplicates"] for x in cases),
                    "elapsed_seconds_this_execution":time.perf_counter()-started},"cases":cases},__file__,tuple(files[1:]))


if __name__=="__main__":
    main()
