"""Replay the measured keyboard CV phasor through the loaded VCO1."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
import json
from pathlib import Path

import numpy as np

import check_keyboard_cv_ripple as keyboard
import check_vco_dual_rail_ripple as dual
import check_vco_neg10_r37 as tuning
import check_vco_neg10_ripple as ripple
import check_vco_shared_neg4 as shared
import vco1_circuit_reference as vco
import voice_circuit_reference as voice

RECEIPT = vco.ROOT / "evidence/keyboard_cv_vco_ripple01.json"
VINTAGE = vco.ROOT / "evidence/rf_d_vintage_saw_sidebands01.json"
SIGNALS = ("v(ramp_c1)", "v(saw_output_9b)", "v(keyboard)", "v(ic1_sum)")
CALIBRATION_PEAK_V = .004


def deck(scene, export, cv):
    text, metadata = ripple.deck(scene, export, "rail", 0., 1e-5)
    dc = f"VKEYBOARD KEYBOARD 0 {scene.oscillator.keyboard_v:.17g}"
    assert text.count(dc) == 1 and "RR27 KEYBOARD IC1_SUM 51100" in text
    source = (dc.replace("KEYBOARD 0", "KEYBOARD CV_RIPPLE") +
              f"\nVcv_ripple CV_RIPPLE 0 SIN(0 {abs(cv):.17g} {ripple.FREQUENCY_HZ:.17g} 0 0 "
              f"{np.angle(cv, deg=True):.17g})")
    path = Path(__file__)
    metadata["source_sha256"][path.relative_to(vco.ROOT).as_posix()] = vco.sha(path)
    return text.replace(dc, source, 1).replace(" ".join(ripple.SIGNALS), " ".join(SIGNALS)), metadata


def cv_phasor(row, state):
    return dual.phasor(row["windows"][state]["harmonic"]["v(keyboard)"])


def experiment(note, ref, keyboards, vintage_peaks_us):
    settings = dict(ref["run"]["scenario"])
    scene = voice.Scenario(oscillator=vco.Scenario(**settings.pop("oscillator")), **settings)
    # Reserve one measured track and hold case. Reuse the full tap sweep below.
    tap = {"La2": 16, "La3": 28}[note]
    anchor = keyboards[f"{tap}-nominal-20"]["opposite"]
    trials = [("quiet", 0j), ("calibration", complex(CALIBRATION_PEAK_V)),
              ("track", cv_phasor(anchor, "track")), ("hold", cv_phasor(anchor, "hold"))]
    results = {}
    for name, cv in trials:
        label = f"key-cv-vco-{note.lower()}-{name}"
        raw, run = shared.circuit_run(scene, label, lambda s, p: deck(s, p, cv), SIGNALS)
        freq, middle, _ = ripple.edges(raw)
        t = np.arange(ripple.SETTLE_S, scene.oscillator.duration_s, 5e-6)
        cv_fit = keyboard.fit(t, np.interp(t, raw[:, 0], raw[:, 3]))
        current = (raw[:, 3] - raw[:, 4]) / 51100.
        current_fit = keyboard.fit(t, np.interp(t, raw[:, 0], current))
        assert abs(cv_fit - cv) < 1e-8
        if name == "quiet":
            base = middle
            shift = 0j
            baseline_current = current_fit
        else:
            assert len(middle) == len(base) and max(abs(middle - base)) < .1 / freq
            shift = keyboard.fit(base, middle - base)
        results[name] = dict(frequency_hz=freq, edge_count=len(middle), cv_v=dual.record(cv_fit),
                             r27_current_a=dual.record(current_fit - baseline_current),
                             edge_shift_s=dual.record(shift), run=run)
        shared.retire(label)
        print(note, name, results[name]["cv_v"]["peak"], results[name]["edge_shift_s"]["peak"], flush=True)
    gain = dual.phasor(results["calibration"]["edge_shift_s"]) / CALIBRATION_PEAK_V
    for state in keyboard.WINDOWS:
        observed = dual.phasor(results[state]["edge_shift_s"])
        expected = gain * dual.phasor(results[state]["cv_v"])
        error = abs(observed - expected)
        results[state]["predicted_edge_shift_s"] = dual.record(expected)
        results[state]["error_s"] = error
        assert error < 8e-9 + .06 * abs(expected), (note, state, expected, observed)
    predicted = {
        label: {
            name: {state: dual.record(gain * cv_phasor(row, state)) for state in keyboard.WINDOWS}
            for name, row in cases.items() if name != "quiet"
        }
        for label, cases in keyboards.items()
    }
    return dict(trials=results, reserved_tap=tap, edge_gain_s_per_v=dual.record(gain),
                predicted_edge_shifts_s=predicted, vintage_peaks_us=vintage_peaks_us,
                cv_required_peak_v=[float(peak*1e-6/abs(gain)) for peak in vintage_peaks_us])


def comparison(notes, dual_report, tuning_report):
    ranges = []
    for low_tap, high_tap in zip(keyboard.PICKOFFS[:-1], keyboard.PICKOFFS[1:], strict=True):
        for profile in ("nominal", "deep-cutoff"):
            step = 20 if profile == "nominal" else 40
            for state in keyboard.WINDOWS:
                case = dict(taps=[low_tap, high_tap], profile=profile, state=state, notes={})
                for note, tap in (("La2", low_tap), ("La3", high_tap)):
                    label = f"{tap}-{profile}-{step}"
                    by_source = notes[note]["predicted_edge_shifts_s"][label]
                    negative = dual.phasor(tuning_report["notes"][note]["rail"]["edge_shift_s"])
                    positive = dual.phasor(dual_report["notes"][note]["trials"]["positive"]["edge_shift_s"])
                    # Same sign convention as the plate 2 opposite-phase stimulus.
                    direct = positive - negative
                    from_keyboard = dual.phasor(by_source["opposite"][state])
                    positive_path = positive + dual.phasor(by_source["positive"][state])
                    negative_path = negative + dual.phasor(by_source["negative"][state])
                    closure = abs((positive_path - negative_path) - (direct + from_keyboard))
                    case["notes"][note] = dict(
                        cv_only=dual.record(from_keyboard), summed_edge_s=dual.record(direct + from_keyboard),
                        linear_positive_rail_s=dual.record(positive_path),
                        linear_negative_rail_s=dual.record(negative_path), opposite_phase_closure_s=closure,
                    )
                la2, la3 = (case["notes"][note] for note in ("La2", "La3"))
                case["cv_ratio"] = la2["cv_only"]["peak"] / la3["cv_only"]["peak"]
                case["summed_ratio"] = la2["summed_edge_s"]["peak"] / la3["summed_edge_s"]["peak"]
                # Triangle inequality bounds the linear response for any phase
                # when both rails have the tested peak voltage.
                bounds = []
                for row in (la2, la3):
                    pos, neg = (row[f"linear_{rail}_rail_s"]["peak"] for rail in ("positive", "negative"))
                    bounds.append((abs(pos - neg), pos + neg))
                case["equal_rail_phase_ratio_bounds"] = [bounds[0][0] / bounds[1][1],
                                                        bounds[0][1] / bounds[1][0]]
                ranges.append(case)
    return ranges


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-report", action="store_true")
    args = parser.parse_args()
    keyboards, vintage, both, neg = map(vco.read, (keyboard.RECEIPT, VINTAGE, dual.RECEIPT, tuning.RECEIPT))
    with ThreadPoolExecutor(max_workers=2) as pool:
        tasks = {}
        for note, ref in both["notes"].items():
            timing = vintage["notes"][note]["simultaneous_timing"]["timing_peak_us"]
            tasks[note] = pool.submit(experiment, note, ref["trials"]["quiet"], keyboards["notes"],
                                      [band[0] for band in timing])
        results = {note: task.result() for note, task in tasks.items()}
    report = dict(schema="rf-d/keyboard-cv-vco-ripple/v1", stimulus_frequency_hz=ripple.FREQUENCY_HZ,
                  calibration_peak_v=CALIBRATION_PEAK_V, keyboard_sha256=vco.sha(keyboard.RECEIPT),
                  vintage_sha256=vco.sha(VINTAGE), supply_contrast_sha256=vco.sha(dual.RECEIPT),
                  negative_reference_sha256=vco.sha(tuning.RECEIPT), notes=results,
                  opposite_rail_comparison=comparison(results, both, neg))
    if args.write_report:
        RECEIPT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
