"""Independent scalar LP check of the statewise fluid capacity-allocation vertices."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
import numpy as np
from itertools import combinations, product
from backbone.recourse_lab import (
    CAPS, PROB, STATIONS, MATERIAL_COST, MANUFACTURING_COSTS, Q1, Q2,
    release, exact_capacity_policy,
)


def scalar(raw, capacities, x):
    rates = [station.yield_rate for station in STATIONS]
    load = [min(raw,capacities[0]),x]
    incoming = x*rates[1]
    for index in (2,3,4):
        load.append(min(incoming,capacities[index]))
        incoming = load[-1]*rates[index]
    cost = load[0]*MATERIAL_COST + sum(l*c for l,c in zip(load,MANUFACTURING_COSTS))
    return incoming*Q1,incoming*Q2,cost


def no_return_value(g1,g2,cost,demands):
    sub = min(max(g1-demands[0],0),max(demands[1]-g2,0))
    return (120*min(g1,demands[0])+60*min(g2+sub,demands[1])
            +90*max(g1-demands[0]-sub,0)+30*max(g2+sub-demands[1],0)-cost)


def lp_max(objective,aub,bub,left,right):
    """Generic bounded two-variable LP by all feasible half-plane intersections."""
    a = np.array(aub+[[1,0],[-1,0],[0,-1]],dtype=float)
    b = np.array(bub+[right,-left,0],dtype=float)
    values = []
    for i,j in combinations(range(len(b)),2):
        matrix = a[[i,j]]
        if abs(np.linalg.det(matrix))<1e-12:
            continue
        vertex = np.linalg.solve(matrix,b[[i,j]])
        if np.all(a@vertex<=b+1e-7):
            values.append(float(objective@vertex))
    return max(values) if values else None


def scalar_optimum(raw,cap,demands,eta,setup):
    rates = [station.yield_rate for station in STATIONS]
    upper = min(min(raw,cap[0])*rates[0],cap[1])
    theta = float(np.prod(rates[1:]))
    points = [0.,upper]
    factor = rates[1]
    for index in (2,3,4):
        points.append(min(upper,cap[index]/factor))
        factor *= rates[index]
    stages = sorted(set(points))
    points += [min(upper,demands[0]/(Q1*theta)),min(upper,demands[1]/(Q2*theta)),
               min(upper,sum(demands)/((Q1+Q2)*theta))]
    best = max(no_return_value(*scalar(raw,cap,x),demands) for x in points)
    for left,right in zip(stages,stages[1:]):
        if right-left < 1e-8:
            continue
        g1l,g2l,cl = scalar(raw,cap,left)
        g1r,g2r,cr = scalar(raw,cap,right)
        a1,a2,ac = ((g1r-g1l)/(right-left),(g2r-g2l)/(right-left),(cr-cl)/(right-left))
        b1,b2,bc = g1l-a1*left,g2l-a2*left,cl-ac*left
        for high in (False,True):
            price = 90.0 if high else 120.0
            objective = np.array([price*a1+30*a2-ac,price*eta-35.5])
            const = price*b1+30*b2+30*demands[1]+(30*demands[0] if high else 0)-bc
            aub = [[-a2,1],[1,1]]
            bub = [b2-demands[1],cap[1]-setup]
            aub.append([-a1,-eta] if high else [a1,eta])
            bub.append(b1-demands[0] if high else demands[0]-b1)
            value = lp_max(objective,aub,bub,left,right)
            if value is not None:
                best = max(best,value+const)
    return best


def scalar_uncertain_optimum(raw,cap,demands,etas,weights,setup):
    rates = [station.yield_rate for station in STATIONS]
    upper = min(min(raw,cap[0])*rates[0],cap[1])
    theta = float(np.prod(rates[1:]))
    stages = [0.,upper]
    factor = rates[1]
    for index in (2,3,4):
        stages.append(min(upper,cap[index]/factor))
        factor *= rates[index]
    stages = sorted(set(stages))
    points = stages+[min(upper,demands[0]/(Q1*theta)),min(upper,demands[1]/(Q2*theta)),
                     min(upper,sum(demands)/((Q1+Q2)*theta))]
    best = max(no_return_value(*scalar(raw,cap,x),demands) for x in points)
    for left,right in zip(stages,stages[1:]):
        if right-left<1e-8:
            continue
        g1l,g2l,cl = scalar(raw,cap,left)
        g1r,g2r,cr = scalar(raw,cap,right)
        a1,a2,ac = ((g1r-g1l)/(right-left),(g2r-g2l)/(right-left),(cr-cl)/(right-left))
        b1,b2,bc = g1l-a1*left,g2l-a2*left,cl-ac*left
        for regimes in product((False,True),repeat=len(etas)):
            objective = np.array([30*a2-ac,-35.5])
            const = 30*b2+30*demands[1]-bc
            aub,bub = [[-a2,1],[1,1]],[b2-demands[1],cap[1]-setup]
            for high,eta,weight in zip(regimes,etas,weights):
                price = 90. if high else 120.
                objective += weight*np.array([price*a1,price*eta])
                const += weight*(price*b1+(30*demands[0] if high else 0))
                aub.append([-a1,-eta] if high else [a1,eta])
                bub.append(b1-demands[0] if high else demands[0]-b1)
            value = lp_max(objective,aub,bub,left,right)
            if value is not None:
                best = max(best,value+const)
    return best


def main():
    rng = np.random.default_rng(20261028)
    selected = np.unique(np.concatenate((np.argsort(PROB)[-16:],rng.choice(len(PROB),20,replace=False))))
    worst = 0.0
    checks = 0
    for demands in ((550.,350.),(650.,250.),(700.,200.),(750.,150.)):
        for eta in (.35,.97):
            raw = release(demands)
            action,_,_ = exact_capacity_policy(raw,demands,eta,setup_workload=350.)
            for index in selected:
                independent = scalar_optimum(raw,CAPS[index],demands,eta,350.)
                error = abs(independent-action["profit"][index])
                worst = max(worst,error)
                checks += 1
                assert error < 2e-5,(demands,eta,int(index),independent,action["profit"][index])
    from backbone.round32_nonanticipative_yield import choose_nonanticipative
    uncertain_error = 0.
    uncertain_checks = 0
    smaller = np.unique(np.concatenate((np.argsort(PROB)[-8:],rng.choice(len(PROB),8,replace=False))))
    for demands in ((550.,350.),(650.,250.),(700.,200.),(750.,150.)):
        for etas,weights in (((.15,.35,.55),(.25,.5,.25)),((.05,.2,.8),(.25,.4375,.3125))):
            raw = release(demands)
            aware,_,_ = choose_nonanticipative(raw,demands,etas,weights)
            for index in smaller:
                independent = scalar_uncertain_optimum(raw,CAPS[index],demands,etas,weights,350.)
                error = abs(independent-aware["profit"][index])
                uncertain_error = max(uncertain_error,error)
                uncertain_checks += 1
                assert error<2e-5,(demands,etas,int(index),independent,aware["profit"][index])
    import json
    result = {"state_order_eta_cases":checks,"max_profit_error":worst,
              "uncertain_cases":uncertain_checks,"max_uncertain_profit_error":uncertain_error,
              "method":"independent generic two-variable LP half-plane vertex enumeration over scalar forward-flow and grade-sales regions"}
    Path(__file__).with_name("capacity_lp_check.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(result)


if __name__=="__main__":
    main()
