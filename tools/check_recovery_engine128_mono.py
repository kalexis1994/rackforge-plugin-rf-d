"""Verify the nominal loaded voice through wasm-v1 and the physical rejection probe."""

import json
import shutil
import subprocess
import traceback
from pathlib import Path

import numpy as np

from check_hybrid_voice import packed, unpack
from check_recovery_cost import digest, read
from check_recovery_engine128_smt import NVIDIA_ENDPOINT
from check_recovery_host import COLUMNS
from check_recovery_host128 import ASIO_DRIVER, asio_profile, read_override, restore_override
from prepare_dual_chain import ROOT, sha

GUEST = "tools/recovery_engine128_mono_guest.rs"
HOST = "tools/recovery_engine128_mono_host.rs"
RUNNER = "tools/check_recovery_engine128_mono.py"
NODE = "tools/recovery_engine128_mono_wasm.js"
PROTOCOL = "docs/RECOVERY_ENGINE128_MONO_PROTOCOLO.md"
VOICE = "crates/rf-d-circuit/src/monophonic_voice.rs"
PATCH = "crates/rf-d-circuit/tests/support/mixer_chain_lab.rs"
ELECTRICAL = (
    "evidence/mono_voice_native01.json", "evidence/mono_voice_analysis01.json",
    "evidence/mono_voice_tests01.json", "evidence/recovery_engine128_reserve07.json",
    "evidence/recovery_engine128_broadcast_fir07.json", "evidence/recovery_engine128_smt18.json",
)
STATE_BYTES = 242 * 8


def guest_source():
    source = (ROOT / GUEST).read_text(encoding="utf8")
    return source.replace("MONO_VOICE_PATH", (ROOT / VOICE).as_posix()).replace(
        "MONO_PATCH_PATH", (ROOT / PATCH).as_posix()).encode()


def host_source(probe, replace_once):
    source = probe.decode()
    for old, new in [
        ('        Some("smt-endpoints") =>', '''        Some("engine-mono-fence") => return engine_mono_fence(Path::new(&args[1]), Path::new(&args[2])),
        Some("smt-endpoints") =>'''),
        ('    silence: bool,', '    silence: bool,\n    mono: bool,\n    layers: ControlLayers,'),
        ('matches!(mode, "rack" | "control")', 'matches!(mode, "rack" | "control" | "mono")'),
        ('allocated_blocks: 0, silence: mode == "control",',
         'allocated_blocks: 0, silence: mode == "control", mono: mode == "mono",\n            layers: ControlLayers::default(),'),
        ('        let padding = self.startup.min(frames);', '''        let padding = self.startup.min(frames);
        if self.mono && self.calls < 2 {
            // Establish the physical clock before invoking the guarded full solver.
            output.fill(0.);
            self.calls += 1;
            self.startup -= padding;
            return (frames - padding) as i32;
        }'''),
        ('                let telemetry = pool.telemetry().clone();', '''                if self.mono {
                    mono_note(rack, &mut self.layers);
                }
                let telemetry = pool.telemetry().clone();'''),
    ]:
        source = replace_once(source, old, new)
    return (source + "\n" + (ROOT / HOST).read_text(encoding="utf8")).encode()


def check_electrical_inputs(artifacts):
    native, analysis, previous_qa, reserve, fir, physical = (read(name) for name in ELECTRICAL)
    assert native["passed"] and analysis["passed"] and previous_qa["passed"]
    assert reserve["passed"] and fir["passed"] and physical["admitted_policy"] == "quiet-event"
    assert unpack(fir["fir_check"]).strip() == b"FIR_EXACT,9288,4,48"
    kernel = artifacts["engine_kernel_columns.rs"]
    assert kernel == reserve["variants"]["registers"]["kernel_sha256"] == fir["kernel_sha256"]
    assert kernel == physical["artifact_sha256"]["engine_kernel_columns.rs"]
    assert artifacts["package-control/component.wasm"] == physical["artifact_sha256"]["package-control/component.wasm"]
    assert reserve["variants"]["scalar"]["modes"] == reserve["variants"]["registers"]["modes"]
    return {path: sha(ROOT / path) for path in ELECTRICAL}


