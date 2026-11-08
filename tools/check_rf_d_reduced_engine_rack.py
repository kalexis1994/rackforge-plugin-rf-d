"""Load the validated RF-D native engine in RackForge and time one real slot."""
import os
import shutil
import subprocess
import traceback
from pathlib import Path

import numpy as np

from affine_evidence import Sources
from check_hybrid_voice import packed, unpack
from check_recovery_cost import digest
from check_recovery_engine128 import HOST_CORE
from check_recovery_host import HOST, HOST_COMPILER
from check_rf_d_reduced_contour_ports import unpack_stamp
from check_rf_d_reduced_engine import (
    AREA, BANKS, COMPILER, CONTOUR, DEADLINE_NS, KERNEL, LIB, MODEL, MODULES, N, PANEL, ROOT,
    SOURCES as ENGINE_SOURCES, TABLE, emit, maps, materialize, pin, read, read_oracle, references, source, text,
)
from prepare_dual_chain import sha, write
from validate_vco_family_voice_bus import J7

OWN = "tools/check_rf_d_reduced_engine_rack.py"
PLUGIN = "tools/rf_d_reduced_engine_native_plugin.rs"
PROBE = "tools/rf_d_reduced_engine_rack_probe.rs"
ABI = "crates/rackforge-plugin-api/src/abi.rs"
HOST_REVISION = "7a14c68aa208290587d985d606b0dbc17600ee07"
HOST_SOURCES = (ABI, "crates/rackforge-core/src/hosted.rs", "crates/rackforge-core/src/rack_voice.rs",
                "crates/rackforge-core/src/parallel_render.rs")
SOURCES = (*ENGINE_SOURCES, OWN, PLUGIN, PROBE)


def plugin_source(kernel, banks):
    path = text(PLUGIN)
    for name, bank in banks.items():
        path = path.replace(name.upper() + "_BANK", bank.as_posix())
    glue = emit("native-plugin.rs", path)
    parts = dict(family=kernel, graph=AREA / "hot-graph.rs", abi=HOST / ABI,
                 incidence=ROOT / "crates/rf-d-circuit/src/incidence_matrix.rs", native_plugin=glue)
    parts.update({name: ROOT / item for name, item in MODULES.items() if name != "reduced_probe"})
    code = "pub use rf_d_circuit::{junction_charge, StepError};\n"
    for name, path in parts.items():
        code += f'#[path = "{path.as_posix()}"] mod {name};\n'
    return emit("native-component.rs", code)


def package(path):
    path.mkdir()
    (path / "rackforge-plugin.toml").write_text("""schema_version = 1
id = "org.rackforge.lab.rf-d-contours"
name = "RF-D Loaded Contours Lab"
vendor = "RackForge"
version = "0.1.0"
kind = "instrument"
state_version = 1
capabilities = ["audio_output", "presets"]

[audio]
output_buses = [{ id = "main", name = "Output", channels = 2, layout = "stereo" }]

[api]
major = 1
minor = 0

[binaries]
windows-x86_64 = "rf-d-loaded.dll"
""", encoding="utf8", newline="\n")


def expected_values(trial):
    out = []
    for line in unpack(trial["stdout"]).decode().splitlines():
        tag, *fields = line.split(",")
        if tag == "GRID" and int(fields[0]) > 0:
            words = fields[4:]
            pair = np.array([int(words[J7], 16), int(words[J7 + N], 16)], "<u8").view("<f8")
            out.append(float(pair[0] + pair[1]))
    assert len(out) == 128
    return np.asarray(out, "<f4")


def metrics(raw, target):
    header, samples = None, []
    for line in raw.decode().splitlines():
        if line.startswith("RACK,"):
            assert header is None
            header = list(map(int, line.split(",")[1:]))
        if line.startswith("SAMPLE,"):
            _, index, left, right = line.split(",")
            assert int(index) == len(samples)
            samples.append([int(left, 16), int(right, 16)])
    frames, elapsed, count, reported, misses, faults = header
    assert frames == len(samples) == 128 and count == 1 and faults == 0
    assert 0 < reported <= elapsed
    sound = np.asarray(samples, "<u4").view("<f4")
    assert np.isfinite(sound).all() and np.array_equal(sound[:, 0], sound[:, 1])
    difference = float(np.max(abs(sound[:, 0].astype(np.float64) - target)))
    assert difference <= 2e-12 + 1e-7 * max(abs(target))
    return dict(frames=frames, elapsed_ns=elapsed, rack_telemetry_ns=reported,
                deadline_misses=misses, faults=faults, max_difference_from_native_v=difference,
                native_output_bit_exact=np.array_equal(sound[:, 0], target),
                deadline_passed=elapsed <= DEADLINE_NS and misses == 0)


