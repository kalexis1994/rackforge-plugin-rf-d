"""Predeclared FD step/component audit; never replace the original reset failure."""
import gzip
import json
import math
from pathlib import Path
import numpy as np
from bjt_charge_ngspice_probes import model_parameters
from loudness_latch_bdf_reference import BdfNetwork
from loudness_latch_bdf_probes import unpack
from loudness_latch_bdf_memory_transfer import stamps
from loudness_latch_bdf_transfer_solve import backward_errors
from loudness_latch_bdf_rational_solve import solve
from loudness_latch_bdf_fd_transfer_audit import OUTPUT as FD_SOURCE, PATHS as FD_PATHS
from loudness_latch_bdf_memory_windows import OUTPUT as WINDOWS
from loudness_latch_bdf_doubling_survey import store
from loudness_latch_increment_probes import hashes
from loudness_lab_metadata import environment

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "evidence/loudness_latch_bdf_fd_sensitivity.json.gz"
SUMMARY = ROOT / "evidence/loudness_latch_bdf_fd_sensitivity_summary.json"
STEPS_V = (1e-4, 1e-5, 1e-6, 1e-7, 1e-8)
MODES = ("full-residual-FD", "static-FD/existing-dynamic-J")
BACKWARD_GATE = 1e-10
MAP_GATE = 1e-8
PATHS = tuple(dict.fromkeys((*FD_PATHS, FD_SOURCE, Path(__file__).resolve(),
    ROOT / "docs/BIESTABLE_SENSIBILIDAD_FD_DE_MEMORIA.md", ROOT / ".gitattributes")))


def matrices(network, old, new, diagnostics, step):
    if not math.isfinite(step) or step <= 0:
        raise ValueError("positive finite declared FD step required")
    virtual, coefficients = network.effective_history(old, diagnostics["actual_dt_s"])
    dt = coefficients["effective_dt_s"]
    n = network.network
    evaluate = n.increment_evaluator(new.key_v, virtual, dt)
    static = n.joint.evaluator(new.key_v)
    delta = np.array(diagnostics["increment_v"])

    def nodes(d):
        return np.array([math.fsum((a, b, v)) for a, b, v in
            zip(virtual.joint.node_v, virtual.node_low_v, d)])

    cap_j = np.zeros((n.joint.n, n.joint.n))
    for left, right, _, cap, resistance in n.branches:
        g = 1 / (dt / cap + resistance)
        cap_j[left, left] += g
        if right is not None:
            cap_j[right, right] += g
            cap_j[left, right] -= g
            cap_j[right, left] -= g
    dynamic_j = cap_j + n.latch.evaluate(nodes(delta), virtual.latch, dt)["capacitance_f"] / dt
    full = np.zeros_like(dynamic_j)
    static_fd = np.zeros_like(dynamic_j)
    coordinate_errors = []
    for col in range(n.joint.n):
        plus = delta.copy(); minus = delta.copy()
        plus[col] += step; minus[col] -= step
        rp, _ = evaluate(plus, False); rm, _ = evaluate(minus, False)
        xp, xm = nodes(plus), nodes(minus)
        sp, _ = static(xp, jacobian=False); sm, _ = static(xm, jacobian=False)
        full[:, col] = (rp - rm) / (2 * step)
        static_fd[:, col] = (sp - sm) / (2 * step)
        coordinate_errors.append(dict(column=col,
            increment_central_span_relative_error=abs((plus[col] - minus[col]) / (2 * step) - 1),
            absolute_node_central_span_relative_error=abs((xp[col] - xm[col]) / (2 * step) - 1)))
    return dict(full=full, separated=static_fd + dynamic_j, static_fd=static_fd,
                dynamic_j=dynamic_j, coordinate_errors=coordinate_errors)


def map_metrics(mixed, candidate):
    error = np.abs(mixed - candidate) / (1 + np.abs(mixed))
    row, col = np.unravel_index(np.argmax(error), error.shape)
    return dict(node_map_max_scaled_difference=float(error[row, col]),
        maximum_difference_node=int(row), maximum_difference_memory=int(col),
        mixed_value=float(mixed[row, col]), candidate_value=float(candidate[row, col]))


