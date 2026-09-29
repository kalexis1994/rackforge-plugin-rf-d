"""Isolated board-3 headphone AC transfer linearized at the matching DC point."""

from __future__ import annotations

import math

from filter_ladder_ebers_moll_dc_reference import _solve_linear
from headphone_amp_active_dc_reference import (
    NODES, _graph, conditional_headphone_amp_dc, evaluate_headphone_amp_dc)
from headphone_output_coupling_reference import _shunt_conductance_s


J7 = len(NODES)
AC_NODES = NODES+("J7_TIP_RING",)


def conditional_headphone_amp_ac(*, frequency_hz: float,
                                 transistor_is_a: float,
                                 beta_forward: float,
                                 beta_reverse: float,
                                 temperature_k: float,
                                 diode_model: dict,
                                 tip_load_ohm: float | None = None,
                                 ring_load_ohm: float | None = None) -> dict:
    """1 V at board-3 pin 7; Jacobian from exactly the requested DC scenario."""
    if not math.isfinite(frequency_hz) or frequency_hz < 0:
        raise ValueError("finite nonnegative frequency required")
    caps = {row["ref"]: row["farad"] for row in _graph()["capacitors"]}
    if caps != {"C19": 2.5e-6, "C15": 220e-12, "C21": 400e-6}:
        raise ValueError("headphone AC capacitors differ from schematic")
    parameters = dict(transistor_is_a=transistor_is_a,
                      beta_forward=beta_forward,
                      beta_reverse=beta_reverse,
                      temperature_k=temperature_k, diode_model=diode_model)
    dc = conditional_headphone_amp_dc(**parameters)
    bias = [dc["node_v"][name] for name in NODES]
    count = len(AC_NODES)
    matrix = [[0j]*count for _ in range(count)]
    derivative_step_v = 1e-5
    for column in range(len(NODES)):
        plus, minus = bias.copy(), bias.copy()
        plus[column] += derivative_step_v
        minus[column] -= derivative_step_v
        higher, _ = evaluate_headphone_amp_dc(plus, **parameters)
        lower, _ = evaluate_headphone_amp_dc(minus, **parameters)
        for row in range(len(NODES)):
            matrix[row][column] = (higher[row]-lower[row])/(2*derivative_step_v)
    index = {name: i for i, name in enumerate(AC_NODES)}
    s = 2j*math.pi*frequency_hz

    def capacitor(left: str, right: str, farad: float) -> None:
        i, j = index[left], index[right]
        y = s*farad
        matrix[i][i] += y
        matrix[j][j] += y
        matrix[i][j] -= y
        matrix[j][i] -= y

    capacitor("Q10_BASE", "Q10_COLLECTOR", caps["C15"])
    capacitor("AMP_OUTPUT_BEFORE_C21", "J7_TIP_RING", caps["C21"])
    matrix[J7][J7] += _shunt_conductance_s(tip_load_ohm, ring_load_ohm)
    rhs = [0j]*count
    # C19 joins imposed 1 V board-3 pin 7 to the Q16 base.
    base = index["Q16_BASE"]
    matrix[base][base] += s*caps["C19"]
    rhs[base] = s*caps["C19"]
    voltage = _solve_linear(matrix, rhs)
    residual = max(abs(sum(matrix[i][j]*voltage[j] for j in range(count))
                       - rhs[i]) for i in range(count))
    return {"frequency_hz": frequency_hz,
            "node_v_per_pin7_v": dict(zip(AC_NODES, voltage)),
            "pre_c21_v_per_pin7_v": voltage[index["AMP_OUTPUT_BEFORE_C21"]],
            "j7_tip_v_per_pin7_v": voltage[J7],
            "j7_ring_v_per_pin7_v": voltage[J7],
            "max_linear_kcl_residual_a_per_pin7_v": residual,
            "dc_max_kcl_residual_a": dc["max_kcl_residual_a"],
            "dc_output_v": dc["node_v"]["AMP_OUTPUT_BEFORE_C21"],
            "linearized_at_same_dc_parameters": True,
            "jacobian_voltage_step_v": derivative_step_v,
            "central_difference_jacobian": True}
