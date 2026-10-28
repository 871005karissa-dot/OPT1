"""Round73: no-repair and always-repair baselines ALSO optimize release.

Same normal-source iid quality, one-way final-station candidate, eta.97, S0,
F2000 when activated, full committed raw material, mandatory downward allocation.
Four orders/targets are specified before comparison. Baseline means optimum
over integer I0..2100 in that restricted allocation class, not a supplier or
optional-substitution optimum. Use unconstrained-profit upper bounds to screen
constrained LPs; record the bounds so pruned inputs remain covered.
"""
import gc
import time
from backbone.recourse_value_curves import *

CASES=(((550.,350.),.9),((650.,250.),.9),((700.,200.),.85),((750.,150.),.75))


def main():
    started=time.perf_counter()
    source=json.loads((SERVICE_OUT/"round71.json").read_text(encoding="utf-8"))
    reference=json.loads((SERVICE_OUT/"round63.json").read_text(encoding="utf-8"))
    q1,q2=reference["grade_shares"]
    f=reference["eligible_fraction"]
    cache_path=SERVICE_OUT/"round71_physical_cache.npz"
    with np.load(cache_path,allow_pickle=False) as archive:
        groups,weights,offsets=(archive[k] for k in ("groups","weights","offsets"))
    normal_cost=np.array([raw*MATERIAL_COST+mean(np.sum(forward(float(raw)).loads*MANUFACTURING_COSTS,axis=1))
                          for raw in range(len(offsets)-1)])
    cost_path=SERVICE_OUT/"round73_committed_normal_cost.npy"
    if not cost_path.exists() or not np.array_equal(np.load(cost_path,allow_pickle=False),normal_cost):
        np.save(cost_path,normal_cost,allow_pickle=False)
    files=[Path(__file__),ROOT/"backbone"/"recourse_value_curves.py",ROOT/"backbone"/"maximal_service_curve.py",
           ROOT/"backbone"/"stochastic_setup_frontier.py",ROOT/"backbone"/"integer_rework.py",
           ROOT/"backbone"/"exact_quality_economics.py",ROOT/"backbone"/"exact_quality_service.py",
           ROOT/"backbone"/"recourse_lab.py",ROOT/"backbone"/"evaluator.py",ROOT/"backbone"/"ball_screw.py",
           SERVICE_OUT/"round71.json",SERVICE_OUT/"round72.json",cache_path,cost_path]
    signature={str(p.relative_to(ROOT)):sha256(p.read_bytes()).hexdigest() for p in files}
    checkpoint=SERVICE_OUT/"round73_progress.json"
    progress={"signature":signature,"cases":{},"status":"running"}
    if checkpoint.exists():
        old=json.loads(checkpoint.read_text(encoding="utf-8"))
        if old.get("signature")==signature:
            progress=old
    def persist():
        temporary=checkpoint.with_suffix(".tmp")
        temporary.write_text(json.dumps(progress,indent=2,allow_nan=False),encoding="utf-8")
        temporary.replace(checkpoint)
    results=[]
    for demands,target in CASES:
        key=f"{int(demands[0])}_{int(demands[1])}_{target}"
        state=progress["cases"].setdefault(key,{"completed":False,"evaluations":[]})
        if state["completed"]:
            results.append(state["result"])
            continue
        order=next(x for x in source["cases"] if tuple(x["demands"])==demands)
        no_r_service=np.array([x["no_repair"] for x in order["integer_input_service"]])
        all_r_service=np.array([x["maximal_repair"] for x in order["integer_input_service"]])
        feasible=np.flatnonzero(all_r_service>=target)
        assert len(feasible)>0
        solver=StochasticSetupFrontier(q1,q2,f,demands)
        if "bounds" not in state:
            engine=RecourseValueCurves(solver)
            max_n=int(groups[:,0].max())
            rev=np.array([solver.no_return_revenue(n) for n in range(max_n+1)])
            no_r_profit=np.add.reduceat(weights*rev[groups[:,0]],offsets[:-1])-normal_cost
            no_r_feasible=np.flatnonzero(no_r_service>=target)
            if len(no_r_feasible):
                best_no=int(no_r_feasible[np.argmax(no_r_profit[no_r_feasible])])
                state["no_repair_best"]={"input":best_no,"expected_profit":float(no_r_profit[best_no]),
                    "fulfilment_probability":float(no_r_service[best_no]),"policy_kind":"no_repair","boundary":None}
            else:
                state["no_repair_best"]=None
            use=np.zeros(len(groups),dtype=bool)
            for raw in feasible:
                use[offsets[raw]:offsets[raw+1]]=True
            ns=np.unique(groups[use,0])
            table_p=np.zeros((max_n+1,solver.maximum+1))
            table_s=np.zeros_like(table_p)
            table_all=np.zeros_like(table_p)
            table_all_s=np.zeros_like(table_p)
            for n in ns:
                values=engine.values(int(n),2000.)
                all_values=engine.always_return_values(int(n),2000.)
                table_p[n],table_s[n]=values["net_revenue"],values["service"]
                table_all[n],table_all_s[n]=all_values["net_revenue"],all_values["service"]
            bound=np.add.reduceat(weights*table_p[groups[:,0],groups[:,1]],offsets[:-1])-normal_cost
            best_service=np.add.reduceat(weights*table_s[groups[:,0],groups[:,1]],offsets[:-1])
            all_profit=np.add.reduceat(weights*table_all[groups[:,0],groups[:,1]],offsets[:-1])-normal_cost
            all_check=np.add.reduceat(weights*table_all_s[groups[:,0],groups[:,1]],offsets[:-1])
            discrepancy=float(np.max(np.abs(all_check[feasible]-all_r_service[feasible])))
            assert discrepancy<1e-9,(demands,discrepancy)
            assert float(np.min(bound[feasible]-all_profit[feasible]))>=-1e-7
            all_best=int(feasible[np.argmax(all_profit[feasible])])
            state["always_return_best"]={"input":all_best,"expected_profit":float(all_profit[all_best]),
                "fulfilment_probability":float(all_r_service[all_best]),"policy_kind":"always_return","boundary":None}
            state["bounds"]=[{"input":int(raw),"profit_bound":float(bound[raw]),
                "profit_best_service":float(best_service[raw]),"always_return_profit":float(all_profit[raw]),
                "maximum_service":float(all_r_service[raw])} for raw in feasible]
            state["full_return_service_check_error"]=discrepancy
            persist()
            RecourseValueCurves.values.cache_clear()
            RecourseValueCurves.always_return_values.cache_clear()
            del engine,table_p,table_s,table_all,table_all_s
            gc.collect()
        bounds=sorted(state["bounds"],key=lambda x:(-x["profit_bound"],x["input"]))
        evaluated={x["input"] for x in state["evaluations"]}
        candidates=[state["always_return_best"]]+([state["no_repair_best"]] if state["no_repair_best"] else [])
        candidates.extend(x["deterministic"] for x in state["evaluations"])
        best=max(candidates,key=lambda x:x["expected_profit"])
        remaining_upper=None
        for bound in bounds:
            raw=bound["input"]
            if raw in evaluated:
                continue
            if bound["profit_bound"]<=best["expected_profit"]+1e-7:
                remaining_upper=bound["profit_bound"]
                break
            if bound["profit_best_service"]>=target:
                candidate={"input":raw,"expected_profit":bound["profit_bound"],
                           "fulfilment_probability":bound["profit_best_service"],"policy_kind":"profit_best","boundary":None}
                record={"input":raw,"upper":bound["profit_bound"],"deterministic":candidate,
                        "full_LP_evaluated":False,"reason":"Unconstrained profit-best policy already meets target"}
            else:
                observed=solver.state_masses(float(raw),0.)
                flow=forward(float(raw))
                observed["base_profit"]-=MATERIAL_COST*(raw-mean(flow.loads[:,0]))
                solution=solve_setup_frontier(observed,2000.,(target,))
                assert abs(solution["profit_best"]["expected_profit"]-bound["profit_bound"])<1e-7
                assert abs(solution["profit_best"]["fulfilment_probability"]-bound["profit_best_service"])<1e-9
                row=solution["frontier"][0]
                assert row["feasible"]
                candidate={"input":raw,**row["deterministic_feasible"],"policy_kind":"threshold","boundary":row["boundary"]}
                record={"input":raw,"upper":row["randomized_optimum"]["expected_profit"],
                        "deterministic":candidate,"full_LP_evaluated":True,"local_gap_bound":row["deterministic_gap_upper_bound"]}
            state["evaluations"].append(record)
            evaluated.add(raw)
            if candidate["expected_profit"]>best["expected_profit"]:
                best=candidate
            persist()
        upper_values=[best["expected_profit"]]+[x["upper"] for x in state["evaluations"]]
        if remaining_upper is not None:
            upper_values.append(remaining_upper)
        global_upper=max(upper_values)
        if demands==(750.,150.):
            old=next(x for x in reference["solutions"] if x["material_basis"]=="fully_committed" and x["target"]==.75)
            assert old["feasible_profit"]-1e-6<=best["expected_profit"]<=old["profit_upper_bound"]+1e-6
        result={"demands":demands,"target":target,"no_repair_best":state["no_repair_best"],
            "always_return_best":state["always_return_best"],"proposed_feasible":best,
            "global_profit_upper_bound":global_upper,"global_deterministic_gap_upper_bound":max(0.,global_upper-best["expected_profit"]),
            "gain_vs_optimized_always_return":best["expected_profit"]-state["always_return_best"]["expected_profit"],
            "gain_vs_optimized_no_repair":None if state["no_repair_best"] is None else best["expected_profit"]-state["no_repair_best"]["expected_profit"],
            "service_feasible_input_count":len(bounds),"inputs_examined_after_profit_screen":len(state["evaluations"]),
            "full_LP_evaluations":sum(x["full_LP_evaluated"] for x in state["evaluations"]),
            "unevaluated_profit_bound_ceiling":remaining_upper,"bounds":state["bounds"],"evaluations":state["evaluations"],
            "full_return_service_check_error":state["full_return_service_check_error"]}
        state["result"],state["completed"]=result,True
        results.append(result)
        persist()
        print(json.dumps({"demands":demands,"target":target,"selected_input":best["input"],
            "profit":best["expected_profit"],"gain_vs_optimized_always":result["gain_vs_optimized_always_return"],
            "LP_evaluations":result["full_LP_evaluations"],"elapsed_seconds":time.perf_counter()-started}),flush=True)
        RecourseValueCurves.values.cache_clear()
        RecourseValueCurves.always_return_values.cache_clear()
        release_integer_caches(solver)
        StochasticSetupFrontier.unbounded_return_law.cache_clear()
        del solver
        gc.collect()
    progress["status"]="complete"
    persist()
    save_service(73,{"question":"Does the setup/service policy still improve profit when both baselines reoptimize their input under the same target?",
        "assumptions":__doc__,"headline":{"order_target_cases":len(results),
                    "full_LP_evaluations":sum(x["full_LP_evaluations"] for x in results),
                    "service_feasible_inputs":sum(x["service_feasible_input_count"] for x in results),
                    "elapsed_seconds_this_execution":time.perf_counter()-started},"cases":results},__file__,tuple(files[1:]))


if __name__=="__main__":
    main()
