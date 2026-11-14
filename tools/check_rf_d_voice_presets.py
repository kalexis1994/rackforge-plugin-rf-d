"""Build the factory program table and verify its playable audio."""
import itertools
import json
import math
import re

import numpy as np

from check_rf_d_playable_filter import change, peak_frequency, rms
from rf_d_playable_build import ROOT, emit, sha

CATALOG_PATH = ROOT / "plugin/voice/presets.json"
FEATURES = {"oscillators", "filter", "modulation", "external", "feedback", "factory"}
FACTORY_SCORE = [
    [960, 0x90, 45, 100], [8001, 0xb0, 1, 100], [15601, 0x90, 37, 100],
    [24599, 0x80, 37, 0], [33401, 0x80, 45, 0], [38401, 0xb0, 1, 0],
]
WHISTLE_SCORE = [
    [960, 0x90, 57, 100], [22000, 0x90, 69, 100], [22000, 0x80, 57, 0],
    [39500, 0x80, 69, 0],
]
POLY_NOTES = (57, 64)
POLY_SCORE = [
    [960, 0x90, POLY_NOTES[0], 100], [1211, 0x90, POLY_NOTES[1], 100],
    [8001, 0xb0, 1, 65],
    [33401, 0x80, POLY_NOTES[0], 0], [33599, 0x80, POLY_NOTES[1], 0],
    [38401, 0xb0, 1, 0],
]


def factory_score(name, poly=False):
    if poly:
        return POLY_SCORE
    # With the mixer sources off, the ladder needs time to reach sustained resonance.
    return WHISTLE_SCORE if name == "ladder_whistle" else FACTORY_SCORE


def prepare_catalog(schema, features):
    data = json.loads(CATALOG_PATH.read_text(encoding="utf8"))
    assert data["schema_version"] == 1
    parameters = {parameter["id"]: parameter for parameter in schema["parameters"]}
    banks = {bank["id"]: bank for bank in data["banks"]}
    assert len(banks) == len(data["banks"])
    programs = {}
    descriptors = []
    seen = set()
    voice_mode = parameters.get("voice_mode")
    bank_modes = {"mono": 0, "poly": 1}
    for preset in data["presets"]:
        name = preset["id"]
        assert re.fullmatch(r"[a-z][a-z0-9_]*", name) and name not in seen, name
        seen.add(name)
        requirement = preset.get("requires")
        assert requirement is None or requirement in FEATURES, name
        if requirement is not None and requirement not in features:
            continue
        assert preset["bank"] in banks, name
        controls = {}
        for key, value in preset["parameters"].items():
            parameter = parameters[key]
            kind = parameter["kind"]
            assert not parameter["flags"].get("read_only", False), (name, key)
            if kind["type"] == "boolean":
                assert type(value) is bool, (name, key, value)
            elif kind["type"] == "enum":
                assert type(value) is int and value in {choice["value"] for choice in kind["choices"]}, (name, key)
            else:
                assert type(value) in (float, int) and math.isfinite(value), (name, key)
                assert kind["minimum"] <= value <= kind["maximum"], (name, key, value)
            controls[parameter["index"]] = float(value)
        if requirement == "factory":
            assert voice_mode is not None and "voice_mode" not in preset["parameters"], name
            controls[voice_mode["index"]] = float(bank_modes[preset["bank"]])
        programs[name] = controls
        # Historic patches remain callable by the lab profiles and regression probes.
        if not preset.get("legacy") or "factory" not in features:
            descriptors.append({key: value for key, value in preset.items()
                                if key not in ("parameters", "requires", "legacy")})
    assert next(iter(programs)) == "default" and not programs["default"]
    active_banks = {preset["bank"] for preset in descriptors}
    descriptors.sort(key=lambda preset: (banks[preset["bank"]]["order"], preset["order"]))
    if "factory" in features:
        assert active_banks == bank_modes.keys() and descriptors[0]["id"] == "classic_saw"
    catalog = dict(schema_version=1, banks=[bank for bank in banks.values() if bank["id"] in active_banks],
                   presets=descriptors)
    return catalog, programs


def emit_program_table(programs):
    rows = []
    for name, parameters in programs.items():
        values = ", ".join(f"({index}, {value!r})" for index, value in sorted(parameters.items()))
        rows.append(f'    ("{name}", &[{values}]),\n')
    return emit("voice-programs.rs", "pub const PRESETS: &[(&str, &[(u32, f64)])] = &[\n" + "".join(rows) + "];\n")


def dyad_levels(audio):
    # A short window retains percussive attacks and avoids wheel modulation.
    span = audio[2100:7500].astype(np.float64)
    window = np.hanning(len(span))
    bins = abs(np.fft.rfft(span * window, 16384)) * (2. / window.sum())
    frequencies = np.fft.rfftfreq(16384, 1. / 48000.)
    return [float(max(bins[abs(frequencies - hz) < 0.023 * hz]))
            for hz in (440. * 2. ** ((note - 69) / 12.) for note in POLY_NOTES)]


