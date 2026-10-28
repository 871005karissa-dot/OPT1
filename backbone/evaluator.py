"""Multistate flow network evaluator for multi-grade demand.

This is the checkable backbone. One call evaluates one demand and one policy.
Policy I fulfills each grade with that grade only. Policy II allows full
downward substitution. A rework path is off unless the caller passes one.
P1, P2, and P3 can be passed alone. P3 is accepted only together with P2.
P1 may be open on top of P2, or on top of P2 and P3.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from itertools import product


@dataclass(frozen=True)
class KQC:
    """One key quality characteristic and its tolerances, strictest first."""

    name: str
    mean: float
    stdev: float
    tolerances: tuple[tuple[float, float], ...]


@dataclass(frozen=True)
class ReworkPath:
    """Stations are numbered from 1. cycles is the rework count in P=(entry, detection, cycles)."""

    entry: int
    detection: int
    cycles: int


@dataclass(frozen=True)
class Workstation:
    name: str
    machine_count: int
    machine_capacity: float
    yield_rate: float
    availability: float

    @property
    def max_capacity(self) -> float:
        return self.machine_count * self.machine_capacity


@dataclass(frozen=True)
class Evaluation:
    policy: int
    component_probabilities: tuple[tuple[float, ...], ...]
    shares: tuple[float, ...]
    raw_input: float
    workloads: tuple[float, ...]
    machines_required: tuple[int, ...] | None
    lower_capacity_vector: tuple[float, ...] | None
    reliability: float
    feasible: bool
    capacity_state_count: int
    dominating_state_count: int


def normal_cdf(z: float) -> float:
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def interval_probability(mean: float, stdev: float, lsl: float, usl: float) -> float:
    """Probability that a normal specification falls inside [lsl, usl]."""
    if stdev <= 0:
        raise ValueError("stdev must be positive")
    upper = normal_cdf((usl - mean) / stdev)
    lower = normal_cdf((lsl - mean) / stdev)
    return max(0.0, upper - lower)


def component_probabilities(kqcs: tuple[KQC, ...]) -> tuple[tuple[float, ...], ...]:
    """Probability that each KQC meets each tolerance."""
    return tuple(
        tuple(interval_probability(kqc.mean, kqc.stdev, lsl, usl) for lsl, usl in kqc.tolerances)
        for kqc in kqcs
    )


def grade_shares(probabilities: tuple[tuple[float, ...], ...]) -> tuple[float, ...]:
    """Grade shares from independent KQCs and nested tolerances.

    The share of grade g is the probability that every KQC meets tolerance g,
    minus the probability that every KQC meets the stricter tolerance g-1.
    """
    if not probabilities:
        raise ValueError("at least one KQC is required")
    grade_count = len(probabilities[0])
    if any(len(row) != grade_count for row in probabilities):
        raise ValueError("every KQC must have the same number of tolerances")

    shares: list[float] = []
    previous = 0.0
    for grade in range(grade_count):
        cumulative = 1.0
        for row in probabilities:
            cumulative *= row[grade]
        shares.append(cumulative - previous)
        previous = cumulative
    return tuple(shares)


def line_yield(stations: tuple[Workstation, ...]) -> float:
    value = 1.0
    for station in stations:
        value *= station.yield_rate
    return value


def as_paths(rework: ReworkPath | tuple[ReworkPath, ...] | None) -> tuple[ReworkPath, ...]:
    if rework is None:
        return ()
    if isinstance(rework, ReworkPath):
        return (rework,)
    return tuple(rework)


def validate_rework(
    rework: ReworkPath | tuple[ReworkPath, ...] | None,
    station_count: int,
    scrap_rate: float | None = None,
) -> tuple[ReworkPath, ...]:
    """P1 is the in-place yield-loss cycle. P2 and P3 return units still outside 0.35 dB.

    P3 is the residue after P2, so it is not accepted alone. P1 may be combined
    with P2, or with P2 and P3. The yield-loss pass stays on the forward flow.
    """
    paths = as_paths(rework)
    keys = tuple((path.entry, path.detection, path.cycles) for path in paths)
    allowed = {(2, 2, 1), (5, 6, 1), (2, 6, 1)}
    for path, key in zip(paths, keys):
        if key not in allowed:
            raise ValueError(f"path {key} is not one of P1, P2, P3")
        if not 1 <= path.entry <= path.detection <= station_count:
            raise ValueError("rework path does not fit this line")
    if (2, 6, 1) in keys and (5, 6, 1) not in keys:
        raise ValueError("P3 returns units that still fail after P2")
    if any(key != (2, 2, 1) for key in keys) and scrap_rate is None:
        raise ValueError("P2 and P3 need the share of output above 0.35 dB")
    return paths


def _flow(
    raw_input: float,
    stations: tuple[Workstation, ...],
    rework: ReworkPath | tuple[ReworkPath, ...] | None = None,
    scrap_rate: float | None = None,
) -> tuple[tuple[float, ...], float]:
    """Station loads and finished process output for one raw input.

    P1 alone keeps the forward yield-loss formula. P2 and P3 alone add the
    insertion-loss returns. When P1 is open together with those returns, the
    forward pass runs first and the returns are added to that finished output.
    """
    paths = validate_rework(rework, len(stations), scrap_rate)
    yields = tuple(station.yield_rate for station in stations)
    keys = tuple((path.entry, path.detection, path.cycles) for path in paths)
    has_p1 = (2, 2, 1) in keys
    returns = tuple(path for path, key in zip(paths, keys) if key != (2, 2, 1))
    if has_p1 and returns:
        loads = [0.0] * len(stations)
        inflow = raw_input
        for index, rate in enumerate(yields):
            if index == 1:
                loads[index] = inflow * (2.0 - rate)
                inflow = inflow * rate * (2.0 - rate)
            else:
                loads[index] = inflow
                inflow *= rate
        finished = inflow
        scrap_units = finished * (scrap_rate or 0.0)
        for path in sorted(returns, key=lambda path: -path.entry):
            extra = scrap_units
            for index in range(path.entry - 1, path.detection):
                loads[index] += extra
                extra *= yields[index]
            finished += extra
            scrap_units = extra * (scrap_rate or 0.0)
        return tuple(loads), finished
    if has_p1:
        loads: list[float] = []
        inflow = raw_input
        for index, rate in enumerate(yields, start=1):
            if index == 2:
                loads.append(inflow * (2.0 - rate))
                inflow = inflow * rate * (2.0 - rate)
            else:
                loads.append(inflow)
                inflow *= rate
        return tuple(loads), inflow

    loads = [0.0] * len(stations)
    inflow = raw_input
    for index, rate in enumerate(yields):
        loads[index] += inflow
        inflow *= rate
    finished = inflow
    scrap_units = finished * (scrap_rate or 0.0)
    ordered = sorted(paths, key=lambda path: -path.entry)
    for path in ordered:
        extra = scrap_units
        for index in range(path.entry - 1, path.detection):
            loads[index] += extra
            extra *= yields[index]
        finished += extra
        scrap_units = extra * (scrap_rate or 0.0)
    return tuple(loads), finished


def throughput(
    stations: tuple[Workstation, ...],
    rework: ReworkPath | tuple[ReworkPath, ...] | None = None,
    scrap_rate: float | None = None,
) -> float:
    """Finished process units per unit of raw input."""
    _loads, finished = _flow(1.0, stations, rework, scrap_rate)
    return finished


def required_input(
    demands: tuple[float, ...],
    shares: tuple[float, ...],
    stations: tuple[Workstation, ...],
    policy: int,
    rework: ReworkPath | tuple[ReworkPath, ...] | None = None,
    scrap_rate: float | None = None,
) -> float:
    """Raw-material input required by Policy I or Policy II.

    Policy I takes the maximum same-grade input. Policy II takes the maximum
    of the grade-1 input and each cumulative downward-substitution input.
    """
    if policy not in (1, 2):
        raise ValueError("policy must be 1 or 2")
    if len(demands) != len(shares):
        raise ValueError("demand and grade share counts differ")
    if any(share <= 0 for share in shares):
        raise ValueError("every grade share must be positive")

    theta = throughput(stations, rework, scrap_rate)
    same_grade = tuple(demand / (theta * share) for demand, share in zip(demands, shares))
    if policy == 1:
        return max(same_grade)

    cumulative_demand = demands[0]
    cumulative_share = shares[0]
    candidates = [same_grade[0]]
    for demand, share in zip(demands[1:], shares[1:]):
        cumulative_demand += demand
        cumulative_share += share
        candidates.append(cumulative_demand / (theta * cumulative_share))
    return max(candidates)


def workloads(
    raw_input: float,
    stations: tuple[Workstation, ...],
    rework: ReworkPath | tuple[ReworkPath, ...] | None = None,
    scrap_rate: float | None = None,
) -> tuple[float, ...]:
    """WIP load at each station. The next station receives the good output.

    P1 processes station 2's yield loss once at station 2. P2 returns units
    above 0.35 dB from station 6 to station 5 once. P3 returns the units that
    are still above 0.35 dB after that pass, from station 6 to station 2 once.
    P1 may run on the same line as P2, or as P2 and P3.
    """
    loads, _finished = _flow(raw_input, stations, rework, scrap_rate)
    return loads


def machines_required(load: float, station: Workstation) -> int | None:
    """Smallest number of machines whose capacity covers the load."""
    if load <= 0:
        return 0
    count = math.ceil(load / station.machine_capacity - 1e-10)
    if count > station.machine_count:
        return None
    return count


def binomial_pmf(machine_count: int, availability: float) -> tuple[float, ...]:
    """P(exactly k machines are up), k = 0, ..., machine_count."""
    if machine_count < 0:
        raise ValueError("machine_count must be non-negative")
    if not 0.0 < availability < 1.0:
        raise ValueError("availability must be strictly between 0 and 1")
    log_q = math.log(1.0 - availability)
    log_p = math.log(availability)
    pmf = []
    for k in range(machine_count + 1):
        log_choose = (
            math.lgamma(machine_count + 1)
            - math.lgamma(k + 1)
            - math.lgamma(machine_count - k + 1)
        )
        pmf.append(math.exp(log_choose + k * log_p + (machine_count - k) * log_q))
    return tuple(pmf)


def reliability_from_machines(
    required: tuple[int, ...],
    stations: tuple[Workstation, ...],
) -> float:
    """Product of binomial tails. Stations are independent."""
    reliability = 1.0
    for count, station in zip(required, stations):
        pmf = binomial_pmf(station.machine_count, station.availability)
        reliability *= sum(pmf[count:])
    return reliability


def capacity_state_count(stations: tuple[Workstation, ...]) -> int:
    count = 1
    for station in stations:
        count *= station.machine_count + 1
    return count


def dominating_state_count(required: tuple[int, ...], stations: tuple[Workstation, ...]) -> int:
    count = 1
    for machines, station in zip(required, stations):
        count *= station.machine_count - machines + 1
    return count


def reliability_by_enumeration(
    required: tuple[int, ...],
    stations: tuple[Workstation, ...],
) -> float:
    """Sum of state probabilities over capacity vectors that dominate the LCV.

    This is the definition behind the product of tails. It is here so a run
    can show that the state space is still small enough to add up.
    """
    pmfs = [binomial_pmf(station.machine_count, station.availability) for station in stations]
    ranges = [
        range(machines, station.machine_count + 1)
        for machines, station in zip(required, stations)
    ]
    total = 0.0
    for state in product(*ranges):
        probability = 1.0
        for index, machines_up in enumerate(state):
            probability *= pmfs[index][machines_up]
        total += probability
    return total


def evaluate(
    demands: tuple[float, ...],
    stations: tuple[Workstation, ...],
    kqcs: tuple[KQC, ...],
    policy: int,
    probabilities: tuple[tuple[float, ...], ...] | None = None,
    rework: ReworkPath | tuple[ReworkPath, ...] | None = None,
    scrap_rate: float | None = None,
) -> Evaluation:
    """Evaluate one demand under one policy.

    Pass `probabilities` only to replay a recorded set of component
    probabilities. The default computes them from the normal formula.
    """
    if probabilities is None:
        probabilities = component_probabilities(kqcs)
    shares = grade_shares(probabilities)
    if scrap_rate is None and any(
        (path.entry, path.detection, path.cycles) != (2, 2, 1) for path in as_paths(rework)
    ):
        scrap_rate = max(0.0, 1.0 - sum(shares))
    raw_input = required_input(demands, shares, stations, policy, rework, scrap_rate)
    loads = workloads(raw_input, stations, rework, scrap_rate)
    required_list: list[int] = []
    feasible = True
    for load, station in zip(loads, stations):
        required = machines_required(load, station)
        if required is None:
            feasible = False
            break
        required_list.append(required)

    if not feasible:
        return Evaluation(
            policy=policy,
            component_probabilities=probabilities,
            shares=shares,
            raw_input=raw_input,
            workloads=loads,
            machines_required=None,
            lower_capacity_vector=None,
            reliability=0.0,
            feasible=False,
            capacity_state_count=capacity_state_count(stations),
            dominating_state_count=0,
        )

    required_tuple = tuple(required_list)
    vector = tuple(
        count * station.machine_capacity
        for count, station in zip(required_tuple, stations)
    )
    return Evaluation(
        policy=policy,
        component_probabilities=probabilities,
        shares=shares,
        raw_input=raw_input,
        workloads=loads,
        machines_required=required_tuple,
        lower_capacity_vector=vector,
        reliability=reliability_from_machines(required_tuple, stations),
        feasible=True,
        capacity_state_count=capacity_state_count(stations),
        dominating_state_count=dominating_state_count(required_tuple, stations),
    )


@dataclass(frozen=True)
class ProfitResult:
    """Accounting profit of a planned input. Capacity randomness stays in reliability."""

    material: float
    manufacturing: float
    inventory: float
    substitution_loss: float
    current_revenue: float
    future_revenue: float
    profit: float
    output: tuple[float, float]
    excess_after_substitution: tuple[float, float]
    substituted_grade1_for_grade2: float


def planned_output(
    raw_input: float,
    shares: tuple[float, ...],
    stations: tuple[Workstation, ...],
    rework: ReworkPath | tuple[ReworkPath, ...] | None = None,
    scrap_rate: float | None = None,
) -> tuple[float, ...]:
    scale = raw_input * throughput(stations, rework, scrap_rate)
    return tuple(scale * share for share in shares)


def _grade_balance(
    grades: tuple[float, float],
    demands: tuple[float, float],
    policy: int,
) -> tuple[tuple[float, float], float, tuple[float, float]]:
    """Excess, substituted units, and units sold into the order."""
    grade1, grade2 = grades
    demand1, demand2 = demands
    if policy == 1:
        return (grade1 - demand1, grade2 - demand2), 0.0, (min(grade1, demand1), min(grade2, demand2))
    grade1_left = grade1 - demand1
    grade2_short = demand2 - grade2
    substituted = min(max(grade1_left, 0.0), max(grade2_short, 0.0))
    excess = (grade1_left - substituted, grade2 - demand2 + substituted)
    sold = (min(grade1, demand1), min(grade2 + substituted, demand2))
    return excess, substituted, sold


def profit_from_flow(
    grades: tuple[float, float],
    loads: tuple[float, ...],
    demands: tuple[float, float],
    prices: tuple[float, float],
    material_cost: float,
    manufacturing_costs: tuple[float, ...],
    holding_cost_per_day: float,
    storage_days: float,
    policy: int,
    revenue_on_delivered: bool = False,
) -> ProfitResult:
    """Same prices and costs as the planned account.

    The planned account books the whole order. Delivered revenue books only
    units the realized flow actually sold into that order.
    """
    if policy not in (1, 2):
        raise ValueError("policy must be 1 or 2")
    if len(manufacturing_costs) != len(loads):
        raise ValueError("one manufacturing cost is required per station")

    excess, substituted, sold = _grade_balance(grades, demands, policy)
    demand1, demand2 = demands
    material = loads[0] * material_cost
    manufacturing = sum(load * cost for load, cost in zip(loads, manufacturing_costs))
    held = sum(max(amount, 0.0) for amount in excess)
    inventory = held * holding_cost_per_day * storage_days
    substitution_loss = substituted * (prices[0] - prices[1])
    if revenue_on_delivered:
        current_revenue = sold[0] * prices[0] + sold[1] * prices[1]
    else:
        current_revenue = demand1 * prices[0] + demand2 * prices[1]
    future_revenue = max(excess[0], 0.0) * prices[0] + max(excess[1], 0.0) * prices[1]
    total = current_revenue + future_revenue - material - manufacturing - inventory - substitution_loss
    return ProfitResult(
        material=material,
        manufacturing=manufacturing,
        inventory=inventory,
        substitution_loss=substitution_loss,
        current_revenue=current_revenue,
        future_revenue=future_revenue,
        profit=total,
        output=grades,
        excess_after_substitution=excess,
        substituted_grade1_for_grade2=substituted,
    )


def profit_two_grades(
    raw_input: float,
    demands: tuple[float, float],
    shares: tuple[float, float],
    stations: tuple[Workstation, ...],
    prices: tuple[float, float],
    material_cost: float,
    manufacturing_costs: tuple[float, ...],
    holding_cost_per_day: float,
    storage_days: float,
    policy: int,
    rework: ReworkPath | tuple[ReworkPath, ...] | None = None,
    scrap_rate: float | None = None,
) -> ProfitResult:
    """Profit for two grades under Policy I or full downward substitution.

    Current revenue prices the order. Excess left after substitution is sold
    later at its own grade price and accrues holding cost. A grade-1 unit used
    for grade-2 demand loses the price gap.
    """
    output = planned_output(raw_input, shares, stations, rework, scrap_rate)
    grades = (output[0], output[1])
    loads = workloads(raw_input, stations, rework, scrap_rate)
    return profit_from_flow(
        grades,
        loads,
        demands,
        prices,
        material_cost,
        manufacturing_costs,
        holding_cost_per_day,
        storage_days,
        policy,
    )


def realized_series_flow(
    raw_input: float,
    available_capacity: tuple[float, ...],
    stations: tuple[Workstation, ...],
    rework: ReworkPath | tuple[ReworkPath, ...] | None = None,
) -> tuple[tuple[float, ...], float]:
    """Flow through a line when each station is capped by the machines that are up.

    Rework off: a station processes the incoming good output up to its realized
    capacity, then applies its yield. P1: station 2 reworks its own yield loss
    once, using whatever capacity remains after the first pass. P2 and P3 are
    not applied here.
    """
    if len(available_capacity) != len(stations):
        raise ValueError("one realized capacity is required per station")
    paths = validate_rework(rework, len(stations))
    incoming = raw_input
    loads: list[float] = []
    p1 = len(paths) == 1 and (paths[0].entry, paths[0].detection, paths[0].cycles) == (2, 2, 1)
    if paths and not p1:
        raise ValueError("realized flow accepts rework off or P1 only")
    for index, (capacity, station) in enumerate(zip(available_capacity, stations)):
        if p1 and index == 1:
            first = min(incoming, capacity)
            loss = first * (1.0 - station.yield_rate)
            reworked = min(loss, capacity - first)
            loads.append(first + reworked)
            incoming = (first + reworked) * station.yield_rate
        else:
            load = min(incoming, capacity)
            loads.append(load)
            incoming = load * station.yield_rate
    return tuple(loads), incoming


def expected_profit_two_grades(
    raw_input: float,
    demands: tuple[float, float],
    shares: tuple[float, float],
    stations: tuple[Workstation, ...],
    prices: tuple[float, float],
    material_cost: float,
    manufacturing_costs: tuple[float, ...],
    holding_cost_per_day: float,
    storage_days: float,
    policy: int,
    rework: ReworkPath | tuple[ReworkPath, ...] | None = None,
) -> tuple[float, float]:
    """Mean delivered profit over every capacity state, and the probability mass.

    Revenue uses units sold. A state that covers the planned load reproduces
    the planned profit. Rework is off unless the caller passes P1.
    """
    pmfs = [binomial_pmf(station.machine_count, station.availability) for station in stations]
    ranges = [range(station.machine_count + 1) for station in stations]
    expected = 0.0
    mass = 0.0
    for state in product(*ranges):
        probability = 1.0
        available = []
        for index, machines_up in enumerate(state):
            probability *= pmfs[index][machines_up]
            available.append(machines_up * stations[index].machine_capacity)
        loads, finished = realized_series_flow(raw_input, tuple(available), stations, rework)
        grades = (finished * shares[0], finished * shares[1])
        result = profit_from_flow(
            grades,
            loads,
            demands,
            prices,
            material_cost,
            manufacturing_costs,
            holding_cost_per_day,
            storage_days,
            policy,
            revenue_on_delivered=True,
        )
        expected += probability * result.profit
        mass += probability
    return expected, mass
