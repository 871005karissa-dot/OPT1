"""Check saved58-84 plus independent small numerics and frozen-policy execution.

Default never rewrites round*.json or heavy search checkpoints. --full reruns
58-84 in dependency order (matching search checkpoints may be resumed).
"""
from contextlib import redirect_stdout
from datetime import datetime,timezone
from hashlib import sha256
from pathlib import Path
import argparse,gc,io,json,runpy,sys,time

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT))
MODULES={58:"integer_rework_success",59:"repairability_ceiling",60:"kqc_dependence_identification",
61:"stochastic_setup_frontier",62:"stochastic_policy_replay",63:"matched_route_release",
64:"selected_release_validation",65:"quality_policy_monotonicity",66:"matched_route_batch_stress",
67:"batch_service_feasibility",68:"batch_release_policy",69:"frozen_policy_batch_validation",
70:"nonanticipative_final_control",71:"source_order_coverage",72:"profit_bound_kernel",
73:"fair_economic_baselines",74:"optional_substitution_audit",75:"joint_policy_execution",
76:"certainty_equivalent_audit",77:"terminal_value_gate",78:"optional_substitution_release",
79:"full_grid_mean_quality",80:"mean_quality_witness_validation",81:"mean_boundary_counterexample",
82:"global_policy_replay",83:"service_target_release_calibration",84:"batch_dispersion_identification"}


def clear_caches():
    for name,module in list(sys.modules.items()):
        if not name.startswith("backbone.") or module is None:
            continue
        for value in list(vars(module).values()):
            if isinstance(value,type):
                for member in vars(value).values():
                    if hasattr(member,"cache_clear"):
                        member.cache_clear()
    gc.collect()


def small_checks():
    import numpy as np
    from backbone.integer_rework import IntegerReworkEconomics
    from backbone.round58_integer_rework_success import brute
    from backbone.batch_stochastic_setup import BatchStochasticSetup
    from backbone.round66_matched_route_batch_stress import brute as dm_brute
    from backbone.maximal_service_curve import MaximalServiceCurves
    from backbone.final_station_service_control import FinalStationServiceControl
    records=[]
    for eta in (.55,.97):
        solver=IntegerReworkEconomics(.5,.3,.25,(5,2),maximum=12,eta=eta,mass_cutoff=0.)
        for mode in ("integer_mean","binomial"):
            exact=solver.metrics(12,4,mode)
            expected=brute(12,.5,.3,.25,(5,2),4,eta,12.4,mode)
            error=max(abs(exact[k]-v) for k,v in zip(("net_revenue","service","expected_rework"),expected))
            assert error<1e-8
            records.append({"test":"iid_integer_success_all_outcomes","eta":eta,"mode":mode,"max_error":error})
        clear_caches()
    for kappa in (10.,100.):
        solver=BatchStochasticSetup(.5,.3,.25,(5,2),kappa,maximum=12)
        _,revenue,service,returned=dm_brute(12,.5,.3,.25,kappa,(5,2),4)
        metrics=solver.metrics(12,4)
        error=max(abs(metrics[k]-v) for k,v in zip(("net_revenue","service","expected_rework"),(revenue,service,returned)))
        assert error<1e-8
        curves=MaximalServiceCurves(solver)
        assert abs(curves.curve(12)[4]-service)<1e-10
        controlled=FinalStationServiceControl(curves,12.).optimize_one(12,11.7)
        assert controlled["controlled_service"]>=controlled["fixed_forward_service"]-1e-12
        records.append({"test":"DM_initial_plus_future_success_all_outcomes","kappa":kappa,"max_error":error})
        clear_caches()
    from backbone.round84_batch_dispersion_identification import enumerate_q
    for kappa in (None,5.):
        error=enumerate_q(7,(.4,.2,.1,.3),kappa)
        records.append({"test":"known_p_batch_Pearson_moment_all_outcomes","kappa":kappa,"max_error":error})
    return records


