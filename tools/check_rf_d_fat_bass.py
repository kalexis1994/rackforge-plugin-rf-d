"""Render the documented Fat Bass patch and measure two controls without fitting."""
import argparse
import itertools
import json
import wave

import numpy as np

from check_rf_d_playable_filter import change, rms
from check_rf_d_playable_voice import ROOT, SAMPLE_RATE, main as build_voice, sha, write

PATCHES = ROOT / "evidence/rf_d_reference_patches.json"
RECEIPT = ROOT / "evidence/rf_d_fat_bass_sweep01.json"
AUDITION = ROOT / "artifacts/rf-d-fat-bass-audicion.wav"
DEMO = "https://www.youtube.com/watch?v=S_FKXtwqJoQ&t=691s"
NOTE_ON = 960
NOTE_OFF = NOTE_ON + SAMPLE_RATE
FRAMES = 86400
NOTES = (57, 45)
CUTOFFS = (20, 30, 40)
EMPHASES = (40, 50, 60)
WINDOWS_MS = {"early": (30, 175), "late": (480, 880)}
AUDITION_ORDER = ((30, 50), (20, 50), (40, 50), (30, 40), (30, 60))
GAP_FRAMES = SAMPLE_RATE // 4


def db_ratio(value, reference):
    return float(20. * np.log10(value / reference))


def measure(audio, fundamental_hz):
    result = {}
    for name, (start_ms, stop_ms) in WINDOWS_MS.items():
        start = NOTE_ON + start_ms * SAMPLE_RATE // 1000
        stop = NOTE_ON + stop_ms * SAMPLE_RATE // 1000
        signal = audio[start:stop].astype(np.float64)
        window = np.hanning(signal.size)
        phase = -2j * np.pi * fundamental_hz / SAMPLE_RATE * np.arange(signal.size)
        harmonics = np.arange(1, 9)[:, None]
        weighted = (signal - np.mean(signal)) * window
        amplitudes = 2. * abs(np.exp(harmonics * phase) @ weighted) / np.sum(window)
        result[name] = dict(
            rms=rms(signal),
            harmonic_2_over_1_db=db_ratio(amplitudes[1], amplitudes[0]),
            harmonics_4_to_8_over_1_to_3_db=db_ratio(
                np.linalg.norm(amplitudes[3:]), np.linalg.norm(amplitudes[:3])),
        )
    result["peak"] = float(np.max(abs(audio)))
    result["held_rms"] = rms(audio[NOTE_ON:NOTE_OFF])
    result["early_to_late_rms_db"] = db_ratio(result["late"]["rms"], result["early"]["rms"])
    result["early_to_late_brightness_db"] = (
        result["late"]["harmonics_4_to_8_over_1_to_3_db"] -
        result["early"]["harmonics_4_to_8_over_1_to_3_db"]
    )
    return result


def write_audition(audio_by_controls, rows, *, destination=AUDITION, order=AUDITION_ORDER):
    selected = [rows[pair] for pair in order]
    rms_target = min(10 ** (-22 / 20), 10 ** (-1 / 20) * min(
        row["held_rms"] / row["peak"] for row in selected))
    pcm = []
    playlist = []
    for cutoff, emphasis in order:
        gain = rms_target / rows[cutoff, emphasis]["held_rms"]
        clip = audio_by_controls[cutoff, emphasis] * gain
        assert np.max(abs(clip)) < 1.
        if pcm:
            pcm.append(np.zeros(GAP_FRAMES, dtype="<i2"))
        playlist.append(dict(cutoff=cutoff, emphasis=emphasis, gain=gain,
                             start_frame=sum(part.size for part in pcm)))
        pcm.append(np.rint(clip * 32767).astype("<i2"))
    destination.parent.mkdir(exist_ok=True)
    with wave.open(str(destination), "wb") as output:
        output.setparams((1, 2, SAMPLE_RATE, 0, "NONE", "not compressed"))
        output.writeframes(np.concatenate(pcm).tobytes())
    return dict(sha256=sha(destination), held_rms_target=rms_target, playlist=playlist)


def sweep(render, schema, component_sha256, audition):
    patches = json.loads(PATCHES.read_bytes())
    settings = patches["emerson_fat_bass"]
    assert (settings["cutoff"], settings["emphasis"]) == (30, 50)
    indices = {parameter["id"]: parameter["index"] for parameter in schema["parameters"]}
    results = []
    listening = {}
    listening_rows = {}
    for note in NOTES:
        # OSC1 at 32 ft sounds two octaves below its 8 ft reference.
        f0 = 440. * 2 ** ((note - 69) / 12.) / 4.
        events = [[NOTE_ON, 0x90, note, 100], [NOTE_OFF, 0x80, note, 0]]
        for cutoff, emphasis in itertools.product(CUTOFFS, EMPHASES):
            controls = dict(settings, cutoff=cutoff, emphasis=emphasis)
            score = [change(indices[name], value) for name, value in controls.items()] + events
            audio, _ = render(score, frames=FRAMES)
            assert not np.any(audio[:NOTE_ON]) and 0.001 < np.max(abs(audio)) < 1.
            if (cutoff, emphasis) == (30, 50):
                assert np.array_equal(audio, render(score, block=480, frames=FRAMES)[0]), note
            row = dict(note=note, cutoff=cutoff, emphasis=emphasis, fundamental_hz=f0, **measure(audio, f0))
            results.append(row)
            if note == NOTES[0] and (cutoff, emphasis) in AUDITION_ORDER:
                listening[cutoff, emphasis] = audio
                listening_rows[cutoff, emphasis] = row
    report = dict(source=DEMO, comparison_status="RF-D only", patch_sha256=sha(PATCHES),
                  component_sha256=component_sha256, sample_rate_hz=SAMPLE_RATE,
                  score=dict(note_on_frame=NOTE_ON, note_off_frame=NOTE_OFF, frames=FRAMES),
                  windows_ms_from_note_on=WINDOWS_MS, rows=results)
    if audition:
        report["audition"] = write_audition(listening, listening_rows)
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
        print(json.dumps(report, indent=2))

    build_voice(["--midi"], inspect_audio=inspect, legacy_timbre=True)


if __name__ == "__main__":
    main()
