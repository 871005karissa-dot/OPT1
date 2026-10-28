"""Round45: local input sensitivity with coupled random-quality replicas.

Fixed forward flow, same scenario as round44 roughness. Within each independent
replica, inputs are increased in order and extra finished items are assigned new
independent quality categories. This gives correct multinomial marginals and
shared product histories across input choices. Return actions follow inspection.
Paired intervals are normal approximations; this is a finite local comparison.
"""
from hashlib import sha256
import time
from backbone.round44_random_quality_counts import *

SEED45=2026102845
REPLICAS45=256


def main():
    started=time.perf_counter()
    quality=recoverability(APPENDIX_COMPONENT_PROBABILITIES)
    q1,q2=quality["implied_grade1_share"],quality["implied_grade2_share"]
    d=(750.,150.)
    f=quality["single_feature_bounds"][0]["single_feature_perfect_repair_upper_bound"]
    anchor=required_input(d,(q1,q2),STATIONS,1)
    offsets=np.array([-20.,-5.,-1.,-.1,0.,.1,1.,5.,20.])
    inputs=anchor+offsets
    flows=[forward(float(raw)) for raw in inputs]
    ns=[np.floor(flow.finished+1e-9).astype(int) for flow in flows]
    probabilities=(q1,f*q2,(1-f)*q2,1-q1-q2)
    service=np.empty((len(inputs),REPLICAS45))
    profit=np.empty_like(service)
    rng=np.random.default_rng(SEED45)
    for replica in range(REPLICAS45):
        counts=np.zeros((len(PROB),4),dtype=int)
        previous=np.zeros(len(PROB),dtype=int)
        for index,(flow,n) in enumerate(zip(flows,ns)):
            increment=n-previous
            assert np.all(increment>=0)
            counts+=rng.multinomial(increment,probabilities)
            previous=n
            stock=GradeStockFlow(flow.loads,flow.finished,counts[:,0].astype(float),(counts[:,1]+counts[:,2]).astype(float))
            action=choose_after_inspection(stock,d,counts[:,1])
            service[index,replica]=mean(action["met"])
            profit[index,replica]=mean(action["profit"])
    anchor_index=int(np.flatnonzero(offsets==0.)[0])
    rows=[]
    for index,(raw,flow,n) in enumerate(zip(inputs,flows,ns)):
        original=QualityFlow(flow.loads,flow.finished,q1,q2)
        floored=QualityFlow(flow.loads,n.astype(float),q1,q2)
        a=choose_after_inspection(original,d,f*original.g2)
        b=choose_after_inspection(floored,d,f*floored.g2)
        rows.append({"input":float(raw),"offset_from_grade1_onset":float(offsets[index]),
            "unrounded_fluid":summary(a),"same_floor_fluid":summary(b),
            "random_quality_service":estimate(service[index]),"random_quality_profit":estimate(profit[index]),
            "paired_service_difference_vs_onset":estimate(service[index]-service[anchor_index]),
            "paired_profit_difference_vs_onset":estimate(profit[index]-profit[anchor_index])})
    samples=SERVICE_OUT/"round45_replica_values.npz"
    np.savez_compressed(samples,inputs=inputs,service=service,profit=profit,seed=SEED45)
    save_service(45,{"question":"Is the fluid service jump at the mean grade1-onset input stable under small input changes?",
        "assumptions":__doc__,"seed":SEED45,"replicas":REPLICAS45,"demands":d,"grade_shares":[q1,q2],
        "eligible_fraction":f,"anchor_input":anchor,
        "replica_trace":{"path":str(samples.relative_to(ROOT)),"sha256":sha256(samples.read_bytes()).hexdigest()},
        "headline":{"elapsed_seconds":time.perf_counter()-started,"inputs":len(inputs)},"rows":rows},__file__,
        (ROOT/"backbone"/"quality_lab.py",ROOT/"backbone"/"round40_quality_recoverability.py",
         ROOT/"backbone"/"round44_random_quality_counts.py"))


if __name__=="__main__":
    main()
