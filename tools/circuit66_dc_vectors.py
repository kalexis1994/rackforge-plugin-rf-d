"""Full DC KCL oracle; all 18 capacitors open, independent FD columns."""
from __future__ import annotations

import copy
import json
from pathlib import Path

from cutoff_ebers_moll_reference import evaluate as cutoff_kcl, panel_equivalent
from cutoff_j7_vectors import setup
from filter_ladder_ebers_moll_dc_reference import evaluate_nodal_kcl, _solve_linear
from filter_recovery_active_dc_reference import _evaluate as recovery_kcl
from filter_vca_output_small_signal_reference import LOCAL_TO_SYSTEM
from headphone_amp_active_dc_reference import evaluate_headphone_amp_dc
from vca_cascaded_output_dc_reference import _evaluate as output_kcl
from vca1_input_boundary_reference import _values as vca_values

OUTPUT = Path(__file__).resolve().parents[1] / "evidence/circuit66_dc_vectors.json"


def fd_direction(x, r, evaluate):
    j = [[0.0]*66 for _ in x]
    for col in range(66):
        shifted = x.copy()
        shifted[col] += 1e-6
        rh, _ = evaluate(shifted)
        for row in range(66):
            j[row][col] = (rh[row]-r[row])/1e-6
    return _solve_linear(j, [-v for v in r])


def solve_dc(seed, evaluate):
    """Offline 40/32 budget; KCL plus unscaled Newton correction in volts."""
    x = seed.copy()
    for _ in range(40):
        r, _ = evaluate(x)
        error = max(abs(v) for v in r)
        direction = fd_direction(x, r, evaluate)
        correction = max(abs(v) for v in direction)
        if error < 1e-11 and correction < 1e-8:
            return x, error, correction
        for power in range(32):
            candidate = [v+2.0**-power*d for v,d in zip(x,direction)]
            try:
                rr, _ = evaluate(candidate)
            except (ValueError, OverflowError):
                continue
            next_error = max(abs(v) for v in rr)
            if error < 1e-11:
                decreases = (next_error < 1e-11 and
                             max(abs(v) for v in fd_direction(candidate, rr, evaluate)) < correction)
            else:
                decreases = next_error < error
            if decreases:
                x = candidate
                break
        else:
            raise ValueError(f"full DC line search: KCL={error} correction={correction}")
    raise ValueError("full DC offline budget")


def dc_evaluator(values, controls):
    ladder, recovery, output, hp, _, _, _ = values
    pv, pg = panel_equivalent(controls["panel"])
    r2 = vca_values()[0]

    def evaluate(x):
        r, _ = evaluate_nodal_kcl(x[:16], **ladder["network_parameters"])
        r[5] += ladder["network_parameters"]["tail_current"]-(x[5]-x[65])/680
        rec, _ = recovery_kcl(x[16:24], **recovery["network_parameters"])
        local, _ = output_kcl([x[i] for i in LOCAL_TO_SYSTEM], **output["network_parameters"])
        r += rec+[0.0]*24
        # DC C6 open: R2 terminates in the otherwise floating C6-left node.
        i2 = (x[21]-x[24])/r2
        r[21] -= i2
        r[24] += i2
        for index, value in zip(LOCAL_TO_SYSTEM, local):
            r[index] += value
        # All panel capacitances open. Use explicit passive KCL; no dynamics.
        # Nominal ON R20 load is only a DC shunt of zero-voltage C2_RIGHT.
        r20_cursor = 1/(1/2500+1/10000+1/(33000+1/(1/1000+1/100000)))
        r[47] -= x[47]/(1000+2500+r20_cursor)
        i77 = (x[47]-x[48])/1000
        i21 = (x[48]-x[49])/3000
        r[47] -= i77
        r += [i21-i77, (x[49]-x[48])/3000+x[49]/2000]
        active, _ = evaluate_headphone_amp_dc(x[50:61], **hp)
        r += active+[x[61]*(1/390+1/32+1/32)]
        control, _ = cutoff_kcl(x[62:66], panel_v=pv, panel_g=pg,
                                range_fraction=controls["range_fraction"], tail_v=x[5],
                                q26=controls["q26"], q28=controls["q28"])
        r += control
        return r, {}

    return evaluate


def generate_vectors():
    cases = []
    for r61 in (200, 200000):
        values = setup(r61)
        initial = list(values[5]["node_v"])
        for name, key, value in (("centre", None, None),
                                 ("cutoff_min", "cutoff_fraction_from_neg10", 0),
                                 ("cutoff_max", "cutoff_fraction_from_neg10", 1),
                                 ("range_min", "range_fraction", 0),
                                 ("range_max", "range_fraction", 1),
                                 ("scale_min", "scale_active_ohm", 0),
                                 ("scale_max", "scale_active_ohm", 500)):
            controls = copy.deepcopy(values[4])
            if key == "range_fraction":
                controls[key] = value
            elif key is not None:
                controls["panel"][key] = value
            try:
                node_v, error, correction = solve_dc(initial, dc_evaluator(values, controls))
            except ValueError as e:
                raise ValueError(f"{name}, R61={r61}: {e}") from e
            cases.append(dict(name=name, r61_ohm=r61, controls=controls,
                              numerical_seed_v=initial, node_v=node_v,
                              tail_current_a=(node_v[5]-node_v[65])/680,
                              max_kcl_a=error, max_newton_correction_v=correction))
    return dict(schema="rf-d/circuit66-dc-vectors/v1", method="all-capacitors-open 66-node FD Newton",
                sources=["SVC-9 Fig. 9-11 PDF p. 13", "SVC-9 Fig. 9-8 PDF p. 10",
                         "SVC-9 Fig. 9-17 PDF p. 19"],
                gates=dict(node_error_v=1e-6, tail_error_a=1e-9, kcl_a=1e-11, dc_correction_v=1e-8),
                cases=cases, audio_fidelity_claim=False)


if __name__ == "__main__":
    report = generate_vectors()
    OUTPUT.write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(dict(cases=len(report["cases"]), max_kcl_a=max(c["max_kcl_a"] for c in report["cases"]))))
