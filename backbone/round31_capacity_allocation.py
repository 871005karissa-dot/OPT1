"""Round 31: allocate station-2 forward work and returns using linear-region vertices.

This aggregate-capacity fluid model does not establish scheduling feasibility.
Unprocessed WIP has zero salvage, as in the existing truncated-flow evaluator.
"""
import time
from backbone.recourse_lab import *


def main():
    started = time.perf_counter()
    fractions = np.linspace(0.0,1.0,21)
    rows = []
    improved = 0
    for demands in ORDERS:
        raw_input = release(demands)
        base_flow = forward(raw_input)
        base = optimize_returns(base_flow,demands,setup_workload=350.0)
        grid, _, fixed, fixed_rows = capacity_policy(raw_input,demands,fractions,setup_workload=350.0)
        action, chosen, vertices = exact_capacity_policy(raw_input,demands,setup_workload=350.0)
        normal_base = evaluate(base_flow,demands)
        normal_adaptive,_,_ = exact_capacity_policy(raw_input,demands,allow_rework=False)
        gain = mean(action["profit"]-base["profit"])
        curtailment = mean(normal_adaptive["profit"]-normal_base["profit"])
        assert gain >= -1e-7
        assert np.all(action["profit"]>=grid["profit"]-1e-6)
        assert mean(action["profit"]) >= fixed["expected_profit"]-1e-7
        improved += gain > 1e-6
        flow = forward(raw_input,chosen)
        upstream = flow.loads[:,0]*STATIONS[0].yield_rate
        unprocessed = mean(np.maximum(upstream-flow.loads[:,1],0.0))
        row = {"demands":demands,"input":raw_input,"forward_first":summary(base),
               "state_adaptive_exact_vertices":summary(action),"best_common_fraction_grid":fixed,
               "gain_vs_forward_first":gain,"probability_positive_reservation":mean(chosen>EPS),
               "mean_reserve_fraction":mean(chosen),"max_chosen_fraction":float(np.max(chosen)),
               "expected_unprocessed_station2_inflow":unprocessed,"fixed_fraction_grid":fixed_rows,
               "no_rework_adaptive":summary(normal_adaptive),"no_rework_forward_first":summary(normal_base),
               "normal_curtailment_gain":curtailment,"return_allocation_interaction":gain-curtailment,
               "vertex_candidates_per_state":vertices,"gain_vs_21_point_grid":mean(action["profit"]-grid["profit"])}
        if demands in ((550.0,350.0),(650.0,250.0),(700.0,200.0),(750.0,150.0)):
            fine, fine_b, _, _ = capacity_policy(raw_input,demands,np.linspace(0.0,1.0,41),setup_workload=350.0)
            refinement = mean(fine["profit"]-action["profit"])
            assert np.all(action["profit"]>=fine["profit"]-1e-6)
            row["refined_grid"] = summary(fine)
            row["gain_vs_41_point_grid"] = -refinement
        rows.append(row)
    anchors = [{key:value for key,value in row.items() if key!="fixed_fraction_grid"}
               for row in rows if row["demands"] in ((650.0,250.0),(700.0,200.0),(750.0,150.0))]
    save(31,{"question":"Can capacity allocated between forward processing and returns improve on forward-first?",
             "assumptions":"Cash ledger; eta=.97; setup workload=350 hypothetical processing-equivalent units; fixed Policy-I releases; capacity observed before allocation; aggregate workload only; zero salvage of unprocessed WIP.",
             "optimality_scope":"Piecewise-linear vertices for continuous station-2 forward work and surplus returns at a fixed raw release; 21-point grid comparison for all orders and 41-point grid for four; not a global production/scheduling optimum.",
             "headline":{"orders_improved":improved,"orders":len(ORDERS),"elapsed_seconds":time.perf_counter()-started,
                         "anchors":anchors},"rows":rows},__file__)


if __name__ == "__main__":
    main()
