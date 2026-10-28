"""Round60: normal marginals alone do not identify joint grade/repairability.

For feature-wise allowed events S_i subset W_i, H=intersection S_i (potential
grade1 after the one specified perfect repair) and T=intersection W_i.
Union bounds give max(0,sum pS_i-m+1)<=Pr(H)<=min pS_i, likewise for T.
The perfect-unlimited service function is monotone in both nested probabilities.
Coordinate lower endpoints give a conservative screen lower endpoint (not
actual feasible-policy service), and upper endpoints are simultaneously attainable
using S_i=[0,pS_i],W_i=[0,pW_i] on a shared uniform variable.
Independence of features is thus a modeling assumption, not a consequence of
normal marginal means/standard deviations. This is within-item dependence,
distinct from the between-item batch dependence in rounds52/55/56.
"""
import time
from backbone.round59_repairability_ceiling import NestedQualityBound
from backbone.round42_one_sided_repair import *


def frechet(probabilities):
    return max(0.,sum(probabilities)-len(probabilities)+1),min(probabilities)


def verify_joint_laws():
    cells=np.array(list(product(range(4),repeat=4)))
    rng=np.random.default_rng(20261028060)
    checks=[]
    for _ in range(64):
        masses=rng.dirichlet(np.full(len(cells),.25))
        strict=np.array([masses[cells[:,i]==0].sum() for i in range(4)])
        wide=np.array([masses[cells[:,i]!=3].sum() for i in range(4)])
        for j in range(4):
            allowed=strict.copy()
            allowed[j]+=masses[cells[:,j]==1].sum()
            hm=np.all(cells==0,axis=1)|((cells[:,j]==1)&np.all(np.delete(cells,j,axis=1)==0,axis=1))
            tm=np.all(cells!=3,axis=1)
            h,t=float(masses[hm].sum()),float(masses[tm].sum())
            hl,hu=frechet(allowed)
            tl,tu=frechet(wide)
            assert hl-1e-12<=h<=hu+1e-12 and tl-1e-12<=t<=tu+1e-12
            # A direct joint uniform construction attains both upper endpoints.
            breaks=np.unique(np.r_[0.,allowed,wide,1.])
            mids=(breaks[:-1]+breaks[1:])/2
            lengths=np.diff(breaks)
            hc=float(lengths[np.all(mids[:,None]<allowed,axis=1)].sum())
            tc=float(lengths[np.all(mids[:,None]<wide,axis=1)].sum())
            checks.append(max(abs(hc-hu),abs(tc-tu)))
            assert checks[-1]<1e-12
    return checks


def main():
    started=time.perf_counter()
    checks=verify_joint_laws()
    probabilities=component_probabilities(KQCS)
    strict=np.array([x[0] for x in probabilities])
    wide=np.array([x[1] for x in probabilities])
    quality,directions=one_sided_bounds()
    q1,q2=quality["implied_grade1_share"],quality["implied_grade2_share"]
    nmax=np.floor(forward(100000.).finished+1e-9).astype(int)
    ns,inverse=np.unique(nmax,return_inverse=True)
    weights=np.bincount(inverse,weights=PROB,minlength=len(ns))
    def screen(h,t):
        solver=NestedQualityBound(h,t-h,0.,(750,150))
        value=float(weights@np.array([solver.probability(int(n)) for n in ns]))
        NestedQualityBound.probability.cache_clear()
        return value
    rows=[]
    tl,tu=frechet(wide)
    for j,direction in ((0,"decrease_value_bound"),(1,"increase_value_bound"),(2,"decrease_value_bound"),(3,"decrease_value_bound")):
        allowed=strict.copy()
        # f is conditional on grade2 under independence; undo it to get the
        # one-feature marginal tail probability before imposing dependence.
        tail=directions[j][direction]*q2/float(np.prod(np.delete(strict,j)))
        allowed[j]+=tail
        hl,hu=frechet(allowed)
        hind=q1+q2*directions[j][direction]
        assert abs(hind-float(np.prod(allowed)))<1e-12
        rows.append({"KQC":KQCS[j].name,"direction":direction,"strict_marginals":strict.tolist(),
            "wide_marginals":wide.tolist(),"allowed_marginals":allowed.tolist(),
            "H_probability_interval":[hl,hu],"T_probability_interval":[tl,tu],
            "independent_H_probability":hind,"independent_T_probability":q1+q2,
            "optimistic_screen_lower_endpoint":screen(hl,tl),
            "independent_optimistic_screen":screen(hind,q1+q2),
            "attainable_optimistic_screen_upper_endpoint":screen(hu,tu),
            "upper_joint_example":{"grade1_probability":float(strict.min()),
                "total_good_probability":tu,"potential_grade1_probability":hu,
                "dependence":"nested events on a common item-wise uniform variable; items remain iid"}})
    save_service(60,{"question":"Does normal marginal KQC data alone justify the independent-grade repairability ceiling?",
        "assumptions":__doc__,"headline":{"random_joint_law_checks":len(checks),
        "max_constructive_upper_error":max(checks),"routes":len(rows),
        "elapsed_seconds":time.perf_counter()-started},"rows":rows},__file__,
        (ROOT/"backbone"/"round59_repairability_ceiling.py",ROOT/"backbone"/"exact_quality_service.py",
         ROOT/"backbone"/"round42_one_sided_repair.py"))


if __name__=="__main__":
    main()
