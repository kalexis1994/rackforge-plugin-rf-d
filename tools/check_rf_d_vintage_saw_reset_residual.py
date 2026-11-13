"""Locate the vintage saw residual in the cycle and run a matched MP3 control."""
import argparse
import json
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory

import numpy as np

from check_rf_d_playable_voice import ROOT, SAMPLE_RATE, sha, write
from check_rf_d_vintage_saw_ab import NOTES, SOURCE, SOURCE_AUDIO, SOURCE_SHA256, SOURCE_WINDOWS, read_reference
from check_rf_d_vintage_saw_air import ANALYSIS, BANDS_HZ, band_power, fit_cycle, saw_phase
from check_rf_d_vintage_saw_phase import phase_corrections

RECEIPT = ROOT / "evidence/rf_d_vintage_saw_reset_residual01.json"
LAB = ROOT / "tmp/lab-current"
BAND = BANDS_HZ[2]
PREDICTOR_BAND = (4_000, 7_500)
PHASE_BINS = 8


def ffmpeg(executable, *args, pcm=None):
    result = subprocess.run([str(executable), "-hide_banner", "-loglevel", "error", *map(str, args)],
                            input=pcm, capture_output=True, check=True, timeout=30)
    return result.stdout


def decode(executable, path):
    data = ffmpeg(executable, "-i", path, "-ar", SAMPLE_RATE, "-ac", 2, "-f", "f32le", "-")
    return np.frombuffer(data, dtype="<f4").reshape(-1, 2).astype(np.float64)


def track(audio):
    phase, f0 = saw_phase(audio)
    phase += np.mean(phase_corrections(audio, phase), axis=0)
    return phase, fit_cycle(audio, phase, f0), f0


def bandpass(audio, band=BAND):
    pad = 2_400
    padded = np.pad(audio, pad, mode="reflect")
    frequencies = np.fft.rfftfreq(padded.size, 1. / SAMPLE_RATE)
    low, high = band
    mask = (frequencies >= low) & (frequencies < high)
    return np.fft.irfft(np.fft.rfft(padded) * mask, n=padded.size)[pad:-pad]


def relative_phase(phase, cycle):
    """Express phase in turns relative to the steepest fitted saw edge."""
    slope = abs(np.gradient(cycle, phase))
    edge = phase[ANALYSIS][np.argmax(slope[ANALYSIS])]
    return (phase - edge) / (2. * np.pi)


def measure(audio, phase, cycle, reference):
    fraction = np.mod(relative_phase(phase, cycle)[ANALYSIS] + 0.5 / PHASE_BINS, 1.)
    bins = (fraction * PHASE_BINS).astype(int)
    residual = audio - cycle
    high = bandpass(residual)[ANALYSIS]
    power = np.bincount(bins, weights=high**2, minlength=PHASE_BINS)
    count = np.bincount(bins, minlength=PHASE_BINS)
    return dict(
        residual_db_over_signal=float(10. * np.log10(band_power(residual)[0][2] / band_power(reference)[1])),
        energy_fraction_near_edge=float(power[0] / power.sum()),
        sample_fraction_near_edge=float(count[0] / count.sum()),
        bin_mean_square_db_over_mean=(10. * np.log10(power / count / np.mean(high**2))).tolist(),
    )


def edge_timing(audio, phase, cycle):
    """Use timing fitted in one frequency band to predict a disjoint band."""
    turns = relative_phase(phase, cycle)[ANALYSIS]
    periods = np.rint(turns).astype(int)
    near_edge = abs(turns - periods) < 0.5 / PHASE_BINS
    residual = audio - cycle
    derivative = np.gradient(cycle) * SAMPLE_RATE
    observed = [bandpass(residual, band)[ANALYSIS] for band in (PREDICTOR_BAND, BAND)]
    template = [bandpass(derivative, band)[ANALYSIS] for band in (PREDICTOR_BAND, BAND)]
    shifts = []
    power_before = power_after = 0.
    for period in np.unique(periods)[1:-1]:
        mask = near_edge & (periods == period)
        fitted = [np.dot(signal[mask], slope[mask]) / np.dot(slope[mask], slope[mask])
                  for signal, slope in zip(observed, template, strict=True)]
        prediction_error = observed[1][mask] - fitted[0] * template[1][mask]
        power_before += np.sum(observed[1][mask]**2)
        power_after += np.sum(prediction_error**2)
        shifts.append(fitted)
    shifts = np.asarray(shifts)
    return dict(
        cycles=len(shifts), shift_estimate_correlation=float(np.corrcoef(shifts.T)[0, 1]),
        predictor_shift_std_us=float(np.std(shifts[:, 0]) * 1e6),
        predicted_band_power_change_db=float(10. * np.log10(power_after / power_before)),
    )


