"""Round77: the full-return simplification depends on terminal values.

One synthetic, reachable observed state, not population/factory results:
A725,B300,E40,remaining work40,D=(750,150),eta.97,c12.4,F2000.
Only scale terminal values together: (v1,v2)=t*(90,30). Price/demand/fee/
success/initial counts remain fixed. Choose r BEFORE its future outcomes.
The existing binary0/R solvers must not be reused once their positive-marginal
condition fails; this script enumerates all integer amounts independently.
"""
import math
from backbone.service_frontier import *


def main():
    a,b,e,spare=725,300,40,40
    d1,d2=750,150
    eta,cost,fee=.97,12.4,2000.
    maximum=min(e,b-d2,spare)
    rows=[]
    cash_errors=[]
    marginal_errors=[]
    for scale in (1.,.5,.25,.2,.1,0.):
        v1,v2=90*scale,30*scale
        baseline=120*min(a,d1)+60*min(b,d2)+v1*max(a-d1,0)+v2*max(b-d2,0)
        actions=[]
        for r in range(maximum+1):
            expected=service=fill=0.
            for y in range(r+1):
                probability=math.comb(r,y)*eta**y*(1-eta)**(r-y)
                high,low=a+y,b-r
                sub=min(max(high-d1,0),max(d2-low,0))
                cash=(120*min(high,d1)+60*min(low+sub,d2)+v1*max(high-d1-sub,0)
                      +v2*max(low+sub-d2,0)-cost*r-fee*(r>0))
                expected+=probability*cash
                service+=probability*(high>=d1 and low+sub>=d2)
                fill+=probability*min(y,d1-a)
            gain_before=(v1*eta-v2-cost)*r+(120-v1)*fill
            cash_errors.append(abs(expected-baseline-(gain_before-fee*(r>0))))
            assert cash_errors[-1]<1e-7
            actions.append({"return":r,"expected_cash_before_normal_cost":expected,
                "gain_after_setup_vs_no_return":expected-baseline,"gain_before_setup":gain_before,
                "conditional_full_order_probability":service})
        for r in range(maximum):
            tail_below_gap=sum(math.comb(r,y)*eta**y*(1-eta)**(r-y) for y in range(min(r,d1-a-1)+1))
            predicted=v1*eta-v2-cost+(120-v1)*eta*tail_below_gap
            actual=actions[r+1]["gain_before_setup"]-actions[r]["gain_before_setup"]
            marginal_errors.append(abs(predicted-actual))
            assert marginal_errors[-1]<1e-9
        best=max(actions,key=lambda x:(x["expected_cash_before_normal_cost"],x["conditional_full_order_probability"]))
        if v1*eta>v2+cost:
            assert best["return"] in (0,maximum)
        rows.append({"terminal_scale":scale,"terminal_values":[v1,v2],
            "excess_marginal":v1*eta-v2-cost,"binary_solver_sufficient_condition":v1*eta>v2+cost,
            "best":best,"always_return":actions[-1],
            "profit_loss_from_forcing_maximal_return":best["expected_cash_before_normal_cost"]-actions[-1]["expected_cash_before_normal_cost"],
            "actions":actions})
    assert 0<rows[-1]["best"]["return"]<maximum
    save_service(77,{"question":"Would the canonical0-or-full return structure survive a more conservative terminal resale assumption?",
        "assumptions":__doc__,"observed_state":{"A":a,"B":b,"eligible":e,"spare":spare,"demands":[d1,d2],"eta":eta,"setup_fee":fee},
        "positive_excess_marginal_scale_threshold":cost/(90*eta-30),
        "headline":{"terminal_scales":len(rows),"integer_actions_per_scale":maximum+1,
                    "direct_cash_vs_gain_max_error":max(cash_errors),"marginal_identity_max_error":max(marginal_errors)},"rows":rows},__file__)


if __name__=="__main__":
    main()
