"""Build the factory program table and verify its playable audio."""
import itertools
import json
import math
import re

import numpy as np

from check_rf_d_playable_filter import change, rms
from check_rf_d_playable_pilot import ROOT, emit, sha

CATALOG_PATH = ROOT / "plugin/voice/presets.json"
FEATURES = {"oscillators", "filter", "modulation", "external", "feedback", "factory"}
FACTORY_SCORE = [
    [960, 0x90, 45, 100], [8001, 0xb0, 1, 100], [15601, 0x90, 37, 100],
    [24599, 0x80, 37, 0], [33401, 0x80, 45, 0], [38401, 0xb0, 1, 0],
]


def prepare_catalog(schema, features):
    data = json.loads(CATALOG_PATH.read_text(encoding="utf8"))
    assert data["schema_version"] == 1
    parameters = {parameter["id"]: parameter for parameter in schema["parameters"]}
    banks = {bank["id"]: bank for bank in data["banks"]}
    assert len(banks) == len(data["banks"])
    programs = {}
    descriptors = []
    seen = set()
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
        programs[name] = controls
        descriptors.append({key: value for key, value in preset.items() if key not in ("parameters", "requires")})
    assert next(iter(programs)) == "default" and not programs["default"]
    active_banks = {preset["bank"] for preset in descriptors}
    catalog = dict(schema_version=1, banks=[bank for bank in banks.values() if bank["id"] in active_banks],
                   presets=descriptors)
    return catalog, programs


def emit_program_table(programs):
    rows = []
    for name, parameters in programs.items():
        values = ", ".join(f"({index}, {value!r})" for index, value in sorted(parameters.items()))
        rows.append(f'    ("{name}", &[{values}]),\n')
    return emit("voice-programs.rs", "pub const PRESETS: &[(&str, &[(u32, f64)])] = &[\n" + "".join(rows) + "];\n")


def verify_presets(render, programs, names, report):
    measurements = report["factory_audio"] = {}
    recordings = {}
    for name in names:
        audio, times = render(FACTORY_SCORE, preset=name)
        controls = [change(index, value) for index, value in programs[name].items()]
        reference, _ = render([*controls, *FACTORY_SCORE])
        assert np.array_equal(audio, reference), name
        assert np.array_equal(audio, render(FACTORY_SCORE, 4096, preset=name)[0]), name
        assert not np.any(audio[:960]), name
        peak = float(max(abs(audio)))
        level = rms(audio[3800:7600])
        assert 0.01 < level < 0.65 and peak < 0.97, (name, level, peak)
        measurements[name] = dict(
            peak=peak, first_note_rms=level, release_rms=rms(audio[34200:36500]),
            max_node_128_ns=max(times),
        )
        recordings[name] = audio
    for left, right in itertools.combinations(names, 2):
        difference = rms(recordings[left][1700:32900] - recordings[right][1700:32900])
        assert difference > 0.01, (left, right, difference)
    quiet = [event for event in FACTORY_SCORE if event[1:3] != [0xb0, 1]]
    dry, _ = render(quiet, preset="wheel_vibrato")
    wheel = recordings["wheel_vibrato"]
    assert np.array_equal(dry[:8001], wheel[:8001])
    assert rms(dry[11000:14800] - wheel[11000:14800]) > 0.03
    assert measurements["interval_drone"]["release_rms"] > 5. * measurements["pulse_pluck"]["release_rms"]
    report["factory_catalog_sha256"] = sha(CATALOG_PATH)


def verify_host_presets(execute, render, folder, probe, package, schema, programs, report):
    samples = np.zeros(43200, dtype="<f4")
    capture = folder / "factory-capture.f32"
    capture.write_bytes(samples.tobytes())
    events = folder / "factory-score.bin"
    events.write_bytes(b"".join(frame.to_bytes(4, "little") + bytes(message)
                                for frame, *message in FACTORY_SCORE))
    state = folder / "factory-state.bin"
    writable = [param for param in schema["parameters"] if param["kind"]["type"] != "meter"]
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
        expected, _ = render(FACTORY_SCORE, samples=samples, preset=name)
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
