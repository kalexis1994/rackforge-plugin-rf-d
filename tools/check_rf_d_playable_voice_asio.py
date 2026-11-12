"""Measure the packaged three-oscillator RF-D voice on NVIDIA ASIO at 128 frames."""
import json
import os
import subprocess
import traceback
from pathlib import Path
from tempfile import TemporaryDirectory

from check_recovery_engine128 import HOST_CORE, analyze, sources_for_build
from check_recovery_engine128_schedule import topology
from check_recovery_engine128_smt import NVIDIA_ENDPOINT, admitted, analyze_smt, fixed_pair_primary
from check_recovery_host import HOST_COMPILER
from check_recovery_host128 import ASIO_DRIVER, asio_profile, read_override, restore_override
from check_rf_d_pilot_returns_asio import temporary_nvidia_profile
from check_rf_d_playable_voice import AREA, COMPILER, HOST, ROOT, sha, write
from prepare_hybrid_stamp import once

CPU = 9
IDLE = 8500


def voice_probe():
    _, source = sources_for_build(schedule=True, smt=True, smt_lean=True)
    source = source.decode()
    source = once(source, "    startup: usize,", """    startup: usize,
    layers: rackforge_core::parameter_link::ControlLayers,""")
    source = once(source, "route, output: [0.; 256], startup: 48,", """route, output: [0.; 256], startup: 48,
            layers: rackforge_core::parameter_link::ControlLayers::default(),""")
    source = once(source, "state: RackSlotStateLoad::Default,", """
                    state: RackSlotStateLoad::LegacyPreset("three_oscillators".into()),""")
    source = once(source, "                let telemetry = pool.telemetry().clone();", """                if !self.silence {
                    let note = match self.calls {
                        0 => Some([0x90, 57, 100]),
                        tick if tick % 512 == 256 => Some([0x90, 45, 100]),
                        tick if tick % 512 == 0 => Some([0x80, 45, 0]),
                        _ => None,
                    };
                    if let Some(data) = note {
                        use rackforge_midi_api::{IngressMidiEvent, MidiPacket, MidiSourceKey};
                        let packet = MidiPacket { frame: 0, length: 3, data, wide: None };
                        rack.route(IngressMidiEvent { source: MidiSourceKey::new(0), packet },
                                   None, &mut self.layers);
                    }
                }
                let telemetry = pool.telemetry().clone();""")
    return source


