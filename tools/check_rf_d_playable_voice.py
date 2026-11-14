"""Build and exercise the playable RF-D voice in WASM and RackForge."""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np

from prepare_long_note_aa import taps
from rf_d_playable_build import (
    AREA, COMPILER, GUEST, HOST, NODE, PACKAGE, ROOT, SDK_PATH, WASM_OPT, emit, sha, write,
)
from check_rf_d_playable_filter import emphasis_table, verify_filter
from check_rf_d_playable_modulation import verify_modulation
from check_rf_d_voice_keyboard import verify_keyboard, verify_left_hand
from check_rf_d_voice_external import verify_external, verify_host_capture
from check_rf_d_voice_feedback import verify_feedback
from check_rf_d_voice_output import verify_output
from check_rf_d_voice_monitor import verify_monitor
from check_rf_d_voice_control_inputs import loudness_table, verify_control_inputs
from check_rf_d_voice_midi import HOST_SCORE, verify_expression, verify_midi
from check_rf_d_voice_poly import verify_polyphony
from check_rf_d_voice_presets import emit_program_table, prepare_catalog, verify_presets
from rf_d_cutoff_calibration import calibrated_cutoff_table
from rf_d_voice_panel import program_parameters, render_panel, render_program_config

VERSION = "0.7.0"
EXE = ".exe" if os.name == "nt" else ""
PLUGIN_ID = "org.rackforge.lab.rf-d-voice"
SCHEMA = ROOT / "plugin/voice/parameters.json"
CONTROL_LAYOUT = SCHEMA.with_name("control-layout.json")
CAPACITY = 4096
SAMPLE_RATE = 48_000
MARGIN_NS = 128 * 1e9 / SAMPLE_RATE / 2
CONTROL_ROLES = {
    "synth.oscillator.noise.level": "noise_level",
    "synth.filter.cutoff": "cutoff",
    "synth.filter.resonance": "emphasis",
    "synth.filter.envelope.amount": "contour_amount",
    "synth.envelope.amp.attack": "loudness_attack",
    "synth.envelope.amp.decay": "loudness_decay",
    "synth.envelope.amp.sustain": "loudness_sustain",
    "performance.modulation": "mod_wheel",
    "performance.expression": "loudness_cv",
}


def oscillator_tables(report, *, calibrated=False, wide_pulse_duty=None):
    # The admitted stationary spectrum is stored as data so a release does
    # not depend on reproducing the laboratory's Windows float hashes.
    spectrum_path = SCHEMA.with_name("oscillator-h128.json")
    spectrum = json.loads(spectrum_path.read_text(encoding="utf8"))
    report["h128_sha256"] = spectrum["h128_table_sha256"]
    report["oscillator_spectrum_sha256"] = sha(spectrum_path)
    assert spectrum["keyboard_cv_v"] == -1.6 and spectrum["mixer_bus_v"] == 0.
    model = np.asarray([spectrum["waveforms"][name] for name in ("saw", "triangle")])
    assert model.shape == (2, 129, 2) and np.isfinite(model).all()
    harmonics = np.arange(1, 129)
    bands = (128, 64, 32, 16, 8, 4, 2, 1)
    samples = 2048
    saw, triangle = model[:, 1:, 0] + 1j * model[:, 1:, 1]
    hybrid = (10. * saw + 47. * triangle) / 57.
    wide = 0.35
    if calibrated:
        evidence = ROOT / "evidence/vco1_circuit_validation.json"
        measured = json.loads(evidence.read_bytes())
        assert measured["passed"]
        wide = measured["result"]["pulse_duties"]["11"]["high"]
        report["wide_pulse"] = dict(duty=wide, contact=11, source_sha256=sha(evidence))
    if wide_pulse_duty is not None:
        assert 0.15 < wide_pulse_duty < 0.5
        wide = wide_pulse_duty
        report["wide_pulse"] = dict(duty=wide, source="laboratory override")
    widths = (0.5, wide, 0.15)
    pulses = [2. * np.sin(np.pi * harmonics * width) * np.exp(-1j * np.pi * harmonics * width)
              / (np.pi * harmonics) for width in widths]
    waves = []
    for shape in (triangle, hybrid, saw, *pulses):
        tables = []
        for count in bands:
            spectrum = np.r_[0., 2. * shape[:count]]
            tables.append(np.fft.ifft(spectrum, n=samples).real * samples)
        tables = np.array(tables)
        waves.append(tables / abs(tables).max())
    waves = np.asarray(waves, dtype="<f4")
    leakage = max(float(np.max(abs(np.fft.rfft(waves[:, index], axis=-1)[:, count + 1:]))) / samples
                  for index, count in enumerate(bands))
    assert leakage < 1e-7 and float(abs(waves).max()) <= 1.
    report["oscillator_tables"] = dict(harmonics=bands, samples=samples, pulse_duties=widths,
                                       shape=list(waves.shape), maximum_out_of_band_coefficient=leakage)
    rust = [f"pub const SAMPLES: usize = {samples};",
            f"pub const HARMONICS: [u16; {len(bands)}] = {list(bands)};",
            f"pub static WAVES: [[[f32; SAMPLES]; {len(bands)}]; {len(waves)}] = ["]
    for shape in waves:
        rust.append("    [")
        rust.extend("        [" + ",".join(f"{value:.9e}" for value in band) + "]," for band in shape)
        rust.append("    ],")
    path = emit("voice-oscillators.rs", "\n".join([*rust, "];", ""]))
    report["oscillator_tables"]["sha256"] = sha(path)
    return path


