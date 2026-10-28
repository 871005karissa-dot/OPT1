"""Exact whole-order service for fixed forward flow and multinomial quality.

Restriction: known eta whose fill and excess marginal profits are positive,
so sending the whole eligible/spare/surplus cap is profit-optimal (eta=.97 here).
Grade counts are integer multinomial; return work and eta remain fluid.
Conditional on A=grade1, B=grade2 ~ Bin(N-A,q2/(1-q1)); E|B~Bin(B,f).
For A<D1, service needs E>=k, B>=D2+k and eta*spare>=D1-A,
where k=ceil((D1-A-EPS)/eta). For A>=D1, only A+B>=D1+D2 is needed.
This evaluates the implemented fixed-forward profit-best policy, not an upper
bound obtained by adapting forward work after seeing the quality counts.
"""
from functools import lru_cache
import math
from backbone.quality_lab import *


class BinomialTables:
    def __init__(self,maximum,probability):
        if not 0<probability<1:
            raise ValueError("tables require a nondegenerate binomial")
        self.maximum=maximum
        self.pmf=np.zeros((maximum+1,maximum+2))
        self.tail=np.zeros_like(self.pmf)
        logfact=np.array([math.lgamma(k+1) for k in range(maximum+1)])
        logp,logq=math.log(probability),math.log1p(-probability)
        largest_mass_error=0.
        for n in range(maximum+1):
            k=np.arange(n+1)
            row=np.exp(logfact[n]-logfact[k]-logfact[n-k]+k*logp+(n-k)*logq)
            largest_mass_error=max(largest_mass_error,abs(float(row.sum())-1.))
            self.pmf[n,:n+1]=row
            self.tail[n,:n+1]=np.cumsum(row[::-1])[::-1]
            self.tail[n,0]=1.
        assert largest_mass_error<2e-10
        self.largest_mass_error=largest_mass_error


class ExactQualityService:
    def __init__(self,q1,q2,eligible,demands,maximum=1600,eta=.97):
        self.q1,self.q2,self.eligible=q1,q2,eligible
        self.d1,self.d2=map(int,demands)
        assert (self.d1,self.d2)==tuple(demands)
        self.eta=eta
        assert eta*90>35.5  # both marginal profit regions positive at H=30.
        self.a=BinomialTables(maximum,q1)
        self.b=BinomialTables(maximum,q2/(1-q1))
        self.e=BinomialTables(maximum,eligible)
        self.maximum=maximum

    @lru_cache(maxsize=None)
    def conditional(self,n,spare):
        n=int(n)
        value=0.
        pa=self.a.pmf[n]
        for a in range(n+1):
            if pa[a]<1e-300:
                continue
            remaining=n-a
            if a>=self.d1:
                threshold=max(0,self.d1+self.d2-a)
                chance=self.b.tail[remaining,threshold] if threshold<=remaining else 0.
            else:
                gap=self.d1-a
                if self.eta*spare<gap-EPS:
                    continue
                k=int(math.ceil((gap-EPS)/self.eta))
                lower=self.d2+k
                if lower>remaining:
                    continue
                bs=np.arange(lower,remaining+1)
                chance=float(np.dot(self.b.pmf[remaining,lower:remaining+1],self.e.tail[bs,k]))
            value+=pa[a]*chance
        assert -1e-10<=value<=1+1e-10
        return min(1.,max(0.,value))

    def evaluate(self,raw,setup=350.):
        flow=forward(raw)
        n=np.floor(flow.finished+1e-9).astype(int)
        spare=np.maximum(CAPS[:,1]-flow.loads[:,1]-setup,0.)
        groups,inverse=np.unique(np.stack((n,spare),axis=1),axis=0,return_inverse=True)
        weights=np.bincount(inverse,weights=PROB,minlength=len(groups))
        conditional=np.array([self.conditional(int(group[0]),float(group[1])) for group in groups])
        value=float(np.dot(weights,conditional))
        return value,{"capacity_groups":len(groups),"weight_mass":float(weights.sum()),
                      "table_max_probability_mass_error":max(t.largest_mass_error for t in (self.a,self.b,self.e))}
