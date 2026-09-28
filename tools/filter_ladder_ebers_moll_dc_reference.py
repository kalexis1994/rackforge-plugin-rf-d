"""16-node conditional DC ladder using simple Ebers-Moll BJTs.

The two BJT junctions are represented, so a forward-biased base-collector
junction is in the domain. Device parameters are imposed, not measured.
"""

from __future__ import annotations

import json
import math

from filter_ladder_active_dc_reference import LEFT, RIGHT, UPPER, conditional_ladder_active_dc
from filter_ladder_spine_dc_reference import _spine
from filter_input_reference import _parts
from filter_input_pair_reference import EVIDENCE as LOWER_EVIDENCE
from semiconductor_ideal import thermal_voltage_v


NODE_NAMES = ("TAP_Q2_Q3", "TAP_Q10_Q11", "TAP_Q19_Q20", "TAP_Q23_Q24",
              "BOTTOM", "TAIL", "BASE_Q29", "BASE_Q30",
              "L_Q29C_Q23E", "L_Q23C_Q19E", "L_Q19C_Q10E", "L_Q10C_Q2E",
              "R_Q30C_Q24E", "R_Q24C_Q20E", "R_Q20C_Q11E", "R_Q11C_Q3E")
DEVICE_NODES = {
    "Q29": (6, 8, 5), "Q23": (3, 9, 8), "Q19": (2, 10, 9),
    "Q10": (1, 11, 10), "Q2": (0, None, 11),
    "Q30": (7, 12, 5), "Q24": (3, 13, 12), "Q20": (2, 14, 13),
    "Q11": (1, 15, 14), "Q3": (0, None, 15),
}


def _solve_linear(matrix: list[list[float]], rhs: list[float]) -> list[float]:
    """Small dense Gaussian elimination with scaled partial pivoting."""
    n = len(rhs)
    rows = [list(matrix[i]) + [rhs[i]] for i in range(n)]
    scales = [max(abs(value) for value in row[:n]) for row in rows]
    for column in range(n):
        pivot = max(range(column, n), key=lambda i: abs(rows[i][column]) / scales[i]
                    if scales[i] else 0)
        if scales[pivot] == 0 or abs(rows[pivot][column]) / scales[pivot] < 1e-12:
            raise ValueError("singular Ebers-Moll nodal Jacobian")
        rows[column], rows[pivot] = rows[pivot], rows[column]
        scales[column], scales[pivot] = scales[pivot], scales[column]
        diagonal = rows[column][column]
        for i in range(column + 1, n):
            factor = rows[i][column] / diagonal
            rows[i][column] = 0.0
            for j in range(column + 1, n + 1):
                rows[i][j] -= factor * rows[column][j]
    result = [0.0] * n
    for i in range(n - 1, -1, -1):
        result[i] = (rows[i][n] - sum(rows[i][j] * result[j]
                                    for j in range(i + 1, n))) / rows[i][i]
    return result


def _device(vb: float, vc: float, ve: float, is_a: float,
            beta_forward: float, beta_reverse: float, vt: float) -> dict:
    xbe, xbc = (vb - ve) / vt, (vb - vc) / vt
    if max(xbe, xbc) > 45:
        raise ValueError("trial voltage outside finite BJT exponential domain")
    forward = is_a * math.expm1(xbe)
    reverse = is_a * math.expm1(xbc)
    transport = forward - reverse
    ib = forward / beta_forward + reverse / beta_reverse
    ic = transport - reverse / beta_reverse
    return {"base_a": ib, "collector_a": ic, "emitter_a": ib + ic,
            "v_be_v": vb - ve, "v_bc_v": vb - vc,
            "forward_junction_a": forward, "reverse_junction_a": reverse}