def parameter_schema(bank, emphasis, modulation, performance, external, feedback, output, monitor, control_inputs,
                     left_hand=False, polyphony=False):
    schema = json.loads(SCHEMA.read_text(encoding="utf8"))
    if bank:
        extra = json.loads(SCHEMA.with_name("oscillators.json").read_text(encoding="utf8"))
        for page in schema["pages"]:
            page["order"] += len(extra["pages"])
        schema["pages"] = extra["pages"] + schema["pages"]
        schema["parameters"][2]["name"] = "OSC 1 Level"
        schema["parameters"][3]["order"] = 6
        schema["parameters"].extend(extra["parameters"])
    if emphasis:
        extra = json.loads(SCHEMA.with_name("filter.json").read_text(encoding="utf8"))
        schema["parameters"][1]["order"] = 2
        schema["parameters"].extend(extra["parameters"])
    if modulation:
        extra = json.loads(SCHEMA.with_name("modulation.json").read_text(encoding="utf8"))
        schema["pages"].extend(extra["pages"])
        schema["parameters"].extend(extra["parameters"])
    if performance:
        extra = json.loads(SCHEMA.with_name("performance.json").read_text(encoding="utf8"))
        schema["pages"].extend(extra["pages"])
        schema["parameters"].extend(extra["parameters"])
    if external:
        extra = json.loads(SCHEMA.with_name("external.json").read_text(encoding="utf8"))
        schema["parameters"].extend(extra["parameters"])
    if feedback:
        extra = json.loads(SCHEMA.with_name("feedback.json").read_text(encoding="utf8"))
        schema["parameters"].extend(extra["parameters"])
    if output:
        extra = json.loads(SCHEMA.with_name("output.json").read_text(encoding="utf8"))
        schema["parameters"][3].update(page="output", order=0)
        schema["pages"].extend(extra["pages"])
        schema["parameters"].extend(extra["parameters"])
    if monitor:
        schema["parameters"][-1]["kind"]["choices"].append({"value": 2, "name": "Phones"})
        extra = json.loads(SCHEMA.with_name("monitor.json").read_text(encoding="utf8"))
        schema["parameters"].extend(extra["parameters"])
    if control_inputs:
        extra = json.loads(SCHEMA.with_name("control_inputs.json").read_text(encoding="utf8"))
        schema["pages"].extend(extra["pages"])
        schema["parameters"].extend(extra["parameters"])
    if left_hand:
        extra = json.loads(SCHEMA.with_name("left_hand.json").read_text(encoding="utf8"))
        schema["parameters"].extend(extra["parameters"])
    if polyphony:
        assert left_hand
        extra = json.loads(SCHEMA.with_name("polyphony.json").read_text(encoding="utf8"))
        schema["parameters"].extend(extra["parameters"])
    schema["parameters"].sort(key=lambda parameter: parameter["index"])
    parameters = {parameter["id"]: parameter for parameter in schema["parameters"]}
    schema["schema_version"] = 2
    schema["semantic_controls"] = [
        dict(role=role, parameter_index=parameters[name]["index"])
        for role, name in CONTROL_ROLES.items() if name in parameters
    ]
    for parameter in parameters.values():
        if parameter["kind"].get("unit") == "ms":
            parameter["kind"]["taper"] = "logarithmic"
    return schema


