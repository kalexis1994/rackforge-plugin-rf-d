"""Compare a sustained RF-D saw with the 1974 Minimoog oscillator demo."""
import argparse
import json
import wave

import numpy as np

from check_rf_d_oboe_ab import PREROLL, VOICE_DELAY, score, write_audition
from check_rf_d_playable_filter import peak_frequency
from check_rf_d_playable_voice import ROOT, SAMPLE_RATE, main as build_voice, sha, write

SOURCE = "https://www.amazona.de/vergleichstest-moog-minimoog-vs-vst-software-clones/"
SOURCE_AUDIO = "https://www.amazona.de/wp-content/uploads/2012/05/11_minimoog_oszis.mp3"
SOURCE_SHA256 = "324700b7d8f521db4826ffae403a1fc5c465f4af3342e9f91895de6ea289ce7b"
SOURCE_WINDOWS = ((0.60, 1.10), (2.35, 2.85))
REFERENCE = ROOT / "references-local/amazona-minimoog-1974-saw.wav"
REFERENCE_SHA256 = "515e9706a619c367bbcdb73c4f56669c7e7c5df566259824036c782af09d5aad"
AUDITION = ROOT / "artifacts/rf-d-sierra-vintage-ab.wav"
RECEIPT = ROOT / "evidence/rf_d_vintage_saw_ab01.json"
FRAMES = SAMPLE_RATE // 2
NOTES = (("La2", 45), ("La3", 57))
HARMONICS = np.arange(1, 25)
SETTINGS = dict(
    osc1_enabled=True, osc1_range=3, osc1_wave=2, saw_mix=50,
    osc2_enabled=False, osc3_enabled=False,
    cutoff=100, emphasis=0, contour_amount=0, filter_modulation=False,
    filter_tracking_one_third=False, filter_tracking_two_thirds=False, oscillator_modulation=False,
    loudness_attack=1, loudness_sustain=100, output_level=50,
)


def read_reference():
    if not REFERENCE.is_file() or sha(REFERENCE) != REFERENCE_SHA256:
        raise SystemExit(f"Expected the verified private excerpt at {REFERENCE}")
    with wave.open(str(REFERENCE), "rb") as wav:
        assert (wav.getnchannels(), wav.getsampwidth(), wav.getframerate(), wav.getnframes()) == (
            1, 2, SAMPLE_RATE, len(NOTES) * FRAMES,
        )
        pcm = np.frombuffer(wav.readframes(wav.getnframes()), dtype="<i2")
    return pcm.reshape(len(NOTES), FRAMES).astype(np.float64) / 32768.


def spectrum(audio):
    frequencies = []
    partials = []
    for segment in np.split(audio, 5):
        frequency, _ = peak_frequency(segment)
        weighted = (segment - segment.mean()) * np.hanning(len(segment))
        phase = -2j * np.pi * frequency * np.arange(len(segment)) / SAMPLE_RATE
        amplitude = abs(np.exp(HARMONICS[:, None] * phase) @ weighted)
        partials.append((amplitude / amplitude[0]) ** 2)
        frequencies.append(frequency)
    return np.asarray(frequencies), np.asarray(partials)


def compare(reference, render, schema):
    takes = {}
    measurements = []
    start = PREROLL + VOICE_DELAY + 4_800
    for (name, note), original, source_window in zip(NOTES, reference, SOURCE_WINDOWS, strict=True):
        ref_pitch, ref_power = spectrum(original)
        nominal = 440. * 2. ** ((note - 69) / 12.)
        tune = round(float(1200. * np.log2(np.median(ref_pitch) / nominal)), 1)
        assert abs(tune) < 50., tune
        events = score(schema, controls=dict(SETTINGS, tune=tune), keys=((0, 700, note),), wheel=())
        rendered, _ = render(events, frames=start + FRAMES, block=128)
        repeat, _ = render(events, frames=start + FRAMES, block=480)
        assert np.array_equal(rendered, repeat)
        candidate = rendered[start:]
        rfd_pitch, rfd_power = spectrum(candidate)
        assert abs(1200. * np.log2(np.median(rfd_pitch) / np.median(ref_pitch))) < 2.
        reference_power = ref_power.mean(axis=0)
        candidate_power = rfd_power.mean(axis=0)
        bands = {}
        for low, high in ((2, 7), (8, 16), (17, 24)):
            mask = (HARMONICS >= low) & (HARMONICS <= high)
            delta = 10. * np.log10(candidate_power[mask].sum() / reference_power[mask].sum())
            bands[f"H{low}-H{high}"] = float(delta)
        measurements.append(dict(
            note=name, midi=note, source_window_seconds=source_window, tune_cents=tune,
            frequency_hz=dict(minimoog=ref_pitch.tolist(), rf_d=rfd_pitch.tolist()),
            harmonic_db_over_fundamental=dict(minimoog=(10. * np.log10(reference_power)).tolist(),
                                              rf_d=(10. * np.log10(candidate_power)).tolist()),
            rf_d_minus_minimoog_band_db=bands,
        ))
        takes[f"Minimoog {name}"] = original - original.mean()
        takes[f"RF-D {name}"] = candidate - candidate.mean()
    return takes, measurements


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-report", action="store_true")
    args = parser.parse_args()
    reference = read_reference()
    reports = {}
    for oversampling in (2, 4):
        def inspect(render, schema, component):
            takes, measurements = compare(reference, render, schema)
            report = dict(component_sha256=component, notes=measurements, bit_equal_block_frames=[128, 480])
            if oversampling == 4:
                report["audition"] = write_audition(takes, tuple(takes) * 2, AUDITION)
            reports[f"{oversampling}x"] = report

        build_voice(["--midi"], inspect_audio=inspect, oversampling=oversampling)

    result = dict(
        source=SOURCE, source_audio=SOURCE_AUDIO, source_audio_sha256=SOURCE_SHA256,
        source_provenance="1974 Minimoog declared by owner. Line routing and cutoff setting unverified.",
        reference_sha256=REFERENCE_SHA256, sample_rate_hz=SAMPLE_RATE, frames_per_note=FRAMES,
        rf_d_settings=SETTINGS, oversampling=reports,
    )
    if args.write_report:
        write(RECEIPT, result)
    for mode, report in reports.items():
        print(mode, json.dumps([n["rf_d_minus_minimoog_band_db"] for n in report["notes"]]))
    print(json.dumps(reports["4x"]["audition"], indent=2))


if __name__ == "__main__":
    main()
