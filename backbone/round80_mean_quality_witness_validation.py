"""Round80: fresh independent count draws validate deterministic CE witnesses.

Six points fixed before RNG: full-grid largest overestimate, its two neighbors,
largest underestimate, and the two original round76 witnesses at integer I.
Analytic values computed before simulation. Draw initial multinomial, freeze
maximal return, then draw future binomial. Both service profiles share histories.
These are model checks, not new factory data or empirical calibration.
"""
import gc
import math
import time
from backbone.round76_certainty_equivalent_audit import mean_quality_service,mean_success_service
from backbone.maximal_service_curve import *
from backbone.round62_stochastic_policy_replay import estimate

SEED=2026102880
REPLICAS=65536
BLOCK=2048
POINTS=(((500,300),1151),((500,300),1152),((500,300),1153),
        ((650,250),1297),((650,250),1316),((750,337),1699))


def main():
    started=time.perf_counter()
    params=json.loads((SERVICE_OUT/"round63.json").read_text(encoding="utf-8"))
    previous=json.loads((SERVICE_OUT/"round79.json").read_text(encoding="utf-8"))
    q1,q2=params["grade_shares"]
    f=params["eligible_fraction"]
    probabilities=(q1,q2*f,q2*(1-f),1-q1-q2)
    # All expectations and deterministic comparators are fixed before RNG exists.
    selected=[]
    for d,raw in POINTS:
        core=StochasticSetupFrontier(q1,q2,f,d)
        curves=MaximalServiceCurves(core)
        finite=curves.evaluate(float(raw))
        saved=next(x for x in previous["cases"] if tuple(x["demands"])==d)["points"][raw]
        assert abs(finite-saved["finite_batch"])<1e-10
        selected.append({"demands":d,"input":raw,"matched_CE":mean_quality_service(float(raw),d,q1,q2,f,True),
            "exact_random_success":finite,"exact_mean_success":mean_success_service(core,float(raw))})
        MaximalServiceCurves.curve.cache_clear()
        release_integer_caches(core)
        StochasticSetupFrontier.unbounded_return_law.cache_clear()
        del core,curves
        gc.collect()
    rng=np.random.default_rng(SEED)
    traces={}
    rows=[]
    for index,spec in enumerate(selected):
        d1,d2=spec["demands"]
        flow=forward(float(spec["input"]))
        n=np.floor(flow.finished+1e-9).astype(int)
        spare=np.minimum(n,np.floor(np.maximum(CAPS[:,4]-flow.loads[:,4],0.)+1e-9).astype(int))
        groups,inverse=np.unique(np.stack((n,spare),axis=1),axis=0,return_inverse=True)
        weights=np.bincount(inverse,weights=PROB,minlength=len(groups))
        values={tag:np.empty(REPLICAS) for tag in ("random_success","mean_success")}
        for start in range(0,REPLICAS,BLOCK):
            size=min(BLOCK,REPLICAS-start)
            counts=rng.multinomial(groups[:,0],probabilities,size=(size,len(groups)))
            a=counts[:,:,0]
            b=counts[:,:,1]+counts[:,:,2]
            r=np.minimum.reduce((counts[:,:,1],np.maximum(b-d2,0),np.broadcast_to(groups[:,1],b.shape)))
            y=rng.binomial(r,.97)
            for tag,success in (("random_success",y),("mean_success",.97*r)):
                high,low=a+success,b-r
                sub=np.minimum(np.maximum(high-d1,0),np.maximum(d2-low,0))
                values[tag][start:start+size]=((high>=d1-EPS)&(low+sub>=d2-EPS))@weights
        radius=math.sqrt(float(weights@weights)*math.log(2*2*len(selected)/.05)/(2*REPLICAS))
        estimates={}
        for tag,draws in values.items():
            interval=[max(0.,float(draws.mean())-radius),min(1.,float(draws.mean())+radius)]
            assert interval[0]<=spec["exact_"+tag]<=interval[1]
            estimates[tag]={**estimate(draws),"simultaneous_interval":interval}
            traces[f"point{index}_"+tag]=draws
        interval=estimates["random_success"]["simultaneous_interval"]
        rows.append({**spec,"group_count":len(groups),"sum_squared_group_weights":float(weights@weights),
            "simulation":estimates,"paired_mean_minus_random":estimate(values["mean_success"]-values["random_success"]),
            "CE_bias_interval":[spec["matched_CE"]-interval[1],spec["matched_CE"]-interval[0]]})
    trace=SERVICE_OUT/"round80_validation.npz"
    np.savez_compressed(trace,seed=SEED,**traces)
    save_service(80,{"question":"Can independent direct outcome draws reproduce the full-grid CE error witnesses?",
        "assumptions":__doc__,"seed":SEED,"replicas_per_group":REPLICAS,"family_error_probability":.05,
        "headline":{"predefined_points":len(rows),"service_profiles_checked":2*len(rows),
            "all_exact_values_inside_simultaneous_intervals":True,"elapsed_seconds":time.perf_counter()-started},
        "trace":{"path":str(trace.relative_to(ROOT)),"sha256":sha256(trace.read_bytes()).hexdigest()},"rows":rows},__file__,
        (ROOT/"backbone"/"round76_certainty_equivalent_audit.py",ROOT/"backbone"/"maximal_service_curve.py",
         ROOT/"backbone"/"stochastic_setup_frontier.py",ROOT/"backbone"/"integer_rework.py",
         ROOT/"backbone"/"round62_stochastic_policy_replay.py",SERVICE_OUT/"round79.json",SERVICE_OUT/"round63.json"))


if __name__=="__main__":
    main()