def verify_presets(render, programs, factory, report):
    measurements = report["factory_audio"] = {}
    recordings = {"mono": {}, "poly": {}}
    for name, bank in factory.items():
        poly = bank == "poly"
        score = factory_score(name, poly)
        audio, times = render(score, preset=name)
        controls = [change(index, value) for index, value in programs[name].items()]
        reference, _ = render([*controls, *score])
        assert np.array_equal(audio, reference), name
        assert np.array_equal(audio, render(score, 4096, preset=name)[0]), name
        assert not np.any(audio[:960]), name
        peak = float(max(abs(audio)))
        sustained = name == "ladder_whistle"
        level = rms(audio[16000:20000] if sustained else audio[2100:7600])
        release = audio[40300:42600] if sustained else audio[34200:36500]
        assert 0.01 < level < 0.65 and peak < 0.97 and np.isfinite(audio).all(), (name, level, peak)
        measurements[name] = dict(
            bank=bank, mode="Poly 2" if poly else "Mono",
            peak=peak, first_phrase_rms=level, release_rms=rms(release),
            max_node_128_ns=max(times),
        )
        if poly:
            levels = dyad_levels(audio)
            assert min(levels) > 0.004, (name, levels)
            measurements[name]["dyad_fundamentals"] = levels
        if sustained:
            low, low_purity = peak_frequency(audio[16000:21500])
            high, high_purity = peak_frequency(audio[32000:39000])
            assert min(low_purity, high_purity) > 0.98
            assert abs(high / low / 2. - 1.) < 0.035, (low, high)
            measurements[name]["tracking_hz"] = [low, high]
        else:
            recordings[bank][name] = audio
    for bank, audio in recordings.items():
        for left, right in itertools.combinations(audio, 2):
            difference = rms(audio[left][1700:32900] - audio[right][1700:32900])
            assert difference > 0.01, (bank, left, right, difference)
    recordings = recordings["mono"]
    quiet = [event for event in FACTORY_SCORE if event[1:3] != [0xb0, 1]]
    dry, _ = render(quiet, preset="wheel_vibrato")
    wheel = recordings["wheel_vibrato"]
    assert np.array_equal(dry[:8001], wheel[:8001])
    assert rms(dry[11000:14800] - wheel[11000:14800]) > 0.03
    for name in ("amber_reed", "shutter_pulse", "copper_sidebands"):
        if name in recordings:
            unwheeled, _ = render(quiet, preset=name)
            assert np.array_equal(unwheeled[:8001], recordings[name][:8001]), name
            wheel_delta = rms(unwheeled[10500:15200] - recordings[name][10500:15200])
            assert wheel_delta > 0.02, (name, wheel_delta)
            measurements[name]["wheel_delta_rms"] = wheel_delta
    assert measurements["interval_drone"]["release_rms"] > 5. * measurements["pulse_pluck"]["release_rms"]
    report["factory_catalog_sha256"] = sha(CATALOG_PATH)


def verify_host_presets(execute, render, folder, probe, package, schema, programs, report):
    samples = np.zeros(43200, dtype="<f4")
    capture = folder / "factory-capture.f32"
    capture.write_bytes(samples.tobytes())
    events = folder / "factory-score.bin"
    state = folder / "factory-state.bin"
    writable = [param for param in schema["parameters"] if param["kind"]["type"] != "meter"]
    mode = next(param["index"] for param in writable if param["id"] == "voice_mode")
    results = report["host_factory"] = {}

    def compare(name, block, expected, *state_args):
        raw, logs = execute(probe, package, folder / "state", capture, block, name, *state_args)
        audio = np.frombuffer(raw, dtype="<f4").reshape(2, len(samples), 2)
        assert np.array_equal(audio, np.broadcast_to(expected[None, :, None], audio.shape)), (name, block)
        rows = [line.split(",")[1:] for line in logs.decode().splitlines() if line.startswith("RF_D_EXT,")]
        assert [int(row[0]) for row in rows] == [2, 3]
        for _, count, maximum, misses, faults in rows:
            assert int(count) == (len(samples) + block - 1) // block and int(misses) == int(faults) == 0, (name, rows)
            if block == 128:
                assert int(maximum) < (block / 48000.) * 0.5e9, (name, rows)
        return [int(row[2]) for row in rows]

    for name, controls in programs.items():
        score = factory_score(name, controls[mode] > 0)
        events.write_bytes(b"".join(frame.to_bytes(4, "little") + bytes(message) for frame, *message in score))
        expected, _ = render(score, samples=samples, preset=name)
        catalog_max = compare(name, 128, expected, "-", events, state)
        values = [controls.get(param["index"], param["kind"]["default"]) for param in writable]
        assert state.read_bytes() == b"RFDC" + np.asarray(values, dtype="<f8").tobytes(), name
        restore_max = compare(name, 128, expected, state, events)
        results[name] = dict(state_bytes=state.stat().st_size, state_sha256=sha(state), catalog_128_max_ns=catalog_max,
                             restored_128_max_ns=restore_max)
        if name in ("glide_lead", "feedback_bass", "interval_drone"):
            results[name]["restored_larger_blocks_max_ns"] = {
                block: compare(name, block, expected, state, events) for block in (480, 4096)
            }
