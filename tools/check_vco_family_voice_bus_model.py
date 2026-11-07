"""Verify extended H128 against held-out circuit cycles and materialize its phase table."""
import hashlib
import math

import numpy as np

from affine_evidence import Sources
from check_vco_family_voice_bus import METHODS, PREFIX, PROTOCOL, RESERVED, TRAINING
from prepare_dual_chain import ROOT, sha, write
from prepare_vco_family_voice_bus import LEGACY, TABLE, hermite_image, prediction, training_image
from vco_cv_load_analysis import compare
from vco_family import CHANNELS, complex_coeff, spectral_ports
from vco_family_voice_bus_receipts import read_receipt, receipt_bytes

AREA = ROOT / "tmp/lab-current"
ORACLE = PREFIX + "_oracle01.json"
OWN = "tools/check_vco_family_voice_bus_model.py"


def read_oracle():
    return read_receipt(ORACLE)


def spectral(frequency, model, target):
    case = target["scenario"]
    cv, bus = case["keyboard_v"], case["imposed_mixer_v"]
    fit = prediction(frequency, model, cv, bus)
    actual = fit["c"][:, :65]
    reference = complex_coeff(target["reduction"])
    difference = actual - reference
    panel, currents = spectral_ports(actual, cv, bus)
    ref_panel, ref_currents = spectral_ports(reference, cv, bus)
    counts = np.linalg.norm(reference[:3, 1:9], axis=1)
    panel_delta, cv_delta = panel - ref_panel, currents - ref_currents
    metrics = dict(
        frequency_error_cents=abs(1200. * math.log2(fit["frequency_hz"] / target["reduction"]["frequency_hz"])),
        wave_dc_error_v=np.abs(difference[:3, 0]).tolist(),
        wave_harmonics_relative=(np.linalg.norm(difference[:3, 1:9], axis=1) / counts).tolist(),
        ic1_dc_error_v=float(abs(difference[3, 0])),
        ic1_harmonics_error_v=float(np.linalg.norm(difference[3, 1:9])),
        panel_dc_error_a=float(max(abs(panel_delta[:, 0]))),
        panel_harmonics_error_a=float(max(np.linalg.norm(panel_delta[:, 1:9], axis=1))),
        cv_dc_error_a=float(max(abs(cv_delta[:, 0]))),
        cv_harmonics_error_a=float(max(np.linalg.norm(cv_delta[:, 1:9], axis=1))),
        timing_dc_balance_relative=float(abs(actual[5, 0] + actual[6, 0]) / abs(actual[5, 0])),
    )
    metrics["passed"] = (
        metrics["frequency_error_cents"] <= 1.
        and max(metrics["wave_dc_error_v"]) <= .005 and max(metrics["wave_harmonics_relative"]) <= .02
        and max(metrics["ic1_dc_error_v"], metrics["ic1_harmonics_error_v"]) <= 1e-5
        and max(metrics[key] for key in ("panel_dc_error_a", "panel_harmonics_error_a",
                                         "cv_dc_error_a", "cv_harmonics_error_a")) <= 2e-9
        and metrics["timing_dc_balance_relative"] <= .002
    )
    return dict(cv=cv, bus=bus, **metrics)


def materialize(oracle):
    assert oracle["passed"] and not oracle["rejected"]
    assert oracle["pack_sha256"] == sha(ROOT / oracle["pack"])
    assert [(x["scenario"]["keyboard_v"], x["scenario"]["imposed_mixer_v"]) for x in oracle["training"]] == list(TRAINING)
    assert [(x["scenario"]["keyboard_v"], x["scenario"]["imposed_mixer_v"]) for x in oracle["reserved"]] == list(RESERVED)
    assert [(x["scenario"]["keyboard_v"], x["scenario"]["imposed_mixer_v"], x["scenario"]["method"],
             x["scenario"]["max_step_s"]) for x in oracle["method"]] == list(METHODS)
    frequency, model = training_image(oracle["training"])
    table, bound = hermite_image(frequency, model)
    cases = [spectral(frequency, model, target) for target in (*oracle["reserved"], *oracle["method"])]
    method = [compare(oracle["reserved"][1]["measurements"], item["measurements"]) for item in oracle["method"]]
    return table, frequency, model, cases, method, bound


def main():
    assert not list(AREA.iterdir())
    sources = Sources([OWN, PROTOCOL, "tools/prepare_vco_family_voice_bus.py", LEGACY])
    oracle = read_oracle()
    table, _, _, cases, method, bound = materialize(oracle)
    passed = all(case["passed"] for case in cases)
    (AREA / TABLE).write_bytes(table)
    report = dict(passed=passed, **sources.fields(), oracle_sha256=hashlib.sha256(receipt_bytes(ORACLE)).hexdigest(),
                  oracle_pack_sha256=oracle["pack_sha256"], channels=CHANNELS, validation=cases,
                  independent_method_comparisons=method, table_sha256=sha(AREA / TABLE),
                  table_bytes=len(table), anchor_hermite_voltage_error_bound_v=bound,
                  reserved_data_used_for_fit=False)
    sources.unchanged()
    number = 1
    while (ROOT / f"{PREFIX}_model{number:02}.json").exists():
        number += 1
    write(ROOT / f"{PREFIX}_model{number:02}.json", report)
    for case in cases:
        print("H128_RESERVED", case, flush=True)
    print("H128_MODEL", passed, bound, flush=True)
    raise SystemExit(0 if passed else 1)


if __name__ == "__main__":
    main()