def package_template(destination, schema, catalog, version, bank, external, programs=False):
    shutil.copytree(PACKAGE, destination)
    write(destination / "metadata/parameters.json", schema)
    write(destination / "metadata/presets.json", catalog)
    if programs:
        layout = json.loads(CONTROL_LAYOUT.read_text(encoding="utf8"))
        assert layout["plugin_id"] == PLUGIN_ID
        parameters = {parameter["id"]: parameter for parameter in schema["parameters"]
                      if not parameter["flags"].get("read_only", False)}
        assert all(binding["parameter_id"] in parameters for binding in layout["slots"])
        shutil.copyfile(CONTROL_LAYOUT, destination / "metadata/control-layout.json")
    for relative in ("rackforge-plugin.toml", "metadata/runtime.json"):
        path = destination / relative
        content = path.read_text(encoding="utf8")
        content = (content.replace("org.rackforge.lab.rf-d-pilot", PLUGIN_ID)
                   .replace("0.3.0", version).replace('name = "RF-D Pilot"', 'name = "RF-D"'))
        if external and relative == "rackforge-plugin.toml":
            content = content.replace('"audio_output"', '"audio_input", "audio_output"', 1)
            content = content.replace("[audio]\n", '[audio]\ninput_buses = [{ id = "main", '
                                      'name = "External Input", channels = 1, layout = "mono" }]\n')
        if programs and relative == "rackforge-plugin.toml":
            content = content.replace("state_version = 1", "state_version = 1\nconfig_mode = true", 1)
            content = content.replace("[component]", '[[web_ui.surfaces]]\nkind = "config"\n'
                                      'entry = "web/config.html"\n\n[component]', 1)
        path.write_text(content, encoding="utf8", newline="\n")
    if programs:
        (destination / "web/config.html").write_text(render_program_config(schema), encoding="utf8", newline="\n")
    html = destination / "web/play.html"
    html.write_text(render_panel(schema, bank, programs), encoding="utf8", newline="\n")


def compile_program_voice(execute, cargo, folder, guest, cfg_flags):
    manifest = folder / "Cargo.toml"
    manifest.write_text(
        '[package]\nname = "rf-d-voice"\nversion = "0.1.0"\nedition = "2021"\n'
        '[workspace]\n[lib]\ncrate-type = ["cdylib"]\n'
        f'path = "{guest.as_posix()}"\n[dependencies]\n'
        f'rackforge-plugin-sdk = {{ path = "{(HOST / "crates/rackforge-plugin-sdk").as_posix()}" }}\n'
        f'rackforge-program-api = {{ path = "{(HOST / "crates/rackforge-program-api").as_posix()}" }}\n'
        'serde = "1.0"\nserde_json = { version = "1.0", features = ["float_roundtrip"] }\n'
        '[profile.release]\nlto = "fat"\npanic = "abort"\ncodegen-units = 1\n',
        encoding="utf8", newline="\n",
    )
    shutil.copyfile(HOST / "Cargo.lock", folder / "Cargo.lock")
    target = folder / "target"
    execute(cargo, "rustc", "--manifest-path", manifest,
            "--config", 'target.wasm32-unknown-unknown.rustflags = ["-C", "target-feature=+simd128"]',
            "--target-dir", target, "--release", "--target", "wasm32-unknown-unknown",
            "--", "-A", "unexpected_cfgs", "-A", "dead_code",
            "--cfg", "pilot_voice_programs", *cfg_flags, timeout=900)
    return target / "wasm32-unknown-unknown/release/rf_d_voice.wasm"


def verify_program_library(execute, component, schema, package, folder):
    document = folder / "user-program.json"
    result, _ = execute("node", ROOT / "tools/check_rf_d_voice_programs.js", component, schema, document)
    print(result.decode().strip())
    core = HOST / f"target/release/rackforge-core{EXE}"
    data = folder / "program-state"
    program = json.loads(document.read_bytes())
    program_id = program["id"]
    result, _ = execute(core, "program-save", data, f"programs/{program_id}.rackforge-program.json", document)
    assert f"PROGRAM_SAVED id={program_id}" in result.decode(), result
    result, _ = execute(core, "smoke", package, "--data-root", data, "--preset", f"custom.{program_id}")
    output = result.decode()
    assert f"PRESET_LOADED id=custom.{program_id}" in output, output
    assert f"PROGRAM_EDIT_READY source=Some(\"custom.{program_id}\")" in output, output
    assert "PLUGIN_SMOKE_OK" in output, output
    print("RackForge reopened the stored User program and validated its editor")
    return dict(saved_parameters=len(program["payload"]["parameters"]), stored_program=f"custom.{program_id}",
                guest_round_trip=True, rackforge_reload=True)


def metrics(samples):
    signal = samples.astype(np.float64)
    rms = float(np.sqrt(np.mean(signal ** 2)))
    spectrum = abs(np.fft.rfft((signal - signal.mean()) * np.hanning(len(signal)))) ** 2
    frequencies = np.fft.rfftfreq(len(signal), 1. / SAMPLE_RATE)
    return dict(rms=rms, mean=float(signal.mean()),
                upper_band_fraction=float(spectrum[frequencies >= 2000].sum() / spectrum.sum()))


