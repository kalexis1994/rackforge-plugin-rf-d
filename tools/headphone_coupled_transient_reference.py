"""Offline 62-node nonlinear transient from filter BUS through R21 to J7."""

from __future__ import annotations

import math

from filter_ladder_ebers_moll_dc_reference import _solve_linear, evaluate_nodal_kcl
from filter_panel_headphone_reference import _headphone_parts
from filter_panel_output_small_signal_reference import _panel_parts
from filter_panel_output_transient_reference import panel_load_reduction
from filter_recovery_active_dc_reference import _evaluate as recovery_kcl
from filter_regeneration_reference import _values as regeneration_values
from filter_vca_output_small_signal_reference import LOCAL_TO_SYSTEM, loaded_output_matrices
from filter_vca_output_transient_reference import initial_output_state
from headphone_amp_active_dc_reference import (
    _graph, evaluate_headphone_amp_dc, headphone_amp_dc_jacobian)
from headphone_amp_active_transient_reference import initial_headphone_amp_state
from headphone_output_coupling_reference import _shunt_conductance_s
from vca1_input_boundary_reference import _values as vca_values
from vca_cascaded_output_dc_reference import _evaluate as output_kcl
from vca_output_conversion_dc_reference import _parts as output_parts


PIN22 = 48
R21_WIPER = 49
AMP_FIRST = 50
J7 = 61
NODE_COUNT = 62
SCALES = ([1e-5]*5 + [1e-7]*3 + [1e-7]*8
          + [1e-6]*2 + [1e-4]*6 + [1e-5]
          + [1e-5, 1e-3, 1e-3, 1e-3, 1e-3, 1e-3, 1e-3, 1e-5, 1e-3]
          + [1e-3]*6 + [1e-3]*8 + [1e-3]*14)


def initial_coupled_headphone_state(*, ladder_dc: dict, recovery_dc: dict,
                                    cascaded_output_dc: dict,
                                    transistor_is_a: float,
                                    beta_forward: float, beta_reverse: float,
                                    temperature_k: float,
                                    diode_model: dict) -> dict:
    """C2 and C19 open at DC; both boards start from their isolated points."""
    upstream = initial_output_state(
        ladder_dc=ladder_dc, recovery_dc=recovery_dc,
        cascaded_output_dc=cascaded_output_dc)
    amp = initial_headphone_amp_state(
        transistor_is_a=transistor_is_a,
        beta_forward=beta_forward, beta_reverse=beta_reverse,
        temperature_k=temperature_k, diode_model=diode_model)
    return {"node_v": tuple(upstream["node_v"])+(0.0, 0.0)+tuple(amp["node_v"]),
            "c10_capacitor_v": upstream["c10_capacitor_v"],
            "amp_capacitor_v": dict(amp["capacitor_v"]),
            "bus_v": 0.0}


