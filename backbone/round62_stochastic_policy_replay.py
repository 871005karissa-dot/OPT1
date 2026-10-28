"""Round62: fresh direct execution of frozen pre-success setup policies.

Independent multinomial initial-quality draws and binomial rework successes;
no analytic eligibility integration in the simulator. Equivalent capacity states
are grouped by integer normal count and spare return capacity. Normal costs are
integrated exactly. Hoeffding uses squared GROUP weights, not original state
weights or the raw number of draws. Same histories across compared policies.
"""
import math
import time
from backbone.stochastic_setup_frontier import *

SEED=2026102862
REPLICAS=32768


def estimate(values):
    return {"estimate":float(np.mean(values)),"standard_error":float(np.std(values,ddof=1)/math.sqrt(len(values)))}


def main():
    started=time.perf_counter()
    prior=json.loads((SERVICE_OUT/"round61.json").read_text(encoding="utf-8"))
    trace=np.load(ROOT/prior["trace"]["path"])
    states={k:trace[k] for k in trace.files}
    for k in ("base_profit","base_service","groups","joint_mass_error"):
        states[k]=float(states[k])
    q1,q2=prior["grade_shares"]
    f=prior["eligible_fraction"]
    raw=prior["input"]
    d1,d2=map(int,prior["demands"])
    fee=2000.
    chosen=next(x for x in prior["rows"] if x["setup_fee"]==fee)
    target_policy=next(x for x in chosen["frontier"] if x["target"]==.75)
    solver=IntegerReworkEconomics(q1,q2,f,(d1,d2))
    flow=forward(raw)
    ns=np.floor(flow.finished+1e-9).astype(int)
    spare=np.floor(np.maximum(CAPS[:,4]-flow.loads[:,4],0.)+1e-9).astype(int)
    spare=np.minimum(spare,ns)
    groups,inverse=np.unique(np.stack((ns,spare),axis=1),axis=0,return_inverse=True)
    weights=np.bincount(inverse,weights=PROB,minlength=len(groups))
    n,limit=groups[:,0],groups[:,1]
    normal_cost=mean(flow.loads[:,0]*MATERIAL_COST+np.sum(flow.loads*MANUFACTURING_COSTS,axis=1))
    rng=np.random.default_rng(SEED)
    counts=rng.multinomial(n,(q1,q2*f,q2*(1-f),1-q1-q2),size=(REPLICAS,len(groups)))
    a=counts[:,:,0]
    b=counts[:,:,1]+counts[:,:,2]
    available=np.minimum.reduce((counts[:,:,1],np.maximum(b-d2,0),np.broadcast_to(limit,b.shape)))
    # Freeze all actions before drawing any future success count.
    choices=(execute_prefix(a,available,solver,fee,None),
             execute_prefix(a,available,solver,fee,target_policy["boundary"]),available>0)
    successes=rng.binomial(available,prior["eta"])
    exacts=(chosen["profit_best"],target_policy["deterministic_feasible"],
            summarize_choice(states,(states["R"]>0).astype(float),fee))
    labels=("profit_best","deterministic_target_75","always_return")
    radius=math.sqrt(float(weights@weights)*math.log(2*len(labels)/.05)/(2*REPLICAS))
    rows=[]
    services=[]
    profits=[]
    for label,opened,expected in zip(labels,choices,exacts):
        returned=np.where(opened,available,0)
        high=a+np.where(opened,successes,0)
        low=b-returned
        sub=np.minimum(np.maximum(high-d1,0),np.maximum(d2-low,0))
        cash=(120*np.minimum(high,d1)+60*np.minimum(low+sub,d2)+90*np.maximum(high-d1-sub,0)
              +30*np.maximum(low+sub-d2,0)-12.4*returned-fee*opened)
        service=((high>=d1)&(low+sub>=d2))@weights
        profit=cash@weights-normal_cost
        service_estimate,profit_estimate=estimate(service),estimate(profit)
        interval=[max(0.,service_estimate["estimate"]-radius),min(1.,service_estimate["estimate"]+radius)]
        z=abs(profit_estimate["estimate"]-expected["expected_profit"])/profit_estimate["standard_error"]
        assert interval[0]<=expected["fulfilment_probability"]<=interval[1],(label,interval,expected)
        assert z<5,(label,z)
        rows.append({"policy":label,"exact_model_value":expected,"simulated_service":service_estimate,
                     "simultaneous_service_interval":interval,"simulated_profit":profit_estimate,
                     "profit_error_in_standard_errors":z})
        services.append(service)
        profits.append(profit)
    path=SERVICE_OUT/"round62_validation.npz"
    np.savez_compressed(path,service=np.array(services),profit=np.array(profits),seed=SEED,groups=groups,weights=weights)
    save_service(62,{"question":"Does a frozen nonanticipative setup policy reproduce its finite-law service and profit when executed with fresh successes?",
        "assumptions":__doc__,"seed":SEED,"replicas_per_capacity_group":REPLICAS,
        "sum_squared_group_weights":float(weights@weights),"simultaneous_error_probability":.05,
        "headline":{"policies":len(rows),"capacity_groups":len(groups),"hoeffding_radius":radius,
                    "elapsed_seconds":time.perf_counter()-started},
        "paired_target_vs_always_profit":estimate(profits[1]-profits[2]),
        "trace":{"path":str(path.relative_to(ROOT)),"sha256":sha256(path.read_bytes()).hexdigest()},"rows":rows},__file__,
        (ROOT/"backbone"/"stochastic_setup_frontier.py",ROOT/"backbone"/"integer_rework.py",
         ROOT/"backbone"/"exact_quality_economics.py",ROOT/"backbone"/"exact_quality_service.py",
         SERVICE_OUT/"round61.json",ROOT/prior["trace"]["path"]))


if __name__=="__main__":
    main()
