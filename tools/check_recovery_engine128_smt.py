"""Control and confirm affinity driven by idle cycles of SMT siblings."""

import ast
import json
import subprocess
import time
import traceback

import numpy as np

from check_hybrid_voice import packed
from check_recovery_cost import digest, read
from check_recovery_engine128_schedule import analyze_markers, distribution, placements, topology
from check_recovery_host import COLUMNS
from check_recovery_host128 import ASIO_DRIVER, asio_profile, read_override, restore_override
from prepare_dual_chain import ROOT, sha

REFERENCE = "evidence/recovery_engine128_schedule05.json"
RESERVE = "evidence/recovery_engine128_reserve08.json"
FIR = "evidence/recovery_engine128_broadcast_fir08.json"
O3_INPUTS = (
    "evidence/recovery_engine128_schedule04.json",
    "evidence/recovery_engine128_reserve07.json",
    "evidence/recovery_engine128_broadcast_fir07.json",
)
PROTOCOL = "docs/RECOVERY_ENGINE128_SMT_PROTOCOLO.md"
SEED = 8
ARTIFACTS = ("engine_kernel_columns.rs", "engine_guest.rs", "package-dsp/component.wasm",
             "package-control/component.wasm")
ENDPOINT = "ASIO_CHANNELS\tHD Audio output 1\tHD Audio output 2\t4\t4"
NVIDIA_ENDPOINT = "ASIO_CHANNELS\tHigh Definition Audio 1\tHigh Definition Audio 2\t4\t4"


def analyze_smt(raw, stream, blocks, policy, seed, top, analyze_asio, silent=False, endpoint=ENDPOINT):
    rows = np.frombuffer(raw, "<u8").reshape(blocks, len(COLUMNS) + 8)
    base = rows[:, :-2]
    metrics = analyze_markers(base.tobytes(), stream, blocks, "control" if silent or not policy else "rack",
                              None, None, analyze_asio)
    metrics["physical_endpoint_verified"] = endpoint in stream.splitlines()
    cpus, elapsed = rows[:, -2:].T
    if not policy:
        assert np.all(cpus == np.iinfo(np.uint64).max) and np.all(elapsed == 0)
        metrics["timing_gate_passed"] = metrics["gate_passed"]
        metrics["gate_passed"] &= metrics["physical_endpoint_verified"]
        return metrics
    line, = [line for line in stream.splitlines() if line.startswith("SMT_BANK\t")]
    _, adaptive, initial, load_at, load_batches, samples, informative, startup = line.split("\t")
    initial, load_at, load_batches, samples, informative = map(int, (initial, load_at, load_batches, samples, informative))
    startup = [list(row) for row in ast.literal_eval(startup)]
    assert [row[0] for row in startup] == placements(top)
    startup_pick = max(startup, key=lambda row: (min(row[1:]), -row[0]))[0]
    qualification = None
    if policy in ("qualified", "quiet-hold"):
        line, = [line for line in stream.splitlines() if line.startswith("SMT_QUALIFIED\t")]
        _, count, windows = line.split("\t")
        windows = json.loads(windows)
        cpus_in_order = placements(top)
        assert len(windows) == 4 and int(count) >= 4
        minimum_system = 8500 if policy == "quiet-hold" else 7000
        assert all(len(window) == len(cpus_in_order) + 1
                   and minimum_system <= window[0] <= 10000 for window in windows)
        scores = [(min(window[i + 1] for window in windows), -cpu) for i, cpu in enumerate(cpus_in_order)]
        score, negative_cpu = max(scores)
        assert score >= 9000 and initial == -negative_cpu and seed is None
        qualification = dict(windows=windows, total_windows=int(count), winning_score=score)
    else:
        assert initial == (startup_pick if seed is None else seed)
    assert cpus[0] == initial
    assert bool(int(adaptive)) == (policy in ("adaptive", "background"))
    if policy == "quiet-hold":
        assert informative == samples == 0 and metrics["cpu_deltas_ns"] == [0]
        metrics["cpu_deltas_ns"] = []
    else:
        assert 0 < informative <= samples
    assert (load_at == load_batches == 0) if seed is None else (load_at >= 128 and load_batches > 0)
    events = [json.loads(line.split("\t", 1)[1]) for line in stream.splitlines() if line.startswith("SMT_EVENT\t")]
    assert all(row[3] * 4 < row[5] * 3 <= row[4] * 4 for row in events)
    assert all(b[0] - a[0] >= 24 and a[2] == b[1] for a, b in zip(events, events[1:]))
    if events:
        assert events[0][1] == initial and policy in ("adaptive", "background")
    transitions = np.r_[True, cpus[1:] != cpus[:-1]]
    out_of_band = [json.loads(line.split("\t", 1)[1]) for line in stream.splitlines()
                   if line.startswith("SMT_BACKGROUND\t")]
    observers = [int(line.split("\t")[1]) for line in stream.splitlines() if line.startswith("SMT_OBSERVER\t")]
    assert len(observers) <= 1 and all(cpu == (top["cores"][0] & -top["cores"][0]).bit_length() - 1 for cpu in observers)
    if policy == "background":
        assert observers and len(out_of_band) == len(events)
        assert [row[0] for row in out_of_band] == [row[0] for row in events]
        assert all(end <= 500000 and slack >= 900000 and cost > 0 for _, end, slack, cost in out_of_band)
        assert elapsed[0] > 0 and np.count_nonzero(elapsed) == 1
    else:
        assert not out_of_band and np.array_equal(transitions, elapsed > 0)
    observed_changes = [[int(i), int(cpus[i])] for i in np.flatnonzero(transitions)]
    assert [row[1] for row in observed_changes[1:]] == [row[2] for row in events[:len(observed_changes) - 1]]
    assert len(events) - len(observed_changes) + 1 in (0, 1)
    verified = bool(np.all(base[:, 7:9] == cpus[:, None]))
    metrics["gate_passed"] &= verified
    metrics["timing_gate_passed"] = metrics["gate_passed"]
    metrics["gate_passed"] &= metrics["physical_endpoint_verified"]
    metrics.update(initial_cpu=initial, preflight=startup, preflight_cpu=startup_pick, samples=samples,
                   informative_samples=informative, placement_verified=verified, load_at=load_at,
                   load_batches=load_batches, requests=events, observed_changes=observed_changes,
                   affinity_ns=distribution(elapsed[elapsed > 0]), background_calls=out_of_band,
                   observer_cpu=observers[0] if observers else None)
    if seed is not None:
        settled = rows[load_at + 64:]
        assert len(settled) >= blocks // 2
        metrics.update(settled_wall_ns=distribution(settled[:, 1]),
                       settled_margin_exceeded=int(sum(settled[:, 1] > 128e9 / 48000 / 2)),
                       settled_blocks=len(settled))
    if qualification:
        assert observers and len(observed_changes) == 1
        metrics["qualification"] = qualification
    return metrics


