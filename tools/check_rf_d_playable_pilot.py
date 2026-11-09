"""Build and admit the MIDI pilot as an installable RackForge audition package."""
import json
import os
import shutil
import struct
import subprocess
import traceback
from pathlib import Path

import numpy as np

from affine_evidence import Sources
from check_hybrid_voice import packed
from check_recovery_engine128 import HOST_CORE
from check_recovery_host import HOST, HOST_COMPILER
from check_rf_d_reduced_engine_rack import HOST_REVISION, HOST_SOURCES
from check_rf_d_pilot_returns import SOURCES as RETURN_SOURCES, generate
from check_rf_d_reduced_voice import (
    AREA, COMPILER, GUEST, N, NODE, ROOT, digest, emit, pin, read, score, sha, write,
)

PACKAGE = ROOT / "plugin/package"
ARTIFACT = ROOT / "artifacts/rf-d-pilot-0.3.0.rfplugin"
REFERENCE = "evidence/rf_d_reduced_voice_pilot03.json"
PANEL_BASELINE = "evidence/rf_d_playable_pilot07.json"
MIDI_PROBE = "tools/rf_d_playable_pilot_probe.rs"
PROTOCOL = "docs/VOZ_PILOTO_JUGABLE_PROTOCOLO.md"
MARGIN = 128e9 / 48_000 / 2
BLOCKS = N // 128
MIDI_LIB = "librackforge_midi_api-9bf68be69a56bbe5.rlib"
SDK_PATH = "crates/rackforge-plugin-sdk/src/lib.rs"
WASM_OPT = ROOT.parent / "rackforge-plugin-rf-5/target/tools/binaryen/binaryen-version_132/bin/wasm-opt.exe"
SOURCES = (*RETURN_SOURCES, GUEST, NODE, MIDI_PROBE, PROTOCOL, "tools/recovery_engine128_broadcast.rs",
           "tools/affine_evidence.py", "tools/check_rf_d_playable_pilot.py",
           *(p.relative_to(ROOT).as_posix() for p in PACKAGE.rglob("*") if p.is_file()))


def assess(raw, stderr, expected, events):
    header, routed, blocks, host_max, misses, faults, dropped = stderr.decode().strip().split(",")
    assert header == "RF_D_MIDI" and int(routed) == events and int(blocks) == BLOCKS
    times = np.frombuffer(raw[:8 * BLOCKS], "<u8")
    samples = np.frombuffer(raw[8 * BLOCKS:], "<f4").reshape(N, 2)
    assert min(times) > 0 and 0 < int(host_max) <= max(times)
    assert np.isfinite(samples).all() and np.array_equal(samples[:, 0], samples[:, 1])
    assert np.all(samples[:48] == 0.)
    peak = float(np.max(abs(samples)))
    assert .05 < peak < 1.
    output_hash = digest(samples.tobytes())
    assert output_hash == expected, (output_hash, expected)
    assert int(faults) == int(dropped) == 0
    return dict(frames=128, blocks=BLOCKS, events=events, j7_f32_sha256=output_hash,
                peak=peak, faults=int(faults), dropped_events=int(dropped), deadline_misses=int(misses),
                max_ns=int(max(times)), p99_ns=float(np.quantile(times, .99)),
                over_margin=int(sum(times > MARGIN)), times=packed(times.tobytes()))


def driven_score():
    events = [[frame, status, note, 100] for frame, status, note in score()]
    for controller, start, period in ((20, 173, 239), (21, 211, 149)):
        events.extend([frame, 0xb0, controller, 127 if i % 2 == 0 else 0]
                      for i, frame in enumerate(range(start, N, period)))
    return sorted(events, key=lambda event: event[0])


def electrical_reference():
    for path in sorted((ROOT / "evidence").glob("rf_d_pilot_returns[0-9][0-9].json"), reverse=True):
        result = read(path.relative_to(ROOT).as_posix())
        if result["passed"] and not result["wide"]:
            return path, result
    raise ValueError("The narrow return model requires a passed Radau contrast")


