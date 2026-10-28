"""Round59: screen a single-feature route before fitting more parameters.

An optimistic bound gives free, perfect, instantaneous, unlimited rework of
the stated eligible class, without using any shared capacity. For a normal
flow producing N iid categorical items, full fulfilment is possible iff
H=A+E>=D1 and T=A+B>=D1+D2. For any forward rule chosen before initial-quality
realization, N<=Nmax(C) from the serial fluid normal-flow capacities.
Couple all potential items in one categorical sequence: H and T cannot decrease
when N increases. Thus E_C Pr(H>=D1,T>=sumD|Nmax(C)) bounds that policy class.
It is not an upper bound if forward yield distributions change, observed
quality guides sequential normal production, more features are repairable,
or arbitrary extra capacity/sourcing is available.
"""
from functools import lru_cache
import math
import time
from backbone.exact_quality_service import *
from backbone.round42_one_sided_repair import one_sided_bounds


class NestedQualityBound:
    def __init__(self,q1,q2,f,demands,maximum=1600):
        self.h=q1+q2*f
        self.total=q1+q2
        self.d1,self.d2=map(int,demands)
        self.high=BinomialTables(maximum,self.h)
        p=q2*(1-f)/(1-self.h)
        self.other=None if p==0 else BinomialTables(maximum,p)

    @lru_cache(maxsize=None)
    def probability(self,n):
        hs=np.arange(self.d1,n+1)
        if len(hs)==0:
            return 0.
        need=np.maximum(self.d1+self.d2-hs,0)
        available=n-hs
        if self.other is None:
            chances=(need==0).astype(float)
        else:
            feasible=need<=available
            chances=np.zeros(len(hs))
            chances[feasible]=self.other.tail[available[feasible],need[feasible]]
        return float(self.high.pmf[n,hs]@chances)


def brute(n,q1,q2,f,d):
    pp=(q1,q2*f,q2*(1-f),1-q1-q2)
    value=0.
    for a in range(n+1):
      for e in range(n-a+1):
       for other in range(n-a-e+1):
        counts=(a,e,other,n-a-e-other)
        if any(count and p==0 for count,p in zip(counts,pp)):
            continue
        mass=math.exp(math.lgamma(n+1)-sum(math.lgamma(k+1) for k in counts)
                      +sum(k*math.log(p) for k,p in zip(counts,pp) if k))
        # Independent feasibility: enumerate the number actually repaired.
        feasible=any(a+r>=d[0] and a+e+other>=sum(d) and e+other-r+max(a+r-d[0],0)>=d[1]
                     for r in range(e+1))
        value+=mass*feasible
    return value


def main():
    started=time.perf_counter()
    errors=[]
    for f in (0.,.05,.3,.8,1.):
      for d in ((5,3),(8,2)):
        solver=NestedQualityBound(.5,.3,f,d,18)
        for n in (8,12,18):
            exact=solver.probability(n)
            independent=brute(n,.5,.3,f,d)
            errors.append(abs(exact-independent))
            assert errors[-1]<1e-10,(f,d,n,exact,independent)
        monotone=[solver.probability(n) for n in range(19)]
        assert min(np.diff(monotone))>=-1e-12
        NestedQualityBound.probability.cache_clear()
    quality,bounds=one_sided_bounds()
    q1,q2=quality["implied_grade1_share"],quality["implied_grade2_share"]
    nmax=np.floor(forward(sum(s.machine_count*s.machine_capacity for s in STATIONS)).finished+1e-9).astype(int)
    ns,inverse=np.unique(nmax,return_inverse=True)
    weights=np.bincount(inverse,weights=PROB,minlength=len(ns))
    d=(750.,150.)
    candidates=[("no repair",0.),("all grade2 perfect upgrade",1.)]
    for i,direction in ((0,"decrease_value_bound"),(1,"increase_value_bound"),(2,"decrease_value_bound"),(3,"decrease_value_bound")):
        candidates.append((bounds[i]["KQC_name"]+" one-direction",bounds[i][direction]))
        candidates.append((bounds[i]["KQC_name"]+" bidirectional",bounds[i]["bidirectional_bound"]))
    rows=[]
    for name,f in candidates:
        solver=NestedQualityBound(q1,q2,f,d)
        bound=float(weights@np.array([solver.probability(int(n)) for n in ns]))
        rows.append({"eligible_class":name,"eligible_fraction":f,"optimistic_fulfilment_upper_bound":bound})
        NestedQualityBound.probability.cache_clear()
    prior=json.loads((SERVICE_OUT/"round58.json").read_text(encoding="utf-8"))
    screw=next(x for x in rows if x["eligible_class"]=="screw diameter one-direction")
    assert all(x["fulfilment_probability"]<=screw["optimistic_fulfilment_upper_bound"]+1e-10 for x in prior["rows"])
    save_service(59,{"question":"Can a physical eligibility limitation rule out a service target even under free perfect unlimited repair?",
        "assumptions":__doc__,"grade_shares":[q1,q2],"demands":d,
        "headline":{"small_brute_cases":len(errors),"max_brute_probability_error":max(errors),
                    "candidate_bounds":len(rows),"normal_output_groups":len(ns),
                    "elapsed_seconds":time.perf_counter()-started},"rows":rows},__file__,
        (ROOT/"backbone"/"exact_quality_service.py",ROOT/"backbone"/"round42_one_sided_repair.py",
         ROOT/"backbone"/"round58_integer_rework_success.py",SERVICE_OUT/"round58.json"))


if __name__=="__main__":
    main()
