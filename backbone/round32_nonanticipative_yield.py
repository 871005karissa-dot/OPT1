"""Round 32: choose forward/rework amounts before batch upgrade yield is revealed.

Three hypothetical batch-yield scenarios are independent of machine availability.
Capacity is observed first. The same x,r must be used for all future eta outcomes.
The clairvoyant policy is an information upper bound, not an implementable policy.
"""
import time
from backbone.recourse_lab import *

ETAS = (0.15,0.35,0.55)
WEIGHTS = (0.25,0.5,0.25)
MEAN_ETA = round(sum(eta*weight for eta,weight in zip(ETAS,WEIGHTS)),12)
SETUP = 350.0


def across_yields(flow,demands,r,etas=ETAS,weights=WEIGHTS):
    result = None
    for eta,weight in zip(etas,weights):
        action = evaluate(flow,demands,r,eta)
        if result is None:
            result = {key:weight*value for key,value in action.items()}
        else:
            for key in result:
                result[key] += weight*action[key]
    return result


def choose_nonanticipative(raw,demands,etas=ETAS,weights=WEIGHTS):
    best = None
    chosen = np.zeros(len(PROB))
    upper = forward(raw).loads[:,1]
    points = forward_candidates(raw,demands,etas+(MEAN_ETA,),SETUP)
    candidates = 0
    for x in points:
        fraction = np.where(np.abs(x-upper)<1e-10,0.0,fraction_for_work(x))
        flow = forward(raw,fraction)
        cap = available_returns(flow,demands,SETUP)
        gap = np.maximum(demands[0]-flow.g1,0.0)
        knots = [np.zeros(len(PROB)),cap]
        knots += [np.minimum(cap,gap/eta) for eta in sorted(set(etas+(MEAN_ETA,)))]
        for r in np.sort(np.stack(knots),axis=0):
            candidate = across_yields(flow,demands,r,etas,weights)
            candidates += 1
            if best is None:
                best = candidate
                chosen[:] = fraction
            else:
                best,improve = pick(best,candidate)
                chosen = np.where(improve,fraction,chosen)
    chosen_flow = forward(raw,chosen)
    used = best["sent"]+SETUP*(best["sent"]>EPS)
    assert np.all(used<=CAPS[:,1]-chosen_flow.loads[:,1]+EPS)
    return best,chosen,candidates


def main():
    started = time.perf_counter()
    rows = []
    distributions = (("symmetric",ETAS,WEIGHTS),("skewed",(0.05,0.2,0.8),(0.25,0.4375,0.3125)))
    for label,etas,weights in distributions:
      assert abs(sum(eta*weight for eta,weight in zip(etas,weights))-MEAN_ETA)<1e-12
      for demands in ((550.,350.),(650.,250.),(700.,200.),(750.,150.)):
        raw = release(demands)
        mean_policy,mean_b,_ = exact_capacity_policy(raw,demands,MEAN_ETA,SETUP)
        mean_actual = across_yields(forward(raw,mean_b),demands,mean_policy["sent"],etas,weights)
        aware,_,n = choose_nonanticipative(raw,demands,etas,weights)
        oracle = None
        for eta,weight in zip(etas,weights):
            action,_,_ = exact_capacity_policy(raw,demands,eta,SETUP)
            if oracle is None:
                oracle = {key:weight*value for key,value in action.items()}
            else:
                for key in oracle:
                    oracle[key] += weight*action[key]
        assert np.all(aware["profit"] >= mean_actual["profit"]-1e-6)
        assert np.all(oracle["profit"] >= aware["profit"]-1e-6)
        assert np.all(mean_policy["profit"] >= mean_actual["profit"]-1e-6)
        rows.append({"distribution":label,"demands":demands,"input":raw,"mean_eta_policy_predicted":summary(mean_policy),
                     "mean_eta_policy_actual":summary(mean_actual),"nonanticipative":summary(aware),
                     "clairvoyant_information_bound":summary(oracle),
                     "gain_vs_mean_eta_policy":mean(aware["profit"]-mean_actual["profit"]),
                     "mean_eta_optimism":mean(mean_policy["profit"]-mean_actual["profit"]),
                     "value_of_perfect_yield_information":mean(oracle["profit"]-aware["profit"]),
                     "forward_return_vertex_pairs_checked":n})
    save(32,{"question":"Does knowing an upgrade-yield distribution differ from pretending its realization is known?",
             "assumptions":__doc__,"distributions":[{"label":label,"etas":etas,"weights":weights} for label,etas,weights in distributions],"mean_eta":MEAN_ETA,
             "setup_workload":SETUP,"distribution_is_hypothetical":True,
             "optimality_scope":"Piecewise-linear vertices of the fluid fixed-release capacity-allocation model; exact probabilities for the specified three-point distribution, not a claim about an unknown real-world yield distribution.",
             "headline":{"elapsed_seconds":time.perf_counter()-started,"joint_capacity_yield_outcomes":len(PROB)*len(ETAS),
                         "rows":rows},"rows":rows},__file__)


if __name__=="__main__":
    main()
