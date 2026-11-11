"""Render the admitted Q15/R59 fixtures through a native RackForge slot."""
import json
import subprocess
from pathlib import Path

import numpy as np

from check_hybrid_voice import packed, unpack
from check_recovery_cost import digest
from check_recovery_engine128 import HOST_CORE
from check_rf_d_pilot_returns import AREA, COMPILER, LIB, ROOT, SCENE, emit
from check_rf_d_pilot_returns_rack import PROBE, plugin
from check_rf_d_reduced_engine_rack import HOST, HOST_COMPILER, HOST_REVISION, HOST_SOURCES, PLUGIN, package
from prepare_dual_chain import sha
from prepare_hybrid_stamp import once

OWN = "tools/rf_d_pilot_q15_rack.py"
SCENE_RUST = "tools/rf_d_pilot_q15_rack_scene.rs"
SOURCES = (OWN, SCENE_RUST, PROBE, PLUGIN, "tools/check_rf_d_pilot_returns_rack.py",
           "tools/check_rf_d_reduced_engine_rack.py", "tools/check_recovery_engine128.py",
           "tools/check_recovery_host.py")
PACKAGE = "q15-rack-package"
REPEATS = 64
STREAM_FRAMES = 128 * 128


def component(code, payload):
    words = np.frombuffer(payload, "<u8")
    assert len(words) == 149 + 512 * 6

    def rust_values(row):
        return "[" + ",".join(f"f64::from_bits(0x{word:016x})" for word in row) + "]"

    fixture = emit("q15-rack-fixture.rs",
                   "pub const HEADER: [f64; 149] = " + rust_values(words[:149]) + ";\n"
                   + "pub static INPUT: [[f64; 6]; 512] = [\n"
                   + ",\n".join(map(rust_values, words[149:].reshape(512, 6))) + "\n];\n")
    code = once(code, f'#[path = "{(ROOT / SCENE).as_posix()}"] mod scene;',
                f'#[path = "{(ROOT / SCENE_RUST).as_posix()}"] mod scene;')
    code += f'#[path = "{fixture.as_posix()}"] mod fixture;\n'
    return once(plugin(code), "self.engine = Some(Scene::new(!negative));",
                """self.engine = match Scene::new() {
            Ok(scene) => Some(scene),
            Err(_) => return STATUS_INTERNAL_ERROR,
        };""")


def metrics(raw, expected, margin, peak_key):
    header_bytes = (4 + 2 * REPEATS) * 8
    count, peak, misses, faults = map(int, np.frombuffer(raw[:32], "<u8"))
    times = np.frombuffer(raw[32:header_bytes], "<u8").reshape(REPEATS, 2)
    assert count == 2 * REPEATS and 0 < peak <= times.max() and times.min() > 0
    audio = raw[header_bytes:]
    assert len(audio) == len(expected)
    samples = np.frombuffer(audio, "<f4")
    assert np.isfinite(samples).all()

    def phase(values):
        return dict(median_ns=float(np.median(values)), max_ns=int(values.max()),
                    over_margin=int(np.count_nonzero(values > margin)))

    return dict(startup=phase(times[:, 0]), warm=phase(times[:, 1]), exact_native=audio == expected,
                j7_f32_sha256=digest(audio),
                max_difference_f32=float(abs(samples - np.frombuffer(expected, "<f4")).max()),
                deadline_misses=misses, faults=faults, times=packed(times.tobytes()), **{peak_key: peak})


def stream_check(run, host, path, exe, payload, expected):
    reference = run([exe, "stream-128"], payload)
    exact_partition = reference == run([exe, "stream-64"], payload)
    audio, state = reference[:-19 * 8], reference[-19 * 8:]
    assert len(audio) == STREAM_FRAMES * 2 * 4 and audio.startswith(expected)
    samples = np.frombuffer(audio, "<f4")
    assert np.isfinite(samples).all() and np.isfinite(np.frombuffer(state, "<f8")).all()
    rendered = run([host, path, "q15-stream"])
    peak, misses, faults = map(int, np.frombuffer(rendered[-24:], "<u8"))
    exact_host = rendered[:-24] == audio
    return dict(passed=exact_partition and exact_host and faults == 0, frames=STREAM_FRAMES,
                exact_partition=exact_partition, exact_host=exact_host,
                native_j7_f32_sha256=digest(audio), final_state_sha256=digest(state),
                host_peak_ns=peak, host_deadline_misses=misses, host_faults=faults)


