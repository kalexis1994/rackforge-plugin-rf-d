"""Build and exercise the playable RF-D voice in WASM and RackForge."""
import argparse
from html import escape
import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np

from check_rf_d_pi_pilot import RATE
from check_rf_d_playable_pilot import (
    AREA, COMPILER, GUEST, HOST, NODE, PACKAGE, ROOT, SDK_PATH, WASM_OPT, emit, sha, write,
)
from check_rf_d_pilot_returns import generate_pi_fir, generate_wave, pilot_wave_model
from check_rf_d_playable_filter import emphasis_table, verify_filter
from check_rf_d_playable_modulation import verify_modulation
from check_rf_d_voice_keyboard import verify_keyboard
from check_rf_d_voice_external import verify_external, verify_host_capture
from check_rf_d_voice_feedback import verify_feedback
from check_rf_d_voice_output import verify_output
from check_rf_d_voice_monitor import verify_monitor
from check_rf_d_voice_control_inputs import loudness_table, verify_control_inputs
from check_rf_d_voice_midi import HOST_SCORE, verify_midi
from check_rf_d_voice_presets import emit_program_table, prepare_catalog, verify_presets
from rf_d_cutoff_calibration import calibrated_cutoff_table

VERSION = "0.7.0"
PLUGIN_ID = "org.rackforge.lab.rf-d-voice"
SCHEMA = ROOT / "plugin/voice/parameters.json"
CAPACITY = 4096
SAMPLE_RATE = 48_000
MARGIN_NS = 128 * 1e9 / SAMPLE_RATE / 2


def oscillator_tables(report, *, calibrated=False):
    model, report["h128_sha256"] = pilot_wave_model()
    harmonics = np.arange(1, 129)
    bands = (128, 64, 32, 16, 8, 4, 2, 1)
    samples = 2048
    saw, triangle = model[:2, 1:].copy()
    hybrid = (10. * saw + 47. * triangle) / 57.
    wide = 0.35
    if calibrated:
        evidence = ROOT / "evidence/vco1_circuit_validation.json"
        measured = json.loads(evidence.read_bytes())
        assert measured["passed"]
        wide = measured["result"]["pulse_duties"]["11"]["high"]
        report["wide_pulse"] = dict(duty=wide, contact=11, source_sha256=sha(evidence))
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


def parameter_schema(bank, emphasis, modulation, performance, external, feedback, output, monitor, control_inputs):
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
    return schema


