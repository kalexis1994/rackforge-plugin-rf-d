"""Measure reset sensitivity to current drawn from the shared −4 V reference."""
import argparse
from dataclasses import replace
import json

import numpy as np

import check_vco1_loaded_reset_edge as edge
import vco1_circuit_reference as vco
import voice_circuit_reference as voice

BASE = edge.RECEIPT
RECEIPT = edge.ROOT / "evidence/vco1_loaded_reset_neg401.json"
LOAD_A = 1e-6
SIGNALS = (*edge.VECTORS, "v(neg4_ref)")
DELAY = "saw_9b_from_c1_minus_3p8_v_s"


def deck(scene, export):
    text, metadata = edge.deck(scene, export, offset_v=0.)
    old = " ".join(edge.VECTORS)
    assert text.count(old) == 2
    return text.replace(old, " ".join(SIGNALS)), metadata


def sweep(note, scene, load_a, observed_shift_s, band):
    label = f"{note.lower()}-reset-neg4-{'plus' if load_a > 0 else 'minus'}"
    scene = replace(scene, oscillator=replace(scene.oscillator, external_neg4_load_a=load_a))
    raw, run = voice.run(scene, label, edge.LAB, edge.EXE, netlist_factory=deck, vectors=SIGNALS)
    assert run["source_sha256"] == run["source_sha256_after"] and run["trajectory_complete"]
    metrics = edge.edge_metrics(raw[:, :-1], .015, observed_shift_s, band)
    resets = [row["c1_reset_s"] for row in metrics["resets"]]
    ref = np.interp(np.asarray(resets) - 100e-6, raw[:, 0], raw[:, -1])
    result = dict(load_a=load_a, frequency_hz=metrics["frequency_hz"],
                  delay_s=edge.median(metrics, DELAY), neg4_ref_before_reset_v=float(np.median(ref)),
                  raw_sha256=run["raw_export_sha256"], deck_sha256=run["deck_sha256"], rows=run["rows"])
    for suffix in ("cir", "log", "json", "txt", "txt.gz"):
        (edge.LAB / f"{label}.{suffix}").unlink()
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-report", action="store_true")
    args = parser.parse_args()
    base = vco.read(BASE)
    assert vco.sha(edge.ROOT / "tools/check_vco1_loaded_reset_edge.py") == (
        base["source_sha256"]["tools/check_vco1_loaded_reset_edge.py"])
    report = dict(source_sha256=vco.sha(BASE), executable_sha256=vco.EXPECTED_EXE_SHA,
                  current_sweep_a=[-LOAD_A, LOAD_A], notes={})
    for note, baseline in base["notes"].items():
        nominal = baseline["gear_250ns"]
        config = dict(nominal["run"]["scenario"])
        scene = voice.Scenario(oscillator=vco.Scenario(**config.pop("oscillator")), **config)
        measured_s = baseline["vintage_edge_timing_std_s"]
        minus, plus = [sweep(note, scene, load, measured_s, base["comparison_band_hz"])
                       for load in (-LOAD_A, LOAD_A)]
        delay_center = (plus["delay_s"] + minus["delay_s"]) / 2.
        center_error_s = abs(delay_center - edge.median(nominal, DELAY))
        delta_s = (plus["delay_s"] - minus["delay_s"]) / 2.
        ref_delta_v = (plus["neg4_ref_before_reset_v"] - minus["neg4_ref_before_reset_v"]) / 2.
        assert ref_delta_v < 0. and center_error_s < .02 * abs(delta_s)
        report["notes"][note] = dict(
            minus=minus, plus=plus, delay_change_s_per_a=delta_s / LOAD_A,
            neg4_ref_change_v_per_a=ref_delta_v / LOAD_A, nominal_vs_center_error_s=center_error_s,
            equivalent_current_a=measured_s * LOAD_A / abs(delta_s),
            equivalent_neg4_ref_change_v=measured_s * abs(ref_delta_v / delta_s),
        )
        print(note, json.dumps(report["notes"][note]), flush=True)
    if args.write_report:
        RECEIPT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
