"""Listen to the calibrated RF-D voice at the Oboe chart's Cutoff setting."""
import argparse
import json

import numpy as np

from check_rf_d_oboe_ab import (
    CONTROLS, DEMO, FRAMES, NOTE_WINDOWS, PREROLL, REFERENCE_SHA256, VOICE_DELAY,
    read_reference, score, vibrato_span, write_audition,
)
from check_rf_d_oboe_clarity import RECEIPT as PREVIOUS, spectra
from check_rf_d_playable_filter import filter_score, peak_frequency, rms
from check_rf_d_playable_voice import ROOT, SAMPLE_RATE, main as build_voice, sha, write

AUDITION = ROOT / "artifacts/rf-d-oboe-calibrado-ab.wav"
RECEIPT = ROOT / "evidence/rf_d_oboe_calibrated01.json"


def compare(render, schema, component, reference):
    previous = json.loads(PREVIOUS.read_bytes())
    assert CONTROLS["cutoff"] == 50 and previous["reference_sha256"] == REFERENCE_SHA256
    events = score(schema)
    length = PREROLL + VOICE_DELAY + FRAMES
    audio, _ = render(events, frames=length)
    repeat, _ = render(events, block=480, frames=length)
    assert np.array_equal(audio, repeat)
    candidate = audio[PREROLL + VOICE_DELAY:]
    assert 0.005 < np.max(abs(candidate)) < 0.8
    target = spectra(reference)
    current = spectra(candidate)
    baseline = np.asarray(previous["results"]["baseline"]["harmonic_2_to_6_over_1_db"])
    opened = np.asarray(previous["results"]["cutoff_90"]["harmonic_2_to_6_over_1_db"])
    assert np.all(current[:, 0] - baseline[:, 0] > 18.)
    assert np.mean(abs(target - current)) < np.mean(abs(target - baseline))
    vibrato = dict(minimoog=vibrato_span(reference), rf_d=vibrato_span(candidate))
    assert abs(vibrato["minimoog"] - vibrato["rf_d"]) < 12.

    calibration = []
    for cutoff in (35, 40, 45, 50):
        tone, _ = render(filter_score(cutoff=cutoff), frames=72_000)
        settled = tone[48_000:68_000]
        frequency, purity = peak_frequency(settled)
        assert purity > 0.98 and rms(settled) > 0.01
        calibration.append(dict(cutoff=cutoff, frequency_hz=frequency))
    frequencies = [point["frequency_hz"] for point in calibration]
    assert np.all(np.diff(frequencies) > 0.) and abs(frequencies[1] - 440.) < 3.

    return dict(
        component_sha256=component, source=DEMO, reference_sha256=REFERENCE_SHA256,
        previous_comparison_sha256=sha(PREVIOUS), sample_rate_hz=SAMPLE_RATE,
        settings=CONTROLS, note_windows_ms=NOTE_WINDOWS,
        harmonic_2_to_6_over_1_db=dict(minimoog=target.tolist(), rf_d=current.tolist()),
        mean_harmonic_error_db=dict(baseline=float(np.mean(abs(target - baseline))),
                                    previous_open=float(np.mean(abs(target - opened))),
                                    calibrated=float(np.mean(abs(target - current)))),
        final_vibrato_p95_minus_p05_cents=vibrato, bit_equal_block_frames=[128, 480],
        filter_range_calibration=calibration,
    ), candidate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audition", action="store_true", help="write one level-matched comparison WAV")
    parser.add_argument("--write-report", action="store_true", help="save measurements in evidence/")
    args = parser.parse_args()
    reference = read_reference()

    def inspect(render, schema, component):
        report, candidate = compare(render, schema, component, reference)
        if args.audition:
            takes = {"Minimoog": reference, "RF-D calibrated": candidate}
            report["audition"] = write_audition(takes, tuple(takes) * 2, AUDITION)
        if args.write_report:
            write(RECEIPT, report)
        print(json.dumps(report, indent=2, allow_nan=False))

    build_voice(["--midi"], inspect_audio=inspect)


if __name__ == "__main__":
    main()
