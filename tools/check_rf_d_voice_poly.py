"""Verify the optional polyphonic path through the RF-D WASM ABI."""
import numpy as np

from check_rf_d_playable_filter import change, rms


def verify_polyphony(render, report):
    notes = (48, 52, 55, 62, 66, 69)
    tone = [change(0, 100), change(1, 0), change(2, 32),
            change(6, 100), change(13, 0), change(4, 2)]

    def measure(signal, keys, begin=6000, end=18000):
        span = signal[begin:end].astype(np.float64)
        window = np.hanning(len(span))
        frequencies = 440. * np.exp2((np.array(keys) - 69.) / 12.)
        phase = -2j * np.pi * frequencies[:, None] * np.arange(len(span)) / 48000.
        return (2. * abs(np.exp(phase) @ (span * window)) / window.sum()).tolist()

    levels = {}
    for count in range(2, 7):
        keys = notes[:count]
        score = [change(55, count - 1), *tone, *([961, 0x90, note, 100] for note in keys),
                 *([23001, 0x80, note, 0] for note in keys)]
        audio, _ = render(score)
        levels[count] = measure(audio, keys)
        assert min(levels[count]) > 0.009, (count, levels[count])
        assert not np.any(audio[:961])
        assert rms(audio[41000:]) < 0.001
        assert np.array_equal(audio, render(score, 4096)[0]), count

    shared = [change(55, 1), *tone, [961, 0x90, 48, 100], [961, 0x91, 55, 100]]
    steal = [*shared, [19001, 0x90, 62, 100], [20001, 0x80, 48, 0]]
    audio, _ = render(steal)
    after = measure(audio, (48, 55, 62), 24000, 39000)
    assert after[0] < 0.001 and min(after[1:]) > 0.009, after
    assert all(np.array_equal(audio, render(steal, block)[0]) for block in (127, 480, 4096))

    sustain = [*shared, [6001, 0xb0, 64, 127, True], [7001, 0x80, 48, 0],
               [20001, 0xb0, 64, 0, True]]
    audio, _ = render(sustain)
    assert min(measure(audio, (48, 55), 10000, 19000)) > 0.009
    after = measure(audio, (48, 55), 31000, 42000)
    assert after[0] < 0.001 and after[1] > 0.009, after
    wrong_channel = [*shared, [19001, 0x82, 48, 0], [21001, 0xb2, 120, 0, True]]
    assert np.array_equal(render(wrong_channel)[0], render(shared)[0])

    transition = [*shared, change(55, 5, 10001), [10001, 0x90, 69, 100],
                  change(55, 0, 23001), [23001, 0x90, 60, 100], [32001, 0x80, 60, 0]]
    switched, _ = render(transition)
    assert all(np.array_equal(switched, render(transition, size)[0]) for size in (127, 480, 4096))
    assert min(measure(switched, (60,), 26500, 31500)) > 0.009
    report["polyphony_audio"] = dict(counts=levels, oldest_note_reassigned=True,
                                    channel_sustain=True, mode_changes_sample_accurate=True)
