"""One-factor robustness extension: batch-correlated INITIAL quality only.

Normal flow, repair eligibility definition, iid future repair successes, cash
and nonanticipative policy timing stay fixed. Initial counts follow a four-class
Dirichlet-multinomial with unchanged means and specified kappa. Neutral category
aggregation replaces five initial-count tables by beta-binomial tables.
The observed (A,R) return-law identity remains valid for any such joint law.
"""
from backbone.stochastic_setup_frontier import *
from backbone.exact_batch_quality import BetaBinomialTables


class BatchStochasticSetup(StochasticSetupFrontier):
    def __init__(self,q1,q2,f,demands,kappa,station_index=4,eta=.97,maximum=1600):
        if kappa<=0 or not (0<q1 and 0<q2 and q1+q2<1 and 0<f<1):
            raise ValueError("nondegenerate initial classes and positive kappa required")
        self.q1,self.q2,self.eligible=q1,q2,f
        self.d1,self.d2=map(int,demands)
        assert tuple(demands)==(self.d1,self.d2)
        self.kappa,self.station_index,self.eta=kappa,station_index,eta
        self.maximum,self.mass_cutoff=maximum,1e-20
        self.unit_cost=MANUFACTURING_COSTS[station_index]
        assert eta*90>30+self.unit_cost
        self.r_values=np.arange(maximum+1)
        self.success=BinomialTables(maximum,eta)
        bb=lambda alpha,beta:BetaBinomialTables(maximum,kappa*alpha,kappa*beta)
        defect=1-q1-q2
        self.a=bb(q1,1-q1)
        self.b=bb(q2,defect)
        self.e=bb(q2*f,q2*(1-f))
        self.marginal_eligible=bb(q2*f,q2*(1-f)+defect)
        self.other_given_eligible=bb(q2*(1-f),defect)

    def no_repair_service(self,n):
        aa=np.arange(self.d1,n+1)
        if len(aa)==0:
            return 0.
        need=np.maximum(self.d1+self.d2-aa,0)
        remaining=n-aa
        valid=need<=remaining
        return float(self.a.pmf[n,aa[valid]]@self.b.tail[remaining[valid],need[valid]])

    def state_masses(self,raw,setup):
        result=super().state_masses(raw,setup)
        # Parent's normal-quality no-repair screen uses a binomial model.
        # Replace this baseline by the DM baseline; all other state quantities
        # already use this instance's beta-binomial tables.
        n=np.floor(forward(raw).finished+1e-9).astype(int)
        ns,inverse=np.unique(n,return_inverse=True)
        weights=np.bincount(inverse,weights=PROB,minlength=len(ns))
        result["base_service"]=float(weights@np.array([self.no_repair_service(int(x)) for x in ns]))
        return result


class BatchRepairabilityBound(NestedQualityBound):
    def __init__(self,q1,q2,f,demands,kappa,maximum=1600):
        self.h=q1+q2*f
        self.total=q1+q2
        self.d1,self.d2=map(int,demands)
        self.high=BetaBinomialTables(maximum,kappa*self.h,kappa*(1-self.h))
        self.other=None if f==1 else BetaBinomialTables(maximum,kappa*q2*(1-f),kappa*(1-self.total))
