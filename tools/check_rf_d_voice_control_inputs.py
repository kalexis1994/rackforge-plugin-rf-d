"""Verify the Model D's three control voltages and shorting trigger in the playable voice."""
import numpy as np

from check_rf_d_playable_filter import change, filter_score, linear_threshold, peak_frequency, rms
from check_rf_d_playable_pilot import emit, sha
from rf_d_cutoff_calibration import AMP_PER_STEP
from vca2_active_core_dc_reference import DEVICES, conditional_vca2_dc

PITCH_CV, FILTER_CV, LOUDNESS_CV, S_TRIGGER = range(45, 49)
WINDOW = slice(24000, 40000)


def collector_current(volts):
    return conditional_vca2_dc(
        q14_base_v=8., q13_base_v=8., q21_base_v=volts, wiper_v=9., balance_left_ohm=50.,
        is_a=dict.fromkeys(DEVICES, 1e-14), beta_forward=dict.fromkeys(DEVICES, 100.),
        beta_reverse=dict.fromkeys(DEVICES, 5.), temperature_k=298.15,
    )["devices"]["Q21"]["collector_a"]


def loudness_table(report):
    volts = np.linspace(0., 5., 101)
    current = np.array([collector_current(voltage) for voltage in volts])
    gain = (current - current[0]) / (current[-1] - current[0])
    reserved = (volts[:-1] + volts[1:]) * 0.5
    expected = np.array([(collector_current(voltage) - current[0]) /
                         (current[-1] - current[0]) for voltage in reserved])
    error = float(max(abs(np.interp(reserved, volts, gain) - expected)))
    assert np.all(np.diff(gain) > 0.) and error < 0.001
    path = emit("loudness-cv-coefficients.rs", f"pub const GAINS: [f64; {len(gain)}] = [\n" +
                "".join(f"    {value:.17e},\n" for value in gain) + "];\n")
    report["loudness_cv_table"] = dict(sha256=sha(path), knots=len(volts),
                                      reserved_points=len(reserved), max_gain_error=error,
                                      zero_collector_a=current[0], full_collector_a=current[-1])
    return path


