"""Round40: can one-feature rework upgrade an arbitrary grade-2 item?

Assume independent KQCs, nested strict/wide specifications, and rework that can
perfectly repair a chosen KQC without changing others. Among grade2 items, only
those failing that feature alone can reach grade1. This is an optimistic upper
bound; actual one-sided machining, damage, and imperfect repair may reduce it.
Use actual-normal and manuscript-rounded probabilities as separate data sources.
No station-to-KQC mapping or observed rework success is inferred.
"""
import math
from itertools import product
from backbone.ball_screw import KQCS,APPENDIX_COMPONENT_PROBABILITIES
from backbone.evaluator import component_probabilities
from backbone.service_frontier import save_service


def recoverability(probabilities):
    strict=[p[0] for p in probabilities]
    wide=[p[1] for p in probabilities]
    q1=math.prod(strict)
    q2=math.prod(wide)-q1
    subtypes=[]
    for flags in product((False,True),repeat=len(strict)):
        mass=math.prod(strict[j] if flag else wide[j]-strict[j] for j,flag in enumerate(flags))
        failures=[j for j,flag in enumerate(flags) if not flag]
        subtypes.append({"strict_failures":failures,"unconditional_mass":mass,
                         "fraction_of_grade2":mass/q2 if failures else None})
    assert abs(sum(p["unconditional_mass"] for p in subtypes)-math.prod(wide))<1e-12
    assert abs(sum(p["unconditional_mass"] for p in subtypes if p["strict_failures"])-q2)<1e-12
    bounds=[]
    for j,kqc in enumerate(KQCS):
        analytic=(wide[j]-strict[j])*math.prod(strict[k] for k in range(len(strict)) if k!=j)/q2
        enumerated=sum(p["unconditional_mass"] for p in subtypes if p["strict_failures"]==[j])/q2
        assert abs(analytic-enumerated)<1e-12
        bounds.append({"KQC_index":j,"KQC_name":kqc.name,"single_feature_perfect_repair_upper_bound":analytic})
    multiple=sum(p["fraction_of_grade2"] for p in subtypes if len(p["strict_failures"])>=2)
    assert abs(multiple+sum(p["single_feature_perfect_repair_upper_bound"] for p in bounds)-1)<1e-12
    return {"component_probabilities":probabilities,"implied_grade1_share":q1,"implied_grade2_share":q2,
            "single_feature_bounds":bounds,"grade2_fraction_failing_multiple_KQCs":multiple,"subtypes":subtypes}


def main():
    rows=[]
    for source,probabilities in (("normal_parameters_and_tolerances",component_probabilities(KQCS)),
                                 ("manuscript_component_probabilities_rounded",APPENDIX_COMPONENT_PROBABILITIES)):
        rows.append({"source":source,**recoverability(probabilities)})
    save_service(40,{"question":"What fraction of low-grade output can possibly be upgraded by repairing one quality characteristic?",
        "assumptions":__doc__,"headline":{"largest_single_feature_bound_by_source":{
            row["source"]:max(p["single_feature_perfect_repair_upper_bound"] for p in row["single_feature_bounds"]) for row in rows}},
        "rows":rows,"selection_caution":"If inspection identifies repairable subtypes, conditional success among selected items may be high, but return volume must also be limited by the eligible pool; aggregate grade2 success and selected-item success are different parameters."},__file__)


if __name__=="__main__":
    main()
