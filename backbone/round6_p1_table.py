"""Round 6: P1 on every published demand in Tables 4 and 5.

Same path and same grade shares as round 5. The question is which rows
change the lower capacity vector.
"""

from __future__ import annotations

from backbone.ball_screw import MANUSCRIPT_SHARES, STATIONS
from backbone.evaluator import (
    ReworkPath,
    machines_required,
    reliability_from_machines,
    required_input,
    workloads,
)
from backbone.round2_share_consistency import POLICY_I_ROWS, POLICY_II_ROWS

P1 = ReworkPath(2, 2, 1)


def picture(raw_input: float, path: ReworkPath | None):
    loads = workloads(raw_input, STATIONS, path)
    counts = []
    for load, station in zip(loads, STATIONS):
        count = machines_required(load, station)
        if count is None:
            return None, 0.0
        counts.append(count)
    required = tuple(counts)
    return required, reliability_from_machines(required, STATIONS)


def main() -> None:
    shares = (float(MANUSCRIPT_SHARES[0]), float(MANUSCRIPT_SHARES[1]))
    changed = 0
    checked = 0
    for label, rows, policy in (
        ("Policy I", POLICY_I_ROWS, 1),
        ("Policy II", POLICY_II_ROWS, 2),
    ):
        print(label)
        for demand, _published_input, _published_r, _e1, _e2 in rows:
            demands = (float(demand[0]), float(demand[1]))
            off_input = required_input(demands, shares, STATIONS, policy)
            on_input = required_input(demands, shares, STATIONS, policy, P1)
            off_machines, off_r = picture(off_input, None)
            on_machines, on_r = picture(on_input, P1)
            checked += 1
            if off_machines != on_machines:
                changed += 1
                print(
                    f"  {demand[0]:4},{demand[1]:<4}"
                    f"  I {off_input:.4f} -> {on_input:.4f}"
                    f"  machines {off_machines} -> {on_machines}"
                    f"  R {off_r:.6f} -> {on_r:.6f}"
                )
    print(f"rows checked {checked}   lower capacity vector changed {changed}")


if __name__ == "__main__":
    main()
