"""Audio checks for the noise mixer and MIDI modulation paths."""
import numpy as np

from check_rf_d_playable_filter import change, peak_frequency, rms

RATE = 48_000


def octave_tilt(audio):
    length = 8192
    windows = [audio[start:start + length] for start in range(RATE // 4, len(audio) - length, length // 2)]
    power = np.mean(abs(np.fft.rfft(np.array(windows) * np.hanning(length), axis=1))**2, axis=0)
    hz = np.fft.rfftfreq(length, 1. / RATE)
    low = power[(150 <= hz) & (hz < 300)].mean()
    high = power[(1200 <= hz) & (hz < 2400)].mean()
    return float(10. * np.log10(low / high))


def carrier(audio):
    frequencies = np.fft.fftfreq(len(audio), 1. / RATE)
    spectrum = np.fft.fft(audio)
    spectrum[(frequencies < 140.) | (frequencies > 320.)] = 0.
    analytic = 2. * np.fft.ifft(spectrum)
    frequency = np.diff(np.unwrap(np.angle(analytic))) * RATE / (2. * np.pi)
    return abs(analytic), frequency


def verify_modulation(render, report, *, cutoff=67):
    frames = 3 * RATE
    key = [960, 0x90, 57, 100]
    loudness = [change(1, 0), change(6, 100)]
    mixer = [change(0, 100), *loudness, change(14, 0), change(30, 20), change(31, 1)]
    white, _ = render([*mixer, key], frames=frames)
    pink, _ = render([*mixer, change(29, 1), key], frames=frames)
    off, _ = render([*mixer, change(31, 0), key], frames=frames)
    tilts = [octave_tilt(audio) for audio in (white, pink)]
    assert not np.any(off) and min(rms(white), rms(pink)) > 0.005
    assert 5. < tilts[1] - tilts[0] < 14., tilts

    solo = [change(0, 100), *loudness, change(2, 15), change(13, 0)]
    unloaded, _ = render([*solo, key])
    loaded, _ = render([*solo, change(30, 0), change(31, 1), key])
    load_ratio = rms(loaded[12000:]) / rms(unloaded[12000:])
    assert 0.24 < load_ratio < 0.27, load_ratio

    source = [change(0, cutoff), *loudness, change(13, 0),
              change(20, 0), change(21, 0), change(24, 0), change(25, 0)]
    wheel = [4801, 0xb0, 1, 127]
    neutral, _ = render([*source, key], frames=frames)
    destinations_off, _ = render([*source, key, wheel], frames=frames)
    no_wheel, _ = render([*source, change(33, 1), change(34, 1), key], frames=frames)
    assert np.array_equal(neutral, destinations_off) and np.array_equal(neutral, no_wheel)
    pitch, _ = render([*source, change(33, 1), key, wheel, [100801, 0xb0, 121, 0]], frames=frames)
    filter_only, _ = render([*source, change(34, 1), key, wheel], frames=frames)
    assert np.array_equal(pitch[:4801], neutral[:4801])
    _, pitch_hz = carrier(pitch)
    neutral_envelope, _ = carrier(neutral)
    filter_envelope, filter_hz = carrier(filter_only)
    window = slice(24000, 96000)
    pitch_span = np.quantile(pitch_hz[window], [0.02, 0.98])
    reset_hz = peak_frequency(pitch[112000:136000])[0]
    filter_carrier_hz = peak_frequency(filter_only[window])[0]
    filter_phase_std = float(np.std(filter_hz[window] - 220.))
    filter_ratio = float(np.quantile(filter_envelope[window], 0.90) / np.quantile(filter_envelope[window], 0.10))
    assert pitch_span[0] < 205. and pitch_span[1] > 235., pitch_span
    assert abs(reset_hz - 220.) < 0.1 and abs(filter_carrier_hz - 220.) < 0.1, (reset_hz, filter_carrier_hz)
    assert filter_ratio > 2. and rms(filter_envelope[window] - neutral_envelope[window]) > 0.01

    red_score = [*source, change(32, 100), change(33, 1), key, wheel]
    red, _ = render(red_score, frames=frames)
    red_alt_osc3, _ = render([*source, change(20, 5), change(21, 3), *red_score[len(source):]], frames=frames)
    pink_control, _ = render([*source, change(29, 1), *red_score[len(source):]], frames=frames)
    assert np.array_equal(red, red_alt_osc3)
    assert rms(red[window] - neutral[window]) > 0.01 and rms(pink_control[window] - red[window]) > 0.01

    combined = [*source, change(19, 1), change(24, 1), change(26, 82), change(29, 1),
                change(30, 35), change(31, 1), change(32, 55), change(33, 1), change(34, 1),
                key, wheel, change(29, 0, 16001), [24001, 0xb0, 1, 63], [31001, 0x80, 57, 0]]
    active, timing = render(combined)
    assert all(np.array_equal(active, render(combined, block)[0]) for block in (127, 480, 4096))
    assert 0.05 < float(np.max(abs(active))) < 1.
    report["modulation_audio"] = dict(
        white_rms=rms(white), pink_rms=rms(pink), white_low_high_db=tilts[0], pink_low_high_db=tilts[1],
        pink_excess_low_db=tilts[1] - tilts[0], noise_branch_load_ratio=load_ratio,
        pitch_quantiles_hz=list(map(float, pitch_span)), pitch_reset_hz=reset_hz,
        filter_only_carrier_hz=filter_carrier_hz, filter_only_phase_frequency_std_hz=filter_phase_std,
        filter_envelope_ratio=filter_ratio,
        red_and_pink_difference_rms=rms(red[window] - pink_control[window]),
        combined_peak=float(np.max(abs(active))),
        combined_node_128_ns=dict(median=int(np.median(timing)), maximum=max(timing)))
