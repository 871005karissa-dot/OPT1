"""Round79: audit matched certainty-equivalent service over the saved full grid.

No new physical or repair model. Reuse immutable round71 finite-batch values;
replace only initial class counts by means, retaining integer N and return R.
Full grid is15 source demand pairs times integer I0..2100. Mean-input formula
anchors are separate and do not reproduce the source's entire Policy I/II.
"""
import gc
import time
from backbone.round76_certainty_equivalent_audit import mean_quality_service
from backbone.maximal_service_curve import *


def main():
    started=time.perf_counter()
    source=json.loads((SERVICE_OUT/"round71.json").read_text(encoding="utf-8"))
    params=json.loads((SERVICE_OUT/"round63.json").read_text(encoding="utf-8"))
    q1,q2=params["grade_shares"]
    f=params["eligible_fraction"]
    cache_path=SERVICE_OUT/"round71_physical_cache.npz"
    with np.load(cache_path,allow_pickle=False) as data:
        groups,weights,offsets=(data[k] for k in ("groups","weights","offsets"))
    n,limit=groups[:,0],groups[:,1]
    rows=[]
    checks=[]
    anchors=[]
    for case in source["cases"]:
        d=tuple(case["demands"])
        a,b=q1*n,q2*n
        r=np.floor(np.minimum.reduce((f*b,np.maximum(b-d[1],0),limit))+1e-9)
        high,low=a+.97*r,b-r
        sub=np.minimum(np.maximum(high-d[0],0),np.maximum(d[1]-low,0))
        ce=np.add.reduceat(weights*((high>=d[0]-EPS)&(low+sub>=d[1]-EPS)),offsets[:-1])
        truth=np.array([x["maximal_repair"] for x in case["integer_input_service"]])
        for raw in (0,1316,1495,1699,2100):
            err=abs(ce[raw]-mean_quality_service(float(raw),d,q1,q2,f,True))
            checks.append(err)
            assert err<1e-12
        delta=ce-truth
        points=[{"input":i,"matched_CE":float(c),"finite_batch":float(t),"CE_minus_finite_batch":float(e)}
                for i,(c,t,e) in enumerate(zip(ce,truth,delta))]
        rows.append({"demands":d,"largest_overestimate":points[int(np.argmax(delta))],
            "largest_underestimate":points[int(np.argmin(delta))],
            "false80_claim_points":int(np.sum((ce>=.8)&(truth<.8))),"points":points})
        # A second mean-input formula is predefined by the original evaluator:
        # grade1 and total-good constraints when downward substitution is allowed.
        raw=required_input(d,(q1,q2),STATIONS,2)
        solver=StochasticSetupFrontier(q1,q2,f,d)
        curves=MaximalServiceCurves(solver)
        exact=curves.evaluate(raw)
        anchors.append({"demands":d,"input":raw,"role":"mean_grade1_and_total_good_formula_anchor",
            "fluid_CE":mean_quality_service(raw,d,q1,q2,f,False),
            "matched_CE":mean_quality_service(raw,d,q1,q2,f,True),"finite_batch":exact})
        MaximalServiceCurves.curve.cache_clear()
        release_integer_caches(solver)
        StochasticSetupFrontier.unbounded_return_law.cache_clear()
        del solver,curves
        gc.collect()
    over=max(rows,key=lambda x:x["largest_overestimate"]["CE_minus_finite_batch"])
    under=min(rows,key=lambda x:x["largest_underestimate"]["CE_minus_finite_batch"])
    save_service(79,{"question":"Do mean-quality service errors persist over all saved integer inputs rather than selected anchors?",
        "assumptions":__doc__,"grade_shares":[q1,q2],"eligible_fraction":f,
        "headline":{"full_grid_points":sum(len(x["points"]) for x in rows),"direct_flow_checks":len(checks),
            "max_direct_flow_error":max(checks),"largest_overestimate":{"demands":over["demands"],**over["largest_overestimate"]},
            "largest_underestimate":{"demands":under["demands"],**under["largest_underestimate"]},
            "false80_claim_points":sum(x["false80_claim_points"] for x in rows),"elapsed_seconds":time.perf_counter()-started},
        "cases":rows,"mean_substitution_input_anchors":anchors},__file__,
        (ROOT/"backbone"/"round76_certainty_equivalent_audit.py",ROOT/"backbone"/"maximal_service_curve.py",
         ROOT/"backbone"/"stochastic_setup_frontier.py",ROOT/"backbone"/"integer_rework.py",
         ROOT/"backbone"/"recourse_lab.py",SERVICE_OUT/"round71.json",SERVICE_OUT/"round63.json",cache_path))


if __name__=="__main__":
    main()
