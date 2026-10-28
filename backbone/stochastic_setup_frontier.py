"""Setup/service frontier when future integer repair success is unknown.

For observed A and maximal allowed return R, expected repair gain G(A,R) and
service increment b(A,R) depend on A,R only. Since the unit marginal gain is
positive, each positive return amount is dominated by R in expected profit and
service. With setup fee F, choices reduce to closed vs open-at-R.
The profit-best choice opens if G>=F. To improve service choose closed states
in increasing (F-G)/b, weighted by their probability times b (not probability
alone). One fractional boundary gives the randomized-policy LP optimum; rounding
it up gives a feasible deterministic policy and a primal/dual gap bound.
Certificate concerns this finite probability model, not parameter uncertainty.
"""
from functools import lru_cache
from backbone.integer_rework import *
from backbone.round59_repairability_ceiling import NestedQualityBound


class StochasticSetupFrontier(IntegerReworkEconomics):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        pe=self.q2*self.eligible/(1-self.q1)
        po=self.q2*(1-self.eligible)/(1-self.q1)
        self.marginal_eligible=BinomialTables(self.maximum,pe)
        self.other_given_eligible=BinomialTables(self.maximum,po/(1-pe))

    @lru_cache(maxsize=None)
    def unbounded_return_law(self,m):
        """R0=min(E,(E+O-D2)+), before capacity clipping.

        P(R0=k)=P(E=k)P(O>D2|E=k)+P(B=D2+k)P(E>=k|B=D2+k),
        with the additional P(B<D2) for k=0. Two disjoint ways to hit k:
        eligibility binds strictly, or low-grade reservation binds.
        """
        if m<=self.d2:
            return np.array([1.])
        ks=np.arange(m-self.d2+1)
        first=np.zeros(len(ks))
        feasible=m-ks>=self.d2+1
        first[feasible]=(self.marginal_eligible.pmf[m,ks[feasible]]*
            self.other_given_eligible.tail[m-ks[feasible],self.d2+1])
        second=self.b.pmf[m,self.d2+ks]*self.e.tail[self.d2+ks,ks]
        result=first+second
        result[0]+=float(self.b.pmf[m,:self.d2].sum())
        assert abs(float(result.sum())-1)<1e-9,(m,result.sum())
        return result

    def state_masses(self,raw,setup):
        flow=forward(raw)
        ns=np.floor(flow.finished+1e-9).astype(int)
        j=self.station_index
        limits=np.floor(np.maximum(CAPS[:,j]-flow.loads[:,j]-setup,0.)+1e-9).astype(int)
        limits=np.minimum(limits,ns)
        groups,inverse=np.unique(np.stack((ns,limits),axis=1),axis=0,return_inverse=True)
        weights=np.bincount(inverse,weights=PROB,minlength=len(groups))
        joint=np.zeros((int(ns.max())+1,int(limits.max())+1))
        base_revenue=base_service=0.
        no_repair=NestedQualityBound(self.q1,self.q2,0.,(self.d1,self.d2),self.maximum)
        for (n,limit),w in zip(groups,weights):
            n,limit=int(n),int(limit)
            base_revenue+=w*self.no_return_revenue(n)
            base_service+=w*no_repair.probability(n)
            for a,pa in enumerate(self.a.pmf[n,:n+1]):
                if pa==0:
                    continue
                law=self.unbounded_return_law(n-a)
                cap=min(limit,len(law)-1)
                joint[a,:cap]+=w*pa*law[:cap]
                joint[a,cap]+=w*pa*float(law[cap:].sum())
        NestedQualityBound.probability.cache_clear()
        normal_cost=mean(flow.loads[:,0]*MATERIAL_COST+np.sum(flow.loads*MANUFACTURING_COSTS,axis=1))
        aa,rr=np.nonzero(joint)
        masses=joint[aa,rr]
        gap=np.maximum(self.d1-aa,0)
        fill=mean_min(self.success,self.eta,rr,gap)
        gains=(90*self.eta-30-self.unit_cost)*rr+30*fill
        benefits=np.where((gap>0)&(rr>0),self.success.tail[rr,gap],0.)
        assert abs(float(masses.sum())-1)<1e-9
        return {"A":aa,"R":rr,"mass":masses,"gain":gains,"benefit":benefits,
                "base_profit":base_revenue-normal_cost,"base_service":base_service,
                "groups":len(groups),"joint_mass_error":abs(float(masses.sum())-1)}


