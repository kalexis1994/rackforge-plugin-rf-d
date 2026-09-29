"""Exact one-port reduction of board-3 active headphone AC onto board-4 R21."""

from __future__ import annotations

import math

from filter_emphasis_loop_small_signal_reference import series_return_admittance_s
from filter_ladder_ebers_moll_dc_reference import _solve_linear
from filter_panel_headphone_reference import (
    NODE_COUNT, R21_WIPER, panel_with_headphone_matrices)
from headphone_amp_active_ac_reference import conditional_headphone_amp_ac
from headphone_amp_active_dc_reference import _graph


OPEN_LOAD_OHM = 1e12


def coupled_headphone_ac(*, ladder_dc: dict, recovery_dc: dict,
                         cascaded_output_dc: dict, frequency_hz: float,
                         r14_pin7_to_pin6_ohm: float,
                         r73_bottom_side_to_wiper_ohm: float,
                         r20_wiper_to_ground_ohm: float,
                         hi_load_ohm: float, lo_load_ohm: float,
                         r21_wiper_to_ground_ohm: float,
                         transistor_is_a: float,
                         beta_forward: float, beta_reverse: float,
                         temperature_k: float, diode_model: dict,
                         tip_load_ohm: float | None = None,
                         ring_load_ohm: float | None = None,
                         sw18_on: bool = True,
                         c10_farads: float | None = None) -> dict:
    """BUS-normalized local transfer to R21, HI/LO and J7 with active load."""
    if not math.isfinite(frequency_hz) or frequency_hz < 0:
        raise ValueError("finite nonnegative frequency required")
    if not cascaded_output_dc["input_and_controls_imposed"]:
        raise ValueError("VCA/output DC boundary differs from AC model")
    if not math.isclose(ladder_dc["network_parameters"]["r30"],
                        330+r73_bottom_side_to_wiper_ohm,
                        rel_tol=0, abs_tol=1e-8):
        raise ValueError("ladder DC R73 segment differs from AC return")
    cap = {row["ref"]: row["farad"] for row in _graph()["capacitors"]}
    if cap["C19"] != 2.5e-6:
        raise ValueError("C19 differs from board-3 schematic")
    amp = conditional_headphone_amp_ac(
        frequency_hz=frequency_hz,
        transistor_is_a=transistor_is_a,
        beta_forward=beta_forward, beta_reverse=beta_reverse,
        temperature_k=temperature_k, diode_model=diode_model,
        tip_load_ohm=tip_load_ohm, ring_load_ohm=ring_load_ohm)
    s = 2j*math.pi*frequency_hz
    base_per_pin7 = amp["node_v_per_pin7_v"]["Q16_BASE"]
    input_admittance = s*cap["C19"]*(1-base_per_pin7)
    g, c, bus_c = panel_with_headphone_matrices(
        ladder_dc=ladder_dc, recovery_dc=recovery_dc,
        cascaded_output_dc=cascaded_output_dc,
        r20_wiper_to_ground_ohm=r20_wiper_to_ground_ohm,
        hi_load_ohm=hi_load_ohm, lo_load_ohm=lo_load_ohm,
        r21_wiper_to_ground_ohm=r21_wiper_to_ground_ohm,
        headphone_wiper_load_ohm=OPEN_LOAD_OHM,
        sw18_on=sw18_on)
    # The 1 TOhm load only satisfies the older positive-finite API. Remove
    # its stamp, then attach the exact complex driving-point admittance.
    matrix = [[-g[i][j]+s*c[i][j] for j in range(NODE_COUNT)]
              for i in range(NODE_COUNT)]
    matrix[R21_WIPER][R21_WIPER] -= 1/OPEN_LOAD_OHM
    matrix[R21_WIPER][R21_WIPER] += input_admittance
    return_y = series_return_admittance_s(
        frequency_hz=frequency_hz,
        r14_pin7_to_pin6_ohm=r14_pin7_to_pin6_ohm,
        r73_bottom_side_to_wiper_ohm=r73_bottom_side_to_wiper_ohm,
        c10_farads=c10_farads)
    for i in (7, 22):
        matrix[i][i] += return_y
    matrix[7][22] -= return_y
    matrix[22][7] -= return_y
    rhs = [0j]*NODE_COUNT
    rhs[6] = s*bus_c
    voltage = _solve_linear(matrix, rhs)
    residual = max(abs(sum(matrix[i][j]*voltage[j] for j in range(NODE_COUNT))
                       - rhs[i]) for i in range(NODE_COUNT))
    wiper = voltage[R21_WIPER]
    return {"frequency_hz": frequency_hz,
            "r21_wiper_v_per_bus_v": wiper,
            "q16_base_v_per_bus_v": base_per_pin7*wiper,
            "j7_tip_v_per_bus_v": amp["j7_tip_v_per_pin7_v"]*wiper,
            "j7_ring_v_per_bus_v": amp["j7_ring_v_per_pin7_v"]*wiper,
            "j4_hi_v_per_bus_v": voltage[49],
            "j5_lo_v_per_bus_v": voltage[50],
            "c2_right_v_per_bus_v": voltage[47],
            "amp_input_admittance_s": input_admittance,
            "amp_input_current_a_per_bus_v": input_admittance*wiper,
            "max_upstream_kcl_residual_a_per_bus_v": residual,
            "max_amp_kcl_residual_a_per_pin7_v": amp["max_linear_kcl_residual_a_per_pin7_v"],
            "sw18_on_imposed": sw18_on,
            "same_dc_linearization": True}
