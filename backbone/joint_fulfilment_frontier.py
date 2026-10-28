"""Optional downward allocation and pre-success setup in one service cover.

This is a separate extension of the frozen automatic-substitution baseline.
Under the surplus-only rework rule, B<D2 implies no rework. Substitution
tradeoffs therefore occur in states disjoint from positive-return setup choices.
Dropping partial substitutions that cannot complete the whole order increases
profit without reducing the full-order service objective. Completable shortages
k=D2-B cost30*k; pre-success setup trades lose F-G and gain binomial-tail b.
Combine both sets in one weighted cover, retaining the original decision times.
"""
from backbone.stochastic_setup_frontier import *
from backbone.adaptive_substitution import AdaptiveSubstitution
from backbone.exact_batch_quality import BetaBinomialTables


class SubstitutionPool(AdaptiveSubstitution):
    def __init__(self,core):
        self.q1,self.q2,self.eligible=core.q1,core.q2,core.eligible
        self.d1,self.d2=core.d1,core.d2
        self.a,self.b=core.a,core.b
        self.maximum=core.maximum
        kappa=getattr(core,"kappa",None)
        if kappa is None:
            self.grade2=BinomialTables(core.maximum,core.q2)
            self.high_given_low=BinomialTables(core.maximum,core.q1/(1-core.q2))
        else:
            self.grade2=BetaBinomialTables(core.maximum,kappa*core.q2,kappa*(1-core.q2))
            self.high_given_low=BetaBinomialTables(core.maximum,kappa*core.q1,kappa*(1-core.q1-core.q2))

    def aggregate(self,normal_counts,weights):
        mass=sum(float(w)*self.completion_masses(int(n)) for n,w in zip(normal_counts,weights))
        expected=sum(float(w)*self.expected_substitution(int(n)) for n,w in zip(normal_counts,weights))
        gaps=np.arange(1,self.d2+1)
        complete_quantity=float(gaps@mass)
        assert expected>=complete_quantity-1e-8
        return {"mass":mass,"expected_automatic_substitution":max(0.,expected),
                "completable_substitution_quantity":complete_quantity,
                "partial_unfulfillable_substitution":max(0.,expected-complete_quantity)}


def cover_actions(masses,losses,benefits,order,needed,round_boundary=None):
    z=np.zeros(len(masses))
    deterministic=np.zeros(len(masses))
    boundary=None
    multiplier=0.
    extra={}
    if needed>1e-14:
        cumulative=np.cumsum(masses[order]*benefits[order])
        stop=min(int(np.searchsorted(cumulative,needed)),len(order)-1)
        prior=float(cumulative[stop-1]) if stop else 0.
        index=int(order[stop])
        theta=min(1.,max(0.,(needed-prior)/(masses[index]*benefits[index])))
        z[order[:stop]]=1.
        deterministic[order[:stop]]=1.
        z[index]=theta
        selected=1.
        if round_boundary is not None:
            selected,extra=round_boundary(index,theta)
        assert theta-1e-10<=selected<=1+1e-10
        deterministic[index]=min(1.,selected)
        multiplier=float(losses[index]/benefits[index])
        boundary={"index":index,"fraction":theta,"deterministic_fraction":float(deterministic[index]),
                  "ratio":multiplier,**extra}
    random_loss=float(masses@(losses*z))
    deterministic_loss=float(masses@(losses*deterministic))
    dual=multiplier*needed+float(masses@np.minimum(0.,losses-multiplier*benefits))
    assert abs(dual-random_loss)<1e-7,(dual,random_loss)
    return {"z":z,"deterministic_z":deterministic,"boundary":boundary,
            "random_loss":random_loss,"deterministic_loss":deterministic_loss,
            "loss_dual":dual,"primal_dual_gap":random_loss-dual}