def generate():
    before = hashes(PATHS); env = environment()
    source = json.loads(gzip.decompress(WINDOWS.read_bytes()))
    original = json.loads(gzip.decompress(FD_SOURCE.read_bytes()))
    network = BdfNetwork(200, model_parameters(1, "finite_transit"))
    cases = []
    for window, frozen in zip(source["windows"], original["rows"]):
        if window["name"] != frozen["window"]:
            raise ValueError("window identities must agree")
        old = unpack(network, window["initial"]); reference = window["reference"][0]
        new = unpack(network, reference["history"]); diag = reference["diagnostics"]
        virtual, c = network.effective_history(old, diag["actual_dt_s"])
        _, mixed_j = network.network.increment_evaluator(new.key_v, virtual, c["effective_dt_s"])(
            np.array(diag["increment_v"]))
        b, _, _ = stamps(network, new, c["effective_dt_s"])
        mixed_x = np.array(window["operators"][0]["node_map"])
        case = dict(window=window["name"],initial=window["initial"],reference_step=reference,
            mixed_jacobian_s=mixed_j.tolist(),memory_rhs_s=b.tolist(),mixed_node_map=mixed_x.tolist(),
            original_fd_passed=frozen["passed"], original_fd_scaled_difference=frozen["node_map_max_scaled_difference"],
            rows=[])
        for step in STEPS_V:
            fd = matrices(network, old, new, diag, step)
            for mode, j in zip(MODES, (fd["full"], fd["separated"])):
                row = dict(step_v=step, mode=mode, jacobian_s=j.tolist(), passed=False,
                    coordinate_errors=fd["coordinate_errors"],
                    jacobian_max_scaled_difference=float(np.max(np.abs(j-mixed_j)/(1+np.abs(mixed_j)))))
                try:
                    x, audit = solve(j, b); _, errors = backward_errors(j, b, x)
                    row.update(node_map=x.tolist(),exact_solve=audit,backward_errors=errors,**map_metrics(mixed_x, x))
                    row["passed"] = max(errors.values()) < BACKWARD_GATE and row["node_map_max_scaled_difference"] < MAP_GATE
                    if step == 1e-6 and mode == MODES[0]:
                        row["original_j_and_x_reproduced_exactly"] = bool(np.array_equal(j, frozen["fd_jacobian_s"])
                            and np.array_equal(x, frozen["node_map"]))
                        if not row["original_j_and_x_reproduced_exactly"]:
                            raise ValueError("original 1 uV FD matrix/map must replay exactly")
                except (ValueError, np.linalg.LinAlgError, OverflowError) as exc:
                    row.update(passed=False,error=str(exc))
                case["rows"].append(row)
                print(json.dumps({k:v for k,v in row.items() if k in
                    ("step_v","mode","passed","error","node_map_max_scaled_difference")}|dict(window=window["name"])),flush=True)
        cases.append(case)
    if hashes(PATHS) != before:
        raise ValueError("FD sensitivity sources changed during execution")
    return dict(schema="rf-d/bdf-fd-sensitivity/v1",source_sha256=before,environment=env,cases=cases,
        steps_v=STEPS_V,modes=MODES,binary_and_decimal_backward_gate=BACKWARD_GATE,scaled_map_gate=MAP_GATE,
        original_reset_map_gate_closed=False,previous_reports_modified=False,new_step_selected=False,
        hypothetical_nonlinear_steps=0,diagnostic_only=True,temporal_error_bound_admitted=False,
        temporal_refinement_admitted=False,physical_switching_admitted=False,audio_admitted=False,
        limitation="finite FD sensitivity; separated route shares existing dynamic derivatives; exact solve only of rounded coefficients")


def save(report):
    storage = store(report, OUTPUT)
    summary = {k:v for k,v in report.items() if k != "cases"} | dict(storage=storage,cases=[
        {k:v for k,v in case.items() if k not in ("initial","reference_step","mixed_jacobian_s","memory_rhs_s","mixed_node_map","rows")}
        | dict(rows=[{k:v for k,v in row.items() if k not in ("jacobian_s","node_map","coordinate_errors","exact_solve")}
            | dict(exact_rational_residual_zero=row.get("exact_solve",{}).get("exact_rational_residual_zero"),
                maximum_increment_span_relative_error=max(r["increment_central_span_relative_error"] for r in row["coordinate_errors"]),
                maximum_absolute_node_span_relative_error=max(r["absolute_node_central_span_relative_error"] for r in row["coordinate_errors"]))
            for row in case["rows"]]) for case in report["cases"]])
    SUMMARY.write_text(json.dumps(summary,indent=2,allow_nan=False)+"\n",encoding="utf-8",newline="\n")
    return summary


if __name__ == "__main__":
    save(generate())
