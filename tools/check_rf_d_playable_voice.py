"""Build and exercise the RackForge RF-D voice with two independent contours."""
import json
import os
import shutil
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np

from check_rf_d_pi_pilot import RATE
from check_rf_d_playable_pilot import (
    AREA, COMPILER, GUEST, HOST, NODE, PACKAGE, ROOT, SDK_PATH, WASM_OPT, emit, sha, write,
)
from check_rf_d_pilot_returns import generate_pi_fir, generate_wave

VERSION = "0.4.0"
PLUGIN_ID = "org.rackforge.lab.rf-d-voice"
ARTIFACT = ROOT / f"artifacts/rf-d-voice-{VERSION}.rfplugin"
SCHEMA = ROOT / "plugin/voice/parameters.json"
CAPACITY = 4096
SAMPLE_RATE = 48_000
MARGIN_NS = 128 * 1e9 / SAMPLE_RATE / 2


def package_template(destination):
    shutil.copytree(PACKAGE, destination)
    shutil.copyfile(SCHEMA, destination / "metadata/parameters.json")
    for relative in ("rackforge-plugin.toml", "metadata/runtime.json", "metadata/presets.json"):
        path = destination / relative
        content = path.read_text(encoding="utf8")
        content = (content.replace("org.rackforge.lab.rf-d-pilot", PLUGIN_ID)
                   .replace("0.3.0", VERSION).replace("RF-D Pilot", "RF-D Voice")
                   .replace("Pilot Saw", "Model D Saw"))
        path.write_text(content, encoding="utf8", newline="\n")
    html = destination / "web/play.html"
    header = html.read_text(encoding="utf8").split('    <div class="controls">')[0]
    header = header.replace("RF-D Pilot", "RF-D Voice").replace("PILOT", "VOICE")
    schema = json.loads(SCHEMA.read_text(encoding="utf8"))
    sections = []
    for page in schema["pages"]:
        controls = sorted((p for p in schema["parameters"] if p["page"] == page["id"]),
                          key=lambda p: p["order"])
        labels = []
        for param in controls:
            index, kind = param["index"], param["kind"]
            unit = kind.get("unit", "")
            if param["id"] == "decay_enabled":
                style = "toggle"
                control = f'<input type="checkbox" data-index="{index}" disabled>'
                mechanism = control
            else:
                style = "fader" if page["id"] == "mixer" else "rotary"
                scale = ' data-scale="log"' if unit == "ms" else ""
                control = (f'<input type="range" min="{kind["minimum"]}" max="{kind["maximum"]}" '
                           f'step="{kind["step"]}" value="{kind["default"]}" '
                           f'data-index="{index}" data-unit="{unit}"{scale} disabled>')
                dial = '<span class="dial" aria-hidden="true"></span>' if style == "rotary" else ""
                mechanism = dial + control
            labels.append(f"""          <label class="control {style}">
            <span class="label">{param["name"]}</span>
            <span class="mechanism">{mechanism}</span>
            <span class="value" aria-hidden="true"></span>
          </label>""")
        sections.append(f"""      <section aria-labelledby="{page["id"]}">
        <h2 id="{page["id"]}">{page["name"]}</h2>
        <div class="pair">
{chr(10).join(labels)}
        </div>
      </section>""")
    html.write_text(header + f"""    <div class="controls">
{chr(10).join(sections)}
    </div>
    <footer><span>MIDI 36–72 · LOW-NOTE PRIORITY</span><span>SINGLE SAW · v{VERSION}</span></footer>
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


def verify_audio(render, report):
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
    assert not np.any(reference[:960]) and not np.any(short_release)
    assert not np.any(long[-960:]) and 0.001 < np.max(abs(reference)) < 1.
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


def main():
    env = dict(os.environ, PATH="C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;" + os.environ["PATH"],
               RACKFORGE_OPTIMIZE_PLUGINS="0")

    def execute(*args):
        run = subprocess.run(list(map(str, args)), cwd=ROOT, env=env, capture_output=True, timeout=120)
        assert run.returncode == 0, run.stderr.decode(errors="replace") + run.stdout.decode(errors="replace")
        return run.stdout, run.stderr

    AREA.mkdir(parents=True, exist_ok=True)
    assert not list(AREA.iterdir()), AREA
    report = dict(passed=False, version=VERSION, plugin_id=PLUGIN_ID, host_rate_hz=SAMPLE_RATE,
                  internal_rate_hz=RATE)
    try:
        wave, report["h128_sha256"] = generate_wave()
        fir = generate_pi_fir()
        report["wave_sha256"], report["fir_sha256"] = sha(wave), sha(fir)
        modules = dict(voice=ROOT / "tools/rf_d_reduced_voice.rs", wave=wave, pi_coefficients=fir)
        code = "".join(f'#[path = "{path.as_posix()}"] mod {name};\n' for name, path in modules.items())
        guest = emit("voice-contours-guest.rs", code + (ROOT / GUEST).read_text(encoding="utf8"))
        with TemporaryDirectory(prefix="rf-d-voice-", dir=AREA) as temporary:
            folder = Path(temporary)
            sdk = folder / "librackforge_plugin_sdk.rlib"
            component = folder / "voice.wasm"
            optimized = folder / "component.wasm"
            flags = [COMPILER, "--target", "wasm32-unknown-unknown", "-C", "target-feature=+simd128",
                     "-C", "opt-level=3", "-A", "dead_code"]
            execute(*flags, "--edition=2024", "--crate-type", "rlib", "--crate-name", "rackforge_plugin_sdk",
                    HOST / SDK_PATH, "-o", sdk)
            execute(*flags, "--edition=2021", "--crate-type", "cdylib", "-C", "panic=abort", "-C", "lto=fat",
                    "--cfg", "pilot_pi", "--cfg", "pilot_returns", "--cfg", "pilot_host_blocks",
                    "--cfg", "pilot_voice_contours", guest, "--extern", f"rackforge_plugin_sdk={sdk}", "-o", component)
            execute(WASM_OPT, component, "-O4", "-o", optimized)

            def render(score, block=128):
                raw, timings = execute("node", ROOT / NODE, optimized, json.dumps(score), 43200,
                                       "--voice-state" if block == 128 else "render", block, CAPACITY, SCHEMA)
                audio = np.frombuffer(raw, dtype="<f4").reshape(-1, 2)
                assert np.isfinite(audio).all() and np.array_equal(audio[:, 0], audio[:, 1])
                return audio[:, 0], json.loads(timings)

            verify_audio(render, report)
            template, archive, store = folder / "package", folder / ARTIFACT.name, folder / "store"
            package_template(template)
            packer = HOST / "target/release/rackforge-store.exe"
            execute(packer, "pack-wasm", template, optimized, archive)
            execute(packer, "install-local", archive, store)
            manifest, = store.rglob("rackforge-plugin.toml")
            report["host_stress"] = {}
            for frames in (128, 480, CAPACITY):
                raw, _ = execute(HOST / "target/release/rackforge-core.exe", "stress", manifest.parent,
                                 "--preset", "default", "--data-root", folder / "state",
                                 "--voices", 1, "--blocks", 100, "--frames", frames)
                result = raw.decode().strip()
                assert "PLUGIN_STRESS_OK" in result and f"frames={frames}" in result
                assert 0.001 < float(result.split("peak=")[1].split()[0]) < 1., result
                assert float(result.split("realtime_ratio=")[1]) < 0.5, result
                report["host_stress"][frames] = result
            report["archive_sha256"] = sha(archive)
            report["component_sha256"] = sha(optimized)
            ARTIFACT.parent.mkdir(exist_ok=True)
            archive.replace(ARTIFACT)
        report["passed"] = True
        write(ROOT / "evidence/rf_d_playable_voice01.json", report)
        print(f"{ARTIFACT}\n{json.dumps(report['audio'], indent=2)}")
    except Exception:
        print(json.dumps({key: report[key] for key in ("audio", "node_128_ns", "host_stress") if key in report},
                         indent=2), flush=True)
        raise
    finally:
        for path in AREA.iterdir():
            assert path.is_file() and path.resolve().parent == AREA.resolve(), path
            path.unlink()


if __name__ == "__main__":
    main()
