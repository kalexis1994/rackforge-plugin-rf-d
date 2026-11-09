"""Build and admit the MIDI pilot as an installable RackForge audition package."""
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
from check_rf_d_reduced_voice import (
    AREA, COMPILER, DATA, DOC, FIR, GUEST, MAPS, N, OWN, PLANT, PROBE, ROOT,
    VOICE, digest, pin, pilot_plant, portable_source, prepare_pilot, read, score, sha, write,
)

PACKAGE = ROOT / "plugin/package"
ARTIFACT = ROOT / "artifacts/rf-d-pilot-0.1.0.rfplugin"
REFERENCE = "evidence/rf_d_reduced_voice_pilot03.json"
MIDI_PROBE = "tools/rf_d_playable_pilot_probe.rs"
PROTOCOL = "docs/VOZ_PILOTO_JUGABLE_PROTOCOLO.md"
MARGIN = 128e9 / 48_000 / 2
BLOCKS = N // 128
MIDI_LIB = "librackforge_midi_api-9bf68be69a56bbe5.rlib"
SDK_PATH = "crates/rackforge-plugin-sdk/src/lib.rs"
SOURCES = (OWN, DOC, DATA, FIR, GUEST, MAPS, PLANT, PROBE, VOICE, MIDI_PROBE, PROTOCOL,
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
        wave, data, checks = prepare_pilot()
        report["maps"] = checks
        prior = read(REFERENCE)
        assert prior["passed"] and prior["portable"]["bit_exact"]
        for name in ("candidate_maps_sha256", "wave_table_sha256"):
            assert checks[name] == prior[name]
        guest = portable_source(pilot_plant(data), wave)
        sdk = AREA / "librackforge_plugin_sdk.rlib"
        component = AREA / "component.wasm"
        flags = [COMPILER, "--target", "wasm32-unknown-unknown", "-C", "target-feature=+simd128",
                 "-C", "opt-level=3", "-A", "dead_code"]
        execute("sdk", [*flags, "--edition=2024", "--crate-type", "rlib", "--crate-name", "rackforge_plugin_sdk",
                        HOST / SDK_PATH, "-o", sdk])
        execute("guest", [*flags, "--edition=2021", "--crate-type", "cdylib", "-C", "panic=abort",
                          "-C", "lto=fat", guest, "--extern", f"rackforge_plugin_sdk={sdk}", "-o", component])
        store = HOST / "target/release/rackforge-store.exe"
        archive = AREA / ARTIFACT.name
        installed = AREA / "pilot-store"
        execute("package", [store, "pack-wasm", PACKAGE, component, archive])
        execute("install", [store, "install-local", archive, installed])
        manifest, = installed.rglob("rackforge-plugin.toml")
        assert sha(manifest.parent / "component.wasm") == sha(component)
        report["component_sha256"] = sha(component)
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
        events = score()
        midi_score = AREA / "pilot-score.bin"
        midi_score.write_bytes(b"".join(struct.pack("<IBBBB", sample, status, note, 100, 0)
                                        for sample, status, note in events))
        report["midi_score"] = events
        report["affinity"] = pin()
        for attempt in (1, 2):
            run = execute(f"rack_{attempt}", [probe, manifest.parent, AREA / "pilot-cache", midi_score])
            trial = assess(run.stdout, run.stderr, prior["portable"]["output_sha256"], len(events))
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
