"""Round42: a one-direction adjustment can repair only one tolerance tail.

Normal KQC data only: rounded strict/wide probabilities cannot identify tails.
Moving a value up can repair the lower tail; moving it down can repair the upper
tail. These are hypothetical perfect capabilities; no actual machining direction
or station-KQC correspondence is inferred. Other KQCs remain unchanged.
"""
from backbone.quality_lab import *
from backbone.round40_quality_recoverability import recoverability
from backbone.ball_screw import KQCS
from backbone.evaluator import component_probabilities,interval_probability


def one_sided_bounds():
    probabilities=component_probabilities(KQCS)
    quality=recoverability(probabilities)
    strict=[p[0] for p in probabilities]
    q2=quality["implied_grade2_share"]
    rows=[]
    for j,kqc in enumerate(KQCS):
        (lo,hi),(wide_lo,wide_hi)=kqc.tolerances
        lower=interval_probability(kqc.mean,kqc.stdev,wide_lo,lo)
        upper=interval_probability(kqc.mean,kqc.stdev,hi,wide_hi)
        others=float(np.prod([p for k,p in enumerate(strict) if k!=j]))
        expected=quality["single_feature_bounds"][j]["single_feature_perfect_repair_upper_bound"]
        assert abs((lower+upper)*others/q2-expected)<1e-12
        rows.append({"KQC_index":j,"KQC_name":kqc.name,"bidirectional_bound":expected,
                     "increase_value_bound":lower*others/q2,"decrease_value_bound":upper*others/q2})
    return quality,rows


def main():
    quality,bounds=one_sided_bounds()
    q1,q2=quality["implied_grade1_share"],quality["implied_grade2_share"]
    rows=[]
    d=(750.,150.)
    raw=required_input(d,(q1,q2),STATIONS,1)
    for feature in bounds:
      bidirectional,_,_,_=quality_action_pair(raw,d,.97,q1,q2,feature["bidirectional_bound"])
      for direction in ("increase_value_bound","decrease_value_bound"):
        b,_,found,_=quality_action_pair(raw,d,.97,q1,q2,feature[direction])
        assert np.all(bidirectional["profit"]>=b["profit"]-1e-6)
        rows.append({"demands":d,"input":raw,**feature,"direction":direction,
                     "bidirectional":summary(bidirectional),"one_sided":summary(b),
                     "one_sided_service_ceiling":mean(found)})
    save_service(42,{"question":"Does a one-direction physical adjustment further limit repairable quality subtypes?",
        "assumptions":__doc__,"grade_shares":[q1,q2],"bounds":bounds,
        "headline":{"cases":len(rows),"source":"normal_parameters_and_tolerances"},"rows":rows},__file__,
        (ROOT/"backbone"/"quality_lab.py",ROOT/"backbone"/"round40_quality_recoverability.py"))


if __name__=="__main__":
    main()
