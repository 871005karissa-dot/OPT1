"""Round82: freeze/decode ALL ten winning policies in the optional-rule study.

An exact expectation replay, not another Monte Carlo repeat of75. In particular
the reoptimized no-repair and always-repair baseline rules are decoded too.
No search rerun and no modification to73/78 result files.
"""
import gc
import time
from types import SimpleNamespace
from backbone.round75_joint_policy_execution import frozen_setup,decoded_substitution_mass
from backbone.joint_fulfilment_frontier import *
from backbone.joint_policy import JointDecisionPolicy


def replay():
    catalog=json.loads((SERVICE_OUT/"round82_policy_catalog.json").read_text(encoding="utf-8"))
    params=json.loads((SERVICE_OUT/"round63.json").read_text(encoding="utf-8"))
    q1,q2=params["grade_shares"]
    f=params["eligible_fraction"]
    rows=[]
    for spec in catalog["policies"]:
        d=tuple(spec["demands"])
        core=StochasticSetupFrontier(q1,q2,f,d)
        pool=SubstitutionPool(core)
        policy=JointDecisionPolicy(ROOT/catalog["path"],spec["key"],catalog["sha256"],spec)
        flow=forward(float(spec["input"]))
        ns=np.floor(flow.finished+1e-9).astype(int)
        unique,inverse=np.unique(ns,return_inverse=True)
        weights=np.bincount(inverse,weights=PROB,minlength=len(unique))
        sub=pool.aggregate(unique,weights)
        states=core.state_masses(float(spec["input"]),0.)
        states["base_profit"]-=MATERIAL_COST*(spec["input"]-mean(flow.loads[:,0]))
        early=summarize_choice(states,policy.decide(states["A"],states["R"]),2000.)
        mass=decoded_substitution_mass(pool,ns,sub,spec["boundary"],policy.capacity_rank)
        expected_profit=early["expected_profit"]+30*sub["expected_automatic_substitution"]-30*float(np.arange(1,int(d[1])+1)@mass)
        service=early["fulfilment_probability"]-float(sub["mass"].sum())+float(mass.sum())
        ep=abs(expected_profit-spec["expected_profit"])
        es=abs(service-spec["fulfilment_probability"])
        assert ep<1e-7 and es<1e-9,(spec,ep,es)
        assert service>=spec["target"]-1e-10
        rows.append({"key":spec["key"],"input":spec["input"],"replayed_profit":expected_profit,
            "replayed_service":service,"profit_error":ep,"service_error":es})
        release_integer_caches(core)
        StochasticSetupFrontier.unbounded_return_law.cache_clear()
        AdaptiveSubstitution.expected_substitution.cache_clear()
        del core,pool,policy,states
        gc.collect()
    return rows


def main():
    started=time.perf_counter()
    source=json.loads((SERVICE_OUT/"round78.json").read_text(encoding="utf-8"))
    policies=[]
    for case in source["cases"]:
        choices=[("proposed",case["proposed_feasible"]),("always",case["always_repair_optional_substitution"]["best_feasible"])]
        if case["no_repair_optional_substitution"] is not None:
            choices.append(("none",case["no_repair_optional_substitution"]["best_feasible"]))
        for label,point in choices:
            d=case["demands"]
            policies.append({"key":f"d{int(d[0])}_{int(d[1])}_{label}","demands":d,"target":case["target"],**point})
    rank=np.empty(len(PROB),dtype=int)
    rank[np.argsort(-PROB,kind="stable")]=np.arange(len(PROB))
    aa,rr=np.arange(1601)[:,None],np.arange(1601)[None,:]
    light=SimpleNamespace(d1=0,eta=.97,unit_cost=12.4,success=BinomialTables(1600,.97))
    packed={"shape":np.array([1601,1601]),"capacity_rank":rank}
    for spec in policies:
        light.d1=int(spec["demands"][0])
        matrix=frozen_setup(aa,rr,light,spec["mode"],spec["boundary"])
        packed[spec["key"]]=np.packbits(matrix,bitorder="big")
    archive=SERVICE_OUT/"round82_frozen_policies.npz"
    np.savez_compressed(archive,**packed)
    catalog={"path":str(archive.relative_to(ROOT)),"sha256":sha256(archive.read_bytes()).hexdigest(),"policies":policies,
        "indices":"Initial A, available R for startup; initial A/B and frozen capacity rank for substitution. Future Y is absent."}
    catalog_path=SERVICE_OUT/"round82_policy_catalog.json"
    catalog_path.write_text(json.dumps(catalog,indent=2),encoding="utf-8")
    del light,matrix,packed
    gc.collect()
    rows=replay()
    save_service(82,{"question":"Do all reoptimized policy classes execute the decisions whose expectations were optimized?",
        "assumptions":__doc__,"headline":{"decoded_policies":len(rows),"max_profit_error":max(x["profit_error"] for x in rows),
            "max_service_error":max(x["service_error"] for x in rows),"elapsed_seconds":time.perf_counter()-started},
        "policy_catalog":catalog,"rows":rows},__file__,
        (ROOT/"backbone"/"joint_policy.py",ROOT/"backbone"/"round75_joint_policy_execution.py",
         ROOT/"backbone"/"joint_fulfilment_frontier.py",ROOT/"backbone"/"stochastic_setup_frontier.py",
         ROOT/"backbone"/"integer_rework.py",SERVICE_OUT/"round78.json",SERVICE_OUT/"round63.json",archive,catalog_path))


if __name__=="__main__":
    main()
