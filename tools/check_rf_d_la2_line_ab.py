"""Render the four La2 conditions and, given documented WAVs, make a vintage A/B."""
import argparse
import json
import wave
from pathlib import Path

import numpy as np

from check_rf_d_oboe_ab import PREROLL, VOICE_DELAY, score, write_audition
from check_rf_d_playable_filter import rms
from check_rf_d_playable_voice import ROOT, SAMPLE_RATE, main as build_voice, sha, write
from check_rf_d_vintage_saw_ab import FRAMES, SETTINGS, spectrum
from check_rf_d_vintage_saw_air import BANDS_HZ, band_power
from check_rf_d_vintage_saw_phase import measure

AUDITION = ROOT / "artifacts/rf-d-la2-registros.wav"
VINTAGE_AB = ROOT / "artifacts/rf-d-la2-linea-ab.wav"
RECEIPT = ROOT / "evidence/rf_d_la2_line01.json"
VINTAGE_RECEIPT = ROOT / "evidence/rf_d_la2_line_ab01.json"
SETTLE_FRAMES = 4_800
PITCH_HZ = 110.
CUTOFFS = {"abierto": 100, "intermedio": 75}
REGISTERS = {"8": (3, 45), "16": (2, 57)}
CONTROLS = dict(
    SETTINGS, noise_enabled=False, external_enabled=False, output_feedback=False,
    tuner_a440=False, main_output_enabled=True, output_jack=0, glide_enabled=False,
)


def read_takes(manifest_path):
    manifest = json.loads(manifest_path.read_bytes())
    for field in ("unit", "line_chain", "settings_evidence"):
        if not isinstance(manifest.get(field), str) or not manifest[field].strip():
            raise ValueError(f"Describe the documented vintage capture in {field!r}")
    takes = {}
    metadata = {}
    cutoff = manifest.get("intermediate_cutoff_percent")
    if type(cutoff) is not int or not 0 < cutoff < 100:
        raise ValueError("Describe the intermediate cutoff as an integer percentage of panel travel")
    for register in REGISTERS:
        for position in CUTOFFS:
            label = f"{register}-{position}"
            entry = manifest["takes"][label]
            path = manifest_path.parent / entry["wav"]
            with wave.open(str(path), "rb") as wav:
                width = wav.getsampwidth()
                rate = wav.getframerate()
                channel = entry.get("channel", 1)
                start = round(entry["start_seconds"] * rate)
                frames = round(FRAMES * rate / SAMPLE_RATE)
                if (not 1 <= channel <= wav.getnchannels() or width not in (2, 3, 4) or rate < 40_000
                        or start < 0 or start + frames > wav.getnframes()):
                    raise ValueError(f"{label}: expected a 0.5 s sustain window in a PCM WAV of at least 40 kHz")
                channels = wav.getnchannels()
                wav.setpos(start)
                raw = wav.readframes(frames)
            if width == 3:
                octets = np.frombuffer(raw, dtype=np.uint8).astype(np.int32).reshape(-1, 3)
                pcm = (octets[:, 0] | octets[:, 1] << 8 | octets[:, 2] << 16)
                pcm = (pcm ^ 0x800000) - 0x800000
            else:
                pcm = np.frombuffer(raw, dtype=f"<i{width}")
            pcm = pcm.reshape(-1, channels)[:, channel - 1]
            full_scale = 2 ** (8 * width - 1)
            if len(pcm) != frames or np.any((pcm == -full_scale) | (pcm == full_scale - 1)):
                raise ValueError(f"{label}: truncated or clipped sustain window")
            takes[label] = at_render_rate(pcm.astype(np.float64) / full_scale, rate)
            metadata[label] = dict(file=path.name, sha256=sha(path), start_frame=start,
                                   source_rate_hz=rate, bits=width * 8, channel=channel)
    if len({(row["sha256"], row["start_frame"], row["channel"]) for row in metadata.values()}) != len(metadata):
        raise ValueError("Use distinct source windows for the four panel conditions")
    provenance = {key: manifest[key] for key in ("unit", "line_chain", "settings_evidence")}
    return takes, provenance, metadata, dict(CUTOFFS, intermedio=cutoff)


