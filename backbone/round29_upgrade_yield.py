"""Round 29: independent grade-upgrade yield and an exact partial-return decision."""
from backbone.recourse_lab import *


def main():
    etas = (0.0,0.2,0.3,0.35,35.5/90.0,0.5,0.97)
    rows = []
    partial_orders = {}
    max_gain_formula_error = 0.0
    for eta in etas:
        count = 0
        for demands in ORDERS:
            flow = forward(release(demands))
            cap = available_returns(flow, demands)
            none = evaluate(flow, demands)
            full = evaluate(flow, demands, cap, eta)
            best = optimize_returns(flow, demands, eta)
            a = np.maximum(demands[0] - flow.g1, 0.0)
            r = best["sent"]
            analytic = 120.0*np.minimum(eta*r,a) + 90.0*np.maximum(eta*r-a,0.0) - 35.5*r
            error = float(np.max(np.abs(best["profit"]-none["profit"]-analytic)))
            max_gain_formula_error = max(max_gain_formula_error,error)
            assert np.all(best["profit"] >= full["profit"] - 1e-7)
            assert np.all(best["profit"] >= none["profit"] - 1e-7)
            partial = (r > EPS) & (r < cap-EPS)
            if np.any(partial):
                assert np.max(np.abs(flow.g1[partial]+eta*r[partial]-demands[0])) < 1e-7
            partial_probability = mean(partial)
            count += partial_probability > 1e-8
            if eta == 0.97:
                assert abs(mean(best["profit"]-full["profit"])) < 1e-6
            rows.append({"eta": eta, "demands": demands, "no_rework": summary(none),
                         "always_max_rework": summary(full), "optimal_rework": summary(best),
                         "partial_return_probability": partial_probability,
                         "profit_gain_vs_always_max": mean(best["profit"]-full["profit"])})
        partial_orders[str(eta)] = count
    assert max_gain_formula_error < 1e-7
    anchors = [row for row in rows if row["eta"]==0.35 and row["demands"] in ((650.0,250.0),(700.0,200.0),(750.0,150.0))]
    save(29, {"question":"Does separating upgrade yield from station yield produce no/partial/full return regions?",
              "assumptions":"Hypothetical eta sensitivity; deterministic fluid fraction, not a measured grade transition probability.",
              "headline":{"eta_threshold_before_grade1_filled":35.5/120.0,
                          "eta_threshold_after_grade1_filled":35.5/90.0,
                          "orders_with_positive_partial_return_probability":partial_orders,
                          "max_analytic_gain_error":max_gain_formula_error,"anchors":anchors},"rows":rows}, __file__)


if __name__ == "__main__":
    main()
