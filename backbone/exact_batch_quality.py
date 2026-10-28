"""Exact Dirichlet-multinomial extension by neutral category aggregation.

If (PA,PE,PI,PD)~Dirichlet(kappa*q), aggregate and condition in this order:
A~BetaBin(N,k*q1,k*(1-q1));
B|A~BetaBin(N-A,k*q2,k*(1-q1-q2));
E|B~BetaBin(B,k*q2*f,k*q2*(1-f)).
The three neutral ratios are independent. Reuse the conditional service/capped
expectation formulas, replacing the three binomial tables by beta-binomial ones.
"""
from backbone.exact_quality_economics import *


class BetaBinomialTables:
    def __init__(self,maximum,alpha,beta):
        if alpha<=0 or beta<=0:
            raise ValueError("positive beta-binomial parameters required")
        self.maximum=maximum
        self.pmf=np.zeros((maximum+1,maximum+2))
        self.tail=np.zeros_like(self.pmf)
        logfact=np.array([math.lgamma(k+1) for k in range(maximum+1)])
        la=np.array([math.lgamma(k+alpha) for k in range(maximum+1)])
        lb=np.array([math.lgamma(k+beta) for k in range(maximum+1)])
        normal=math.lgamma(alpha+beta)-math.lgamma(alpha)-math.lgamma(beta)
        largest=0.
        for n in range(maximum+1):
            k=np.arange(n+1)
            row=np.exp(logfact[n]-logfact[k]-logfact[n-k]+la[k]+lb[n-k]
                       -math.lgamma(n+alpha+beta)+normal)
            largest=max(largest,abs(float(row.sum())-1.))
            self.pmf[n,:n+1]=row
            self.tail[n,:n+1]=np.cumsum(row[::-1])[::-1]
            self.tail[n,0]=1.
        assert largest<2e-10,largest
        self.largest_mass_error=largest


class ExactBatchQualityEconomics(ExactQualityEconomics):
    def __init__(self,q1,q2,eligible,demands,kappa,maximum=1600,eta=.97):
        if kappa<=0 or not 0<eligible<1:
            raise ValueError("positive concentration and nondegenerate eligibility required")
        self.q1,self.q2,self.eligible=q1,q2,eligible
        self.d1,self.d2=map(int,demands)
        assert tuple(demands)==(self.d1,self.d2)
        self.eta=eta
        assert eta*90>35.5
        self.maximum=maximum
        self.kappa=kappa
        self.a=BetaBinomialTables(maximum,kappa*q1,kappa*(1-q1))
        self.b=BetaBinomialTables(maximum,kappa*q2,kappa*(1-q1-q2))
        self.e=BetaBinomialTables(maximum,kappa*q2*eligible,kappa*q2*(1-eligible))


def clear_solver_caches(solver):
    for name in ("conditional","expected_return","no_return_revenue","net_revenue_and_return"):
        getattr(solver,name).cache_clear()
