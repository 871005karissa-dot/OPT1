"""Round54: train a deterministic startup-loss threshold, independently validate.

Known eta=.97, fixed input1333, F10000 and workload350 remain hypothetical.
No setup and full eligible return are the exact two recourse choices. If paying
setup rescues a whole order, its profit sacrifice is loss=F-gain. Train a scalar
loss threshold using weighted quality samples; include complete ties to obtain
a deterministic rule. Target .85, training buffer .006 chosen in advance.
Independent validation controls service simulation error; the sample covering
bound is not a population optimality certificate.
"""
from hashlib import sha256
import math
import time
from backbone.round44_random_quality_counts import *

RAW=1333.
FEE=10000.
TARGET=.85
TRAINING_TARGET=.856
TRAINING_REPLICAS=512
VALIDATION_REPLICAS=2048
TRAINING_SEED=2026102854
VALIDATION_SEED=2026102954


def sample_actions(rng,flow,ns,spare,probabilities,d):
    counts=rng.multinomial(ns,probabilities)
    stock=GradeStockFlow(flow.loads,flow.finished,counts[:,0].astype(float),
                        (counts[:,1]+counts[:,2]).astype(float))
    cap=np.minimum.reduce((np.maximum(stock.g2-d[1],0.),counts[:,1].astype(float),spare))
    zero=evaluate_quality(stock,d,np.zeros(len(PROB)),.97)
    full=evaluate_quality(stock,d,cap,.97)
    gain=full["profit"]-zero["profit"]
    rescue=full["met"]&~zero["met"]
    baseline=(cap>EPS)&(gain>FEE+1e-8)
    return cap,zero,full,gain,rescue,baseline


def performance(activate,zero,full):
    p=np.where(activate,full["profit"]-FEE,zero["profit"])
    s=np.where(activate,full["met"],zero["met"])
    return mean(p),mean(s),mean(activate)


def main():
    started=time.perf_counter()
    source=json.loads((SERVICE_OUT/"round49.json").read_text(encoding="utf-8"))
    q1,q2=source["grade_shares"]
    f=source["eligible_fraction"]
    d=tuple(source["demands"])
    probabilities=(q1,f*q2,(1-f)*q2,1-q1-q2)
    flow=forward(RAW)
    ns=np.floor(flow.finished+1e-9).astype(int)
    spare=np.maximum(CAPS[:,1]-flow.loads[:,1]-350.,0.)
    rng=np.random.default_rng(TRAINING_SEED)
    histogram={}
    baseline_values=[]
    for replica in range(TRAINING_REPLICAS):
        cap,zero,full,gain,rescue,baseline=sample_actions(rng,flow,ns,spare,probabilities,d)
        baseline_values.append(performance(baseline,zero,full))
        eligible=(cap>EPS)&rescue&~baseline
        losses=np.round(np.maximum(FEE-gain[eligible],0.),8)
        unique,inverse=np.unique(losses,return_inverse=True)
        masses=np.bincount(inverse,weights=PROB[eligible]/TRAINING_REPLICAS,minlength=len(unique))
        for loss,mass in zip(unique,masses):
            histogram[float(loss)]=histogram.get(float(loss),0.)+float(mass)
    base=np.array(baseline_values).mean(axis=0)
    losses=np.array(sorted(histogram))
    masses=np.array([histogram[float(loss)] for loss in losses])
    cumulative=np.cumsum(masses)
    needed=TRAINING_TARGET-float(base[1])
    if needed<0 or needed>float(cumulative[-1]):
        raise RuntimeError("Predefined training target is outside the service tradeoff; do not silently change it.")
    j=int(np.searchsorted(cumulative,needed))
    threshold=float(losses[j])
    selected_mass=float(cumulative[j])
    training_service=float(base[1])+selected_mass
    loss=float(np.dot(losses[:j+1],masses[:j+1]))
    previous=float(cumulative[j-1]) if j else 0.
    fractional_loss=float(np.dot(losses[:j],masses[:j]))+threshold*(needed-previous)
    training_gap=loss-fractional_loss
    assert abs(training_gap-threshold*(training_service-TRAINING_TARGET))<1e-7
    rng=np.random.default_rng(VALIDATION_SEED)
    labels=("profit_best","trained_service_threshold","all_rescuable_orders")
    validation={label:[] for label in labels}
    for replica in range(VALIDATION_REPLICAS):
        cap,zero,full,gain,rescue,baseline=sample_actions(rng,flow,ns,spare,probabilities,d)
        rules=(baseline,baseline|((cap>EPS)&rescue&(FEE-gain<=threshold+5e-8)),
               baseline|((cap>EPS)&rescue))
        for label,activate in zip(labels,rules):
            validation[label].append(performance(activate,zero,full))
    radius=math.sqrt(float((PROB**2).sum())*math.log(2*len(labels)/.05)/(2*VALIDATION_REPLICAS))
    rows=[]
    for label in labels:
        values=np.array(validation[label])
        p,s,a=(estimate(values[:,j]) for j in range(3))
        interval=[max(0.,s["estimate"]-radius),min(1.,s["estimate"]+radius)]
        rows.append({"policy":label,"profit":p,"service":s,"activation_probability":a,
                     "simultaneous_hoeffding_service_interval":interval,
                     "service_lower_bound_meets_85_percent":interval[0]>=TARGET})
    selected=np.array(validation[labels[1]])
    baseline=np.array(validation[labels[0]])
    all_rescue=np.array(validation[labels[2]])
    trace=SERVICE_OUT/"round54_validation_values.npz"
    np.savez_compressed(trace,**{label:np.array(values) for label,values in validation.items()})
    save_service(54,{"question":"Can a sample-selected deterministic rework-start policy meet a service floor on independent quality draws?",
        "assumptions":__doc__,"input":RAW,"setup_fee":FEE,"target":TARGET,
        "training":{"seed":TRAINING_SEED,"replicas":TRAINING_REPLICAS,"target_with_buffer":TRAINING_TARGET,
            "loss_threshold":threshold,"deterministic_service":training_service,
            "expected_profit":float(base[0])-loss,"sample_randomized_covering_profit_gap":training_gap,
            "loss_group_count":len(histogram)},
        "validation":{"seed":VALIDATION_SEED,"replicas":VALIDATION_REPLICAS,
            "family_error_probability":.05,"hoeffding_radius":radius},
        "paired_profit_difference_vs_profit_best":estimate(selected[:,0]-baseline[:,0]),
        "paired_profit_gain_vs_all_rescuable":estimate(selected[:,0]-all_rescue[:,0]),
        "trace":{"path":str(trace.relative_to(ROOT)),"sha256":sha256(trace.read_bytes()).hexdigest()},
        "headline":{"elapsed_seconds":time.perf_counter()-started,"threshold":threshold,"validated_policies":len(rows)},"rows":rows},__file__,
        (ROOT/"backbone"/"quality_lab.py",ROOT/"backbone"/"round44_random_quality_counts.py"))


if __name__=="__main__":
    main()
