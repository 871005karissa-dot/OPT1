"""Independent generic LP checks for custom grade shares, eligibility, retention."""
from pathlib import Path
import importlib.util
import json
import sys
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from backbone.quality_lab import *
from backbone.round40_quality_recoverability import recoverability
from backbone.evaluator import component_probabilities
from backbone.ball_screw import KQCS,APPENDIX_COMPONENT_PROBABILITIES

spec=importlib.util.spec_from_file_location("base_lp",Path(__file__).parents[1]/"six_rounds"/"check_capacity_lp.py")
base=importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)


def scalar_flow(raw,cap,x,q1,q2):
    g1,g2,cost=base.scalar(raw,cap,x)
    return g1/Q1*q1,g2/Q2*q2,cost


def solve(raw,cap,d,eta,eligible,q1,q2,rho,complete):
    rates=[s.yield_rate for s in STATIONS]
    upper=min(min(raw,cap[0])*rates[0],cap[1])
    theta=float(np.prod(rates[1:]))
    stages=[0.,upper]
    factor=rates[1]
    for j in (2,3,4):
        stages.append(min(upper,cap[j]/factor))
        factor*=rates[j]
    stages=sorted(set(stages))
    points=stages+[min(upper,d[0]/(q1*theta)),min(upper,d[1]/(q2*theta)),min(upper,sum(d)/((q1+q2)*theta))]
    values=[]
    for x in points:
        g1,g2,cost=scalar_flow(raw,cap,x,q1,q2)
        if not complete or (g1>=d[0]-1e-7 and g1+g2>=sum(d)-1e-7):
            values.append(base.no_return_value(g1,g2,cost,d))
    a=1-rho*(1-eta)
    for left,right in zip(stages,stages[1:]):
        if right-left<1e-8:
            continue
        g1l,g2l,cl=scalar_flow(raw,cap,left,q1,q2)
        g1r,g2r,cr=scalar_flow(raw,cap,right,q1,q2)
        a1,a2,ac=((g1r-g1l)/(right-left),(g2r-g2l)/(right-left),(cr-cl)/(right-left))
        b1,b2,bc=g1l-a1*left,g2l-a2*left,cl-ac*left
        for high in ((True,) if complete else (False,True)):
            price=90. if high else 120.
            objective=np.array([price*a1+30*a2-ac,price*eta-30*a-5.5])
            const=price*b1+30*b2+30*d[1]+(30*d[0] if high else 0.)-bc
            aub=[[-a2,1],[1,1],[-eligible*a2,1],[-a1,-eta] if high else [a1,eta]]
            bub=[b2-d[1],cap[1]-350.,eligible*b2,b1-d[0] if high else d[0]-b1]
            value=base.lp_max(objective,aub,bub,left,right)
            if value is not None:
                values.append(value+const)
    return max(values) if values else None


def main():
    rng=np.random.default_rng(2026102841)
    selected=np.unique(np.concatenate((np.argsort(PROB)[-8:],rng.choice(len(PROB),8,replace=False))))
    worst=worst_complete=0.
    checks=feasible=0
    for probabilities in (component_probabilities(KQCS),APPENDIX_COMPONENT_PROBABILITIES):
      quality=recoverability(probabilities)
      q1,q2=quality["implied_grade1_share"],quality["implied_grade2_share"]
      for d in ((550.,350.),(750.,150.)):
       raw=required_input(d,(q1,q2),STATIONS,1)
       for feature in quality["single_feature_bounds"]:
        f=feature["single_feature_perfect_repair_upper_bound"]
        for eta,eligible in ((.97,f),(.97*f,1.)):
         for rho in (0.,1.):
          best,serve,found,_=quality_action_pair(raw,d,eta,q1,q2,eligible,retention=rho)
          for j in selected:
            independent=solve(raw,CAPS[j],d,eta,eligible,q1,q2,rho,False)
            error=abs(independent-best["profit"][j])
            worst=max(worst,error)
            assert error<2e-5,(d,eta,eligible,rho,int(j),error)
            complete=solve(raw,CAPS[j],d,eta,eligible,q1,q2,rho,True)
            assert (complete is not None)==bool(found[j])
            if complete is not None:
                error=abs(complete-serve["profit"][j])
                worst_complete=max(worst_complete,error)
                assert error<2e-5
                feasible+=1
            checks+=1
    result={"state_quality_eta_eligibility_retention_cases":checks,"complete_action_feasible_checks":feasible,
            "max_profit_error":worst,"max_complete_action_profit_error":worst_complete,
            "method":"independent scalar forward grades plus generic LP half-plane intersections with eligible-pool and complete-order constraints"}
    Path(__file__).with_name("quality_check.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(json.dumps(result))


if __name__=="__main__":
    main()
