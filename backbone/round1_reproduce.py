"""Round 1: reproduce the manuscript example D = (550, 350).

Run from the workspace root:

    python -m backbone.round1_reproduce
"""

from __future__ import annotations

import time

from backbone.ball_screw import (
    APPENDIX_COMPONENT_PROBABILITIES,
    APPENDIX_SHARES,
    DEMAND,
    KQCS,
    POLICY_I_TARGET,
    POLICY_II_TARGET,
    PUBLISHED_PMF,
    STATIONS,
)
from backbone.evaluator import (
    binomial_pmf,
    component_probabilities,
    evaluate,
    grade_shares,
    machines_required,
    reliability_by_enumeration,
    reliability_from_machines,
)


def close(left: float, right: float, tol: float = 5e-5) -> str:
    return "match" if abs(left - right) <= tol else "diff"


def vector_close(left: tuple[float, ...], right: tuple[float, ...], tol: float = 5e-4) -> str:
    if len(left) != len(right):
        return "diff"
    return "match" if all(abs(a - b) <= tol for a, b in zip(left, right)) else "diff"


def print_policy(title: str, result, target: dict) -> None:
    lcv = result.lower_capacity_vector
    print(title)
    print(f"  input        computed {result.raw_input:.6f}   manuscript {target['input']:.4f}   {close(result.raw_input, target['input'], 5e-4)}")
    print(f"  workloads    computed ({', '.join(f'{w:.4f}' for w in result.workloads)})")
    print(f"               manuscript ({', '.join(f'{w:.4f}' for w in target['workloads'])})   {vector_close(result.workloads, target['workloads'])}")
    if lcv is None:
        print("  LCV          infeasible")
    else:
        shown = tuple(float(v) for v in lcv)
        print(f"  LCV          computed {shown}")
        print(f"               manuscript {target['lcv']}   {vector_close(shown, target['lcv'], 1e-6)}")
    print(
        f"  reliability  computed {result.reliability:.6f}"
        f"   four decimals {result.reliability:.4f}"
        f"   manuscript {target['reliability']:.4f}"
        f"   {close(result.reliability, target['reliability'])}"
    )
    print(f"  machines     {result.machines_required}")
    print(f"  dominating states {result.dominating_state_count}")
    if result.feasible and result.machines_required is not None:
        started = time.perf_counter()
        enumerated = reliability_by_enumeration(result.machines_required, STATIONS)
        elapsed = time.perf_counter() - started
        gap = abs(enumerated - result.reliability)
        print(f"  enumeration  {enumerated:.6f}   gap {gap:.3e}   states summed {result.dominating_state_count}   {elapsed:.4f} s")
        if gap > 1e-9:
            raise SystemExit("enumeration and the product of tails disagree")
    print()


def main() -> None:
    probabilities = component_probabilities(KQCS)
    shares = grade_shares(probabilities)
    state_count = 1
    for station in STATIONS:
        state_count *= station.machine_count + 1
    factors = " x ".join(str(station.machine_count + 1) for station in STATIONS)
    print("D = (550, 350), two grades, ball-screw stations from Tables 2 and 3")
    print(f"capacity states = {factors} = {state_count}")
    print()

    print("component probabilities, normal formula versus Appendix D")
    names = [kqc.name for kqc in KQCS]
    for name, computed, printed in zip(names, probabilities, APPENDIX_COMPONENT_PROBABILITIES):
        for grade, (value, published) in enumerate(zip(computed, printed), start=1):
            print(f"  {name}, tolerance {grade}: computed {value:.6f}  printed {published:.4f}  {close(value, published, 5e-4)}")
    print(f"  shares computed Q = ({shares[0]:.6f}, {shares[1]:.6f})")
    print(f"  shares appendix Q = {APPENDIX_SHARES}")
    print()

    print("binomial probabilities versus Table 2, four decimals")
    for station in STATIONS:
        pmf = binomial_pmf(station.machine_count, station.availability)
        published = PUBLISHED_PMF[station.name]
        flags = [close(value, target, 5e-5) for value, target in zip(pmf, published)]
        verdict = "match" if all(flag == "match" for flag in flags) else "diff"
        rounded = ", ".join(f"{value:.4f}" for value in pmf)
        print(f"  {station.name}: {rounded}  {verdict}")
    print()

    model_i = evaluate(DEMAND, STATIONS, KQCS, policy=1)
    model_ii = evaluate(DEMAND, STATIONS, KQCS, policy=2)
    print_policy("Policy I, normal formula on Table 3", model_i, POLICY_I_TARGET)
    print_policy("Policy II, normal formula on Table 3", model_ii, POLICY_II_TARGET)

    replay_i = evaluate(
        DEMAND,
        STATIONS,
        KQCS,
        policy=1,
        probabilities=APPENDIX_COMPONENT_PROBABILITIES,
    )
    replay_ii = evaluate(
        DEMAND,
        STATIONS,
        KQCS,
        policy=2,
        probabilities=APPENDIX_COMPONENT_PROBABILITIES,
    )
    print_policy("Policy I, Appendix D printed probabilities", replay_i, POLICY_I_TARGET)
    print_policy("Policy II, Appendix D printed probabilities", replay_ii, POLICY_II_TARGET)

    print("LCV and reliability when the manuscript workloads are given directly")
    for title, target in (("Policy I", POLICY_I_TARGET), ("Policy II", POLICY_II_TARGET)):
        required = tuple(
            machines_required(load, station)
            for load, station in zip(target["workloads"], STATIONS)
        )
        if any(count is None for count in required):
            print(f"  {title}: infeasible")
            continue
        counts = tuple(count for count in required if count is not None)
        vector = tuple(
            count * station.machine_capacity for count, station in zip(counts, STATIONS)
        )
        reliability = reliability_from_machines(counts, STATIONS)
        print(
            f"  {title}: LCV {vector} {vector_close(vector, target['lcv'], 1e-6)};"
            f" reliability {reliability:.6f} (four decimals {reliability:.4f})"
            f" versus {target['reliability']:.4f}"
        )


if __name__ == "__main__":
    main()