def package_template(destination, schema, catalog, version, bank, external, midi):
    shutil.copytree(PACKAGE, destination)
    write(destination / "metadata/parameters.json", schema)
    write(destination / "metadata/presets.json", catalog)
    for relative in ("rackforge-plugin.toml", "metadata/runtime.json"):
        path = destination / relative
        content = path.read_text(encoding="utf8")
        content = (content.replace("org.rackforge.lab.rf-d-pilot", PLUGIN_ID)
                   .replace("0.3.0", version).replace("RF-D Pilot", "RF-D Voice"))
        if external and relative == "rackforge-plugin.toml":
            content = content.replace('"audio_output"', '"audio_input", "audio_output"', 1)
            content = content.replace("[audio]\n", '[audio]\ninput_buses = [{ id = "main", '
                                      'name = "External Input", channels = 1, layout = "mono" }]\n')
        path.write_text(content, encoding="utf8", newline="\n")
    if bank:
        path = destination / "web/panel.css"
        with path.open("a", encoding="utf8") as css:
            css.write("""
.choice .mechanism { width: 100%; height: auto; min-height: 42px; }
.choice select {
  width: min(100%, 135px);
  color: inherit;
  background: #242320;
  border: 1px solid var(--line);
  border-radius: 4px;
  padding: 4px;
}
.pair { row-gap: 12px; }
.meter { width: 14px; height: 14px; border-radius: 50%; background: #522626; appearance: none; }
.meter[data-active="true"] { background: #f66551; box-shadow: 0 0 10px #f6655166; }
.meter::-webkit-meter-bar { background: transparent; border: 0; }
.meter::-webkit-meter-optimum-value { background: transparent; }
""")
    html = destination / "web/play.html"
    header = html.read_text(encoding="utf8").split('    <div class="controls">')[0]
    header = header.replace("RF-D Pilot", "RF-D Voice").replace("PILOT", "VOICE")
    sections = []
    for page in schema["pages"]:
        controls = sorted((p for p in schema["parameters"] if p["page"] == page["id"]),
                          key=lambda p: p["order"])
        labels = []
        for param in controls:
            index, kind = param["index"], param["kind"]
            unit = kind.get("unit", "")
            if kind["type"] == "meter":
                style = "indicator"
                mechanism = f'<meter class="meter" min="0" max="1" value="0" data-index="{index}"></meter>'
            elif param["id"] == "decay_enabled" or kind["type"] == "boolean":
                style = "toggle"
                checked = " checked" if kind["default"] else ""
                control = f'<input type="checkbox" data-index="{index}"{checked} disabled>'
                mechanism = control
            elif kind["type"] == "enum":
                style = "choice"
                options = []
                for choice in kind["choices"]:
                    selected = " selected" if choice["value"] == kind["default"] else ""
                    options.append(f'<option value="{choice["value"]}"{selected}>{escape(choice["name"])}</option>')
                mechanism = f'<select data-index="{index}" disabled>{"".join(options)}</select>'
            else:
                style = "fader" if page["id"] == "mixer" else "rotary"
                scale = ' data-scale="log"' if unit == "ms" else ""
                control = (f'<input type="range" min="{kind["minimum"]}" max="{kind["maximum"]}" '
                           f'step="{kind["step"]}" value="{kind["default"]}" '
                           f'data-index="{index}" data-unit="{unit}"{scale} disabled>')
                dial = '<span class="dial" aria-hidden="true"></span>' if style == "rotary" else ""
                mechanism = dial + control
            labels.append(f"""          <label class="control {style}">
            <span class="label">{escape(param["name"])}</span>
            <span class="mechanism">{mechanism}</span>
            <span class="value" aria-hidden="true"></span>
          </label>""")
        sections.append(f"""      <section aria-labelledby="{page["id"]}">
        <h2 id="{page["id"]}">{page["name"]}</h2>
        <div class="pair">
{chr(10).join(labels)}
        </div>
      </section>""")
    voice_label = "THREE OSCILLATORS" if bank else "SINGLE SAW"
    midi_label = "MIDI 0–127 · LOW-NOTE PRIORITY · SUSTAIN" if midi else "MIDI 36–72 · LOW-NOTE PRIORITY"
    html.write_text(header + f"""    <div class="controls">
{chr(10).join(sections)}
    </div>
    <footer><span>{midi_label}</span><span>{voice_label} · v{version}</span></footer>
  </main>
</body>
</html>
""", encoding="utf8", newline="\n")


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


