"""Exact optional-downward-substitution service frontier, fixed forward quality.

At H=30, replacing a future grade1 sale by current grade2 sale costs30/unit.
Without a shortage penalty, profit-best substitution is zero. If B<D2, rework
is unavailable under the surplus-only rule; whole-order completion is possible
iff A>=D1+(D2-B). Such an event costs30*(D2-B) to complete. All other recourse
remains the known eta=.97 maximal eligible return of exact_quality_economics.
"""
from backbone.exact_quality_economics import *


class AdaptiveSubstitution(ExactQualityEconomics):
    def __init__(self,q1,q2,f,demands,maximum=1600):
        super().__init__(q1,q2,f,demands,maximum)
        self.grade2=BinomialTables(maximum,q2)
        self.high_given_low=BinomialTables(maximum,q1/(1-q2))

    @lru_cache(maxsize=None)
    def expected_substitution(self,n):
        aa=np.arange(n+1)
        remaining=n-aa
        pa=self.a.pmf[n,:n+1]
        p2=self.q2/(1-self.q1)
        excess=np.maximum(aa-self.d1,0.)
        z=np.maximum(self.d2-excess,0.)
        loss0=self.d2-mean_min(self.b,p2,remaining,self.d2)
        loss1=z-mean_min(self.b,p2,remaining,z)
        return float(pa@(loss0-loss1))

    def completion_masses(self,n):
        gaps=np.arange(1,self.d2+1)
        if n<self.d1+self.d2:
            return np.zeros(len(gaps))
        b=self.d2-gaps
        return self.grade2.pmf[n,b]*self.high_given_low.tail[n-b,self.d1+gaps]

    def deterministic_boundary(self,ns,k,required):
        """Complete a prefix of observed (capacity, grade1, grade2) atoms."""
        if required<=1e-14:
            return {"selected_mass":0.,"extra_mass":0.,"boundary":None}
        b=self.d2-k
        selected=0.
        order=np.argsort(-PROB,kind="stable")
        for position,index in enumerate(order):
            n=int(ns[index])
            if n<self.d1+self.d2:
                continue
            amin=self.d1+k
            remaining=n-b
            atoms=PROB[index]*self.grade2.pmf[n,b]*self.high_given_low.pmf[remaining,amin:remaining+1]
            mass=float(atoms.sum())
            if selected+mass<required-1e-14:
                selected+=mass
                continue
            cumulative=np.cumsum(atoms)
            offset=min(int(np.searchsorted(cumulative,required-selected,side="left")),len(atoms)-1)
            selected+=float(cumulative[offset])
            extra=max(0.,selected-required)
            assert extra<=float(atoms[offset])+1e-10
            return {"selected_mass":selected,"extra_mass":extra,
                "boundary":{"capacity_order":"descending probability, stable original index on ties",
                    "capacity_position":position,"capacity_counts":COUNTS[index].tolist(),
                    "grade1_count":amin+offset,"grade2_count":b,
                    "atom_probability":float(atoms[offset]),
                    "interpretation":"Within this gap band, complete all earlier capacity states and all eligible grade1 counts up to this count in the boundary capacity state."}}
        assert selected>=required-1e-9
        return {"selected_mass":selected,"extra_mass":max(0.,selected-required),"boundary":None}

    def frontier(self,raw,targets):
        mandatory=self.evaluate_economics(raw)
        flow=forward(raw)
        ns=np.floor(flow.finished+1e-9).astype(int)
        counts,inverse=np.unique(ns,return_inverse=True)
        weights=np.bincount(inverse,weights=PROB)
        mass=sum(weight*self.completion_masses(int(n)) for n,weight in zip(counts,weights))
        expected_sub=sum(weight*self.expected_substitution(int(n)) for n,weight in zip(counts,weights))
        base_r=mandatory["fulfilment_probability"]-float(mass.sum())
        base_profit=mandatory["expected_profit"]+30*expected_sub
        maximum=mandatory["fulfilment_probability"]
        cumulative=np.cumsum(mass)
        rows=[]
        for target in targets:
            row={"target":target,"feasible":target<=maximum+1e-10}
            if not row["feasible"]:
                rows.append(row)
                continue
            needed=max(0.,min(target-base_r,maximum-base_r))
            if needed<=1e-14:
                cost=over=0.
                boundary=None
                actual_r=base_r
                gap=0
                boundary_mass=0.
            else:
                j=min(int(np.searchsorted(cumulative,needed,side="left")),len(mass)-1)
                before=float(cumulative[j-1]) if j else 0.
                residual=needed-before
                gap=j+1
                cost=float(np.dot(30*np.arange(1,j+1),mass[:j]))+30*gap*residual
                rounded=self.deterministic_boundary(ns,gap,residual)
                over=rounded["extra_mass"]*30*gap
                actual_r=base_r+before+rounded["selected_mass"]
                boundary=rounded["boundary"]
                boundary_mass=residual
            assert actual_r>=target-1e-9 or target<=base_r
            rows.append({**row,"randomized_optimum_profit":base_profit-cost,
                "randomized_service":max(base_r,target),"deterministic_feasible_profit":base_profit-cost-over,
                "deterministic_service":actual_r,"deterministic_profit_gap_bound":over,
                "boundary_substitution_gap":gap,"randomized_boundary_mass":boundary_mass,"boundary":boundary})
        return {"input":raw,"mandatory_substitution":mandatory,
            "profit_best_no_substitution":{"expected_profit":base_profit,"fulfilment_probability":base_r},
            "maximum_fulfilment_probability":maximum,"expected_mandatory_substitution":expected_sub,
            "completion_probability_by_substitution_gap":mass.tolist(),"frontier":rows,
            "complete_only_when_feasible_profit":base_profit-float(np.dot(30*np.arange(1,self.d2+1),mass))}
