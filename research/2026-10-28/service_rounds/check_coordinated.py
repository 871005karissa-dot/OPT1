"""Generic scalar LP validation of coordinated upstream and material accounting."""
from pathlib import Path
import importlib.util
import json
import sys
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from backbone.service_frontier import *

spec=importlib.util.spec_from_file_location("base_lp",Path(__file__).parents[1]/"six_rounds"/"check_capacity_lp.py")
base=importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)


def state_flow(raw,cap,x,recovery):
    g1,g2,cost=base.scalar(raw,cap,x)
    m=MATERIAL_COST
    v=m*recovery
    old_stage1=min(raw,cap[0])
    cost-=(m+MANUFACTURING_COSTS[0])*old_stage1
    cost+=(v+MANUFACTURING_COSTS[0])*x/STATIONS[0].yield_rate+(m-v)*raw
    return g1,g2,cost


def solve(raw,cap,d,eta,setup,recovery,complete_only):
    rates=[s.yield_rate for s in STATIONS]
    upper=min(min(raw,cap[0])*rates[0],cap[1])
    theta=float(np.prod(rates[1:]))
    stages=[0.,upper]
    factor=rates[1]
    for j in (2,3,4):
        stages.append(min(upper,cap[j]/factor))
        factor*=rates[j]
    stages=sorted(set(stages))
    points=stages+[min(upper,d[0]/(Q1*theta)),min(upper,d[1]/(Q2*theta)),min(upper,sum(d)/((Q1+Q2)*theta))]
    values=[]
    for x in points:
        g1,g2,cost=state_flow(raw,cap,x,recovery)
        if not complete_only or (g1>=d[0]-1e-7 and g1+g2>=sum(d)-1e-7):
            values.append(base.no_return_value(g1,g2,cost,d))
    for left,right in zip(stages,stages[1:]):
        if right-left<1e-8:
            continue
        g1l,g2l,cl=state_flow(raw,cap,left,recovery)
        g1r,g2r,cr=state_flow(raw,cap,right,recovery)
        a1,a2,ac=((g1r-g1l)/(right-left),(g2r-g2l)/(right-left),(cr-cl)/(right-left))
        b1,b2,bc=g1l-a1*left,g2l-a2*left,cl-ac*left
        for high in ((True,) if complete_only else (False,True)):
            price=90. if high else 120.
            objective=np.array([price*a1+30*a2-ac,price*eta-35.5])
            const=price*b1+30*b2+30*d[1]+(30*d[0] if high else 0.)-bc
            aub=[[-a2,1],[1,1],[-a1,-eta] if high else [a1,eta]]
            bub=[b2-d[1],cap[1]-setup,b1-d[0] if high else d[0]-b1]
            value=base.lp_max(objective,aub,bub,left,right)
            if value is not None:
                values.append(value+const)
    return max(values) if values else None


def main():
    rng=np.random.default_rng(2026102838)
    selected=np.unique(np.concatenate((np.argsort(PROB)[-10:],rng.choice(len(PROB),10,replace=False))))
    errors=[]
    service_errors=[]
    checks=0
    for d in ((550.,350.),(650.,250.),(700.,200.),(750.,150.)):
      for eta in (.2,.35,.97):
       for recovery in (0.,.5,1.):
        raw=release(d)
        best,serve,found,_,_,_=action_pair(raw,d,eta,350.,True,True,recovery)
        for index in selected:
            optimum=solve(raw,CAPS[index],d,eta,350.,recovery,False)
            error=abs(optimum-best["profit"][index])
            errors.append(error)
            assert error<2e-5,(d,eta,recovery,int(index),error)
            fulfilled=solve(raw,CAPS[index],d,eta,350.,recovery,True)
            assert (fulfilled is not None)==bool(found[index])
            if fulfilled is not None:
                error=abs(fulfilled-serve["profit"][index])
                service_errors.append(error)
                assert error<2e-5,(d,eta,recovery,int(index),error)
            checks+=1
    result={"state_order_eta_recovery_cases":checks,"max_profit_error":max(errors),
        "complete_action_feasible_checks":len(service_errors),"max_complete_action_profit_error":max(service_errors),
        "method":"independent scalar flow/cost plus generic two-variable LP half-plane intersections, both profit-only and complete-order constraints"}
    Path(__file__).with_name("coordinated_check.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(json.dumps(result))


if __name__=="__main__":
    main()