def replay_frozen_policies():
    from backbone.stochastic_setup_frontier import StochasticSetupFrontier,summarize_choice
    from backbone.batch_stochastic_setup import BatchStochasticSetup
    from backbone.frozen_policy import FrozenPolicy
    from backbone.recourse_lab import MATERIAL_COST,forward,mean
    source=json.loads((HERE/"round63.json").read_text(encoding="utf-8"))
    catalog=json.loads((HERE/"round69_policy_catalog.json").read_text(encoding="utf-8"))
    q1,q2=source["grade_shares"]
    f=source["eligible_fraction"]
    records=[]
    for policy in catalog["policies"]:
        frozen=FrozenPolicy(ROOT/catalog["archive"],policy["key"],catalog["sha256"])
        kappa=policy["kappa"]
        solver=(StochasticSetupFrontier(q1,q2,f,(750,150)) if kappa is None else
                BatchStochasticSetup(q1,q2,f,(750,150),kappa))
        raw=policy["input"]
        states=solver.state_masses(float(raw),0.)
        states["base_profit"]-=MATERIAL_COST*(raw-mean(forward(float(raw)).loads[:,0]))
        result=summarize_choice(states,frozen.decide(states["A"],states["R"]),2000.)
        profit_error=abs(result["expected_profit"]-policy["expected_profit"])
        service_error=abs(result["fulfilment_probability"]-policy["expected_service"])
        assert profit_error<1e-7 and service_error<1e-10
        records.append({"policy":policy["key"],"input":raw,"profit_error":profit_error,"service_error":service_error})
        clear_caches()
    return records


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--full",action="store_true")
    full=parser.parse_args().full
    started=time.perf_counter()
    if full:
        for number,suffix in MODULES.items():
            with redirect_stdout(io.StringIO()):
                runpy.run_module(f"backbone.round{number}_{suffix}",run_name="__main__")
            clear_caches()
            print(f"Round {number}: regenerated",flush=True)
    before={p.name:sha256(p.read_bytes()).hexdigest() for p in HERE.glob("round*.json")}
    with redirect_stdout(io.StringIO()):
        numerical=small_checks()
        replay=replay_frozen_policies()
        from backbone.round82_global_policy_replay import replay as replay_joint
        joint_replay=replay_joint() if (HERE/"round82_policy_catalog.json").exists() else []
        runpy.run_path(str(HERE.parent/"audit_artifacts.py"),run_name="__main__")
    after={p.name:sha256(p.read_bytes()).hexdigest() for p in HERE.glob("round*.json")}
    assert before==after,"Read-only checks unexpectedly rewrote a result or checkpoint"
    audit=json.loads((HERE.parent/"artifact_audit.json").read_text(encoding="utf-8"))
    inventory_files=list((ROOT/"backbone").glob("*.py"))+[Path(__file__),HERE.parent/"audit_artifacts.py"]
    inventory={str(p.relative_to(ROOT)):sha256(p.read_bytes()).hexdigest() for p in inventory_files}
    report={"completed_at_utc":datetime.now(timezone.utc).isoformat(),
        "mode":"full_regeneration_plus_checks" if full else "saved_results_plus_fresh_checks",
        "elapsed_seconds":time.perf_counter()-started,"round_outputs_rewritten_by_checks":False,
        "independent_small_numerics":numerical,"full_observed_state_frozen_replays":replay,
        "full_observed_state_joint_and_baseline_replays":joint_replay,
        "recorded_provenance_and_trace_outputs_checked":audit["round_outputs"],
        "current_source_inventory_sha256":inventory,
        "scope":"Recorded source/trace hashes checked; inventory is a current snapshot, not historical proof for every unrecorded transitive dependency. Numerical checks concern the specified model, not empirical validity."}
    path=HERE/("validation_second_batch_full.json" if full else "validation_second_batch.json")
    path.write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps({"passed":True,"small_checks":len(numerical),"frozen_policy_replays":len(replay),"joint_baseline_replays":len(joint_replay),
                      "audited_round_outputs":audit["round_outputs"],"elapsed_seconds":report["elapsed_seconds"]}))


if __name__=="__main__":
    main()
