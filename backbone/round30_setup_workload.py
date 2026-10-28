"""Round 30: a rework batch consumes station-2 setup workload as well as processing."""
from backbone.recourse_lab import *


def main():
    rows = []
    differences = {}
    for setup in (0.0,100.0,350.0,700.0):
        service_down = 0
        for demands in ORDERS:
            flow = forward(release(demands))
            base = optimize_returns(flow, demands)
            action = optimize_returns(flow, demands, setup_workload=setup)
            assert mean(action["profit"]) <= mean(base["profit"]) + 1e-7
            service_down += mean(action["met"]) < mean(base["met"]) - 1e-9
            rows.append({"setup_workload":setup,"demands":demands,
                         "without_setup_workload":summary(base),"with_setup_workload":summary(action),
                         "expected_setup_capacity_used":setup*mean(action["sent"]>EPS)})
        differences[str(int(setup))] = service_down
    anchors = [row for row in rows if row["setup_workload"]==350 and row["demands"] in ((650.0,250.0),(700.0,200.0),(750.0,150.0))]
    save(30,{"question":"Does startup work remove capacity that a cost-only setup model leaves available?",
             "assumptions":"Hypothetical workload units equivalent to station-2 unit processing, not measured hours; eta=.97, F=0, cash ledger.",
             "headline":{"orders_with_lower_fulfilment":differences,"anchors":anchors},"rows":rows},__file__)


if __name__ == "__main__":
    main()
