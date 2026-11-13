"""Test the measured vintage phase variation through RF-D's oscillator CV input."""
import argparse
import json

import numpy as np

from check_rf_d_la2_line_ab import CONTROLS, PITCH_HZ, SETTLE_FRAMES, cents
from check_rf_d_oboe_ab import PREROLL, VOICE_DELAY, score, write_audition
from check_rf_d_playable_filter import change
from check_rf_d_playable_voice import ROOT, SAMPLE_RATE, main as build_voice, write
from check_rf_d_vintage_saw_ab import FRAMES, NOTES, REFERENCE_SHA256, SOURCE, read_reference, spectrum
from check_rf_d_vintage_saw_air import ANALYSIS, BANDS_HZ, band_power, fit_cycle, high_residual, saw_phase
from check_rf_d_vintage_saw_phase import phase_corrections
from check_rf_d_voice_control_inputs import PITCH_CV

AUDITION = ROOT / "artifacts/rf-d-la2-textura-cv-ab.wav"
RECEIPT = ROOT / "evidence/rf_d_la2_pitch_cv_ab01.json"
CV_EVENT_FRAMES = 96
START = PREROLL + VOICE_DELAY + SETTLE_FRAMES


def band_levels(audio, cycle):
    bands, power = band_power(audio)
    residual, _ = band_power(audio - cycle)
    return dict(total_db=(10. * np.log10(bands / power)).tolist(),
                residual_db=(10. * np.log10(residual / power)).tolist())


def inspect_note(render, schema, original, midi_key):
    phase, fundamental = saw_phase(original)
    correction = np.mean(phase_corrections(original, phase), axis=0)
    cycle = fit_cycle(original, phase, fundamental)
    tracked_cycle = fit_cycle(original, phase + correction, fundamental)
    reduced = original - high_residual(tracked_cycle - cycle)

    # The oscillator advances at f0 * 2**V. Convert the derivative of the
    # phase correction to a voltage at the documented 1 V/octave input.
    delta_hz = np.gradient(correction) * SAMPLE_RATE / (2. * np.pi)
    volts = np.log2(1. + delta_hz / fundamental)
    cv_offsets = np.arange(0, FRAMES, CV_EVENT_FRAMES)
    cv_values = [float(volts[offset:offset + CV_EVENT_FRAMES].mean()) for offset in cv_offsets]
    pitch, _ = spectrum(original)
    nominal_hz = PITCH_HZ * 2. ** ((midi_key - 45) / 12.)
    tune = round(cents(float(np.median(pitch)), nominal_hz), 1)
    events = score(schema, controls=dict(CONTROLS, tune=tune), keys=((0, 700, midi_key),), wheel=())
    cv_events = [change(PITCH_CV, voltage, START - VOICE_DELAY + int(offset))
                 for offset, voltage in zip(cv_offsets, cv_values, strict=True)]
    modulated_events = sorted(events + cv_events, key=lambda event: event[0])

    renders = []
    for performance in (events, modulated_events):
        first, _ = render(performance, frames=START + FRAMES, block=128)
        second, _ = render(performance, frames=START + FRAMES, block=480)
        assert np.array_equal(first, second)
        renders.append(first[START:])
    dry, driven = renders
    assert not np.array_equal(dry, driven)

    def rf_d_levels(audio):
        angle, f0 = saw_phase(audio)
        assert abs(cents(f0, fundamental)) < 2.
        return band_levels(audio, fit_cycle(audio, angle, f0))

    metrics = dict(
        fundamental_hz=fundamental, tune_cents=tune,
        phase_correction_rms_us=float(np.std(correction[ANALYSIS]) / (2. * np.pi * fundamental) * 1e6),
        cv_rms_mv=float(np.sqrt(np.mean(volts[ANALYSIS]**2)) * 1e3),
        cv_peak_mv=float(max(abs(value) for value in cv_values) * 1e3),
        vintage=band_levels(original, cycle),
        vintage_with_phase_contribution_attenuated=band_levels(reduced, cycle),
        rf_d_open=rf_d_levels(dry), rf_d_with_cv=rf_d_levels(driven),
    )
    return metrics, (original, dry, driven, reduced)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-report", action="store_true")
    args = parser.parse_args()
    reference = read_reference()
    report = dict(
        source=SOURCE, reference_sha256=REFERENCE_SHA256,
        reference_limits="Archived MP3. The equivalent voltage is a stimulus derived from audio, not a measurement.",
        sample_rate_hz=SAMPLE_RATE, oversampling=4, ladder="trapezoidal",
        rf_d_controls=CONTROLS, cv_event_frames=CV_EVENT_FRAMES, bands_hz=BANDS_HZ,
        bit_equal_block_frames=[128, 480], notes={},
    )

    def inspect(render, schema, component):
        report["component_sha256"] = component
        for (name, midi), original in zip(NOTES, reference, strict=True):
            report["notes"][name], clips = inspect_note(render, schema, original, midi)
            if name == "La2":
                labels = ("Minimoog original", "RF-D abierto", "RF-D con CV de prueba",
                          "Minimoog con aporte de fase atenuado")
                audition = {label: clip[ANALYSIS] for label, clip in zip(labels, clips, strict=True)}
                report["audition_gain_order"] = list(audition)
                report["audition"] = write_audition(audition, labels, AUDITION, sample_width=3)

    build_voice(["--midi"], inspect_audio=inspect, oversampling=4, trapezoidal_ladder=True)
    if args.write_report:
        write(RECEIPT, report)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
