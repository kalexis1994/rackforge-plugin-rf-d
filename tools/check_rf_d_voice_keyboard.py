"""Verify the shared keyboard CV and pitch wheel through the staged voice."""
import numpy as np

from check_rf_d_playable_filter import change, filter_score, peak_frequency

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
