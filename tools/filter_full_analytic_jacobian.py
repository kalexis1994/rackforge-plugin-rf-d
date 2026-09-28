"""Exact local Jacobian of the conditional 24-node BJT circuit.

KCL uses incoming-minus-outgoing current. The capacitor companion and C10
series return are added for a backward Euler step. This is still offline
Python preparation, not a real-time audio implementation.
"""

from __future__ import annotations

import math

from filter_ladder_ebers_moll_dc_reference import DEVICE_NODES


RECOVERY_DEVICE_NODES = {
    "Q8": (16, 21, 18), "Q6": (17, None, 19),
    "Q7": (18, 21, 20), "Q5": (19, None, 20),
}


def analytic_dc_jacobian(*, node_v: list[float] | tuple[float, ...],
                         ladder_parameters: dict,
                         recovery_parameters: dict) -> list[list[float]]:
    """Derivatives d(KCL_A)/d(V), in siemens, of all 24 DC rows."""
    if len(node_v) != 24 or not all(math.isfinite(value) for value in node_v):
        raise ValueError("finite 24-node voltage required")
    j = [[0.0] * 24 for _ in range(24)]

    def resistor(left: int, right: int | None, ohm: float) -> None:
        g = 1 / ohm
        j[left][left] -= g
        if right is not None:
            j[left][right] += g
            j[right][right] -= g
            j[right][left] += g

    def transistor(base: int, collector: int | None, emitter: int,
                   collector_v: float, is_a: float, bf: float, br: float,
                   vt: float) -> None:
        be = (node_v[base] - node_v[emitter]) / vt
        bc = (node_v[base] - collector_v) / vt
        if max(be, bc) > 45:
            raise ValueError("trial voltage outside finite BJT exponential domain")
        gf = is_a * math.exp(be) / vt
        gr = is_a * math.exp(bc) / vt
        # Each row has a signed coefficient for the forward and reverse
        # junction currents. Their terminal derivatives are stamped once.
        branches = ((base, -1 / bf, -1 / br),
                    (collector, -1, 1 + 1 / br),
                    (emitter, 1 + 1 / bf, -1))
        for row, forward_coeff, reverse_coeff in branches:
            if row is None:
                continue
            j[row][base] += forward_coeff * gf + reverse_coeff * gr
            j[row][emitter] -= forward_coeff * gf
            if collector is not None:
                j[row][collector] -= reverse_coeff * gr

    lp = ladder_parameters
    spine = lp["spine_resistances"]
    resistor(0, None, spine[0])
    for index in range(4):
        resistor(index, index + 1, spine[index + 1])
    resistor(4, None, lp["r61_ohm"])
    resistor(4, 6, lp["r54"])
    resistor(4, 7, lp["r30"])
    for name, (base, collector, emitter) in DEVICE_NODES.items():
        transistor(base, collector, emitter,
                   lp["plus"] if collector is None else node_v[collector],
                   lp["values_is"][name], lp["values_bf"][name],
                   lp["reverse_beta"][name], lp["vt"])

    rp = recovery_parameters
    r = rp["resistance"]
    for left, right, name in ((16, None, "R31"), (17, None, "R38"),
                              (18, None, "R24"), (19, None, "R20"),
                              (20, None, "R26"), (22, 21, "R3"),
                              (23, 22, "R7"), (23, None, "R6")):
        resistor(left, right, r[name])
    for name, (base, collector, emitter) in RECOVERY_DEVICE_NODES.items():
        transistor(base, collector, emitter,
                   rp["plus"] if collector is None else node_v[collector],
                   rp["is_a"][name], rp["beta_forward"][name],
                   rp["beta_reverse"][name], rp["vt"])
    return j


def analytic_step_jacobian(*, node_v: list[float] | tuple[float, ...],
                           ladder_parameters: dict,
                           recovery_parameters: dict,
                           capacitance_matrix_f: list[list[float]],
                           dt_s: float, c10_farads: float,
                           return_series_ohm: float) -> list[list[float]]:
    """Exact Newton matrix for the backward Euler residual, in siemens."""
    if (not math.isfinite(dt_s) or dt_s <= 0
            or not math.isfinite(c10_farads) or c10_farads <= 0
            or not math.isfinite(return_series_ohm) or return_series_ohm < 0
            or len(capacitance_matrix_f) != 24
            or any(len(row) != 24 for row in capacitance_matrix_f)):
        raise ValueError("valid step, capacitance matrix and return path required")
    j = analytic_dc_jacobian(
        node_v=node_v, ladder_parameters=ladder_parameters,
        recovery_parameters=recovery_parameters)
    for row in range(24):
        for column in range(24):
            j[row][column] -= capacitance_matrix_f[row][column] / dt_s
    gc = c10_farads / dt_s
    y = gc / (1 + gc * return_series_ohm)
    base, tap = 7, 22
    j[base][base] -= y
    j[tap][tap] -= y
    j[base][tap] += y
    j[tap][base] += y
    return j
