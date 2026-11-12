"""Compare the Oboe phrase with its initial articulation and a closer attack."""
import argparse
import json

import numpy as np

from check_rf_d_oboe_ab import (
    DEMO, FRAMES, KEYS, PREROLL, REFERENCE_SHA256, VOICE_DELAY,
    frames_at, read_reference, score, write_audition,
)
from check_rf_d_oboe_body import RECEIPT as PREVIOUS
from check_rf_d_oboe_spectrum import band_levels
from check_rf_d_playable_filter import rms
from check_rf_d_playable_voice import ROOT, SAMPLE_RATE, main as build_voice, sha, write

AUDITION = ROOT / "artifacts/rf-d-oboe-ataque-ab.wav"
RECEIPT = ROOT / "evidence/rf_d_oboe_articulation01.json"
ATTACK_KEYS = (0, 4, 6)
OFFSETS_MS = tuple(range(-4, 60, 4))
ATTACK_DELAY_MS = 6
LOUDNESS_ATTACK_MS = 30


def attack_curves(audio):
    rows = []
    for index in ATTACK_KEYS:
        onset, _, _ = KEYS[index]
        settled = rms(audio[frames_at(onset + 50):frames_at(onset + 70)])
        levels = [rms(audio[frames_at(onset + offset):frames_at(onset + offset + 8)])
                  for offset in OFFSETS_MS]
        rows.append(np.maximum(20. * np.log10(np.maximum(levels, 1e-12) / settled), -35.))
    return np.asarray(rows)


def compare(render, schema, component, reference, previous, audition):
    controls = previous["settings"]
    adjusted = dict(controls, loudness_attack=LOUDNESS_ATTACK_MS)
    keys = tuple((onset + ATTACK_DELAY_MS if index in ATTACK_KEYS else onset, end, note)
                 for index, (onset, end, note) in enumerate(KEYS))
    start = PREROLL + VOICE_DELAY

    def phrase(settings, key_events, block=128):
        events = score(schema, controls=settings, keys=key_events)
        audio, _ = render(events, frames=start + FRAMES, block=block)
        return audio[start:]

    assert component == previous["component_sha256"]
    baseline = phrase(controls, KEYS)
    candidate = phrase(adjusted, keys)
    assert np.array_equal(candidate, phrase(adjusted, keys, block=480))
    assert np.max(abs(candidate)) < 0.8
    takes = {"Minimoog": reference, "RF-D attack": candidate, "RF-D prior": baseline}
    curves = {name: attack_curves(take) for name, take in takes.items()}
    errors = {name: np.mean(abs(curve - curves["Minimoog"]), axis=1).tolist()
              for name, curve in curves.items() if name != "Minimoog"}
    assert np.all(np.asarray(errors["RF-D attack"]) < 0.75 * np.asarray(errors["RF-D prior"])), errors
    # Compare sustained passages after the faster attack has settled.
    spectral_shift = abs(band_levels(candidate)[[2, 3, 5, 6]] - band_levels(baseline)[[2, 3, 5, 6]])
    assert np.max(np.mean(spectral_shift, axis=0)) < 1., spectral_shift
    report = dict(
        source=DEMO, reference_sha256=REFERENCE_SHA256, prior_settings_sha256=sha(PREVIOUS),
        sample_rate_hz=SAMPLE_RATE, component_sha256=component, settings=adjusted,
        gate_ms_and_midi_note=keys, original_gate_ms_and_midi_note=KEYS,
        attack_key_indices=ATTACK_KEYS, envelope_offsets_ms=OFFSETS_MS,
        envelope_window_ms=8, envelope_normalization_ms=[50, 70], envelope_floor_db=-35,
        attack_curves_db={name: curve.tolist() for name, curve in curves.items()},
        attack_mean_absolute_error_db=errors, mean_sustained_spectral_shift_by_band_db=spectral_shift.mean(axis=0).tolist(),
        bit_equal_block_frames=[128, 480],
    )
    if audition:
        order = ("Minimoog", "RF-D attack", "Minimoog", "RF-D prior")
        report["audition"] = write_audition(takes, order, AUDITION)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audition", action="store_true", help="write one level-matched comparison WAV")
    parser.add_argument("--write-report", action="store_true", help="save measurements in evidence/")
    args = parser.parse_args()
    reference = read_reference()
    previous = json.loads(PREVIOUS.read_bytes())
    assert previous["reference_sha256"] == REFERENCE_SHA256

    def inspect(render, schema, component):
        report = compare(render, schema, component, reference, previous, args.audition)
        if args.write_report:
            write(RECEIPT, report)
        print(json.dumps(report, indent=2, allow_nan=False))

    build_voice(["--midi"], inspect_audio=inspect, wide_pulse_duty=previous["wide_pulse_duty"])


if __name__ == "__main__":
    main()
