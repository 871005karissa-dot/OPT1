"""Service-only normal/rework allocation at the final station, before quality.

Given known integer capacity C and normal-flow upper bound U, choose x<=U.
N=floor(y*x), L=floor(C-x), with setup workload0. Conditional service is
nondecreasing in N for fixed L (consistent iid/DM item sequences, same repair
law). A fractional x is weakly dominated for SERVICE by ceil(x) if feasible,
else U: it has the same L and at least as many initial items. Hence integers
plus U suffice for exact continuous-x service maximization in this model.
This does not establish profit optimality or physical scheduling feasibility.
"""
from backbone.maximal_service_curve import *


class FinalStationServiceControl:
    def __init__(self,curves,max_normal_upper):
        self.curves=curves
        self.solver=curves.solver
        assert self.solver.station_index==4
        self.yield_rate=STATIONS[4].yield_rate
        self.max_integer=int(math.floor(max_normal_upper+1e-9))
        self.prefix={}

    def optimize_one(self,capacity,upper):
        capacity=int(capacity)
        assert 0<=upper<=capacity+1e-8
        if capacity not in self.prefix:
            xs=np.arange(min(capacity,self.max_integer)+1)
            ns=np.floor(xs*self.yield_rate+1e-9).astype(int)
            limits=np.minimum(ns,capacity-xs)
            values=np.array([self.curves.curve(int(n))[int(l)] for n,l in zip(ns,limits)])
            best=np.maximum.accumulate(values)
            indices=np.empty(len(xs),dtype=int)
            choice=0
            for i,value in enumerate(values):
                if value>=values[choice]:
                    choice=i
                indices[i]=choice
            self.prefix[capacity]=(best,indices)
        best,indices=self.prefix[capacity]
        end=min(capacity,self.max_integer,int(math.floor(upper+1e-9)))
        chosen=float(indices[end])
        service=float(best[end])
        n=int(math.floor(upper*self.yield_rate+1e-9))
        limit=min(n,int(math.floor(capacity-upper+1e-9)))
        baseline=float(self.curves.curve(n)[limit])
        if baseline>=service:
            service,chosen=baseline,float(upper)
        return {"final_capacity":capacity,"normal_upper":float(upper),"chosen_normal_work":chosen,
                "fixed_forward_service":baseline,"controlled_service":service,
                "quality_seen_when_choosing_normal_work":False}

    def solve(self,raw):
        flow=forward(raw)
        pairs,inverse=np.unique(np.stack((CAPS[:,4],flow.loads[:,4]),axis=1),axis=0,return_inverse=True)
        weights=np.bincount(inverse,weights=PROB,minlength=len(pairs))
        records=[{**self.optimize_one(int(c),float(u)),"probability":float(w)} for (c,u),w in zip(pairs,weights)]
        controlled=sum(x["probability"]*x["controlled_service"] for x in records)
        baseline=sum(x["probability"]*x["fixed_forward_service"] for x in records)
        assert controlled>=baseline-1e-10
        return {"release":raw,"maximum_service_with_control":controlled,"fixed_forward_at_same_release":baseline,
                "service_increase":controlled-baseline,"capacity_upper_groups":len(records),
                "probability_of_normal_curtailment":sum(x["probability"] for x in records if x["chosen_normal_work"]<x["normal_upper"]-1e-8),
                "expected_normal_work_reduction":sum(x["probability"]*(x["normal_upper"]-x["chosen_normal_work"]) for x in records),
                "policy":records}
