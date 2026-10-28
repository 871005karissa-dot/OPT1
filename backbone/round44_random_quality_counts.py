"""Round44: random grade/repairable-subtype counts, fixed forward flow.

Choose raw release ex ante; machine capacities determine forward flow before
quality is revealed. Inspect grades/subtypes, then choose return quantity.
Enumerate C exactly; use independent multinomial quality replicas conditional
on each C. Upgrade eta=.97 is still a known fluid fraction, not random Bernoulli
rework success. This is a hybrid uncertainty experiment, not an integer schedule.
Floored finished counts and the same-floor fluid benchmark isolate rounding.
Monte Carlo intervals quantify numerical sampling error, not empirical uncertainty.
"""
import math
import time
from backbone.quality_lab import *
from backbone.round40_quality_recoverability import recoverability
from backbone.ball_screw import APPENDIX_COMPONENT_PROBABILITIES

REPLICAS=256
SEED=2026102844
ETA=.97
SETUP=350.


def choose_after_inspection(flow,d,eligible):
    cap=np.minimum(np.minimum(np.maximum(flow.g2-d[1],0.),eligible),
                   np.maximum(CAPS[:,1]-flow.loads[:,1]-SETUP,0.))
    gap=np.maximum(d[0]-flow.g1,0.)
    best=evaluate(flow,d)
    for r in np.sort(np.stack((np.zeros(len(PROB)),cap,np.minimum(cap,gap/ETA))),axis=0):
        best,_=pick(best,evaluate_quality(flow,d,r,ETA))
    return best


def estimate(values):
    values=np.asarray(values,dtype=float)
    average=float(values.mean())
    se=float(values.std(ddof=1)/math.sqrt(len(values)))
    return {"estimate":average,"standard_error":se,
            "normal_approximation_95_interval":[average-1.95996398454*se,average+1.95996398454*se],
            "replicas":len(values)}


def binomial_tail(n,p,threshold):
    if threshold<=0:
        return 1.
    if threshold>n:
        return 0.
    return sum(math.exp(math.lgamma(n+1)-math.lgamma(k+1)-math.lgamma(n-k+1)
                        +k*math.log(p)+(n-k)*math.log1p(-p)) for k in range(int(threshold),n+1))


def main():
    started=time.perf_counter()
    quality=recoverability(APPENDIX_COMPONENT_PROBABILITIES)
    q1,q2=quality["implied_grade1_share"],quality["implied_grade2_share"]
    rows=[]
    for case_index,(d,j) in enumerate(((d,j) for d in ((550.,350.),(750.,150.)) for j in (0,1))):
        raw=required_input(d,(q1,q2),STATIONS,1)
        feature=quality["single_feature_bounds"][j]
        f=feature["single_feature_perfect_repair_upper_bound"]
        original=forward(raw)
        continuous=QualityFlow(original.loads,original.finished,q1,q2)
        n=np.floor(original.finished+1e-9).astype(int)
        floored=QualityFlow(original.loads,n.astype(float),q1,q2)
        fluid=choose_after_inspection(continuous,d,f*continuous.g2)
        floor_fluid=choose_after_inspection(floored,d,f*floored.g2)
        probabilities=(q1,f*q2,(1-f)*q2,1-q1-q2)
        assert abs(sum(probabilities)-1)<1e-12
        rng=np.random.default_rng(SEED+case_index)
        values={key:[] for key in ("profit","met","sent","short1","short2","no_return_grade1_service")}
        for replica in range(REPLICAS):
            counts=rng.multinomial(n,probabilities)
            assert np.all(counts.sum(axis=1)==n)
            sampled=GradeStockFlow(original.loads,original.finished,counts[:,0].astype(float),
                                  (counts[:,1]+counts[:,2]).astype(float))
            action=choose_after_inspection(sampled,d,counts[:,1])
            for key in ("profit","met","sent","short1","short2"):
                values[key].append(mean(action[key]))
            values["no_return_grade1_service"].append(mean(counts[:,0]>=d[0]))
        statistics={key:estimate(value) for key,value in values.items()}
        tails={int(k):binomial_tail(int(k),q1,int(d[0])) for k in np.unique(n)}
        exact=mean(np.array([tails[int(k)] for k in n]))
        diagnostic=statistics["no_return_grade1_service"]
        discrepancy=abs(diagnostic["estimate"]-exact)
        assert discrepancy<=5*diagnostic["standard_error"]+1e-10
        rows.append({"demands":d,"KQC_name":feature["KQC_name"],"input":raw,"eligible_fraction":f,
            "seed":SEED+case_index,"unrounded_fluid":summary(fluid),"same_floor_fluid":summary(floor_fluid),
            "random_quality":statistics,"exact_no_return_grade1_service":exact,
            "binomial_validation_absolute_error":discrepancy,
            "binomial_validation_error_in_standard_errors":discrepancy/diagnostic["standard_error"] if diagnostic["standard_error"] else 0.,
            "joint_quality_replica_capacity_outcomes":len(PROB)*REPLICAS,
            "expected_finished_integer_count":mean(n)})
        print(json.dumps({"case_done":d,"KQC":feature["KQC_name"],
                          "fluid_R":summary(floor_fluid)["fulfilment_probability"],
                          "MC_R":statistics["met"]},ensure_ascii=True),flush=True)
    save_service(44,{"question":"Do deterministic grade/subtype proportions overstate or understate whole-order fulfilment?",
        "assumptions":__doc__,"grade_shares":[q1,q2],"replicas":REPLICAS,"seed":SEED,
        "headline":{"elapsed_seconds":time.perf_counter()-started,"cases":len(rows),
                    "capacity_quality_replica_outcomes_per_case":len(PROB)*REPLICAS},"rows":rows},__file__,
        (ROOT/"backbone"/"quality_lab.py",ROOT/"backbone"/"round40_quality_recoverability.py"))


if __name__=="__main__":
    main()