def main():
    package_report = json.loads((ROOT / "evidence/rf_d_playable_voice02.json").read_bytes())
    version = package_report["version"]
    artifact = ROOT / f"artifacts/rf-d-voice-{version}.rfplugin"
    assert sha(artifact) == package_report["archive_sha256"]
    assert not list(AREA.iterdir()), AREA
    env = {key: value for key, value in os.environ.items() if not key.startswith(("RF_D_SMT_", "RF_D_SCHED_"))}
    env.update(RACKFORGE_AUDIO_WORKERS="0", RACKFORGE_OPTIMIZE_PLUGINS="0")

    def execute(*args, environment=env):
        command = list(map(str, args))
        return subprocess.run(command, cwd=ROOT, env=environment, capture_output=True, timeout=120)

    def successful(*args, environment=env):
        run = execute(*args, environment=environment)
        assert run.returncode == 0, run.stderr.decode(errors="replace")
        return run.stdout.decode().strip()

    deps = HOST / "target/release/deps"
    core = deps / HOST_CORE
    cpal = deps / "libcpal-7dab8e06a9b0e32f.rlib"
    windows = deps / "libwindows-30e5b7032d286333.rlib"
    midi = deps / "librackforge_midi_api-9bf68be69a56bbe5.rlib"
    asio = HOST / "target/release/build/asio-sys-bb9248db199c7ec7/out"
    registry = Path(COMPILER).parents[4] / ".cargo/registry/src"
    native = list(dict.fromkeys(path.parent for path in (
        *sorted((HOST / "target/release/build").glob("*/out/*.lib")),
        *sorted(registry.glob("*/windows_x86_64_msvc-*/lib/*.lib")),
    )))
    probe = AREA / "voice-physical.rs"
    exe = AREA / "recovery-host128.exe"
    attempt = 1
    while (receipt := ROOT / f"evidence/rf_d_playable_voice_asio{attempt:02}.json").exists():
        attempt += 1
    report = dict(passed=False, version=version, artifact_sha256=sha(artifact), endpoint=NVIDIA_ENDPOINT,
                  core_sha256=sha(core), cpu=CPU, minimum_idle=IDLE, runs=[])
    try:
        probe.write_text(voice_probe(), encoding="utf8", newline="\n")
        report["probe_sha256"] = sha(probe)
        successful(HOST_COMPILER, "--edition=2021", "-C", "opt-level=2", "-A", "dead_code",
                   "-A", "unused_imports", "--cfg", "asio128", "-L", f"dependency={deps}",
                   *[arg for path in native for arg in ("-L", f"native={path}")],
                   "-L", f"native={asio}", "-l", "static=asio", probe, "--extern", f"cpal={cpal}",
                   "--extern", f"windows={windows}", "--extern", f"rackforge_core={core}",
                   "--extern", f"rackforge_midi_api={midi}", "-o", exe)
        with TemporaryDirectory(prefix="voice-asio-", dir=AREA) as temporary:
            folder = Path(temporary)
            store = folder / "store"
            successful(HOST / "target/release/rackforge-store.exe", "install-local", artifact, store)
            manifest, = store.rglob("rackforge-plugin.toml")
            assert sha(manifest.parent / "component.wasm") == package_report["component_sha256"]
            profile = asio_profile(exe)
            with temporary_nvidia_profile(profile, report):
                before = read_override(profile)
                report["before"] = successful(exe, "asio-query", ASIO_DRIVER)
                try:
                    endpoint = successful(exe, "smt-endpoints", ASIO_DRIVER)
                    assert endpoint == NVIDIA_ENDPOINT, endpoint
                    top = topology(successful(exe, "schedule-topology"))
                    fixed_pair_primary(top, CPU)
                    rows = folder / "callbacks.bin"
                    for route, blocks in (("control", 1200), ("rack", 4800), ("rack", 4800)):
                        rows.unlink(missing_ok=True)
                        controls = dict(env, RF_D_ENGINE_ROUTE=route, RF_D_ENGINE_PACKAGE=str(manifest.parent),
                                        RF_D_ENGINE_CACHE=str(folder / "cache"), RF_D_ENGINE_ROWS=str(rows),
                                        RF_D_SMT_MODE="quiet-event", RF_D_SMT_SUPERVISOR="1",
                                        RF_D_SMT_FIXED_CPU=str(CPU), RF_D_SMT_FIXED_IDLE=str(IDLE))
                        run = execute(exe, "asio-bench", ASIO_DRIVER, blocks, "dsp", environment=controls)
                        stream = run.stderr.decode(errors="replace")
                        item = dict(route=route, blocks=blocks, exit_code=run.returncode)
                        report["runs"].append(item)
                        if run.returncode:
                            item["stderr"] = stream
                            print(stream, flush=True)
                            continue
                        item["rows_sha256"] = sha(rows)
                        item["metrics"] = analyze_smt(rows.read_bytes(), stream, blocks, "quiet-event", None,
                                                      top, analyze, silent=route == "control",
                                                      endpoint=endpoint, event_cpu=CPU, event_idle=IDLE)
                        print(route, item["metrics"]["wall_ns"], item["metrics"]["gate_passed"], flush=True)
                    report["passed"] = admitted(report["runs"][0], report["runs"][1:])
                finally:
                    restore_override(profile, before)
                    report["restored"] = successful(exe, "asio-query", ASIO_DRIVER)
                    assert report["before"] == report["restored"]
    except Exception:
        report["failure"] = traceback.format_exc()
        raise
    finally:
        for path in (probe, exe, exe.with_suffix(".pdb")):
            path.unlink(missing_ok=True)
        write(receipt, report)
    if not report["passed"]:
        raise SystemExit("The two 128-frame ASIO passes did not meet the timing gate")


if __name__ == "__main__":
    main()
