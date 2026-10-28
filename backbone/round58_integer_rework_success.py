"""Round58: separate integer repair capacity from future Bernoulli success.

Candidate screw-diameter reduction at final station5, normal KQC source,
one-direction eligible subset, failures scrapped, all eligible surplus returns.
Process name is sourced; direction, eligibility preservation and eta are
unvalidated hypothetical capabilities. No assertion of a measured factory route.
Initial-quality model remains item-independent to isolate return outcomes.
"""
import math
import time
from backbone.integer_rework import *
from backbone.round57_process_route_audit import RouteEconomics
from backbone.round42_one_sided_repair import one_sided_bounds


def brute(n,q1,q2,f,d,spare,eta,cost,mode):
    probabilities=(q1,q2*f,q2*(1-f),1-q1-q2)
    revenue=service=sent=0.
    for a in range(n+1):
      for e in range(n-a+1):
       for other in range(n-a-e+1):
        counts=(a,e,other,n-a-e-other)
        mass=math.exp(math.lgamma(n+1)-sum(math.lgamma(k+1) for k in counts)
                      +sum(k*math.log(p) for k,p in zip(counts,probabilities)))
        b=e+other
        r=min(e,max(b-d[1],0),int(spare))
        sent+=mass*r
        outcomes=[(eta*r,1.)] if mode=="integer_mean" else [
            (y,math.comb(r,y)*eta**y*(1-eta)**(r-y)) for y in range(r+1)]
        for y,py in outcomes:
            high,low=a+y,b-r
            sub=min(max(high-d[0],0),max(d[1]-low,0))
            cash=(120*min(high,d[0])+60*min(low+sub,d[1])
                  +90*max(high-d[0]-sub,0)+30*max(low+sub-d[1],0)-cost*r)
            revenue+=mass*py*cash
            service+=mass*py*(high>=d[0]-EPS and low+sub>=d[1]-EPS)
    return revenue,service,sent


def main():
    started=time.perf_counter()
    checks=[]
    for eta in (.55,.97):
      solver=IntegerReworkEconomics(.5,.3,.25,(5,2),maximum=12,eta=eta,mass_cutoff=0.)
      for n in (6,9,12):
       for spare in (0,2,7):
        for mode in ("integer_mean","binomial"):
            exact=solver.metrics(n,spare,mode)
            independent=brute(n,.5,.3,.25,(5,2),spare,eta,solver.unit_cost,mode)
            errors=[abs(exact[k]-v) for k,v in zip(("net_revenue","service","expected_rework"),independent)]
            assert max(errors)<1e-8,(eta,n,spare,mode,errors)
            checks.append(errors)
      release_integer_caches(solver)
    quality,bounds=one_sided_bounds()
    q1,q2=quality["implied_grade1_share"],quality["implied_grade2_share"]
    f=bounds[3]["decrease_value_bound"]
    d=(750.,150.)
    raw=required_input(d,(q1,q2),STATIONS,1)
    solver=IntegerReworkEconomics(q1,q2,f,d)
    fluid=RouteEconomics(q1,q2,f,d,4)
    rows=[]
    for setup in (0.,300.):
        baseline={"mode":"fractional_return_mean_success","input":raw,"setup_workload":setup,
                  **fluid.evaluate_route(raw,setup)}
        rows.append(baseline)
        print(json.dumps({"mode":baseline["mode"],"setup":setup,"R":baseline["fulfilment_probability"]}),flush=True)
        for mode in ("integer_mean","binomial"):
            row=solver.evaluate_integer(raw,setup,mode)
            rows.append(row)
            print(json.dumps({"mode":mode,"setup":setup,"R":row["fulfilment_probability"],"Pi":row["expected_profit"]}),flush=True)
    save_service(58,{"question":"Does replacing eta*r by an unknown future integer success count change full-order service after route matching?",
        "assumptions":__doc__,"model_derivation":__import__("backbone.integer_rework",fromlist=["__doc__"]).__doc__,
        "grade_shares":[q1,q2],"eligible_fraction":f,"demands":d,"eta":.97,
        "headline":{"elapsed_seconds":time.perf_counter()-started,"small_brute_cases":len(checks),
                    "max_revenue_error":max(x[0] for x in checks),"max_service_error":max(x[1] for x in checks),
                    "max_return_error":max(x[2] for x in checks),"full_size_cases":len(rows)},"rows":rows},__file__,
        (ROOT/"backbone"/"integer_rework.py",ROOT/"backbone"/"exact_quality_economics.py",
         ROOT/"backbone"/"exact_quality_service.py",ROOT/"backbone"/"round57_process_route_audit.py",
         ROOT/"backbone"/"round42_one_sided_repair.py"))


if __name__=="__main__":
    main()
