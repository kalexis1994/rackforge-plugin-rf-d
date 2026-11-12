"""Contrast the staged output controls with an independent reduced C2 network."""
import numpy as np

from check_rf_d_playable_filter import change, rms


def response(level, frequency):
    """Solve the four resistive nodes for 1 V at the right side of C2."""
    lower = 5000. * level
    upper = 5000. - lower
    load_cursor = 1. / (1. / lower + 1. / 34000.)
    if upper == 0.:
        # A short joins pin 21 and HI.
        matrix = np.array([[1. / 1000. + 1. / lower + 1. / 33000., -1. / 33000.],
                           [-1. / 33000., 1. / 33000. + 1. / 1000.]])
        hi, lo = np.linalg.solve(matrix, [1. / 1000., 0.])
    else:
        matrix = np.array([
            [1. / 1000. + 1. / upper, -1. / upper, 0.],
            [-1. / upper, 1. / upper + 1. / lower + 1. / 33000., -1. / 33000.],
            [0., -1. / 33000., 1. / 33000. + 1. / 1000.],
        ])
        _, hi, lo = np.linalg.solve(matrix, [1. / 1000., 0., 0.])
    tau = 10e-6 / (1. / 6000. + 1. / (1000. + upper + load_cursor))
    delay = np.exp(-2j * np.pi * frequency / 96000.)
    pole = np.exp(-1. / (tau * 96000.))
    gain = float(abs(hi * pole * (1. - delay) / (1. - pole * delay)))
    return gain, float(lo / hi), float(tau)


def verify_output(render, report):
    tone = [change(0, 100), change(1, 0), change(2, 15), change(6, 100), change(13, 0)]
    note = [960, 0x90, 57, 100]
    release = [24001, 0x80, 57, 0]
    hi, _ = render([*tone, note, release])
    lo, _ = render([*tone, change(42, 1), note, release])
    half, _ = render([*tone, change(3, 50), note, release])
    off, _ = render([*tone, change(41, 0), note, release])
    zero, _ = render([*tone, change(3, 0), note, release])
    assert not np.any(off) and not np.any(zero)
    full_gain, divider, tau = response(1., 220.)
    half_gain, _, _ = response(0.5, 220.)
    assert np.allclose(lo, hi * divider, atol=6e-9, rtol=0.)
    window = slice(12000, 21600)
    attenuation = rms(half[window]) / rms(hi[window])
    assert abs(attenuation - half_gain / full_gain) < 0.001, attenuation

    tails = [rms(hi[start:start + 384]) for start in (26400, 28800)]
    assert tails[0] > tails[1] > 1e-9, tails
    expected_decay = np.exp(-(2400 / 48000.) / tau)
    assert abs(tails[1] / tails[0] - expected_decay) < 0.002, (tails, expected_decay)

    loop = [*tone, change(37, 1), change(38, 72), change(40, 1)]
    loop_hi, _ = render([*loop, note, release])
    loop_lo, _ = render([*loop, change(42, 1), note, release])
    assert np.allclose(loop_lo, loop_hi * divider, atol=6e-9, rtol=0.)
    switched = [*loop, note, change(41, 0, 8001), change(41, 1, 14001),
                change(42, 1, 19111), release]
    dynamic, times = render(switched)
    assert np.array_equal(loop_hi[:8001], dynamic[:8001])
    assert not np.any(dynamic[8300:14001]) and rms(dynamic[15500:18800]) > 0.01
    assert all(np.array_equal(dynamic, render(switched, block)[0]) for block in (127, 480, 4096))
    report["output_audio"] = dict(
        lo_hi_ratio=rms(lo[window]) / rms(hi[window]), half_level_ratio=attenuation,
        half_level_expected=half_gain / full_gain, c2_tau_s=tau, c2_tail_rms=tails,
        c2_tail_ratio=tails[1] / tails[0], c2_tail_expected=expected_decay,
        switched_node_128_ns=dict(median=int(np.median(times)), maximum=max(times)))
