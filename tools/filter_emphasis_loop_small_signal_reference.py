"""Conditional AC closure of C10/R14/R73 into the active ladder and recovery.

The unbranched series path C10 -> R14 -> right segment of R73 is reduced
to one complex admittance between the recovery tap and Q30 base. The DC
ladder already includes R76 plus the left segment of R73 to BOTTOM.
"""

from __future__ import annotations

import math

from filter_ladder_ebers_moll_dc_reference import _solve_linear
from filter_recovery_active_small_signal_reference import coupled_matrices
from filter_regeneration_reference import _values


def series_return_admittance_s(*, frequency_hz: float,
                               r14_pin7_to_pin6_ohm: float,
                               r73_bottom_side_to_wiper_ohm: float) -> complex:
    """C10 plus panel/trimmer series impedance, in siemens."""
    c10, r14_total, r73_total, _ = _values()
    if (not math.isfinite(frequency_hz) or frequency_hz < 0
            or not math.isfinite(r14_pin7_to_pin6_ohm)
            or not 0 <= r14_pin7_to_pin6_ohm <= r14_total
            or not math.isfinite(r73_bottom_side_to_wiper_ohm)
            or not 0 <= r73_bottom_side_to_wiper_ohm <= r73_total):
        raise ValueError("frequency and electrical resistance segments must be in range")
    s_c = 2j * math.pi * frequency_hz * c10
    series_ohm = (r14_pin7_to_pin6_ohm
                  + r73_total - r73_bottom_side_to_wiper_ohm)
    return s_c / (1 + s_c * series_ohm)


def coupled_emphasis_small_signal(*, ladder_dc: dict, recovery_dc: dict,
                                  frequency_hz: float,
                                  r14_pin7_to_pin6_ohm: float,
                                  r73_bottom_side_to_wiper_ohm: float) -> dict:
    """Closed 24-node incremental network for BUS=1 V; no input clipping.

    The ladder's Q30 base-to-BOTTOM path must have been solved with the same
    R73 left segment at DC, where C10 leaves the right segment open.
    """
    c10, r14_total, r73_total, r76 = _values()
    del c10, r14_total, r73_total
    r30_dc = ladder_dc["network_parameters"]["r30"]
    if not math.isclose(r30_dc, r76 + r73_bottom_side_to_wiper_ohm,
                        rel_tol=0, abs_tol=1e-8):
        raise ValueError("ladder DC R73 left segment differs from AC return")
    admittance = series_return_admittance_s(
        frequency_hz=frequency_hz,
        r14_pin7_to_pin6_ohm=r14_pin7_to_pin6_ohm,
        r73_bottom_side_to_wiper_ohm=r73_bottom_side_to_wiper_ohm)
    g, c, c27 = coupled_matrices(ladder_dc, recovery_dc)
    s = 2j * math.pi * frequency_hz
    system = [[g[i][j] - s * c[i][j] for j in range(24)] for i in range(24)]
    # Each KCL row is incoming minus outgoing, hence a branch contributes
    # -Y to both diagonal entries and +Y to both off-diagonal entries.
    base, tap = 7, 22
    system[base][base] -= admittance
    system[tap][tap] -= admittance
    system[base][tap] += admittance
    system[tap][base] += admittance
    rhs = [0j] * 24
    rhs[6] = -s * c27
    v = _solve_linear(system, rhs)
    residual = max(abs(sum(system[i][j] * v[j] for j in range(24)) - rhs[i])
                   for i in range(24))
    return {
        "frequency_hz": frequency_hz,
        "r14_pin7_to_pin6_ohm": r14_pin7_to_pin6_ohm,
        "r73_bottom_side_to_wiper_ohm": r73_bottom_side_to_wiper_ohm,
        "node_v_per_bus_v": tuple(v),
        "q30_base_v_per_bus_v": v[base],
        "bottom_v_per_bus_v": v[4],
        "recovery_tap_v_per_bus_v": v[tap],
        "recovery_collector_v_per_bus_v": v[21],
        "ladder_top_differential_v_per_bus_v": v[11] - v[15],
        "return_current_a_per_bus_v": admittance * (v[tap] - v[base]),
        "return_series_admittance_s": admittance,
        "input_admittance_s": s * c27 * (1 - v[6]),
        "max_linear_kcl_residual_a_per_bus_v": residual,
        "device_parameters_imposed": True,
        "feedback_closed_in_small_signal": True,
    }


if __name__ == "__main__":
    import json

    from filter_ladder_active_dc_reference import UPPER
    from filter_ladder_ebers_moll_dc_reference import DEVICE_NODES, conditional_ladder_ebers_moll_dc
    from filter_recovery_active_dc_reference import DEVICES, conditional_recovery_dc

    recovery = conditional_recovery_dc(
        is_a={name: 1e-14 for name in DEVICES},
        beta_forward={name: 100 for name in DEVICES},
        beta_reverse={name: 5 for name in DEVICES}, temperature_k=298.15)
    cutoff_inputs = dict(panel_inputs=dict(cutoff_fraction_from_neg10=0.5,
                                           scale_active_ohm=250, contour_pin16_v=0),
                         range_fraction_from_ground=0.1,
                         is26_a=1e-14, is28_a=1e-14,
                         beta26=100, beta28=100, temperature_k=298.15)
    for r61 in (200, 200000):
        ladder = conditional_ladder_ebers_moll_dc(
            cutoff_inputs=cutoff_inputs, is29_a=1e-14, is30_a=1e-14,
            beta29=100, beta30=100,
            upper_is_a={name: 1e-14 for name in UPPER},
            upper_beta={name: 100 for name in UPPER},
            reverse_beta={name: 5 for name in DEVICE_NODES},
            r61_ohm=r61, r73_bottom_side_to_wiper_ohm=500)
        for r14 in (0, 25000, 50000):
            for frequency in (0, 30, 100, 300, 1000):
                out = coupled_emphasis_small_signal(
                    ladder_dc=ladder, recovery_dc=recovery,
                    frequency_hz=frequency, r14_pin7_to_pin6_ohm=r14,
                    r73_bottom_side_to_wiper_ohm=500)
                print(json.dumps({"r61_ohm": r61, "r14_ohm": r14,
                                  "frequency_hz": frequency,
                                  "tap_magnitude": abs(out[
                                      "recovery_tap_v_per_bus_v"]),
                                  "top_magnitude": abs(out[
                                      "ladder_top_differential_v_per_bus_v"]),
                                  "kcl_residual": out[
                                      "max_linear_kcl_residual_a_per_bus_v"]}))
