"""Round64: independently check selected release and integer-domain maximum service.

Round63 used a compressed observed-state distribution and LP. Here use the
separate conditional A,B,E integration for maximal-return service, plus fresh
direct multinomial/Bernoulli execution of the saved deterministic policy.
Both new simulations pay for fully committed material. Simulation intervals
cover numerical sampling error, not uncertainty about the factory parameters.
"""
import math
import time
from backbone.stochastic_setup_frontier import *
from backbone.round62_stochastic_policy_replay import estimate

REPLICAS=65536
SEED=2026102864


def main():
    started=time.perf_counter()
    prior=json.loads((SERVICE_OUT/"round63.json").read_text(encoding="utf-8"))
    chosen=next(x for x in prior["solutions"] if x["material_basis"]=="fully_committed" and x["target"]==.75)
    maximum=max((x for x in prior["rows"] if "maximum_service" in x),key=lambda x:x["maximum_service"])
    q1,q2=prior["grade_shares"]
    f=prior["eligible_fraction"]
    d1,d2=map(int,prior["demands"])
    solver=IntegerReworkEconomics(q1,q2,f,(d1,d2))
    rng=np.random.default_rng(SEED)
    rows=[]
    traces={}
    for index,(label,raw,fee,boundary) in enumerate((
        ("selected_75",chosen["best_deterministic_input"],2000.,chosen["boundary"]),
        ("integer_domain_maximum_service",maximum["input"],0.,None))):
        exact_all=solver.evaluate_integer(float(raw))
        stored=next(x for x in prior["rows"] if x["input"]==raw)
        discrepancy=abs(exact_all["fulfilment_probability"]-stored["maximum_service"])
        assert discrepancy<1e-10,(raw,discrepancy)
        flow=forward(float(raw))
        n=np.floor(flow.finished+1e-9).astype(int)
        spare=np.floor(np.maximum(CAPS[:,4]-flow.loads[:,4],0.)+1e-9).astype(int)
        groups,inverse=np.unique(np.stack((n,np.minimum(n,spare)),axis=1),axis=0,return_inverse=True)
        weights=np.bincount(inverse,weights=PROB,minlength=len(groups))
        normal_cost=float(raw)*MATERIAL_COST+mean(np.sum(flow.loads*MANUFACTURING_COSTS,axis=1))
        counts=rng.multinomial(groups[:,0],(q1,q2*f,q2*(1-f),1-q1-q2),size=(REPLICAS,len(groups)))
        a=counts[:,:,0]
        b=counts[:,:,1]+counts[:,:,2]
        available=np.minimum.reduce((counts[:,:,1],np.maximum(b-d2,0),np.broadcast_to(groups[:,1],b.shape)))
        opened=available>0 if fee==0 else execute_prefix(a,available,solver,fee,boundary)
        success=rng.binomial(available,.97)
        returned=np.where(opened,available,0)
        high=a+np.where(opened,success,0)
        low=b-returned
        sub=np.minimum(np.maximum(high-d1,0),np.maximum(d2-low,0))
        revenue=(120*np.minimum(high,d1)+60*np.minimum(low+sub,d2)+90*np.maximum(high-d1-sub,0)
                 +30*np.maximum(low+sub-d2,0)-12.4*returned-fee*opened)
        services=((high>=d1)&(low+sub>=d2))@weights
        profits=revenue@weights-normal_cost
        radius=math.sqrt(float(weights@weights)*math.log(4/.05)/(2*REPLICAS))
        interval=[max(0.,float(np.mean(services))-radius),min(1.,float(np.mean(services))+radius)]
        expected_service=chosen["feasible_service"] if fee>0 else maximum["maximum_service"]
        expected_profit=chosen["feasible_profit"] if fee>0 else exact_all["expected_profit"]-stored["extra_full_commitment_cost"]
        z=abs(float(profits.mean())-expected_profit)/estimate(profits)["standard_error"]
        assert interval[0]<=expected_service<=interval[1]
        assert z<5,(label,z)
        rows.append({"policy":label,"input":raw,"material_basis":"fully_committed","setup_fee":fee,
                     "exact_service":expected_service,"exact_profit":expected_profit,
                     "independent_maximal_return_service_discrepancy":discrepancy,
                     "simulated_service":estimate(services),"simultaneous_service_interval":interval,
                     "simulated_profit":estimate(profits),"profit_error_in_standard_errors":z,
                     "groups":len(groups),"sum_squared_group_weights":float(weights@weights),
                     "hoeffding_radius":radius})
        traces[f"service{index}"]=services
        traces[f"profit{index}"]=profits
        traces[f"groups{index}"]=groups
        traces[f"weights{index}"]=weights
    path=SERVICE_OUT/"round64_validation.npz"
    np.savez_compressed(path,seed=SEED,**traces)
    save_service(64,{"question":"Do the selected release and maximal-service point survive a separate integration and fresh policy execution?",
        "assumptions":__doc__,"seed":SEED,"replicas_per_group":REPLICAS,"simultaneous_error_probability":.05,
        "headline":{"validated_points":len(rows),"elapsed_seconds":time.perf_counter()-started,
                    "max_integrated_service_discrepancy":max(x["independent_maximal_return_service_discrepancy"] for x in rows)},
        "trace":{"path":str(path.relative_to(ROOT)),"sha256":sha256(path.read_bytes()).hexdigest()},"rows":rows},__file__,
        (ROOT/"backbone"/"integer_rework.py",ROOT/"backbone"/"stochastic_setup_frontier.py",
         ROOT/"backbone"/"round62_stochastic_policy_replay.py",ROOT/"backbone"/"exact_quality_service.py",
         ROOT/"backbone"/"exact_quality_economics.py",SERVICE_OUT/"round63.json"))


if __name__=="__main__":
    main()