def at_render_rate(signal, rate):
    if rate == SAMPLE_RATE:
        return signal
    # Windowed sinc with a transition above the highest 17 kHz analysis band.
    half_width = int(np.ceil(rate * 128 / SAMPLE_RATE))
    offsets = np.arange(-half_width, half_width + 1)
    cutoff = 0.94 * min(1., SAMPLE_RATE / rate)
    window = np.hanning(offsets.size)
    padded = np.pad(signal, half_width + 1, mode="reflect")
    output = np.empty(FRAMES)
    for start in range(0, FRAMES, 1_024):
        stop = min(start + 1_024, FRAMES)
        positions = np.arange(start, stop) * rate / SAMPLE_RATE
        centers = positions.astype(int)[:, None]
        distance = positions[:, None] - centers - offsets
        kernel = np.sinc(cutoff * distance) * window
        samples = padded[centers + offsets + half_width + 1]
        output[start:stop] = np.sum(samples * kernel, axis=1) / kernel.sum(axis=1)
    return output


def bands_db_over_signal(audio):
    bands, total = band_power(audio)
    return (10. * np.log10(bands / total)).tolist()


def cents(frequency, target):
    return float(1200. * np.log2(frequency / target))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", type=Path, help="JSON manifest for the four vintage line takes")
    parser.add_argument("--write-report", action="store_true")
    args = parser.parse_args()
    reference, provenance, inputs, cutoffs = read_takes(args.reference) if args.reference else ({}, None, {}, CUTOFFS)
    report = dict(
        vintage=provenance, sample_rate_hz=SAMPLE_RATE, frames_per_take=FRAMES,
        rf_d_controls=CONTROLS, oversampling=4, ladder="trapezoidal", conditions=[], bands_hz=BANDS_HZ,
    )

    def inspect(render, schema, component):
        report["component_sha256"] = component
        takes = {}
        start = PREROLL + VOICE_DELAY + SETTLE_FRAMES
        for register, (osc1_range, midi) in REGISTERS.items():
            for position, cutoff in cutoffs.items():
                label = f"{register}-{position}"
                original = reference.get(label)
                target = PITCH_HZ
                if original is not None:
                    pitch, _ = spectrum(original)
                    target = float(np.median(pitch))
                    if max(abs(cents(hz, PITCH_HZ)) for hz in pitch) > 50.:
                        raise ValueError(f"{label}: the chosen window is not a sustained La2")
                    takes[f"Minimoog {label}"] = original
                tune = round(cents(target, PITCH_HZ), 1)
                controls = dict(CONTROLS, osc1_range=osc1_range, cutoff=cutoff, tune=tune)
                events = score(schema, controls=controls, keys=((0, 700, midi),), wheel=())
                rendered, _ = render(events, frames=start + FRAMES, block=128)
                repeat, _ = render(events, frames=start + FRAMES, block=480)
                assert np.array_equal(rendered, repeat), label
                candidate = rendered[start:]
                pitch, harmonics = spectrum(candidate)
                assert abs(cents(np.median(pitch), target)) < 2., (label, pitch, target)
                row = dict(
                    register_feet=int(register), midi_key=midi, cutoff_percent=cutoff,
                    tune_cents=tune, rf_d_rms_dbfs=20. * np.log10(rms(candidate)),
                    rf_d_harmonic_db_over_fundamental=(10. * np.log10(harmonics.mean(axis=0))).tolist(),
                    rf_d_band_db_over_signal=bands_db_over_signal(candidate),
                    rf_d_phase=measure(candidate),
                )
                if original is not None:
                    row["vintage_input"] = inputs[label]
                    row["vintage_band_db_over_signal"] = bands_db_over_signal(original)
                    row["vintage_phase"] = measure(original)
                report["conditions"].append(row)
                takes[f"RF-D {label}"] = candidate
        destination = VINTAGE_AB if reference else AUDITION
        report["bit_equal_block_frames"] = [128, 480]
        report["audition_gain_order"] = list(takes)
        report["audition"] = write_audition(takes, tuple(takes), destination, sample_width=3)

    build_voice(["--midi"], inspect_audio=inspect, oversampling=4, trapezoidal_ladder=True)
    if args.write_report:
        write(VINTAGE_RECEIPT if reference else RECEIPT, report)
    print(json.dumps(report["audition"], indent=2))


if __name__ == "__main__":
    main()