def verify_audio(render, report, output=False):
    def parameter(index, value, frame=0):
        return [frame, 0xb0, 20 + index, value]

    note_on, note_off = [960, 0x90, 57, 100], [19200, 0x80, 57, 0]
    score = [note_on, note_off]
    reference, times = render(score)
    assert all(np.array_equal(reference, render(score, block)[0]) for block in (127, 480, CAPACITY))
    report["partitions"] = [127, 128, 480, CAPACITY]
    report["node_128_ns"] = dict(median=int(np.median(times)), maximum=int(max(times)),
                                 over_half_period=sum(value > MARGIN_NS for value in times))
    short_release = reference[20160:22560]
    long, _ = render([parameter(10, 127), *score])
    quiet, _ = render([parameter(6, 0), *score])
    closed, _ = render([parameter(0, 0), parameter(1, 0), *score])
    opened, _ = render([parameter(0, 127), parameter(1, 0), *score])
    sweep, _ = render([parameter(0, 0), parameter(1, 127), *score])
    slow_attack, _ = render([parameter(4, 12), *score])
    slow_filter, _ = render([parameter(7, 12), *score])
    held_filter, _ = render([parameter(9, 127), *score])
    legato, _ = render([note_on, [9001, 0x90, 60, 100], [12001, 0x80, 60, 0], note_off])
    retrigger, _ = render([note_on, [9001, 0x80, 57, 0], [9001, 0x90, 57, 100], note_off])
    changes = [*score, parameter(10, 127, 19201)]
    automated, _ = render(changes)
    assert np.array_equal(automated, render(changes, 480)[0])
    assert np.array_equal(reference, render([note_on, [19200, 0xb0, 123, 0]])[0])
    assert np.max(abs(automated[20160:22560])) > 0.02
    assert np.array_equal(reference, legato)
    assert np.max(abs(reference[9100:9350] - retrigger[9100:9350])) > 1e-4
    assert not np.any(reference[:960]) and 0.001 < np.max(abs(reference)) < 1.
    if output:
        assert np.max(abs(short_release)) < 0.005 and np.max(abs(long[-960:])) < 1e-5
    else:
        assert not np.any(short_release) and not np.any(long[-960:])
    measurements = dict(
        reference_peak=float(np.max(abs(reference))),
        default_sustain=metrics(reference[12000:18720]),
        zero_sustain=metrics(quiet[12000:18720]),
        release_on=metrics(long[20160:22560]),
        fast_attack=metrics(reference[1056:1248]),
        slow_attack=metrics(slow_attack[1056:1248]),
        cutoff_low=metrics(closed[12000:18720]),
        cutoff_high=metrics(opened[12000:18720]),
        contour_on=metrics(sweep[1440:2400]),
        contour_off=metrics(closed[1440:2400]),
        slow_filter_attack=metrics(slow_filter[1440:2400]),
        fast_filter_attack=metrics(reference[1440:2400]),
        held_filter=metrics(held_filter[12000:18720]),
    )
    report["audio"] = measurements
    assert measurements["zero_sustain"]["rms"] < 0.02 * measurements["default_sustain"]["rms"]
    assert abs(measurements["default_sustain"]["mean"]) < 0.02 * measurements["default_sustain"]["rms"]
    assert measurements["slow_attack"]["rms"] < 0.25 * measurements["fast_attack"]["rms"]
    assert measurements["release_on"]["rms"] > 0.1 * measurements["default_sustain"]["rms"]
    assert measurements["cutoff_high"]["rms"] > 4. * measurements["cutoff_low"]["rms"]
    assert measurements["cutoff_high"]["upper_band_fraction"] > 1e-3
    assert measurements["contour_on"]["upper_band_fraction"] > 100. * measurements["contour_off"]["upper_band_fraction"]
    assert measurements["fast_filter_attack"]["upper_band_fraction"] > measurements["slow_filter_attack"]["upper_band_fraction"]
    assert measurements["held_filter"]["upper_band_fraction"] > 2. * measurements["default_sustain"]["upper_band_fraction"]


