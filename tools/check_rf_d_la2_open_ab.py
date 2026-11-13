"""Audition the archived vintage La2 against RF-D with Cutoff fully open."""
import argparse
import json

import numpy as np

from check_rf_d_la2_line_ab import CONTROLS, PITCH_HZ, REGISTERS, SETTLE_FRAMES, cents
from check_rf_d_oboe_ab import PREROLL, VOICE_DELAY, score, write_audition
from check_rf_d_playable_voice import ROOT, SAMPLE_RATE, main as build_voice, write
from check_rf_d_vintage_saw_ab import FRAMES, REFERENCE_SHA256, SOURCE, SOURCE_WINDOWS, read_reference, spectrum
from check_rf_d_vintage_saw_air import ANALYSIS, BANDS_HZ, describe, periodic_component

AUDITION = ROOT / "artifacts/rf-d-la2-filtro-abierto-ab.wav"
RECEIPT = ROOT / "evidence/rf_d_la2_open_ab01.json"


def describe_take(audio):
    cycle, pitch = periodic_component(audio)
    return describe(audio, cycle, pitch)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-report", action="store_true")
    args = parser.parse_args()
    original = read_reference()[0]
    frequencies, _ = spectrum(original)
    target = float(np.median(frequencies))
    tune = round(cents(target, PITCH_HZ), 1)
    osc1_range, midi_key = REGISTERS["8"]
    controls = dict(CONTROLS, osc1_range=osc1_range, tune=tune)
    start = PREROLL + VOICE_DELAY + SETTLE_FRAMES
    report = dict(
        source=SOURCE, reference_sha256=REFERENCE_SHA256, source_window_seconds=SOURCE_WINDOWS[0],
        reference_limits="Vintage MP3 excerpt. Capture chain and hardware cutoff position unverified.",
        sample_rate_hz=SAMPLE_RATE, oversampling=4, ladder="trapezoidal", midi_key=midi_key,
        rf_d_controls=controls, bands_hz=BANDS_HZ, bit_equal_block_frames=[128, 480],
    )

    def inspect(render, schema, component):
        report["component_sha256"] = component
        signals = {"Minimoog vintage La2": original}
        for cutoff in (100, 75):
            events = score(schema, controls=dict(controls, cutoff=cutoff), keys=((0, 700, midi_key),), wheel=())
            render_128, _ = render(events, frames=start + FRAMES, block=128)
            render_480, _ = render(events, frames=start + FRAMES, block=480)
            assert np.array_equal(render_128, render_480), cutoff
            audio = render_128[start:]
            frequency, _ = spectrum(audio)
            assert abs(cents(float(np.median(frequency)), target)) < 2., cutoff
            signals[f"RF-D cutoff {cutoff}%"] = audio
        report["measurements"] = {name: describe_take(audio) for name, audio in signals.items()}
        audition = {name: signals[name][ANALYSIS] for name in ("Minimoog vintage La2", "RF-D cutoff 100%")}
        report["audition_gain_order"] = list(audition)
        report["audition"] = write_audition(audition, tuple(audition) * 2, AUDITION, sample_width=3)

    build_voice(["--midi"], inspect_audio=inspect, oversampling=4, trapezoidal_ladder=True)
    if args.write_report:
        write(RECEIPT, report)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
