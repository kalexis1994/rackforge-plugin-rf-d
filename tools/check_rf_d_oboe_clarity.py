"""Isolate the audible cutoff error in the transcribed Oboe comparison."""
import argparse
import json

import numpy as np

from check_rf_d_oboe_ab import (
    CONTROLS, DEMO, FRAMES, KEYS, NOTE_WINDOWS, PREROLL, REFERENCE_SHA256, VOICE_DELAY,
    frames_at, read_reference, score, write_audition,
)
from check_rf_d_playable_filter import filter_score, peak_frequency, rms
from check_rf_d_playable_voice import ROOT, SAMPLE_RATE, main as build_voice, write

AUDITION = ROOT / "artifacts/rf-d-oboe-cutoff-ab.wav"
RECEIPT = ROOT / "evidence/rf_d_oboe_clarity01.json"
SERVICE_MANUAL = "https://www.vintagesynthparts.com/wp-content/uploads/2016/08/MINIMOOG-D_SERVICE_MANUAL.pdf"
OPEN_CUTOFF = 90


def spectra(audio):
    result = []
    for (start, stop), (_, _, key) in zip(NOTE_WINDOWS, KEYS, strict=True):
        signal = audio[frames_at(start):frames_at(stop)].astype(np.float64)
        hz, _ = peak_frequency(signal)
        expected = 440. * 2 ** ((key + 12 - 69 + CONTROLS["tune"] / 100.) / 12.)
        assert abs(1200. * np.log2(hz / expected)) < 9., (key, hz, expected)
        weighted = (signal - signal.mean()) * np.hanning(len(signal))
        phase = -2j * np.pi * hz / SAMPLE_RATE * np.arange(len(signal))
        amplitudes = abs(np.exp(np.arange(1, 7)[:, None] * phase) @ weighted)
        result.append(20. * np.log10(amplitudes[1:] / amplitudes[0]))
    return np.asarray(result)


def compare(render, schema, component, reference, audition):
    length = PREROLL + VOICE_DELAY + FRAMES

    def phrase(controls, block=128):
        audio, _ = render(score(schema, controls=controls), block=block, frames=length)
        return audio[PREROLL + VOICE_DELAY:]

    baseline = phrase(CONTROLS)
    candidate_controls = dict(CONTROLS, cutoff=OPEN_CUTOFF)
    candidate = phrase(candidate_controls)
    assert np.array_equal(candidate, phrase(candidate_controls, block=480))
    output_lower = phrase(dict(CONTROLS, output_level=25))
    mixer_lower = phrase(dict(CONTROLS, saw_mix=20))
    takes = dict(reference=reference, baseline=baseline, cutoff_90=candidate,
                 output_25=output_lower, mixer_20=mixer_lower)
    results = {name: dict(peak=float(np.max(abs(audio))), rms=rms(audio),
                          harmonic_2_to_6_over_1_db=spectra(audio).tolist())
               for name, audio in takes.items()}
    harmonic_rows = {name: np.asarray(row["harmonic_2_to_6_over_1_db"]) for name, row in results.items()}
    baseline_h2 = harmonic_rows["baseline"][:, 0]
    h2_recovered = harmonic_rows["cutoff_90"][:, 0] - baseline_h2
    # Stage::tick enters its output soft limiter at 0.8 FS.
    assert results["baseline"]["peak"] < 0.08
    assert np.max(abs(harmonic_rows["output_25"][:, 0] - baseline_h2)) < 0.1
    assert np.max(abs(harmonic_rows["mixer_20"][:, 0] - baseline_h2)) < 1.5
    assert np.min(h2_recovered) > 17., h2_recovered

    range_check = []
    for knob in (40, 65, 66.5, 70):
        tone, _ = render(filter_score(cutoff=knob), frames=96_000)
        early, late = tone[24_000:41_280], tone[72_000:91_200]
        hz, power = peak_frequency(late)
        assert power > 0.97 and rms(late) > 1e-5, (knob, hz, power, rms(late))
        range_check.append(dict(cutoff=knob, peak_hz=hz, early_rms=rms(early), late_rms=rms(late)))
    assert 80. < range_check[0]["peak_hz"] < 115.
    assert 430. < range_check[2]["peak_hz"] < 455.

    report = dict(component_sha256=component, source=DEMO, reference_sha256=REFERENCE_SHA256,
                  sample_rate_hz=SAMPLE_RATE, note_windows_ms=NOTE_WINDOWS,
                  baseline_controls=CONTROLS, open_cutoff=OPEN_CUTOFF, results=results,
                  recovered_h2_db=h2_recovered.tolist(), bit_equal_block_frames=[128, 480],
                  filter_range=dict(source=SERVICE_MANUAL, printed_page=14, dial_mark=-1,
                                    expected_hz=440, comparison=range_check))
    if audition:
        listening = {"Minimoog": reference, "RF-D at 50": baseline, "RF-D at 90": candidate}
        order = ("Minimoog", "RF-D at 50", "Minimoog", "RF-D at 90")
        report["audition"] = write_audition(listening, order, AUDITION)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audition", action="store_true", help="write one level-matched comparison WAV")
    parser.add_argument("--write-report", action="store_true", help="save the measurements in evidence/")
    args = parser.parse_args()
    reference = read_reference()

    def inspect(render, schema, component):
        report = compare(render, schema, component, reference, args.audition)
        if args.write_report:
            write(RECEIPT, report)
        print(json.dumps(report, indent=2, allow_nan=False))

    build_voice(["--midi"], inspect_audio=inspect)


if __name__ == "__main__":
    main()
