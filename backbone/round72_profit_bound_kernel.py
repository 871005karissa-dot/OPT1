"""Round72: validate a profit-best upper bound before comparing economic cases.

Same fixed-forward binary-setup model. The direct enumeration chooses r based
on EXPECTED future cash, then reveals success, never maximizes after seeing Y.
This bound may safely exclude an input whose unconstrained profit is already
below a known service-feasible value; it is not the constrained optimum itself.
"""
import gc
import math
import time
from backbone.recourse_value_curves import *
from backbone.batch_stochastic_setup import BatchStochasticSetup


def direct(n,q1,q2,f,kappa,d,cap,fee,always=False):
    pp=(q1,q2*f,q2*(1-f),1-q1-q2)
    revenue=service=0.
    for a in range(n+1):
      for e in range(n-a+1):
       for other in range(n-a-e+1):
        cc=(a,e,other,n-a-e-other)
        if kappa is None:
            logmass=math.lgamma(n+1)-sum(math.lgamma(k+1) for k in cc)+sum(k*math.log(p) for k,p in zip(cc,pp))
        else:
            logmass=math.lgamma(n+1)+math.lgamma(kappa)-math.lgamma(kappa+n)+sum(
                math.lgamma(k+kappa*p)-math.lgamma(kappa*p)-math.lgamma(k+1) for k,p in zip(cc,pp))
        mass=math.exp(logmass)
        b=e+other
        available=min(e,max(b-d[1],0),cap)
        choices=[]
        for r in range(available+1):
            cash=met=0.
            for y in range(r+1):
                chance=math.comb(r,y)*.97**y*.03**(r-y)
                high,low=a+y,b-r
                sub=min(max(high-d[0],0),max(d[1]-low,0))
                value=120*min(high,d[0])+60*min(low+sub,d[1])+90*max(high-d[0]-sub,0)+30*max(low+sub-d[1],0)-12.4*r-fee*(r>0)
                cash+=chance*value
                met+=chance*(high>=d[0] and low+sub>=d[1])
            choices.append((cash,met))
        best=choices[-1] if always else max(choices,key=lambda x:(x[0],x[1]))
        revenue+=mass*best[0]
        service+=mass*best[1]
    return revenue,service


def main():
    started=time.perf_counter()
    checks=[]
    for kappa in (None,10.):
        solver=(StochasticSetupFrontier(.5,.3,.25,(5,2),maximum=12) if kappa is None else
                BatchStochasticSetup(.5,.3,.25,(5,2),kappa,maximum=12))
        engine=RecourseValueCurves(solver)
        for n in (8,12):
          for cap in (0,3,8):
           for fee in (0.,20.,100.):
            independent=direct(n,.5,.3,.25,kappa,(5,2),cap,fee)
            values=engine.values(n,fee)
            errors=[abs(float(values[key][cap])-v) for key,v in zip(("net_revenue","service"),independent)]
            assert errors[0]<1e-8 and errors[1]<1e-10,(kappa,n,cap,fee,errors)
            checks.append(errors)
            all_expected=direct(n,.5,.3,.25,kappa,(5,2),cap,fee,always=True)
            all_values=engine.always_return_values(n,fee)
            all_errors=[abs(float(all_values[key][cap])-v) for key,v in zip(("net_revenue","service"),all_expected)]
            assert all_errors[0]<1e-8 and all_errors[1]<1e-10
            checks.append(all_errors)
        RecourseValueCurves.values.cache_clear()
        RecourseValueCurves.always_return_values.cache_clear()
        release_integer_caches(solver)
        StochasticSetupFrontier.unbounded_return_law.cache_clear()
        del solver,engine
        gc.collect()
    prior=json.loads((SERVICE_OUT/"round61.json").read_text(encoding="utf-8"))
    q1,q2=prior["grade_shares"]
    solver=StochasticSetupFrontier(q1,q2,prior["eligible_fraction"],tuple(prior["demands"]))
    engine=RecourseValueCurves(solver)
    comparisons=[]
    for old in prior["rows"]:
        actual=engine.evaluate_profit_best(prior["input"],old["setup_fee"])
        profit_diff=abs(actual["expected_profit"]-old["profit_best"]["expected_profit"])
        service_diff=abs(actual["fulfilment_probability"]-old["profit_best"]["fulfilment_probability"])
        assert profit_diff<1e-7 and service_diff<1e-10
        comparisons.append({"fee":old["setup_fee"],**actual,"profit_difference":profit_diff,"service_difference":service_diff})
    save_service(72,{"question":"Can a cached exact profit-best value screen outer releases without discarding a better constrained policy?",
        "assumptions":__doc__,"headline":{"small_all_action_future_success_enumerations":len(checks),
                    "max_revenue_error":max(x[0] for x in checks),"max_service_error":max(x[1] for x in checks),
                    "full_size_comparisons":len(comparisons),"elapsed_seconds":time.perf_counter()-started},"rows":comparisons},__file__,
        (ROOT/"backbone"/"recourse_value_curves.py",ROOT/"backbone"/"maximal_service_curve.py",
         ROOT/"backbone"/"stochastic_setup_frontier.py",ROOT/"backbone"/"batch_stochastic_setup.py",
         ROOT/"backbone"/"integer_rework.py",ROOT/"backbone"/"exact_quality_economics.py",
         ROOT/"backbone"/"exact_quality_service.py",ROOT/"backbone"/"exact_batch_quality.py",SERVICE_OUT/"round61.json"))


if __name__=="__main__":
    main()
