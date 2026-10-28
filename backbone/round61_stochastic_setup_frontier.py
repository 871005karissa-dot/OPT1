"""Round61: exact finite-law setup policies with unknown future repair outcomes.

Same candidate final-station route, input and normal/item-quality assumptions as
round58. Only add a hypothetical batch setup fee; no multi-period extension.
The service increment in a pre-success observed state is a binomial tail, not
an indicator. Fees/targets illustrate tradeoffs and are not measured settings.
"""
import math
import time
from itertools import product
from backbone.stochastic_setup_frontier import *


def brute_return_law(m,pe,po,d2):
    result=np.zeros(max(m-d2,0)+1)
    for e in range(m+1):
      for o in range(m-e+1):
        z=m-e-o
        mass=math.factorial(m)/math.factorial(e)/math.factorial(o)/math.factorial(z)*pe**e*po**o*(1-pe-po)**z
        r=min(e,max(e+o-d2,0))
        result[r]+=mass
    return result


def brute_fractional_policy(states,fee,target):
    """Independent LP vertex enumeration: all binary actions, one fractional."""
    n=len(states["mass"])
    best=-math.inf
    best_integer=-math.inf
    for bits in product((0.,1.),repeat=n):
        x=np.array(bits)
        candidate=summarize_choice(states,x,fee)
        if candidate["fulfilment_probability"]>=target-1e-12:
            best=max(best,candidate["expected_profit"])
            best_integer=max(best_integer,candidate["expected_profit"])
        for j in range(n):
            wb=states["mass"][j]*states["benefit"][j]
            if wb==0:
                continue
            z=x[j]+(target-candidate["fulfilment_probability"])/wb
            if -1e-12<=z<=1+1e-12:
                value=candidate["expected_profit"]+(z-x[j])*states["mass"][j]*(states["gain"][j]-fee)
                best=max(best,value)
    return best,best_integer


def main():
    started=time.perf_counter()
    small=StochasticSetupFrontier(.5,.3,.25,(8,2),maximum=18,eta=.6)
    law_errors=[]
    for m in range(19):
        exact=small.unbounded_return_law(m)
        independent=brute_return_law(m,.3*.25/.5,.3*.75/.5,2)
        law_errors.append(float(np.max(np.abs(exact-independent))))
        assert law_errors[-1]<1e-10
    aa=np.array([2,3,4,5,6,7,9,10])
    rr=np.array([7,6,8,5,4,2,3,1])
    gap=np.maximum(8-aa,0)
    toy={"A":aa,"R":rr,"mass":np.array([.08,.12,.17,.13,.15,.1,.15,.1]),
         "gain":(90*.6-30-small.unit_cost)*rr+30*mean_min(small.success,.6,rr,gap),
         "benefit":np.where(gap>0,small.success.tail[rr,gap],0.),"base_profit":1000.,"base_service":.1}
    lp_errors=[]
    det_gap_checks=[]
    for fee in (70.,140.,250.):
        initial=solve_setup_frontier(toy,fee,[])
        base,ceiling=initial["profit_best"]["fulfilment_probability"],initial["maximum_service"]
        targets=[base+x*(ceiling-base) for x in (0.,.3,.7,1.)]
        result=solve_setup_frontier(toy,fee,targets)
        for row in result["frontier"]:
            exact,det=brute_fractional_policy(toy,fee,row["target"])
            lp_errors.append(abs(exact-row["randomized_optimum"]["expected_profit"]))
            assert lp_errors[-1]<1e-8
            gap=det-row["deterministic_feasible"]["expected_profit"]
            assert -1e-8<=gap<=row["deterministic_gap_upper_bound"]+1e-8
            det_gap_checks.append(gap)
    release_integer_caches(small)
    StochasticSetupFrontier.unbounded_return_law.cache_clear()
    prior=json.loads((SERVICE_OUT/"round58.json").read_text(encoding="utf-8"))
    q1,q2=prior["grade_shares"]
    raw=prior["rows"][0]["input"]
    solver=StochasticSetupFrontier(q1,q2,prior["eligible_fraction"],tuple(prior["demands"]))
    states=solver.state_masses(raw,0.)
    zero_fee=solve_setup_frontier(states,0.,[])["profit_best"]
    expected=next(x for x in prior["rows"] if x["mode"]=="binomial" and x["setup_workload"]==0.)
    assert abs(zero_fee["expected_profit"]-expected["expected_profit"])<1e-7
    assert abs(zero_fee["fulfilment_probability"]-expected["fulfilment_probability"])<1e-10
    rows=[]
    for fee in (1000.,2000.,3000.):
        result=solve_setup_frontier(states,fee,(.7,.75,.78,.8))
        for row in result["frontier"]:
            if row["feasible"]:
                actual=execute_prefix(states["A"],states["R"],solver,fee,row["boundary"])
                replay=summarize_choice(states,actual,fee)
                assert abs(replay["expected_profit"]-row["deterministic_feasible"]["expected_profit"])<1e-7
                assert abs(replay["fulfilment_probability"]-row["deterministic_feasible"]["fulfilment_probability"])<1e-10
        rows.append(result)
    trace_path=SERVICE_OUT/"round61_states.npz"
    np.savez_compressed(trace_path,**states)
    save_service(61,{"question":"What setup/service policy is valid before random repair successes are revealed?",
        "assumptions":__doc__,"derivation":__import__("backbone.stochastic_setup_frontier",fromlist=["__doc__"]).__doc__,
        "input":raw,"setup_workload":0.,"grade_shares":[q1,q2],"eligible_fraction":prior["eligible_fraction"],
        "demands":prior["demands"],"eta":.97,"return_station":5,
        "headline":{"return_law_brute_cases":len(law_errors),"max_law_error":max(law_errors),
                    "independent_LP_vertex_cases":len(lp_errors),"max_LP_error":max(lp_errors),
                    "observed_AR_states":len(states["mass"]),"joint_mass_error":states["joint_mass_error"],
                    "elapsed_seconds":time.perf_counter()-started},
        "no_repair":{"expected_profit":states["base_profit"],"fulfilment_probability":states["base_service"]},
        "zero_fee_check":zero_fee,"trace":{"path":str(trace_path.relative_to(ROOT)),
            "sha256":sha256(trace_path.read_bytes()).hexdigest()},"rows":rows},__file__,
        (ROOT/"backbone"/"stochastic_setup_frontier.py",ROOT/"backbone"/"integer_rework.py",
         ROOT/"backbone"/"exact_quality_service.py",ROOT/"backbone"/"exact_quality_economics.py",
         ROOT/"backbone"/"round59_repairability_ceiling.py",SERVICE_OUT/"round58.json"))


if __name__=="__main__":
    main()