def nonlinear_coupled_headphone_step(*, ladder_dc: dict,
                                     recovery_dc: dict,
                                     cascaded_output_dc: dict,
                                     previous_state: dict,
                                     bus_v: float, dt_s: float,
                                     r14_pin7_to_pin6_ohm: float,
                                     r73_bottom_side_to_wiper_ohm: float,
                                     r20_wiper_to_ground_ohm: float,
                                     hi_load_ohm: float,
                                     lo_load_ohm: float,
                                     r21_wiper_to_ground_ohm: float,
                                     transistor_is_a: float,
                                     beta_forward: float,
                                     beta_reverse: float,
                                     temperature_k: float,
                                     diode_model: dict,
                                     tip_load_ohm: float | None = None,
                                     ring_load_ohm: float | None = None,
                                     sw18_on: bool = True,
                                     c10_farads: float | None = None) -> dict:
    """One simultaneous implicit step; no imposed R21 wiper resistance."""
    old_v = previous_state["node_v"]
    old_amp_cap = previous_state["amp_capacitor_v"]
    if (len(old_v) != NODE_COUNT
            or not all(math.isfinite(v) for v in old_v)
            or not all(math.isfinite(v) for v in old_amp_cap.values())
            or set(old_amp_cap) != {"C19", "C15", "C21"}
            or not all(math.isfinite(v) for v in (
                previous_state["c10_capacitor_v"], previous_state["bus_v"],
                bus_v, dt_s, r14_pin7_to_pin6_ohm,
                r73_bottom_side_to_wiper_ohm))
            or dt_s <= 0 or not isinstance(sw18_on, bool)):
        raise ValueError("finite complete 62-node state and valid step required")
    c10_nominal, r14_total, r73_total, r76 = regeneration_values()
    c10 = c10_nominal if c10_farads is None else c10_farads
    if (not math.isfinite(c10) or not 0.9*c10_nominal <= c10 <= 1.5*c10_nominal
            or not 0 <= r14_pin7_to_pin6_ohm <= r14_total
            or not 0 <= r73_bottom_side_to_wiper_ohm <= r73_total
            or not math.isclose(ladder_dc["network_parameters"]["r30"],
                                r76+r73_bottom_side_to_wiper_ohm,
                                rel_tol=0, abs_tol=1e-8)
            or not cascaded_output_dc["input_and_controls_imposed"]):
        raise ValueError("DC boundary or return controls differ from transient")
    panel = _panel_parts()
    reduced = panel_load_reduction(
        r20_wiper_to_ground_ohm=r20_wiper_to_ground_ohm,
        hi_load_ohm=hi_load_ohm, lo_load_ohm=lo_load_ohm)
    main_load = (reduced["equivalent_main_load_ohm"] if sw18_on
                 else panel["R20_PANEL"]-r20_wiper_to_ground_ohm)
    head = _headphone_parts()
    if (not math.isfinite(r21_wiper_to_ground_ohm)
            or not 0 < r21_wiper_to_ground_ohm < head["R21_PANEL"]):
        raise ValueError("interior R21 position required")
    upper21 = head["R21_PANEL"]-r21_wiper_to_ground_ohm
    # The capacitor matrix and BUS coupling do not depend on the artificial
    # headphone resistance; its conductance is never stamped below.
    _, cap, bus_c = loaded_output_matrices(
        ladder_dc=ladder_dc, recovery_dc=recovery_dc,
        cascaded_output_dc=cascaded_output_dc,
        main_load_ohm=main_load, headphone_input_ohm=1e12)
    amp_graph = _graph()
    amp_cap = {row["ref"]: row["farad"] for row in amp_graph["capacitors"]}
    if amp_cap != {"C19": 2.5e-6, "C15": 220e-12, "C21": 400e-6}:
        raise ValueError("headphone capacitor values differ from schematic")
    load_g = _shunt_conductance_s(tip_load_ohm, ring_load_ohm)
    r2, _, _, _, _ = vca_values()
    out_r = output_parts()
    lp = ladder_dc["network_parameters"]
    rp = recovery_dc["network_parameters"]
    vp = cascaded_output_dc["network_parameters"]
    amp_params = dict(transistor_is_a=transistor_is_a,
                      beta_forward=beta_forward, beta_reverse=beta_reverse,
                      temperature_k=temperature_k, diode_model=diode_model,
                      _prepared_graph=amp_graph)
    rtop = r14_pin7_to_pin6_ohm+r73_total-r73_bottom_side_to_wiper_ohm
    gc10 = c10/dt_s
    y10 = gc10/(1+gc10*rtop)
    delta_bus = bus_v-previous_state["bus_v"]

    def evaluate(x: list[float]) -> tuple[list[float], dict]:
        if (vp["output_parameters"]["diode_model"] is None
                and not 0 <= x[46] <= vp["plus_v"]):
            raise ValueError("diode-open output domain exceeded")
        ladder, _ = evaluate_nodal_kcl(x[:16], **lp)
        recovery, _ = recovery_kcl(x[16:24], **rp)
        local, devices = output_kcl([x[i] for i in LOCAL_TO_SYSTEM], **vp)
        f = ladder+recovery+[0.0]*24
        r2_current = (x[21]-x[24])/r2
        f[21] -= r2_current
        f[24] += r2_current
        for index, value in zip(LOCAL_TO_SYSTEM, local):
            f[index] += value
        f[47] -= x[47]/(out_r["R75"]+main_load)
        r77_current = (x[47]-x[PIN22])/head["R77_BOARD4"]
        r21_upper_current = (x[PIN22]-x[R21_WIPER])/upper21
        f[47] -= r77_current
        i10 = y10*(x[22]-x[7]-previous_state["c10_capacitor_v"])
        f[22] -= i10
        f[7] += i10
        dv = [x[j]-old_v[j] for j in range(48)]
        charge = [sum(cap[i][j]*dv[j] for j in range(48))
                  - (bus_c*delta_bus if i == 6 else 0.0)
                  for i in range(48)]
        residual = [f[i]-charge[i]/dt_s for i in range(48)]
        residual += [r21_upper_current-r77_current,
                     (x[R21_WIPER]-x[PIN22])/upper21
                     + x[R21_WIPER]/r21_wiper_to_ground_ohm]
        active, amp_parts = evaluate_headphone_amp_dc(
            x[AMP_FIRST:J7], **amp_params)
        residual += active+[load_g*x[J7]]
        cap_currents = {}
        for name, left, right in (("C19", R21_WIPER, AMP_FIRST),
                                  ("C15", AMP_FIRST+7, AMP_FIRST+8),
                                  ("C21", AMP_FIRST+10, J7)):
            current = amp_cap[name]/dt_s*(
                x[left]-x[right]-old_amp_cap[name])
            cap_currents[name] = current
            residual[left] += current
            residual[right] -= current
        return residual, {"i10": i10, "charge": charge,
                          "r77_current": r77_current,
                          "r21_upper_current": r21_upper_current,
                          "cap_currents": cap_currents,
                          "amp_parts": amp_parts,
                          "upstream_devices": devices}

    x = list(old_v)
    for iteration in range(80):
        residual, parts = evaluate(x)
        error = max(abs(v/scale) for v, scale in zip(residual, SCALES))
        if max(abs(v) for v in residual) < 1e-10 and error < 1e-3:
            break
        jacobian = [[0.0]*NODE_COUNT for _ in range(NODE_COUNT)]
        # Upstream 50 columns retain their numerical tangent. The board-3
        # device columns use the exact Ebers-Moll/Shockley conductance stamp.
        for col in range(AMP_FIRST):
            trial = x.copy()
            trial[col] += 1e-5
            high, _ = evaluate(trial)
            for row in range(NODE_COUNT):
                jacobian[row][col] = (high[row]-residual[row])/1e-5/SCALES[row]
        active = headphone_amp_dc_jacobian(x[AMP_FIRST:J7], **amp_params)
        for local_row, values in enumerate(active):
            row = AMP_FIRST+local_row
            for local_col, value in enumerate(values):
                jacobian[row][AMP_FIRST+local_col] = value/SCALES[row]

        def stamp_cap(left: int, right: int, farad: float) -> None:
            g = farad/dt_s
            for row, col, sign in ((left, left, 1), (left, right, -1),
                                   (right, left, -1), (right, right, 1)):
                if col >= AMP_FIRST:
                    jacobian[row][col] += sign*g/SCALES[row]

        stamp_cap(R21_WIPER, AMP_FIRST, amp_cap["C19"])
        stamp_cap(AMP_FIRST+7, AMP_FIRST+8, amp_cap["C15"])
        stamp_cap(AMP_FIRST+10, J7, amp_cap["C21"])
        jacobian[J7][J7] += load_g/SCALES[J7]
        direction = _solve_linear(jacobian,
                                  [-v/scale for v, scale in zip(residual, SCALES)])
        for power in range(32):
            trial = [v+0.5**power*dv for v, dv in zip(x, direction)]
            try:
                next_residual, _ = evaluate(trial)
            except ValueError:
                continue
            if max(abs(v/scale) for v, scale in zip(next_residual, SCALES)) < error:
                x = trial
                break
        else:
            raise ValueError("coupled headphone Newton iteration did not decrease KCL")
    else:
        raise ValueError("coupled headphone Newton iteration did not converge")
    residual, parts = evaluate(x)
    pin21 = x[47]*main_load/(out_r["R75"]+main_load)
    hi = pin21*reduced["hi_to_pin21_ratio"] if sw18_on else 0.0
    lo = hi*reduced["lo_to_hi_ratio"] if sw18_on else 0.0
    return {"node_v": tuple(x),
            "c10_capacitor_v": x[22]-x[7]-rtop*parts["i10"],
            "amp_capacitor_v": {
                "C19": x[R21_WIPER]-x[AMP_FIRST],
                "C15": x[AMP_FIRST+7]-x[AMP_FIRST+8],
                "C21": x[AMP_FIRST+10]-x[J7]},
            "bus_v": bus_v, "c2_right_v": x[47],
            "r21_wiper_v": x[R21_WIPER],
            "j7_tip_v": x[J7], "j7_ring_v": x[J7],
            "j4_hi_v": hi, "j5_lo_v": lo,
            "c19_current_a": parts["cap_currents"]["C19"],
            "r21_upper_current_a": parts["r21_upper_current"],
            "r21_lower_current_a": x[R21_WIPER]/r21_wiper_to_ground_ohm,
            "r77_current_a": parts["r77_current"],
            "c21_current_a": parts["cap_currents"]["C21"],
            "max_charge_kcl_residual_a": max(abs(v) for v in residual),
            "iterations": iteration, "sw18_on_imposed": sw18_on,
            "offline_reference_only": True}
