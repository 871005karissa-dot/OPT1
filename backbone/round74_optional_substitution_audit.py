"""Round74: isolate the fixed automatic-substitution restriction.

Freeze EACH input chosen for the three baseline classes in round73, then allow
optional downward allocation. Only that decision rule is relaxed. This is a
fixed-input sensitivity test, not reoptimization of input under the new model.
Setup decisions precede success. B<D2 states cannot rework, so optional
substitution cost bands can be merged with setup trades without future leakage.
"""
import gc
import math
import time
from backbone.joint_fulfilment_frontier import *
from backbone.round61_stochastic_setup_frontier import brute_fractional_policy


def direct_sub_summary(n,q1,q2,d):
    masses=np.zeros(d[1])
    total=0.
    for a in range(n+1):
      for b in range(n-a+1):
        z=n-a-b
        p=math.factorial(n)/math.factorial(a)/math.factorial(b)/math.factorial(z)*q1**a*q2**b*(1-q1-q2)**z
        k=d[1]-b
        total+=p*min(max(a-d[0],0),max(k,0))
        if k>0 and a>=d[0]+k:
            masses[k-1]+=p
    return total,masses


def main():
    started=time.perf_counter()
    core=StochasticSetupFrontier(.5,.3,.25,(5,2),maximum=12)
    pool=SubstitutionPool(core)
    errors=[]
    for n in (6,8,12):
        expected,mass=direct_sub_summary(n,.5,.3,(5,2))
        actual=pool.aggregate([n],[1.])
        error=max(abs(expected-actual["expected_automatic_substitution"]),float(np.max(np.abs(mass-actual["mass"]))))
        errors.append(error)
        assert error<1e-10
    losses=np.array([5.,12.,30.,60.,80.,100.])
    masses=np.array([.1,.12,.16,.14,.18,.1])
    benefits=np.array([.2,.7,1.,1.,.9,.95])
    toy={"A":np.arange(6),"R":np.ones(6),"mass":masses,"gain":200-losses,
         "benefit":benefits,"base_profit":1000.,"base_service":.1}
    lp_errors=[]
    order=np.argsort(losses/benefits,kind="stable")
    for target in (.25,.4,.6):
        result=cover_actions(masses,losses,benefits,order,target-.1)
        independent,integer=brute_fractional_policy(toy,200.,target)
        error=abs(1000-result["random_loss"]-independent)
        lp_errors.append(error)
        assert error<1e-8
        assert 1000-result["deterministic_loss"]<=integer+1e-8
        assert integer-(1000-result["deterministic_loss"])<=result["deterministic_loss"]-result["random_loss"]+1e-8
    release_integer_caches(core)
    StochasticSetupFrontier.unbounded_return_law.cache_clear()
    AdaptiveSubstitution.expected_substitution.cache_clear()
    prior=json.loads((SERVICE_OUT/"round73.json").read_text(encoding="utf-8"))
    params=json.loads((SERVICE_OUT/"round63.json").read_text(encoding="utf-8"))
    q1,q2=params["grade_shares"]
    rows=[]
    for case in prior["cases"]:
        d=tuple(case["demands"])
        core=StochasticSetupFrontier(q1,q2,params["eligible_fraction"],d)
        pool=SubstitutionPool(core)
        choices=[("selective",case["proposed_feasible"]),("always",case["always_return_best"])]
        if case["no_repair_best"] is not None:
            choices.append(("none",case["no_repair_best"]))
        for mode,reference in choices:
            raw=reference["input"]
            flow=forward(float(raw))
            ns=np.floor(flow.finished+1e-9).astype(int)
            unique,inverse=np.unique(ns,return_inverse=True)
            weights=np.bincount(inverse,weights=PROB,minlength=len(unique))
            sub=pool.aggregate(unique,weights)
            states=core.state_masses(float(raw),0.)
            states["base_profit"]-=MATERIAL_COST*(raw-mean(flow.loads[:,0]))
            result=joint_frontier(states,sub,pool,ns,2000.,(case["target"],),mode)
            item=result["frontier"][0]
            assert item["feasible"]
            simple_profit=reference["expected_profit"]+30*sub["partial_unfulfillable_substitution"]
            randomized=item["randomized_optimum"]["expected_profit"]
            assert randomized>=simple_profit-1e-7,(d,raw,mode,randomized,simple_profit)
            candidates=(item["deterministic_feasible"]["expected_profit"],simple_profit)
            best=max(candidates)
            rows.append({"demands":d,"target":case["target"],"frozen_input":raw,"mode":mode,
                "automatic_reference_profit":reference["expected_profit"],
                "complete_only_reference_profit":simple_profit,
                "best_feasible_profit_at_this_input":best,
                "best_feasible_rule":"merged_threshold" if candidates[0]>=candidates[1] else "original_setup_complete_only_substitution",
                "gap_against_randomized_bound":max(0.,randomized-best),
                "gain_vs_automatic_same_input":best-reference["expected_profit"],"joint_frontier":result})
        release_integer_caches(core)
        StochasticSetupFrontier.unbounded_return_law.cache_clear()
        AdaptiveSubstitution.expected_substitution.cache_clear()
        del core,pool
        gc.collect()
    save_service(74,{"question":"Does forcing automatic downward substitution materially affect the economic comparisons?",
        "assumptions":__doc__,"structural_argument":__import__("backbone.joint_fulfilment_frontier",fromlist=["__doc__"]).__doc__,
        "headline":{"small_joint_quality_summary_checks":len(errors),"max_summary_error":max(errors),
                    "independent_six_action_LP_vertex_checks":len(lp_errors),"max_LP_error":max(lp_errors),
                    "frozen_input_variant_cases":len(rows),"elapsed_seconds":time.perf_counter()-started},"rows":rows},__file__,
        (ROOT/"backbone"/"joint_fulfilment_frontier.py",ROOT/"backbone"/"adaptive_substitution.py",
         ROOT/"backbone"/"stochastic_setup_frontier.py",ROOT/"backbone"/"integer_rework.py",
         ROOT/"backbone"/"exact_quality_economics.py",ROOT/"backbone"/"exact_quality_service.py",
         ROOT/"backbone"/"round61_stochastic_setup_frontier.py",ROOT/"backbone"/"exact_batch_quality.py",SERVICE_OUT/"round73.json"))


if __name__=="__main__":
    main()
