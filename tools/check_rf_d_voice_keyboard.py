"""Verify the shared keyboard CV and pitch wheel through the staged voice."""
import numpy as np

from check_rf_d_playable_filter import change, filter_score, peak_frequency, rms

RATE = 48_000
LATENCY = 48


def frequency(audio, start, stop):
    return peak_frequency(audio[start:stop])[0]


def verify_keyboard(render, report, *, cutoff=65):
    base = [change(0, 100), change(1, 0), change(6, 100), change(13, 0)]
    glide = [change(35, 1), change(36, 500)]
    notes = [[960, 0x90, 69, 100], [12001, 0x90, 57, 100], [42001, 0x80, 57, 0]]
    score = [*base, *glide, *notes]
    slide, times = render(score, frames=72_000)
    assert all(np.array_equal(slide, render(score, block, frames=72_000)[0])
               for block in (127, 480, 4096))
    assert abs(frequency(slide, 5000, 11000) - 440.) < 0.1
    observed = []
    expected = []
    for start, source, target, time in ((12001, 69, 57, 0.125), (12001, 69, 57, 0.25),
                                         (12001, 69, 57, 0.5), (42001, 57, 69, 0.125)):
        center = start + LATENCY + round(RATE * time)
        note = target + (source - target) * 0.01**(time / 0.5)
        expected.append(440. * 2**((note - 69.) / 12.))
        observed.append(frequency(slide, center - 768, center + 768))
    assert np.allclose(observed, expected, atol=3.0, rtol=0.), (observed, expected)

    released, _ = render([*base, *glide, change(10, 1), change(5, 2000),
                          [960, 0x90, 57, 100], [12001, 0x80, 57, 0],
                          [12001, 0x90, 69, 100], [18001, 0x80, 69, 0]])
    held_release = [frequency(released, start, start + 4200) for start in (19000, 27000)]
    release_hz = 440. * 2**(-0.01**0.25)
    assert np.allclose(held_release, [release_hz] * 2, atol=0.2, rtol=0.), held_release

    wheel = [[12001, 0xe0, 127, 127], [24001, 0xe0, 0, 0], [36001, 0xb0, 121, 0]]
    key = [960, 0x90, 57, 100]
    bent, _ = render([*base, key, *wheel], frames=51_000)
    bends = [frequency(bent, start, start + 6400) for start in (3500, 14500, 26500, 39000)]
    assert np.allclose(bends, [220., 220. * 2**0.5, 220. / 2**0.5, 220.], atol=0.1, rtol=0.)
    osc3 = [*base, change(14, 0), change(21, 0), change(24, 1)]
    tracked, _ = render([*osc3, key, *wheel], frames=51_000)
    assert abs(frequency(tracked, 14500, 20900) - 220. * 2**0.5) < 0.1
    free = [*osc3, change(25, 0), key]
    assert np.array_equal(render(free)[0], render([*free, *wheel])[0])

    filter_cv = filter_score(note=69, thirds=3, cutoff=cutoff)
    filter_bend = filter_cv + wheel
    assert np.array_equal(render(filter_cv)[0], render(filter_bend)[0])
    filter_glide = sorted([*filter_cv, *glide, [12001, 0x90, 57, 100]], key=lambda event: event[0])
    filtered, _ = render(filter_glide)
    tracking = [frequency(filtered, a, b) for a, b in ((7000, 11000), (17400, 18600), (38000, 42400))]
    assert tracking[0] > 780. and 450. < tracking[1] < 650. and 395. < tracking[2] < 420., tracking

    report["keyboard_audio"] = dict(glide_hz=observed, expected_rc_hz=expected,
                                    release_held_hz=held_release, bend_hz=bends,
                                    filter_tracking_hz=tracking,
                                    node_128_ns=dict(median=int(np.median(times)), maximum=max(times)))


def verify_left_hand(render, report, *, cutoff):
    pitch, mod, glide, decay, glide_r, decay_r = range(49, 55)
    tone = [change(0, 100), change(1, 0), change(6, 100), change(13, 0)]
    note = [960, 0x90, 69, 100]
    lower = [12001, 0x90, 57, 100]
    legato = [*tone, change(36, 500), note, lower]
    slide, _ = render(sorted([*legato, change(35, 1)]))
    switched, _ = render(sorted([*legato, change(glide, 1)]))
    assert np.array_equal(slide, switched)
    assert np.array_equal(slide, render(sorted([*legato, change(35, 1), change(glide_r, 0.125)]))[0])

    timing_ms = 1 + 499 * (0.125 * 1000 * np.log(100)) / (499 + 0.125 * 1000 * np.log(100))
    faster, _ = render(sorted([*legato, change(glide_r, 0.125)]))
    equivalent, _ = render(sorted([*tone, change(35, 1), change(36, timing_ms), note, lower]))
    np.testing.assert_allclose(faster, equivalent, atol=2e-8, rtol=0)
    handoff_score = sorted([*legato, change(glide, 1, 11999), change(glide, 0, 21001)])
    handoff, _ = render(handoff_score)
    assert np.array_equal(handoff[:21001], slide[:21001])
    assert abs(frequency(handoff, 22000, 28000) - 220.) < 0.1
    assert all(np.array_equal(handoff, render(handoff_score, block)[0]) for block in (127, 480, 4096))

    release_time = 18001
    held = [*tone, change(5, 500), note, [release_time, 0x80, 69, 0]]
    fast, _ = render(held)
    slow, _ = render(sorted([*held, change(10, 1)]))
    contact, _ = render(sorted([*held, change(decay, 1, 17000)]))
    opened, _ = render(sorted([*held, change(decay_r, 0.001)]))
    assert np.array_equal(slow, contact)
    assert np.array_equal(slow, render(sorted([*held, change(10, 1), change(decay_r, 0.001)]))[0])
    assert np.array_equal(opened[:release_time], fast[:release_time])
    releases = [rms(audio[19900:21600]) for audio in (fast, opened, slow)]
    assert releases[0] < releases[1] < releases[2], releases
    muted = filter_score(note=69, thirds=0, cutoff=cutoff)[:-1]
    filtered = [*muted, change(1, 80), change(9, 100), change(8, 600), note, [release_time, 0x80, 69, 0]]
    short, _ = render(sorted(filtered))
    long, _ = render(sorted([*filtered, change(decay, 1)]))
    assert np.array_equal(long[:release_time], short[:release_time])
    filter_tail = [rms(audio[22200:26700]) for audio in (short, long)]
    filter_hz = frequency(long, 22200, 26700)
    assert filter_tail[1] > 10 * filter_tail[0] and filter_hz > 100., (filter_tail, filter_hz)

    wave = [*tone, change(20, 0), change(21, 0), change(25, 0), change(33, 1), note]
    gestures = [*wave, [12001, 0xe0, 0, 127], [15001, 0xb0, 1, 93], [24001, 0xb0, 121, 0]]
    automation = [*wave, change(pitch, 16256, 12001), change(mod, 93, 15001),
                  change(pitch, 8192, 24001), change(mod, 0, 24001)]
    midi_audio, _ = render(sorted(gestures))
    touch_audio, _ = render(sorted(automation))
    assert np.array_equal(midi_audio, touch_audio)
    report["left_hand_audio"] = dict(glide_rc_ms=timing_ms, pedal_release_rms=releases,
                                     filter_tail_rms=filter_tail, filter_enabled_release_hz=filter_hz,
                                     panel_matches_midi_bit_exact=True,
                                     pedal_handoff_partitions_bit_exact=True)
