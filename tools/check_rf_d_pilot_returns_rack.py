"""Run the bounded pilot on a real RackForge slot at 128 frames."""
import argparse
import ctypes
import os
import shutil
import subprocess
import traceback
from pathlib import Path
from ctypes import wintypes

import numpy as np

from affine_evidence import Sources
from check_rf_d_pilot_returns_asio import SOURCES as ASIO_SOURCES, campaign as physical_campaign
from check_hybrid_voice import packed
from check_recovery_cost import digest, read
from check_recovery_engine128 import HOST_CORE
from check_rf_d_pilot_returns import AREA, COMPILER, ROOT, SOURCES as PILOT_SOURCES, emit, generate, pin
from check_rf_d_reduced_engine_rack import ABI, HOST, HOST_COMPILER, HOST_REVISION, HOST_SOURCES, PLUGIN, package
from prepare_dual_chain import sha, write
from prepare_hybrid_stamp import once

OWN = "tools/check_rf_d_pilot_returns_rack.py"
PROBE = "tools/rf_d_pilot_returns_rack.rs"
SOURCES = (*PILOT_SOURCES, OWN, PROBE, PLUGIN, "tools/check_rf_d_reduced_engine_rack.py")
BLOCKS = 376
MARGIN = 128e9 / 48_000 / 2


def plugin(code):
    original = (ROOT / PLUGIN).read_text(encoding="utf8")
    original = once(original, "//! Native ABI adapter for the two frozen electrical scenes.\n", "")
    source = once(original, "reduced_engine::{Engine, Frame, BLOCK, RATE},",
                  "scene::Scene,\n    voice::{Frame, MAX_BLOCK as BLOCK, RATE},")
    source = once(source, "engine: Option<Engine>,", "engine: Option<Scene>,")
    source = once(source, "    frame: usize,\n", "")
    start = source.index("        let (bank, cap)")
    end = source.index("\n    }\n}", start)
    source = source[:start] + """        self.engine = Some(Scene::new(!negative));
        self.negative = negative;
        STATUS_OK""" + source[end:]
    source = once(source, """    if let Some(engine) = &mut voice.engine {
        engine.reset();
    }
    voice.frame = 0;""", """    if voice.engine.is_some() {
        return voice.prepare(voice.negative);
    }""")
    start = source.index("    let keys:")
    end = source.index("        return STATUS_INTERNAL_ERROR;", start)
    source = source[:start] + """    let mut result = [Frame::default(); BLOCK];
    if engine.render(&mut result[..frames]).is_err() {
""" + source[end:]
    source = once(source, "    voice.frame += frames;\n", "")
    source = once(source, "Positive reserve", "Driven returns")
    source = once(source, "Negative reserve", "Zero-drive control")
    return "//! Native ABI adapter for the staged pilot.\n" + code + f'#[path = "{(HOST / ABI).as_posix()}"] mod abi;\n' + source


