"""Round50: treat downward substitution as a decision under a service constraint.

Same cash account (holding30), known eta=.97, random quality and fixed forward.
Mandatory downward substitution can reduce expected profit even in states where
it cannot complete the order. Permit zero substitution for profit, or only the
amount needed for whole-order completion. The service-profit frontier prices
each additional completion event by its actual substitution gap.
"""
import time
from backbone.adaptive_substitution import *
from backbone.round40_quality_recoverability import recoverability
from backbone.ball_screw import APPENDIX_COMPONENT_PROBABILITIES


def small_checks():
    q1,q2,f=.5,.3,.2
    solver=AdaptiveSubstitution(q1,q2,f,(5,3),maximum=18)
    errors=[]
    for n in (8,12,18):
        masses=np.zeros(3)
        sub=0.
        p=(q1,q2*f,q2*(1-f),1-q1-q2)
        for a in range(n+1):
          for e in range(n-a+1):
           for other in range(n-a-e+1):
            counts=(a,e,other,n-a-e-other)
            probability=math.exp(math.lgamma(n+1)-sum(math.lgamma(k+1) for k in counts)
                                  +sum(k*math.log(v) for k,v in zip(counts,p)))
            b=e+other
            sub+=probability*min(max(a-5,0),max(3-b,0))
            if b<3 and a>=5+(3-b):
                masses[3-b-1]+=probability
        errors.extend((float(np.max(np.abs(masses-solver.completion_masses(n)))),abs(sub-solver.expected_substitution(n))))
        assert max(errors)<1e-10
    return max(errors)


def main():
    started=time.perf_counter()
    error=small_checks()
    quality=recoverability(APPENDIX_COMPONENT_PROBABILITIES)
    q1,q2=quality["implied_grade1_share"],quality["implied_grade2_share"]
    f=quality["single_feature_bounds"][0]["single_feature_perfect_repair_upper_bound"]
    d=(550.,350.)
    solver=AdaptiveSubstitution(q1,q2,f,d)
    rows=[]
    for policy in (1,2):
        raw=required_input(d,(q1,q2),STATIONS,policy)
        result=solver.frontier(raw,(.6,.8,.9,.94,.95))
        assert result["complete_only_when_feasible_profit"]>=result["mandatory_substitution"]["expected_profit"]-1e-7
        rows.append({"input_reference_policy":policy,**result})
    save_service(50,{"question":"Does mandatory downward substitution obscure the true profit-service tradeoff?",
        "assumptions":__doc__,"scope":"Fixed inputs, fixed forward, known eta=.97, observed initial quality. Exact randomized frontier and constructive deterministic feasible prefix with a profit-gap bound; no general deterministic optimality claim.",
        "grade_shares":[q1,q2],"eligible_fraction":f,"demands":d,
        "headline":{"elapsed_seconds":time.perf_counter()-started,"inputs":len(rows),
                    "small_multinomial_max_error":error},"rows":rows},__file__,
        (ROOT/"backbone"/"adaptive_substitution.py",ROOT/"backbone"/"exact_quality_economics.py",
         ROOT/"backbone"/"exact_quality_service.py",ROOT/"backbone"/"quality_lab.py",
         ROOT/"backbone"/"round40_quality_recoverability.py"))


if __name__=="__main__":
    main()
