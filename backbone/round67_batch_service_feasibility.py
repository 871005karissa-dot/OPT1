"""Round67: can any integer release restore75% under batch-quality stress?

Maximal return maximizes service for the reserved-D2 single route. Setup fees
do not change this feasibility ceiling. Use cached service-vs-spare curves,
independently checked against A/B/E integration, and exhaust I=0,...,2100.
Larger integers give the same physical flows; no adaptive forward, ex-ante
mixed release or other repair class is included. Hypothetical batch law only.
"""
import gc
import time
from backbone.maximal_service_curve import *
from backbone.batch_stochastic_setup import BatchStochasticSetup


def main():
    started=time.perf_counter()
    checks=[]
    for kappa in (None,10.,100.):
        solver=(StochasticSetupFrontier(.5,.3,.25,(5,2),maximum=18) if kappa is None else
                BatchStochasticSetup(.5,.3,.25,(5,2),kappa,maximum=18))
        engine=MaximalServiceCurves(solver)
        for n in (8,12,18):
          for spare in (0,2,9):
            diff=abs(float(engine.curve(n)[spare])-solver.metrics(n,spare)["service"])
            checks.append(diff)
            assert diff<1e-10,(kappa,n,spare,diff)
        MaximalServiceCurves.curve.cache_clear()
        release_integer_caches(solver)
        StochasticSetupFrontier.unbounded_return_law.cache_clear()
        del engine,solver
        gc.collect()
    prior=json.loads((SERVICE_OUT/"round66.json").read_text(encoding="utf-8"))
    reference=json.loads((SERVICE_OUT/"round63.json").read_text(encoding="utf-8"))
    q1,q2=reference["grade_shares"]
    f=reference["eligible_fraction"]
    files=[Path(__file__),ROOT/"backbone"/"maximal_service_curve.py",ROOT/"backbone"/"batch_stochastic_setup.py",
           ROOT/"backbone"/"stochastic_setup_frontier.py",ROOT/"backbone"/"integer_rework.py",
           ROOT/"backbone"/"exact_batch_quality.py",ROOT/"backbone"/"recourse_lab.py",
           ROOT/"backbone"/"ball_screw.py",ROOT/"backbone"/"evaluator.py",SERVICE_OUT/"round66.json"]
    signature={str(p.relative_to(ROOT)):sha256(p.read_bytes()).hexdigest() for p in files}
    path=SERVICE_OUT/"round67_progress.json"
    progress={"signature":signature,"cases":{},"status":"running"}
    if path.exists():
        candidate=json.loads(path.read_text(encoding="utf-8"))
        if candidate.get("signature")==signature:
            progress=candidate
    def persist():
        temporary=path.with_suffix(".tmp")
        temporary.write_text(json.dumps(progress,indent=2,allow_nan=False),encoding="utf-8")
        temporary.replace(path)
    cases=[]
    for kappa in (1000.,100.):
        solver=BatchStochasticSetup(q1,q2,f,tuple(reference["demands"]),kappa)
        engine=MaximalServiceCurves(solver)
        expected=next(x for x in prior["rows"] if x["kappa"]==kappa)["retuned_at_same_input"]["maximum_service"]
        check=abs(engine.evaluate(1495.)-expected)
        assert check<1e-9,(kappa,check)
        key=str(kappa)
        rows=progress["cases"].setdefault(key,[])
        assert [x["input"] for x in rows]==list(range(len(rows)))
        for raw in range(len(rows),int(STATIONS[0].max_capacity)+1):
            rows.append({"input":raw,"maximum_service":engine.evaluate(float(raw))})
            if raw%100==0:
                persist()
                print(json.dumps({"kappa":kappa,"last_input":raw,"elapsed_seconds":time.perf_counter()-started}),flush=True)
        persist()
        feasible=[x for x in rows if x["maximum_service"]>=.75]
        cases.append({"kappa":kappa,"maximum":max(rows,key=lambda x:x["maximum_service"]),
                      "target_75_feasible":bool(feasible),"feasible_inputs":[x["input"] for x in feasible],
                      "fixed_input_independent_integral_discrepancy":check,
                      "max_law_mass_error":engine.max_law_mass_error,"rows":rows})
        MaximalServiceCurves.curve.cache_clear()
        release_integer_caches(solver)
        StochasticSetupFrontier.unbounded_return_law.cache_clear()
        del solver,engine
        gc.collect()
    progress["status"]="complete"
    persist()
    save_service(67,{"question":"Can release reoptimization restore75% when the frozen matched-route policy fails under batch variation?",
        "assumptions":__doc__,"headline":{"small_curve_vs_integral_cases":len(checks),"max_small_error":max(checks),
                    "integer_input_checks":sum(len(x["rows"]) for x in cases),
                    "elapsed_seconds_this_execution":time.perf_counter()-started},"cases":cases},__file__,tuple(files[1:]))


if __name__=="__main__":
    main()
