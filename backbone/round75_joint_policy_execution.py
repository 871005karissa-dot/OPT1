"""Round75: decode and directly execute the merged two-timepoint decisions.

Verify three mechanisms: pure substitution with a fine capacity/A boundary,
merged setup/substitution with a substitution boundary, and a setup boundary.
Freeze all decisions before success; compare paired automatic-rule histories.
This validates fixed-input policies from74, not an outer-input optimum.
"""
import gc
import math
import time
from types import SimpleNamespace
from backbone.joint_fulfilment_frontier import *
from backbone.joint_policy import JointDecisionPolicy
from backbone.round62_stochastic_policy_replay import estimate

REPLICAS=32768
BLOCK=2048
SEED=2026102875


def frozen_setup(a,r,core,mode,boundary):
    a,r=np.broadcast_arrays(a,r)
    if mode=="none":
        return np.zeros(a.shape,dtype=bool)
    if mode=="always":
        return r>0
    if boundary is None:
        return execute_prefix(a,r,core,2000.,None)
    if boundary["kind"]=="substitution":
        threshold={"ratio":boundary["ratio"],"A":1600,"R":1600}
    else:
        threshold={k:boundary[k] for k in ("ratio","A","R")}
    return execute_prefix(a,r,core,2000.,threshold)


def decoded_substitution_mass(pool,ns,sub,boundary,rank):
    gaps=np.arange(1,pool.d2+1)
    if boundary is None:
        return np.zeros(len(gaps))
    if boundary["kind"]=="setup":
        return sub["mass"]*(30*gaps<boundary["ratio"])
    k=boundary["gap"]
    selected=sub["mass"]*(gaps<k)
    fine=boundary["fine_prefix"]["boundary"]
    if fine is None:
        selected[k-1]=sub["mass"][k-1]*boundary["deterministic_fraction"]
        return selected
    valid=ns>=pool.d1+pool.d2
    b=pool.d2-k
    probability=np.zeros(len(ns))
    probability[valid]=pool.grade2.pmf[ns[valid],b]*pool.high_given_low.tail[ns[valid]-b,pool.d1+k]
    early=rank<fine["capacity_position"]
    value=float(PROB[early]@probability[early])
    index=int(np.flatnonzero(rank==fine["capacity_position"])[0])
    assert COUNTS[index].tolist()==fine["capacity_counts"]
    if valid[index]:
        m=int(ns[index]-b)
        upper=min(fine["grade1_count"],m)
        probability_between=float(pool.high_given_low.pmf[m,pool.d1+k:upper+1].sum())
        value+=PROB[index]*pool.grade2.pmf[ns[index],b]*probability_between
    assert abs(value-boundary["fine_prefix"]["selected_mass"])<1e-10
    selected[k-1]=value
    return selected


