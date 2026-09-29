"""53-node AC and exact resistive R21 reduction at board-4 pin 22."""

from __future__ import annotations

import json
import math
from pathlib import Path

from filter_emphasis_loop_small_signal_reference import series_return_admittance_s
from filter_ladder_ebers_moll_dc_reference import _solve_linear
from filter_panel_output_small_signal_reference import (
    NODE_COUNT as MAIN_COUNT, _panel_parts, panel_output_matrices)
from filter_panel_output_transient_reference import nonlinear_panel_output_step
from filter_vca_output_transient_reference import nonlinear_output_step
from vca_output_conversion_dc_reference import _parts as board_parts


EVIDENCE = Path(__file__).resolve().parents[1] / "evidence" / "output_panel_headphone_r21.json"
PIN22 = 51
R21_WIPER = 52
NODE_COUNT = 53


def _headphone_parts() -> dict[str, float]:
    data = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    values = {row["ref"]: row["ohm"] for row in data["resistors"]}
    if (data["source"] != "SVC-9 Fig. 9-17 interconnecting wiring diagram, PDF p. 19 (SVC-204D PDF p. 75)"
            or values != {"R77_BOARD4": 1000, "R21_PANEL": 5000}
            or board_parts()["R77"] != values["R77_BOARD4"]):
        raise ValueError("headphone panel graph differs from documentary values")
    return values


def headphone_load_reduction(*, r21_wiper_to_ground_ohm: float,
                             headphone_wiper_load_ohm: float) -> dict[str, float]:
    """Exact load after R77, with an imposed finite load at R21 wiper."""
    r = _headphone_parts()
    if (not math.isfinite(r21_wiper_to_ground_ohm)
            or not 0 < r21_wiper_to_ground_ohm < r["R21_PANEL"]
            or not math.isfinite(headphone_wiper_load_ohm)
            or headphone_wiper_load_ohm <= 0):
        raise ValueError("interior R21 position and positive finite load required")
    lower_shunt = 1/(1/r21_wiper_to_ground_ohm
                     + 1/headphone_wiper_load_ohm)
    upper = r["R21_PANEL"]-r21_wiper_to_ground_ohm
    return {"r21_lower_shunt_ohm": lower_shunt,
            "r21_upper_ohm": upper,
            "equivalent_headphone_input_ohm": upper+lower_shunt,
            "wiper_to_pin22_ratio": lower_shunt/(upper+lower_shunt)}


def panel_with_headphone_matrices(*, ladder_dc: dict, recovery_dc: dict,
                                  cascaded_output_dc: dict,
                                  r20_wiper_to_ground_ohm: float,
                                  hi_load_ohm: float, lo_load_ohm: float,
                                  r21_wiper_to_ground_ohm: float,
                                  headphone_wiper_load_ohm: float,
                                  sw18_on: bool = True
                                  ) -> tuple[list[list[float]], list[list[float]], float]:
    """Expand the 51-node HI/LO graph with pin 22 and R21 wiper."""
    hp = headphone_load_reduction(
        r21_wiper_to_ground_ohm=r21_wiper_to_ground_ohm,
        headphone_wiper_load_ohm=headphone_wiper_load_ohm)
    old_g, old_c, bus_c = panel_output_matrices(
        ladder_dc=ladder_dc, recovery_dc=recovery_dc,
        cascaded_output_dc=cascaded_output_dc,
        r20_wiper_to_ground_ohm=r20_wiper_to_ground_ohm,
        hi_load_ohm=hi_load_ohm, lo_load_ohm=lo_load_ohm,
        headphone_input_ohm=hp["equivalent_headphone_input_ohm"])
    g = [[0.0]*NODE_COUNT for _ in range(NODE_COUNT)]
    c = [[0.0]*NODE_COUNT for _ in range(NODE_COUNT)]
    for i in range(MAIN_COUNT):
        for j in range(MAIN_COUNT):
            g[i][j] = old_g[i][j]
            c[i][j] = old_c[i][j]
    if not isinstance(sw18_on, bool):
        raise ValueError("explicit SW18 state required")
    if not sw18_on:
        upper = _panel_parts()["R20_PANEL"]-r20_wiper_to_ground_ohm
        lower = r20_wiper_to_ground_ohm
        # Remove ON branches pin21--HI and HI--ground. The OFF contacts
        # ground the R20 wiper, leaving its upper segment at pin 21.
        g[48][49] -= 1/upper
        g[49][48] -= 1/upper
        g[49][49] += 1/upper+1/lower
    r = _headphone_parts()
    g[47][47] += 1/(r["R77_BOARD4"]+hp["equivalent_headphone_input_ohm"])

    def stamp(left: int, right: int | None, ohm: float) -> None:
        y = 1/ohm
        g[left][left] -= y
        if right is not None:
            g[right][right] -= y
            g[left][right] += y
            g[right][left] += y

    stamp(47, PIN22, r["R77_BOARD4"])
    stamp(PIN22, R21_WIPER, hp["r21_upper_ohm"])
    stamp(R21_WIPER, None, r21_wiper_to_ground_ohm)
    stamp(R21_WIPER, None, headphone_wiper_load_ohm)
    return g, c, bus_c


