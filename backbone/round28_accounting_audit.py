"""Round 28: isolate the additional substitution price-gap penalty."""
from backbone.recourse_lab import *


def main():
    rows = []
    flips = {}
    for holding in (30.0,75.0):
        count = 0
        for demands in ORDERS:
            flow = forward(release(demands))
            same = evaluate(flow, demands, allow_sub=False, holding=holding)
            cash = evaluate(flow, demands, holding=holding)
            legacy = evaluate(flow, demands, ledger="legacy", holding=holding)
            cash_delta = mean(cash["profit"] - same["profit"])
            legacy_delta = mean(legacy["profit"] - same["profit"])
            moved = mean(cash["substituted"])
            assert abs(cash_delta - moved * (holding - 60.0)) < 1e-7
            assert abs(legacy_delta - moved * (holding - 120.0)) < 1e-7
            assert abs(mean(cash["met"]) - mean(legacy["met"])) < 1e-12
            if cash_delta > 1e-6 and legacy_delta < -1e-6:
                count += 1
            rows.append({"demands": demands, "holding": holding, "same": summary(same),
                         "cash": summary(cash), "legacy_with_extra_penalty": summary(legacy),
                         "cash_delta_vs_same": cash_delta, "legacy_delta_vs_same": legacy_delta})
        flips[str(int(holding))] = count
    headline = {"opposite_policy_ranking_by_holding": flips,
                "cash_break_even_holding": 60.0, "legacy_break_even_holding": 120.0,
                "anchor_75_days": next(row for row in rows if row["demands"]==(550.0,350.0) and row["holding"]==75)}
    save(28, {"question": "Is a second price-gap term a distinct penalty or ordinary sales accounting?",
              "interpretation": "Both ledgers retained. Cash excludes the additional gap; it does not revise the manuscript replication.",
              "headline": headline, "rows": rows}, __file__)


if __name__ == "__main__":
    main()
