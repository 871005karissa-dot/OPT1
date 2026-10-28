"""Round49: exhaustive integer-input choice under exact random-quality measures.

Explicit domain I in {0,...,2100}; normal processing uses the original forward
rule and yields fluid intermediate quantities, finished quality counts are
multinomial at floor(finished), and eta=.97 remains a fluid upgrade fraction.
Returns follow inspection and use the eligible/surplus/spare cap. This is exact
within this hybrid policy class, not a fully integer manufacturing schedule or
an optimization over pre-quality normal work allocations.
"""
import time
from backbone.exact_quality_economics import *


def main():
    started=time.perf_counter()
    training=json.loads((SERVICE_OUT/"round45.json").read_text(encoding="utf-8"))
    q1,q2=training["grade_shares"]
    d=tuple(training["demands"])
    f=training["eligible_fraction"]
    solver=ExactQualityEconomics(q1,q2,f,d)
    maximum=int(STATIONS[0].max_capacity)
    rows=[]
    for raw in range(maximum+1):
        row=solver.evaluate_economics(float(raw))
        rows.append(row)
        if raw%200==0:
            print(json.dumps({"last_integer_input":raw,"elapsed_seconds":time.perf_counter()-started}),flush=True)
    best=max(rows,key=lambda r:r["expected_profit"])
    maximum_service=max(rows,key=lambda r:r["fulfilment_probability"])
    constrained=[]
    for target in (.5,.6,.7,.75,.8,.85,.9,.95):
        feasible=[r for r in rows if r["fulfilment_probability"]>=target-1e-12]
        constrained.append({"target":target,"feasible":bool(feasible),
            "best":max(feasible,key=lambda r:r["expected_profit"]) if feasible else None})
    save_service(49,{"question":"Within an explicit integer-input fixed-forward policy class, what is the exact service-profit tradeoff?",
        "assumptions":__doc__,"grade_shares":[q1,q2],"eligible_fraction":f,"demands":d,
        "input_domain":{"minimum":0,"maximum":maximum,"integer_step":1},
        "optimality_scope":"Exhaustive optimum over the explicitly enumerated integer input domain and this fixed-forward maximal-return recourse class only. Material paid when processed; no global continuous-input/adaptive-forward/scheduling claim.",
        "best_unconstrained":best,"maximum_service":maximum_service,"constrained":constrained,
        "headline":{"elapsed_seconds":time.perf_counter()-started,"integer_inputs":len(rows),
                    "best_input":best["input"],"best_profit":best["expected_profit"],
                    "maximum_service_probability":maximum_service["fulfilment_probability"]},"rows":rows},__file__,
        (ROOT/"backbone"/"exact_quality_economics.py",ROOT/"backbone"/"exact_quality_service.py",
         ROOT/"backbone"/"quality_lab.py",ROOT/"backbone"/"round45_threshold_stability.py"))


if __name__=="__main__":
    main()
