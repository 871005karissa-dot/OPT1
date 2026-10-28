"""Round43: unsuccessful upgrade may remain grade2 instead of being scrapped.

retention rho is the fraction of failed returns still saleable as grade2.
Keep the conservative pre-reserved grade2-demand rule and all other assumptions.
No increased use of reserved demand or extra rework pass is introduced here.
rho=0 reproduces earlier scrap; rho=1 is full grade2 retention. Values are
hypothetical. Compare identifying repairable subtypes under both failure fates.
"""
from backbone.quality_lab import *
from backbone.round40_quality_recoverability import recoverability
from backbone.ball_screw import APPENDIX_COMPONENT_PROBABILITIES


def main():
    quality=recoverability(APPENDIX_COMPONENT_PROBABILITIES)
    q1,q2=quality["implied_grade1_share"],quality["implied_grade2_share"]
    d=(750.,150.)
    raw=required_input(d,(q1,q2),STATIONS,1)
    thresholds=[]
    rows=[]
    for rho in (0.,.5,1.):
        fill=(35.5-30*rho)/(120-30*rho)
        inventory=(35.5-30*rho)/(90-30*rho)
        thresholds.append({"failed_grade2_retention":rho,"fill_threshold":fill,"inventory_threshold":inventory})
        for feature in quality["single_feature_bounds"]:
            f=feature["single_feature_perfect_repair_upper_bound"]
            selected,_,selected_f,_=quality_action_pair(raw,d,.97,q1,q2,f,retention=rho)
            unselected,_,unselected_f,_=quality_action_pair(raw,d,.97*f,q1,q2,retention=rho)
            assert np.all(selected["profit"]>=unselected["profit"]-1e-6)
            assert np.all(selected_f>=unselected_f)
            rows.append({"KQC_name":feature["KQC_name"],"eligible_fraction":f,"failed_grade2_retention":rho,
                "selected":summary(selected),"unselected":summary(unselected),
                "selection_profit_gain":mean(selected["profit"]-unselected["profit"])})
    # Fixed-flow marginal-gain formula, independent of the allocation optimizer.
    flow=quality_forward(raw,forward(raw).loads[:,1],q1,q2)
    cap=available_returns(flow,d,350.)
    gap=np.maximum(d[0]-flow.g1,0.)
    errors=[]
    for eta in (.05,.1,.2,.35,.97):
      for rho in (0.,.5,1.):
        r=cap*.63
        direct=evaluate_quality(flow,d,r,eta,rho)["profit"]-evaluate_quality(flow,d,np.zeros(len(PROB)),eta,rho)["profit"]
        grade2_loss=1-rho*(1-eta)
        analytic=120*np.minimum(eta*r,gap)+90*np.maximum(eta*r-gap,0.)-(30*grade2_loss+5.5)*r
        error=float(np.max(np.abs(direct-analytic)))
        errors.append(error)
        assert error<1e-7
    save_service(43,{"question":"How much of the apparent upgrade threshold and inspection value comes from scrapping failed returns?",
        "assumptions":__doc__,"grade_shares":[q1,q2],"demands":d,"input":raw,
        "thresholds":thresholds,"headline":{"cases":len(rows),"analytic_marginal_gain_checks":len(errors),
                    "max_marginal_gain_error":max(errors)},"rows":rows},__file__,
        (ROOT/"backbone"/"quality_lab.py",ROOT/"backbone"/"round40_quality_recoverability.py"))


if __name__=="__main__":
    main()
