"""Round 27: distinguish workload coverage from joint order fulfilment."""
from backbone.recourse_lab import *
from backbone.evaluator import line_yield
from backbone.round25_state_policy import load_reliability, sweep


def main():
    rows = []
    max_replay_error = 0.0
    for demands in ORDERS:
        for label, raw_input in (("grade1_onset", demands[0] / (line_yield(STATIONS) * Q1)),
                                 ("I", release(demands, 1)), ("II", release(demands, 2))):
            flow = forward(raw_input)
            same = evaluate(flow, demands, allow_sub=False, ledger="legacy")
            sub = evaluate(flow, demands, ledger="legacy")
            state = evaluate(flow, demands, available_returns(flow, demands), ledger="legacy")
            reference = sweep(raw_input, demands)
            errors = (abs(mean(same["profit"]) - reference["same_profit"]),
                      abs(mean(sub["profit"]) - reference["substitute_profit"]),
                      abs(mean(state["profit"]) - reference["state_profit"]),
                      abs(mean(same["met"]) - reference["same_met"]),
                      abs(mean(state["met"]) - reference["state_met"]))
            max_replay_error = max(max_replay_error, *errors)
            load_r = load_reliability(raw_input)[1]
            if label == "I":
                assert abs(load_r - mean(same["met"])) < 1e-9
            if label == "II":
                assert abs(load_r - mean(sub["met"])) < 1e-9
            rows.append({"demands": demands, "input_type": label, "input": raw_input,
                         "workload_coverage_probability": load_r,
                         "same_grade": summary(same), "downward_substitution": summary(sub),
                         "state_rule": summary(state)})
    assert max_replay_error < 1e-6
    false_confidence = sum(row["input_type"] == "grade1_onset" and
                           row["workload_coverage_probability"] > 0 and
                           row["state_rule"]["fulfilment_probability"] < 1e-9 for row in rows)
    headline = {"grade1_onset_positive_workload_R_but_zero_fulfilment": false_confidence,
                "orders": len(ORDERS), "max_legacy_replay_error": max_replay_error,
                "anchor": next(row for row in rows if row["demands"] == (550.0,350.0) and row["input_type"] == "grade1_onset")}
    save(27, {"question": "Can workload reliability stand in for order fulfilment at arbitrary releases?",
              "headline": headline, "rows": rows}, __file__)


if __name__ == "__main__":
    main()
