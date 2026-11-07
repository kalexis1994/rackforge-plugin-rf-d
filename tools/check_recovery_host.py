"""Run the fixed Windows host campaign and retain its raw timing rows."""

import os
import re
import subprocess
import sys
import traceback
from pathlib import Path

import numpy as np

from affine_evidence import Sources
from check_hybrid_voice import packed, unpack
from check_recovery_cost import AREA, decode, digest, read
from check_vco_phase import COMPILER, LIB
from prepare_dual_chain import ROOT, sha, write

HOST = ROOT.parent / "rackforge"
HOST_COMPILER = Path(COMPILER).parents[2] / "1.98.0-x86_64-pc-windows-msvc/bin/rustc.exe"
REALTIME = "crates/rackforge-core/src/realtime.rs"
PRIOR = "evidence/recovery_cost_exp_native01.json"
QA = "evidence/recovery_cost_tests01.json"
COLUMNS = [
    "start_ns", "wall_ns", "cycles", "frames", "produced", "dsp_ns", "max128_ns",
    "cpu_before", "cpu_after", "thread_id", "setup_ns", "policy_bits", "dsp_error",
]
CAMPAIGN = [
    ("native", 4800), ("control", 1200), ("dsp", 1200), ("dsp", 4800),
]


def summarize(raw, mode, blocks):
    rows = np.frombuffer(raw, "<u8").reshape(blocks, len(COLUMNS))
    start, wall, cycles, frames, produced, dsp, chunk, cpu1, cpu2, tid, setup, posture, error = rows.T
    assert np.all(start[1:] > start[:-1]) and np.all(wall > 0)
    assert np.all(frames > 0) and np.all(error == 0) and np.all(dsp <= wall)
    assert np.all(cycles != np.iinfo(np.uint64).max)
    assert np.all(setup[1:] == 0)
    assert len(set(tid.tolist())) == 1 and len(set(posture.tolist())) == 1
    if mode == "control":
        assert np.all(produced == 0) and np.all(dsp == 0) and np.all(chunk == 0)
    else:
        cumulative = np.maximum(0, np.cumsum(frames, dtype=np.int64) - 48)
        assert np.array_equal(produced, np.diff(cumulative, prepend=0))
        assert np.all(chunk[frames >= 128] > 0) and np.all(chunk[frames < 128] == 0)
    if mode == "native":
        assert np.all(frames == 128) and posture[0] == 0
    else:
        assert int(posture[0]) & 255 in (1, 2, 3) and int(posture[0]) >> 8 in (1, 2)

    budget = frames.astype(np.float64) * 1e9 / 48000
    ratio = wall / budget
    gap = np.r_[0, np.diff(start)]
    gap_ratio = gap / budget
    deadline = ratio > 1
    margin = ratio > 0.5
    late = gap_ratio > 1.5 if mode != "native" else np.zeros(blocks, dtype=bool)

    def distribution(values):
        return {**{name: float(np.quantile(values, q)) for name, q in (
            ("median", 0.5), ("p99", 0.99), ("p999", 0.999),
        )}, "max": float(max(values))}

    def details(index):
        peer = (frames == frames[index]) & ~margin & (cycles > 0)
        count = int(sum(peer))
        p99 = float(np.quantile(cycles[peer], 0.99)) if count >= 20 else None
        if p99 is None or cycles[index] == 0:
            kind = "insufficient_cycle_peers"
        elif cycles[index] > p99:
            kind = "cycles_above_peer_p99"
        else:
            kind = "cycles_within_peer_p99"
        return dict(
            block=int(index), frames=int(frames[index]), wall_ns=int(wall[index]),
            wall_budget_ratio=float(ratio[index]), cycles=int(cycles[index]),
            peers=count, peer_cycles_p99=p99, comparison=kind,
            gap_ns=int(gap[index]), gap_budget_ratio=float(gap_ratio[index]),
            cpu_before=int(cpu1[index]), cpu_after=int(cpu2[index]),
        )

    miss_counts = {}
    for index in np.flatnonzero(deadline):
        key = details(index)["comparison"]
        miss_counts[key] = miss_counts.get(key, 0) + 1
    sizes, counts = np.unique(frames, return_counts=True)
    return dict(
        blocks=blocks, frames_by_size={str(int(s)): int(c) for s, c in zip(sizes, counts)},
        total_frames=int(sum(frames)), first_frames=int(frames[0]),
        first_produced=int(produced[0]), callback_setup_ns=int(setup[0]),
        scheduling=int(posture[0]) & 255, throttling=int(posture[0]) >> 8,
        wall_ns=distribution(wall), wall_budget_ratio=distribution(ratio),
        cycles=distribution(cycles), zero_cycle_deltas=int(sum(cycles == 0)),
        dsp_ns=distribution(dsp), max128_ns=distribution(chunk[chunk > 0]) if np.any(chunk) else None,
        max128_over_deadline_callbacks=int(sum(chunk > 128e9 / 48000)),
        deadline_misses=int(sum(deadline)), margin_exceeded=int(sum(margin)),
        gap_over_1_5_periods=int(sum(late)), max_gap_ratio=float(max(gap_ratio)) if mode != "native" else None,
        cpu_changed_within_call=int(sum(cpu1 != cpu2)), miss_cycle_comparison=miss_counts,
        worst_processing=[details(i) for i in np.argsort(-ratio, kind="stable")[:8]],
        worst_gaps=[details(i) for i in np.argsort(-gap_ratio, kind="stable")[:8]] if mode != "native" else [],
    )


