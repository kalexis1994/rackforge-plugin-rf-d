"""Check the reference tone, R21 and the C19/C21 monitor branch."""
import numpy as np

from check_rf_d_playable_filter import change, rms
from headphone_amp_active_ac_reference import conditional_headphone_amp_ac
from output_diode_reference import diode_model_from_reference


def amplitude(signal, frequency):
    cycles = np.exp(-2j * np.pi * frequency / 48000. * np.arange(len(signal)))
    return float(2. * abs(np.dot(signal.astype(np.float64), cycles)) / len(signal))


def expected_ratio(frequency, level):
    # Use the full linearized amplifier, with the Thevenin source of the R21 cursor.
    circuit = conditional_headphone_amp_ac(
        frequency_hz=frequency, transistor_is_a=1e-14, beta_forward=160, beta_reverse=5,
        temperature_k=300, diode_model=diode_model_from_reference(
            ideality=1.5, forward_voltage_at_100ma_v=0.7, temperature_k=300),
        tip_load_ohm=32, ring_load_ohm=32,
    )
    base = circuit["node_v_per_pin7_v"]["Q16_BASE"]
    input_admittance = (1. - base) * (2j * np.pi * frequency * 2.5e-6)
    lower, upper = 5000. * level, 6000. - 5000. * level
    source = 1. / (1. / lower + 1. / upper)
    pin7 = lower / (lower + upper) / (1. + source * input_admittance)
    hi_cursor = 1. / (1. / 5000. + 1. / 34000.)
    hi = hi_cursor / (1000. + hi_cursor)
    return float(abs(pin7 * circuit["j7_tip_v_per_pin7_v"]) / hi)


def verify_monitor(render, report):
    phones, main_off, tuner = change(42, 2), change(41, 0), change(44, 1)
    window = slice(19200, 38400)
    hi, _ = render([tuner])
    lo, _ = render([change(42, 1), tuner])
    j7, times = render([phones, tuner])
    muted_phones, _ = render([phones, change(43, 0), tuner])
    muted_main, _ = render([main_off, tuner])
    silent, _ = render([phones])
    assert not np.any(muted_phones) and not np.any(muted_main) and not np.any(silent)
    j7_main_off, _ = render([main_off, phones, tuner])
    j7_zero_main_level, _ = render([phones, change(3, 0), tuner])
    assert all(amplitude(signal[window], 440) > 0.002 for signal in (j7_main_off, j7_zero_main_level))
    assert np.array_equal(hi, render([change(11, 100), change(0, 0), tuner])[0])
    assert np.array_equal(hi, render([change(43, 0), tuner])[0])
    assert np.allclose(lo, hi / 34., rtol=0., atol=3e-10)
    peaks = {}
    for name, audio in (("hi", hi), ("lo", lo), ("phones", j7)):
        signal = audio[window]
        crossing = np.flatnonzero((signal[:-1] < 0.) & (signal[1:] >= 0.))
        exact = crossing - signal[crossing] / (signal[crossing + 1] - signal[crossing])
        frequency = float((len(exact) - 1) * 48000. / (exact[-1] - exact[0]))
        peak = amplitude(signal, 440)
        assert abs(frequency - 440.) < 0.001
        assert abs(rms(signal) * np.sqrt(2.) / peak - 1.) < 1e-6
        peaks[name] = dict(frequency_hz=frequency, amplitude=peak)

    # Drive the shared VCA output with two in-band frequencies through EXT.
    frames = np.arange(43200)
    samples = 0.075 * (np.sin(2. * np.pi * 40. * frames / 48000.) +
                      np.sin(2. * np.pi * 440. * frames / 48000.))
    score = [change(0, 100), change(1, 0), change(14, 0), change(37, 1),
             change(38, 55), [960, 0x90, 57, 100]]
    external_hi, _ = render(score, samples=samples)
    assert np.max(abs(external_hi)) < 0.8
    response = {}
    for level in (0.25, 0.5, 1.):
        external_j7, _ = render([phones, change(43, level * 100.), *score], samples=samples)
        response[level] = {}
        for frequency in (40, 440):
            ratio = amplitude(external_j7[window], frequency) / amplitude(external_hi[window], frequency)
            expected = expected_ratio(frequency, level)
            assert abs(ratio / expected - 1.) < 0.002, (level, frequency, ratio, expected)
            response[level][frequency] = dict(measured=ratio, expected=expected)

    # Compare the direct endpoints with the same feedback loop running while monitoring Phones.
    loop = [change(37, 1), change(38, 72), change(40, 1), tuner, [960, 0x90, 57, 100]]
    loop_hi, _ = render(loop)
    loop_j7, _ = render([phones, *loop])
    switched = [*loop, change(42, 2, 8001), change(42, 1, 14111),
                change(42, 2, 16111), change(41, 0, 19201), change(44, 0, 24001),
                change(43, 82, 25559), change(44, 1, 27001)]
    dynamic, _ = render(switched)
    assert np.array_equal(dynamic[:8001], loop_hi[:8001])
    assert np.array_equal(dynamic[8300:14111], loop_j7[8300:14111])
    assert np.allclose(dynamic[14400:16111], loop_hi[14400:16111] / 34., atol=6e-9, rtol=0.)
    assert rms(dynamic[21120:23520]) > 0.002
    assert all(np.array_equal(dynamic, render(switched, block)[0]) for block in (127, 480, 4096))
    report["monitor_audio"] = dict(tuner=peaks, phones_tuner_main_off=amplitude(j7_main_off[window], 440),
                                   phones_tuner_main_level_zero=amplitude(j7_zero_main_level[window], 440),
                                   phones_hi_transfer=response, phones_tuner_node_128_ns=dict(
                                       median=int(np.median(times)), maximum=max(times)))