def main():
    started=time.perf_counter()
    prior=json.loads((SERVICE_OUT/"round74.json").read_text(encoding="utf-8"))
    old=json.loads((SERVICE_OUT/"round73.json").read_text(encoding="utf-8"))
    params=json.loads((SERVICE_OUT/"round63.json").read_text(encoding="utf-8"))
    selected=[]
    for demand,mode in (((550.,350.),"none"),((650.,250.),"selective"),((700.,200.),"selective")):
        row=next(x for x in prior["rows"] if tuple(x["demands"])==demand and x["mode"]==mode)
        point=row["joint_frontier"]["frontier"][0]
        case=next(x for x in old["cases"] if tuple(x["demands"])==demand)
        reference=case["no_repair_best"] if mode=="none" else case["proposed_feasible"]
        selected.append({"key":f"d{int(demand[0])}_{int(demand[1])}_{mode}","demands":list(demand),
            "mode":mode,"input":row["frozen_input"],"target":row["target"],"boundary":point["boundary"],
            "expected":point["deterministic_feasible"],"automatic_reference":reference})
    rank=np.empty(len(PROB),dtype=int)
    rank[np.argsort(-PROB,kind="stable")]=np.arange(len(PROB))
    light=SimpleNamespace(d1=0,eta=.97,unit_cost=12.4,success=BinomialTables(1600,.97))
    aa,rr=np.arange(1601)[:,None],np.arange(1601)[None,:]
    packed={"shape":np.array([1601,1601]),"capacity_rank":rank}
    for spec in selected:
        light.d1=int(spec["demands"][0])
        decision=frozen_setup(aa,rr,light,spec["mode"],spec["boundary"])
        packed[spec["key"]]=np.packbits(decision,bitorder="big")
    archive=SERVICE_OUT/"round75_joint_policies.npz"
    np.savez_compressed(archive,**packed)
    archive_hash=sha256(archive.read_bytes()).hexdigest()
    catalog={"path":str(archive.relative_to(ROOT)),"sha256":archive_hash,"policies":selected,
             "indices":"setup indexed by initialA,availableR; substitution by initialA,B and frozen capacity priority"}
    catalog_path=SERVICE_OUT/"round75_policy_catalog.json"
    catalog_path.write_text(json.dumps(catalog,indent=2),encoding="utf-8")
    del decision,light,packed
    gc.collect()
    q1,q2=params["grade_shares"]
    f=params["eligible_fraction"]
    probabilities=(q1,q2*f,q2*(1-f),1-q1-q2)
    rng=np.random.default_rng(SEED)
    rows=[]
    traces={}
    for spec in selected:
        d1,d2=map(int,spec["demands"])
        raw=spec["input"]
        policy=JointDecisionPolicy(archive,spec["key"],archive_hash,spec)
        core=StochasticSetupFrontier(q1,q2,f,(d1,d2))
        pool=SubstitutionPool(core)
        flow=forward(float(raw))
        ns=np.floor(flow.finished+1e-9).astype(int)
        unique,inverse=np.unique(ns,return_inverse=True)
        weights_n=np.bincount(inverse,weights=PROB,minlength=len(unique))
        sub=pool.aggregate(unique,weights_n)
        states=core.state_masses(float(raw),0.)
        states["base_profit"]-=MATERIAL_COST*(raw-mean(flow.loads[:,0]))
        early=summarize_choice(states,policy.decide(states["A"],states["R"]),2000.)
        selected_mass=decoded_substitution_mass(pool,ns,sub,spec["boundary"],rank)
        exact={"expected_profit":early["expected_profit"]+30*sub["expected_automatic_substitution"]-30*float(np.arange(1,d2+1)@selected_mass),
            "fulfilment_probability":early["fulfilment_probability"]-float(sub["mass"].sum())+float(selected_mass.sum())}
        assert abs(exact["expected_profit"]-spec["expected"]["expected_profit"])<1e-7
        assert abs(exact["fulfilment_probability"]-spec["expected"]["fulfilment_probability"])<1e-9
        spare=np.minimum(ns,np.floor(np.maximum(CAPS[:,4]-flow.loads[:,4],0.)+1e-9).astype(int))
        side=policy.priority_for_indices(np.arange(len(PROB)))
        groups,inverse=np.unique(np.stack((ns,spare,side),axis=1),axis=0,return_inverse=True)
        weights=np.bincount(inverse,weights=PROB,minlength=len(groups))
        normal_cost=raw*MATERIAL_COST+mean(np.sum(flow.loads*MANUFACTURING_COSTS,axis=1))
        values={k:np.empty(REPLICAS) for k in ("new_profit","old_profit","new_service","old_service")}
        reference=spec["automatic_reference"]
        for start in range(0,REPLICAS,BLOCK):
            size=min(BLOCK,REPLICAS-start)
            counts=rng.multinomial(groups[:,0],probabilities,size=(size,len(groups)))
            a=counts[:,:,0]
            b=counts[:,:,1]+counts[:,:,2]
            available=np.minimum.reduce((counts[:,:,1],np.maximum(b-d2,0),np.broadcast_to(groups[:,1],b.shape)))
            new_open=policy.decide(a,available)
            if reference["policy_kind"]=="no_repair":
                old_open=np.zeros(a.shape,dtype=bool)
            elif reference["policy_kind"]=="always_return":
                old_open=available>0
            else:
                old_open=execute_prefix(a,available,core,2000.,reference["boundary"])
            sub_new=policy.substitute(a,b,groups[:,2])
            # Both startup choices and the new substitution plan are now frozen.
            potential_success=rng.binomial(available,.97)
            for tag,opened in (("new",new_open),("old",old_open)):
                returned=np.where(opened,available,0)
                high=a+np.where(opened,potential_success,0)
                low=b-returned
                substitute=sub_new if tag=="new" else np.minimum(np.maximum(high-d1,0),np.maximum(d2-low,0))
                cash=(120*np.minimum(high,d1)+60*np.minimum(low+substitute,d2)+90*np.maximum(high-d1-substitute,0)
                      +30*np.maximum(low+substitute-d2,0)-12.4*returned-2000*opened)
                values[tag+"_profit"][start:start+size]=cash@weights-normal_cost
                values[tag+"_service"][start:start+size]=((high>=d1)&(low+substitute>=d2))@weights
        radius=math.sqrt(float(weights@weights)*math.log(2*2*len(selected)/.05)/(2*REPLICAS))
        for tag,expected in (("new",spec["expected"]),("old",reference)):
            observed=float(values[tag+"_service"].mean())
            assert observed-radius<=expected["fulfilment_probability"]<=observed+radius
            error=abs(float(values[tag+"_profit"].mean())-expected["expected_profit"])
            assert error/estimate(values[tag+"_profit"])["standard_error"]<5
        paired=estimate(values["new_profit"]-values["old_profit"])
        exact_gain=spec["expected"]["expected_profit"]-reference["expected_profit"]
        assert abs(paired["estimate"]-exact_gain)<=max(1e-6,5*paired["standard_error"])
        rows.append({"demands":spec["demands"],"mode":spec["mode"],"input":raw,
            "decoded_exact_value":exact,"new_service":estimate(values["new_service"]),
            "new_service_interval":[max(0.,float(values["new_service"].mean())-radius),min(1.,float(values["new_service"].mean())+radius)],
            "new_profit":estimate(values["new_profit"]),"paired_profit_gain":paired,"exact_profit_gain":exact_gain,
            "hoeffding_radius":radius,"capacity_groups":len(groups),"sum_squared_group_weights":float(weights@weights)})
        for name,value in values.items():
            traces[spec["key"]+"_"+name]=value
        release_integer_caches(core)
        StochasticSetupFrontier.unbounded_return_law.cache_clear()
        AdaptiveSubstitution.expected_substitution.cache_clear()
        del core,pool,states
        gc.collect()
    trace_path=SERVICE_OUT/"round75_validation.npz"
    np.savez_compressed(trace_path,seed=SEED,**traces)
    save_service(75,{"question":"Do the merged setup/substitution policies execute using only the permitted information?",
        "assumptions":__doc__,"seed":SEED,"replicas_per_group":REPLICAS,"joint_service_family_error":.05,
        "policy_archive":catalog,"headline":{"fixed_input_policies":len(rows),"elapsed_seconds":time.perf_counter()-started},
        "trace":{"path":str(trace_path.relative_to(ROOT)),"sha256":sha256(trace_path.read_bytes()).hexdigest()},"rows":rows},__file__,
        (ROOT/"backbone"/"joint_policy.py",ROOT/"backbone"/"joint_fulfilment_frontier.py",
         ROOT/"backbone"/"frozen_policy.py",ROOT/"backbone"/"adaptive_substitution.py",
         ROOT/"backbone"/"stochastic_setup_frontier.py",ROOT/"backbone"/"integer_rework.py",
         ROOT/"backbone"/"exact_quality_service.py",ROOT/"backbone"/"exact_quality_economics.py",
         ROOT/"backbone"/"round62_stochastic_policy_replay.py",SERVICE_OUT/"round73.json",SERVICE_OUT/"round74.json",archive,catalog_path))


if __name__=="__main__":
    main()
