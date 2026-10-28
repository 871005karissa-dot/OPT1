"""Ball-screw case data read from the manuscript tables.

Table 2 supplies station yield, machine capacity, availability, and the
published binomial probabilities. The machine count is the number of positive
capacity steps in that table. Table 3 supplies the four KQCs.
"""

from backbone.evaluator import KQC, Workstation, line_yield

DEMAND = (550.0, 350.0)

# Manuscript targets for D = (550, 350): input, lower capacity vector, reliability.
POLICY_I_TARGET = {
    "input": 1615.1585,
    "workloads": (1615.1585, 1534.4006, 1488.3686, 1399.0665, 1343.1038),
    "lcv": (1800.0, 1750.0, 1500.0, 1575.0, 1500.0),
    "reliability": 0.6036,
}
POLICY_II_TARGET = {
    "input": 1266.6672,
    "workloads": (1266.6672, 1203.3338, 1167.2338, 1097.1998, 1053.3118),
    "lcv": (1500.0, 1400.0, 1250.0, 1125.0, 1200.0),
    "reliability": 0.9486,
}

# Appendix D prints these eight component probabilities, then Q1 = 0.6251
# and Q2 = 0.8994 - 0.6251 = 0.2743.
APPENDIX_COMPONENT_PROBABILITIES = (
    (0.8413, 0.9999),
    (0.9195, 0.9647),
    (0.9332, 0.9772),
    (0.8659, 0.9542),
)
APPENDIX_SHARES = (0.6251, 0.2743)

STATIONS = (
    Workstation("e1", machine_count=7, machine_capacity=300.0, yield_rate=0.95, availability=0.91),
    Workstation("e2", machine_count=6, machine_capacity=350.0, yield_rate=0.97, availability=0.92),
    Workstation("e3", machine_count=7, machine_capacity=250.0, yield_rate=0.94, availability=0.91),
    Workstation("e4", machine_count=8, machine_capacity=225.0, yield_rate=0.96, availability=0.93),
    Workstation("e5", machine_count=6, machine_capacity=300.0, yield_rate=0.95, availability=0.94),
)

# Table 2 probabilities, rounded to four decimals, in capacity order.
PUBLISHED_PMF = {
    "e1": (0.0000, 0.0000, 0.0001, 0.0017, 0.0175, 0.1061, 0.3578, 0.5168),
    "e2": (0.0000, 0.0000, 0.0005, 0.0080, 0.0688, 0.3164, 0.6064),
    "e3": (0.0000, 0.0000, 0.0001, 0.0017, 0.0175, 0.1061, 0.3578, 0.5168),
    "e4": (0.0000, 0.0000, 0.0000, 0.0001, 0.0013, 0.0134, 0.0888, 0.3370, 0.5596),
    "e5": (0.0000, 0.0000, 0.0002, 0.0036, 0.0422, 0.2642, 0.6899),
}

# Section 6 prices and unit costs, USD.
PRICES = (120.0, 60.0)
MATERIAL_COST = 20.7
MANUFACTURING_COSTS = (3.8, 5.5, 5.8, 7.6, 12.4)
HOLDING_COST_PER_DAY = 1.0
STORAGE_DAYS = 30.0

# Shares implied by D = (550, 350), I = 1615.1585, and excess (247.6121, 0).
# Tables 4 and 5 use this pair. It is not the normal-formula pair.
_ANCHOR_OUTPUT = (550.0 + 247.6121, 350.0)
_ANCHOR_SCALE = 1615.1585 * line_yield(STATIONS)
MANUSCRIPT_SHARES = tuple(value / _ANCHOR_SCALE for value in _ANCHOR_OUTPUT)

KQCS = (
    KQC("surface roughness", 0.0007, 0.0001, ((0.0, 0.0008), (0.0, 0.0009))),
    KQC("center hole diameter", 36.124, 0.052, ((36.0, 36.2), (35.98, 36.22))),
    KQC("external diameter", 26.86, 0.04, ((26.8, 27.05), (26.78, 27.06))),
    KQC("screw diameter", 40.481, 0.020, ((40.45, 40.51), (40.44, 40.52))),
)