def verify_control_inputs(render, report, *, cutoff=65):
    def frequency(audio, window=WINDOW):
        return peak_frequency(audio[window])[0]

    tone = [change(0, 100), change(1, 0), change(2, 18), change(6, 100), change(13, 0)]
    note = [960, 0x90, 57, 100]
    pitch = []
    for oscillator, shape, level in ((14, 13, 2), (19, 16, 18), (24, 21, 23)):
        voice = [*tone, change(14, 0), change(oscillator, 1),
                 change(shape, 0), change(level, 18), note]
        row = [frequency(render([change(PITCH_CV, voltage), *voice])[0])
               for voltage in (-1., 0., 1.)]
        assert np.allclose(row, [110., 220., 440.], atol=0.1, rtol=0.), (oscillator, row)
        pitch.append(row)
    free = [change(25, 0), *voice]
    assert np.array_equal(render(free)[0], render([change(PITCH_CV, 1.), *free])[0])

    filtered = filter_score(cutoff=cutoff)
    dry_filter, _ = render(filtered)
    filter_pitch = [frequency(render([change(FILTER_CV, voltage), *filtered])[0])
                    for voltage in (-1., 0., 1.)]
    ratios = [0.5, 1., 2.]
    expected_ratios = ratios
    if "cutoff_calibration" in report:
        tails = report["cutoff_calibration"]["knots_tail_a"]
        tail = np.interp(cutoff / 100., np.linspace(0., 1., len(tails)), tails)
        currents = tail * np.asarray(ratios)
        frequencies = np.asarray([linear_threshold(step)[1] for step in currents / (AMP_PER_STEP + currents)])
        expected_ratios = frequencies / frequencies[1]
    assert np.allclose(np.array(filter_pitch) / filter_pitch[1], expected_ratios, atol=0.025, rtol=0.), (
        filter_pitch, expected_ratios,
    )
    tracked, _ = render(filter_score(note=69, thirds=3, cutoff=cutoff))
    assert abs(filter_pitch[2] - frequency(tracked)) < 0.1
    assert np.array_equal(dry_filter, render([change(PITCH_CV, 1.), *filtered])[0])

    dry, _ = render([*tone, note])
    muted, _ = render([change(LOUDNESS_CV, 0.), *tone, note])
    assert not np.any(muted)
    assert np.array_equal(dry, render([change(LOUDNESS_CV, 5.), *tone, note])[0])
    minimum, maximum = collector_current(0.), collector_current(5.)
    gains = {}
    for voltage in (0.425, 1.275, 2.475, 3.825):
        audio, _ = render([change(LOUDNESS_CV, voltage), *tone, note])
        measured = rms(audio[WINDOW]) / rms(dry[WINDOW])
        expected = (collector_current(voltage) - minimum) / (maximum - minimum)
        assert abs(measured - expected) < 0.001, (voltage, measured, expected)
        gains[voltage] = dict(measured=measured, expected=expected)
    tuner = change(44, 1)
    assert np.array_equal(render([tuner])[0], render([change(LOUDNESS_CV, 0.), tuner])[0])

    closed = change(S_TRIGGER, 1, 960)
    opened = change(S_TRIGGER, 0, 32001)
    no_keyboard, _ = render([*tone, closed, opened])
    assert rms(no_keyboard[WINDOW.start:31000]) > 0.01
    assert rms(no_keyboard[-2000:]) < 0.001
    assert abs(frequency(no_keyboard, slice(12000, 28000)) - 440.) < 0.1
    continuous = [*tone, note, [32001, 0x80, 57, 0]]
    handoff = [*tone, note, change(S_TRIGGER, 1, 12001), [12001, 0x80, 57, 0],
               change(S_TRIGGER, 0, 24001), [24001, 0x90, 57, 100], [32001, 0x80, 57, 0]]
    assert np.array_equal(render(continuous)[0], render(handoff)[0])
    sustained = [*tone, closed, note, [12001, 0x80, 57, 0], [18001, 0xb0, 123, 0], opened]
    assert np.array_equal(render(continuous)[0], render(sustained)[0])
    contour = [*filter_score(cutoff=50)[:-1], change(1, 55), change(7, 125), change(9, 70)]
    filter_only, _ = render([*contour, closed, opened])
    keyboard_filter, _ = render([*contour, [960, 0x90, 69, 100], [32001, 0x80, 69, 0]])
    fixed_filter, _ = render([*contour, change(1, 0), closed, opened])
    assert np.array_equal(filter_only, keyboard_filter)
    filter_contour_hz = frequency(filter_only, slice(14000, 28000))
    filter_fixed_hz = frequency(fixed_filter, slice(14000, 28000))
    assert filter_contour_hz > 1.5 * filter_fixed_hz

    moving = sorted([*handoff, change(PITCH_CV, 1.5, 3751), change(FILTER_CV, -1.5, 12001),
                     change(LOUDNESS_CV, 1.75, 17203), change(PITCH_CV, -1.25, 19007),
                     change(FILTER_CV, 0.5, 24001), change(LOUDNESS_CV, 5., 28003)],
                    key=lambda event: event[0])
    swept, times = render(moving)
    assert all(np.array_equal(swept, render(moving, block)[0]) for block in (127, 480, 4096))
    report["control_inputs_audio"] = dict(pitch_hz=pitch, filter_hz=filter_pitch, loudness_gains=gains,
                                          trigger_no_keyboard_hz=frequency(no_keyboard, slice(12000, 28000)),
                                          trigger_filter_hz=dict(with_contour=filter_contour_hz,
                                                                 fixed_cutoff=filter_fixed_hz),
                                          trigger_gate_handoff_bit_exact=True,
                                          moving_node_128_ns=dict(median=int(np.median(times)), maximum=max(times)))
