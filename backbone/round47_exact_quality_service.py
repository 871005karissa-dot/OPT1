"""Round47: remove Monte Carlo error for the fixed-forward random-quality policy.

Exact binomial conditioning of multinomial quality counts, plus exact weighted
capacity enumeration. Restrictions are those of exact_quality_service.py.
Cross-check small batches by direct four-category multinomial enumeration and
compare the full-size result with round46's independent confidence intervals.
"""
import math
import time
from backbone.exact_quality_service import *


def brute(n,q1,q2,f,d,spare,eta=.97):
    p=(q1,q2*f,q2*(1-f),1-q1-q2)
    result=0.
    for a in range(n+1):
      for e in range(n-a+1):
       for other in range(n-a-e+1):
        defect=n-a-e-other
        counts=(a,e,other,defect)
        mass=math.exp(math.lgamma(n+1)-sum(math.lgamma(k+1) for k in counts)
                      +sum(k*math.log(v) for k,v in zip(counts,p)))
        b=e+other
        r=min(max(b-d[1],0.),e,spare)
        grade1=a+eta*r
        grade2=b-r
        sub=min(max(grade1-d[0],0.),max(d[1]-grade2,0.))
        if grade1>=d[0]-EPS and grade2+sub>=d[1]-EPS:
            result+=mass
    return result


def main():
    started=time.perf_counter()
    errors=[]
    for q1,q2,f in ((.5,.3,.2),(.625,.254,.397)):
      for d in ((5,3),(8,2)):
        solver=ExactQualityService(q1,q2,f,d,maximum=18)
        for n in (8,12,18):
          for spare in (0.,1.5,4.,12.):
            independent=brute(n,q1,q2,f,d,spare)
            computed=solver.conditional(n,spare)
            errors.append(abs(independent-computed))
            assert errors[-1]<1e-10,(q1,q2,f,d,n,spare,independent,computed)
    earlier=json.loads((SERVICE_OUT/"round46.json").read_text(encoding="utf-8"))
    training=json.loads((SERVICE_OUT/"round45.json").read_text(encoding="utf-8"))
    q1,q2=training["grade_shares"]
    solver=ExactQualityService(q1,q2,training["eligible_fraction"],tuple(training["demands"]))
    rows=[]
    for row in earlier["rows"]:
        exact,diagnostics=solver.evaluate(row["input"])
        lower,upper=row["simultaneous_hoeffding_interval"]
        assert lower<=exact<=upper
        rows.append({"input":row["input"],"exact_service_probability":exact,
            "round46_estimate":row["service"]["estimate"],"round46_simultaneous_interval":[lower,upper],
            "MC_absolute_error":abs(row["service"]["estimate"]-exact),**diagnostics})
    save_service(47,{"question":"Can exact multinomial service probabilities confirm the Monte Carlo service findings?",
        "assumptions":__doc__,"scope":"Exact service probability for the specified fixed-forward, post-inspection maximal-return policy and known fluid eta=.97; not an exact expected-profit optimizer for random quality or a scheduling theorem.",
        "headline":{"elapsed_seconds":time.perf_counter()-started,"small_batch_exhaustive_cases":len(errors),
                    "max_exhaustive_probability_error":max(errors),"full_size_policies":len(rows)},"rows":rows},__file__,
        (ROOT/"backbone"/"exact_quality_service.py",ROOT/"backbone"/"quality_lab.py",
         ROOT/"backbone"/"round44_random_quality_counts.py",ROOT/"backbone"/"round45_threshold_stability.py",
         ROOT/"backbone"/"round46_independent_service_validation.py"))


if __name__=="__main__":
    main()