def reference_trajectory():
    reference = read(ELECTRICAL[0])
    profile, = [item for item in reference["profiles"] if item["args"] == ["128", "coarse", "480"]]
    return profile["measurements"]


def compare_trajectory(raw):
    reference = reference_trajectory()
    states = []
    volts = []
    position = 0
    next_state = 0
    while True:
        stop = position + STATE_BYTES
        data = np.frombuffer(raw[position:stop], "<f8")
        assert len(data) == 242 and np.isfinite(data).all()
        states.append(data)
        position = stop
        assert data[236] == next_state
        if next_state == 480:
            break
        frames = min(128, 480 - next_state)
        end = position + frames * 8
        samples = np.frombuffer(raw[position:end], "<f4").reshape(frames, 2)
        assert np.array_equal(samples[:, 0].view("<u4"), samples[:, 1].view("<u4"))
        volts.append(samples[:, 0])
        position = end
        next_state += frames
    assert position == len(raw)
    observed = np.concatenate(volts).astype("f8")
    target = np.array([reference["audio"][str(i)] for i in range(480)])
    assert np.isfinite(observed).all() and np.all(observed[:48] == 0.)
    peak = float(max(abs(target)))
    error = observed - target
    assert peak > 0. and max(abs(observed)) > 0.
    audio = dict(peak_v=peak, relative_rms=float(np.linalg.norm(error) / np.linalg.norm(target)),
                 peak_relative_error=float(max(abs(error)) / peak), mean_error_v=float(abs(error.mean())))
    assert audio["relative_rms"] <= .001 and audio["peak_relative_error"] <= .003
    assert audio["mean_error_v"] <= 1e-6

    nodes = []
    for key, data in (("INITIAL", states[0]), ("FINAL", states[-1])):
        oracle = np.array([int(v) for v in reference["states"][key]], "<u8").view("<f8").reshape(2, 118)
        current = data[:236].reshape(2, 118)
        difference = (current[0] - oracle[0]) + (current[1] - oracle[1])
        nodes.append(float(max(abs(difference))))
    assert max(nodes) <= 1e-6
    max_limits = np.max([row[239:242] for row in states[1:]], axis=0)
    assert np.all(max_limits <= [1e-12, 2e-9, 1.])
    assert all(0 < row[237] <= row[238] for row in states[1:])
    bus = [float(row[116] + row[234]) for row in states]
    assert all(value < -.125 for value in bus)
    return dict(audio=audio, maximum_initial_final_node_error_v=nodes,
                maximum_residual_correction_estimator=max_limits.tolist(), bus_v=bus,
                h128_bus_domain_v=[-.125, .125],
                contour_timing_v=[[float(row[i] + row[i + 118]) for i in (5, 38)] for row in states],
                samples=480, latency_frames=48)


def parse_timed_rejection(raw, stream):
    assert NVIDIA_ENDPOINT in stream.splitlines()
    rows = np.frombuffer(raw, "<u8").reshape(3, len(COLUMNS) + 8)
    assert np.all(rows[:, 3] == 128) and np.all(rows[:, 7:9] == 9)
    assert np.all(rows[:, -2] == 9)
    positions = rows[:, len(COLUMNS)]
    buffers = rows[:, len(COLUMNS) + 1]
    assert np.all(positions != np.iinfo(np.uint64).max)
    steps = np.diff(positions.astype("i8")).tolist()
    assert steps == [128, 128] and np.all(buffers[1:] != buffers[:-1])
    line, = [line for line in stream.splitlines() if line.startswith("SMT_QUALIFIED\t")]
    _, count, windows = line.split("\t")
    windows = json.loads(windows)
    assert len(windows) == 4 and int(count) >= 4
    assert all(len(row) == 6 and 8500 <= row[0] <= 10000 and 9500 <= row[4] <= 10000 for row in windows)
    assert rows[:, 4].tolist() == [80, 128, 0]
    assert rows[:, 12].tolist() == [0, 0, 6]
    line, = [line for line in stream.splitlines() if line.startswith("ASIO_BANK\t")]
    _, name, original, active, restored, frames, count, notices, errors = line.split("\t")
    assert (name, original, active, restored, frames, count) == (ASIO_DRIVER, "44100", "48000", "44100", "128", "3")
    line, = [line for line in stream.splitlines() if line.startswith("ENGINE128\t")]
    calls, allocations, _, allocated, faults, misses, engine_blocks, _ = map(int, line.split("\t")[1:])
    assert calls == 3 and engine_blocks == misses == 1
    quarantines = [line for line in stream.splitlines() if
                   line.startswith("PLUGIN_PROCESS_QUARANTINED context=rack-slot:rf-d-lab action=silence")]
    assert len(quarantines) == 1
    wall = [int(row[1]) for row in rows]
    assert wall[2] > 128e9 / 48000
    render = int(rows[2, len(COLUMNS) + 2])
    assert 128e9 / 48000 < render <= wall[2]
    return dict(position_steps=steps, buffers=buffers.tolist(),
                wall_ns=wall, voice_render_ns=render, frames=128, sample_rate=48000,
                first_with_setup_ns=wall[0] + int(rows[0, 10]), notices_mask=int(notices),
                asio_errors=int(errors), render_allocations=allocations, allocating_blocks=allocated,
                scheduler_slot_faults=faults, rack_quarantines=len(quarantines), rack_deadline_misses=misses,
                clock_prefix_blocks=2,
                voice_rendered_samples=0, admitted=False)


