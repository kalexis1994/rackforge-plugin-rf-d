"""Separate the repeatable saw cycle from the high residual in the vintage A2."""
import argparse
import json
import wave

import numpy as np

from check_rf_d_ladder_trapezoidal_ab import AUDITION as PRIOR_AUDIO, RECEIPT as PRIOR_REPORT
from check_rf_d_oboe_ab import write_audition
from check_rf_d_playable_filter import peak_frequency, rms
from check_rf_d_playable_voice import ROOT, SAMPLE_RATE, sha, write
from check_rf_d_vintage_saw_ab import FRAMES, REFERENCE_SHA256, read_reference

AUDITION = ROOT / "artifacts/rf-d-la2-apertura-ab.wav"
RECEIPT = ROOT / "evidence/rf_d_vintage_saw_air01.json"
BANDS_HZ = ((4_000, 6_000), (6_000, 8_000), (8_000, 12_000), (12_000, 17_000))
ANALYSIS = slice(2_400, -2_400)
PHASE_SMOOTH_HZ = 22.
PERIODIC_BAND_LIMIT_HZ = 20_500
HIGH_PASS_HZ = (3_000, 4_000)


def read_renders():
    prior = json.loads(PRIOR_REPORT.read_bytes())
    if not PRIOR_AUDIO.is_file() or sha(PRIOR_AUDIO) != prior["audition"]["sha256"]:
        raise SystemExit(f"Expected the verified previous A/B at {PRIOR_AUDIO}")
    assert prior["reference_sha256"] == REFERENCE_SHA256
    with wave.open(str(PRIOR_AUDIO), "rb") as wav:
        assert (wav.getnchannels(), wav.getsampwidth(), wav.getframerate()) == (1, 2, SAMPLE_RATE)
        pcm = np.frombuffer(wav.readframes(wav.getnframes()), dtype="<i2").astype(np.float64) / 32768.
    return {clip["source"]: pcm[clip["start_frame"]:clip["start_frame"] + FRAMES]
            for clip in prior["audition"]["playlist"][:6]}


def saw_phase(audio):
    fundamental, _ = peak_frequency(audio[ANALYSIS])
    carrier = 2. * np.pi * fundamental * np.arange(audio.size) / SAMPLE_RATE
    baseband = audio * np.exp(-1j * carrier)
    half = 1_200
    t = np.arange(-half, half + 1) / SAMPLE_RATE
    kernel = np.sinc(2. * PHASE_SMOOTH_HZ * t) * np.hanning(t.size)
    envelope = np.convolve(np.pad(baseband, half, mode="reflect"), kernel / kernel.sum(), mode="valid")
    phase = carrier + np.unwrap(np.angle(envelope))
    assert np.all(np.diff(phase) > 0.)
    return phase, fundamental


def fit_cycle(audio, phase, fundamental):
    harmonics = np.arange(1, int(PERIODIC_BAND_LIMIT_HZ / fundamental) + 1)
    angles = phase[:, None] * harmonics
    basis = np.column_stack((np.ones(audio.size), np.cos(angles), np.sin(angles)))
    weights = np.linalg.lstsq(basis[ANALYSIS], audio[ANALYSIS], rcond=None)[0]
    return basis @ weights


def periodic_component(audio):
    phase, fundamental = saw_phase(audio)
    return fit_cycle(audio, phase, fundamental), np.diff(phase[ANALYSIS]) * SAMPLE_RATE / (2. * np.pi)


def high_residual(residual):
    padded = np.pad(residual, FRAMES // 2, mode="reflect")
    f = np.fft.rfftfreq(padded.size, 1. / SAMPLE_RATE)
    low, high = HIGH_PASS_HZ
    transition = np.clip((f - low) / (high - low), 0., 1.)
    response = 0.5 - 0.5 * np.cos(np.pi * transition)
    isolated = np.fft.irfft(response * np.fft.rfft(padded), n=padded.size)
    return isolated[FRAMES // 2:FRAMES // 2 + FRAMES]


def band_power(audio):
    segment = audio[ANALYSIS]
    weighted = (segment - segment.mean()) * np.hanning(segment.size)
    spectrum = abs(np.fft.rfft(weighted)) ** 2
    f = np.fft.rfftfreq(segment.size, 1. / SAMPLE_RATE)
    powers = [spectrum[(f >= lo) & (f < hi)].sum() for lo, hi in BANDS_HZ]
    return np.asarray(powers), spectrum.sum()


def describe(audio, periodic, pitch):
    total, power = band_power(audio)
    coherent, _ = band_power(periodic)
    residual, _ = band_power(audio - periodic)
    return dict(
        fundamental_hz_p05_p50_p95=np.percentile(pitch, [5, 50, 95]).tolist(),
        total_band_db_over_signal=(10. * np.log10(total / power)).tolist(),
        periodic_band_db_over_signal=(10. * np.log10(coherent / power)).tolist(),
        residual_band_db_over_signal=(10. * np.log10(residual / power)).tolist(),
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-report", action="store_true")
    args = parser.parse_args()
    original_a2, original_a3 = read_reference()
    renders = read_renders()
    signals = {
        "Minimoog La2": original_a2,
        "RF-D actual La2": renders["RF-D actual La2"],
        "RF-D trapezoidal La2": renders["RF-D trapezoidal La2"],
        "Minimoog La3": original_a3,
        "RF-D trapezoidal La3": renders["RF-D trapezoidal La3"],
    }
    measurements = {}
    for name, audio in signals.items():
        periodic, pitch = periodic_component(audio)
        measurements[name] = describe(audio, periodic, pitch)
        if name == "Minimoog La2":
            air = high_residual(audio - periodic)
            reduced = audio - air
            assert np.allclose(reduced + air, audio, rtol=0., atol=1e-15)
            assert 0.03 < rms(air[ANALYSIS]) / rms(audio[ANALYSIS]) < 0.2

    a2 = measurements["Minimoog La2"]
    rfd = measurements["RF-D trapezoidal La2"]
    assert min(np.asarray(a2["residual_band_db_over_signal"]) - rfd["residual_band_db_over_signal"]) > 20.
    reduced_power, _ = band_power(reduced)
    original_power, _ = band_power(original_a2)
    takes = {
        "Minimoog La2": original_a2[ANALYSIS],
        "Minimoog La2 con menos residuo agudo": reduced[ANALYSIS],
        "RF-D trapezoidal La2": renders["RF-D trapezoidal La2"][ANALYSIS],
    }
    report = dict(
        reference_sha256=REFERENCE_SHA256, previous_receipt_sha256=sha(PRIOR_REPORT),
        previous_audition_sha256=sha(PRIOR_AUDIO), sample_rate_hz=SAMPLE_RATE,
        analysis_frames=[ANALYSIS.start, FRAMES + ANALYSIS.stop], bands_hz=BANDS_HZ,
        phase_smooth_hz=PHASE_SMOOTH_HZ, periodic_band_limit_hz=PERIODIC_BAND_LIMIT_HZ,
        residual_high_pass_transition_hz=HIGH_PASS_HZ, measurements=measurements,
        reduction_band_delta_db=(10. * np.log10(reduced_power / original_power)).tolist(),
        audition=write_audition(takes, tuple(takes) * 2, AUDITION),
    )
    if args.write_report:
        write(RECEIPT, report)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
