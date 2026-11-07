"""Compare the same RackEngine under a timer, SMT load and ASIO."""

import json
import subprocess
import traceback

import numpy as np

from check_hybrid_voice import packed, unpack
from check_recovery_cost import digest, read
from check_recovery_host import COLUMNS, summarize
from check_recovery_host128 import ASIO_DRIVER, asio_profile, read_override, restore_override
from prepare_dual_chain import ROOT, sha

REFERENCE = "evidence/recovery_engine128_native15.json"
SELECTED = "evidence/recovery_engine128_schedule04.json"
RESERVE_O2 = "evidence/recovery_engine128_reserve08.json"
FIR_O2 = "evidence/recovery_engine128_broadcast_fir08.json"
PROTOCOL = "docs/RECOVERY_ENGINE128_SCHED_PROTOCOLO.md"
OFFLINE = ("quiet", "sibling", "remote", "remote", "sibling", "quiet")
ASIO = ("control", "free", "pinned", "pinned", "free")
INVALID = np.iinfo(np.uint64).max


def distribution(values):
    return dict(median=float(np.median(values)), p99=float(np.quantile(values, .99)), max=int(max(values)))


def calibration(raw):
    rows = np.frombuffer(raw, "<u8").reshape(2, 128, 3)
    assert np.all(rows != INVALID) and np.all(rows[:, :, 0] >= 800000)
    busy, wait = rows
    assert np.median(busy[:, 1]) > 10 * np.median(wait[:, 1])
    # A usable per-callback clock needs to see the known busy intervals.
    useful = (np.count_nonzero(busy[:, 2] == 0) == 0
              and np.quantile(abs(busy[:, 2].astype("i8") - busy[:, 0].astype("i8")), .95) < 200000)
    return dict(cpu_clock_useful=bool(useful), busy_zero_cpu=int(sum(busy[:, 2] == 0)),
                busy_wall_ns=distribution(busy[:, 0]), busy_cycles=distribution(busy[:, 1]),
                wait_wall_ns=distribution(wait[:, 0]), wait_cycles=distribution(wait[:, 1]),
                observed_cpu_deltas_ns=[int(value) for value in np.unique(rows[:, :, 2])])


def topology(line):
    tag, allowed, cores = line.strip().split("\t")
    allowed, cores = int(allowed), json.loads(cores)
    assert tag == "SCHED_TOPOLOGY" and len(cores) >= 4
    assert all(mask & allowed == mask for mask in cores) and cores == sorted(cores)
    assert sum(cores) == allowed and all(a & b == 0 for i, a in enumerate(cores) for b in cores[i + 1:])
    logical = lambda mask: [i for i in range(mask.bit_length()) if mask & (1 << i)]
    eligible = [mask for mask in cores if mask.bit_count() >= 2]
    assert len(eligible) >= 3
    cpu, sibling, *_ = logical(eligible[2])
    remote = logical(next(mask for mask in cores if mask > eligible[2]))[0]
    return dict(allowed=allowed, cores=cores, cpu=cpu, sibling=sibling, remote=remote)


def placements(top):
    return [(mask & -mask).bit_length() - 1 for mask in top["cores"][1:] if mask.bit_count() >= 2]


def select_placement(survey):
    eligible = [item for item in survey if item.get("metrics", {}).get("frames_128_confirmed")
                and item["metrics"]["pinned_verified"]]
    if not eligible:
        return None
    chosen = min(eligible, key=lambda item: (
        not item["metrics"]["gate_passed"], item["metrics"]["margin_exceeded"],
        item["metrics"]["wall_ns"]["max"], item["cpu"],
    ))
    return chosen["cpu"]


