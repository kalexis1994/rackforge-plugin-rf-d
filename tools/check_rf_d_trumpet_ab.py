"""Compare the first SynthMania Trumpet phrase with the RF-D MIDI voice."""
import argparse
import itertools
import json
import wave

import numpy as np

from check_rf_d_oboe_ab import PREROLL, VOICE_DELAY, frames_at, score, write_audition
from check_rf_d_playable_filter import peak_frequency, rms
from check_rf_d_playable_voice import ROOT, SAMPLE_RATE, main as build_voice, sha, write

DEMO = "https://www.youtube.com/watch?v=S_FKXtwqJoQ&t=416s"
REFERENCE = ROOT / "references-local/rhea-synthmania-trumpet-frase.wav"
REFERENCE_SHA256 = "e6472a1b4051aa0d3770ff202435fa41941da7d29d7e1e2684c0d510674af2f4"
PATCHES = ROOT / "evidence/rf_d_reference_patches.json"
AUDITION = ROOT / "artifacts/rf-d-trumpet-ab.wav"
RECEIPT = ROOT / "evidence/rf_d_trumpet_ab01.json"
FRAMES = 115_200
KEYS = (
    (38, 315, 55), (315, 424, 60), (424, 546, 64), (546, 694, 67),
    (866, 997, 64), (1034, 1159, 67), (1417, 1490, 69),
    (1576, 1877, 67), (1926, 2205, 65),
)
WINDOWS = ((140, 195), (346, 402), (449, 520), (585, 675), (903, 985),
           (1088, 1149), (1450, 1484), (1720, 1840), (2050, 2180))
FIT = (0, 1, 2, 3, 4, 5)
RESERVED = (6, 7, 8)
FLOOR_DB = -45.


def read_reference():
    if not REFERENCE.is_file() or sha(REFERENCE) != REFERENCE_SHA256:
        raise SystemExit(f"Expected the verified private Trumpet excerpt at {REFERENCE}")
    with wave.open(str(REFERENCE), "rb") as wav:
        assert (wav.getnchannels(), wav.getsampwidth(), wav.getframerate(), wav.getnframes()) == (
            2, 2, SAMPLE_RATE, FRAMES,
        )
        pcm = np.frombuffer(wav.readframes(FRAMES), dtype="<i2")
    return pcm.reshape(-1, 2).mean(axis=1) / 32768.


def measure(audio):
    harmonics = []
    pitch = []
    attack = []
    level = rms(audio)
    for (on, off, note), (left, right) in zip(KEYS, WINDOWS, strict=True):
        assert on < left < right < off
        signal = audio[frames_at(left):frames_at(right)].astype(np.float64)
        frequency, _ = peak_frequency(signal)
        nominal = 440. * 2. ** ((note - 69) / 12.)
        cents = 1200. * np.log2(frequency / nominal)
        assert abs(cents) < 50., (note, frequency, cents)
        pitch.append(cents)
        phase = -2j * np.pi * frequency * np.arange(signal.size) / SAMPLE_RATE
        weighted = (signal - signal.mean()) * np.hanning(signal.size)
        amplitude = abs(np.exp(np.arange(1, 9)[:, None] * phase) @ weighted)
        harmonics.append(20. * np.log10(np.maximum(amplitude / amplitude[0], 10. ** (FLOOR_DB / 20.))))
        edges = np.linspace(on, min(on + 120, off), 5)
        attack.append([
            20. * np.log10(max(rms(audio[frames_at(a):frames_at(b)]) / level, 0.01))
            for a, b in zip(edges[:-1], edges[1:])
        ])
    return dict(harmonics=np.asarray(harmonics), attack=np.asarray(attack), pitch=np.asarray(pitch))


def errors(measured, reference, notes):
    return {
        "h2_h8_db": float(abs(measured["harmonics"][notes, 1:] - reference["harmonics"][notes, 1:]).mean()),
        "attack_db": float(abs(measured["attack"][notes] - reference["attack"][notes]).mean()),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-report", action="store_true", help="save measurements in evidence/")
    args = parser.parse_args()
    reference = read_reference()
    reference_metrics = measure(reference)
    panel = json.loads(PATCHES.read_bytes())["trumpet"]
    # Use the single-oscillator position in the chart. Three oscillators are its tutti variant.
    settings = dict(panel, osc2_enabled=False, osc3_enabled=False,
                    tune=round(float(np.median(reference_metrics["pitch"])), 1))

    def inspect(render, schema, component):
        start = PREROLL + VOICE_DELAY

        def phrase(controls, block=128):
            events = score(schema, controls=controls, keys=KEYS, wheel=())
            audio, _ = render(events, frames=start + FRAMES, block=block)
            return audio[start:]

        baseline = phrase(settings)
        baseline_metrics = measure(baseline)
        grid = []
        for cutoff, filter_attack, loudness_attack in itertools.product(
            (40, 48, 56, 64), (50, 100, 200), (35, 70, 110),
        ):
            overrides = dict(cutoff=cutoff, filter_attack=filter_attack, loudness_attack=loudness_attack)
            result = measure(phrase(dict(settings, **overrides)))
            grid.append(dict(overrides=overrides, fit=errors(result, reference_metrics, list(FIT))))
        best = min(grid, key=lambda trial: sum(trial["fit"].values()))
        adjusted = dict(settings, **best["overrides"])
        candidate = phrase(adjusted)
        candidate_metrics = measure(candidate)
        assert np.array_equal(candidate, phrase(adjusted, block=480))
        assert 0. < np.max(abs(candidate)) < 0.8
        metrics = {
            name: {subset: errors(take, reference_metrics, list(notes))
                   for subset, notes in (("fit", FIT), ("reserved", RESERVED))}
            for name, take in (("baseline", baseline_metrics), ("adjusted", candidate_metrics))
        }
        for metric, error in metrics["adjusted"]["reserved"].items():
            assert error < metrics["baseline"]["reserved"][metric], metrics
        order = ("Minimoog", "RF-D") * 2
        report = dict(
            source=DEMO, source_excerpt="first phrase through the F4 release",
            reference_sha256=REFERENCE_SHA256, component_sha256=component, patch_table_sha256=sha(PATCHES),
            sample_rate_hz=SAMPLE_RATE, oversampling=4, frames_per_take=FRAMES,
            gate_ms_and_midi_note=KEYS, note_windows_ms=WINDOWS, fitted_notes=FIT, reserved_notes=RESERVED,
            preroll_frames=PREROLL, compensated_voice_delay_frames=VOICE_DELAY,
            bit_equal_block_frames=[128, 480], harmonic_floor_db=FLOOR_DB,
            settings=adjusted, chart_baseline=settings, errors_db=metrics, fit_grid=grid,
            per_note={name: {key: value.tolist() for key, value in take.items()}
                      for name, take in (("minimoog", reference_metrics),
                                         ("baseline", baseline_metrics), ("adjusted", candidate_metrics))},
            audition=write_audition({"Minimoog": reference, "RF-D": candidate}, order, AUDITION),
        )
        if args.write_report:
            write(RECEIPT, report)
        print(json.dumps({"settings": adjusted, "errors_db": metrics, "audition": report["audition"]}, indent=2))

    build_voice(["--midi"], inspect_audio=inspect, oversampling=4)


if __name__ == "__main__":
    main()
