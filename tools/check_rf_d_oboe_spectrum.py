"""Match the Oboe capture's spectral balance with the playable panel controls."""
import argparse
import itertools
import json

import numpy as np

from check_rf_d_oboe_ab import (
    CONTROLS, DEMO, FRAMES, NOTE_WINDOWS, PREROLL, REFERENCE_SHA256, VOICE_DELAY,
    frames_at, read_reference, score, write_audition,
)
from check_rf_d_playable_voice import ROOT, SAMPLE_RATE, main as build_voice, write

AUDITION = ROOT / "artifacts/rf-d-oboe-brillo-ab.wav"
RECEIPT = ROOT / "evidence/rf_d_oboe_spectrum01.json"
BANDS = ((700, 1200), (1200, 2200), (2200, 4000), (4000, 8000), (8000, 16000))
FFT_SIZE = 32768
FIT_NOTES = (3, 4)
RESERVED_NOTES = (0, 1, 2, 5, 6)


def band_levels(audio, bands=BANDS):
    frequencies = np.fft.rfftfreq(FFT_SIZE, 1. / SAMPLE_RATE)
    masks = [(low <= frequencies) & (frequencies < high) for low, high in bands]
    rows = []
    for start, stop in NOTE_WINDOWS:
        signal = audio[frames_at(start):frames_at(stop)].astype(np.float64)
        windowed = (signal - signal.mean()) * np.hanning(signal.size)
        power = abs(np.fft.rfft(windowed, FFT_SIZE))**2
        rows.append(10. * np.log10([power[mask].sum() / power.sum() for mask in masks]))
    return np.asarray(rows)


def compare(render, schema, component, reference, audition):
    length = PREROLL + VOICE_DELAY + FRAMES

    def phrase(controls, block=128):
        audio, _ = render(score(schema, controls=controls), frames=length, block=block)
        return audio[PREROLL + VOICE_DELAY:]

    def error(target, actual, notes):
        return float(np.mean(abs(target[list(notes)] - actual[list(notes)])))

    baseline = phrase(CONTROLS)
    target = band_levels(reference)
    original = band_levels(baseline)
    grid = []
    for cutoff, emphasis in itertools.product(range(64, 76), (25, 40, 50, 60)):
        controls = dict(CONTROLS, cutoff=cutoff, emphasis=emphasis)
        measured = band_levels(phrase(controls))
        grid.append(dict(cutoff=cutoff, emphasis=emphasis, fit_error_db=error(target, measured, FIT_NOTES)))
    selected = min(grid, key=lambda row: row["fit_error_db"])
    controls = dict(CONTROLS, cutoff=selected["cutoff"], emphasis=selected["emphasis"])
    candidate = phrase(controls)
    measured = band_levels(candidate)
    assert np.array_equal(candidate, phrase(controls, block=480))
    assert 0.005 < np.max(abs(candidate)) < 0.8
    before = error(target, original, RESERVED_NOTES)
    after = error(target, measured, RESERVED_NOTES)
    assert after < 0.4 * before, (before, after)
    high_band_errors = abs(target[list(RESERVED_NOTES), 2:4] - measured[list(RESERVED_NOTES), 2:4])
    assert np.max(np.median(high_band_errors, axis=0)) < 5., high_band_errors
    report = dict(
        source=DEMO, reference_sha256=REFERENCE_SHA256, component_sha256=component,
        sample_rate_hz=SAMPLE_RATE, note_windows_ms=NOTE_WINDOWS, band_edges_hz=BANDS,
        fit_note_indices=FIT_NOTES, reserved_note_indices=RESERVED_NOTES,
        settings=controls, baseline_settings=CONTROLS,
        fit_grid=grid, mean_reserved_error_db=dict(baseline=before, adjusted=after),
        band_level_db=dict(minimoog=target.tolist(), baseline=original.tolist(), adjusted=measured.tolist()),
        bit_equal_block_frames=[128, 480],
    )
    if audition:
        takes = {"Minimoog": reference, "RF-D matched Oboe": candidate, "RF-D chart": baseline}
        order = ("Minimoog", "RF-D matched Oboe", "Minimoog", "RF-D chart")
        report["audition"] = write_audition(takes, order, AUDITION)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audition", action="store_true", help="write one level-matched comparison WAV")
    parser.add_argument("--write-report", action="store_true", help="save measurements in evidence/")
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