def analyze_markers(raw, stream, blocks, mode, cpu, helper, analyze_asio):
    rows = np.frombuffer(raw, "<u8").reshape(blocks, len(COLUMNS) + 6)
    base, extra = rows[:, :len(COLUMNS)], rows[:, -4:]
    assert np.all(extra != INVALID) and np.all(extra[:, 1] > 0)
    wall, cycles = base[:, 1], base[:, 2]
    assert np.all(base[:, 5] <= extra[:, 0])
    if mode in OFFLINE:
        m = summarize(base.tobytes(), "dsp", blocks)
        line, = [line for line in stream.splitlines() if line.startswith("SCHED_OFFLINE\t")]
        observed_blocks, observed_cpu, observed_helper, batches = map(int, line.split("\t")[1:])
        assert (observed_blocks, observed_cpu, observed_helper) == (blocks, cpu, -1 if helper is None else helper)
        assert (batches > 0) == (helper is not None)
        assert np.all(wall <= extra[:, 0])
        m.update(helper_batches=batches, frames_128_confirmed=False)
    else:
        m = analyze_asio(rows[:, :-4].tobytes(), stream, blocks, "control" if mode == "control" else "rack")
        assert np.all(extra[:, 0] <= wall) and np.all(extra[:, 1] <= cycles)
        m["outside_render_ns"] = distribution(wall - extra[:, 0])
        worst = int(np.argmax(wall))
        m["worst_split"] = dict(block=worst, wall_ns=int(wall[worst]), render_ns=int(extra[worst, 0]),
                                cycles=int(cycles[worst]), render_cycles=int(extra[worst, 1]))
    m.update(render_window_ns=distribution(extra[:, 0]), render_cycles=distribution(extra[:, 1]),
             cpu_deltas_ns=[int(x) for x in np.unique(extra[:, 2:])],
             pinned_verified=cpu is not None and bool(np.all(base[:, 7:9] == cpu)),
             observed_cpus=[int(x) for x in np.unique(base[:, 7:9])])
    if cpu is not None:
        m["gate_passed"] = m.get("gate_passed", False) and m["pinned_verified"]
    if mode in OFFLINE:
        line, = [line for line in stream.splitlines() if line.startswith("ENGINE128\t")]
        calls, allocations, first, allocated, faults, _, telemetry, _ = map(int, line.split("\t")[1:])
        assert calls == telemetry == blocks and allocations == first == allocated == faults == 0
    return m


def wpr_probe():
    args = ["wpr", "-start", "CPU"]
    state = subprocess.check_output(["wpr", "-status"], cwd=ROOT).decode(errors="replace")
    if "WPR is not recording" not in state:
        return dict(skipped=True, state=state)
    runs = []
    for _ in range(2):
        p = subprocess.run(args, cwd=ROOT, capture_output=True, timeout=20)
        runs.append(dict(exit_code=p.returncode, stdout=packed(p.stdout), stderr=packed(p.stderr)))
        if p.returncode == 0:
            subprocess.run(["wpr", "-cancel"], cwd=ROOT, capture_output=True, timeout=20, check=True)
            break
    return dict(command=args, runs=runs,
                final=subprocess.check_output(["wpr", "-status"], cwd=ROOT).decode(errors="replace"))


