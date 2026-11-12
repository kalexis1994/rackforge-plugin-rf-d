"""Exercise the virtual LO cable in a running voice."""
import numpy as np

from check_rf_d_playable_filter import change, rms
from check_rf_d_voice_external import sine


def verify_feedback(render, report, output=False):
    frames = 57600
    note_on = [960, 0x90, 57, 100]
    note_off = [48000, 0x80, 57, 0]
    tone = [change(0, 88), change(1, 0), change(6, 100), change(13, 0), change(2, 25)]
    ext = [change(37, 1), change(38, 100)]
    cable = change(40, 1)

    def play(controls, **options):
        return render([*controls, note_on, note_off], frames=frames, **options)

    open_loop, _ = play([*tone, *ext])
    medium, _ = play([*tone, *ext, change(38, 25), cable])
    high, _ = play([*tone, *ext, cable])
    with_capture, readout = play([*tone, *ext, cable], samples=sine(0.9, frames))
    assert np.array_equal(high, with_capture)
    quieter_output, _ = play([*tone, *ext, cable, change(3, 25)])
    window = slice(24000, 45000)
    if output:
        assert rms(quieter_output[window]) < 0.4 * rms(medium[window])
    else:
        assert np.allclose(quieter_output[window], medium[window] * 0.25, atol=2e-6, rtol=0.)
    levels = [rms(audio[window]) for audio in (open_loop, medium, high)]
    assert 0.01 < levels[0] < levels[1] < levels[2], levels
    assert levels[1] > 1.12 * levels[0] and levels[2] > 1.5 * levels[0], levels
    assert float(np.max(abs(high))) < 1.
    if output:
        assert np.max(abs(high[-960:])) < 0.01
    else:
        assert not np.any(high[50000:])

    muted, _ = play([*tone, *ext, change(37, 0), cable])
    reference, _ = play(tone)
    assert np.array_equal(muted, reference)
    no_excitation, _ = play([*tone, *ext, change(14, 0), cable])
    assert not np.any(no_excitation)

    switched = [*tone, *ext, note_on, change(40, 1, 8001), change(3, 35, 18001),
                change(38, 83, 28009), change(40, 0, 39001), note_off]
    switched_samples = sine(0.07, frames)
    switched_audio, switched_stats = render(switched, samples=switched_samples)
    assert all(np.array_equal(switched_audio, render(switched, block, samples=switched_samples)[0])
               for block in (127, 480, 4096))
    report["feedback_audio"] = dict(
        rms_open_medium_high=levels, high_peak=float(np.max(abs(high))),
        overload_peak=max(readout["overload"]), release_peak_after_2000=float(np.max(abs(high[50000:]))),
        swapped_gain_output_peak=float(np.max(abs(quieter_output[window]))),
        switch_node_128_ns=dict(median=int(np.median(switched_stats["timings"])),
                                maximum=max(switched_stats["timings"])))
