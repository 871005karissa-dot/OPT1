"""Jumper-cable line from the rework case.

Yield and availability follow that table's column names. The manuscript uses
different symbols for the same two ideas. Grades come from the stated insertion
loss, mean 0.32 dB and standard deviation 0.04 dB, tolerances [0, 0.3] and
[0, 0.35]. The case states no order quantity.
"""

from backbone.evaluator import KQC, Workstation, component_probabilities, grade_shares

STATIONS = (
    Workstation("v1", machine_count=3, machine_capacity=160.0, yield_rate=0.9997, availability=0.9896),
    Workstation("v2", machine_count=4, machine_capacity=115.0, yield_rate=0.9753, availability=0.9725),
    Workstation("v3", machine_count=3, machine_capacity=120.0, yield_rate=0.9982, availability=0.9862),
    Workstation("v4", machine_count=4, machine_capacity=125.0, yield_rate=0.9945, availability=0.9723),
    Workstation("v5", machine_count=5, machine_capacity=85.0, yield_rate=0.9218, availability=0.9769),
    Workstation("v6", machine_count=3, machine_capacity=135.0, yield_rate=0.7733, availability=0.9831),
)

PUBLISHED_PMF = {
    "v1": (0.0000, 0.0003, 0.0306, 0.9691),
    "v2": (0.0000, 0.0001, 0.0043, 0.1012, 0.8945),
    "v3": (0.0000, 0.0006, 0.0403, 0.9592),
    "v4": (0.0000, 0.0001, 0.0044, 0.1018, 0.8937),
    "v5": (0.0000, 0.0000, 0.0001, 0.0050, 0.1052, 0.8897),
    "v6": (0.0000, 0.0008, 0.0490, 0.9502),
}

INSERTION_LOSS = (
    KQC("insertion loss", 0.32, 0.04, ((0.0, 0.3), (0.0, 0.35))),
)

SHARES = grade_shares(component_probabilities(INSERTION_LOSS))
SCRAP_RATE = 1.0 - sum(SHARES)