def campaign(report, exe, env, dsp_package, silent_package, cache, rows_path, analyze_asio, execute,
             survey=False, confirm_cpu=None):
    reference = read(REFERENCE)
    identity = ("engine_kernel_columns.rs", "engine_guest.rs")
    if confirm_cpu is None:
        identity += ("package-dsp/component.wasm", "package-control/component.wasm")
    for name in identity:
        assert report["artifact_sha256"][name] == reference["artifact_sha256"][name], name
    assert report["fixtures"]["sha256"] == reference["fixtures"]["sha256"]
    report["reference_sha256"] = sha(ROOT / REFERENCE)
    if confirm_cpu is not None:
        selected, reserve, fir = [read(path) for path in (SELECTED, RESERVE_O2, FIR_O2)]
        assert selected["selected_cpu"] == confirm_cpu and not selected["selected_128_admitted"]
        assert reserve["passed"] and fir["passed"] and reserve["wasm_lto"] and fir["wasm_lto"]
        assert reserve["wasm_opt_level"] == fir["wasm_opt_level"] == report["wasm_opt_level"] == 2
        kernel = report["artifact_sha256"]["engine_kernel_columns.rs"]
        assert kernel == reserve["variants"]["registers"]["kernel_sha256"] == fir["kernel_sha256"]
        assert reserve["variants"]["registers"]["modes"] == reserve["variants"]["scalar"]["modes"]
        assert unpack(fir["fir_check"]).strip() == b"FIR_EXACT,9288,4,48"
        report["placement_inputs"] = {path: sha(ROOT / path) for path in (SELECTED, RESERVE_O2, FIR_O2)}
    if not survey and confirm_cpu is None:
        report["wpr"] = wpr_probe()
    top = topology(execute([exe, "schedule-topology"]).stdout.decode())
    report["topology"] = top
    print("SCHED_TOPOLOGY", top, flush=True)
    rows_path.unlink(missing_ok=True)
    execute([exe, "schedule-calibration"])
    raw = rows_path.read_bytes()
    report["calibration"] = dict(raw=packed(raw), metrics=calibration(raw))
    print("SCHED_CALIBRATION", report["calibration"]["metrics"], flush=True)

    def capture(mode, blocks, cpu=None, helper=None, offline=False):
        rows_path.unlink(missing_ok=True)
        bank_env = dict(env, RF_D_ENGINE_ROUTE="control" if mode == "control" else "rack",
                        RF_D_ENGINE_PACKAGE=str(silent_package if mode == "control" else dsp_package),
                        RF_D_ENGINE_CACHE=str(cache))
        for variable, value in (("RF_D_SCHED_CPU", cpu), ("RF_D_SCHED_LOAD", helper)):
            bank_env.pop(variable, None)
            if value is not None:
                bank_env[variable] = str(value)
        command = ([str(exe), "schedule-offline", str(blocks)] if offline else
                   [str(exe), "asio-bench", ASIO_DRIVER, str(blocks), "dsp"])
        try:
            measured = subprocess.run(command, cwd=ROOT, env=bank_env, capture_output=True, timeout=45)
            stdout, stderr, code = measured.stdout, measured.stderr, measured.returncode
        except subprocess.TimeoutExpired as error:
            stdout, stderr, code = error.stdout or b"", error.stderr or b"", None
        stream = stderr.decode(errors="replace")
        raw = rows_path.read_bytes() if rows_path.exists() else b""
        item = dict(mode=mode, blocks=blocks, cpu=cpu, helper=helper, exit_code=code, rows=packed(raw),
                    sha256=digest(raw), stream=stream, log=stdout.decode(errors="replace"))
        if code == 0:
            try:
                item["metrics"] = analyze_markers(raw, stream, blocks, mode, cpu, helper, analyze_asio)
            except Exception:
                item["analysis_failure"] = traceback.format_exc()
        m = item.get("metrics", {})
        print("SCHED_BANK", mode, blocks, code, {k: m.get(k) for k in
              ("frames_128_confirmed", "pinned_verified", "observed_cpus", "deadline_misses",
               "margin_exceeded", "render_window_ns", "render_cycles", "wall_ns", "host_allocations", "notices")},
              item.get("analysis_failure", ""), flush=True)
        return item

    if not survey and confirm_cpu is None:
        report["offline"] = []
        for mode in OFFLINE:
            item = capture(mode, 1200, top["cpu"], top.get(mode), offline=True)
            report["offline"].append(item)
            if not item.get("metrics", {}).get("pinned_verified", False):
                report["unchanged_pin_replay"] = capture(mode, 1200, top["cpu"], top.get(mode), offline=True)
                raise AssertionError("Offline capture did not confirm its requested CPU")
    profile = asio_profile(exe)
    original = read_override(profile)
    initial = execute([exe, "asio-query", ASIO_DRIVER]).stdout.decode().strip()
    report["asio"] = []
    try:
        modes = ("control",) if survey or confirm_cpu is not None else ASIO
        for mode in modes:
            report["asio"].append(capture(mode, 1200 if mode == "control" else 4800,
                                          top["cpu"] if mode == "pinned" else None))
        if survey:
            report["survey"] = [capture("survey", 1200, cpu) for cpu in placements(top)]
            cpu = select_placement(report["survey"])
            report["selected_cpu"] = cpu
            print("SCHED_SELECTED", cpu, flush=True)
            if cpu is not None:
                for _ in range(2):
                    report["asio"].append(capture("selected", 4800, cpu))
        if confirm_cpu is not None:
            assert confirm_cpu in placements(top)
            report["selected_cpu"] = confirm_cpu
            for _ in range(2):
                report["asio"].append(capture("selected", 4800, confirm_cpu))
    finally:
        during = read_override(profile)
        restore_override(profile, original)
        final = execute([exe, "asio-query", ASIO_DRIVER]).stdout.decode().strip()
        report["asio_profile"] = dict(before=initial, verified=final, original=original, during=during)
        assert initial == final and read_override(profile) == original
    control = report["asio"][0].get("metrics", {}).get("gate_passed", False)
    if survey or confirm_cpu is not None:
        report["selected_128_admitted"] = control and len(report["asio"]) == 3 and all(
            item.get("metrics", {}).get("gate_passed", False) for item in report["asio"][1:]
        )
        return
    for mode in ("free", "pinned"):
        report[mode + "_128_admitted"] = control and all(item.get("metrics", {}).get("gate_passed", False)
                                                          for item in report["asio"] if item["mode"] == mode)
