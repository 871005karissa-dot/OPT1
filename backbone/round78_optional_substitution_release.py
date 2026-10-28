"""Round78: optional substitution is allowed in ALL three policy classes.

Same four orders/targets and economic parameters as73. No repair, always repair,
and selective setup each reoptimize integer release with optional substitution.
Reuse the verified automatic-rule unconstrained-profit bound, adding the exact
gain from dropping automatic substitutions; this remains a valid upper bound.
All physical service-feasible sets are unchanged. Contract permitting optional
allocation is an explicit alternative, not an unapproved factory rule change.
"""
import gc
import time
from backbone.joint_fulfilment_frontier import *


def scalar_sub_cover(base_profit,base_service,mass,target):
    need=max(0.,target-base_service)
    if need<=1e-14:
        return {"profit_upper":base_profit,"service":base_service,"gap_band":0,"residual_mass":0.,"cost":0.}
    cumulative=np.cumsum(mass)
    j=min(int(np.searchsorted(cumulative,need)),len(mass)-1)
    previous=float(cumulative[j-1]) if j else 0.
    residual=max(0.,need-previous)
    cost=float((30*np.arange(1,j+1))@mass[:j])+30*(j+1)*residual
    assert need<=float(mass.sum())+1e-9
    return {"profit_upper":base_profit-cost,"service":target,"gap_band":j+1,
            "residual_mass":residual,"cost":cost}


def optimize_sub_only(mode,raws,base_profit,base_service,masses,target,pool):
    rows=[]
    for raw in raws:
        raw=int(raw)
        row=scalar_sub_cover(float(base_profit[raw]),float(base_service[raw]),masses[raw],target)
        rows.append({"input":raw,**row})
    if not rows:
        return None
    rows.sort(key=lambda x:(-x["profit_upper"],x["input"]))
    best=None
    checked=[]
    for row in rows:
        if best is not None and row["profit_upper"]<=best["expected_profit"]+1e-7:
            break
        raw=row["input"]
        k=row["gap_band"]
        boundary=None
        extra_cost=0.
        actual_service=row["service"]
        if k:
            ns=np.floor(forward(float(raw)).finished+1e-9).astype(int)
            rounded=pool.deterministic_boundary(ns,k,row["residual_mass"])
            extra_cost=30*k*rounded["extra_mass"]
            actual_service+=rounded["extra_mass"]
            boundary={"kind":"substitution","gap":k,"ratio":30.*k,
                "fraction":row["residual_mass"]/masses[raw,k-1],
                "deterministic_fraction":min(1.,rounded["selected_mass"]/masses[raw,k-1]),"fine_prefix":rounded}
        candidate={"input":raw,"mode":mode,"expected_profit":row["profit_upper"]-extra_cost,
            "fulfilment_probability":actual_service,"boundary":boundary,"policy_kind":"optional_substitution"}
        checked.append({"input":raw,"randomized_profit":row["profit_upper"],"deterministic":candidate,"rounding_cost":extra_cost})
        if best is None or candidate["expected_profit"]>best["expected_profit"]:
            best=candidate
    return {"best_feasible":best,"profit_upper_bound":rows[0]["profit_upper"],
            "global_deterministic_gap_bound":max(0.,rows[0]["profit_upper"]-best["expected_profit"]),
            "feasible_integer_inputs":len(rows),"fine_prefix_evaluations":len(checked),"checked":checked,
            "randomized_input_values":rows}


