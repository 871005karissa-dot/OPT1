"""Round84: an identifiable batch-dispersion diagnostic, with known-p scope.

For independent batches of known exogenous sizes N_b and common known category
probabilities p, DM gives E[Q_b]=(K-1)*(1+(N_b-1)*rho), rho=1/(kappa+1),
Q_b=sum_j(X_bj-N_bp_j)^2/(N_bp_j). Thus the raw rho estimator below is unbiased.
Clipping or estimating p from the same counts changes that statement. This is
a synthetic diagnostic for planning data collection, not an empirical estimate
of kappa or a proposed new statistical method.
"""
import math
from backbone.service_frontier import *
from backbone.round62_stochastic_policy_replay import estimate

SEED=2026102884
REPEATS=2048
BATCHES=128


def raw_rho(counts,sizes,p):
    p=np.asarray(p,dtype=float)
    sizes=np.asarray(sizes)
    if p.ndim!=1 or np.any(p<=0) or not np.isclose(p.sum(),1.):
        raise ValueError("This known-p diagnostic requires one positive probability vector")
    if sizes.ndim!=1 or counts.shape[-2:]!=(len(sizes),len(p)) or np.sum(sizes-1)<=0:
        raise ValueError("Batch sizes must match the count rows and include repeated-item information")
    if np.any(counts<0) or not np.all(counts.sum(axis=-1)==sizes):
        raise ValueError("Each nonnegative count row must sum to its recorded batch size")
    expected=sizes[...,None]*p
    q=np.sum((counts-expected)**2/expected,axis=-1)
    return (np.sum(q,axis=-1)/(p.shape[-1]-1)-counts.shape[-2])/np.sum(np.asarray(sizes)-1)


def enumerate_q(n,p,kappa):
    result=mass_sum=0.
    for a in range(n+1):
        for b in range(n-a+1):
            for c in range(n-a-b+1):
                x=(a,b,c,n-a-b-c)
                log_mass=math.lgamma(n+1)-sum(math.lgamma(v+1) for v in x)
                if kappa is None:
                    log_mass+=sum(v*math.log(pp) for v,pp in zip(x,p))
                else:
                    log_mass+=math.lgamma(kappa)-math.lgamma(kappa+n)
                    log_mass+=sum(math.lgamma(kappa*pp+v)-math.lgamma(kappa*pp) for v,pp in zip(x,p))
                mass=math.exp(log_mass)
                q=sum((v-n*pp)**2/(n*pp) for v,pp in zip(x,p))
                mass_sum+=mass
                result+=mass*q
    rho=0. if kappa is None else 1/(kappa+1)
    expected=(len(p)-1)*(1+(n-1)*rho)
    assert abs(mass_sum-1)<1e-11 and abs(result-expected)<1e-10
    return abs(result-expected)


def main():
    checks=[enumerate_q(n,(.4,.2,.1,.3),k) for n in (3,7) for k in (None,5.,100.)]
    params=json.loads((SERVICE_OUT/"round63.json").read_text(encoding="utf-8"))
    q1,q2=params["grade_shares"]
    f=params["eligible_fraction"]
    p=np.array((q1,q2*f,q2*(1-f),1-q1-q2))
    sizes=np.linspace(600,1600,BATCHES).astype(int)
    rng=np.random.default_rng(SEED)
    rows=[]
    traces={}
    for kappa in (None,1000.,100.):
        probabilities=p if kappa is None else rng.dirichlet(kappa*p,size=(REPEATS,BATCHES))
        counts=rng.multinomial(sizes,probabilities,size=(REPEATS,BATCHES))
        raw=raw_rho(counts,sizes,p)
        truth=0. if kappa is None else 1/(kappa+1)
        moment=estimate(raw)
        z=abs(moment["estimate"]-truth)/moment["standard_error"]
        assert z<5
        clipped=np.clip(raw,0.,1.)
        pooled=counts.sum(axis=1)/sizes.sum()
        expected=sizes[None,:,None]*pooled[:,None,:]
        q=np.sum((counts-expected)**2/expected,axis=-1)
        plug_in=(np.sum(q,axis=1)/3-BATCHES)/np.sum(sizes-1)
        key="iid" if kappa is None else f"kappa{int(kappa)}"
        traces[key+"_known_p_raw_rho"]=raw
        traces[key+"_same_data_p_raw_rho"]=plug_in
        rows.append({"kappa":kappa,"true_rho":truth,"known_p_raw":moment,"error_in_standard_errors":z,
            "clipped_rho_mean":float(clipped.mean()),"raw_negative_fraction":float(np.mean(raw<0)),
            "same_data_p_raw":estimate(plug_in),
            "warning":"Known-p unbiasedness does not transfer to same-data p estimation or clipping; these synthetic rows do not calibrate the factory."})
    trace=SERVICE_OUT/"round84_validation.npz"
    np.savez_compressed(trace,seed=SEED,sizes=sizes,**traces)
    save_service(84,{"question":"What batch-ID count data can identify the overdispersion stress parameter, and what cannot?",
        "assumptions":__doc__,"seed":SEED,"synthetic_datasets_per_law":REPEATS,"batches_per_dataset":BATCHES,
        "known_category_probabilities":p.tolist(),"batch_size_range":[int(sizes.min()),int(sizes.max())],
        "headline":{"all_outcome_moment_checks":len(checks),"max_moment_error":max(checks)},"rows":rows,
        "trace":{"path":str(trace.relative_to(ROOT)),"sha256":sha256(trace.read_bytes()).hexdigest()}},__file__,
        (ROOT/"backbone"/"round62_stochastic_policy_replay.py",SERVICE_OUT/"round63.json"))


if __name__=="__main__":
    main()