def joint_frontier(states,sub,pool,normal_counts,fee,targets,mode="selective"):
    if mode not in ("selective","none","always"):
        raise ValueError(mode)
    w,g,b=states["mass"],states["gain"],states["benefit"]
    if mode=="none":
        initial=np.zeros(len(w))
    elif mode=="always":
        initial=(states["R"]>0).astype(float)
    else:
        initial=((states["R"]>0)&(g>=fee)).astype(float)
    automatic=summarize_choice(states,initial,fee)
    base_profit=automatic["expected_profit"]+30*sub["expected_automatic_substitution"]
    base_service=automatic["fulfilment_probability"]-float(sub["mass"].sum())
    assert base_service>=-1e-9
    base_service=max(0.,base_service)
    setup_ids=(np.flatnonzero((initial==0)&(states["R"]>0)&(b>0)&(w*b>0))
               if mode=="selective" else np.array([],dtype=int))
    gaps=np.flatnonzero(sub["mass"]>0)+1
    masses=np.r_[w[setup_ids],sub["mass"][gaps-1]]
    losses=np.r_[fee-g[setup_ids],30*gaps]
    benefits=np.r_[b[setup_ids],np.ones(len(gaps))]
    kinds=np.r_[np.zeros(len(setup_ids),dtype=int),np.ones(len(gaps),dtype=int)]
    key_a=np.r_[states["A"][setup_ids],gaps]
    key_r=np.r_[states["R"][setup_ids],np.zeros(len(gaps),dtype=int)]
    with np.errstate(over="ignore",divide="ignore"):
        ratio=losses/benefits
    order=np.lexsort((key_r,key_a,kinds,ratio))
    maximum=base_service+float(masses@benefits)
    rows=[]
    for target in targets:
        row={"target":target,"feasible":bool(target<=maximum+1e-10)}
        if not row["feasible"]:
            rows.append(row)
            continue
        need=max(0.,target-base_service)
        def rounder(index,fraction):
            if kinds[index]==0:
                return 1.,{"kind":"setup","A":int(key_a[index]),"R":int(key_r[index])}
            k=int(key_a[index])
            rounded=pool.deterministic_boundary(normal_counts,k,float(masses[index]*fraction))
            return min(1.,rounded["selected_mass"]/masses[index]),{
                "kind":"substitution","gap":k,"fine_prefix":rounded}
        solution=cover_actions(masses,losses,benefits,order,need,rounder)
        def summarize(z,loss):
            setup_z=z[:len(setup_ids)]
            sub_z=z[len(setup_ids):]
            return {"expected_profit":base_profit-loss,
                    "fulfilment_probability":base_service+float(masses@(benefits*z)),
                    "expected_rework":automatic["expected_rework"]+float(w[setup_ids]@(setup_z*states["R"][setup_ids])),
                    "activation_probability":automatic["activation_probability"]+float(w[setup_ids]@setup_z),
                    "expected_substitution":float(sub["mass"][gaps-1]@(sub_z*gaps))}
        randomized=summarize(solution["z"],solution["random_loss"])
        deterministic=summarize(solution["deterministic_z"],solution["deterministic_loss"])
        assert deterministic["fulfilment_probability"]>=target-1e-9
        gap=solution["deterministic_loss"]-solution["random_loss"]
        row.update({"randomized_optimum":randomized,"deterministic_feasible":deterministic,
            "deterministic_gap_bound":max(0.,gap),"boundary":solution["boundary"],
            "loss_dual":solution["loss_dual"],"primal_dual_gap":solution["primal_dual_gap"]})
        rows.append(row)
    return {"mode":mode,"profit_best_no_substitution":{"expected_profit":base_profit,"fulfilment_probability":base_service},
            "maximum_service":maximum,"substitution_completion_mass":float(sub["mass"].sum()),
            "expected_automatic_substitution":sub["expected_automatic_substitution"],
            "partial_unfulfillable_substitution":sub["partial_unfulfillable_substitution"],
            "setup_tradeoff_states":len(setup_ids),"substitution_gap_bands":len(gaps),"frontier":rows}
