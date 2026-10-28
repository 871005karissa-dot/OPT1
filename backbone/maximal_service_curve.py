"""Cache all spare-capacity service values for a normal output N in one pass.

Let p_m(r) be the unlimited-capacity return count distribution conditional on
A (m=N-A). For gap g>0 and capacity L,
  Pr(success>=g)=sum_{r<L}p_m(r)T_eta(r,g)+Pr(R0>=L)T_eta(L,g).
Compute all L by cumulative sums, then average over A and add no-repair service.
Works with the iid and DM initial-count tables, keeping future successes iid.
This avoids rebuilding an observed(A,R) probability table for a service-only
feasibility query. It does not solve the setup-profit LP.
"""
from functools import lru_cache
from backbone.stochastic_setup_frontier import *


class MaximalServiceCurves:
    def __init__(self,solver):
        self.solver=solver
        self.maximum=solver.maximum
        self.laws=np.zeros((self.maximum+1,self.maximum+1))
        for m in range(self.maximum+1):
            law=solver.unbounded_return_law(m)
            self.laws[m,:len(law)]=law
        self.tails=np.cumsum(self.laws[:,::-1],axis=1)[:,::-1]
        self.max_law_mass_error=float(np.max(np.abs(self.laws.sum(axis=1)-1)))

    def no_return_service(self,n):
        s=self.solver
        aa=np.arange(s.d1,n+1)
        if len(aa)==0:
            return 0.
        need=np.maximum(s.d1+s.d2-aa,0)
        remaining=n-aa
        valid=need<=remaining
        return float(s.a.pmf[n,aa[valid]]@s.b.tail[remaining[valid],need[valid]])

    @lru_cache(maxsize=None)
    def curve(self,n):
        n=int(n)
        s=self.solver
        if n<s.d1+s.d2:
            return np.zeros(self.maximum+1)
        aa=np.arange(min(s.d1,n+1))
        aa=aa[s.a.pmf[n,aa]>0]
        m=n-aa
        rmax=n-s.d2
        rr=np.arange(rmax+1)
        success=s.success.tail[rr[None,:],(s.d1-aa)[:,None]]
        weighted=self.laws[m,:rmax+1]*success
        prefix=np.zeros_like(weighted)
        prefix[:,1:]=np.cumsum(weighted[:,:-1],axis=1)
        values=s.a.pmf[n,aa]@(prefix+self.tails[m,:rmax+1]*success)
        values+=self.no_return_service(n)
        result=np.empty(self.maximum+1)
        result[:rmax+1]=values
        result[rmax+1:]=values[-1]
        assert np.min(np.diff(result))>=-1e-10
        assert -1e-10<=result.min() and result.max()<=1+1e-10
        return result

    def evaluate(self,raw,setup=0.):
        s=self.solver
        flow=forward(raw)
        n=np.floor(flow.finished+1e-9).astype(int)
        spare=np.floor(np.maximum(CAPS[:,s.station_index]-flow.loads[:,s.station_index]-setup,0.)+1e-9).astype(int)
        spare=np.minimum(n,spare)
        groups,inverse=np.unique(np.stack((n,spare),axis=1),axis=0,return_inverse=True)
        weights=np.bincount(inverse,weights=PROB,minlength=len(groups))
        values=np.array([self.curve(int(nn))[int(ll)] for nn,ll in groups])
        return float(weights@values)