def calibration(raw):
    values = {kind: [] for kind in ("counter", "wait", "busy")}
    for line in raw.decode().splitlines():
        kind, wall, cycles = line.split(",")
        values[kind].append((int(wall), int(cycles)))
    assert all(len(v) == 12 for v in values.values())
    medians = {key: np.median(rows, axis=0).tolist() for key, rows in values.items()}
    assert medians["busy"][1] > 10 * max(medians["wait"][1], medians["counter"][1], 1)
    assert all(medians[key][0] >= 4e6 for key in ("busy", "wait"))
    return medians


def fixtures(raw):
    values = np.frombuffer(raw, "<f8").reshape(2, 4096 + 464)
    assert np.isfinite(values).all()
    assert values[0].tobytes() == values[1].tobytes()
    prior = np.frombuffer(decode(read(PRIOR), "vectors"), "<f8").reshape(3, 1537, 93)
    assert values[0, :1536].tobytes() == prior[1, :1536, 5].tobytes()
    return dict(prior_samples_bit_exact=1536, partition_input_samples=4096,
                partition_fir_frames_bit_exact=464, startup_output_frames=48)


def run(report, endpoints=(), long_control=False):
    assert not list(AREA.iterdir())
    deps = HOST / "target/release/deps"
    cpal, = deps.glob("libcpal-*.rlib")
    registry = Path(COMPILER).parents[4] / ".cargo/registry/src"
    windows_import, = registry.glob("*/windows_x86_64_msvc-0.52.6/lib/windows.0.52.0.lib")
    cpal_deps = [deps / name for name in (
        "libdasp_sample-2afcd869b85b3c7a.rlib", "libwindows-30e5b7032d286333.rlib",
        "libwindows_core-b43b419d6265e5f1.rlib", "libwindows_result-fd18a7c25a2f3fff.rlib",
        "libwindows_targets-6f7ce55fc1841be5.rlib",
    )]
    previous = read(QA)
    assert sha(Path(COMPILER)) == previous["compiler"]["sha256"]
    assert sha(LIB) == previous["private_input_sha256"][LIB.relative_to(ROOT).as_posix()]
    host_head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=HOST, text=True).strip()
    realtime = (HOST / REALTIME).read_bytes()
    frozen = subprocess.check_output(["git", "show", f"{host_head}:{REALTIME}"], cwd=HOST)
    assert realtime == frozen or realtime == frozen.replace(b"\n", b"\r\n")
    report.update(
        host_commit=host_head, host_source={REALTIME: sha(HOST / REALTIME)},
        input_sha256={str(p): sha(p) for p in [
            Path(COMPILER), LIB, HOST_COMPILER, cpal, windows_import, *cpal_deps,
        ]},
        previous_qa_sha256=sha(ROOT / QA), prior_sha256=sha(ROOT / PRIOR),
    )
    dll = AREA / "recovery-host-dsp.dll"
    exe = AREA / "recovery-host.exe"
    env = dict(os.environ, PATH="C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;" + os.environ["PATH"])
    command = []
    result = None

    def execute(args, timeout=125):
        nonlocal command, result
        command = [str(arg) for arg in args]
        result = None
        result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, timeout=timeout)
        assert result.returncode == 0, result.stderr.decode(errors="replace")
        return result

    try:
        common = ["--edition=2021", "-C", "opt-level=2", "-A", "dead_code", "-A", "unused_imports"]
        report["build"] = []
        for cmd in [
            [COMPILER, *common, "--crate-type", "cdylib", "-C", "strip=symbols",
             ROOT / "tools/recovery_host_dsp.rs", "--extern", f"rf_d_circuit={LIB}", "-o", dll],
            [HOST_COMPILER, *common, "-L", f"dependency={deps}",
             "-L", f"native={windows_import.parent}",
             ROOT / "tools/recovery_host_probe.rs", "--extern", f"cpal={cpal}", "-o", exe],
        ]:
            output = execute(cmd)
            report["build"].append(dict(command=command, stderr=packed(output.stderr)))
        report["binary_sha256"] = {p.name: sha(p) for p in (dll, exe)}
        raw = execute([exe, "calibrate"]).stdout
        report["calibration"] = dict(rows=packed(raw), medians=calibration(raw))
        raw = execute([exe, "fixtures"]).stdout
        report["fixtures"] = dict(rows=packed(raw), sha256=digest(raw), metrics=fixtures(raw))
        print("HOST_FIXTURES", report["fixtures"]["metrics"], flush=True)
        devices = execute([exe, "devices"]).stdout.decode().splitlines()
        available = [line.split("\t", 1)[1] for line in devices]
        names = endpoints or available
        assert all(name in available for name in names)
        report["endpoint_discovery"] = dict(devices=devices, attempts=[])
        endpoint = None
        for name in dict.fromkeys(names):
            args = [str(exe), "control", "16", name]
            opened = subprocess.run(args, cwd=ROOT, env=env, capture_output=True, timeout=125)
            attempt = dict(name=name, exit_code=opened.returncode, rows=packed(opened.stdout),
                           stream=opened.stderr.decode(errors="replace"))
            report["endpoint_discovery"]["attempts"].append(attempt)
            if opened.returncode == 0:
                summarize(opened.stdout, "control", 16)
                endpoint = name
                break
            replay = subprocess.run(args, cwd=ROOT, env=env, capture_output=True, timeout=125)
            attempt["unchanged_replay"] = dict(exit_code=replay.returncode, rows=packed(replay.stdout),
                                               stream=replay.stderr.decode(errors="replace"))
        assert endpoint is not None, "No WASAPI endpoint opened for the fixed request"
        report["endpoint_discovery"]["selected"] = endpoint
        print("HOST_ENDPOINT", endpoint, flush=True)
        report["banks"] = []
        sequence = [("control", 4800)] if long_control else CAMPAIGN[1:] if endpoints else CAMPAIGN
        for mode, blocks in sequence:
            bank = dict(mode=mode, blocks=blocks, runs=[])
            report["banks"].append(bank)
            for attempt in range(2):
                print("HOST_START", mode, blocks, attempt, flush=True)
                output = execute([exe, mode, blocks, *([endpoint] if mode != "native" else [])])
                raw = output.stdout
                metrics = summarize(raw, mode, blocks)
                bank["runs"].append(dict(
                    rows=packed(raw), sha256=digest(raw), metrics=metrics,
                    stream=output.stderr.decode(errors="replace").strip(),
                ))
                print("HOST_BANK", mode, blocks, attempt, metrics["frames_by_size"],
                      metrics["deadline_misses"], metrics["margin_exceeded"],
                      metrics["wall_ns"]["max"], metrics["gap_over_1_5_periods"], flush=True)
                if metrics["margin_exceeded"] == 0:
                    break
        report.update(passed=True, whole_voice_rt=False, cost_admitted=False)
    except Exception:
        report["failure"] = traceback.format_exc()
        if result is not None:
            report["failed_output"] = dict(exit_code=result.returncode, stdout=packed(result.stdout),
                                           stderr=packed(result.stderr), command=command)
        if command:
            replay = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, timeout=125)
            report["unchanged_failure_replay"] = dict(
                exit_code=replay.returncode, stdout=packed(replay.stdout), stderr=packed(replay.stderr),
            )
    finally:
        allowed = {p.name for p in (dll, exe)} | {
            "recovery-host-dsp.dll.a", "recovery-host-dsp.dll.lib", "recovery-host-dsp.lib",
            "recovery-host-dsp.exp", "recovery-host.pdb", "librecovery-host-dsp.dll.a",
        }
        for artifact in AREA.iterdir():
            generated_object = re.fullmatch(r"recovery-host\.[\w.-]+\.rcgu\.o", artifact.name)
            assert (artifact.name in allowed or generated_object) and artifact.resolve().parent == AREA.resolve(), artifact
            artifact.unlink()
    report["temporary_area_empty"] = not list(AREA.iterdir())