def main():
    assert not list(AREA.iterdir())
    seq = 1
    while (out := ROOT / f"evidence/rf_d_playable_pilot{seq:02}.json").exists():
        seq += 1
    sources = Sources(SOURCES)
    report = dict(passed=False, physical_measured=False, **sources.fields(),
                  pilot_reference=REFERENCE, pilot_reference_sha256=sha(ROOT / REFERENCE),
                  host_revision=HOST_REVISION, deadline_ns=MARGIN, builds={}, trials=[])
    env = dict(os.environ, RACKFORGE_OPTIMIZE_PLUGINS="0",
               PATH="C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;" + os.environ["PATH"])
    last = None

    def execute(key, args):
        nonlocal last
        command = list(map(str, args))
        proc = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, timeout=120)
        last = command, proc
        report["builds"][key] = dict(command=command, exit_code=proc.returncode,
                                     stdout_sha256=digest(proc.stdout), stderr=packed(proc.stderr))
        assert proc.returncode == 0, proc.stderr.decode(errors="replace")
        return proc

    try:
        assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=HOST, text=True).strip() == HOST_REVISION
        host_sources = (*HOST_SOURCES, SDK_PATH)
        assert not subprocess.check_output(["git", "status", "--porcelain", "--", *host_sources], cwd=HOST)
        report["host_sources"] = {path: sha(HOST / path) for path in host_sources}
        reference, electrical = electrical_reference()
        report["electrical_reference"] = reference.relative_to(ROOT).as_posix()
        report["electrical_reference_sha256"] = sha(reference)
        code, report["maps"] = generate()
        assert report["maps"] == electrical["maps"]
        for path in ("tools/rf_d_pilot_return_plant.rs", "tools/prepare_rf_d_pilot_returns.py"):
            assert electrical["source_sha256"][path] == sha(ROOT / path)
        prior = read(REFERENCE)
        assert prior["passed"] and prior["portable"]["bit_exact"]
        assert report["maps"]["wave_sha256"] == prior["wave_table_sha256"]
        guest = emit("pilot-return-guest.rs", code + (ROOT / GUEST).read_text(encoding="utf8"))
        sdk = AREA / "librackforge_plugin_sdk.rlib"
        component = AREA / "component.wasm"
        flags = [COMPILER, "--target", "wasm32-unknown-unknown", "-C", "target-feature=+simd128",
                 "-C", "opt-level=3", "-A", "dead_code"]
        execute("sdk", [*flags, "--edition=2024", "--crate-type", "rlib", "--crate-name", "rackforge_plugin_sdk",
                        HOST / SDK_PATH, "-o", sdk])
        guest_flags = [*flags, "--edition=2021", "--crate-type", "cdylib", "-C", "panic=abort",
                       "-C", "lto=fat", "--cfg", "pilot_returns", guest,
                       "--extern", f"rackforge_plugin_sdk={sdk}"]
        execute("guest_scalar", [*guest_flags, "-o", component])
        simd = AREA / "component-simd.wasm"
        execute("guest_simd", [*guest_flags, "--cfg", "pilot_returns_simd", "-o", simd])
        optimizer = Path(os.environ.get("RF_D_WASM_OPT", WASM_OPT))
        version = execute("optimizer_version", [optimizer, "--version"]).stdout.decode().strip()
        assert version.startswith("wasm-opt version 132"), version
        optimized = AREA / "component-opt.wasm"
        execute("optimize", [optimizer, simd, "-O4", "-o", optimized])
        report["optimizer"] = dict(version=version, sha256=sha(optimizer), input_sha256=sha(simd))
        store = HOST / "target/release/rackforge-store.exe"
        archive = AREA / ARTIFACT.name
        installed = AREA / "pilot-store"
        execute("package", [store, "pack-wasm", PACKAGE, optimized, archive])
        execute("install", [store, "install-local", archive, installed])
        manifest, = installed.rglob("rackforge-plugin.toml")
        assert sha(manifest.parent / "component.wasm") == sha(optimized)
        report["component_sha256"] = sha(optimized)
        report["store_sha256"] = sha(store)

        deps = HOST / "target/release/deps"
        core, midi = deps / HOST_CORE, deps / MIDI_LIB
        report["host_libraries"] = {path.name: sha(path) for path in (core, midi)}
        registry = Path(COMPILER).parents[4] / ".cargo/registry/src"
        imports = sorted(registry.glob("*/windows_x86_64_msvc-*/lib/*.lib"))
        libraries = sorted((HOST / "target/release/build").glob("*/out/*.lib"))
        native_dirs = list(dict.fromkeys(p.parent for p in [*libraries, *imports]))
        probe = AREA / "pilot-midi-rack.exe"
        execute("host", [HOST_COMPILER, "--edition=2021", "-C", "opt-level=3", "-L", f"dependency={deps}",
                         *[arg for path in native_dirs for arg in ("-L", f"native={path}")],
                         ROOT / MIDI_PROBE, "--extern", f"rackforge_core={core}",
                         "--extern", f"rackforge_midi_api={midi}", "-o", probe])
        base_events = driven_score()
        events = sorted(base_events + [
            [at, 0xb0, controller, 0 if i % 2 == 0 else 127]
            for controller, first, period in ((22, 1013, 1639), (23, 1427, 1979),
                                              (24, 37, 1831), (25, 91, 2239))
            for i, at in enumerate(range(first, N, period))
        ], key=lambda event: event[0])
        midi_score = AREA / "pilot-score.bin"
        midi_score.write_bytes(b"".join(struct.pack("<IBBBB", sample, status, note, value, 0)
                                        for sample, status, note, value in events))
        report["midi_score"] = events
        report["affinity"] = pin()
        direct = execute("direct_wasm", ["node", ROOT / NODE, optimized, json.dumps(events), N])
        raw = execute("scalar_wasm", ["node", ROOT / NODE, component, json.dumps(events), N])
        assert direct.stdout == raw.stdout
        neutral = execute("neutral_wasm", ["node", ROOT / NODE, optimized, json.dumps(score()), N])
        returns = execute("returns_wasm", ["node", ROOT / NODE, optimized, json.dumps(base_events), N, "--panel-state"])
        baseline = read(PANEL_BASELINE)["direct_wasm"]
        assert baseline["driven_j7_sha256"] == digest(returns.stdout)
        assert baseline["neutral_j7_sha256"] == digest(neutral.stdout)
        report["panel_baseline_sha256"] = sha(ROOT / PANEL_BASELINE)
        report["panel_state_round_trip"] = True

        phrase = [[61, 0x90, 57, 100], [6179, 0x80, 57, 100]]
        count = 8192
        clean = execute("panel_control", ["node", ROOT / NODE, optimized, json.dumps(phrase), count]).stdout
        neutral_samples = np.frombuffer(clean, "<f4").reshape(-1, 2)
        report["control_checks"] = {}
        for i, value in enumerate((127, 127, 0, 0, 127, 127)):
            control = sorted([*phrase, [173, 0xb0, 20 + i, value]], key=lambda event: event[0])
            audio = execute(f"panel_{i}", ["node", ROOT / NODE, optimized, json.dumps(control), count]).stdout
            samples = np.frombuffer(audio, "<f4").reshape(-1, 2)
            delta = abs(samples - neutral_samples)
            assert np.isfinite(samples).all() and float(delta.max()) > 1e-7
            assert np.array_equal(samples[:173], neutral_samples[:173])
            if i == 3:
                assert not samples[173 + 64:].any()
            report["control_checks"][i] = dict(max_delta=float(delta.max()), first_change=int(np.flatnonzero(delta[:, 0])[0]))
        assert len(direct.stdout) == len(neutral.stdout) == N * 8
        expected = digest(direct.stdout)
        assert expected != digest(neutral.stdout)
        report["direct_wasm"] = dict(driven_j7_sha256=expected, neutral_j7_sha256=digest(neutral.stdout),
                                     legacy_returns_j7_sha256=digest(returns.stdout))
        for attempt in (1, 2):
            run = execute(f"rack_{attempt}", [probe, manifest.parent, AREA / "pilot-cache", midi_score])
            audio = run.stdout[8 * BLOCKS:]
            if audio != direct.stdout:
                observed = np.frombuffer(audio, "<f4").reshape(N, 2)
                target = np.frombuffer(direct.stdout, "<f4").reshape(N, 2)
                indices = np.flatnonzero(np.any(observed.view("<u4") != target.view("<u4"), axis=1))
                first = int(indices[0])
                window = slice(max(0, first - 16), min(N, first + 48))
                report["rack_audio_difference"] = dict(
                    first_frame=first, different_frames=len(indices), max_absolute=float(abs(observed - target).max()),
                    window_start=window.start, observed=observed[window, 0].tolist(), expected=target[window, 0].tolist(),
                    nearby_events=[event for event in events if abs(event[0] - first) < 256],
                )
                replay = execute("rack_unchanged_replay", [probe, manifest.parent, AREA / "pilot-cache", midi_score])
                assert replay.stdout[8 * BLOCKS:] == audio
            trial = assess(run.stdout, run.stderr, expected, len(events))
            report["trials"].append(trial)
            print("RF_D_MIDI", attempt, {k: v for k, v in trial.items() if k != "times"}, flush=True)
        report["offline_margin_passed"] = all(t["over_margin"] == t["deadline_misses"] == 0 for t in report["trials"])
        report["archive_sha256"] = sha(archive)
        sources.unchanged()
        if report["offline_margin_passed"]:
            ARTIFACT.parent.mkdir(exist_ok=True)
            archive.replace(ARTIFACT)
            report["archive"] = ARTIFACT.relative_to(ROOT).as_posix()
        report["passed"] = True
    except Exception:
        report["failure"] = traceback.format_exc()
        if last is not None and last[1].returncode != 0:
            command, proc = last
            replay = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, timeout=120)
            report["unchanged_replay"] = dict(exit_code=replay.returncode, same_exit=replay.returncode == proc.returncode,
                                               stdout_sha256=digest(replay.stdout), stderr=packed(replay.stderr))
        raise
    finally:
        for path in AREA.iterdir():
            assert path.resolve().parent == AREA.resolve()
            if path.is_dir():
                assert path.name in ("pilot-cache", "pilot-store")
                shutil.rmtree(path)
            else:
                path.unlink()
        write(out, report)
    raise SystemExit(0 if report["offline_margin_passed"] else 1)


if __name__ == "__main__":
    main()
