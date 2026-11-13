"""Measure 100 Hz supply sensitivity of the loaded Model D CA3046 oscillator."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
import json
from pathlib import Path

import numpy as np

import check_vco1_loaded_reset_edge as edge
import check_vco_shared_neg4 as shared
import vco1_circuit_reference as vco
import voice_circuit_reference as voice

RECEIPT = vco.ROOT / "evidence/vco_neg10_ripple01.json"
VINTAGE = vco.ROOT / "evidence/rf_d_vintage_saw_edge_timing01.json"
FREQUENCY_HZ = 100.
SETTLE_S = .024
SIGNALS = ("v(ramp_c1)", "v(saw_output_9b)", "v(neg4_ref)", "v(neg10_test)")
TRIALS = (
    ("quiet", "rail", 0., .5e-6, 1e-5),
    ("rail-2mv", "rail", .002, .5e-6, 1e-5),
    ("rail-8mv", "rail", .008, .5e-6, 1e-5),
    ("divider-8mv", "divider", .008, .5e-6, 1e-5),
    ("rail-8mv-fine", "rail", .008, .25e-6, 5e-6),
    ("quiet-fine", "rail", 0., .25e-6, 5e-6),
)


def deck(scene, export, route, peak_v, reltol):
    text, metadata = edge.deck(scene, export, 0.)
    supply = "Vneg10 NEG10_V 0 -10"
    divider = "RR166 NEG10_V NEG4_REF 6200"
    assert text.count(supply) == text.count(divider) == 1 and "CC14 NEG4_REF 0 " in text
    source = f"Vneg10_test NEG10_TEST 0 SIN(0 {peak_v:.17g} {FREQUENCY_HZ:.17g})"
    if route == "rail":
        # NEG10_TEST is an ideal series perturbation of the entire -10 V pin.
        supplies = ["Vneg10 NEG10_V NEG10_TEST -10"]
    else:
        # Apply the same stimulus only to the supply side of R166.
        text = text.replace(divider, divider.replace("NEG10_V", "NEG10_DIV"), 1)
        supplies = [supply, "Vneg10_div NEG10_DIV NEG10_TEST -10"]
    text = text.replace(supply, "\n".join([*supplies, source]), 1)
    assert "reltol=1e-7" in text and "vntol=1e-8" in text
    text = text.replace("reltol=1e-7", f"reltol={reltol:.17g}", 1)
    text = text.replace("vntol=1e-8", "vntol=1e-7", 1)
    metadata["rail_perturbation"] = dict(route=route, peak_v=peak_v, reltol=reltol, vntol=1e-7)
    metadata["source_sha256"][Path(__file__).relative_to(vco.ROOT).as_posix()] = vco.sha(Path(__file__))
    return text.replace(" ".join(edge.VECTORS), " ".join(SIGNALS)), metadata


def edges(raw):
    t, ramp, saw = raw[:, :3].T
    reset = vco.crossings(t, ramp, -2., True)
    reset = reset[(reset > SETTLE_S) & (reset + 2e-6 < t[-1])]
    assert len(reset) >= 9
    middle, local_delay = [], []
    for crossing in reset:
        window = (t > crossing - 2e-6) & (t < crossing + 1.5e-6)
        before, after = np.interp(crossing + np.array([-1., 1.]) * 1e-6, t, saw)
        midpoint = edge.single_crossing(t[window], saw[window], (before + after) / 2.)
        prior = (t > crossing - .001) & (t < crossing - 2e-6)
        anchor = edge.single_crossing(t[prior], ramp[prior], -3.8, False)
        middle.append(midpoint)
        local_delay.append(midpoint - anchor)
    return 1. / np.diff(reset).mean(), np.asarray(middle), np.asarray(local_delay)


def harmonic(time, signal):
    angle = 2. * np.pi * FREQUENCY_HZ * time
    basis = np.column_stack((np.ones_like(time), time - time.mean(), np.sin(angle), np.cos(angle)))
    coeff = np.linalg.lstsq(basis, signal, rcond=None)[0]
    fitted = basis @ coeff
    return dict(sine=float(coeff[-2]), cosine=float(coeff[-1]), peak=float(np.linalg.norm(coeff[-2:])),
                error_rms=float(np.sqrt(np.mean((signal - fitted)**2))))


def experiment(note, reference, vintage, shared_reference):
    settings = dict(reference["gear_250ns"]["run"]["scenario"])
    oscillator = vco.Scenario(**settings.pop("oscillator"))
    extra_current = sum(branch["trap500"]["load_mean_a"]
                        for branch in shared_reference["isolated_loads"].values())
    oscillator = replace(oscillator, duration_s=.124, method="trap", external_neg4_load_a=extra_current)
    scene = voice.Scenario(oscillator=oscillator, **settings)
    vintage_peak_us = vintage["fits"]["100"]["fitted_peak_us"]
    trials = {}
    quiet = {}
    for name, route, peak, step, reltol in sorted(TRIALS, key=lambda item: item[2]):
        label = f"neg10-edge-{note.lower()}-{name}"
        trial = replace(scene, oscillator=replace(scene.oscillator, max_step_s=step))
        raw, info = shared.circuit_run(trial, label, lambda s, p: deck(s, p, route, peak, reltol), SIGNALS)
        frequency, middle, local_delay = edges(raw)
        time = np.arange(SETTLE_S, oscillator.duration_s, 5e-6)
        rail, stimulus = [np.interp(time, raw[:, 0], raw[:, k]) for k in (-2, -1)]
        response = dict(frequency_hz=frequency, edge_count=len(middle), run=info,
                        reference_100hz_v=harmonic(time, rail), stimulus_100hz_v=harmonic(time, stimulus),
                        route=route, reltol=reltol, peak_v=peak)
        if peak:
            nominal, nominal_local = quiet[step]
            assert len(middle) == len(nominal) and max(abs(middle - nominal)) < .1 / frequency
            assert abs(response["stimulus_100hz_v"]["peak"] / peak - 1.) < .0001
            response["edge_shift_s"] = harmonic(nominal, middle - nominal)
            response["local_delay_s"] = harmonic(nominal, local_delay - nominal_local)
            response["edge_sensitivity_s_per_v"] = response["edge_shift_s"]["peak"] / peak
            response["local_sensitivity_s_per_v"] = response["local_delay_s"]["peak"] / peak
        else:
            quiet[step] = middle, local_delay
            response["edge_timing_floor_s"] = harmonic(middle, middle - np.arange(len(middle)) / frequency)
        trials[name] = response
        shared.retire(label)
        print(note, name, json.dumps({k: v for k, v in response.items() if k != "run"}), flush=True)
    small, large, fine = [trials[name]["edge_sensitivity_s_per_v"]
                          for name in ("rail-2mv", "rail-8mv", "rail-8mv-fine")]
    assert abs(small / large - 1.) < .05
    assert abs(fine / large - 1.) < .05
    return dict(vintage_100hz_peak_us=vintage_peak_us, trials=trials,
                equivalent_full_rail_peak_v=[peak * 1e-6 / fine for peak in vintage_peak_us])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-report", action="store_true")
    args = parser.parse_args()
    reference, vintage, loads = map(vco.read, (edge.RECEIPT, VINTAGE, shared.RECEIPT))
    with ThreadPoolExecutor(max_workers=2) as pool:
        trials = {note: pool.submit(experiment, note, ref, vintage["notes"][note], loads["notes"][note])
                  for note, ref in reference["notes"].items()}
        results = {note: trial.result() for note, trial in trials.items()}
    report = dict(schema="rf-d/vco-neg10-ripple/v1", stimulus_frequency_hz=FREQUENCY_HZ,
                  edge_window_settle_s=SETTLE_S, executable_sha256=vco.EXPECTED_EXE_SHA,
                  vintage_sha256=vco.sha(VINTAGE), edge_sha256=vco.sha(edge.RECEIPT),
                  shared_load_sha256=vco.sha(shared.RECEIPT), notes=results)
    if args.write_report:
        RECEIPT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
