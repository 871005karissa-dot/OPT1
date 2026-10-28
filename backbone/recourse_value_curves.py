"""Cached unconstrained-profit setup values, for safe outer-release screening.

For a known pre-success state (A,R), positive unit gain means only0/R matter.
The profit-best incremental value is (G(A,R)-F)+; its service increment is
b(A,R)*1(G>=F,R>0). Integrate either function against the capped R0 law via
prefix sums. Add no-return revenue/service separately. The resulting profit
is an upper bound for any service-constrained policy at that fixed release.
No additional economic mechanism or terminal-value change is introduced.
"""
from backbone.maximal_service_curve import *


class RecourseValueCurves(MaximalServiceCurves):
    @staticmethod
    def capped_values(laws,tails,values):
        weighted=laws*values
        prefix=np.zeros_like(weighted)
        prefix[:,1:]=np.cumsum(weighted[:,:-1],axis=1)
        return prefix+tails*values

    @lru_cache(maxsize=None)
    def values(self,n,fee):
        n=int(n)
        if fee<0:
            raise ValueError("This screening model assumes nonnegative setup fees")
        s=self.solver
        base_revenue=s.no_return_revenue(n)
        base_service=self.no_return_service(n)
        if n<=s.d2:
            return {"net_revenue":np.full(self.maximum+1,base_revenue),
                    "service":np.full(self.maximum+1,base_service)}
        rmax=n-s.d2
        rr=np.arange(rmax+1)[None,:]
        aa=np.flatnonzero(s.a.pmf[n,:n+1]>0)
        profit=np.zeros(rmax+1)
        service=np.zeros(rmax+1)
        for start in range(0,len(aa),128):
            a=aa[start:start+128]
            m=n-a
            gap=np.maximum(s.d1-a,0)[:,None]
            fill=mean_min(s.success,s.eta,rr,gap)
            gain=(90*s.eta-30-s.unit_cost)*rr+30*fill
            active=(rr>0)&(gain>=fee)
            rescue=np.where(gap>0,s.success.tail[rr,gap],0.)
            masses=s.a.pmf[n,a]
            laws=self.laws[m,:rmax+1]
            tails=self.tails[m,:rmax+1]
            profit+=masses@self.capped_values(laws,tails,(gain-fee)*active)
            service+=masses@self.capped_values(laws,tails,rescue*active)
        p=np.empty(self.maximum+1)
        r=np.empty(self.maximum+1)
        p[:rmax+1]=base_revenue+profit
        r[:rmax+1]=base_service+service
        p[rmax+1:]=p[rmax]
        r[rmax+1:]=r[rmax]
        return {"net_revenue":p,"service":r}

    def evaluate_profit_best(self,raw,fee,setup=0.,fully_committed=False):
        s=self.solver
        flow=forward(raw)
        n=np.floor(flow.finished+1e-9).astype(int)
        spare=np.minimum(n,np.floor(np.maximum(CAPS[:,s.station_index]-flow.loads[:,s.station_index]-setup,0.)+1e-9).astype(int))
        groups,inverse=np.unique(np.stack((n,spare),axis=1),axis=0,return_inverse=True)
        weights=np.bincount(inverse,weights=PROB,minlength=len(groups))
        p=np.array([self.values(int(nn),fee)["net_revenue"][int(ll)] for nn,ll in groups])
        r=np.array([self.values(int(nn),fee)["service"][int(ll)] for nn,ll in groups])
        material=raw*MATERIAL_COST if fully_committed else mean(flow.loads[:,0])*MATERIAL_COST
        cost=material+mean(np.sum(flow.loads*MANUFACTURING_COSTS,axis=1))
        return {"expected_profit":float(weights@p)-cost,"fulfilment_probability":float(weights@r)}

    @lru_cache(maxsize=None)
    def always_return_values(self,n,fee):
        """All maximal returns, including unprofitable startups, for fair baselines.

        For any L>=1, activation iff R0>=1; hence its probability is independent
        of the positive capacity level. At fee0 the positive marginal condition
        makes values(n,0) exactly the all-return policy.
        """
        s=self.solver
        aa=np.arange(n+1)
        activation=float(s.a.pmf[n,:n+1]@self.tails[n-aa,1])
        free=self.values(n,0.)
        costs=np.full(self.maximum+1,fee*activation)
        costs[0]=0.
        return {"net_revenue":free["net_revenue"]-costs,"service":free["service"],
                "activation_when_capacity_positive":activation}