def main(argv=None, *, inspect_audio=None, legacy_timbre=False):
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
    args = parser.parse_args(argv)
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
    profile_version = VERSION if modulation else "0.6.0" if emphasis else "0.5.0" if bank else "0.4.0"
    version = args.package or (f"{profile_version}-dev" if performance else profile_version)
    schema = parameter_schema(bank, emphasis, modulation, performance, external, feedback, output, monitor, control_inputs)
    features = {name for name, enabled in (("oscillators", bank), ("filter", emphasis), ("modulation", modulation),
                                          ("external", external), ("feedback", feedback), ("factory", factory))
                if enabled}
    catalog, programs = prepare_catalog(schema, features)
    factory_names = [entry["id"] for entry in catalog["presets"] if entry["bank"] == "factory"]
    env = dict(os.environ, PATH="C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;" + os.environ["PATH"],
               RACKFORGE_OPTIMIZE_PLUGINS="0")

    def execute(*args):
        run = subprocess.run(list(map(str, args)), cwd=ROOT, env=env, capture_output=True, timeout=120)
        assert run.returncode == 0, run.stderr.decode(errors="replace") + run.stdout.decode(errors="replace")
        return run.stdout, run.stderr

    AREA.mkdir(parents=True, exist_ok=True)
    assert not list(AREA.iterdir()), AREA
    report = dict(passed=False, version=version, plugin_id=PLUGIN_ID, host_rate_hz=SAMPLE_RATE,
                  internal_rate_hz=RATE, packaged=bool(args.package))
    try:
        fir = generate_pi_fir()
        report["fir_sha256"] = sha(fir)
        modules = dict(voice=ROOT / "tools/rf_d_reduced_voice.rs", pi_coefficients=fir)
        if bank:
            modules["oscillator_tables"] = oscillator_tables(report, calibrated=calibrated)
            modules["voice_programs"] = emit_program_table(programs)
        else:
            wave, report["h128_sha256"] = generate_wave()
            modules["wave"] = wave
            report["wave_sha256"] = sha(wave)
        if emphasis:
            modules["emphasis_coefficients"] = emphasis_table(report, calibrated=calibrated)
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
            flags = [COMPILER, "--target", "wasm32-unknown-unknown", "-C", "target-feature=+simd128",
                     "-C", "opt-level=3", "-A", "dead_code"]
            execute(*flags, "--edition=2024", "--crate-type", "rlib", "--crate-name", "rackforge_plugin_sdk",
                    HOST / SDK_PATH, "-o", sdk)
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
            calibrated_flags = ("--cfg", "pilot_calibrated_filter") if calibrated else ()
            execute(*flags, "--edition=2021", "--crate-type", "cdylib", "-C", "panic=abort", "-C", "lto=fat",
                    "--cfg", "pilot_pi", "--cfg", "pilot_returns", "--cfg", "pilot_host_blocks",
                    "--cfg", "pilot_voice_contours", *bank_flags, *filter_flags, *modulation_flags,
                    *performance_flags, *external_flags, *feedback_flags, *output_flags, *monitor_flags, *cv_flags,
                    *midi_flags, *calibrated_flags, guest,
                    "--extern", f"rackforge_plugin_sdk={sdk}", "-o", component)
            execute(WASM_OPT, component, "-O4", "-o", optimized)

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
            if factory:
                verify_presets(render, programs, factory_names, report)
            template = folder / "package"
            package_template(template, schema, catalog, version, bank, external, midi)
            if args.package:
                artifact = ROOT / f"artifacts/rf-d-voice-{version}.rfplugin"
                archive, store = folder / artifact.name, folder / "store"
                packer = HOST / "target/release/rackforge-store.exe"
                execute(packer, "pack-wasm", template, optimized, archive)
                execute(packer, "install-local", archive, store)
                manifest, = store.rglob("rackforge-plugin.toml")
                host_package = manifest.parent
            else:
                shutil.copyfile(optimized, template / "component.wasm")
                host_package = template
            if external:
                verify_host_capture(execute, render, folder, host_package, report, feedback,
                                    schema if monitor else None, control_inputs, HOST_SCORE if midi else None,
                                    {name: programs[name] for name in factory_names})
            report["host_stress"] = {}
            preset = ("loop_drive" if feedback else "wheel_motion" if modulation else "resonant_bass" if emphasis
                      else "three_oscillators" if bank else "default")
            for frames in (128, 480, CAPACITY):
                raw, _ = execute(HOST / "target/release/rackforge-core.exe", "stress", host_package,
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
            write(ROOT / "evidence/rf_d_voice_development09.json", report)
        if args.package:
            print(f"{artifact}\n{report['archive_sha256']}")
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
                  "host_control_inputs", "midi_audio", "host_midi", "factory_audio", "host_factory",
                  "node_128_ns", "host_stress")
        print(json.dumps({key: report[key] for key in fields if key in report},
                         indent=2), flush=True)
        raise
    finally:
        for path in AREA.iterdir():
            assert path.is_file() and path.resolve().parent == AREA.resolve(), path
            path.unlink()


if __name__ == "__main__":
    main()