def verify_oscillators(render, report):
    def change(index, value, frame=0):
        return [frame, 0xb1, 20 + index, value]

    def score(controls, note=57):
        return [change(0, 100), change(1, 0), *[change(*item) for item in controls],
                [960, 0x90, note, 100], [38400, 0x80, note, 0]]

    def spectrum(audio):
        signal = audio[9600:36000].astype(np.float64)
        return abs(np.fft.rfft(signal * np.hanning(len(signal)), 2**18)) * 4. / len(signal)

    def frequency(audio, expected):
        magnitudes = spectrum(audio)
        bin_hz = SAMPLE_RATE / (2**18)
        center = int(round(expected / bin_hz))
        radius = max(4, int(0.01 * center))
        peak = center - radius + np.argmax(magnitudes[center - radius:center + radius + 1])
        left, middle, right = np.log(magnitudes[peak - 1:peak + 2])
        hz = bin_hz * (peak + 0.5 * (left - right) / (left - 2. * middle + right))
        assert abs(1200. * np.log2(hz / expected)) < 0.5, (hz, expected)
        assert magnitudes[peak] > 0.01, (hz, magnitudes[peak])
        return float(hz)

    def harmonic_ratio(audio, hz, harmonic):
        magnitudes = spectrum(audio)
        index = lambda f: round(f * 2**18 / SAMPLE_RATE)
        return float(magnitudes[index(harmonic * hz)] / magnitudes[index(hz)])

    osc2 = [(14, 0), (19, 1), (18, 100)]
    osc3 = [(14, 0), (24, 1), (23, 100)]
    saw, _ = render(score(osc2))
    tuned, _ = render(score([*osc2, (15, 2), (17, 7), (11, 50)]))
    osc3_tracked, _ = render(score(osc3, 69))
    osc3_free, _ = render(score([*osc3, (25, 0)], 69))
    assert np.array_equal(osc3_free, render(score([*osc3, (25, 0)], 57))[0])
    reverse, _ = render(score([*osc3, (21, 1)], 57))
    assert not np.array_equal(reverse, render(score(osc3))[0])
    triangle, _ = render(score([*osc2, (16, 0)]))
    hybrid, _ = render(score([*osc2, (16, 1)]))
    square, _ = render(score([*osc2, (16, 3)]))
    wide, _ = render(score([*osc2, (16, 4)]))
    narrow, _ = render(score([*osc2, (16, 5)]))
    assert all(np.max(abs(signal)) > 0.01 for signal in (triangle, hybrid, square, wide, narrow))
    ratios = {name: harmonic_ratio(signal, 220., 2) for name, signal in
              (("triangle", triangle), ("hybrid", hybrid), ("saw", saw),
               ("square", square), ("wide", wide), ("narrow", narrow))}
    assert ratios["square"] < 0.02 and ratios["triangle"] < ratios["hybrid"] < ratios["saw"]
    assert ratios["narrow"] > ratios["wide"] > ratios["square"]

    # A fifth at 329.63 Hz would share this FFT window with the square's third at 330 Hz.
    triad_score = score([(19, 1), (17, 5), (16, 0), (24, 1), (20, 2), (21, 3)])
    triad, _ = render(triad_score)
    live_score = sorted(triad_score + [change(14, 0, 8233), change(14, 1, 12001),
                                      change(16, 2, 17487), change(22, -4, 21331)], key=lambda event: event[0])
    live, times = render(live_score)
    assert all(np.array_equal(live, render(live_score, block)[0]) for block in (127, 480, CAPACITY))
    muted, _ = render(score([(14, 0)]))
    assert not np.any(muted)
    peak = max(float(np.max(abs(signal))) for signal in (triad, live))
    assert 0.01 < peak < 1.
    report["oscillator_audio"] = dict(
        frequencies_hz=dict(osc2=frequency(saw, 220.), osc2_tuned=frequency(tuned, 110. * 2**(7.5/12)),
                            osc3_tracked=frequency(osc3_tracked, 440.), osc3_free=frequency(osc3_free, 220.),
                            triad=[frequency(triad, hz) for hz in (110., 220., 220. * 2**(5/12))]),
        second_harmonic_ratio=ratios, live_peak=peak,
        live_node_128_ns=dict(median=int(np.median(times)), maximum=int(max(times)),
                              over_half_period=sum(value > MARGIN_NS for value in times)))


