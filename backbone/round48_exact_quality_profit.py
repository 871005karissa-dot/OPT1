"""Round48: exact expected-profit benchmark for fixed-forward random quality."""
import math
import time
from backbone.exact_quality_economics import *


def brute_net_revenue(n,q1,q2,f,d,spare,eta=.97):
    p=(q1,q2*f,q2*(1-f),1-q1-q2)
    result=sent=0.
    for a in range(n+1):
      for e in range(n-a+1):
       for other in range(n-a-e+1):
        counts=(a,e,other,n-a-e-other)
        mass=math.exp(math.lgamma(n+1)-sum(math.lgamma(k+1) for k in counts)
                      +sum(k*math.log(v) for k,v in zip(counts,p)))
        b=e+other
        r=min(max(b-d[1],0.),e,spare)
        g1,g2=a+eta*r,b-r
        sub=min(max(g1-d[0],0.),max(d[1]-g2,0.))
        revenue=(120*min(g1,d[0])+60*min(g2+sub,d[1])
                 +90*max(g1-d[0]-sub,0.)+30*max(g2+sub-d[1],0.)-5.5*r)
        result+=mass*revenue
        sent+=mass*r
    return result,sent


def main():
    started=time.perf_counter()
    errors=[]
    return_errors=[]
    for q1,q2,f in ((.5,.3,.2),(.625,.254,.397)):
      for d in ((5,3),(8,2)):
        solver=ExactQualityEconomics(q1,q2,f,d,maximum=18)
        for n in (8,12,18):
          for spare in (0.,1.5,4.,12.):
            independent,r=brute_net_revenue(n,q1,q2,f,d,spare)
            exact,sent=solver.net_revenue_and_return(n,spare)
            errors.append(abs(independent-exact))
            return_errors.append(abs(r-sent))
            assert errors[-1]<1e-8,(q1,q2,f,d,n,spare,independent,exact)
            assert return_errors[-1]<1e-10
    training=json.loads((SERVICE_OUT/"round45.json").read_text(encoding="utf-8"))
    validation=json.loads((SERVICE_OUT/"round46.json").read_text(encoding="utf-8"))
    q1,q2=training["grade_shares"]
    solver=ExactQualityEconomics(q1,q2,training["eligible_fraction"],tuple(training["demands"]))
    rows=[]
    for row in validation["rows"]:
        exact=solver.evaluate_economics(row["input"])
        difference=abs(exact["expected_profit"]-row["profit"]["estimate"])
        z=difference/row["profit"]["standard_error"]
        assert z<5.,(row["input"],exact,row["profit"])
        rows.append({**exact,"round46_profit_estimate":row["profit"]["estimate"],
                     "MC_profit_absolute_error":difference,"MC_profit_error_in_standard_errors":z})
    save_service(48,{"question":"Can exact expected cash profit and return quantities replace Monte Carlo for this restricted policy?",
        "assumptions":__doc__,"scope":"Exact expectation for fixed-forward, known eta=.97, maximal eligible return, multinomial initial quality and the specified cash accounting. No continuous-input or adaptive-forward optimality claim.",
        "headline":{"elapsed_seconds":time.perf_counter()-started,"small_batch_exhaustive_cases":len(errors),
                    "max_brute_revenue_error":max(errors),"max_brute_return_error":max(return_errors),
                    "full_size_policies":len(rows)},"rows":rows},__file__,
        (ROOT/"backbone"/"exact_quality_economics.py",ROOT/"backbone"/"exact_quality_service.py",
         ROOT/"backbone"/"quality_lab.py",ROOT/"backbone"/"round45_threshold_stability.py",
         ROOT/"backbone"/"round46_independent_service_validation.py"))


if __name__=="__main__":
    main()