def campaign(report, exe, env, package, cache, rows_path, execute):
    report["electrical_inputs"] = check_electrical_inputs(report["artifact_sha256"])
    node = shutil.which("node")
    assert node is not None
    output = execute([node, ROOT / NODE, package / "component.wasm"], timeout=240)
    report["node"] = dict(sha256=sha(Path(node)), rows=packed(output.stdout), timings=output.stderr.decode())
    report["node"]["electrical"] = compare_trajectory(output.stdout)
    print("MONO_WASM_ELECTRICAL", report["node"]["electrical"], report["node"]["timings"], flush=True)
    fence = execute([exe, "engine-mono-fence", package, cache], timeout=60)
    report["epoch_fence"] = fence.stderr.decode(errors="replace")
    print("MONO_EPOCH_FENCE", report["epoch_fence"], flush=True)

    bank_env = dict(env, RF_D_ENGINE_ROUTE="mono", RF_D_ENGINE_PACKAGE=str(package),
                    RF_D_ENGINE_CACHE=str(cache), RF_D_SMT_MODE="quiet-event",
                    RF_D_SMT_SUPERVISOR="1", RF_D_SMT_FIXED_CPU="9", RF_D_SMT_FIXED_IDLE="8500")
    for name in ("RF_D_SMT_SEED", "RF_D_SCHED_CPU", "RF_D_SCHED_LOAD"):
        bank_env.pop(name, None)
    profile = asio_profile(exe)
    original = read_override(profile)
    initial = execute([exe, "asio-query", ASIO_DRIVER]).stdout.decode().strip()
    probe = execute([exe, "smt-endpoints", ASIO_DRIVER])
    report["physical_endpoint"] = probe.stdout.decode().strip()
    assert report["physical_endpoint"] == NVIDIA_ENDPOINT
    report["physical_rejections"] = []
    try:
        for _ in range(2):
            rows_path.unlink(missing_ok=True)
            command = [str(exe), "asio-bench", ASIO_DRIVER, "3", "dsp"]
            result = subprocess.run(command, cwd=ROOT, env=bank_env, capture_output=True, timeout=75)
            raw = rows_path.read_bytes() if rows_path.exists() else b""
            stream = result.stderr.decode(errors="replace")
            item = dict(command=command, exit_code=result.returncode, rows=packed(raw),
                        sha256=digest(raw), stream=stream, log=result.stdout.decode(errors="replace"))
            report["physical_rejections"].append(item)
            if raw:
                try:
                    item["metrics"] = parse_timed_rejection(raw, stream)
                except Exception:
                    item["analysis_failure"] = traceback.format_exc()
            print("MONO_ASIO", item.get("metrics", stream), item.get("analysis_failure", ""), flush=True)
        assert all("metrics" in item for item in report["physical_rejections"]), "incomplete physical rejection pair"
    finally:
        during = read_override(profile)
        restore_override(profile, original)
        final = execute([exe, "asio-query", ASIO_DRIVER]).stdout.decode().strip()
        report["asio_profile"] = dict(before=initial, verified=final, original=original, during=during)
        assert final == initial and read_override(profile) == original