def main():
    started=time.perf_counter()
    automatic=json.loads((SERVICE_OUT/"round73.json").read_text(encoding="utf-8"))
    coverage=json.loads((SERVICE_OUT/"round71.json").read_text(encoding="utf-8"))
    params=json.loads((SERVICE_OUT/"round63.json").read_text(encoding="utf-8"))
    q1,q2=params["grade_shares"]
    f=params["eligible_fraction"]
    with np.load(SERVICE_OUT/"round71_physical_cache.npz",allow_pickle=False) as archive:
        groups,weights,offsets=(archive[k] for k in ("groups","weights","offsets"))
    cost=np.load(SERVICE_OUT/"round73_committed_normal_cost.npy",allow_pickle=False)
    files=[Path(__file__),ROOT/"backbone"/"joint_fulfilment_frontier.py",ROOT/"backbone"/"adaptive_substitution.py",
           ROOT/"backbone"/"stochastic_setup_frontier.py",ROOT/"backbone"/"integer_rework.py",
           ROOT/"backbone"/"exact_quality_service.py",ROOT/"backbone"/"exact_quality_economics.py",
           ROOT/"backbone"/"recourse_lab.py",ROOT/"backbone"/"ball_screw.py",ROOT/"backbone"/"evaluator.py",
           SERVICE_OUT/"round73.json",SERVICE_OUT/"round71.json",SERVICE_OUT/"round71_physical_cache.npz",
           SERVICE_OUT/"round73_committed_normal_cost.npy"]
    signature={str(p.relative_to(ROOT)):sha256(p.read_bytes()).hexdigest() for p in files}
    path=SERVICE_OUT/"round78_progress.json"
    progress={"signature":signature,"cases":{},"status":"running"}
    if path.exists():
        old=json.loads(path.read_text(encoding="utf-8"))
        if old.get("signature")==signature:
            progress=old
    def persist():
        temp=path.with_suffix(".tmp")
        temp.write_text(json.dumps(progress,indent=2,allow_nan=False),encoding="utf-8")
        temp.replace(path)
    results=[]
    for original in automatic["cases"]:
        d=tuple(original["demands"])
        target=original["target"]
        key=f"{int(d[0])}_{int(d[1])}_{target}"
        status=progress["cases"].setdefault(key,{"complete":False,"evaluations":[]})
        if status["complete"]:
            results.append(status["result"])
            continue
        data=next(x for x in coverage["cases"] if tuple(x["demands"])==d)
        no_service=np.array([x["no_repair"] for x in data["integer_input_service"]])
        all_service=np.array([x["maximal_repair"] for x in data["integer_input_service"]])
        feasible=np.flatnonzero(all_service>=target)
        core=StochasticSetupFrontier(q1,q2,f,d)
        pool=SubstitutionPool(core)
        max_n=int(groups[:,0].max())
        u_by_n=np.array([pool.expected_substitution(n) for n in range(max_n+1)])
        mass_by_n=np.array([pool.completion_masses(n) for n in range(max_n+1)])
        rev_by_n=np.array([core.no_return_revenue(n) for n in range(max_n+1)])
        automatic_no_profit=np.add.reduceat(weights*rev_by_n[groups[:,0]],offsets[:-1])-cost
        expected_u=np.add.reduceat(weights*u_by_n[groups[:,0]],offsets[:-1])
        mass=np.zeros((len(cost),int(d[1])))
        for raw in feasible:
            lo,hi=offsets[raw],offsets[raw+1]
            mass[raw]=weights[lo:hi]@mass_by_n[groups[lo:hi,0]]
        completion=mass.sum(axis=1)
        no_profit=automatic_no_profit+30*expected_u
        no_base_service=np.maximum(no_service-completion,0.)
        no_result=optimize_sub_only("none",np.flatnonzero(no_service>=target),no_profit,no_base_service,mass,target,pool)
        bound_lookup={x["input"]:x for x in original["bounds"]}
        assert set(bound_lookup)==set(map(int,feasible))
        all_profit=np.zeros(len(cost))
        profit_bound=np.zeros(len(cost))
        profit_service=np.zeros(len(cost))
        for raw in feasible:
            bound=bound_lookup[int(raw)]
            all_profit[raw]=bound["always_return_profit"]+30*expected_u[raw]
            profit_bound[raw]=bound["profit_bound"]+30*expected_u[raw]
            profit_service[raw]=max(0.,bound["profit_best_service"]-completion[raw])
        all_result=optimize_sub_only("always",feasible,all_profit,np.maximum(all_service-completion,0.),mass,target,pool)
        baseline_candidates=[all_result["best_feasible"]]+([no_result["best_feasible"]] if no_result else [])
        baseline_candidates.extend(x["deterministic"] for x in status["evaluations"])
        best=max(baseline_candidates,key=lambda x:x["expected_profit"])
        order=sorted(map(int,feasible),key=lambda raw:(-profit_bound[raw],raw))
        evaluated={x["input"] for x in status["evaluations"]}
        remaining_upper=None
        for raw in order:
            if raw in evaluated:
                continue
            if profit_bound[raw]<=best["expected_profit"]+1e-7:
                remaining_upper=float(profit_bound[raw])
                break
            if profit_service[raw]>=target:
                candidate={"input":raw,"mode":"selective","expected_profit":float(profit_bound[raw]),
                    "fulfilment_probability":float(profit_service[raw]),"boundary":None,"policy_kind":"joint_optional"}
                record={"input":raw,"upper":float(profit_bound[raw]),"deterministic":candidate,"LP_evaluated":False}
            else:
                observed=core.state_masses(float(raw),0.)
                flow=forward(float(raw))
                observed["base_profit"]-=MATERIAL_COST*(raw-mean(flow.loads[:,0]))
                ns=np.floor(flow.finished+1e-9).astype(int)
                summary={"mass":mass[raw],"expected_automatic_substitution":float(expected_u[raw]),
                    "completable_substitution_quantity":float(np.arange(1,int(d[1])+1)@mass[raw]),
                    "partial_unfulfillable_substitution":max(0.,float(expected_u[raw]-np.arange(1,int(d[1])+1)@mass[raw]))}
                result=joint_frontier(observed,summary,pool,ns,2000.,(target,),"selective")
                assert abs(result["profit_best_no_substitution"]["expected_profit"]-profit_bound[raw])<1e-7
                row=result["frontier"][0]
                assert row["feasible"]
                candidate={"input":raw,"mode":"selective",**row["deterministic_feasible"],
                    "boundary":row["boundary"],"policy_kind":"joint_optional"}
                record={"input":raw,"upper":row["randomized_optimum"]["expected_profit"],
                    "deterministic":candidate,"LP_evaluated":True,"local_gap":row["deterministic_gap_bound"]}
            status["evaluations"].append(record)
            evaluated.add(raw)
            if candidate["expected_profit"]>best["expected_profit"]:
                best=candidate
            persist()
        upper=max([best["expected_profit"]]+[x["upper"] for x in status["evaluations"]]+
                  ([remaining_upper] if remaining_upper is not None else []))
        result={"demands":d,"target":target,"no_repair_optional_substitution":no_result,
            "always_repair_optional_substitution":all_result,"proposed_feasible":best,
            "global_profit_upper_bound":upper,"global_deterministic_gap_bound":max(0.,upper-best["expected_profit"]),
            "gain_over_best_optional_baseline":best["expected_profit"]-max(x["expected_profit"] for x in baseline_candidates[:len([all_result])+int(no_result is not None)]),
            "full_joint_LP_evaluations":sum(x["LP_evaluated"] for x in status["evaluations"]),
            "evaluations":status["evaluations"],"unevaluated_unconstrained_profit_ceiling":remaining_upper,
            "unconstrained_input_bounds":[{"input":raw,"profit_bound":float(profit_bound[raw]),
                "profit_best_service":float(profit_service[raw])} for raw in order]}
        status["complete"],status["result"]=True,result
        results.append(result)
        persist()
        print(json.dumps({"demands":d,"target":target,"selected_input":best["input"],
            "profit":best["expected_profit"],"gap":result["global_deterministic_gap_bound"],
            "gain_over_best_optional_baseline":result["gain_over_best_optional_baseline"],
            "elapsed_seconds":time.perf_counter()-started}),flush=True)
        release_integer_caches(core)
        StochasticSetupFrontier.unbounded_return_law.cache_clear()
        AdaptiveSubstitution.expected_substitution.cache_clear()
        del core,pool
        gc.collect()
    progress["status"]="complete"
    persist()
    save_service(78,{"question":"Do the economic comparisons survive when optional substitution and release are optimized in every baseline?",
        "assumptions":__doc__,"headline":{"order_target_cases":len(results),
            "full_joint_LP_evaluations":sum(x["full_joint_LP_evaluations"] for x in results),
            "elapsed_seconds_this_execution":time.perf_counter()-started},"cases":results},__file__,tuple(files[1:]))


if __name__=="__main__":
    main()
