"""48-node conditional AC through board-4 output coupling and finite loads."""

from __future__ import annotations

import json
import math

from filter_emphasis_loop_small_signal_reference import series_return_admittance_s
from filter_ladder_ebers_moll_dc_reference import _solve_linear
from filter_vca1_loaded_small_signal_reference import loaded_matrices
from vca1_input_boundary_reference import _values as vca_values
from vca_cascaded_output_dc_reference import NODES as VCA_OUTPUT_NODES
from vca_output_conversion_dc_reference import EVIDENCE, _parts as output_parts


NODE_COUNT = 48
LOCAL_TO_SYSTEM = (25, 26, 27, 28, 29, 30, 31, 32, 33,
                   34, 35, 36, 37, 38, 39, 40, 41, 42, 43,
                   44, 45, 46)
C2_RIGHT = 47


def _capacitors() -> dict[str, float]:
    data = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    values = {row["ref"]: row["farad"] for row in data["capacitors"]}
    if values != {"C4": 220e-6, "C2": 10e-6}:
        raise ValueError("output capacitors differ from documentary graph")
    return values


def loaded_output_matrices(*, ladder_dc: dict, recovery_dc: dict,
                           cascaded_output_dc: dict,
                           main_load_ohm: float | None,
                           headphone_input_ohm: float,
                           ) -> tuple[list[list[float]], list[list[float]], float]:
    """Stamp full local Jacobian, C4, C2 and two declared output loads."""
    if (not math.isfinite(headphone_input_ohm)
            or headphone_input_ohm <= 0
            or (main_load_ohm is not None and
                (not math.isfinite(main_load_ohm) or main_load_ohm <= 0))):
        raise ValueError("positive finite output terminations required")
    old_g, old_c, bus_c = loaded_matrices(
        ladder_dc=ladder_dc, recovery_dc=recovery_dc)
    g = [[0.0] * NODE_COUNT for _ in range(NODE_COUNT)]
    c = [[0.0] * NODE_COUNT for _ in range(NODE_COUNT)]
    for row in range(27):
        for col in range(27):
            g[row][col] = old_g[row][col]
            c[row][col] = old_c[row][col]
    _, _, r34, _, r36 = vca_values()
    g[25][25] += 1/r34
    g[26][26] += 1/r34 + 1/r36
    g[25][26] -= 1/r34
    g[26][25] -= 1/r34
    local = cascaded_output_dc["conductance_matrix_s"]
    if len(local) != len(VCA_OUTPUT_NODES) or any(
            len(row) != len(VCA_OUTPUT_NODES) for row in local):
        raise ValueError("VCA/output Jacobian must have 22 rows and columns")
    for row, system_row in enumerate(LOCAL_TO_SYSTEM):
        for col, system_col in enumerate(LOCAL_TO_SYSTEM):
            g[system_row][system_col] += local[row][col]
    capacitors = _capacitors()
    c[40][40] += capacitors["C4"]  # Q1 base to ideal +10 AC ground.
    q17c = 46
    c[q17c][q17c] += capacitors["C2"]
    c[C2_RIGHT][C2_RIGHT] += capacitors["C2"]
    c[q17c][C2_RIGHT] -= capacitors["C2"]
    c[C2_RIGHT][q17c] -= capacitors["C2"]
    r = output_parts()
    g[C2_RIGHT][C2_RIGHT] -= 1/(r["R77"] + headphone_input_ohm)
    if main_load_ohm is not None:
        g[C2_RIGHT][C2_RIGHT] -= 1/(r["R75"] + main_load_ohm)
    return g, c, bus_c


def filter_with_output(*, ladder_dc: dict, recovery_dc: dict,
                       cascaded_output_dc: dict, frequency_hz: float,
                       r14_pin7_to_pin6_ohm: float,
                       r73_bottom_side_to_wiper_ohm: float,
                       main_load_ohm: float,
                       headphone_input_ohm: float,
                       c10_farads: float | None = None) -> dict:
    """BUS=1 V phasor response to board-4 output and both loaded pins."""
    if not math.isfinite(frequency_hz) or frequency_hz < 0:
        raise ValueError("finite nonnegative frequency required")
    if not cascaded_output_dc["input_and_controls_imposed"]:
        raise ValueError("VCA/output DC boundary differs from AC model")
    r30_dc = ladder_dc["network_parameters"]["r30"]
    if not math.isclose(r30_dc, 330 + r73_bottom_side_to_wiper_ohm,
                        rel_tol=0, abs_tol=1e-8):
        raise ValueError("ladder DC R73 segment differs from AC return")
    y_return = series_return_admittance_s(
        frequency_hz=frequency_hz,
        r14_pin7_to_pin6_ohm=r14_pin7_to_pin6_ohm,
        r73_bottom_side_to_wiper_ohm=r73_bottom_side_to_wiper_ohm,
        c10_farads=c10_farads)
    g, c, bus_c = loaded_output_matrices(
        ladder_dc=ladder_dc, recovery_dc=recovery_dc,
        cascaded_output_dc=cascaded_output_dc,
        main_load_ohm=main_load_ohm,
        headphone_input_ohm=headphone_input_ohm)
    s = 2j * math.pi * frequency_hz
    system = [[g[i][j] - s*c[i][j] for j in range(NODE_COUNT)]
              for i in range(NODE_COUNT)]
    base, tap = 7, 22
    system[base][base] -= y_return
    system[tap][tap] -= y_return
    system[base][tap] += y_return
    system[tap][base] += y_return
    rhs = [0j] * NODE_COUNT
    rhs[6] = -s * bus_c
    v = _solve_linear(system, rhs)
    residual = max(abs(sum(system[i][j]*v[j] for j in range(NODE_COUNT))
                       - rhs[i]) for i in range(NODE_COUNT))
    r = output_parts()
    return {
        "frequency_hz": frequency_hz,
        "node_v_per_bus_v": tuple(v),
        "vca_output_node_v_per_bus_v": dict(zip(
            VCA_OUTPUT_NODES, (v[i] for i in LOCAL_TO_SYSTEM))),
        "q17_collector_v_per_bus_v": v[46],
        "c2_right_v_per_bus_v": v[C2_RIGHT],
        "main_pin21_v_per_bus_v": (v[C2_RIGHT]*main_load_ohm
                                    /(r["R75"]+main_load_ohm)),
        "headphone_pin22_v_per_bus_v": (v[C2_RIGHT]*headphone_input_ohm
                                         /(r["R77"]+headphone_input_ohm)),
        "main_pin21_current_a_per_bus_v": (v[C2_RIGHT]
                                            /(r["R75"]+main_load_ohm)),
        "headphone_pin22_current_a_per_bus_v": (v[C2_RIGHT]
                                                 /(r["R77"]+headphone_input_ohm)),
        "max_linear_kcl_residual_a_per_bus_v": residual,
        "diodes_assumed_open": cascaded_output_dc["diodes_assumed_open"],
        "plus_rail_and_controls_ac_ground_imposed": True,
    }
