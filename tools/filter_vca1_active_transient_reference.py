"""Offline 33-node nonlinear transient through Q16/Q15/Q18 first VCA.

All 17 BJTs in the ladder, recovery and first VCA are reevaluated per step.
The balance wiper and loudness voltage are fixed ideal boundaries. The
second VCA remains an unloaded output. This implementation is not DSP.
"""

from __future__ import annotations

import math

from filter_full_nonlinear_transient_reference import initial_state
from filter_ladder_ebers_moll_dc_reference import _solve_linear, evaluate_nodal_kcl
from filter_recovery_active_dc_reference import _evaluate as recovery_kcl
from filter_regeneration_reference import _values as regeneration_values
from filter_vca1_active_small_signal_reference import NODE_COUNT, VCA_TO_SYSTEM, active_loaded_matrices
from vca1_active_core_dc_reference import _evaluate as vca_kcl
from vca1_input_boundary_reference import _values as vca_values


def initial_active_state(*, ladder_dc: dict, recovery_dc: dict,
                         vca_dc: dict) -> dict:
    """DC state; C6_LEFT follows recovery, while Q16/Q15 retain VCA bias."""
    core = initial_state(ladder_dc=ladder_dc, recovery_dc=recovery_dc)
    vca = tuple(vca_dc["nodes_v"].values())
    if len(vca) != 8:
        raise ValueError("eight first-VCA DC voltages required")
    x = (core["node_v"] + (core["node_v"][21], vca[0], vca[1])
         + vca[2:])
    return {"node_v": x, "c10_capacitor_v": core["c10_capacitor_v"],
            "bus_v": 0.0}


def nonlinear_active_step(*, ladder_dc: dict, recovery_dc: dict,
                          vca_dc: dict, previous_node_v: tuple[float, ...],
                          previous_c10_capacitor_v: float,
                          previous_bus_v: float, bus_v: float,
                          dt_s: float, r14_pin7_to_pin6_ohm: float,
                          r73_bottom_side_to_wiper_ohm: float,
                          c10_farads: float | None = None) -> dict:
    """One backward-Euler step; finite-difference Newton is offline only."""
    c10_nominal, r14_total, r73_total, r76 = regeneration_values()
    c10 = c10_nominal if c10_farads is None else c10_farads
    r2, _, _, _, _ = vca_values()
    if (len(previous_node_v) != NODE_COUNT
            or not all(math.isfinite(v) for v in previous_node_v)
            or not all(math.isfinite(v) for v in (
                previous_c10_capacitor_v, previous_bus_v, bus_v, dt_s,
                r14_pin7_to_pin6_ohm, r73_bottom_side_to_wiper_ohm, c10))
            or dt_s <= 0 or not 0.9 * c10_nominal <= c10 <= 1.5 * c10_nominal
            or not 0 <= r14_pin7_to_pin6_ohm <= r14_total
            or not 0 <= r73_bottom_side_to_wiper_ohm <= r73_total):
        raise ValueError("finite 33-node state and in-range step/settings required")
    lp = ladder_dc["network_parameters"]
    rp = recovery_dc["network_parameters"]
    vp = vca_dc["network_parameters"]
    if not math.isclose(lp["r30"], r76 + r73_bottom_side_to_wiper_ohm,
                        rel_tol=0, abs_tol=1e-8):
        raise ValueError("ladder DC R73 segment differs from transient return")
    if not (vca_dc["external_wiper_and_loudness_voltages_imposed"]
            and vca_dc["second_vca_base_currents_imposed_zero"]):
        raise ValueError("first-VCA DC boundary differs from transient model")
    _, cap, bus_c = active_loaded_matrices(
        ladder_dc=ladder_dc, recovery_dc=recovery_dc, vca_dc=vca_dc)
    rtop = r14_pin7_to_pin6_ohm + r73_total - r73_bottom_side_to_wiper_ohm
    gc10 = c10 / dt_s
    y10 = gc10 / (1 + gc10 * rtop)
    delta_bus = bus_v - previous_bus_v
    scales = ([1e-5] * 5 + [1e-7] * 3 + [1e-7] * 8
              + [1e-6] * 2 + [1e-4] * 6 + [1e-5] * 3
              + [1e-3] * 6)

    def evaluate(x: list[float]) -> tuple[list[float], list[float], float, dict]:
        ladder, _ = evaluate_nodal_kcl(x[:16], **lp)
        recovery, _ = recovery_kcl(x[16:24], **rp)
        local, devices = vca_kcl([x[i] for i in VCA_TO_SYSTEM], **vp)
        f = ladder + recovery + [0.0] * 9
        r2_current = (x[21] - x[24]) / r2
        f[21] -= r2_current
        f[24] += r2_current
        for index, value in zip(VCA_TO_SYSTEM, local):
            f[index] += value
        i10 = y10 * (x[22] - x[7] - previous_c10_capacitor_v)
        f[22] -= i10
        f[7] += i10
        dv = [x[j] - previous_node_v[j] for j in range(NODE_COUNT)]
        charge = [sum(cap[i][j] * dv[j] for j in range(NODE_COUNT))
                  - (bus_c * delta_bus if i == 6 else 0.0)
                  for i in range(NODE_COUNT)]
        return ([f[i] - charge[i] / dt_s for i in range(NODE_COUNT)],
                charge, i10, devices)

    x = list(previous_node_v)
    for iteration in range(70):
        residual, charge, i10, devices = evaluate(x)
        error = max(abs(v / s) for v, s in zip(residual, scales))
        if max(abs(v) for v in residual) < 1e-10 and error < 1e-3:
            break
        jacobian = [[0.0] * NODE_COUNT for _ in range(NODE_COUNT)]
        for col in range(NODE_COUNT):
            trial = x.copy()
            trial[col] += 1e-5
            high, _, _, _ = evaluate(trial)
            for row in range(NODE_COUNT):
                jacobian[row][col] = (high[row] - residual[row]) / 1e-5 / scales[row]
        direction = _solve_linear(jacobian,
                                  [-v / s for v, s in zip(residual, scales)])
        for power in range(30):
            candidate = [v + 0.5 ** power * dv for v, dv in zip(x, direction)]
            try:
                candidate_residual, _, _, _ = evaluate(candidate)
            except ValueError:
                continue
            if max(abs(v / s) for v, s in zip(candidate_residual, scales)) < error:
                x = candidate
                break
        else:
            raise ValueError("active-VCA Newton step did not decrease residual")
    else:
        raise ValueError("active-VCA transient Newton step did not converge")
    residual, charge, i10, devices = evaluate(x)
    c10_v = x[22] - x[7] - rtop * i10
    return {
        "node_v": tuple(x), "c10_capacitor_v": c10_v,
        "bus_v": bus_v,
        "first_vca_differential_collector_v": x[30] - x[31],
        "first_vca_collector_currents_a": (devices["Q16"]["collector_a"],
                                           devices["Q15"]["collector_a"]),
        "r2_current_a": (x[21] - x[24]) / r2,
        "c6_current_a": charge[24] / dt_s,
        "return_current_a": i10,
        "charge_change_c": tuple(charge),
        "max_charge_kcl_residual_a": max(abs(v) for v in residual),
        "iterations": iteration, "offline_reference_only": True,
        "wiper_and_loudness_voltages_fixed": True,
        "second_vca_base_currents_imposed_zero": True,
    }
