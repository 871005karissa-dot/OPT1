"""Round41: selected repairable subtypes versus an aggregate upgrade fraction.

One hypothetical rework operation can fix one KQC only. Inspection identifies
eligible low-grade items; reserve low-grade demand from ineligible items first.
Return <= min(eligible*total grade2, total grade2-demand2, station spare-setup).
Compare this with random selection, whose fluid upgrade fraction is eligible*.97,
and the optimistic relaxation that any grade2 item can upgrade with fraction .97.
All fail-to-upgrade returns are scrapped, as in earlier exploratory rounds.
"""
import time
from backbone.quality_lab import *
from backbone.round40_quality_recoverability import recoverability
from backbone.ball_screw import KQCS,APPENDIX_COMPONENT_PROBABILITIES
from backbone.evaluator import component_probabilities


def main():
    started=time.perf_counter()
    rows=[]
    for source,probabilities in (("normal_parameters_and_tolerances",component_probabilities(KQCS)),
                                ("manuscript_component_probabilities_rounded",APPENDIX_COMPONENT_PROBABILITIES)):
      quality=recoverability(probabilities)
      q1,q2=quality["implied_grade1_share"],quality["implied_grade2_share"]
      for d in ((550.,350.),(650.,250.),(700.,200.),(750.,150.)):
        raw=required_input(d,(q1,q2),STATIONS,1)
        optimistic,_,optimistic_f,_=quality_action_pair(raw,d,.97,q1,q2)
        for feature in quality["single_feature_bounds"]:
            eligible=feature["single_feature_perfect_repair_upper_bound"]
            selected,_,selected_f,n=quality_action_pair(raw,d,.97,q1,q2,eligible)
            unselected,_,unselected_f,_=quality_action_pair(raw,d,eligible*.97,q1,q2)
            assert np.all(optimistic["profit"]>=selected["profit"]-1e-6)
            assert np.all(selected["profit"]>=unselected["profit"]-1e-6)
            assert np.all(optimistic_f>=selected_f)
            assert np.all(selected_f>=unselected_f)
            rows.append({"source":source,"shares":[q1,q2],"demands":d,"input":raw,
                "KQC_index":feature["KQC_index"],"KQC_name":feature["KQC_name"],"eligible_fraction_of_grade2":eligible,
                "optimistic_any_grade2":summary(optimistic),"selected_repairable_subtype":summary(selected),
                "unselected_grade2":summary(unselected),"maximum_service_selected":mean(selected_f),
                "maximum_service_unselected":mean(unselected_f),
                "selection_profit_gain":mean(selected["profit"]-unselected["profit"]),
                "optimistic_relaxation_overstatement":mean(optimistic["profit"]-selected["profit"]),
                "candidate_pairs":n})
    save_service(41,{"question":"Does identifying repairable quality subtypes change the return decision and prevent overstating upgrade potential?",
        "assumptions":__doc__,"parameters_are_hypothetical":True,
        "grade_shares_recomputed_within_each_source":True,
        "scope":"Fixed raw input, aggregate flow capacity, known conditional success .97; full quality-subtype inspection assumed free. No empirical station-KQC mapping or random subtype-count model.",
        "headline":{"elapsed_seconds":time.perf_counter()-started,"cases":len(rows),
                    "max_selection_profit_gain":max(r["selection_profit_gain"] for r in rows)},"rows":rows},__file__,
        (ROOT/"backbone"/"quality_lab.py",ROOT/"backbone"/"round40_quality_recoverability.py"))


if __name__=="__main__":
    main()
