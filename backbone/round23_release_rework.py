"""Round 23: open P1 on the manuscript release quantity.

Round 5 lowered the input after the second pass, and planned profit rose on
every row. Here the release quantity stays at the no-rework input. Storage
uses Table 9's 15 and 75 days, with 30 days as the reference. The second pass
still uses station 2's own yield.
"""

from __future__ import annotations

from backbone.ball_screw import (
    HOLDING_COST_PER_DAY,
    MANUFACTURING_COSTS,
    MANUSCRIPT_SHARES,
    MATERIAL_COST,
    PRICES,
    STATIONS,
)
from backbone.evaluator import (
    ReworkPath,
    machines_required,
    profit_two_grades,
    reliability_from_machines,
    required_input,
    workloads,
)
from backbone.round2_share_consistency import POLICY_I_ROWS, POLICY_II_ROWS

P1 = ReworkPath(2, 2, 1)
SHARES = (float(MANUSCRIPT_SHARES[0]), float(MANUSCRIPT_SHARES[1]))
STORAGES = (15, 30, 75)


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


def profit_at(raw_input: float, demands, policy: int, storage: float, path):
    return profit_two_grades(
        raw_input,
        demands,
        SHARES,
        STATIONS,
        PRICES,
        MATERIAL_COST,
        MANUFACTURING_COSTS,
        HOLDING_COST_PER_DAY,
        storage,
        policy,
        path,
    ).profit


def sign(delta: float, tolerance: float) -> str:
    if delta > tolerance:
        return "+"
    if delta < -tolerance:
        return "-"
    return "0"


def main() -> None:
    print(f"P1 = ({P1.entry}, {P1.detection}, {P1.cycles})   release quantity is the no-rework input")
    print(f"states = {8 * 7 * 8 * 9 * 7}")
    print()
    open_at = {storage: 0 for storage in STORAGES}
    cells = {storage: {} for storage in STORAGES}
    for label, rows, policy in (
        ("Policy I", POLICY_I_ROWS, 1),
        ("Policy II", POLICY_II_ROWS, 2),
    ):
        print(label)
        for demand, *_rest in rows:
            demands = (float(demand[0]), float(demand[1]))
            raw_input = required_input(demands, SHARES, STATIONS, policy)
            machines_off, reliability_off = picture(raw_input, None)
            machines_on, reliability_on = picture(raw_input, P1)
            deltas = {
                storage: profit_at(raw_input, demands, policy, storage, P1)
                - profit_at(raw_input, demands, policy, storage, None)
                for storage in STORAGES
            }
            slope = (deltas[75] - deltas[30]) / (75 - 30)
            cross = None if abs(slope) < 1e-9 else 30 - deltas[30] / slope
            reliability_delta = reliability_on - reliability_off
            marks = []
            for storage in STORAGES:
                profit_sign = sign(deltas[storage], 1e-2)
                reliability_sign = sign(reliability_delta, 1e-6)
                cell = f"P{profit_sign} R{reliability_sign}"
                cells[storage][cell] = cells[storage].get(cell, 0) + 1
                if profit_sign == "+" and reliability_sign != "-":
                    open_at[storage] += 1
                    mark = "open"
                else:
                    mark = "shut"
                marks.append(f"{storage}d {mark} {deltas[storage]:+.2f}")
            cross_text = "none" if cross is None else f"{cross:.2f}"
            print(
                f"  {demand[0]:4},{demand[1]:<4}"
                f"  input {raw_input:.4f}"
                f"  machines {machines_off} -> {machines_on}"
                f"  R {reliability_off:.6f} -> {reliability_on:.6f}"
                f"  profit crosses 0 at day {cross_text}"
            )
            print(f"    {'   '.join(marks)}")
        print()
    for storage in STORAGES:
        shown = ", ".join(f"{name} {count}" for name, count in sorted(cells[storage].items()))
        print(f"storage {storage:2}   open {open_at[storage]:2} of 30   {shown}")


if __name__ == "__main__":
    main()