def campaign(run, report, receipt, code, flags, cfg, exe, payload, rows, continuous=False, physical_env=None):
    admitted = json.loads(receipt.read_text(encoding="utf8"))
    assert admitted["passed"] and admitted["dynamic_q15"] and admitted["partition_bit_exact"]
    assert admitted["branch"] == report["branch"]
    assert unpack(admitted["input"]) == payload and admitted["input_sha256"] == report["input_sha256"]
    for key in ("map_sha256", "output_sha256", "compiler_sha256", "library_sha256"):
        assert admitted[key] == report[key], key
    assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=HOST, text=True).strip() == HOST_REVISION
    assert not subprocess.check_output(["git", "status", "--porcelain", "--", *HOST_SOURCES], cwd=HOST)

    deps = HOST / "target/release/deps"
    core = deps / HOST_CORE
    path = AREA / PACKAGE
    dll = path / "rf-d-loaded.dll"
    host = AREA / "q15-rack.exe"
    rack = report["rack"] = dict(native_receipt=receipt.relative_to(ROOT).as_posix(),
                                 native_receipt_sha256=sha(receipt), host_revision=HOST_REVISION,
                                 core_sha256=sha(core), physical_measured=False,
                                 host_sources={name: sha(HOST / name) for name in HOST_SOURCES},
                                 host_compiler_sha256=sha(HOST_COMPILER), pairs=[])
    package(path)
    if continuous:
        cfg = [*cfg, "--cfg", "pilot_q15_continuous"]
    source = component(code, payload)
    component_flags = [*flags, *cfg, "-C", "panic=abort", "--extern", f"rf_d_circuit={LIB}"]
    run([*component_flags, "--crate-type", "cdylib", emit("q15-rack-component.rs", source), "-o", dll])
    rack["component_sha256"] = sha(dll)
    imports = (Path(COMPILER).parents[4] / ".cargo/registry/src").glob("*/windows_x86_64_msvc-*/lib/*.lib")
    libs = (HOST / "target/release/build").glob("*/out/*.lib")
    native_dirs = sorted({p.parent for p in [*libs, *imports]})
    run([HOST_COMPILER, "--edition=2021", "-C", "opt-level=3", "-L", f"dependency={deps}",
         *[arg for d in native_dirs for arg in ("-L", f"native={d}")], ROOT / PROBE,
         "--extern", f"rackforge_core={core}", "-o", host])

    expected = np.repeat(rows[1::2, 0].astype("<f4"), 2).tobytes()
    rack["native_j7_f32_sha256"] = digest(expected)
    for order in (("native", "direct", "host"), ("host", "direct", "native")):
        pair = {}
        for which in order:
            if which == "native":
                keys = ("blocks", "median_ns", "max_ns", "allocations")
                pair[which] = dict(zip(keys, map(int, run([exe, "bench"], payload).split(b",")), strict=True))
            else:
                mode, peak = ("q15", "telemetry_max_ns") if which == "host" else ("q15-direct", "process_max_ns")
                pair[which] = metrics(run([host, path, mode]), expected, report["budget_ns"], peak)
        pair["warm_median_delta_ns"] = pair["host"]["warm"]["median_ns"] - pair["native"]["median_ns"]
        pair["rack_minus_direct_median_ns"] = pair["host"]["warm"]["median_ns"] - pair["direct"]["warm"]["median_ns"]
        pair["direct_minus_native_median_ns"] = pair["direct"]["warm"]["median_ns"] - pair["native"]["median_ns"]
        rack["pairs"].append(pair)
    report["rack_integrated"] = all(
        pair["host"]["exact_native"] and pair["host"]["faults"] == 0
        and pair["direct"]["exact_native"] and pair["direct"]["faults"] == 0
        and pair["native"]["allocations"] == 0
        for pair in rack["pairs"])
    rack["warm_realtime"] = report["rack_integrated"] and all(
        pair["host"]["warm"]["over_margin"] == 0 and pair["host"]["deadline_misses"] == 0
        for pair in rack["pairs"])
    if continuous:
        rack["continuous"] = stream_check(run, host, path, exe, payload, expected)
        report["rack_integrated"] &= rack["continuous"]["passed"]
        rack["warm_realtime"] &= rack["continuous"]["passed"]
        print("Q15 CONTINUOUS", rack["continuous"], flush=True)
    print("Q15 RACK", report["rack_integrated"], rack["warm_realtime"],
          [(p["native"], p["direct"]["warm"], p["host"]["startup"], p["host"]["warm"],
            p["rack_minus_direct_median_ns"])
           for p in rack["pairs"]], flush=True)
    if physical_env is not None and report["rack_integrated"]:
        from check_rf_d_pilot_returns_asio import campaign as physical_campaign
        physical_campaign(path, source, rack, physical_env, cpu=9, component_flags=component_flags)
