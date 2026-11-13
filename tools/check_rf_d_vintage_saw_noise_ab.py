"""Test the panel's white noise against the high residual of the vintage saw."""
import argparse
import json

import numpy as np

from check_rf_d_ladder_trapezoidal_ab import RECEIPT as LADDER_REPORT
from check_rf_d_oboe_ab import PREROLL, VOICE_DELAY, score, write_audition
from check_rf_d_playable_filter import rms
from check_rf_d_playable_voice import ROOT, SAMPLE_RATE, main as build_voice, sha, write
from check_rf_d_vintage_saw_ab import FRAMES, NOTES, REFERENCE_SHA256, SETTINGS, read_reference
from check_rf_d_vintage_saw_air import ANALYSIS, BANDS_HZ, RECEIPT as AIR_REPORT, describe, periodic_component

AUDITION = ROOT / "artifacts/rf-d-sierra-ruido-ab.wav"
RECEIPT = ROOT / "evidence/rf_d_vintage_saw_noise_ab01.json"
LEVELS = (1, 2, 3, 4, 5, 7, 10)


def measure(audio):
    periodic, pitch = periodic_component(audio)
    return describe(audio, periodic, pitch)


def residual_error(reference, candidate):
    wanted = np.asarray(reference["residual_band_db_over_signal"])
    actual = np.asarray(candidate["residual_band_db_over_signal"])
    return float(abs(actual - wanted).mean())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-report", action="store_true")
    args = parser.parse_args()
    reference = read_reference()
    ladder = json.loads(LADDER_REPORT.read_bytes())
    assert ladder["reference_sha256"] == REFERENCE_SHA256
    original = [measure(audio) for audio in reference]

    def inspect(render, schema, component):
        baseline = ladder["modes"]["RF-D trapezoidal"]
        assert component == baseline["component_sha256"]
        tunes = [item["tune_cents"] for item in baseline["notes"]]
        start = PREROLL + VOICE_DELAY + 4_800

        def note(index, *, enabled, level=0, block=128):
            midi = NOTES[index][1]
            controls = dict(SETTINGS, tune=tunes[index], noise_enabled=enabled, noise_color=0, noise_level=level)
            events = score(schema, controls=controls, keys=((0, 700, midi),), wheel=())
            audio, _ = render(events, frames=start + FRAMES, block=block)
            return audio[start:]

        trials = []
        for level in LEVELS:
            result = measure(note(0, enabled=True, level=level))
            trials.append(dict(noise_level_percent=level, residual_error_db=residual_error(original[0], result),
                               measurements=result))
        best = min(trials, key=lambda trial: trial["residual_error_db"])
        level = best["noise_level_percent"]
        assert level in LEVELS[1:-1], trials
        takes = {}
        results = {}
        for index, ((label, _), target) in enumerate(zip(NOTES, original, strict=True)):
            clean = note(index, enabled=False)
            loaded = note(index, enabled=True)
            with_noise = note(index, enabled=True, level=level)
            assert np.array_equal(with_noise, note(index, enabled=True, level=level, block=480))
            clean_metrics, loaded_metrics, noise_metrics = map(measure, (clean, loaded, with_noise))
            assert residual_error(target, noise_metrics) < residual_error(target, clean_metrics)
            results[label] = dict(
                minimoog=target, rf_d_clean=clean_metrics, rf_d_noise_connected_at_zero=loaded_metrics,
                rf_d_with_noise=noise_metrics, residual_error_db=residual_error(target, noise_metrics),
                zero_level_load_rms_change_db=float(20. * np.log10(rms(loaded[ANALYSIS]) / rms(clean[ANALYSIS]))),
            )
            takes[f"Minimoog {label}"] = reference[index][ANALYSIS]
            takes[f"RF-D limpio {label}"] = clean[ANALYSIS]
            takes[f"RF-D con ruido {label}"] = with_noise[ANALYSIS]

        report = dict(
            reference_sha256=REFERENCE_SHA256, air_receipt_sha256=sha(AIR_REPORT),
            ladder_receipt_sha256=sha(LADDER_REPORT), component_sha256=component, sample_rate_hz=SAMPLE_RATE,
            oversampling=4, bands_hz=BANDS_HZ, tested_note="La2", held_out_note="La3",
            selected_noise_level_percent=level, fitted_trials=trials, results=results,
            bit_equal_block_frames=[128, 480], audition=write_audition(takes, tuple(takes) * 2, AUDITION),
        )
        if args.write_report:
            write(RECEIPT, report)
        print(json.dumps(dict(level=level, results=results, audition=report["audition"]), indent=2))

    build_voice(["--midi"], inspect_audio=inspect, oversampling=4, trapezoidal_ladder=True)


if __name__ == "__main__":
    main()
