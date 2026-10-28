"""Round52: same mean quality proportions, different within-batch correlation.

Exploratory Dirichlet-multinomial model: P~Dirichlet(kappa*q), then counts|P,C
~Multinomial(floor(finished(C)),P). P is drawn independently in each simulated
capacity stratum/replica; this is valid stratified integration of a quality law
independent of C. Items in one realized batch share P and are correlated.
All kappas are hypothetical, with no factory calibration. This is distinct from
correlation between machine states or correlation among KQCs of one product.
"""
import math
import time
from backbone.round44_random_quality_counts import *
from backbone.exact_quality_economics import ExactQualityEconomics

SEED52=2026102852
REPLICAS52=512


def main():
    started=time.perf_counter()
    earlier=json.loads((SERVICE_OUT/"round49.json").read_text(encoding="utf-8"))
    q1,q2=earlier["grade_shares"]
    f=earlier["eligible_fraction"]
    d=tuple(earlier["demands"])
    local=json.loads((SERVICE_OUT/"round46.json").read_text(encoding="utf-8"))
    inputs=(earlier["best_unconstrained"]["input"],local["selected_input"])
    probabilities=np.array((q1,f*q2,(1-f)*q2,1-q1-q2))
    solver=ExactQualityEconomics(q1,q2,f,d)
    rows=[]
    m=len(inputs)*4
    radius=math.sqrt(float((PROB**2).sum())*math.log(2*m/.05)/(2*REPLICAS52))
    for input_index,raw in enumerate(inputs):
      flow=forward(raw)
      ns=np.floor(flow.finished+1e-9).astype(int)
      mode_state=int(np.argmax(PROB))
      exact_independent=solver.evaluate_economics(raw)
      for kappa_index,kappa in enumerate((None,1000.,100.,10.)):
        seed=SEED52+input_index*10+kappa_index
        rng=np.random.default_rng(seed)
        values={key:[] for key in ("profit","service","grade1_count","grade1_in_mode_capacity_state")}
        for replica in range(REPLICAS52):
            ps=(probabilities if kappa is None else rng.dirichlet(kappa*probabilities,size=len(PROB)))
            counts=rng.multinomial(ns,ps)
            stock=GradeStockFlow(flow.loads,flow.finished,counts[:,0].astype(float),
                                (counts[:,1]+counts[:,2]).astype(float))
            action=choose_after_inspection(stock,d,counts[:,1])
            values["profit"].append(mean(action["profit"]))
            values["service"].append(mean(action["met"]))
            values["grade1_count"].append(mean(counts[:,0]))
            values["grade1_in_mode_capacity_state"].append(float(counts[mode_state,0]))
        stats={key:estimate(value) for key,value in values.items() if key!="grade1_in_mode_capacity_state"}
        expected_mean=mean(ns)*q1
        assert abs(stats["grade1_count"]["estimate"]-expected_mean)<=5*stats["grade1_count"]["standard_error"]+1e-8
        observed=stats["service"]["estimate"]
        interval=[max(0.,observed-radius),min(1.,observed+radius)]
        if kappa is None:
            assert interval[0]<=exact_independent["fulfilment_probability"]<=interval[1]
        n=int(ns[mode_state])
        theoretical_variance=n*q1*(1-q1)*(1. if kappa is None else (n+kappa)/(1+kappa))
        rows.append({"input":raw,"kappa":kappa,"independent_item_quality":kappa is None,
            "within_batch_same_category_indicator_correlation":0. if kappa is None else 1/(kappa+1),
            "seed":seed,"statistics":stats,"simultaneous_hoeffding_service_interval":interval,
            "expected_grade1_count":expected_mean,"independent_item_exact_reference":exact_independent,
            "mode_capacity_state":{"counts":COUNTS[mode_state].tolist(),"finished_count":n,
                "theoretical_grade1_count_variance":theoretical_variance,
                "sample_grade1_count_variance":float(np.var(values["grade1_in_mode_capacity_state"],ddof=1))}})
        print(json.dumps({"input":raw,"kappa":kappa,"MC_service":observed},ensure_ascii=True),flush=True)
    save_service(52,{"question":"Are policies optimized under independent item quality robust to batch-level quality variation with the same means?",
        "assumptions":__doc__,"grade_shares":[q1,q2],"eligible_fraction":f,"replicas":REPLICAS52,
        "same_mean_proportions_for_all_kappas":True,"family_error_probability":.05,"service_radius":radius,
        "headline":{"elapsed_seconds":time.perf_counter()-started,"cases":len(rows)},"rows":rows},__file__,
        (ROOT/"backbone"/"quality_lab.py",ROOT/"backbone"/"round44_random_quality_counts.py",
         ROOT/"backbone"/"exact_quality_economics.py",ROOT/"backbone"/"exact_quality_service.py"))


if __name__=="__main__":
    main()
