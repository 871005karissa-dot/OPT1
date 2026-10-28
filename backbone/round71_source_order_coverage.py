"""Round71: cover all15 demand pairs transcribed from source Tables4/5.

Keep the canonical NORMAL-source q, candidate one-direction final-station route,
iid initial quality, unknown iid repair successes, fixed forward, S0. Service
capability only; monetary setup fee and material basis do not affect this query.
No-repair baseline permits the SAME fixed downward substitution as the extension.
The mean-gradewise input formula is an input anchor, not reproduction of the
source's full PolicyI (which has different allocation/quality assumptions).
"""
import gc
import time
from backbone.maximal_service_curve import *


def physical_cache():
    meta_path=SERVICE_OUT/"round71_physical_cache.json"
    data_path=SERVICE_OUT/"round71_physical_cache.npz"
    paths=[ROOT/"backbone"/"recourse_lab.py",ROOT/"backbone"/"ball_screw.py",ROOT/"backbone"/"evaluator.py"]
    signature={str(p.relative_to(ROOT)):sha256(p.read_bytes()).hexdigest() for p in paths}
    signature.update(CAPS=sha256(CAPS.tobytes()).hexdigest(),PROB=sha256(PROB.tobytes()).hexdigest())
    if meta_path.exists() and data_path.exists():
        meta=json.loads(meta_path.read_text(encoding="utf-8"))
        if meta.get("signature")==signature and meta.get("sha256")==sha256(data_path.read_bytes()).hexdigest():
            with np.load(data_path,allow_pickle=False) as archive:
                return {key:archive[key] for key in archive.files},data_path,meta_path
    groups=[]
    masses=[]
    offsets=[0]
    for raw in range(int(STATIONS[0].max_capacity)+1):
        flow=forward(float(raw))
        n=np.floor(flow.finished+1e-9).astype(int)
        spare=np.minimum(n,np.floor(np.maximum(CAPS[:,4]-flow.loads[:,4],0.)+1e-9).astype(int))
        pair,inverse=np.unique(np.stack((n,spare),axis=1),axis=0,return_inverse=True)
        weights=np.bincount(inverse,weights=PROB,minlength=len(pair))
        assert abs(float(weights.sum())-1)<1e-10
        groups.append(pair)
        masses.append(weights)
        offsets.append(offsets[-1]+len(pair))
    data={"groups":np.concatenate(groups).astype(np.int16),"weights":np.concatenate(masses),
          "offsets":np.array(offsets,dtype=int)}
    np.savez_compressed(data_path,**data)
    meta={"signature":signature,"sha256":sha256(data_path.read_bytes()).hexdigest(),
          "scope":"Fixed forward, final station5, integer floor quality/return capacity, setup workload0, integer inputs0..2100. Independent of demand and quality law."}
    meta_path.write_text(json.dumps(meta,indent=2),encoding="utf-8")
    return data,data_path,meta_path


def main():
    started=time.perf_counter()
    reference=json.loads((SERVICE_OUT/"round63.json").read_text(encoding="utf-8"))
    q1,q2=reference["grade_shares"]
    f=reference["eligible_fraction"]
    data,cache_path,meta_path=physical_cache()
    groups,weights,offsets=(data[k] for k in ("groups","weights","offsets"))
    max_n=int(groups[:,0].max())
    files=[Path(__file__),ROOT/"backbone"/"maximal_service_curve.py",ROOT/"backbone"/"stochastic_setup_frontier.py",
           ROOT/"backbone"/"integer_rework.py",ROOT/"backbone"/"exact_quality_service.py",
           ROOT/"backbone"/"recourse_lab.py",ROOT/"backbone"/"ball_screw.py",ROOT/"backbone"/"evaluator.py",
           ROOT/"backbone"/"round2_share_consistency.py",cache_path,meta_path,SERVICE_OUT/"round63.json"]
    signature={str(p.relative_to(ROOT)):sha256(p.read_bytes()).hexdigest() for p in files}
    checkpoint=SERVICE_OUT/"round71_progress.json"
    progress={"signature":signature,"cases":[],"status":"running"}
    if checkpoint.exists():
        candidate=json.loads(checkpoint.read_text(encoding="utf-8"))
        if candidate.get("signature")==signature:
            progress=candidate
    def persist():
        temporary=checkpoint.with_suffix(".tmp")
        temporary.write_text(json.dumps(progress,indent=2,allow_nan=False),encoding="utf-8")
        temporary.replace(checkpoint)
    cases=progress["cases"]
    assert [tuple(x["demands"]) for x in cases]==ORDERS[:len(cases)]
    for d in ORDERS[len(cases):]:
        solver=StochasticSetupFrontier(q1,q2,f,d)
        curves=MaximalServiceCurves(solver)
        table=np.array([curves.curve(n) for n in range(max_n+1)])
        conditional=table[groups[:,0],groups[:,1]]
        service=np.add.reduceat(weights*conditional,offsets[:-1])
        base=np.array([curves.no_return_service(n) for n in range(max_n+1)])
        no_repair=np.add.reduceat(weights*base[groups[:,0]],offsets[:-1])
        assert min(service-no_repair)>=-1e-9
        assert min(np.diff(no_repair))>=-1e-9
        best=int(np.argmax(service))
        anchor=required_input(d,(q1,q2),STATIONS,1)
        anchor_service=curves.evaluate(anchor)
        targets=[]
        for target in (.75,.9,.95):
            feasible=np.flatnonzero(service>=target)
            targets.append({"target":target,"feasible":bool(len(feasible)),"feasible_input_count":len(feasible),
                            "smallest_feasible_input":int(feasible[0]) if len(feasible) else None})
        if tuple(d)==(750.,150.):
            expected=max(x["maximum_service"] for x in reference["rows"] if "maximum_service" in x)
            assert abs(float(service[best])-expected)<1e-9
        cases.append({"demands":d,"normal_source_grade_shares":[q1,q2],"candidate_eligible_fraction":f,
            "max_no_repair_with_substitution":float(no_repair[-1]),
            "max_with_candidate_repair":float(service[best]),"first_maximizing_input":best,
            "service_gain_at_capability_ceiling":float(service[best]-no_repair[-1]),
            "mean_gradewise_input_anchor":anchor,"anchor_full_return_service":anchor_service,
            "targets":targets,"integer_input_service":[{"input":raw,"no_repair":float(nr),"maximal_repair":float(rr)}
                for raw,(nr,rr) in enumerate(zip(no_repair,service))]})
        persist()
        print(json.dumps({"demands":d,"no_repair_max":float(no_repair[-1]),"repair_max":float(service[best]),
                          "elapsed_seconds":time.perf_counter()-started}),flush=True)
        MaximalServiceCurves.curve.cache_clear()
        release_integer_caches(solver)
        StochasticSetupFrontier.unbounded_return_law.cache_clear()
        del solver,curves,table
        gc.collect()
    progress["status"]="complete"
    persist()
    save_service(71,{"question":"Are the feasibility conclusions specific to the highlighted750/150 order?",
        "assumptions":__doc__,"headline":{"source_order_pairs":len(cases),"integer_input_values_per_order":len(offsets)-1,
                    "total_order_input_checks":sum(len(x["integer_input_service"]) for x in cases),
                    "cached_physical_groups":len(groups),"elapsed_seconds_this_execution":time.perf_counter()-started},
        "cases":cases},__file__,tuple(files[1:]))


if __name__=="__main__":
    main()
