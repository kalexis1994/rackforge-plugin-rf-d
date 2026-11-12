"""Linearized loop design and audio checks for the playable emphasis and keyboard controls."""
import math

import numpy as np

from check_rf_d_playable_pilot import emit, sha

RATE = 96_000
RECOVERY_TAU_S = 47e3 * 0.22e-6
RETURN_TAU_S = (1000. + 330.) * 10e-6
LOG2_MIN = -12
STEPS_PER_OCTAVE = 32


def linear_threshold(step):
    """Find the first negative-real crossing of the discrete open loop."""
    poles = [math.exp(-1. / (RATE * tau)) for tau in (RECOVERY_TAU_S, RETURN_TAU_S)]

    def loop(omega):
        delay = np.exp(-1j * omega)
        stage = step / (1. - (1. - step) * delay)
        capacitors = [pole * (1. - delay) / (1. - pole * delay) for pole in poles]
        phase = -omega + 4. * np.angle(stage) + sum(np.angle(value) for value in capacitors)
        return phase, abs(delay * stage**4 * math.prod(capacitors))

    low, high = 1e-12, 0.8
    if loop(high)[0] >= -np.pi:
        high = np.pi - 1e-6
    assert loop(low)[0] > -np.pi and loop(high)[0] < -np.pi
    for _ in range(48):
        middle = (low + high) / 2.
        if loop(middle)[0] > -np.pi:
            low = middle
        else:
            high = middle
    omega = (low + high) / 2.
    phase, magnitude = loop(omega)
    assert abs(phase + np.pi) < 1e-10
    return float(1. / magnitude), omega * RATE / (2. * np.pi)


def emphasis_table(report, *, calibrated=False):
    log2_max = -0.75 if calibrated else -2
    intervals = round((log2_max - LOG2_MIN) * STEPS_PER_OCTAVE)
    logs = LOG2_MIN + np.arange(intervals + 1) / STEPS_PER_OCTAVE
    gains = [linear_threshold(step)[0] for step in np.exp2(logs)]
    points = [linear_threshold(step)[0] for step in np.exp2((logs[:-1] + logs[1:]) / 2.)]
    error = max(abs((a + b) / (2. * exact) - 1.)
                for a, b, exact in zip(gains, gains[1:], points))
    assert error < 0.001
    source = f"""pub const LOG2_MIN: f64 = {float(LOG2_MIN)};
pub const STEPS_PER_OCTAVE: f64 = {float(STEPS_PER_OCTAVE)};
pub const RETURN_TAU_S: f64 = {RETURN_TAU_S:.16e};
pub const CRITICAL_GAIN: [f64; {len(gains)}] = [
""" + "".join(f"    {gain:.16e},\n" for gain in gains) + "];\n"
    path = emit("voice-emphasis.rs", source)
    report["emphasis_table"] = dict(knots=len(gains), internal_rate_hz=RATE,
                                    recovery_tau_s=RECOVERY_TAU_S, return_tau_s=RETURN_TAU_S,
                                    midpoint_relative_error=error, sha256=sha(path))
    return path


def change(index, value, frame=0):
    return [frame, 0xb1, 20 + index, value]


def filter_score(note=57, emphasis=100, thirds=0, cutoff=65, excite=False):
    return [
        change(0, cutoff), change(1, 0), change(6, 100), change(14, int(excite)),
        change(26, emphasis), change(27, thirds & 1), change(28, thirds >> 1),
        [960, 0x90, note, 100],
        *([change(14, 0, 7200)] if excite else []),
    ]


def peak_frequency(signal):
    signal = signal.astype(np.float64)
    signal -= signal.mean()
    fft_size = 2**18
    spectrum = abs(np.fft.rfft(signal * np.hanning(len(signal)), fft_size))
    peak = int(np.argmax(spectrum))
    left, center, right = np.log(spectrum[peak - 1:peak + 2])
    frequency = RATE / 2. / fft_size * (peak + 0.5 * (left - right) / (left - 2. * center + right))
    radius = int(14. * fft_size / (RATE / 2.))
    power = spectrum**2
    fraction = power[max(0, peak - radius):peak + radius + 1].sum() / power.sum()
    return float(frequency), float(fraction)


def rms(signal):
    return float(np.sqrt(np.mean(signal.astype(np.float64)**2)))


def verify_filter(render, report, *, cutoff=65):
    window = slice(24_000, 41_280)
    reference, _ = render(filter_score(cutoff=cutoff))
    off, _ = render(filter_score(emphasis=0, cutoff=cutoff))
    damped, _ = render(filter_score(emphasis=80, cutoff=cutoff, excite=True))
    assert not np.any(off)
    damping = [rms(damped[start:end]) for start, end in ((7500, 8000), (9000, 10500), (24000, 41280))]
    assert damping[0] > 0.005 and damping[2] < 0.001 * damping[0], damping
    baseline_hz, purity = peak_frequency(reference[window])
    level = rms(reference[window])
    assert 300. < baseline_hz < 700. and 0.02 < level < 0.7 and purity > 0.98, (baseline_hz, level, purity)
    assert 0.95 < rms(reference[32_000:40_000]) / rms(reference[20_000:28_000]) < 1.05

    frequencies = {}
    for thirds in (0, 1, 2, 3):
        moved, _ = render(filter_score(69, thirds=thirds, cutoff=cutoff))
        hz, _ = peak_frequency(moved[window])
        frequencies[thirds] = hz
        assert abs(hz / baseline_hz / (2**(thirds / 3.)) - 1.) < 0.035, (thirds, hz, baseline_hz)
        if not thirds:
            assert np.array_equal(reference, moved)

    legato_score = filter_score(69, thirds=3, cutoff=cutoff) + [[24001, 0x90, 57, 100], [48001, 0x80, 57, 0]]
    legato, times = render(legato_score, frames=72000)
    assert all(np.array_equal(legato, render(legato_score, block, frames=72000)[0])
               for block in (127, 480, 4096))
    legato_hz = [peak_frequency(legato[start:end])[0] for start, end in
                 ((12000, 23000), (36500, 47000), (60000, 71000))]
    assert np.allclose(legato_hz, [frequencies[3], baseline_hz, frequencies[3]], rtol=0.005), legato_hz

    corner = sorted(filter_score(72, thirds=3, cutoff=100, excite=True) +
                    [change(19, 1), change(24, 1), change(15, 5), change(20, 5),
                     change(0, 0, 11111), change(0, 100, 15555), change(26, 0, 21111)],
                    key=lambda event: event[0])
    extreme, _ = render(corner)
    extreme_peak = float(np.max(abs(extreme)))
    assert 0.005 < extreme_peak < 1.
    report["filter_audio"] = dict(free_oscillation_hz=baseline_hz, free_oscillation_rms=level,
                                  fundamental_power_fraction=purity, damped_tail_rms=damping,
                                  tracking_octave_up_hz=frequencies, legato_hz=legato_hz,
                                  extreme_peak=extreme_peak,
                                  legato_node_128_ns=dict(median=int(np.median(times)), maximum=max(times)))
