"""Integer single-pass rework, with outcomes revealed after the return decision.

Initial A,B,E are multinomial grade/subtype counts. Observe them and capacity,
then send r=min(E,(B-D2)+,floor(spare)); Y|r~Bin(r,eta) is still unknown.
Failure is scrap. No downstream route or collateral KQC damage is represented.
Costs and future-sale assumptions match the specified cash benchmark (H=30).
When 90*eta > 30+unit_cost, maximal r is optimal in this restricted action set:
the expected increment is 90*eta-30-unit_cost +30*eta*Pr(A+Y_r<D1)>0.
This is not a claim over actions allowed to consume the low-grade reservation.

The formula is a finite sum. Small a/b masses may be omitted for performance;
their actual summed mass and a conservative gain bound are returned explicitly.
Eligibility and future-success sums are not simulated or truncated.
"""
from functools import lru_cache
from backbone.exact_quality_economics import *


class IntegerReworkEconomics(ExactQualityEconomics):
    def __init__(self,q1,q2,f,demands,station_index=4,eta=.97,maximum=1600,mass_cutoff=1e-20):
        super().__init__(q1,q2,f,demands,maximum,eta)
        self.station_index=station_index
        self.unit_cost=MANUFACTURING_COSTS[station_index]
        assert 90*eta>30+self.unit_cost
        self.success=BinomialTables(maximum,eta)
        self.mass_cutoff=mass_cutoff
        self.r_values=np.arange(maximum+1)

    def capped_eligibility_expectation(self,bs,caps,values):
        """E[values(min(E,cap))|B=b], including saturated upper eligibility tail."""
        maximum=int(np.max(caps,initial=0))
        if maximum==0:
            return np.full(len(bs),values[0])
        es=np.arange(maximum)
        weights=self.e.pmf[bs,:maximum]*(es[None,:]<caps[:,None])
        return weights@values[:maximum]+self.e.tail[bs,caps]*values[caps]

    @lru_cache(maxsize=20000)
    def metrics(self,n,spare,mode="binomial"):
        if mode not in ("binomial","integer_mean"):
            raise ValueError(mode)
        n=int(n)
        spare=max(0,min(n,int(spare)))
        base=self.no_return_revenue(n)
        service=sent=gain=omitted=0.
        pa=self.a.pmf[n,:n+1]
        aa=np.flatnonzero(pa>self.mass_cutoff)
        omitted+=float(pa[pa<=self.mass_cutoff].sum())
        for a in aa:
            m=n-a
            pb=self.b.pmf[m,:m+1]
            bs=np.flatnonzero(pb>self.mass_cutoff)
            omitted+=pa[a]*float(pb[pb<=self.mass_cutoff].sum())
            caps=np.minimum(np.maximum(bs-self.d2,0),spare)
            er=mean_min(self.e,self.eligible,bs,caps)
            gap=max(self.d1-a,0)
            if gap==0:
                full=(a+bs>=self.d1+self.d2).astype(float)
                fill=np.zeros(len(bs))
            else:
                if mode=="binomial":
                    full_values=self.success.tail[:,gap]
                    fill_values=mean_min(self.success,self.eta,self.r_values,gap)
                else:
                    full_values=(self.eta*self.r_values>=gap-EPS).astype(float)
                    fill_values=np.minimum(self.eta*self.r_values,gap)
                full=self.capped_eligibility_expectation(bs,caps,full_values)
                # Reserving D2 forbids service if B<D2 even when grade1 can be repaired.
                full=np.where(bs>=self.d2,full,0.)
                fill=self.capped_eligibility_expectation(bs,caps,fill_values)
            gain_by_b=(90*self.eta-30-self.unit_cost)*er+30*fill
            service+=pa[a]*float(pb[bs]@full)
            sent+=pa[a]*float(pb[bs]@er)
            gain+=pa[a]*float(pb[bs]@gain_by_b)
        assert -1e-10<=service<=1+1e-10
        return {"net_revenue":base+gain,"service":float(service),"expected_rework":float(sent),
                "omitted_mass":float(omitted),
                "gain_omission_bound":float(omitted*n*(120*self.eta-30-self.unit_cost))}

    def evaluate_integer(self,raw,setup=0.,mode="binomial"):
        flow=forward(raw)
        n=np.floor(flow.finished+1e-9).astype(int)
        j=self.station_index
        spare=np.floor(np.maximum(CAPS[:,j]-flow.loads[:,j]-setup,0.)+1e-9).astype(int)
        spare=np.minimum(spare,n)
        groups,inverse=np.unique(np.stack((n,spare),axis=1),axis=0,return_inverse=True)
        weights=np.bincount(inverse,weights=PROB,minlength=len(groups))
        records=[self.metrics(int(nn),int(ll),mode) for nn,ll in groups]
        expected=lambda key:float(weights@np.array([x[key] for x in records]))
        cost=mean(flow.loads[:,0]*MATERIAL_COST+np.sum(flow.loads*MANUFACTURING_COSTS,axis=1))
        return {"input":raw,"setup_workload":setup,"mode":mode,"capacity_groups":len(groups),
                "expected_profit":expected("net_revenue")-cost,
                "fulfilment_probability":expected("service"),"expected_rework":expected("expected_rework"),
                "service_sum_omission_bound":expected("omitted_mass"),
                "profit_sum_omission_bound":expected("gain_omission_bound"),
                "table_max_mass_error":max(t.largest_mass_error for t in (self.a,self.b,self.e,self.success))}


def release_integer_caches(solver):
    from backbone.exact_batch_quality import clear_solver_caches
    clear_solver_caches(solver)
    IntegerReworkEconomics.metrics.cache_clear()
