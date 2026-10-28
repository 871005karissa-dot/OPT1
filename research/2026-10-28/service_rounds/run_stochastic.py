"""Default rechecks exact benchmarks against saved simulations; --full reruns44-57."""
from contextlib import redirect_stdout
from datetime import datetime,timezone
from hashlib import sha256
from pathlib import Path
import argparse,gc,io,json,runpy,sys,time
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT))
MODULES={44:"random_quality_counts",45:"threshold_stability",46:"independent_service_validation",
47:"exact_quality_service",48:"exact_quality_profit",49:"integer_release_exact",50:"adaptive_substitution",
51:"substitution_policy_validation",52:"batch_quality_variation",53:"quality_setup_decision",
54:"setup_service_policy",55:"exact_batch_quality",56:"correlated_release_exact",57:"process_route_audit"}


def release_caches():
    for mod,clsname in (("exact_quality_service","ExactQualityService"),("exact_quality_economics","ExactQualityEconomics"),("adaptive_substitution","AdaptiveSubstitution")):
        module=sys.modules.get("backbone."+mod)
        if module:
            cls=getattr(module,clsname)
            for name in ("conditional","expected_return","no_return_revenue","net_revenue_and_return","expected_substitution"):
                method=getattr(cls,name,None)
                if hasattr(method,"cache_clear"):
                    method.cache_clear()
    gc.collect()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--full",action="store_true")
    full=parser.parse_args().full
    rounds=list(range(44,58)) if full else [47,48,50,55,57]
    records=[]
    for number in rounds:
        started=time.perf_counter()
        with redirect_stdout(io.StringIO()):
            runpy.run_module(f"backbone.round{number}_{MODULES[number]}",run_name="__main__")
        result=json.loads((HERE/f"round{number}.json").read_text(encoding="utf-8"))
        for relative,expected in result["provenance"]["sha256"].items():
            assert sha256((ROOT/relative).read_bytes()).hexdigest()==expected,(number,relative)
        records.append({"round":number,"passed":True,"elapsed_seconds":time.perf_counter()-started})
        release_caches()
        print(f"Round {number}: passed",flush=True)
    with redirect_stdout(io.StringIO()):
        runpy.run_path(str(HERE.parent/"audit_artifacts.py"),run_name="__main__")
    manifest={"completed_at_utc":datetime.now(timezone.utc).isoformat(),"mode":"full" if full else "exact_rechecks",
        "rounds":records,"runner_sha256":sha256(Path(__file__).read_bytes()).hexdigest(),
        "note":"Default uses saved independent Monte Carlo comparisons; --full regenerates all stochastic rounds in dependency order."}
    (HERE/("validation_stochastic_full.json" if full else "validation_stochastic_exact.json")).write_text(json.dumps(manifest,indent=2),encoding="utf-8")


if __name__=="__main__":
    main()