def metrics(raw, stderr):
    tag, frames, count, measured, misses, faults = stderr.decode().strip().split(",")
    assert tag == "PILOT_RACK" and int(frames) == 128 and int(count) == BLOCKS
    times = np.frombuffer(raw[:8 * BLOCKS], "<u8")
    output = np.frombuffer(raw[8 * BLOCKS:], "<f4").reshape(BLOCKS * 128, 2)
    assert np.isfinite(output).all() and output[:, 0].tobytes() == output[:, 1].tobytes()
    assert 0 < int(measured) <= max(times) and min(times) > 0
    return dict(max_ns=int(max(times)), p99_ns=float(np.quantile(times, .99)),
                median_ns=float(np.median(times)), over_margin=int(sum(times > MARGIN)),
                faults=int(faults), deadline_misses=int(misses),
                passed=bool(max(times) <= MARGIN and int(faults) == int(misses) == 0),
                j7_f32_sha256=digest(output[:, 0].tobytes()), times=packed(times.tobytes()))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--physical", action="store_true")
    parser.add_argument("--physical-cpu", type=int, help="logical CPU for all three physical banks (default 9)")
    options = parser.parse_args()
    if options.physical_cpu is not None and (not options.physical or not 0 <= options.physical_cpu < 64):
        parser.error("--physical-cpu requires --physical and a logical CPU from 0 to 63")
    cpu = 9 if options.physical_cpu is None else options.physical_cpu
    assert not list(AREA.iterdir())
    control, native = next((path, report) for path in sorted(
        (ROOT / "evidence").glob("rf_d_pilot_returns[0-9][0-9].json"), reverse=True)
        if (report := read(path.relative_to(ROOT).as_posix()))["passed"])
    seq = 1
    while (output := ROOT / f"evidence/rf_d_pilot_returns_rack{seq:02}.json").exists():
        seq += 1
    sources = Sources((*SOURCES, *ASIO_SOURCES) if options.physical else SOURCES)
    report = dict(passed=False, physical_measured=False, audio_device_opened=False, wide=native.get("wide", False), **sources.fields(),
                  native_sha256=sha(control), host_revision=HOST_REVISION, margin_ns=MARGIN,
                  builds={}, trials={})
    env = dict(os.environ, PATH="C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;" + os.environ["PATH"])
    last = None

    def run(args):
        nonlocal last
        command = list(map(str, args))
        process = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, timeout=120)
        last = command, process
        result = dict(command=command, exit_code=process.returncode, stderr=packed(process.stderr),
                      stdout_sha256=digest(process.stdout), stdout_bytes=len(process.stdout))
        assert process.returncode == 0, process.stderr.decode(errors="replace")
        return process, result

    try:
        assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=HOST, text=True).strip() == HOST_REVISION
        assert not subprocess.check_output(["git", "status", "--porcelain", "--", *HOST_SOURCES], cwd=HOST)
        report["host_sources"] = {path: sha(HOST / path) for path in HOST_SOURCES}
        deps = HOST / "target/release/deps"
        core = deps / HOST_CORE
        report["core_sha256"] = sha(core)
        report["cutoff_laws"] = native.get("cutoff_laws", report["wide"])
        code, report["maps"] = generate(report["cutoff_laws"])
        assert report["maps"] == native["maps"]
        report["affinity"] = pin()
        path = AREA / "reduced-rack-package"
        package(path)
        dll = path / "rf-d-loaded.dll"
        component = plugin(code)
        _, report["builds"]["plugin"] = run([COMPILER, "--edition=2021", "-C", "opt-level=3", "-C", "target-feature=+fma",
            "-C", "panic=abort", "-A", "dead_code", "--cfg", "pilot_returns",
            *(["--cfg", "pilot_wide_returns"] if report["wide"] else []), "--crate-type", "cdylib",
            emit("pilot-native.rs", component), "-o", dll])
        report["component_sha256"] = sha(dll)
        imports = sorted((Path(COMPILER).parents[4] / ".cargo/registry/src").glob("*/windows_x86_64_msvc-*/lib/*.lib"))
        libs = sorted((HOST / "target/release/build").glob("*/out/*.lib"))
        native_dirs = list(dict.fromkeys(p.parent for p in [*libs, *imports]))
        exe = AREA / "pilot-rack.exe"
        _, report["builds"]["rack"] = run([HOST_COMPILER, "--edition=2021", "-C", "opt-level=3",
            "-L", f"dependency={deps}", *[arg for d in native_dirs for arg in ("-L", f"native={d}")],
            ROOT / PROBE, "--extern", f"rackforge_core={core}", "-o", exe])
        for preset in ("negative", "positive", "positive"):
            process, execution = run([exe, path, preset])
            item = metrics(process.stdout, process.stderr)
            report["trials"].setdefault(preset, []).append(dict(execution=execution, metrics=item))
            print("PILOT_RACK", preset, {k: v for k, v in item.items() if k != "times"}, flush=True)
        target = native["native"]["host_expected_j7_f32_sha256"]
        report["exact_native_output"] = all(item["metrics"]["j7_f32_sha256"] == target
                                           for item in report["trials"]["positive"])
        assert report["exact_native_output"]
        report["passed"] = all(item["metrics"]["passed"] for run in report["trials"].values() for item in run)
        if options.physical:
            # The callback pins itself. The supervisor needs the other CPUs.
            kernel = ctypes.WinDLL("kernel32", use_last_error=True)
            kernel.GetCurrentProcess.restype = wintypes.HANDLE
            kernel.SetProcessAffinityMask.argtypes = (wintypes.HANDLE, ctypes.c_size_t)
            kernel.SetProcessAffinityMask.restype = wintypes.BOOL
            if not kernel.SetProcessAffinityMask(kernel.GetCurrentProcess(), report["affinity"]["original_mask"]):
                raise ctypes.WinError(ctypes.get_last_error())
            physical_campaign(path, component, report, env, cpu)
        sources.unchanged()
    except Exception:
        report["failure"] = traceback.format_exc()
        if last is not None and last[1].returncode != 0:
            command, process = last
            replay = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, timeout=120)
            report["unchanged_replay"] = dict(exit_code=replay.returncode, same_exit=replay.returncode == process.returncode,
                                              stderr=packed(replay.stderr), stdout_sha256=digest(replay.stdout))
        raise
    finally:
        write(output, report)
        for path in AREA.iterdir():
            assert path.resolve().parent == AREA.resolve()
            if path.is_dir():
                assert path.name in ("reduced-rack-package", "reduced-asio-control", "pilot-cache")
                shutil.rmtree(path)
            else:
                path.unlink()


if __name__ == "__main__":
    main()
