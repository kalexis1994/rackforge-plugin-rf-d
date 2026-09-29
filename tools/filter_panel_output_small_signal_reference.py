"""50-node conditional AC through the front-panel HI/LO output divider."""

from __future__ import annotations

import json
import math
from pathlib import Path

from filter_emphasis_loop_small_signal_reference import series_return_admittance_s
from filter_ladder_ebers_moll_dc_reference import _solve_linear
from filter_vca_output_small_signal_reference import loaded_output_matrices


EVIDENCE = Path(__file__).resolve().parents[1] / "evidence" / "output_panel_hi_lo.json"
NODE_COUNT = 50
HI = 48
LO = 49


def _panel_parts() -> dict[str, float]:
    data = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    parts = {row["ref"]: row["ohm"] for row in data["resistors"]}
    if (data["source"], parts) != (
            "SVC-9 Fig. 9-17 interconnecting wiring diagram, PDF p. 19 (SVC-204D PDF p. 75)",
            {"R75_BOARD4": 1000, "R57_PANEL": 33000,
             "R58_PANEL": 1000}):
        raise ValueError("panel output graph differs from documentary values")
    return parts


def panel_output_matrices(*, ladder_dc: dict, recovery_dc: dict,
                          cascaded_output_dc: dict,
                          hi_load_ohm: float, lo_load_ohm: float,
                          headphone_input_ohm: float,
                          ) -> tuple[list[list[float]], list[list[float]], float]:
    """Connect C2_RIGHT/R75 to panel HI/LO while SW18 is ON."""
    if not all(math.isfinite(v) and v > 0 for v in
               (hi_load_ohm, lo_load_ohm, headphone_input_ohm)):
        raise ValueError("positive finite HI/LO/headphone loads required")
    old_g, old_c, bus_c = loaded_output_matrices(
        ladder_dc=ladder_dc, recovery_dc=recovery_dc,
        cascaded_output_dc=cascaded_output_dc,
        main_load_ohm=None, headphone_input_ohm=headphone_input_ohm)
    g = [[0.0]*NODE_COUNT for _ in range(NODE_COUNT)]
    c = [[0.0]*NODE_COUNT for _ in range(NODE_COUNT)]
    for row in range(48):
        for col in range(48):
            g[row][col] = old_g[row][col]
            c[row][col] = old_c[row][col]
    r = _panel_parts()

    def stamp(left: int, right: int | None, ohm: float) -> None:
        conductance = 1/ohm
        g[left][left] -= conductance
        if right is not None:
            g[right][right] -= conductance
            g[left][right] += conductance
            g[right][left] += conductance

    stamp(47, HI, r["R75_BOARD4"])
    stamp(HI, LO, r["R57_PANEL"])
    stamp(LO, None, r["R58_PANEL"])
    stamp(HI, None, hi_load_ohm)
    stamp(LO, None, lo_load_ohm)
    return g, c, bus_c


def filter_with_panel_output(*, ladder_dc: dict, recovery_dc: dict,
                             cascaded_output_dc: dict, frequency_hz: float,
                             r14_pin7_to_pin6_ohm: float,
                             r73_bottom_side_to_wiper_ohm: float,
                             hi_load_ohm: float, lo_load_ohm: float,
                             headphone_input_ohm: float,
                             c10_farads: float | None = None) -> dict:
    """BUS=1 V local transfer to panel J4 HI and J5 LO with declared loads."""
    if not math.isfinite(frequency_hz) or frequency_hz < 0:
        raise ValueError("finite nonnegative frequency required")
    if not cascaded_output_dc["input_and_controls_imposed"]:
        raise ValueError("VCA/output DC boundary differs from panel AC model")
    r30_dc = ladder_dc["network_parameters"]["r30"]
    if not math.isclose(r30_dc, 330+r73_bottom_side_to_wiper_ohm,
                        rel_tol=0, abs_tol=1e-8):
        raise ValueError("ladder DC R73 segment differs from panel return")
    y_return = series_return_admittance_s(
        frequency_hz=frequency_hz,
        r14_pin7_to_pin6_ohm=r14_pin7_to_pin6_ohm,
        r73_bottom_side_to_wiper_ohm=r73_bottom_side_to_wiper_ohm,
        c10_farads=c10_farads)
    g, c, bus_c = panel_output_matrices(
        ladder_dc=ladder_dc, recovery_dc=recovery_dc,
        cascaded_output_dc=cascaded_output_dc,
        hi_load_ohm=hi_load_ohm, lo_load_ohm=lo_load_ohm,
        headphone_input_ohm=headphone_input_ohm)
    s = 2j*math.pi*frequency_hz
    system = [[g[i][j]-s*c[i][j] for j in range(NODE_COUNT)]
              for i in range(NODE_COUNT)]
    base, tap = 7, 22
    system[base][base] -= y_return
    system[tap][tap] -= y_return
    system[base][tap] += y_return
    system[tap][base] += y_return
    rhs = [0j]*NODE_COUNT
    rhs[6] = -s*bus_c
    v = _solve_linear(system, rhs)
    residual = max(abs(sum(system[i][j]*v[j] for j in range(NODE_COUNT))
                       - rhs[i]) for i in range(NODE_COUNT))
    return {
        "frequency_hz": frequency_hz,
        "node_v_per_bus_v": tuple(v),
        "c2_right_v_per_bus_v": v[47],
        "j4_hi_v_per_bus_v": v[HI],
        "j5_lo_v_per_bus_v": v[LO],
        "j4_hi_current_a_per_bus_v": v[HI]/hi_load_ohm,
        "j5_lo_current_a_per_bus_v": v[LO]/lo_load_ohm,
        "hi_to_lo_ratio": v[LO]/v[HI] if v[HI] else None,
        "max_linear_kcl_residual_a_per_bus_v": residual,
        "sw18_on_imposed": True,
        "diodes_assumed_open": True,
    }
