"""Fixed circuit/convergence scenes for the conditional CA3046 oscillator."""
from dataclasses import asdict, replace
import argparse
import json
import math
from pathlib import Path

import numpy as np

from vco1_circuit_reference import ROOT, Scenario, VECTORS, run, measure, sha

GATES = dict(frequency_refinement_cents=1.0, output_extrema_refinement_v=.005,
             period_spread_relative=1e-5, cycle_charge_relative=.002)


def scenarios():
    nominal = Scenario(duration_s=.03)
    cases = {}
    for c4 in (10e-12, 100e-12):
        prefix = "c4-10" if c4 == 10e-12 else "c4-100"
        for ns in (500, 250, 125):
            cases[f"{prefix}-gear{ns}"] = replace(nominal, c4_f=c4, max_step_s=ns * 1e-9)
        cases[f"{prefix}-trap125"] = replace(nominal, c4_f=c4, max_step_s=125e-9, method="trap")
    cases["keyboard-low"] = replace(nominal, keyboard_v=-3.1, max_step_s=125e-9)
    cases["keyboard-high"] = replace(nominal, keyboard_v=-1.1, max_step_s=125e-9)
    for contact in (10, 11, 12):
        cases[f"pulse-{contact}"] = replace(nominal, upper_contact=4, lower_contact=contact, max_step_s=125e-9)
    cases["triangle-open-pulse"] = replace(nominal, upper_contact=1, lower_contact=8, max_step_s=125e-9)
    return cases


def observations(raw, scene):
    m = measure(raw, settle_s=.015)
    t = raw[:, 0]
    edges = np.array(m["reset_crossings_s"])
    a, b = edges[-3], edges[-1]
    # Include the actual window endpoints when integrating C1 current balance.
    knots = np.r_[a, t[(t > a) & (t < b)], b]
    qa, q10 = [np.interp(knots, t, raw[:, k]) for k in (15, 16)]
    dq = float(np.trapezoid(-qa-q10, knots))
    dv = float(np.interp(b, t, raw[:, 1]) - np.interp(a, t, raw[:, 1]))
    timing_charge_c = 1e-8 * dv
    # Qa/Q10 collector currents omit the very small Q7 gate charge/current.
    throughput = float(np.trapezoid(np.abs(qa), knots))
    m["cycle_charge_check"] = dict(integrated_qa_q10_c=dq, c1_delta_c=timing_charge_c,
        relative_imbalance=abs(dq-timing_charge_c)/throughput,
        excludes="Q7 gate displacement/leakage and numerical quadrature; finite observation check, not a continuous proof")
    return m


def comparison(a, b):
    cents = abs(1200 * math.log2(a["frequency_hz"]/b["frequency_hz"]))
    differences = {wave: max(abs(a["windows_v"][wave][edge]-b["windows_v"][wave][edge])
                            for edge in ("min_v", "max_v")) for wave in VECTORS[2:5]}
    return dict(frequency_error_cents=cents, output_extrema_error_v=differences,
        phase_aligned_peak_v=float(np.max(np.abs(np.array(a["cycle_v"]) - np.array(b["cycle_v"])))),
        phase_alignment="Each trace uses its last actual ramp reset-to-reset cycle. Peak difference is diagnostic, not a same-clock error gate.")


def validate(report):
    if report["gates"] != GATES or set(report["cases"]) != set(scenarios()):
        raise ValueError("frozen gates/scenario inventory changed")
    for label, case in report["cases"].items():
        if case["scenario"] != asdict(scenarios()[label]):
            raise ValueError("scene changed")
        r, m = case["receipt"], case["measurements"]
        if not r["trajectory_complete"] or r["exit_code"] != 0 or r["source_sha256"] != r["source_sha256_after"]:
            raise ValueError("incomplete or changing-source run")
        if m["period_spread_relative"] > GATES["period_spread_relative"]:
            raise ValueError("settled periodicity gate failed")
        if m["cycle_charge_check"]["relative_imbalance"] > GATES["cycle_charge_relative"]:
            raise ValueError("C1 integrated current check failed")
    for pair in report["comparisons"].values():
        if pair["frequency_error_cents"] > GATES["frequency_refinement_cents"] or max(pair["output_extrema_error_v"].values()) > GATES["output_extrema_refinement_v"]:
            raise ValueError("fine refinement/method gate failed")
    if not report["cases"]["keyboard-low"]["measurements"]["frequency_hz"] < report["cases"]["c4-10-gear125"]["measurements"]["frequency_hz"] < report["cases"]["keyboard-high"]["measurements"]["frequency_hz"]:
        raise ValueError("keyboard direction is wrong")
    duties = [report["cases"][f"pulse-{i}"]["measurements"]["pulse_negative_duty"] for i in (10, 11, 12)]
    if not 0 < duties[2] < duties[1] < duties[0] < 1:
        raise ValueError("pulse selector direction/domain gate failed")


def generate(bank):
    exe = ROOT / "references-local/ngspice46/runtime/Spice64/bin/ngspice_con.exe"
    work = ROOT / "references-local/vco1-circuit" / bank
    if work.exists():
        raise ValueError("fresh bank required")
    work.mkdir(parents=True)
    report = dict(schema="rf-d/vco1-circuit-bank/v1", gates=GATES, bank=bank, cases={}, comparisons={},
        source_sha256={p.relative_to(ROOT).as_posix():sha(p) for p in (Path(__file__), ROOT/"docs/VCO1_ORACULO_CIRCUITO.md")},
        scope="Conditional single oscillator, imposed board controls/rails/mixer and unknown extra -4 V rail load; no hardware fidelity, native voice or real-time claim")
    for label, scene in scenarios().items():
        raw, receipt = run(scene, label, work, exe)
        metrics = observations(raw, scene)
        report["cases"][label] = dict(scenario=asdict(scene), receipt=receipt, measurements=metrics)
        (work/"partial-report.json").write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8", newline="\n")
        print(json.dumps(dict(scene=label, frequency_hz=metrics["frequency_hz"], duty=metrics["pulse_negative_duty"], charge_error=metrics["cycle_charge_check"]["relative_imbalance"])), flush=True)
    for prefix in ("c4-10", "c4-100"):
        def m(suffix):
            return report["cases"][prefix+"-"+suffix]["measurements"]
        report["comparisons"][prefix+"-refinement"] = comparison(m("gear250"),m("gear125"))
        report["comparisons"][prefix+"-method"] = comparison(m("gear125"),m("trap125"))
    try:
        validate(report)
        report["gates_passed"] = True
    except ValueError as error:
        report.update(gates_passed=False, error=str(error))
    report["source_sha256_after"] = {p:sha(ROOT/p) for p in report["source_sha256"]}
    (work/"report.json").write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8", newline="\n")
    return report


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--bank", required=True)
    args = p.parse_args()
    if not args.bank or any(c not in "abcdefghijklmnopqrstuvwxyz0123456789_-" for c in args.bank):
        p.error("safe fresh bank name required")
    result = generate(args.bank)
    print(json.dumps({"gates_passed":result["gates_passed"],"comparisons":result["comparisons"],"error":result.get("error")},indent=2))
    if not result["gates_passed"]:
        raise SystemExit(1)
