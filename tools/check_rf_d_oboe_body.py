"""Compare Oboe body and the seventh-harmonic notch at two pulse widths."""
import argparse
import itertools
import json

import numpy as np

from check_rf_d_oboe_ab import (
    DEMO, FRAMES, NOTE_WINDOWS, PREROLL, REFERENCE_SHA256, VOICE_DELAY,
    frames_at, read_reference, score, write_audition,
)
from check_rf_d_oboe_spectrum import BANDS, FIT_NOTES, RESERVED_NOTES, RECEIPT as PREVIOUS, band_levels
from check_rf_d_playable_filter import peak_frequency
from check_rf_d_playable_voice import ROOT, SAMPLE_RATE, main as build_voice, sha, write

AUDITION = ROOT / "artifacts/rf-d-oboe-cuerpo-ab.wav"
RECEIPT = ROOT / "evidence/rf_d_oboe_body01.json"
# A high state lasting 2/7 of each period gives a rectangular-pulse zero at H7
# near the circuit model's Wide Pulse setting.
TEST_DUTY = 2. / 7.
BODY_BANDS = ((300, 650), *BANDS)
BODY = slice(2, 4)


def render_phrase(render, schema, controls, block=128):
    start = PREROLL + VOICE_DELAY
    audio, _ = render(score(schema, controls=controls), frames=start + FRAMES, block=block)
    return audio[start:]


def harmonic_7_db(audio):
    ratios = []
    for start, stop in NOTE_WINDOWS:
        signal = audio[frames_at(start):frames_at(stop)].astype(np.float64)
        hz, _ = peak_frequency(signal)
        phase = -2j * np.pi * hz * np.arange(signal.size) / SAMPLE_RATE
        windowed = (signal - signal.mean()) * np.hanning(signal.size)
        first, seventh = abs(np.exp(np.asarray([1, 7])[:, None] * phase) @ windowed)
        ratios.append(float(20. * np.log10(seventh / first)))
    return ratios


def compare(render, schema, component, reference, baseline, baseline_component, settings, audition):
    target = band_levels(reference, BODY_BANDS)
    previous = band_levels(baseline, BODY_BANDS)

    def error(actual, notes, bands=slice(None)):
        return float(np.mean(abs(actual[list(notes), bands] - target[list(notes), bands])))

    grid = []
    for cutoff, emphasis, mixer in itertools.product(range(65, 75), (40, 50, 60), (40, 60)):
        controls = dict(settings, cutoff=cutoff, emphasis=emphasis, saw_mix=mixer)
        actual = band_levels(render_phrase(render, schema, controls), BODY_BANDS)
        body = error(actual, FIT_NOTES, BODY)
        spectrum = error(actual, FIT_NOTES)
        grid.append(dict(cutoff=cutoff, emphasis=emphasis, saw_mix=mixer, fit_error_db=(body + spectrum) / 2.))
    best = min(grid, key=lambda row: row["fit_error_db"])
    controls = dict(settings, **{name: best[name] for name in ("cutoff", "emphasis", "saw_mix")})
    candidate = render_phrase(render, schema, controls)
    assert np.array_equal(candidate, render_phrase(render, schema, controls, block=480))
    assert 0.005 < np.max(abs(candidate)) < 0.8
    actual = band_levels(candidate, BODY_BANDS)
    body_before, body_after = (error(take, RESERVED_NOTES, BODY) for take in (previous, actual))
    high_after = error(actual, RESERVED_NOTES, slice(4, 5))
    assert body_after < 0.8 * body_before and high_after < 3.5, (body_before, body_after, high_after, best)
    takes = {"Minimoog": reference, "RF-D body": candidate, "RF-D prior": baseline}
    report = dict(
        source=DEMO, reference_sha256=REFERENCE_SHA256, prior_settings_sha256=sha(PREVIOUS),
        component_sha256=component, prior_component_sha256=baseline_component,
        sample_rate_hz=SAMPLE_RATE, wide_pulse_duty=TEST_DUTY, settings=controls,
        note_windows_ms=NOTE_WINDOWS, fit_note_indices=FIT_NOTES, reserved_note_indices=RESERVED_NOTES,
        band_edges_hz=BODY_BANDS, fit_grid=grid,
        mean_reserved_body_error_db=dict(prior=body_before, adjusted=body_after),
        mean_reserved_4_to_8_khz_error_db=high_after,
        band_levels_db=dict(minimoog=target.tolist(), prior=previous.tolist(), adjusted=actual.tolist()),
        harmonic_7_over_1_db={name: harmonic_7_db(take) for name, take in takes.items()},
        bit_equal_block_frames=[128, 480],
    )
    if audition:
        order = ("Minimoog", "RF-D body", "Minimoog", "RF-D prior")
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
    settings = previous["settings"]

    def inspect_baseline(render, schema, component):
        nonlocal baseline, baseline_component
        baseline = render_phrase(render, schema, settings)
        baseline_component = component

    baseline = baseline_component = None
    build_voice(["--midi"], inspect_audio=inspect_baseline)

    def inspect_candidate(render, schema, component):
        report = compare(render, schema, component, reference, baseline, baseline_component, settings, args.audition)
        if args.write_report:
            write(RECEIPT, report)
        print(json.dumps(report, indent=2, allow_nan=False))

    build_voice(["--midi"], inspect_audio=inspect_candidate, wide_pulse_duty=TEST_DUTY)


if __name__ == "__main__":
    main()