def summarize_choice(states,opened,fee):
    w=states["mass"]
    return {"expected_profit":float(states["base_profit"]+w@(opened*(states["gain"]-fee))),
            "fulfilment_probability":float(states["base_service"]+w@(opened*states["benefit"])),
            "expected_rework":float(w@(opened*states["R"])),
            "activation_probability":float(w@opened)}


def solve_setup_frontier(states,fee,targets):
    w,g,b=states["mass"],states["gain"],states["benefit"]
    opened=((states["R"]>0)&(g>=fee)).astype(float)
    baseline=summarize_choice(states,opened,fee)
    eligible=np.flatnonzero((opened==0)&(states["R"]>0)&(b>0))
    losses=fee-g
    with np.errstate(over="ignore",divide="ignore"):
        ratios=losses[eligible]/b[eligible]
    order=eligible[np.lexsort((states["R"][eligible],states["A"][eligible],ratios))]
    available=w[order]*b[order]
    maximum=baseline["fulfilment_probability"]+float(available.sum())
    records=[]
    for target in targets:
        row={"target":target,"feasible":bool(target<=maximum+1e-12)}
        if not row["feasible"]:
            records.append(row)
            continue
        need=max(0.,target-baseline["fulfilment_probability"])
        random=opened.copy()
        deterministic=opened.copy()
        boundary=None
        multiplier=0.
        bound=0.
        if need>0:
            cumulative=np.cumsum(available)
            stop=min(int(np.searchsorted(cumulative,need)),len(order)-1)
            random[order[:stop]]=1.
            deterministic[order[:stop+1]]=1.
            index=int(order[stop])
            prior=float(cumulative[stop-1]) if stop else 0.
            z=min(1.,max(0.,(need-prior)/available[stop]))
            random[index]=z
            multiplier=float(losses[index]/b[index])
            bound=float(w[index]*losses[index]*(1-z))
            boundary={"A":int(states["A"][index]),"R":int(states["R"][index]),
                      "ratio":multiplier,"randomized_open_probability":z,
                      "observed_state_mass":float(w[index]),"conditional_service_gain":float(b[index])}
        rand=summarize_choice(states,random,fee)
        det=summarize_choice(states,deterministic,fee)
        dual=multiplier*need+float(w[eligible]@np.minimum(0.,losses[eligible]-multiplier*b[eligible]))
        primal=baseline["expected_profit"]-rand["expected_profit"]
        assert abs(dual-primal)<1e-7,(dual,primal)
        assert det["fulfilment_probability"]>=target-1e-10
        assert abs(rand["expected_profit"]-det["expected_profit"]-bound)<1e-7
        row.update({"randomized_optimum":rand,"deterministic_feasible":det,
                    "deterministic_gap_upper_bound":bound,"boundary":boundary,
                    "lagrangian_loss_lower_bound":dual,"primal_dual_gap":primal-dual})
        records.append(row)
    return {"setup_fee":fee,"profit_best":baseline,"maximum_service":maximum,
            "positive_service_tradeoff_states":len(order),"frontier":records}


def execute_prefix(a,r,solver,fee,boundary):
    """Only pre-success A,R and a frozen recorded threshold are inspected."""
    a,r=np.broadcast_arrays(np.asarray(a,dtype=int),np.asarray(r,dtype=int))
    gap=np.maximum(solver.d1-a,0)
    fill=mean_min(solver.success,solver.eta,r,gap)
    gain=(90*solver.eta-30-solver.unit_cost)*r+30*fill
    benefit=np.where((gap>0)&(r>0),solver.success.tail[r,gap],0.)
    opened=(r>0)&(gain>=fee)
    if boundary is not None:
        eligible=(~opened)&(r>0)&(benefit>0)
        with np.errstate(divide="ignore",over="ignore",invalid="ignore"):
            ratio=np.divide(fee-gain,benefit,out=np.full(a.shape,np.inf),where=benefit>0)
        before=(ratio<boundary["ratio"])|((ratio==boundary["ratio"])&
            ((a<boundary["A"])|((a==boundary["A"])&(r<=boundary["R"]))))
        opened|=eligible&before
    return opened
