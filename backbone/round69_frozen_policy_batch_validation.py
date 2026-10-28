"""Round69: freeze exact discrete actions, then independently execute iid/DM cases.

Truth tables are authoritative for runtime-stable boundary decisions. Future
repair outcomes are not inputs. Direct simulation draws batch probabilities
from Dirichlet, then multinomial initial counts, then binomial successes AFTER
the return decision. No beta-binomial table is used to generate simulation data.
Full committed-material cost; F2000, one candidate final-station repair route.
"""
import gc
import math
import time
from types import SimpleNamespace
from backbone.batch_stochastic_setup import *
from backbone.frozen_policy import FrozenPolicy
from backbone.round62_stochastic_policy_replay import estimate

REPLICAS=32768
BLOCK=2048
SEED=2026102869


def main():
    started=time.perf_counter()
    iid=json.loads((SERVICE_OUT/"round63.json").read_text(encoding="utf-8"))
    batch=json.loads((SERVICE_OUT/"round68.json").read_text(encoding="utf-8"))
    chosen=next(x for x in iid["solutions"] if x["material_basis"]=="fully_committed" and x["target"]==.75)
    specifications=[{"key":"iid","kappa":None,"input":chosen["best_deterministic_input"],
        "boundary":chosen["boundary"],"expected_profit":chosen["feasible_profit"],"expected_service":chosen["feasible_service"]}]
    for case in batch["cases"]:
        specifications.append({"key":"batch_"+str(int(case["kappa"])),"kappa":case["kappa"],
            "input":case["best_deterministic_input"],"boundary":case["boundary"],
            "expected_profit":case["feasible_policy"]["expected_profit"],
            "expected_service":case["feasible_policy"]["fulfilment_probability"]})
    maximum=1600
    lightweight=SimpleNamespace(d1=750,eta=.97,unit_cost=12.4,success=BinomialTables(maximum,.97))
    a_grid=np.arange(maximum+1)[:,None]
    r_grid=np.arange(maximum+1)[None,:]
    packed={"shape":np.array([maximum+1,maximum+1])}
    for spec in specifications:
        matrix=execute_prefix(a_grid,r_grid,lightweight,2000.,spec["boundary"])
        assert not np.any(matrix[:,0])
        packed[spec["key"]]=np.packbits(matrix,bitorder="big")
        spec["packed_decisions_sha256"]=sha256(packed[spec["key"]].tobytes()).hexdigest()
    archive=SERVICE_OUT/"round69_frozen_policies.npz"
    np.savez_compressed(archive,**packed)
    archive_hash=sha256(archive.read_bytes()).hexdigest()
    catalog={"archive":str(archive.relative_to(ROOT)),"sha256":archive_hash,"shape":[maximum+1,maximum+1],
             "indices":["initial grade1 count A","available maximal return R"],"bitorder":"big",
             "demands":[750,150],"setup_fee":2000.,"eta":.97,"station":5,
             "warning":"Decisions reproducible; route and quality law still hypothetical and order-specific.",
             "policies":specifications}
    catalog_path=SERVICE_OUT/"round69_policy_catalog.json"
    catalog_path.write_text(json.dumps(catalog,indent=2),encoding="utf-8")
    del matrix,lightweight,packed
    gc.collect()
    q1,q2=iid["grade_shares"]
    f=iid["eligible_fraction"]
    pp=np.array([q1,q2*f,q2*(1-f),1-q1-q2])
    rng=np.random.default_rng(SEED)
    rows=[]
    traces={}
    for index,spec in enumerate(specifications):
        kappa,raw=spec["kappa"],spec["input"]
        frozen=FrozenPolicy(archive,spec["key"],archive_hash)
        solver=(StochasticSetupFrontier(q1,q2,f,(750,150)) if kappa is None else
                BatchStochasticSetup(q1,q2,f,(750,150),kappa))
        states=solver.state_masses(float(raw),0.)
        flow=forward(float(raw))
        states["base_profit"]-=MATERIAL_COST*(raw-mean(flow.loads[:,0]))
        replay=summarize_choice(states,frozen.decide(states["A"],states["R"]),2000.)
        assert abs(replay["expected_profit"]-spec["expected_profit"])<1e-7
        assert abs(replay["fulfilment_probability"]-spec["expected_service"])<1e-10
        release_integer_caches(solver)
        StochasticSetupFrontier.unbounded_return_law.cache_clear()
        del solver,states
        gc.collect()
        n=np.floor(flow.finished+1e-9).astype(int)
        spare=np.minimum(n,np.floor(np.maximum(CAPS[:,4]-flow.loads[:,4],0.)+1e-9).astype(int))
        groups,inverse=np.unique(np.stack((n,spare),axis=1),axis=0,return_inverse=True)
        weights=np.bincount(inverse,weights=PROB,minlength=len(groups))
        normal_cost=raw*MATERIAL_COST+mean(np.sum(flow.loads*MANUFACTURING_COSTS,axis=1))
        services=np.empty(REPLICAS)
        profits=np.empty(REPLICAS)
        for start in range(0,REPLICAS,BLOCK):
            size=min(BLOCK,REPLICAS-start)
            probabilities=pp if kappa is None else rng.dirichlet(kappa*pp,size=(size,len(groups)))
            counts=rng.multinomial(groups[:,0],probabilities,size=(size,len(groups)))
            a=counts[:,:,0]
            b=counts[:,:,1]+counts[:,:,2]
            available=np.minimum.reduce((counts[:,:,1],np.maximum(b-150,0),np.broadcast_to(groups[:,1],b.shape)))
            opened=frozen.decide(a,available)
            returned=np.where(opened,available,0)
            successes=rng.binomial(returned,.97)
            high,low=a+successes,b-returned
            sub=np.minimum(np.maximum(high-750,0),np.maximum(150-low,0))
            cash=(120*np.minimum(high,750)+60*np.minimum(low+sub,150)+90*np.maximum(high-750-sub,0)
                  +30*np.maximum(low+sub-150,0)-12.4*returned-2000*opened)
            services[start:start+size]=((high>=750)&(low+sub>=150))@weights
            profits[start:start+size]=cash@weights-normal_cost
        radius=math.sqrt(float(weights@weights)*math.log(2*len(specifications)/.05)/(2*REPLICAS))
        interval=[max(0.,float(services.mean())-radius),min(1.,float(services.mean())+radius)]
        z=abs(float(profits.mean())-spec["expected_profit"])/estimate(profits)["standard_error"]
        assert interval[0]<=spec["expected_service"]<=interval[1]
        assert z<5,(spec,z)
        rows.append({"key":spec["key"],"kappa":kappa,"input":raw,"truth_table_replay":replay,
            "simulated_service":estimate(services),"simultaneous_service_interval":interval,
            "simulated_profit":estimate(profits),"profit_error_in_standard_errors":z,
            "hoeffding_radius":radius,"group_count":len(groups),"sum_squared_group_weights":float(weights@weights)})
        traces[spec["key"]+"_service"]=services
        traces[spec["key"]+"_profit"]=profits
    trace_path=SERVICE_OUT/"round69_validation.npz"
    np.savez_compressed(trace_path,seed=SEED,**traces)
    save_service(69,{"question":"Can the optimized policies be frozen and executed without floating-point threshold differences or future information?",
        "assumptions":__doc__,"seed":SEED,"replicas_per_group":REPLICAS,"simultaneous_error_probability":.05,
        "policy_archive":catalog,"headline":{"frozen_policies":len(rows),"elapsed_seconds":time.perf_counter()-started,
            "all_exact_service_values_inside_intervals":True},
        "trace":{"path":str(trace_path.relative_to(ROOT)),"sha256":sha256(trace_path.read_bytes()).hexdigest()},"rows":rows},__file__,
        (ROOT/"backbone"/"frozen_policy.py",ROOT/"backbone"/"batch_stochastic_setup.py",
         ROOT/"backbone"/"stochastic_setup_frontier.py",ROOT/"backbone"/"integer_rework.py",
         ROOT/"backbone"/"exact_quality_service.py",ROOT/"backbone"/"exact_quality_economics.py",
         ROOT/"backbone"/"exact_batch_quality.py",ROOT/"backbone"/"round62_stochastic_policy_replay.py",
         SERVICE_OUT/"round63.json",SERVICE_OUT/"round68.json",archive,catalog_path))


if __name__=="__main__":
    main()
