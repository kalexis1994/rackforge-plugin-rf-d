"""Exercise MIDI 1.0 ownership, sustain and range through the RF-D voice."""
from collections import Counter

import numpy as np

from check_rf_d_playable_filter import change, peak_frequency, rms

HOST_SCORE = [
    [960, 0x90, 84, 100], [4111, 0x91, 24, 100], [7201, 0xb1, 64, 64],
    [10001, 0x81, 24, 0], [12599, 0x80, 84, 0], [15361, 0x9f, 57, 100],
    [17111, 0x9f, 57, 100], [19777, 0x8f, 57, 0], [21001, 0xb1, 121, 0],
    [24799, 0xbf, 120, 0], [29001, 0x91, 36, 100], [35555, 0xb1, 123, 0],
    *([[37001, 0x9f, 60, 100]] * 128), *([[37001, 0x8f, 60, 0]] * 128),
]


def sustain(frame, value):
    return [frame, 0xb0, 64, value, True]


def verify_midi(render, report):
    tone = [change(0, 100), change(1, 0), change(2, 25), change(6, 100), change(13, 0)]
    attack, release = [960, 0x90, 57, 100], [30001, 0x80, 57, 0]
    reference, _ = render([*tone, attack, release])
    same_channel = [*tone, attack, [8001, 0x90, 57, 1], [14001, 0x80, 57, 0], release]
    two_channels = [*tone, attack, [11001, 0x91, 57, 100], [14001, 0x90, 57, 0], [30001, 0x81, 57, 0]]
    assert all(np.array_equal(render(overlap)[0], reference) for overlap in (same_channel, two_channels))
    wrong_channel = [*tone, attack, [9001, 0x81, 57, 0], [10001, 0xb1, 120, 0],
                     [11001, 0xb1, 123, 0], release]
    assert np.array_equal(render(wrong_channel)[0], reference)

    pedal = [*tone, attack, sustain(8001, 64), [12001, 0x80, 57, 0]]
    for lift in (sustain(30001, 63), [30001, 0xb0, 121, 0]):
        assert np.array_equal(render([*pedal, lift])[0], reference)
    notes_off = [*tone, attack, sustain(8001, 127), [12001, 0xb0, 123, 0], sustain(30001, 0)]
    assert np.array_equal(render(notes_off)[0], reference)
    armed = [*tone, sustain(960, 127)]
    assert not np.any(render(armed)[0])

    resumed = [*pedal, [18001, 0x91, 69, 100], [24001, 0x81, 69, 0], sustain(30001, 0)]
    sustain_audio, _ = render(resumed)
    sustain_hz = [peak_frequency(sustain_audio[a:b])[0] for a, b in ((13000, 17000), (25000, 29000))]
    assert np.allclose(sustain_hz, [220., 440.], atol=0.1, rtol=0.)

    tail = [*tone, change(10, 1), change(5, 1000), attack]
    normal, _ = render([*tail, [12001, 0xb0, 123, 0]])
    stopped, _ = render([*tail, [12001, 0xb0, 120, 0]])
    assert np.array_equal(normal[:12001], stopped[:12001])
    panic_rms = [rms(audio[14500:16500]) for audio in (normal, stopped)]
    assert panic_rms[1] < 0.1 * panic_rms[0]
    st = [*tone, change(48, 1, 960), [960, 0x90, 69, 100]]
    assert np.array_equal(render(st)[0], render([*st, [12001, 0xb0, 120, 0]])[0])
    tuner = change(44, 1)
    assert np.array_equal(render([tuner])[0], render([tuner, [12001, 0xb0, 120, 0]])[0])

    score = [*tone, [960, 0x9f, 84, 100], [12001, 0x90, 24, 100],
             [24001, 0x80, 24, 0], [35001, 0x8f, 84, 0]]
    ranged, _ = render(score)
    pitches = [peak_frequency(ranged[a:b])[0] for a, b in ((3000, 11000), (14000, 23000), (26000, 34000))]
    expected = [440. * 2**((key - 69) / 12.) for key in (84, 24, 84)]
    assert np.allclose(pitches, expected, atol=0.1, rtol=0.)

    extremes = []
    for key, range_index in ((0, 5), (127, 3)):
        audio, _ = render([*tone, change(12, range_index), [960, 0x90, key, 100]])
        hz, purity = peak_frequency(audio[16000:40000])
        expected = 440. * 2**((key - 69) / 12.) * (4. if key == 0 else 1.)
        assert abs(hz - expected) < 0.1 and purity > 0.98, (key, hz, purity)
        extremes.append(hz)
    highest = [*tone, change(12, 5), change(45, 2.)]
    high_note = [960, 0x90, 127, 100]
    cold, _ = render([*highest, change(14, 0), change(14, 1, 960), high_note])
    assert not np.any(cold)
    warm, _ = render([*highest, high_note])
    warm_peak = float(np.max(abs(warm)))
    warm_tail = float(np.max(abs(warm[24000:])))
    assert 0. < warm_peak and warm_tail < 1e-6, (warm_peak, warm_tail)

    literal = [[*event, True] for event in HOST_SCORE]
    host_case, times = render(literal)
    assert all(np.array_equal(host_case, render(literal, block)[0]) for block in (127, 480, 4096))
    report["midi_audio"] = dict(low_priority_hz=pitches, sustained_pitch_hz=sustain_hz, extremes_hz=extremes,
                                panic_release_rms=dict(all_notes_off=panic_rms[0], all_sound_off=panic_rms[1]),
                                duplicate_and_channel_ownership_bit_exact=True,
                                simultaneous_events=max(Counter(event[0] for event in HOST_SCORE).values()),
                                over_band_silent=True,
                                over_band_from_running_oscillator=dict(transient_peak=warm_peak, late_peak=warm_tail),
                                live_node_128_ns=dict(median=int(np.median(times)), maximum=max(times)))
