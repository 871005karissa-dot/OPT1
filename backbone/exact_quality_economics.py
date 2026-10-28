"""Exact expected cash profit of the fixed-forward maximal-return quality policy.

Builds on exact_quality_service's assumptions; no optimization of forward work.
The binomial tail-sum identity evaluates capped expected quantities. Conditional
on A, integrate B and eligible E analytically rather than substitute mean counts.
"""
from functools import lru_cache
from backbone.exact_quality_service import *


def mean_min(table,probability,ns,limits):
    ns,limits=np.broadcast_arrays(np.asarray(ns,dtype=int),np.asarray(limits,dtype=float))
    t=np.clip(limits,0.,ns)
    k=np.floor(t).astype(int)
    if not hasattr(table,"prefix_tail"):
        table.prefix_tail=np.zeros_like(table.tail)
        table.prefix_tail[:,1:]=np.cumsum(table.tail[:,1:],axis=1)
    result=table.prefix_tail[ns,k]+(t-k)*table.tail[ns,k+1]
    return np.where(limits>=ns,ns*probability,result)


class ExactQualityEconomics(ExactQualityService):
    @lru_cache(maxsize=500000)
    def expected_return(self,remaining,spare):
        if remaining<=self.d2 or spare<=0:
            return 0.
        bs=np.arange(self.d2+1,remaining+1)
        caps=np.minimum(bs-self.d2,spare)
        expected=mean_min(self.e,self.eligible,bs,caps)
        return float(np.dot(self.b.pmf[remaining,self.d2+1:remaining+1],expected))

    @lru_cache(maxsize=None)
    def no_return_revenue(self,n):
        aa=np.arange(n+1)
        remaining=n-aa
        pa=self.a.pmf[n,:n+1]
        p2=self.q2/(1-self.q1)
        low_grade_served=mean_min(self.b,p2,remaining,self.d2)
        excess1=np.maximum(aa-self.d1,0.)
        lower_shortage=np.maximum(self.d2-excess1,0.)
        short_before=self.d2-low_grade_served
        short_after=lower_shortage-mean_min(self.b,p2,remaining,lower_shortage)
        substitution=short_before-short_after
        value=90*n*self.q1+30*n*self.q2
        value+=30*float(np.dot(pa,np.minimum(aa,self.d1)))
        value+=30*float(np.dot(pa,low_grade_served))
        value-=30*float(np.dot(pa,substitution))
        return value

    @lru_cache(maxsize=None)
    def net_revenue_and_return(self,n,spare):
        """Sales less return cost, prior to all normal-flow material/work costs."""
        revenue=self.no_return_revenue(n)
        if spare<=0:
            return revenue,0.
        gain=sent=0.
        for a,prob in enumerate(self.a.pmf[n,:n+1]):
            if prob<1e-300:
                continue
            remaining=n-a
            r=self.expected_return(remaining,spare)
            fill=self.expected_return(remaining,min(spare,max(self.d1-a,0.)/self.eta))
            sent+=prob*r
            gain+=prob*((90*self.eta-35.5)*r+30*self.eta*fill)
        return revenue+gain,sent

    def evaluate_economics(self,raw,setup=350.):
        flow=forward(raw)
        n=np.floor(flow.finished+1e-9).astype(int)
        spare=np.maximum(CAPS[:,1]-flow.loads[:,1]-setup,0.)
        groups,inverse=np.unique(np.stack((n,spare),axis=1),axis=0,return_inverse=True)
        weights=np.bincount(inverse,weights=PROB,minlength=len(groups))
        values=np.array([self.net_revenue_and_return(int(group[0]),float(group[1])) for group in groups])
        normal_cost=mean(flow.loads[:,0]*MATERIAL_COST+np.sum(flow.loads*MANUFACTURING_COSTS,axis=1))
        service,_=self.evaluate(raw,setup)
        return {"input":raw,"expected_profit":float(weights@values[:,0])-normal_cost,
                "fulfilment_probability":service,"expected_rework":float(weights@values[:,1]),
                "expected_normal_processing_and_material_cost":normal_cost,"capacity_groups":len(groups)}
