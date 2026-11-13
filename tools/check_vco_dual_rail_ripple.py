"""Compare correlated +10 V and -10 V ripple at the loaded VCO1."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
import json
from pathlib import Path

import numpy as np

import check_vco_neg10_r37 as tuning
import check_vco_neg10_ripple as ripple
import check_vco_shared_neg4 as shared
import vco1_circuit_reference as vco
import voice_circuit_reference as voice

RECEIPT = vco.ROOT / "evidence/vco_dual_rail_ripple01.json"
SIGNALS = (*ripple.SIGNALS, "v(pos10_test)")
PEAK_V = tuning.AMPLITUDE_V
CASES = (
    ("quiet", 0., 0., 0.),
    ("positive", PEAK_V, 0., 0.),
    ("same-phase", PEAK_V, PEAK_V, 0.),
    ("opposite-phase", PEAK_V, PEAK_V, 180.),
    ("quadrature", PEAK_V, PEAK_V, 90.),
)


def deck(scene, export, positive, negative, phase_deg, reltol):
    text, metadata = ripple.deck(scene, export, "rail", negative, reltol)
    pos = "Vpos10 POS10_V 0 10"
    neg = f"Vneg10_test NEG10_TEST 0 SIN(0 {negative:.17g} {ripple.FREQUENCY_HZ:.17g})"
    assert text.count(pos) == text.count(neg) == 1
    text = text.replace(pos, "Vpos10 POS10_V POS10_TEST 10\n"
                        f"Vpos10_test POS10_TEST 0 SIN(0 {positive:.17g} {ripple.FREQUENCY_HZ:.17g})", 1)
    text = text.replace(neg, neg[:-1] + f" 0 0 {phase_deg:.17g})", 1)
    source = Path(__file__)
    metadata["source_sha256"][source.relative_to(vco.ROOT).as_posix()] = vco.sha(source)
    return text.replace(" ".join(ripple.SIGNALS), " ".join(SIGNALS)), metadata


def phasor(fit):
    return complex(fit["sine"], fit["cosine"])


def record(value):
    return dict(sine=float(value.real), cosine=float(value.imag), peak=float(abs(value)),
                phase_deg=float(np.angle(value, deg=True)))


def measure(note, scenario, name, positive, negative, phase_deg, reltol):
    label = f"dual-rail-{note.lower()}-{name}"
    raw, run = shared.circuit_run(
        scenario, label, lambda s, p: deck(s, p, positive, negative, phase_deg, reltol), SIGNALS)
    frequency, middle, local = ripple.edges(raw)
    time = np.arange(ripple.SETTLE_S, scenario.oscillator.duration_s, 5e-6)
    neg, pos = [phasor(ripple.harmonic(time, np.interp(time, raw[:, 0], raw[:, col]))) for col in (-2, -1)]
    assert abs(pos - positive) < 2e-8
    assert abs(neg - negative * np.exp(1j * np.deg2rad(phase_deg))) < 2e-8
    shared.retire(label)
    print(note, name, len(middle), flush=True)
    return middle, local, dict(frequency_hz=frequency, negative_v=record(neg), positive_v=record(pos),
                               edge_count=len(middle), reltol=reltol, run=run)


def summarize(note, runs, negative_reference):
    quiet, quiet_local, zero = runs.pop("quiet")
    fine, fine_local, zero_fine = runs.pop("quiet-fine")
    results = dict(quiet=zero, quiet_fine=zero_fine)
    for name, (middle, local, data) in runs.items():
        base, base_local = (fine, fine_local) if name.endswith("-fine") else (quiet, quiet_local)
        assert len(middle) == len(base)
        assert max(abs(middle - base)) < .1 / data["frequency_hz"]
        data["edge_shift_s"] = ripple.harmonic(base, middle - base)
        data["local_delay_s"] = ripple.harmonic(base, local - base_local)
        results[name] = data

    negative = phasor(negative_reference["rail"]["edge_shift_s"])
    positive = phasor(results["positive"]["edge_shift_s"])
    for name in ("same-phase", "opposite-phase", "quadrature", "opposite-phase-fine"):
        data = results[name]
        predicted = (positive * phasor(data["positive_v"]) + negative * phasor(data["negative_v"])) / PEAK_V
        measured = phasor(data["edge_shift_s"])
        data["predicted_edge_shift_s"] = record(predicted)
        data["complex_prediction_error_s"] = abs(measured - predicted)
        assert abs(measured - predicted) < .05 * (abs(positive) + abs(negative))
    coarse = phasor(results["opposite-phase"]["edge_shift_s"])
    refined = phasor(results["opposite-phase-fine"]["edge_shift_s"])
    assert abs(coarse - refined) < .02 * (abs(positive) + abs(negative))
    print(note, json.dumps({name: data["edge_shift_s"] for name, data in results.items()
                            if "edge_shift_s" in data}), flush=True)
    return dict(negative_only_edge_shift_s=record(negative), trials=results)


def contrast(notes, vintage):
    # The same two rail phasors have to explain both notes.
    positive = np.array([phasor(row["trials"]["positive"]["edge_shift_s"]) for row in notes.values()]) / PEAK_V
    negative = np.array([phasor(row["negative_only_edge_shift_s"]) for row in notes.values()]) / PEAK_V
    names = list(notes)
    assert names == ["La2", "La3"]
    band_peaks = np.array([vintage["notes"][note]["fits"]["100"]["fitted_peak_us"] for note in names]) * 1e-6
    ratios = band_peaks[0] / band_peaks[1]

    # With an arbitrary complex ratio r=V+/V-, Y2/Y3=(H2- + H2+ r)/(H3- + H3+ r).
    # The allowed magnitude ratio is bounded above by the larger estimate across bands.
    target_ratio = float(max(ratios))
    equal_min = float((abs(negative[0]) - abs(positive[0])) / (abs(negative[1]) + abs(positive[1])))
    equal_max = float((abs(negative[0]) + abs(positive[0])) / (abs(negative[1]) - abs(positive[1])))
    center = -negative[0] / positive[0]
    a = abs(positive[0])**2 - target_ratio**2 * abs(positive[1])**2
    b = positive[0].conjugate() * negative[0] - target_ratio**2 * positive[1].conjugate() * negative[1]
    c = abs(negative[0])**2 - target_ratio**2 * abs(negative[1])**2
    assert a > 0.
    disk_center = -b / a
    disk_radius = float(np.sqrt(abs(disk_center)**2 - c / a))
    equality = {}
    for sign, name in ((1, "same_phase"), (-1, "opposite_phase")):
        response = negative + sign * positive
        equality[name] = dict(la2_over_la3=float(abs(response[0] / response[1])),
                              la3_matching_input_peak_v=(band_peaks[1] / abs(response[1])).tolist(),
                              la2_predicted_peak_us=(abs(response[0] / response[1]) * band_peaks[1] * 1e6).tolist())
    return dict(vintage_same_band_ratios=ratios.tolist(), max_observed_ratio=target_ratio,
                equal_amplitude_ratio_bounds=[equal_min, equal_max],
                exact_la2_cancellation_ratio=record(center),
                ratios_matching_or_below_max_observed=dict(center=record(disk_center), radius=disk_radius,
                                                           equal_amplitude_possible=bool(abs(abs(disk_center) - 1.) <= disk_radius)),
                equal_amplitude_cases=equality)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-report", action="store_true")
    args = parser.parse_args()
    reference, negative, vintage = map(vco.read, (ripple.RECEIPT, tuning.RECEIPT, ripple.VINTAGE))
    with ThreadPoolExecutor(max_workers=3) as pool:
        queued = {}
        for note, row in reference["notes"].items():
            settings = dict(row["trials"]["quiet"]["run"]["scenario"])
            osc = vco.Scenario(**settings.pop("oscillator"))
            scene = voice.Scenario(oscillator=osc, **settings)
            fine = replace(scene, oscillator=replace(osc, max_step_s=.25e-6))
            queued[note] = {case[0]: pool.submit(measure, note, scene, *case, 1e-5) for case in CASES}
            queued[note]["quiet-fine"] = pool.submit(measure, note, fine, "quiet-fine", 0., 0., 0., 5e-6)
            queued[note]["opposite-phase-fine"] = pool.submit(
                measure, note, fine, "opposite-phase-fine", *CASES[3][1:], 5e-6)
        notes = {note: summarize(note, {case: task.result() for case, task in tasks.items()},
                                 negative["notes"][note])
                 for note, tasks in queued.items()}
    report = dict(schema="rf-d/vco-dual-rail-ripple/v1", stimulus_frequency_hz=ripple.FREQUENCY_HZ,
                  input_peak_v=PEAK_V, executable_sha256=vco.EXPECTED_EXE_SHA,
                  negative_reference_sha256=vco.sha(tuning.RECEIPT), vintage_sha256=vco.sha(ripple.VINTAGE),
                  circuit_reference_sha256=vco.sha(ripple.RECEIPT), notes=notes,
                  contrast=contrast(notes, vintage))
    print(json.dumps(report["contrast"], indent=2), flush=True)
    if args.write_report:
        RECEIPT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
