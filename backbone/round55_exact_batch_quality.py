"""Round55: exact batch-correlated quality benchmark, not a new sampling run."""
import gc
import math
import time
from backbone.exact_batch_quality import *


def brute(n,q1,q2,f,d,spare,kappa,eta=.97):
    qs=(q1,q2*f,q2*(1-f),1-q1-q2)
    alphas=[kappa*q for q in qs]
    service=revenue=sent=0.
    for a in range(n+1):
      for e in range(n-a+1):
       for other in range(n-a-e+1):
        counts=(a,e,other,n-a-e-other)
        logmass=math.lgamma(n+1)-sum(math.lgamma(k+1) for k in counts)
        logmass+=math.lgamma(kappa)-math.lgamma(kappa+n)
        logmass+=sum(math.lgamma(alpha+k)-math.lgamma(alpha) for alpha,k in zip(alphas,counts))
        mass=math.exp(logmass)
        b=e+other
        r=min(max(b-d[1],0.),e,spare)
        g1,g2=a+eta*r,b-r
        sub=min(max(g1-d[0],0.),max(d[1]-g2,0.))
        value=120*min(g1,d[0])+60*min(g2+sub,d[1])+90*max(g1-d[0]-sub,0.)+30*max(g2+sub-d[1],0.)-5.5*r
        revenue+=mass*value
        sent+=mass*r
        service+=mass*(g1>=d[0]-EPS and g2+sub>=d[1]-EPS)
    return service,revenue,sent


def main():
    started=time.perf_counter()
    errors=[]
    for q1,q2,f in ((.5,.3,.2),(.625,.254,.397)):
     for kappa in (10.,100.,1000.):
      for d in ((5,3),(8,2)):
        solver=ExactBatchQualityEconomics(q1,q2,f,d,kappa,maximum=18)
        for n in (8,12,18):
          for spare in (0.,1.5,4.,12.):
            s,p,r=brute(n,q1,q2,f,d,spare,kappa)
            exact_s=solver.conditional(n,spare)
            exact_p,exact_r=solver.net_revenue_and_return(n,spare)
            error=(abs(s-exact_s),abs(p-exact_p),abs(r-exact_r))
            assert error[0]<1e-10 and error[1]<2e-8 and error[2]<1e-10,error
            errors.append(error)
        clear_solver_caches(solver)
    previous=json.loads((SERVICE_OUT/"round52.json").read_text(encoding="utf-8"))
    q1,q2=previous["grade_shares"]
    f=previous["eligible_fraction"]
    rows=[]
    for kappa in (None,1000.,100.,10.):
        solver=(ExactQualityEconomics(q1,q2,f,(750,150)) if kappa is None else
                ExactBatchQualityEconomics(q1,q2,f,(750,150),kappa))
        for old in [row for row in previous["rows"] if row["kappa"]==kappa]:
            exact=solver.evaluate_economics(old["input"])
            interval=old["simultaneous_hoeffding_service_interval"]
            assert interval[0]<=exact["fulfilment_probability"]<=interval[1]
            p=old["statistics"]["profit"]
            error=abs(exact["expected_profit"]-p["estimate"])
            assert error<=5*p["standard_error"]+1e-7
            rows.append({"kappa":kappa,"exact":exact,"round52_service_estimate":old["statistics"]["service"]["estimate"],
                "round52_simultaneous_interval":interval,"round52_profit_error_in_standard_errors":error/p["standard_error"]})
        clear_solver_caches(solver)
        del solver
        gc.collect()
    save_service(55,{"question":"Can the same exact evaluation structure handle batch-correlated quality without using mean proportions?",
        "assumptions":__doc__,"scope":"Exact expectation for specified Dirichlet-multinomial quality laws and fixed-forward known-eta maximal returns. Kappas are hypothetical and not identified from the available marginal quality means.",
        "headline":{"elapsed_seconds":time.perf_counter()-started,"small_multinomial_exhaustive_cases":len(errors),
            "max_probability_error":max(e[0] for e in errors),"max_net_revenue_error":max(e[1] for e in errors),
            "max_return_error":max(e[2] for e in errors),"full_size_policies":len(rows)},"rows":rows},__file__,
        (ROOT/"backbone"/"exact_batch_quality.py",ROOT/"backbone"/"exact_quality_economics.py",
         ROOT/"backbone"/"exact_quality_service.py",ROOT/"backbone"/"quality_lab.py",
         ROOT/"backbone"/"round52_batch_quality_variation.py"))


if __name__=="__main__":
    main()