def main():
    assert not list(AREA.iterdir())
    base, native = next((path, report) for path in sorted(
        (ROOT / "evidence").glob("rf_d_reduced_engine[0-9][0-9].json"), reverse=True)
        if (report := read(path.relative_to(ROOT).as_posix()))["passed"] and report.get("clock_banks", BANKS) == BANKS)
    sequence = 1
    while (out := ROOT / f"evidence/rf_d_reduced_engine_rack{sequence:02}.json").exists():
        sequence += 1
    sources = Sources(SOURCES)
    report = dict(passed=False, physical_measured=False, audio_device_opened=False, **sources.fields(),
                  native_evidence=base.name, native_sha256=sha(base), deadline_ns=DEADLINE_NS,
                  host_revision=HOST_REVISION, trials={}, builds={})
    env = dict(os.environ, PATH="C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;" + os.environ["PATH"])
    last = None

    def run(name, args, binary=False):
        nonlocal last
        command = list(map(str, args))
        proc = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, timeout=180)
        receipt = dict(command=command, exit_code=proc.returncode, stderr=packed(proc.stderr),
                       stdout=dict(sha256=digest(proc.stdout), bytes=len(proc.stdout)) if binary else packed(proc.stdout))
        last = command, proc
        report["builds"][name] = receipt
        assert proc.returncode == 0, proc.stderr.decode(errors="replace")
        return proc.stdout

    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=HOST, text=True).strip()
        assert commit == HOST_REVISION
        assert not subprocess.check_output(["git", "status", "--porcelain", "--", *HOST_SOURCES], cwd=HOST)
        report["host_sources"] = {path: sha(HOST / path) for path in HOST_SOURCES}
        deps = HOST / "target/release/deps"
        core = deps / HOST_CORE
        report["host_core_sha256"] = sha(core)
        report["compiler_sha256"] = sha(Path(COMPILER))
        report["host_compiler_sha256"] = sha(HOST_COMPILER)
        ref, report["reference_inputs"] = references()
        assert report["reference_inputs"] == native["reference_inputs"]
        table, *_ = materialize(read_oracle())
        report["table_sha256"] = digest(table)
        assert report["table_sha256"] == read(MODEL)["table_sha256"] == native["table_sha256"]
        table_path = AREA / TABLE
        table_path.write_bytes(table)
        kernel = emit("family-kernel.rs", text(KERNEL).replace("H128_VOICE_TABLE_PATH", table_path.as_posix())
                      .replace("VCO_PANEL_PORT_PATH", (ROOT / PANEL).as_posix()))
        branches = ("negative", "positive")
        keys = [ref[name][1][0] for name in branches]
        path = AREA / "rack-anchors.bin"
        np.asarray([np.r_[key[3].ravel(), key[0], 0.] for key in keys], "<f8").tofile(path)
        report["affinity"] = pin()
        probe = AREA / "rack-prepare.exe"
        flags = ["--edition=2021", "-C", "opt-level=3", "-A", "dead_code", "-C", "target-feature=+fma"]
        run("prepare", [COMPILER, *flags, "-C", "link-arg=-Wl,--stack,33554432", "--cfg", "laboratory",
                        source(kernel), "--extern", f"rf_d_circuit={LIB}", "-o", probe])
        raw = run("stamps", [probe, "contour-stamps", path], binary=True)
        banks = {}
        for name, key, row in zip(branches, keys, np.frombuffer(raw, "<f8").reshape(2, -1)):
            parts, _, phase, _ = unpack_stamp(row)
            bank = AREA / f"audio-{name}.bin"
            with bank.open("wb") as stream:
                stream.write(np.asarray(np.r_[key[3].ravel(), key[0]], "<f8").tobytes())
                for chunk in maps(parts[1], phase, key[3]):
                    stream.write(chunk)
            assert sha(bank) == native["trials"][name]["bank_sha256"]
            banks[name] = bank
        report["banks_sha256"] = {name: sha(bank) for name, bank in banks.items()}
        package_path = AREA / "reduced-rack-package"
        package(package_path)
        dll = package_path / "rf-d-loaded.dll"
        run("plugin", [COMPILER, *flags, "--crate-type", "cdylib", "-C", "panic=abort",
                       plugin_source(kernel, banks), "--extern", f"rf_d_circuit={LIB}", "-o", dll])
        report["plugin_sha256"] = sha(dll)
        report["manifest_sha256"] = sha(package_path / "rackforge-plugin.toml")
        exe = AREA / "rack-engine.exe"
        registry = Path(COMPILER).parents[4] / ".cargo/registry/src"
        imports = sorted(registry.glob("*/windows_x86_64_msvc-*/lib/*.lib"))
        libraries = sorted((HOST / "target/release/build").glob("*/out/*.lib"))
        native_dirs = list(dict.fromkeys(p.parent for p in [*libraries, *imports]))
        run("rack", [HOST_COMPILER, "--edition=2021", "-C", "opt-level=3", "-C", "link-arg=/STACK:33554432",
                     "-L", f"dependency={deps}", *[arg for p in native_dirs for arg in ("-L", f"native={p}")],
                     ROOT / PROBE, "--extern", f"rackforge_core={core}", "-o", exe])
        report["rack_probe_sha256"] = sha(exe)
        for label in branches:
            target = expected_values(native["trials"][label]["runs"]["128"])
            passes = []
            for attempt in range(1, 3):
                key = f"rack_{label}_{attempt}"
                raw = run(key, [exe, package_path, label])
                result = metrics(raw, target)
                passes.append(dict(raw=report["builds"].pop(key), metrics=result))
                print("RACK_FRAME", label, attempt, result, flush=True)
            report["trials"][label] = passes
        report["passed"] = True
        report["rack_offline_deadline_passed"] = all(
            item["metrics"]["deadline_passed"] for passes in report["trials"].values() for item in passes)
        sources.unchanged()
    except Exception:
        report["failure"] = traceback.format_exc()
        if last is not None and last[1].returncode != 0:
            command, original = last
            replay = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, timeout=180)
            report["unchanged_replay"] = dict(exit_code=replay.returncode, stderr=packed(replay.stderr),
                                              same_status=replay.returncode == original.returncode)
        raise
    finally:
        write(out, report)
        for path in AREA.iterdir():
            assert path.resolve().parent == AREA.resolve()
            if path.is_dir():
                assert path.name == "reduced-rack-package"
                shutil.rmtree(path)
            else:
                path.unlink()


if __name__ == "__main__":
    main()