def admitted(control, runs):
    return (control.get("metrics", {}).get("gate_passed", False)
            and len(runs) == 2 and all(item.get("metrics", {}).get("gate_passed", False) for item in runs))


def campaign(report, exe, env, dsp_package, silent_package, cache, rows_path, analyze_asio, execute,
             background=False, qualified=False, lean=False, endpoint=ENDPOINT):
    if endpoint != ENDPOINT:
        report["expected_endpoint"] = endpoint
    inputs = O3_INPUTS if lean and report["wasm_opt_level"] == 3 else (REFERENCE, RESERVE, FIR)
    reference = read(inputs[0])
    for name in ARTIFACTS:
        assert report["artifact_sha256"][name] == reference["artifact_sha256"][name], name
    assert report["fixtures"]["sha256"] == reference["fixtures"]["sha256"]
    report["reference_inputs"] = {path: sha(ROOT / path) for path in inputs}
    top = topology(execute([exe, "schedule-topology"]).stdout.decode())
    assert SEED in placements(top)
    report["topology"] = top
    report["background_campaign"] = background
    report["qualification_campaign"] = qualified
    report["lean_campaign"] = lean

    def capture(label, blocks, policy=None, seed=None):
        rows_path.unlink(missing_ok=True)
        bank_env = dict(env, RF_D_ENGINE_ROUTE="control" if label == "control" else "rack",
                        RF_D_ENGINE_PACKAGE=str(silent_package if label == "control" else dsp_package),
                        RF_D_ENGINE_CACHE=str(cache))
        for variable in ("RF_D_SMT_MODE", "RF_D_SMT_SEED", "RF_D_SMT_SUPERVISOR", "RF_D_SCHED_CPU", "RF_D_SCHED_LOAD"):
            bank_env.pop(variable, None)
        if policy is not None:
            bank_env["RF_D_SMT_MODE"] = policy
            if background or qualified:
                bank_env["RF_D_SMT_SUPERVISOR"] = "1"
        if seed is not None:
            bank_env["RF_D_SMT_SEED"] = str(seed)
        args = [str(exe), "asio-bench", ASIO_DRIVER, str(blocks), "dsp"]
        try:
            result = subprocess.run(args, cwd=ROOT, env=bank_env, capture_output=True, timeout=75 if qualified else 45)
            stdout, stderr, code = result.stdout, result.stderr, result.returncode
        except subprocess.TimeoutExpired as error:
            stdout, stderr, code = error.stdout or b"", error.stderr or b"", None
        raw = rows_path.read_bytes() if rows_path.exists() else b""
        stream = stderr.decode(errors="replace")
        item = dict(label=label, policy=policy, seed=seed, blocks=blocks, exit_code=code,
                    rows=packed(raw), sha256=digest(raw), stream=stream, log=stdout.decode(errors="replace"))
        if code == 0:
            try:
                item["metrics"] = analyze_smt(raw, stream, blocks, policy, seed, top, analyze_asio,
                                              silent=label == "control", endpoint=endpoint)
            except Exception:
                item["analysis_failure"] = traceback.format_exc()
        m = item.get("metrics", {})
        print("SMT128_BANK", label, code, {k: m.get(k) for k in
              ("frames_128_confirmed", "placement_verified", "initial_cpu", "observed_changes", "affinity_ns",
               "wall_ns", "settled_wall_ns", "margin_exceeded", "deadline_misses", "gate_passed")},
              item.get("analysis_failure", ""), flush=True)
        return item

    profile = asio_profile(exe)
    original = read_override(profile)
    initial = execute([exe, "asio-query", ASIO_DRIVER]).stdout.decode().strip()
    try:
        report["endpoint_checks"] = []
        for attempt in range(6):
            probe = subprocess.run([str(exe), "smt-endpoints", ASIO_DRIVER], cwd=ROOT, env=env,
                                   capture_output=True, timeout=10)
            found = probe.stdout.decode(errors="replace").strip()
            report["endpoint_checks"].append(dict(exit_code=probe.returncode, endpoint=found,
                                                  stderr=probe.stderr.decode(errors="replace")))
            if probe.returncode == 0 and found == endpoint:
                break
            if attempt < 5:
                time.sleep(5)
        report["endpoint_available"] = probe.returncode == 0 and found == endpoint
        if not report["endpoint_available"]:
            report["admitted_policy"] = None
            print("SMT128_ENDPOINT_UNAVAILABLE", report["endpoint_checks"], flush=True)
            return
        fixed = "quiet-hold" if lean else "qualified"
        report["control"] = capture("control", 1200, fixed if qualified else None)
        if qualified:
            runs = [capture("confirmation-" + fixed, 4800, fixed) for _ in range(2)]
            report["confirmations"] = [dict(policy=fixed, runs=runs)]
            report["admitted_policy"] = fixed if admitted(report["control"], runs) else None
            return
        report["pressure"] = []
        adaptive = "background" if background else "adaptive"
        for policy in ("hold", adaptive):
            item = capture("pressure-" + policy, 1200, policy, SEED)
            report["pressure"].append(item)
            if "metrics" not in item:
                item["unchanged_replay"] = capture("pressure-" + policy, 1200, policy, SEED)
                raise AssertionError("Pressure bank did not return usable timing rows")
        report["confirmations"] = []
        report["admitted_policy"] = None
        for policy in (adaptive, "hold"):
            runs = [capture("confirmation-" + policy, 4800, policy) for _ in range(2)]
            report["confirmations"].append(dict(policy=policy, runs=runs))
            if admitted(report["control"], runs):
                report["admitted_policy"] = policy
                break
    finally:
        during = read_override(profile)
        restore_override(profile, original)
        final = execute([exe, "asio-query", ASIO_DRIVER]).stdout.decode().strip()
        report["asio_profile"] = dict(before=initial, verified=final, original=original, during=during)
        assert initial == final and read_override(profile) == original
