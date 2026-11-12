"""Render a mid-register Oboe from the 1974 Moog chart for listening."""
import argparse
import json

import numpy as np

from check_rf_d_fat_bass import FRAMES, NOTE_ON, NOTE_OFF, WINDOWS_MS, measure, write_audition
from check_rf_d_playable_filter import change, peak_frequency
from check_rf_d_playable_voice import ROOT, SAMPLE_RATE, main as build_voice, write

AUDITION = ROOT / "artifacts/rf-d-oboe-audicion.wav"
RECEIPT = ROOT / "evidence/rf_d_oboe_sweep01.json"
CHART = "https://medias.audiofanzine.com/files/minimoog-sounds-by-tom-rhea-ld-480638.pdf#page=5"
DEMO = "https://www.youtube.com/watch?v=S_FKXtwqJoQ&t=365s"
SETTINGS = dict(
    osc1_range=4, osc1_wave=4, saw_mix=40,
    osc3_range=0, osc3_wave=0, osc3_frequency=3, osc3_tracking=False,
    modulation_mix=0, oscillator_modulation=True, filter_modulation=True,
    cutoff=50, emphasis=50, contour_amount=30, filter_tracking_one_third=True,
    filter_attack=10, filter_decay=600, filter_sustain=80,
    loudness_attack=100, loudness_decay=200, loudness_sustain=80, decay_enabled=1, output_level=50,
)
NOTES = (57, 60)
ORDER = ((50, 50), (40, 50), (60, 50))


def sweep(render, schema, component_sha256, audition):
    indices = {parameter["id"]: parameter["index"] for parameter in schema["parameters"]}
    results = []
    listening = {}
    listening_rows = {}
    for note in NOTES:
        f0 = 2. * 440. * 2 ** ((note - 69) / 12.)
        events = [[NOTE_ON, 0x90, note, 100], [NOTE_OFF, 0x80, note, 0]]
        for cutoff, emphasis in ORDER:
            controls = dict(SETTINGS, cutoff=cutoff, emphasis=emphasis)
            score = [change(indices[name], value) for name, value in controls.items()] + events
            audio, _ = render(score, frames=FRAMES)
            assert not np.any(audio[:NOTE_ON]) and 0.001 < np.max(abs(audio)) < 1.
            metrics = measure(audio, f0)
            start_ms, stop_ms = WINDOWS_MS["late"]
            settled = audio[NOTE_ON + start_ms * SAMPLE_RATE // 1000:NOTE_ON + stop_ms * SAMPLE_RATE // 1000]
            measured_hz, _ = peak_frequency(settled)
            assert abs(measured_hz - f0) < 0.1, (note, cutoff, measured_hz, f0)
            if cutoff == SETTINGS["cutoff"]:
                assert np.array_equal(audio, render(score, block=480, frames=FRAMES)[0]), note
            row = dict(note=note, cutoff=cutoff, emphasis=emphasis, fundamental_hz=f0,
                       measured_hz=measured_hz, **metrics)
            results.append(row)
            if note == NOTES[0]:
                listening[cutoff, emphasis] = audio
                listening_rows[cutoff, emphasis] = row
    report = dict(chart=CHART, demo=DEMO, comparison_status="RF-D only", settings=SETTINGS,
                  component_sha256=component_sha256, sample_rate_hz=SAMPLE_RATE,
                  score=dict(note_on_frame=NOTE_ON, note_off_frame=NOTE_OFF, frames=FRAMES),
                  windows_ms_from_note_on=WINDOWS_MS, rows=results)
    if audition:
        report["audition"] = write_audition(listening, listening_rows, destination=AUDITION, order=ORDER)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audition", action="store_true", help="write one level-matched WAV for listening")
    parser.add_argument("--write-report", action="store_true", help="save the measurements in evidence/")
    args = parser.parse_args()

    def inspect(render, schema, component_sha256):
        report = sweep(render, schema, component_sha256, args.audition)
        if args.write_report:
            write(RECEIPT, report)
        print(json.dumps(report, indent=2, allow_nan=False))

    build_voice(["--midi"], inspect_audio=inspect, legacy_timbre=True)


if __name__ == "__main__":
    main()
