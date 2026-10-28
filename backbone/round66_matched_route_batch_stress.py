"""Round66: stress the selected canonical policy against initial batch variation.

Freeze I1495 and round63's deterministic75% policy, fully committed material.
Only change initial quality to mean-preserving Dirichlet-multinomial kappa
1000/100/10, keeping future repair successes independent binomial eta=.97.
Also retune the setup threshold at the SAME input, and calculate a perfect,
free unlimited-repair bound over all inputs. Hypothetical kappa, not fitted.
"""
import gc
import math
import time
from backbone.batch_stochastic_setup import *


def brute(n,q1,q2,f,kappa,d,cap):
    pp=np.array([q1,q2*f,q2*(1-f),1-q1-q2])
    alpha=kappa*pp
    revenue=service=returned=0.
    joint=np.zeros((n+1,cap+1))
    normal=math.lgamma(kappa)-math.lgamma(kappa+n)+math.lgamma(n+1)
    for a in range(n+1):
      for e in range(n-a+1):
       for other in range(n-a-e+1):
        cc=(a,e,other,n-a-e-other)
        mass=math.exp(normal+sum(math.lgamma(k+x)-math.lgamma(x)-math.lgamma(k+1) for k,x in zip(cc,alpha)))
        b=e+other
        r=min(e,max(b-d[1],0),cap)
        joint[a,r]+=mass
        returned+=mass*r
        for y in range(r+1):
            p=math.comb(r,y)*.97**y*.03**(r-y)
            h,l=a+y,b-r
            sub=min(max(h-d[0],0),max(d[1]-l,0))
            cash=120*min(h,d[0])+60*min(l+sub,d[1])+90*max(h-d[0]-sub,0)+30*max(l+sub-d[1],0)-12.4*r
            revenue+=mass*p*cash
            service+=mass*p*(h>=d[0] and l+sub>=d[1])
    return joint,revenue,service,returned


def main():
    started=time.perf_counter()
    checks=[]
    for kappa in (10.,100.,1000.):
        small=BatchStochasticSetup(.5,.3,.25,(5,2),kappa,maximum=18)
        for n in (8,12,18):
          for cap in (0,2,9):
            independent,rev,service,returned=brute(n,.5,.3,.25,kappa,(5,2),cap)
            exact_joint=np.zeros_like(independent)
            for a in range(n+1):
                law=small.unbounded_return_law(n-a)
                limit=min(cap,len(law)-1)
                exact_joint[a,:limit]=small.a.pmf[n,a]*law[:limit]
                exact_joint[a,limit]=small.a.pmf[n,a]*float(law[limit:].sum())
            metrics=small.metrics(n,cap)
            errors=[float(np.max(np.abs(independent-exact_joint))),abs(rev-metrics["net_revenue"]),
                    abs(service-metrics["service"]),abs(returned-metrics["expected_rework"])]
            assert errors[0]<1e-10 and max(errors[1:])<1e-8,(kappa,n,cap,errors)
            checks.append(errors)
        release_integer_caches(small)
        StochasticSetupFrontier.unbounded_return_law.cache_clear()
        del small
        gc.collect()
    prior=json.loads((SERVICE_OUT/"round63.json").read_text(encoding="utf-8"))
    chosen=next(x for x in prior["solutions"] if x["material_basis"]=="fully_committed" and x["target"]==.75)
    raw=chosen["best_deterministic_input"]
    q1,q2=prior["grade_shares"]
    f=prior["eligible_fraction"]
    nmax=np.floor(forward(100000.).finished+1e-9).astype(int)
    ns,inverse=np.unique(nmax,return_inverse=True)
    weights=np.bincount(inverse,weights=PROB,minlength=len(ns))
    flow=forward(float(raw))
    extra_commitment=MATERIAL_COST*(raw-mean(flow.loads[:,0]))
    rows=[]
    for kappa in (1000.,100.,10.):
        solver=BatchStochasticSetup(q1,q2,f,tuple(prior["demands"]),kappa)
        states=solver.state_masses(float(raw),0.)
        states["base_profit"]-=extra_commitment
        opened=execute_prefix(states["A"],states["R"],solver,2000.,chosen["boundary"])
        frozen=summarize_choice(states,opened,2000.)
        retuned=solve_setup_frontier(states,2000.,(.75,))
        direct=solver.evaluate_integer(float(raw))
        difference=abs(direct["fulfilment_probability"]-retuned["maximum_service"])
        assert difference<1e-9,(kappa,difference)
        bound=BatchRepairabilityBound(q1,q2,f,tuple(prior["demands"]),kappa)
        upper=float(weights@np.array([bound.probability(int(n)) for n in ns]))
        rows.append({"kappa":kappa,"within_batch_correlation":1/(kappa+1),"input":raw,
            "frozen_policy":frozen,"retuned_at_same_input":retuned,
            "perfect_unlimited_repair_upper_bound_all_inputs":upper,
            "direct_full_return_service_difference":difference,
            "initial_tables_max_mass_error":max(t.largest_mass_error for t in
                (solver.a,solver.b,solver.e,solver.marginal_eligible,solver.other_given_eligible))})
        release_integer_caches(solver)
        StochasticSetupFrontier.unbounded_return_law.cache_clear()
        NestedQualityBound.probability.cache_clear()
        del solver,states,bound
        gc.collect()
    save_service(66,{"question":"Does the selected matched-route service policy survive mean-preserving batch-quality variation?",
        "assumptions":__doc__,"iid_reference":chosen,
        "headline":{"small_DM_plus_success_brute_cases":len(checks),
                    "max_joint_mass_error":max(x[0] for x in checks),"max_revenue_error":max(x[1] for x in checks),
                    "max_service_error":max(x[2] for x in checks),"max_return_error":max(x[3] for x in checks),
                    "batch_cases":len(rows),"elapsed_seconds":time.perf_counter()-started},"rows":rows},__file__,
        (ROOT/"backbone"/"batch_stochastic_setup.py",ROOT/"backbone"/"stochastic_setup_frontier.py",
         ROOT/"backbone"/"integer_rework.py",ROOT/"backbone"/"exact_batch_quality.py",
         ROOT/"backbone"/"exact_quality_economics.py",ROOT/"backbone"/"exact_quality_service.py",
         ROOT/"backbone"/"round59_repairability_ceiling.py",SERVICE_OUT/"round63.json"))


if __name__=="__main__":
    main()