def main(argv=None, *, inspect_audio=None, legacy_timbre=False, wide_pulse_duty=None,
         oversampling=2, trapezoidal_ladder=False):
    parser = argparse.ArgumentParser(description=__doc__)
    profiles = parser.add_mutually_exclusive_group()
    profiles.add_argument("--single-saw", action="store_true", help="rebuild the 0.4.0 single-oscillator voice")
    profiles.add_argument("--oscillator-bank", action="store_true", help="rebuild the 0.5.0 oscillator bank")
    profiles.add_argument("--resonant-filter", action="store_true", help="rebuild the 0.6.0 resonant filter")
    profiles.add_argument("--modulation", action="store_true", help="select the 0.7.0 modulation profile")
    profiles.add_argument("--keyboard", action="store_true", help="select the keyboard development profile")
    profiles.add_argument("--external", action="store_true", help="select the external input development profile")
    profiles.add_argument("--feedback", action="store_true", help="select the LO feedback development profile")
    profiles.add_argument("--main-output", action="store_true", help="select the HI/LO development profile")
    profiles.add_argument("--monitor", action="store_true", help="select the Phones and A-440 development profile")
    profiles.add_argument("--control-inputs", action="store_true", help="select the rear-jack development profile")
    profiles.add_argument("--midi", action="store_true", help="select the MIDI development profile")
    parser.add_argument("--package", metavar="VERSION", help="export one .rfplugin for the selected profile")
    parser.add_argument("--ci-thread-cpu", action="store_true",
                        help="check the offline Linux RackForge render budget with the render thread's CPU clock")
    args = parser.parse_args(argv)
    if args.ci_thread_cpu and sys.platform != "linux":
        parser.error("--ci-thread-cpu requires Linux")
    if inspect_audio is not None and args.package:
        parser.error("audio inspection uses the temporary WASM component")
    if args.package and not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+(?:-[0-9A-Za-z.-]+)?", args.package):
        parser.error("--package expects a version such as 0.8.0")
    bank = not args.single_saw
    emphasis = bank and not args.oscillator_bank
    modulation = emphasis and not args.resonant_filter
    performance = modulation and not args.modulation
    external = performance and not args.keyboard
    feedback = external and not args.external
    output = feedback and not args.feedback
    monitor = output and not args.main_output
    control_inputs = monitor and not args.monitor
    midi = control_inputs and not args.control_inputs
    factory = midi and not args.midi
    calibrated = midi and not legacy_timbre
    if wide_pulse_duty is not None and (not calibrated or inspect_audio is None):
        parser.error("wide pulse duty overrides require calibrated MIDI audio inspection")
    if oversampling not in (2, 4) or (oversampling == 4 and (not calibrated or inspect_audio is None)):
        parser.error("4x oversampling requires calibrated MIDI audio inspection")
    if trapezoidal_ladder and (not calibrated or inspect_audio is None):
        parser.error("trapezoidal ladder requires calibrated MIDI audio inspection")
    profile_version = VERSION if modulation else "0.6.0" if emphasis else "0.5.0" if bank else "0.4.0"
    version = args.package or (f"{profile_version}-dev" if performance else profile_version)
    schema = parameter_schema(bank, emphasis, modulation, performance, external, feedback, output, monitor,
                              control_inputs, left_hand=midi, polyphony=midi)
    features = {name for name, enabled in (("oscillators", bank), ("filter", emphasis), ("modulation", modulation),
                                          ("external", external), ("feedback", feedback), ("factory", factory))
                if enabled}
    catalog, programs = prepare_catalog(schema, features)
    if midi:
        catalog["banks"].append(dict(id="user", name="User", order=2))
    factory_programs = {entry["id"]: entry["bank"] for entry in catalog["presets"]} if factory else {}
    compiler = Path(COMPILER)
    if os.name != "nt":
        compiler = Path(shutil.which("rustc") or "rustc")
    elif midi:
        # Cargo also needs the native Rust standard library for build scripts and proc macros.
        compiler = compiler.parents[2] / "1.98.0-x86_64-pc-windows-gnu/bin/rustc.exe"
    compiler = Path(os.environ.get("RF_D_RUSTC", compiler))
    cargo = compiler.with_name(f"cargo{EXE}")
    optimizer = os.environ.get("RF_D_WASM_OPT", WASM_OPT if os.name == "nt" else "wasm-opt")
    env = dict(os.environ, RACKFORGE_OPTIMIZE_PLUGINS="0", RUSTC=str(compiler))
    if os.name == "nt":
        env["PATH"] = "C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;" + env["PATH"]

    env.pop("RF_D_HOST_THREAD_CPU", None)

    def execute(*command, timeout=120):
        command_env = env
        if args.ci_thread_cpu and Path(command[0]).name == "external-rack":
            command_env = dict(env, RF_D_HOST_THREAD_CPU="1")
        run = subprocess.run(list(map(str, command)), cwd=ROOT, env=command_env, capture_output=True, timeout=timeout)
        assert run.returncode == 0, run.stderr.decode(errors="replace") + run.stdout.decode(errors="replace")
        return run.stdout, run.stderr

    AREA.mkdir(parents=True, exist_ok=True)
    assert not list(AREA.iterdir()), AREA
    internal_rate = SAMPLE_RATE * oversampling
    report = dict(passed=False, version=version, plugin_id=PLUGIN_ID, host_rate_hz=SAMPLE_RATE,
                  internal_rate_hz=internal_rate, packaged=bool(args.package))
    try:
        kernel = taps(internal_rate)
        fir = emit("pilot-pi-fir.rs", f"pub const H{internal_rate}:[f64;{len(kernel)}]=[\n"
                   + "".join(f"    {value:.17e},\n" for value in kernel) + "];\n")
        report["fir_sha256"] = sha(fir)
        modules = dict(voice=ROOT / "tools/rf_d_reduced_voice.rs", pi_coefficients=fir)
        if not bank:
            from check_rf_d_pilot_returns import generate_wave

            wave, report["h128_sha256"] = generate_wave()
            modules["wave"] = wave
            report["wave_sha256"] = sha(wave)
        else:
            modules["oscillator_tables"] = oscillator_tables(
                report, calibrated=calibrated, wide_pulse_duty=wide_pulse_duty,
            )
            modules["voice_programs"] = emit_program_table(programs)
        if midi:
            program_data = "pub const FIELDS: &[(u32, &str, Option<f64>)] = &[\n"
            for field in program_parameters(schema):
                default = field.get("missing_default")
                fallback = "None" if default is None else f"Some({float(default)})"
                program_data += f'    ({field["index"]}, "{field["id"]}", {fallback}),\n'
            program_data += "];\n"
            program_data += f'pub const CATALOG: &str = r#"{json.dumps(catalog, ensure_ascii=False, separators=(",", ":"))}"#;\n'
            program_data += f'pub const VERSION: &str = "{version}";\n'
            modules["program_data"] = emit("voice-program-data.rs", program_data)
            modules["program"] = ROOT / "tools/rf_d_voice_program.rs"
        if emphasis:
            modules["emphasis_coefficients"] = emphasis_table(report, calibrated=calibrated, rate=internal_rate)
        if calibrated:
            modules["cutoff_coefficients"] = calibrated_cutoff_table(report)
        if control_inputs:
            modules["loudness_cv_coefficients"] = loudness_table(report)
        code = "".join(f'#[path = "{path.as_posix()}"] mod {name};\n' for name, path in modules.items())
        guest = emit("voice-contours-guest.rs", code + (ROOT / GUEST).read_text(encoding="utf8"))
        with TemporaryDirectory(prefix="rf-d-voice-", dir=AREA) as temporary:
            folder = Path(temporary)
            sdk = folder / "librackforge_plugin_sdk.rlib"
            component = folder / "voice.wasm"
            optimized = folder / "component.wasm"
            render_schema = folder / "parameters.json"
            write(render_schema, schema)
            flags = [compiler, "--target", "wasm32-unknown-unknown", "-C", "target-feature=+simd128",
                     "-C", "opt-level=3", "-A", "dead_code"]
            bank_flags = ("--cfg", "pilot_oscillator_bank") if bank else ()
            filter_flags = ("--cfg", "pilot_voice_filter") if emphasis else ()
            modulation_flags = ("--cfg", "pilot_voice_modulation") if modulation else ()
            performance_flags = ("--cfg", "pilot_voice_performance") if performance else ()
            external_flags = ("--cfg", "pilot_voice_external") if external else ()
            feedback_flags = ("--cfg", "pilot_voice_feedback") if feedback else ()
            output_flags = ("--cfg", "pilot_voice_output") if output else ()
            monitor_flags = ("--cfg", "pilot_voice_monitor") if monitor else ()
            cv_flags = ("--cfg", "pilot_voice_control_inputs") if control_inputs else ()
            midi_flags = ("--cfg", "pilot_voice_midi") if midi else ()
            poly_flags = ("--cfg", "pilot_voice_poly") if midi else ()
            calibrated_flags = ("--cfg", "pilot_calibrated_filter") if calibrated else ()
            oversampling_flags = ("--cfg", "pilot_oversample_4x") if oversampling == 4 else ()
            ladder_flags = ("--cfg", "pilot_ladder_trapezoidal") if trapezoidal_ladder else ()
            cfg_flags = ("--cfg", "pilot_pi", "--cfg", "pilot_returns", "--cfg", "pilot_host_blocks",
                         "--cfg", "pilot_voice_contours", *bank_flags, *filter_flags, *modulation_flags,
                         *performance_flags, *external_flags, *feedback_flags, *output_flags, *monitor_flags,
                         *cv_flags, *midi_flags, *poly_flags, *calibrated_flags, *oversampling_flags, *ladder_flags)
            if midi:
                component = compile_program_voice(execute, cargo, folder, guest, cfg_flags)
            else:
                execute(*flags, "--edition=2024", "--crate-type", "rlib", "--crate-name", "rackforge_plugin_sdk",
                        HOST / SDK_PATH, "-o", sdk)
                execute(*flags, "--edition=2021", "--crate-type", "cdylib", "-C", "panic=abort", "-C", "lto=fat",
                        *cfg_flags, guest, "--extern", f"rackforge_plugin_sdk={sdk}", "-o", component)
            execute(optimizer, component, "-O4", "-o", optimized)

            def render(score, block=128, frames=43200, samples=None, preset=None):
                input_path = "-"
                if samples is not None:
                    frames = len(samples)
                    input_path = folder / "input.f32"
                    input_path.write_bytes(np.asarray(samples, dtype="<f4").tobytes())
                extra_args = (input_path, preset) if preset is not None else (input_path,) if samples is not None else ()
                raw, timings = execute("node", ROOT / NODE, optimized, json.dumps(score), frames,
                                       "--voice-state" if block == 128 else "render", block, CAPACITY,
                                       render_schema, *extra_args)
                audio = np.frombuffer(raw, dtype="<f4").reshape(-1, 2)
                assert np.isfinite(audio).all() and np.array_equal(audio[:, 0], audio[:, 1])
                return audio[:, 0], json.loads(timings)

            if inspect_audio is not None:
                inspect_audio(render, schema, sha(optimized))
                return

            verify_audio(render, report, output)
            if bank:
                verify_oscillators(render, report)
            resonance_cutoff = 38.8 if calibrated else 65
            if emphasis:
                verify_filter(render, report, cutoff=resonance_cutoff)
            if modulation:
                verify_modulation(render, report, cutoff=41 if calibrated else 67)
            if performance:
                verify_keyboard(render, report, cutoff=resonance_cutoff)
            if external:
                verify_external(render, report)
            if feedback:
                verify_feedback(render, report, output)
            if output:
                verify_output(render, report)
            if monitor:
                verify_monitor(render, report)
            if control_inputs:
                verify_control_inputs(render, report, cutoff=resonance_cutoff)
            if midi:
                verify_midi(render, report)
                verify_expression(render, report)
                verify_left_hand(render, report, cutoff=resonance_cutoff)
                verify_polyphony(render, report)
            if factory:
                verify_presets(render, programs, factory_programs, report)
            template = folder / "package"
            package_template(template, schema, catalog, version, bank, external, midi)
            if args.package:
                artifact = ROOT / f"artifacts/rf-d-voice-{version}.rfplugin"
                archive, store = folder / artifact.name, folder / "store"
                packer = HOST / f"target/release/rackforge-store{EXE}"
                execute(packer, "pack-wasm", template, optimized, archive)
                execute(packer, "install-local", archive, store)
                manifest, = store.rglob("rackforge-plugin.toml")
                host_package = manifest.parent
            else:
                shutil.copyfile(optimized, template / "component.wasm")
                host_package = template
            if midi:
                report["program_library"] = verify_program_library(execute, optimized, render_schema, host_package, folder)
            if external:
                verify_host_capture(execute, render, folder, host_package, report, feedback,
                                    schema if monitor else None, control_inputs, HOST_SCORE if midi else None,
                                    {name: programs[name] for name in factory_programs}, host=HOST,
                                    thread_cpu=args.ci_thread_cpu)
            report["host_stress"] = {}
            preset = ("feedback_bass" if factory else "loop_drive" if feedback
                      else "wheel_motion" if modulation else "resonant_bass" if emphasis
                      else "three_oscillators" if bank else "default")
            for frames in (128, 480, CAPACITY):
                raw, _ = execute(HOST / f"target/release/rackforge-core{EXE}", "stress", host_package,
                                 "--preset", preset, "--data-root", folder / "state",
                                 "--voices", 1, "--blocks", 100, "--frames", frames)
                result = raw.decode().strip()
                assert "PLUGIN_STRESS_OK" in result and f"frames={frames}" in result
                assert 0.001 < float(result.split("peak=")[1].split()[0]) < 1., result
                assert float(result.split("realtime_ratio=")[1]) < 0.5, result
                report["host_stress"][frames] = result
            report["component_sha256"] = sha(optimized)
            if args.package:
                report["archive_sha256"] = sha(archive)
                artifact.parent.mkdir(exist_ok=True)
                archive.replace(artifact)
        report["passed"] = True
        if factory and not args.package:
            write(ROOT / "evidence/rf_d_voice_development10.json", report)
        if args.package:
            print(f"{artifact}\n{report['archive_sha256']}")
            if args.ci_thread_cpu:
                timing_results = [result for key in ("host_monitor", "host_control_inputs", "host_midi",
                                                     "host_left_hand", "host_keyboard_expression")
                                  for result in report.get(key, {}).get(128, ())]
                for preset in report.get("host_factory", {}).values():
                    timing_results.extend(preset["catalog_128_timing"])
                    timing_results.extend(preset["restored_128_timing"])
                if timing_results:
                    print("RackForge 128-frame maxima (ns): "
                          f"thread CPU {max(result['cpu_max_ns'] for result in timing_results)}, "
                          f"wall time {max(result['max_ns'] for result in timing_results)}")
        else:
            print("WASM and RackForge checks passed with no archive")
        result_keys = ("factory_audio", "midi_audio", "control_inputs_audio", "monitor_audio", "output_audio", "feedback_audio", "external_audio", "keyboard_audio", "modulation_audio", "filter_audio",
                       "oscillator_audio", "audio")
        results = next(report[key] for key in result_keys if key in report)
        print(json.dumps(results, indent=2))
    except Exception:
        fields = ("audio", "oscillator_audio", "filter_audio", "modulation_audio", "keyboard_audio",
                  "external_audio", "feedback_audio", "output_audio", "monitor_audio",
                  "loudness_cv_table", "control_inputs_audio", "host_capture", "host_feedback", "host_monitor",
                  "host_control_inputs", "midi_audio", "keyboard_expression", "host_keyboard_expression",
                  "host_midi", "factory_audio", "host_factory",
                  "node_128_ns", "host_stress", "left_hand_audio", "host_left_hand")
        print(json.dumps({key: report[key] for key in fields if key in report},
                         indent=2), flush=True)
        raise
    finally:
        for path in AREA.iterdir():
            assert path.is_file() and path.resolve().parent == AREA.resolve(), path
            path.unlink()


if __name__ == "__main__":
    main()