def conditional_ladder_ebers_moll_dc(*, cutoff_inputs: dict,
                                     is29_a: float, is30_a: float,
                                     beta29: float, beta30: float,
                                     upper_is_a: dict[str, float],
                                     upper_beta: dict[str, float],
                                     reverse_beta: dict[str, float],
                                     r61_ohm: int,
                                     r73_bottom_side_to_wiper_ohm: float) -> dict:
    """Solve the nominal board-4 DC network, allowing B-C forward bias.

    Q26/Q28 remain the earlier conditional active current source. Any
    failed Q28 margin invalidates the joint solution as a physical point.
    """
    if set(reverse_beta) != set(DEVICE_NODES) or not all(
            math.isfinite(value) and value > 0 for value in reverse_beta.values()):
        raise ValueError("positive finite reverse beta required for all ten devices")
    active = conditional_ladder_active_dc(
        cutoff_inputs=cutoff_inputs, is29_a=is29_a, is30_a=is30_a,
        beta29=beta29, beta30=beta30, upper_is_a=upper_is_a,
        upper_beta=upper_beta, r61_ohm=r61_ohm,
        r73_bottom_side_to_wiper_ohm=r73_bottom_side_to_wiper_ohm)
    vt = thermal_voltage_v(cutoff_inputs["temperature_k"])
    tail_current = active["lower"]["lower_pair"]["tail_current_a"]
    cutoff = active["lower"]["lower_pair"]["cutoff"]
    values_is = {"Q29": is29_a, "Q30": is30_a, **upper_is_a}
    values_bf = {"Q29": beta29, "Q30": beta30, **upper_beta}
    plus, spine_resistances = _spine()
    r54 = _parts()["R54"]["ohm"]
    r30 = active["lower"]["r30_bottom_path_ohm"]
    r60 = json.loads(LOWER_EVIDENCE.read_text(encoding="utf-8"))["connections"]["R60"]["ohm"]

    def evaluate(x: list[float]) -> tuple[list[float], dict]:
        currents = {}
        for name, (bi, ci, ei) in DEVICE_NODES.items():
            currents[name] = _device(x[bi], plus if ci is None else x[ci],
                                     x[ei], values_is[name], values_bf[name],
                                     reverse_beta[name], vt)
        r = [0.0] * 16
        pairs = (("Q2", "Q3"), ("Q10", "Q11"),
                 ("Q19", "Q20"), ("Q23", "Q24"))
        previous = plus
        for i, pair in enumerate(pairs):
            incoming = (previous - x[i]) / spine_resistances[i]
            outgoing = ((x[i] - x[i + 1]) / spine_resistances[i + 1]
                        if i < 3 else (x[i] - x[4]) / spine_resistances[4])
            r[i] = incoming - outgoing - sum(currents[name]["base_a"] for name in pair)
            previous = x[i]
        r[4] = ((x[3] - x[4]) / spine_resistances[4] - x[4] / r61_ohm
                - (x[4] - x[6]) / r54 - (x[4] - x[7]) / r30)
        r[5] = currents["Q29"]["emitter_a"] + currents["Q30"]["emitter_a"] - tail_current
        r[6] = (x[4] - x[6]) / r54 - currents["Q29"]["base_a"]
        r[7] = (x[4] - x[7]) / r30 - currents["Q30"]["base_a"]
        for side, start in ((LEFT, 8), (RIGHT, 12)):
            for offset, (lower, higher) in enumerate(zip(side, side[1:])):
                # Higher emitter injects into this node; lower collector
                # draws from it. All 16 rows use incoming-minus-outgoing.
                r[start + offset] = (currents[higher]["emitter_a"]
                                     - currents[lower]["collector_a"])
        return r, currents

    x = [*active["spine"]["tap_voltages_top_to_bottom_v"],
         active["bottom_v"], active["tail_v"],
         active["lower"]["q29_base_v"], active["lower"]["q30_base_v"]]
    for side in (LEFT, RIGHT):
        x.extend(active["upper_devices"][name]["emitter_v"] for name in side[1:])
    scales = [1e-5] * 5 + [1e-7] * 3 + [1e-7] * 8
    iterations = 0
    for iteration in range(80):
        residual, currents = evaluate(x)
        error = max(abs(r / scale) for r, scale in zip(residual, scales))
        if max(abs(r) for r in residual) < 1e-11 and error < 1e-4:
            iterations = iteration
            break
        jacobian = [[0.0] * 16 for _ in range(16)]
        for column in range(16):
            shifted = x.copy()
            shifted[column] += 1e-5
            perturbed, _ = evaluate(shifted)
            for row in range(16):
                jacobian[row][column] = (perturbed[row] - residual[row]) / 1e-5 / scales[row]
        direction = _solve_linear(jacobian,
                                  [-r / scale for r, scale in zip(residual, scales)])
        accepted = False
        for power in range(24):
            step = 0.5 ** power
            trial = [value + step * change for value, change in zip(x, direction)]
            try:
                trial_residual, _ = evaluate(trial)
            except ValueError:
                continue
            trial_error = max(abs(r / scale) for r, scale in zip(trial_residual, scales))
            if trial_error < error:
                x = trial
                accepted = True
                break
        if not accepted:
            raise ValueError("Ebers-Moll DC Newton iteration did not decrease KCL residual")
    else:
        raise ValueError("Ebers-Moll DC Newton iteration did not converge")

    residual, currents = evaluate(x)
    # Jacobian of incoming-minus-outgoing DC KCL in siemens. This is the
    # exact interface for small-signal capacitor stamping at this bias.
    conductance = [[0.0] * 16 for _ in range(16)]
    for column in range(16):
        high = x.copy()
        low = x.copy()
        high[column] += 1e-6
        low[column] -= 1e-6
        high_r, _ = evaluate(high)
        low_r, _ = evaluate(low)
        for row in range(16):
            conductance[row][column] = (high_r[row] - low_r[row]) / 2e-6
    q28_collector_v = x[5] - tail_current * r60
    q28_candidate = 0 < cutoff["shared_node_v"] < q28_collector_v
    reverse_forward = tuple(name for name, part in currents.items()
                            if part["v_bc_v"] > 0)
    return {"nodes_v": dict(zip(NODE_NAMES, x)), "devices": currents,
            "max_kcl_residual_a": max(abs(value) for value in residual),
            "kcl_residuals_a": dict(zip(NODE_NAMES, residual)),
            "conductance_matrix_s": tuple(tuple(row) for row in conductance),
            "iterations": iterations,
            "forward_biased_base_collector_devices": reverse_forward,
            "q28_forward_active_candidate": q28_candidate,
            "q28_collector_v": q28_collector_v,
            "r61_ohm_selected": r61_ohm,
            "reverse_beta_imposed": reverse_beta,
            "tail_current_a": tail_current,
            "simple_ebers_moll_only": True,
            "physical_r61_unresolved": True}


if __name__ == "__main__":
    cutoff_inputs = dict(panel_inputs=dict(cutoff_fraction_from_neg10=0.5,
                                           scale_active_ohm=250, contour_pin16_v=0),
                         range_fraction_from_ground=0.1,
                         is26_a=1e-14, is28_a=1e-14,
                         beta26=100, beta28=100, temperature_k=298.15)
    for candidate in (200, 200000):
        result = conditional_ladder_ebers_moll_dc(
            cutoff_inputs=cutoff_inputs, is29_a=1e-14, is30_a=1e-14,
            beta29=100, beta30=100,
            upper_is_a={name: 1e-14 for name in UPPER},
            upper_beta={name: 100 for name in UPPER},
            reverse_beta={name: 5 for name in DEVICE_NODES},
            r61_ohm=candidate, r73_bottom_side_to_wiper_ohm=500)
        print(json.dumps({"r61_ohm": candidate,
                          "bottom_v": result["nodes_v"]["BOTTOM"],
                          "tail_v": result["nodes_v"]["TAIL"],
                          "forward_biased_base_collector_devices": result[
                              "forward_biased_base_collector_devices"],
                          "max_kcl_residual_a": result["max_kcl_residual_a"],
                          "iterations": result["iterations"]}, indent=2))
