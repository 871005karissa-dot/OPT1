"""Round53: quality-aware rework setup charge creates an activation decision.

Fixed forward, independent item quality, known fluid eta=.97 and workload350.
Setup money F is hypothetical and charged only on positive return. Since both
active-return marginal profits are positive, the active optimum is its full cap;
compare it with no return. A preset service bonus lambda selects full return
when gain-F+lambda*(met_full-met_zero)>0. Lambda is a policy parameter/dual
weight, not a measured per-unit shortage penalty or a claim of frontier optimality.
Keep downward substitution mandatory to isolate this setup mechanism.
"""
import math
import time
from backbone.round44_random_quality_counts import *
from backbone.exact_quality_economics import ExactQualityEconomics

SEED53=2026102853
REPLICAS53=512
FEES=(0.,1000.,5000.,10000.)
BONUSES=(0.,1000.,2500.,10000.,20000.)


def main():
    started=time.perf_counter()
    ref=json.loads((SERVICE_OUT/"round49.json").read_text(encoding="utf-8"))
    q1,q2=ref["grade_shares"]
    f=ref["eligible_fraction"]
    d=tuple(ref["demands"])
    local=json.loads((SERVICE_OUT/"round46.json").read_text(encoding="utf-8"))
    inputs=(ref["best_unconstrained"]["input"],local["anchor_input"])
    exact=ExactQualityEconomics(q1,q2,f,d)
    rows=[]
    for case_index,raw in enumerate(inputs):
        flow=forward(raw)
        ns=np.floor(flow.finished+1e-9).astype(int)
        spare=np.maximum(CAPS[:,1]-flow.loads[:,1]-350.,0.)
        rng=np.random.default_rng(SEED53+case_index)
        measures=np.empty((len(FEES),len(BONUSES),REPLICAS53,4))
        for replica in range(REPLICAS53):
            counts=rng.multinomial(ns,(q1,f*q2,(1-f)*q2,1-q1-q2))
            stock=GradeStockFlow(flow.loads,flow.finished,counts[:,0].astype(float),
                                (counts[:,1]+counts[:,2]).astype(float))
            cap=np.minimum.reduce((np.maximum(stock.g2-d[1],0.),counts[:,1].astype(float),spare))
            zero=evaluate_quality(stock,d,np.zeros(len(PROB)),.97)
            full=evaluate_quality(stock,d,cap,.97)
            gain=full["profit"]-zero["profit"]
            service_gain=full["met"].astype(int)-zero["met"].astype(int)
            assert np.all(gain>=-1e-7) and np.all(service_gain>=0)
            for fi,fee in enumerate(FEES):
              for li,bonus in enumerate(BONUSES):
                activate=(cap>EPS)&(gain-fee+bonus*service_gain>1e-8)
                p=np.where(activate,full["profit"]-fee,zero["profit"])
                met=np.where(activate,full["met"],zero["met"])
                measures[fi,li,replica]=(mean(p),mean(met),mean(activate),mean(np.where(activate,cap,0.)))
            assert np.all(np.diff(measures[:,:,replica,1],axis=1)>=-1e-12)
            assert np.all(np.diff(measures[:,:,replica,0],axis=1)<=1e-7)
        reference=exact.evaluate_economics(raw)
        base_profit=estimate(measures[0,0,:,0])
        assert abs(base_profit["estimate"]-reference["expected_profit"])<=5*base_profit["standard_error"]+1e-7
        for fi,fee in enumerate(FEES):
          for li,bonus in enumerate(BONUSES):
            row={"input":raw,"setup_fee":fee,"service_bonus":bonus,"seed":SEED53+case_index,
                "profit":estimate(measures[fi,li,:,0]),"service":estimate(measures[fi,li,:,1]),
                "activation_probability":estimate(measures[fi,li,:,2]),"expected_rework":estimate(measures[fi,li,:,3]),
                "zero_fee_exact_reference":reference}
            rows.append(row)
        print(json.dumps({"input_completed":raw},ensure_ascii=True),flush=True)
    radius=math.sqrt(float((PROB**2).sum())*math.log(2*len(rows)/.05)/(2*REPLICAS53))
    for row in rows:
        s=row["service"]["estimate"]
        row["simultaneous_hoeffding_service_interval"]=[max(0.,s-radius),min(1.,s+radius)]
        if row["setup_fee"]==0.:
            assert abs(s-row["zero_fee_exact_reference"]["fulfilment_probability"])<=radius
    save_service(53,{"question":"Can a batch setup charge make service requirements change rework activation after quality is inspected?",
        "assumptions":__doc__,"parameters_are_hypothetical":True,"replicas":REPLICAS53,
        "family_error_probability":.05,"service_radius":radius,
        "scope":"Exact two-action recourse for each preset fee/bonus and observed quality realization; Monte Carlo expectation. Finite bonus grid is not the globally constrained frontier.",
        "headline":{"elapsed_seconds":time.perf_counter()-started,"policies":len(rows)},"rows":rows},__file__,
        (ROOT/"backbone"/"quality_lab.py",ROOT/"backbone"/"round44_random_quality_counts.py",
         ROOT/"backbone"/"exact_quality_economics.py",ROOT/"backbone"/"exact_quality_service.py"))


if __name__=="__main__":
    main()
