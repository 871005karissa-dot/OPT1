"""Round46: independent validation after selecting input from round45's sample.

Freeze a finite-grid policy using training-only normal service lower limits;
then use a fresh random stream for two fixed policies (onset and selected input).
For each validation replica and capacity state, quality draws are independent.
Weighted Hoeffding plus a union bound gives simultaneous two-sided intervals:
epsilon = sqrt(sum_s p_s^2 * log(2*m/delta)/(2*N)).
N is independent QUALITY REPLICAS PER CAPACITY STATE, not N*28224 unweighted
Bernoulli trials. Bounds address simulation error under the stated model only.
No continuous-input global optimum or empirical service guarantee is claimed.
"""
from hashlib import sha256
import math
import time
from backbone.round44_random_quality_counts import *

VALIDATION_REPLICAS=4096
VALIDATION_SEED=2026102846
FAMILY_ERROR=.05
TARGET=.75


def main():
    started=time.perf_counter()
    training=json.loads((SERVICE_OUT/"round45.json").read_text(encoding="utf-8"))
    candidates=[row for row in training["rows"]
                if row["random_quality_service"]["normal_approximation_95_interval"][0]>=TARGET]
    if not candidates:
        raise RuntimeError("No training candidate passes the stated selection rule; do not silently change it.")
    chosen=max(candidates,key=lambda row:row["random_quality_profit"]["estimate"])
    anchor=training["anchor_input"]
    selected=chosen["input"]
    inputs=sorted(set((anchor,selected)))
    assert VALIDATION_SEED!=training["seed"]
    d=tuple(training["demands"])
    q1,q2=training["grade_shares"]
    f=training["eligible_fraction"]
    probabilities=(q1,f*q2,(1-f)*q2,1-q1-q2)
    flows=[forward(raw) for raw in inputs]
    ns=[np.floor(flow.finished+1e-9).astype(int) for flow in flows]
    service=np.empty((len(inputs),VALIDATION_REPLICAS))
    profit=np.empty_like(service)
    rng=np.random.default_rng(VALIDATION_SEED)
    for replica in range(VALIDATION_REPLICAS):
        counts=np.zeros((len(PROB),4),dtype=int)
        previous=np.zeros(len(PROB),dtype=int)
        for j,(flow,n) in enumerate(zip(flows,ns)):
            counts+=rng.multinomial(n-previous,probabilities)
            previous=n
            stock=GradeStockFlow(flow.loads,flow.finished,counts[:,0].astype(float),
                                (counts[:,1]+counts[:,2]).astype(float))
            action=choose_after_inspection(stock,d,counts[:,1])
            service[j,replica]=mean(action["met"])
            profit[j,replica]=mean(action["profit"])
        if (replica+1)%1024==0:
            print(json.dumps({"validation_replicas_completed":replica+1},ensure_ascii=True),flush=True)
    sum_p2=float(np.sum(PROB**2))
    radius=math.sqrt(sum_p2*math.log(2*len(inputs)/FAMILY_ERROR)/(2*VALIDATION_REPLICAS))
    rows=[]
    for j,raw in enumerate(inputs):
        observed=estimate(service[j])
        lower=max(0.,observed["estimate"]-radius)
        upper=min(1.,observed["estimate"]+radius)
        rows.append({"input":raw,"role":"grade1_onset" if raw==anchor else "selected_on_training",
            "service":observed,"simultaneous_hoeffding_interval":[lower,upper],
            "hoeffding_radius":radius,"profit":estimate(profit[j]),
            "passes_75_percent_under_model":lower>=TARGET,
            "rejects_80_percent_under_model":upper<.80})
    selected_index=inputs.index(selected)
    anchor_index=inputs.index(anchor)
    trace=SERVICE_OUT/"round46_validation_values.npz"
    np.savez_compressed(trace,inputs=inputs,service=service,profit=profit,seed=VALIDATION_SEED)
    save_service(46,{"question":"Does the fluid-policy service claim survive independent quality scenarios, and can an input buffer meet a lower target?",
        "assumptions":__doc__,"training_round":45,"training_selection_rule":"Highest estimated profit among the nine local candidates whose training normal-approximation 95% service lower limit is at least .75; this rule is for candidate selection only.",
        "validation_seed":VALIDATION_SEED,"replicas_per_capacity_state":VALIDATION_REPLICAS,
        "family_error_probability":FAMILY_ERROR,"sum_squared_capacity_probabilities":sum_p2,
        "independent_validation_after_policy_selection":True,"selected_input":selected,"anchor_input":anchor,
        "paired_service_difference":estimate(service[selected_index]-service[anchor_index]),
        "paired_profit_difference":estimate(profit[selected_index]-profit[anchor_index]),
        "trace":{"path":str(trace.relative_to(ROOT)),"sha256":sha256(trace.read_bytes()).hexdigest()},
        "headline":{"elapsed_seconds":time.perf_counter()-started,"validated_policies":len(rows),
            "quality_capacity_outcomes":len(PROB)*VALIDATION_REPLICAS*len(inputs),"radius":radius},"rows":rows},__file__,
        (ROOT/"backbone"/"quality_lab.py",ROOT/"backbone"/"round40_quality_recoverability.py",
         ROOT/"backbone"/"round44_random_quality_counts.py",ROOT/"backbone"/"round45_threshold_stability.py"))


if __name__=="__main__":
    main()
