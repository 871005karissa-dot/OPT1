"""Round51: independently simulate the constructive deterministic substitution rule.

Validate no substitution, automatic maximum substitution, and the round50
whole-order service rule on fresh multinomial quality histories. All policies
share a quality realization, so differences are paired. The implementation uses
the recorded observed-capacity/grade prefix, not an unimplemented randomized coin.
"""
from hashlib import sha256
import math
import time
from backbone.round44_random_quality_counts import *

SEED51=2026102851
REPLICAS51=1024


def cash_from_stocks(loads,g1,g2,r,u,d):
    assert np.all(u<=np.minimum(np.maximum(g1-d[0],0.),np.maximum(d[1]-g2,0.))+EPS)
    sold1=np.minimum(g1,d[0])
    sold2=np.minimum(g2+u,d[1])
    extra1=np.maximum(g1-d[0]-u,0.)
    extra2=np.maximum(g2+u-d[1],0.)
    cost=loads[:,0]*MATERIAL_COST+np.sum(loads*MANUFACTURING_COSTS,axis=1)+5.5*r
    profit=120*sold1+60*sold2+90*extra1+30*extra2-cost
    met=(sold1>=d[0]-EPS)&(sold2>=d[1]-EPS)
    return mean(profit),mean(met)


def main():
    started=time.perf_counter()
    source=json.loads((SERVICE_OUT/"round50.json").read_text(encoding="utf-8"))
    case=source["rows"][0]
    rule=next(row for row in case["frontier"] if row["target"]==.9)
    assert rule["feasible"] and rule["boundary"] is not None
    q1,q2=source["grade_shares"]
    f=source["eligible_fraction"]
    d=tuple(source["demands"])
    flow=forward(case["input"])
    n=np.floor(flow.finished+1e-9).astype(int)
    spare=np.maximum(CAPS[:,1]-flow.loads[:,1]-350.,0.)
    order=np.argsort(-PROB,kind="stable")
    ranks=np.empty(len(PROB),dtype=int)
    ranks[order]=np.arange(len(PROB))
    boundary=rule["boundary"]
    boundary_gap=rule["boundary_substitution_gap"]
    rng=np.random.default_rng(SEED51)
    values={label:{"profit":[],"service":[]} for label in ("none","mandatory","deterministic_service_rule")}
    for replica in range(REPLICAS51):
        counts=rng.multinomial(n,(q1,f*q2,(1-f)*q2,1-q1-q2))
        a=counts[:,0]
        b=counts[:,1]+counts[:,2]
        r=np.minimum.reduce((np.maximum(b-d[1],0.),counts[:,1].astype(float),spare))
        g1=a+.97*r
        g2=b-r
        k=np.maximum(d[1]-b,0.)
        can_complete=(k>0)&(a>=d[0]+k)
        prefix=(ranks<boundary["capacity_position"])|((ranks==boundary["capacity_position"])&(a<=boundary["grade1_count"]))
        choose=can_complete&((k<boundary_gap)|((k==boundary_gap)&prefix))
        us={"none":np.zeros(len(PROB)),
            "mandatory":np.minimum(np.maximum(g1-d[0],0.),np.maximum(d[1]-g2,0.)),
            "deterministic_service_rule":np.where(choose,k,0.)}
        for label,u in us.items():
            profit,service=cash_from_stocks(flow.loads,g1,g2,r,u,d)
            values[label]["profit"].append(profit)
            values[label]["service"].append(service)
    exact={"none":{"profit":case["profit_best_no_substitution"]["expected_profit"],"service":case["profit_best_no_substitution"]["fulfilment_probability"]},
           "mandatory":{"profit":case["mandatory_substitution"]["expected_profit"],"service":case["maximum_fulfilment_probability"]},
           "deterministic_service_rule":{"profit":rule["deterministic_feasible_profit"],"service":rule["deterministic_service"]}}
    radius=math.sqrt(float((PROB**2).sum())*math.log(2*len(values)/.05)/(2*REPLICAS51))
    rows=[]
    for label,v in values.items():
        p,s=estimate(v["profit"]),estimate(v["service"])
        interval=[max(0.,s["estimate"]-radius),min(1.,s["estimate"]+radius)]
        assert interval[0]<=exact[label]["service"]<=interval[1]
        assert abs(p["estimate"]-exact[label]["profit"])<=5*p["standard_error"]+1e-7
        rows.append({"policy":label,"exact":exact[label],"MC_profit":p,"MC_service":s,
                     "simultaneous_hoeffding_service_interval":interval})
    trace=SERVICE_OUT/"round51_replica_values.npz"
    np.savez_compressed(trace,**{label+"_"+key:np.array(value) for label,v in values.items() for key,value in v.items()})
    save_service(51,{"question":"Does the recorded deterministic quality/capacity substitution threshold execute as predicted?",
        "assumptions":__doc__,"seed":SEED51,"replicas":REPLICAS51,"input":case["input"],
        "target":.9,"family_error_probability":.05,"hoeffding_radius":radius,
        "trace":{"path":str(trace.relative_to(ROOT)),"sha256":sha256(trace.read_bytes()).hexdigest()},
        "headline":{"elapsed_seconds":time.perf_counter()-started,"policies":len(rows)},"rows":rows},__file__,
        (ROOT/"backbone"/"adaptive_substitution.py",ROOT/"backbone"/"exact_quality_economics.py",
         ROOT/"backbone"/"exact_quality_service.py",ROOT/"backbone"/"quality_lab.py",
         ROOT/"backbone"/"round44_random_quality_counts.py",ROOT/"backbone"/"round50_adaptive_substitution.py"))


if __name__=="__main__":
    main()
