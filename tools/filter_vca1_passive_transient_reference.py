"""Offline nonlinear filter transient with passive R2/C6/C15 VCA entrance.

The 14 BJT devices of ladder/recovery stay nonlinear. Q16/Q15 base
currents, balance, both VCA gain stages and final output remain omitted.
"""

from __future__ import annotations

import math

from filter_full_analytic_jacobian import analytic_dc_jacobian
from filter_full_nonlinear_transient_reference import initial_state
from filter_ladder_ebers_moll_dc_reference import _solve_linear, evaluate_nodal_kcl
from filter_recovery_active_dc_reference import _evaluate as recovery_kcl
from filter_regeneration_reference import _values as regeneration_values
from filter_vca1_loaded_small_signal_reference import loaded_matrices
from vca1_input_boundary_reference import _values as vca_values


def initial_loaded_state(*, ladder_dc: dict, recovery_dc: dict) -> dict:
    core = initial_state(ladder_dc=ladder_dc, recovery_dc=recovery_dc)
    node = core["node_v"] + (core["node_v"][21], 0.0, 0.0)
    return {"node_v": node, "c10_capacitor_v": core["c10_capacitor_v"],
            "bus_v": 0.0}


def nonlinear_loaded_step(*, ladder_dc: dict, recovery_dc: dict,
                          previous_node_v: tuple[float, ...],
                          previous_c10_capacitor_v: float,
                          previous_bus_v: float, bus_v: float,
                          dt_s: float, r14_pin7_to_pin6_ohm: float,
                          r73_bottom_side_to_wiper_ohm: float,
                          c10_farads: float | None = None,
                          jacobian_method: str = "analytic") -> dict:
    """Backward Euler step with 27 voltages plus C10 capacitor state."""
    c10_nominal, r14_total, r73_total, r76 = regeneration_values()
    c10 = c10_nominal if c10_farads is None else c10_farads
    r2, _, r34, _, r36 = vca_values()
    if (len(previous_node_v) != 27
            or not all(math.isfinite(value) for value in previous_node_v)
            or not all(math.isfinite(value) for value in (
                previous_c10_capacitor_v, previous_bus_v, bus_v, dt_s,
                r14_pin7_to_pin6_ohm, r73_bottom_side_to_wiper_ohm, c10))
            or dt_s <= 0 or not 0.9 * c10_nominal <= c10 <= 1.5 * c10_nominal
            or not 0 <= r14_pin7_to_pin6_ohm <= r14_total
            or not 0 <= r73_bottom_side_to_wiper_ohm <= r73_total
            or jacobian_method not in ("analytic", "finite_difference")):
        raise ValueError("finite 27-node state and in-range step/settings required")
    lp = ladder_dc["network_parameters"]
    rp = recovery_dc["network_parameters"]
    if not math.isclose(lp["r30"], r76 + r73_bottom_side_to_wiper_ohm,
                        rel_tol=0, abs_tol=1e-8):
        raise ValueError("ladder DC R73 segment differs from transient return")
    _, cap, c27 = loaded_matrices(ladder_dc=ladder_dc, recovery_dc=recovery_dc)
    rtop = r14_pin7_to_pin6_ohm + r73_total - r73_bottom_side_to_wiper_ohm
    gc10 = c10 / dt_s
    y10 = gc10 / (1 + gc10 * rtop)
    delta_bus = bus_v - previous_bus_v
    scales = [1e-5] * 5 + [1e-7] * 3 + [1e-7] * 8 + [1e-6] * 2 + [1e-4] * 6 + [1e-5] * 3

    def evaluate(x: list[float]) -> tuple[list[float], list[float], float]:
        ladder, _ = evaluate_nodal_kcl(x[:16], **lp)
        recovery, _ = recovery_kcl(x[16:24], **rp)
        f = ladder + recovery + [0.0] * 3
        def resistor(left, right, ohm):
            current = (x[left] - x[right]) / ohm
            f[left] -= current
            f[right] += current
        resistor(21, 24, r2)
        resistor(25, 26, r34)
        f[26] -= x[26] / r36
        i10 = y10 * (x[22] - x[7] - previous_c10_capacitor_v)
        f[22] -= i10
        f[7] += i10
        dv = [x[j] - previous_node_v[j] for j in range(27)]
        charge = [sum(cap[i][j] * dv[j] for j in range(27))
                  - (c27 * delta_bus if i == 6 else 0.0)
                  for i in range(27)]
        return [f[i] - charge[i] / dt_s for i in range(27)], charge, i10

    def analytic(x: list[float]) -> list[list[float]]:
        core = analytic_dc_jacobian(node_v=x[:24], ladder_parameters=lp,
                                    recovery_parameters=rp)
        j = [[0.0] * 27 for _ in range(27)]
        for row in range(24):
            for column in range(24):
                j[row][column] = core[row][column]
        def resistor(left, right, ohm):
            g = 1 / ohm
            j[left][left] -= g
            j[right][right] -= g
            j[left][right] += g
            j[right][left] += g
        resistor(21, 24, r2)
        resistor(25, 26, r34)
        j[26][26] -= 1 / r36
        for row in range(27):
            for column in range(27):
                j[row][column] -= cap[row][column] / dt_s
        j[7][7] -= y10
        j[22][22] -= y10
        j[7][22] += y10
        j[22][7] += y10
        return j

    x = list(previous_node_v)
    iterations = 0
    for iteration in range(60):
        residual, charge, i10 = evaluate(x)
        error = max(abs(value / scale) for value, scale in zip(residual, scales))
        if max(abs(value) for value in residual) < 1e-10 and error < 1e-3:
            iterations = iteration
            break
        if jacobian_method == "analytic":
            jacobian = analytic(x)
            for row in range(27):
                jacobian[row] = [value / scales[row] for value in jacobian[row]]
        else:
            jacobian = [[0.0] * 27 for _ in range(27)]
            for column in range(27):
                shifted = x.copy()
                shifted[column] += 1e-5
                high, _, _ = evaluate(shifted)
                for row in range(27):
                    jacobian[row][column] = (high[row] - residual[row]) / 1e-5 / scales[row]
        direction = _solve_linear(jacobian,
                                  [-value / scale for value, scale in zip(residual, scales)])
        accepted = False
        for power in range(28):
            trial = [value + 0.5 ** power * change
                     for value, change in zip(x, direction)]
            try:
                trial_residual, _, _ = evaluate(trial)
            except ValueError:
                continue
            if max(abs(value / scale) for value, scale in zip(trial_residual, scales)) < error:
                x = trial
                accepted = True
                break
        if not accepted:
            raise ValueError("loaded transient Newton step did not decrease residual")
    else:
        raise ValueError("loaded transient Newton step did not converge")
    residual, charge, i10 = evaluate(x)
    c10_v = x[22] - x[7] - rtop * i10
    c6_current = charge[24] / dt_s
    # Node 24 has only C6 and R2; its charge row is exactly C6 charge.
    return {
        "node_v": tuple(x), "c10_capacitor_v": c10_v,
        "r2_current_a": (x[21] - x[24]) / r2,
        "c6_current_a": c6_current,
        "return_current_a": i10,
        "charge_change_c": tuple(charge),
        "max_charge_kcl_residual_a": max(abs(value) for value in residual),
        "iterations": iterations,
        "jacobian_method": jacobian_method,
        "offline_reference_only": True,
    }
