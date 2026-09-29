"""Passive-only board-3 C19/R50/R53 input boundary; Q16 base left open."""

from __future__ import annotations

import json
import math
from pathlib import Path

from filter_emphasis_loop_small_signal_reference import series_return_admittance_s
from filter_ladder_ebers_moll_dc_reference import _solve_linear
from filter_panel_headphone_reference import (
    NODE_COUNT as PANEL_NODES, R21_WIPER, panel_with_headphone_matrices)


EVIDENCE = Path(__file__).resolve().parents[1] / "evidence" / "headphone_amp_input_board3.json"
Q16_BASE = 53
NODE_COUNT = 54
OPEN_LOAD_OHM = 1e12


def _input_parts() -> tuple[float, float, float]:
    data = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    values = {row["ref"]: (row["farad"] if "farad" in row else row["ohm"])
              for row in data["components"]}
    if (data["source"] != "SVC-9 Fig. 9-8 board 3 schematic, PDF p. 10 (SVC-204D PDF p. 66)"
            or values != {"C19": 2.5e-6, "R50": 6200, "R53": 24000}):
        raise ValueError("headphone amplifier input differs from schematic")
    return values["C19"], values["R50"], values["R53"]


def passive_input_impedance_ohm(frequency_hz: float) -> complex | None:
    """Impedance at pin 7 with Q16 base open; None at DC."""
    if not math.isfinite(frequency_hz) or frequency_hz < 0:
        raise ValueError("finite nonnegative frequency required")
    c19, r50, r53 = _input_parts()
    if frequency_hz == 0:
        return None
    r_bias = 1/(1/r50+1/r53)
    return r_bias+1/(2j*math.pi*frequency_hz*c19)


def passive_amp_input_matrices(*, ladder_dc: dict, recovery_dc: dict,
                               cascaded_output_dc: dict,
                               r20_wiper_to_ground_ohm: float,
                               hi_load_ohm: float, lo_load_ohm: float,
                               r21_wiper_to_ground_ohm: float,
                               sw18_on: bool = True
                               ) -> tuple[list[list[float]], list[list[float]], float]:
    """Replace imposed R21 wiper load with actual C19 and bias resistors."""
    old_g, old_c, bus_c = panel_with_headphone_matrices(
        ladder_dc=ladder_dc, recovery_dc=recovery_dc,
        cascaded_output_dc=cascaded_output_dc,
        r20_wiper_to_ground_ohm=r20_wiper_to_ground_ohm,
        hi_load_ohm=hi_load_ohm, lo_load_ohm=lo_load_ohm,
        r21_wiper_to_ground_ohm=r21_wiper_to_ground_ohm,
        headphone_wiper_load_ohm=OPEN_LOAD_OHM,
        sw18_on=sw18_on)
    g = [[0.0]*NODE_COUNT for _ in range(NODE_COUNT)]
    c = [[0.0]*NODE_COUNT for _ in range(NODE_COUNT)]
    for i in range(PANEL_NODES):
        for j in range(PANEL_NODES):
            g[i][j] = old_g[i][j]
            c[i][j] = old_c[i][j]
    cap, r50, r53 = _input_parts()
    g[R21_WIPER][R21_WIPER] += 1/OPEN_LOAD_OHM
    g[Q16_BASE][Q16_BASE] -= 1/r50+1/r53
    for i in (R21_WIPER, Q16_BASE):
        c[i][i] += cap
    c[R21_WIPER][Q16_BASE] -= cap
    c[Q16_BASE][R21_WIPER] -= cap
    return g, c, bus_c


def filter_with_passive_headphone_input(*, ladder_dc: dict,
                                        recovery_dc: dict,
                                        cascaded_output_dc: dict,
                                        frequency_hz: float,
                                        r14_pin7_to_pin6_ohm: float,
                                        r73_bottom_side_to_wiper_ohm: float,
                                        r20_wiper_to_ground_ohm: float,
                                        hi_load_ohm: float,
                                        lo_load_ohm: float,
                                        r21_wiper_to_ground_ohm: float,
                                        sw18_on: bool = True,
                                        c10_farads: float | None = None) -> dict:
    """BUS-normalized AC through C19, stopping at unloaded Q16 base."""
    if not math.isfinite(frequency_hz) or frequency_hz < 0:
        raise ValueError("finite nonnegative frequency required")
    if not cascaded_output_dc["input_and_controls_imposed"]:
        raise ValueError("VCA/output DC boundary differs from AC model")
    if not math.isclose(ladder_dc["network_parameters"]["r30"],
                        330+r73_bottom_side_to_wiper_ohm,
                        rel_tol=0, abs_tol=1e-8):
        raise ValueError("ladder DC R73 segment differs from AC return")
    y_return = series_return_admittance_s(
        frequency_hz=frequency_hz,
        r14_pin7_to_pin6_ohm=r14_pin7_to_pin6_ohm,
        r73_bottom_side_to_wiper_ohm=r73_bottom_side_to_wiper_ohm,
        c10_farads=c10_farads)
    g, c, bus_c = passive_amp_input_matrices(
        ladder_dc=ladder_dc, recovery_dc=recovery_dc,
        cascaded_output_dc=cascaded_output_dc,
        r20_wiper_to_ground_ohm=r20_wiper_to_ground_ohm,
        hi_load_ohm=hi_load_ohm, lo_load_ohm=lo_load_ohm,
        r21_wiper_to_ground_ohm=r21_wiper_to_ground_ohm,
        sw18_on=sw18_on)
    s = 2j*math.pi*frequency_hz
    matrix = [[g[i][j]-s*c[i][j] for j in range(NODE_COUNT)]
              for i in range(NODE_COUNT)]
    for i in (7, 22):
        matrix[i][i] -= y_return
    matrix[7][22] += y_return
    matrix[22][7] += y_return
    rhs = [0j]*NODE_COUNT
    rhs[6] = -s*bus_c
    v = _solve_linear(matrix, rhs)
    residual = max(abs(sum(matrix[i][j]*v[j] for j in range(NODE_COUNT))
                       - rhs[i]) for i in range(NODE_COUNT))
    return {"frequency_hz": frequency_hz,
            "node_v_per_bus_v": tuple(v),
            "r21_wiper_v_per_bus_v": v[R21_WIPER],
            "q16_base_v_per_bus_v": v[Q16_BASE],
            "j4_hi_v_per_bus_v": v[49], "j5_lo_v_per_bus_v": v[50],
            "max_linear_kcl_residual_a_per_bus_v": residual,
            "sw18_on_imposed": sw18_on,
            "q16_base_current_assumed_zero": True}
