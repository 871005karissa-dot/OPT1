"""Independent service-action LP and exhaustive small covering-policy checks."""
from pathlib import Path
import importlib.util
import itertools
import json
import sys

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from backbone.service_frontier import *

spec=importlib.util.spec_from_file_location("independent_lp",Path(__file__).parents[1]/"six_rounds"/"check_capacity_lp.py")
lp=importlib.util.module_from_spec(spec)
spec.loader.exec_module(lp)


def scalar_best_complete(raw,cap,d,eta,setup):
    rates=[s.yield_rate for s in STATIONS]
    upper=min(min(raw,cap[0])*rates[0],cap[1])
    theta=float(np.prod(rates[1:]))
    stages=[0.,upper]
    factor=rates[1]
    for index in (2,3,4):
        stages.append(min(upper,cap[index]/factor))
        factor*=rates[index]
    stages=sorted(set(stages))
    points=stages+[min(upper,d[0]/(Q1*theta)),min(upper,d[1]/(Q2*theta)),
                   min(upper,sum(d)/((Q1+Q2)*theta))]
    values=[]
    for x in points:
        g1,g2,cost=lp.scalar(raw,cap,x)
        if g1>=d[0]-1e-7 and g1+g2>=sum(d)-1e-7:
            values.append(lp.no_return_value(g1,g2,cost,d))
    for left,right in zip(stages,stages[1:]):
        if right-left<1e-8:
            continue
        g1l,g2l,cl=lp.scalar(raw,cap,left)
        g1r,g2r,cr=lp.scalar(raw,cap,right)
        a1,a2,ac=((g1r-g1l)/(right-left),(g2r-g2l)/(right-left),(cr-cl)/(right-left))
        b1,b2,bc=g1l-a1*left,g2l-a2*left,cl-ac*left
        objective=np.array([90*a1+30*a2-ac,90*eta-35.5])
        const=90*b1+30*d[0]+30*b2+30*d[1]-bc
        value=lp.lp_max(objective,[[-a2,1],[1,1],[-a1,-eta]],
                        [b2-d[1],cap[1]-setup,b1-d[0]],left,right)
        if value is not None:
            values.append(value+const)
    return max(values) if values else None


def covering_check(rng):
    """Compare a ratio rule with every small hypercube/covering-plane vertex."""
    n=8
    p=rng.uniform(.01,1,n)
    p/=p.sum()
    loss=rng.uniform(0,100,n)
    required=float(rng.uniform(.05,.95))
    order=np.argsort(loss)
    z=np.zeros(n)
    remaining=required
    for j in order:
        z[j]=min(1.,max(0.,remaining/p[j]))
        remaining-=p[j]*z[j]
    greedy=float(np.dot(p*loss,z))
    continuous=[]
    discrete=[]
    for bits in itertools.product((0.,1.),repeat=n):
        v=np.array(bits)
        if np.dot(p,v)>=required-1e-12:
            discrete.append(float(np.dot(p*loss,v)))
    for boundary in range(n):
        others=[j for j in range(n) if j!=boundary]
        for bits in itertools.product((0.,1.),repeat=n-1):
            v=np.zeros(n)
            v[others]=bits
            v[boundary]=(required-np.dot(p,v))/p[boundary]
            if -1e-12<=v[boundary]<=1+1e-12:
                continuous.append(float(np.dot(p*loss,v)))
    error=abs(greedy-min(continuous+discrete))
    rounded=np.ceil(z-1e-12)
    rounded_cost=float(np.dot(p*loss,rounded))
    discrete_opt=min(discrete)
    assert error<1e-9
    assert greedy<=discrete_opt+1e-9<=rounded_cost+1e-9
    return error,rounded_cost-discrete_opt,rounded_cost-greedy


def main():
    rng=np.random.default_rng(2026102833)
    selected=np.unique(np.concatenate((np.argsort(PROB)[-16:],rng.choice(len(PROB),20,replace=False))))
    checks=0
    feasible_checks=0
    worst=0.
    for d in ((550.,350.),(650.,250.),(700.,200.),(750.,150.)):
      for eta in (.2,.35,.97):
        raw=release(d)
        _,serve,found,_,_,_=action_pair(raw,d,eta,350.,True)
        for index in selected:
            independent=scalar_best_complete(raw,CAPS[index],d,eta,350.)
            assert (independent is not None)==bool(found[index]),(d,eta,int(index))
            if independent is not None:
                error=abs(independent-serve["profit"][index])
                worst=max(worst,error)
                assert error<2e-5,(d,eta,int(index),error)
                feasible_checks+=1
            checks+=1
    covers=[covering_check(rng) for _ in range(40)]
    result={"service_LP_cases":checks,"feasible_service_LP_cases":feasible_checks,
            "max_complete_action_profit_error":worst,"exhaustive_eight_state_covering_cases":len(covers),
            "max_fractional_profit_error":max(row[0] for row in covers),
            "max_actual_deterministic_gap_in_synthetic_cases":max(row[1] for row in covers),
            "max_certified_gap_in_synthetic_cases":max(row[2] for row in covers),
            "note":"Synthetic checks verify bound logic; their gap size is not a real manufacturing estimate."}
    Path(__file__).with_name("service_check.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(json.dumps(result))


if __name__=="__main__":
    main()
