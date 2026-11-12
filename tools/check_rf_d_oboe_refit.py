"""Refit the 4x Oboe using individual harmonics and verify the remaining notes."""
import argparse
import itertools
import json

import numpy as np

from check_rf_d_oboe_ab import (
    DEMO, FRAMES, NOTE_WINDOWS, PREROLL, REFERENCE_SHA256, VOICE_DELAY,
    frames_at, read_reference, score, write_audition,
)
from check_rf_d_oboe_articulation import attack_curves, RECEIPT as ARTICULATION
from check_rf_d_oboe_oversampling import BANDS, RECEIPT as PREVIOUS
from check_rf_d_oboe_spectrum import FIT_NOTES, RESERVED_NOTES, band_levels
from check_rf_d_playable_filter import peak_frequency
from check_rf_d_playable_voice import ROOT, SAMPLE_RATE, main as build_voice, sha, write

AUDITION = ROOT / "artifacts/rf-d-oboe-refit-ab.wav"
RECEIPT = ROOT / "evidence/rf_d_oboe_refit01.json"
HARMONICS = np.arange(1, 21)
FLOOR_DB = -45.


def harmonic_levels(audio):
    rows = []
    for left, right in NOTE_WINDOWS:
        signal = audio[frames_at(left):frames_at(right)].astype(np.float64)
        frequency, _ = peak_frequency(signal)
        phase = -2j * np.pi * frequency * np.arange(signal.size) / SAMPLE_RATE
        windowed = (signal - signal.mean()) * np.hanning(signal.size)
        amplitude = abs(np.exp(HARMONICS[:, None] * phase) @ windowed)
        rows.append(20. * np.log10(amplitude / amplitude[0]))
    return np.asarray(rows)


def compare(render, schema, component, reference, prior, articulation, audition):
    settings = prior["settings"]
    start = PREROLL + VOICE_DELAY

    def phrase(controls, block=128):
        events = score(schema, controls=controls, keys=articulation["gate_ms_and_midi_note"])
        audio, _ = render(events, frames=start + FRAMES, block=block)
        return audio[start:]

    baseline = phrase(settings)
    reference_harmonics = harmonic_levels(reference)
    reference_bands = band_levels(reference, BANDS)

    def analyze(audio):
        harmonics = harmonic_levels(audio)
        bands = band_levels(audio, BANDS)
        harmonic_delta = abs(np.maximum(harmonics, FLOOR_DB) - np.maximum(reference_harmonics, FLOOR_DB))
        band_delta = abs(bands - reference_bands)
        metrics = {}
        for name, notes in (("fit", FIT_NOTES), ("reserved", RESERVED_NOTES)):
            notes = list(notes)
            metrics[name] = dict(
                low_harmonics_db=float(harmonic_delta[notes, 1:6].mean()),
                upper_harmonics_db=float(harmonic_delta[notes, 7:20].mean()),
                bands_db=float(band_delta[notes, 2:6].mean()),
            )
        return metrics, harmonics, bands

    before, baseline_harmonics, baseline_bands = analyze(baseline)
    frozen = prior["variants"]["RF-D 4x"]
    assert component == frozen["component_sha256"]
    assert np.allclose(baseline_bands, frozen["band_levels_db"], atol=1e-6, rtol=0.)
    grid = []
    for cutoff, emphasis, level in itertools.product((65, 67, 69, 71), (45, 50, 55, 60), (25, 40, 55)):
        values = dict(cutoff=cutoff, emphasis=emphasis, saw_mix=level)
        errors, _, _ = analyze(phrase(dict(settings, **values)))
        grid.append(dict(controls=values, fit_error_db=sum(errors["fit"].values())))
    best = min(grid, key=lambda entry: entry["fit_error_db"])
    adjusted = dict(settings, **best["controls"])
    candidate = phrase(adjusted)
    assert np.array_equal(candidate, phrase(adjusted, block=480))
    assert 0.005 < np.max(abs(candidate)) < 0.8
    after, candidate_harmonics, candidate_bands = analyze(candidate)
    assert after["reserved"]["upper_harmonics_db"] < 0.8 * before["reserved"]["upper_harmonics_db"]
    assert after["reserved"]["low_harmonics_db"] < before["reserved"]["low_harmonics_db"] + 0.4
    assert after["reserved"]["bands_db"] < before["reserved"]["bands_db"]
    reference_attack = attack_curves(reference)
    attack_error = [float(abs(attack_curves(take) - reference_attack).mean()) for take in (baseline, candidate)]
    assert abs(attack_error[1] - attack_error[0]) < 0.1
    report = dict(
        source=DEMO, reference_sha256=REFERENCE_SHA256, previous_sha256=sha(PREVIOUS),
        articulation_sha256=sha(ARTICULATION), component_sha256=component, sample_rate_hz=SAMPLE_RATE,
        oversampling=4, wide_pulse_duty=prior["wide_pulse_duty"], settings=adjusted, baseline_settings=settings,
        fit_note_indices=FIT_NOTES, reserved_note_indices=RESERVED_NOTES, note_windows_ms=NOTE_WINDOWS,
        harmonic_floor_db=FLOOR_DB, band_edges_hz=BANDS, fit_grid=grid,
        errors_db=dict(baseline=before, adjusted=after),
        attack_error_db=dict(baseline=attack_error[0], adjusted=attack_error[1]),
        harmonics_over_fundamental_db=dict(minimoog=reference_harmonics.tolist(),
                                           baseline=baseline_harmonics.tolist(),
                                           adjusted=candidate_harmonics.tolist()),
        band_levels_db=dict(minimoog=reference_bands.tolist(), baseline=baseline_bands.tolist(),
                            adjusted=candidate_bands.tolist()),
        bit_equal_block_frames=[128, 480],
    )
    if audition:
        takes = {"Minimoog": reference, "RF-D adjusted": candidate, "RF-D prior 4x": baseline}
        report["audition"] = write_audition(
            takes, ("Minimoog", "RF-D adjusted", "Minimoog", "RF-D prior 4x"), AUDITION,
        )
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audition", action="store_true", help="write one level-matched comparison WAV")
    parser.add_argument("--write-report", action="store_true", help="save measurements in evidence/")
    args = parser.parse_args()
    reference = read_reference()
    prior = json.loads(PREVIOUS.read_bytes())
    articulation = json.loads(ARTICULATION.read_bytes())
    assert prior["reference_sha256"] == articulation["reference_sha256"] == REFERENCE_SHA256
    assert prior["articulation_sha256"] == sha(ARTICULATION)

    def inspect(render, schema, component):
        report = compare(render, schema, component, reference, prior, articulation, args.audition)
        if args.write_report:
            write(RECEIPT, report)
        print(json.dumps(report, indent=2, allow_nan=False))

    build_voice(["--midi"], inspect_audio=inspect, wide_pulse_duty=prior["wide_pulse_duty"], oversampling=4)


if __name__ == "__main__":
    main()
