"""Measure the external preamp, overload readout and RackForge capture route."""
from pathlib import Path

import numpy as np

from check_rf_d_playable_filter import change, rms
from check_rf_d_playable_pilot import COMPILER, HOST, HOST_COMPILER, HOST_CORE, MIDI_LIB, ROOT, sha

RATE = 48000
KEY = [960, 0x90, 57, 100]
PRESET = [change(0, 100), change(1, 0), change(6, 100), change(14, 0), change(37, 1), change(38, 60)]


def sine(amplitude, frames=43200):
    return (amplitude * np.sin(2. * np.pi * 440. * np.arange(frames) / RATE)).astype("<f4")


def harmonic(signal, multiplier):
    window = signal[12000:36000]
    carrier = np.exp(-2j * np.pi * 440. * multiplier * np.arange(len(window)) / RATE)
    return float(2. * abs(window @ carrier) / len(window))


def verify_external(render, report):
    score = [*PRESET, KEY]
    quiet, quiet_metrics = render(score, samples=sine(0.025))
    high, high_metrics = render(score, samples=sine(0.95))
    direct = high
    for block in (127, 480, 4096):
        other, _ = render(score, block, samples=sine(0.95))
        assert np.array_equal(direct, other)
    silent, muted_metrics = render([*PRESET, change(37, 0), KEY], samples=sine(0.95))
    closed, _ = render(PRESET, samples=sine(0.95))
    assert not np.any(silent) and not np.any(closed)
    assert max(quiet_metrics["overload"]) == 0 and max(high_metrics["overload"]) > 0.99
    assert high_metrics["overload"] == muted_metrics["overload"]
    burst = sine(0.95)
    burst[18000:] = 0.
    _, burst_metrics = render(score, samples=burst)
    assert max(burst_metrics["overload"]) > 0.99 and burst_metrics["overload"][-1] < 0.001
    first = [harmonic(audio, 1) for audio in (quiet, high)]
    third = [harmonic(audio, 3) / fundamental for audio, fundamental in zip((quiet, high), first)]
    peak = float(np.max(abs(high)))
    assert 0.005 < first[0] < first[1] and first[1] / first[0] < 20., first
    assert 0.05 < peak < 1., peak
    assert third[0] < 0.01 and third[1] > 0.08, third

    tone = [change(0, 100), change(1, 0), change(6, 100), change(2, 10), change(13, 0)]
    dry, _ = render([*tone, KEY])
    with_input, _ = render([*tone, KEY], samples=sine(0.95))
    assert np.array_equal(dry, with_input)
    loaded, _ = render([*tone, change(37, 1), change(38, 0), KEY], samples=sine(0.95))
    load_ratio = rms(loaded[12000:36000]) / rms(dry[12000:36000])
    assert 0.49 < load_ratio < 0.52, load_ratio
    mix, metrics = render([*tone, change(19, 1), change(24, 1), change(26, 70), change(31, 1),
                           change(33, 1), change(34, 1), change(37, 1), change(38, 80),
                           KEY, [6001, 0xb0, 1, 96]], samples=sine(0.95))
    assert 0.01 < float(np.max(abs(mix))) < 1.
    dirty = sine(0.95)
    dirty[4000:4005] = [np.nan, np.inf, -np.inf, 2., -2.]
    sanitized = dirty.copy()
    sanitized[~np.isfinite(sanitized)] = 0.
    sanitized = sanitized.clip(-1., 1.)
    assert np.array_equal(render(score, samples=dirty)[0], render(score, samples=sanitized)[0])
    report["external_audio"] = dict(
        fundamental=first, saturated_peak=peak, third_harmonic_ratio=third, connected_load_ratio=load_ratio,
        overload_peak=max(high_metrics["overload"]), overload_after_burst=burst_metrics["overload"][-1],
        mixed_peak=float(np.max(abs(mix))), mixed_node_128_ns=dict(median=int(np.median(metrics["timings"])),
                                                                  maximum=max(metrics["timings"])))


def verify_host_capture(execute, render, folder, package, report, feedback=False, monitor_schema=None):
    deps = HOST / "target/release/deps"
    core, midi = deps / HOST_CORE, deps / MIDI_LIB
    registry = Path(COMPILER).parents[4] / ".cargo/registry/src"
    imports = sorted(registry.glob("*/windows_x86_64_msvc-*/lib/*.lib"))
    libraries = sorted((HOST / "target/release/build").glob("*/out/*.lib"))
    native_dirs = list(dict.fromkeys(p.parent for p in [*libraries, *imports]))
    source = ROOT / "tools/rf_d_voice_external_host.rs"
    probe = folder / "external-rack.exe"
    execute(HOST_COMPILER, "--edition=2021", "-C", "opt-level=3", "-L", f"dependency={deps}",
            *[arg for path in native_dirs for arg in ("-L", f"native={path}")],
            source, "--extern", f"rackforge_core={core}", "--extern", f"rackforge_midi_api={midi}", "-o", probe)
    samples = sine(0.65)
    fixture = folder / "capture.f32"
    fixture.write_bytes(samples.tobytes())

    def compare(preset, controls, receipt, independent, state=None):
        expected, _ = render([*controls, KEY], samples=samples)
        missing = expected if independent else np.zeros_like(expected)
        capture = report[receipt] = {}
        for block in (128, 480, 4096):
            state_args = (state,) if state is not None else ()
            raw, logs = execute(probe, package, folder / "state", fixture, block, preset, *state_args)
            stereo = np.frombuffer(raw, dtype="<f4").reshape(2, len(samples), 2)
            for audio, target in zip(stereo, (expected, missing)):
                assert np.array_equal(audio[:, 0], target) and np.array_equal(audio[:, 1], target), (preset, block)
            measured = [line.split(",")[1:] for line in logs.decode().splitlines() if line.startswith("RF_D_EXT,")]
            assert [int(row[0]) for row in measured] == [2, 3]
            assert all(int(count) == (len(samples) + block - 1) // block and int(faults) == 0
                       for _, count, _, _, faults in measured)
            capture[block] = [{"capture_input": int(channel), "blocks": int(count), "max_ns": int(maximum),
                               "deadline_misses": int(misses)} for channel, count, maximum, misses, _ in measured]

    compare("external_filter", PRESET, "host_capture", independent=False)
    if feedback:
        loop = [change(0, 78), change(2, 75), change(3, 90), change(26, 32),
                change(37, 1), change(38, 72), change(40, 1)]
        compare("loop_drive", loop, "host_feedback", independent=True)
    if monitor_schema is not None:
        overrides = {41: 0., 42: 2., 43: 65., 44: 1.}
        values = [overrides.get(parameter["index"], parameter["kind"]["default"])
                  for parameter in monitor_schema["parameters"] if parameter["index"] != 39]
        state = folder / "monitor-state.bin"
        state.write_bytes(b"RFDC" + np.asarray(values, dtype="<f8").tobytes())
        controls = [change(index, value) for index, value in overrides.items()]
        compare("monitor", controls, "host_monitor", independent=True, state=state)
        for result in report["host_monitor"][128]:
            assert result["deadline_misses"] == 0 and result["max_ns"] < 128e9 / RATE / 2, result
    report["host_capture_libraries"] = {library.name: sha(library) for library in (core, midi)}