if __name__ == "__main__":
    args = sys.argv[1:]
    long_control = bool(args and args[0] == "--long-control")
    endpoints = tuple(args[1:] if long_control else args)
    if long_control:
        assert len(endpoints) == 1, "Select the endpoint of the matched DSP bank"
    sources = Sources([
        "tools/check_recovery_host.py", "tools/recovery_host_probe.rs", "tools/recovery_host_dsp.rs",
        "tools/recovery_cost_exp_kernel.rs", "tools/recovery_cost_exp_data.rs",
        "crates/rf-d-circuit/src/j7_stream_output.rs", "docs/RECOVERY_HOST_PROTOCOLO.md",
        *(["docs/RECOVERY_HOST_CONTROL.md"] if long_control else
          ["docs/RECOVERY_HOST_FISICO.md"] if endpoints else []),
    ])
    report = dict(passed=False, columns=COLUMNS, **sources.fields())
    run(report, endpoints, long_control)
    sources.unchanged()
    number = 1
    while (ROOT / f"evidence/recovery_host_native{number:02d}.json").exists():
        number += 1
    write(ROOT / f"evidence/recovery_host_native{number:02d}.json", report)
    print("HOST_FINAL", report["passed"], report.get("failure", ""), flush=True)
    if not report["passed"]:
        raise SystemExit(1)