def codec_control(executable, path, cycle, phase, original_level):
    fade = np.ones(cycle.size)
    fade[:480] = np.linspace(0., 1., 480)
    fade[-480:] = fade[:480][::-1]
    stereo = np.repeat((cycle * fade)[:, None], 2, axis=1).astype("<f4")
    ffmpeg(executable, "-f", "f32le", "-ar", SAMPLE_RATE, "-ac", 2, "-i", "-",
           "-ar", 44_100, "-c:a", "libmp3lame", "-b:a", "256k", "-y", path, pcm=stereo.tobytes())
    audio = decode(executable, path).mean(axis=1)
    assert abs(audio.size - cycle.size) <= 1, (audio.size, cycle.size)
    if audio.size < cycle.size:
        audio = np.pad(audio, (0, 1), mode="edge")
    audio = audio[:cycle.size]
    assert np.corrcoef(audio[ANALYSIS], cycle[ANALYSIS])[0, 1] > 0.999
    angle, recovered, _ = track(audio)
    return dict(
        decoded_residual=measure(audio, angle, recovered, original_level),
        decoded_minus_input=measure(audio, phase, cycle, original_level),
        decoded_minus_input_edge_timing=edge_timing(audio, phase, cycle),
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ffmpeg", required=True, type=Path)
    parser.add_argument("--source-mp3", required=True, type=Path)
    parser.add_argument("--write-report", action="store_true")
    args = parser.parse_args()
    if sha(args.source_mp3) != SOURCE_SHA256:
        raise SystemExit("Source MP3 hash differs from the archived reference")
    recording = decode(args.ffmpeg, args.source_mp3)
    codec_version = ffmpeg(args.ffmpeg, "-version").decode().splitlines()[0]
    report = dict(source=SOURCE, source_audio=SOURCE_AUDIO, source_sha256=SOURCE_SHA256,
                  source_pcm_hz=44_100, source_bitrate_kbps=256, source_channels=2,
                  analysis_rate_hz=SAMPLE_RATE, analysis_band_hz=BAND, predictor_band_hz=PREDICTOR_BAND,
                  phase_bins=PHASE_BINS,
                  codec_control=dict(encoder="libmp3lame", sample_rate_hz=44_100,
                                     bitrate_kbps=256, channels=2, ffmpeg=codec_version),
                  notes={})
    LAB.mkdir(exist_ok=True)
    with TemporaryDirectory(prefix="saw-codec-", dir=LAB) as temp:
        for (name, _), (start, end), previous in zip(NOTES, SOURCE_WINDOWS, read_reference(), strict=True):
            stereo = recording[round(start * SAMPLE_RATE):round(end * SAMPLE_RATE)]
            mono = stereo.mean(axis=1)
            assert np.corrcoef(mono, previous)[0, 1] > 0.99999
            phase, cycle, f0 = track(mono)
            channels = {}
            for channel, audio in zip(("mean", "left", "right"), (mono, *stereo.T), strict=True):
                angle, channel_cycle, _ = track(audio) if channel != "mean" else (phase, cycle, f0)
                channels[channel] = measure(audio, angle, channel_cycle, audio)
            report["notes"][name] = dict(
                window_seconds=[start, end], fundamental_hz=f0,
                stereo_correlation=float(np.corrcoef(stereo.T)[0, 1]),
                source=channels,
                source_edge_timing=edge_timing(mono, phase, cycle),
                codec_control=codec_control(args.ffmpeg, Path(temp) / "control.mp3", cycle, phase, mono),
            )
    if args.write_report:
        write(RECEIPT, report)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
