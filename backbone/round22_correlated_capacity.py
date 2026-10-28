"""Round 22: within-station correlation on the manuscript capacity vectors.

Chen and Lin compute system reliability as a product of independent binomial
tails. Yeh and Fiondella replace that tail with their correlated binomial,
equation (7): machines on one station share a correlation, and stations stay
independent. The manuscript machine counts, availabilities, and lower capacity
vectors are unchanged.
"""

from __future__ import annotations

import math

from backbone.ball_screw import STATIONS

POLICY_I = (6, 5, 6, 7, 5)
POLICY_II = (5, 4, 5, 5, 4)
RHOS = (0.0, 0.2, 0.4, 0.6, 0.8, 1.0)

# Yeh and Fiondella, Table 1: four lines, p = 0.8.
TABLE_1 = {
    0.0: (0.00160, 0.02560, 0.15360, 0.40960, 0.40960),
    0.2: (0.04824, 0.01311, 0.10322, 0.36127, 0.47416),
    1.0: (0.20000, 0.00000, 0.00000, 0.00000, 0.80000),
}


def state_probabilities(machine_count: int, availability: float, correlation: float) -> tuple[float, ...]:
    """Correlated binomial of Yeh and Fiondella, equation (7).

    beta = 1 + correlation * (1 - p) / p. For one or more machines up, the mass
    is the binomial probability at success probability p * beta, divided by beta.
    The all-down mass is whatever remains. Correlation 0 is the ordinary binomial.
    """
    if machine_count < 0:
        raise ValueError("machine_count must be non-negative")
    if not 0.0 < availability < 1.0:
        raise ValueError("availability must be strictly between 0 and 1")
    if not 0.0 <= correlation <= 1.0:
        raise ValueError("correlation must lie between 0 and 1")
    beta = 1.0 + correlation * (1.0 - availability) / availability
    success = availability * beta
    failure = 1.0 - success
    probabilities = [0.0] * (machine_count + 1)
    running = 0.0
    if failure <= 0.0:
        probabilities[machine_count] = 1.0 / beta
        running = probabilities[machine_count]
    else:
        for up in range(1, machine_count + 1):
            log_choose = (
                math.lgamma(machine_count + 1)
                - math.lgamma(up + 1)
                - math.lgamma(machine_count - up + 1)
            )
            probabilities[up] = math.exp(
                log_choose
                + up * math.log(success)
                + (machine_count - up) * math.log(failure)
                - math.log(beta)
            )
            running += probabilities[up]
    probabilities[0] = 1.0 - running
    return tuple(probabilities)


def tail(required: int, machine_count: int, availability: float, correlation: float) -> float:
    probabilities = state_probabilities(machine_count, availability, correlation)
    return sum(probabilities[required:])


def reliability(required: tuple[int, ...], correlation: float) -> float:
    value = 1.0
    for count, station in zip(required, STATIONS):
        value *= tail(count, station.machine_count, station.availability, correlation)
    return value


def table_check() -> str:
    worst = 0.0
    for correlation, published in TABLE_1.items():
        got = state_probabilities(4, 0.8, correlation)
        worst = max(worst, max(abs(left - right) for left, right in zip(got, published)))
    return "match" if worst <= 5e-5 else "diff"


def main() -> None:
    print(f"Table 1 of Yeh and Fiondella: {table_check()}")
    print(f"stations {tuple(station.machine_count for station in STATIONS)}")
    print(f"Policy I machines {POLICY_I}   Policy II machines {POLICY_II}")
    base_i = reliability(POLICY_I, 0.0)
    base_ii = reliability(POLICY_II, 0.0)
    print(f"correlation 0: Policy I {base_i:.6f}   Policy II {base_ii:.6f}   gap {base_ii - base_i:.6f}")
    for correlation in RHOS:
        policy_i = reliability(POLICY_I, correlation)
        policy_ii = reliability(POLICY_II, correlation)
        print(
            f"  rho {correlation:.1f}"
            f"  I {policy_i:.6f} ({policy_i - base_i:+.6f})"
            f"  II {policy_ii:.6f} ({policy_ii - base_ii:+.6f})"
            f"  gap {policy_ii - policy_i:.6f}"
        )


if __name__ == "__main__":
    main()
