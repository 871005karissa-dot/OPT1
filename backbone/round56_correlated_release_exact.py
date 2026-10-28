"""Round56: reoptimize integer release under two batch-quality distributions.

Exhaust I=0,...,2100 with exact Dirichlet-multinomial expectations for kappa1000
and100. Same fixed forward, known fluid upgrade .97, setup workload350 and
processed-only material cost as round49. No setup money charge in this ablation.
Checkpoint only self-generated results whose code/input hashes still match.
"""
import gc
from hashlib import sha256
import time
from backbone.exact_batch_quality import *


def summarize(rows,kappa):
    constrained=[]
    for target in (.6,.7,.75,.8,.85,.9):
        feasible=[row for row in rows if row["fulfilment_probability"]>=target-1e-12]
        constrained.append({"target":target,"feasible":bool(feasible),
                            "best":max(feasible,key=lambda row:row["expected_profit"]) if feasible else None})
    return {"kappa":kappa,"integer_inputs":len(rows),
        "best_unconstrained":max(rows,key=lambda row:row["expected_profit"]),
        "maximum_service":max(rows,key=lambda row:row["fulfilment_probability"]),
        "constrained":constrained,"rows":rows}


def main():
    started=time.perf_counter()
    source=SERVICE_OUT/"round49.json"
    old=json.loads(source.read_text(encoding="utf-8"))
    q1,q2=old["grade_shares"]
    f=old["eligible_fraction"]
    d=tuple(old["demands"])
    files=[Path(__file__),ROOT/"backbone"/"exact_batch_quality.py",ROOT/"backbone"/"exact_quality_economics.py",
           ROOT/"backbone"/"exact_quality_service.py",ROOT/"backbone"/"quality_lab.py",
           ROOT/"backbone"/"recourse_lab.py",ROOT/"backbone"/"ball_screw.py",ROOT/"backbone"/"evaluator.py",source]
    signature={str(path.relative_to(ROOT)):sha256(path.read_bytes()).hexdigest() for path in files}
    checkpoint=SERVICE_OUT/"round56_progress.json"
    progress={"signature":signature,"cases":{},"status":"running"}
    if checkpoint.exists():
        candidate=json.loads(checkpoint.read_text(encoding="utf-8"))
        if candidate.get("signature")==signature:
            progress=candidate
    def persist():
        temporary=checkpoint.with_suffix(".tmp")
        temporary.write_text(json.dumps(progress,indent=2,allow_nan=False),encoding="utf-8")
        temporary.replace(checkpoint)
    results=[]
    for kappa in (1000.,100.):
        key=str(kappa)
        rows=progress["cases"].get(key,[])
        assert [row["input"] for row in rows]==list(map(float,range(len(rows))))
        solver=ExactBatchQualityEconomics(q1,q2,f,d,kappa)
        for raw in range(len(rows),int(STATIONS[0].max_capacity)+1):
            rows.append(solver.evaluate_economics(float(raw)))
            if raw%200==0:
                progress["cases"][key]=rows
                persist()
                print(json.dumps({"kappa":kappa,"last_input":raw,"elapsed_seconds":time.perf_counter()-started}),flush=True)
        progress["cases"][key]=rows
        persist()
        results.append(summarize(rows,kappa))
        clear_solver_caches(solver)
        del solver
        gc.collect()
    save_service(56,{"question":"Do exact integer release and service decisions change when batch correlation changes but mean quality does not?",
        "assumptions":__doc__,"grade_shares":[q1,q2],"eligible_fraction":f,"demands":d,
        "parameters_are_hypothetical":True,
        "optimality_scope":"Exhaustive optimum on I=0,...,2100 for each stated quality law in the fixed-forward maximal-return policy class, with no cross-model or factory guarantee.",
        "independent_item_reference":{"kappa":None,"best_unconstrained":old["best_unconstrained"],"maximum_service":old["maximum_service"]},
        "headline":{"elapsed_seconds_this_execution":time.perf_counter()-started,"cases":len(results),
                    "integer_input_evaluations":sum(len(case["rows"]) for case in results)},"cases":results},__file__,
        (ROOT/"backbone"/"exact_batch_quality.py",ROOT/"backbone"/"exact_quality_economics.py",
         ROOT/"backbone"/"exact_quality_service.py",ROOT/"backbone"/"quality_lab.py"))
    progress["status"]="complete"
    persist()


if __name__=="__main__":
    main()