def filter_with_panel_and_headphone(*, ladder_dc: dict, recovery_dc: dict,
                                    cascaded_output_dc: dict,
                                    frequency_hz: float,
                                    r14_pin7_to_pin6_ohm: float,
                                    r73_bottom_side_to_wiper_ohm: float,
                                    r20_wiper_to_ground_ohm: float,
                                    hi_load_ohm: float, lo_load_ohm: float,
                                    r21_wiper_to_ground_ohm: float,
                                    headphone_wiper_load_ohm: float,
                                    sw18_on: bool = True,
                                    c10_farads: float | None = None) -> dict:
    """Local BUS-normalized transfer to HI, LO and R21 wiper."""
    if not math.isfinite(frequency_hz) or frequency_hz < 0:
        raise ValueError("finite nonnegative frequency required")
    if not cascaded_output_dc["input_and_controls_imposed"]:
        raise ValueError("VCA/output DC boundary differs from panel AC model")
    if not math.isclose(ladder_dc["network_parameters"]["r30"],
                        330+r73_bottom_side_to_wiper_ohm,
                        rel_tol=0, abs_tol=1e-8):
        raise ValueError("ladder DC R73 segment differs from AC return")
    y_return = series_return_admittance_s(
        frequency_hz=frequency_hz,
        r14_pin7_to_pin6_ohm=r14_pin7_to_pin6_ohm,
        r73_bottom_side_to_wiper_ohm=r73_bottom_side_to_wiper_ohm,
        c10_farads=c10_farads)
    g, c, bus_c = panel_with_headphone_matrices(
        ladder_dc=ladder_dc, recovery_dc=recovery_dc,
        cascaded_output_dc=cascaded_output_dc,
        r20_wiper_to_ground_ohm=r20_wiper_to_ground_ohm,
        hi_load_ohm=hi_load_ohm, lo_load_ohm=lo_load_ohm,
        r21_wiper_to_ground_ohm=r21_wiper_to_ground_ohm,
        headphone_wiper_load_ohm=headphone_wiper_load_ohm,
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
    return {"node_v_per_bus_v": tuple(v),
            "c2_right_v_per_bus_v": v[47],
            "j4_hi_v_per_bus_v": v[49],
            "j5_lo_v_per_bus_v": v[50],
            "board4_pin22_v_per_bus_v": v[PIN22],
            "r21_wiper_v_per_bus_v": v[R21_WIPER],
            "max_linear_kcl_residual_a_per_bus_v": residual,
            "diodes_assumed_open": cascaded_output_dc["diodes_assumed_open"],
            "sw18_on_imposed": sw18_on,
            "downstream_headphone_stage_imposed_load": True}


def nonlinear_panel_headphone_step(*, r21_wiper_to_ground_ohm: float,
                                   headphone_wiper_load_ohm: float,
                                   sw18_on: bool = True,
                                   **panel_step_parameters) -> dict:
    """Reduce R21 exactly, take one nonlinear step, reconstruct its nodes."""
    if "headphone_input_ohm" in panel_step_parameters:
        raise ValueError("headphone input load is derived from R21")
    hp = headphone_load_reduction(
        r21_wiper_to_ground_ohm=r21_wiper_to_ground_ohm,
        headphone_wiper_load_ohm=headphone_wiper_load_ohm)
    if not isinstance(sw18_on, bool):
        raise ValueError("explicit SW18 state required")
    if sw18_on:
        out = nonlinear_panel_output_step(
            headphone_input_ohm=hp["equivalent_headphone_input_ohm"],
            **panel_step_parameters)
    else:
        if "main_load_ohm" in panel_step_parameters:
            raise ValueError("main load is derived from R20 in OFF")
        r20_lower = panel_step_parameters.pop("r20_wiper_to_ground_ohm")
        hi_load = panel_step_parameters.pop("hi_load_ohm")
        lo_load = panel_step_parameters.pop("lo_load_ohm")
        if not all(math.isfinite(v) and v > 0 for v in (hi_load, lo_load)):
            raise ValueError("positive finite HI/LO jack loads required")
        panel_r = _panel_parts()
        if not math.isfinite(r20_lower) or not 0 < r20_lower < panel_r["R20_PANEL"]:
            raise ValueError("interior R20 wiper position required")
        upper = panel_r["R20_PANEL"]-r20_lower
        core = nonlinear_output_step(
            main_load_ohm=upper,
            headphone_input_ohm=hp["equivalent_headphone_input_ohm"],
            **panel_step_parameters)
        out = {**core, "board4_pin21_v": core["main_pin21_v"],
               "j4_hi_v": 0.0, "j5_lo_v": 0.0,
               "j4_hi_external_current_a": 0.0,
               "j5_lo_external_current_a": 0.0,
               "r57_current_a": 0.0, "r58_current_a": 0.0,
               "r20_upper_current_a": core["main_pin21_v"]/upper,
               "r20_lower_current_a": 0.0,
               "sw18_on_imposed": False}
    pin22 = out["headphone_pin22_v"]
    wiper = pin22*hp["wiper_to_pin22_ratio"]
    return {**out,
            "board4_pin22_v": pin22,
            "r21_wiper_v": wiper,
            "r21_upper_current_a": (pin22-wiper)/hp["r21_upper_ohm"],
            "r21_lower_current_a": wiper/r21_wiper_to_ground_ohm,
            "headphone_wiper_load_current_a": wiper/headphone_wiper_load_ohm,
            "headphone_reduction": hp,
            "sw18_on_imposed": sw18_on,
            "downstream_headphone_stage_imposed_load": True}
