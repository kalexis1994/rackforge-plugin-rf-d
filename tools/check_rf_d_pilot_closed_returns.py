"""Check the bidirectional pilot contours on independent full solver reserves."""
import argparse
import json
import os
import subprocess
import traceback
from pathlib import Path

import numpy as np

from affine_evidence import Sources
import check_rf_d_pilot_contours as c
from check_rf_d_reduced_contour_ports import AUDIO_ROWS, OUTPUT
from rf_d_reduced_contour_live import Diode, Transistor, junction_incidence
from check_rf_d_pilot_split_returns import CONTOURS, inspect_reserve, packed

OWN = "tools/check_rf_d_pilot_closed_returns.py"
MODEL = "tools/rf_d_pilot_closed_returns.rs"
CLOCK = "tools/rf_d_pilot_contour_clock.rs"
REDUCED = "tools/rf_d_pilot_reduced_audio.rs"
MODES = tuple((256, 8, policy, True, True, True) for policy in (0, 3, 4, 5))
POLICIES = {1: "adaptive", 2: "port_clock", 3: "latch_clock",
            4: "collector_clock", 5: "whole_clock"}
CHANNELS = (c.J7, None, None, 5, 38, 3, 37, 54, 55, 26, 28)
BLOCK = 128
BUDGET_NS = BLOCK * 1_000_000_000 // (2 * 48_000)


def radau_devices():
    # Q21 is biased by the same fixed 2 V reference used in the nominal stamp.
    spec = (*OUTPUT, Transistor(2., 35, 36))
    inject, sense, fixed, current = junction_incidence(spec, np.zeros(64))
    with np.errstate(invalid="ignore"):
        rejected = np.flatnonzero(~np.isfinite(current / np.exp(fixed))).tolist()
    assert len(rejected) == 1 and fixed[rejected[0]] < -745.
    saturation = np.array([value for device in spec for value in
                           ((device.saturation_a,) if isinstance(device, Diode) else (1e-14, 1e-14))])
    assert np.array_equal(saturation * np.exp(fixed), current)
    terms = []
    for row, offset in zip(sense, fixed):
        positive = np.flatnonzero(row > 0.)
        negative = np.flatnonzero(row < 0.)
        assert len(positive) <= 1 and len(negative) <= 1
        a = AUDIO_ROWS[positive[0]] if len(positive) else 68
        b = AUDIO_ROWS[negative[0]] if len(negative) else 68
        terms.append(f"({a},{b},{max(abs(row)):.17e},{offset:.17e})")
    n = len(terms)
    arrays = lambda x: "[" + ",".join(f"{v:.17e}" for v in x) + "]"
    path = c.emit("radau-devices.rs", f"pub const S:[(usize,usize,f64,f64);{n}]=[" + ",".join(terms)
                  + f"];\npub const IS:[f64;{n}]=" + arrays(saturation)
                  + f";\npub const D:[[f64;64];{n}]=[" + ",".join(map(arrays, inject.T)) + "];\n")
    return path, rejected


def telemetry(stderr):
    (tag, peak, outer, audio, mismatch, solve, defect, switch, worst, builds, reused,
     trials, reused_substeps, whole, elapsed, fallbacks) = stderr.split(",")
    assert tag == "PORTS"
    return dict(max_frame_ns=int(peak), max_outer_iterations=int(outer),
                max_audio_iterations=int(audio), max_port_mismatch_v=float(mismatch),
                rejections=dict(solve=int(solve), defect=int(defect), switch=int(switch)),
                max_accepted_defect=float(worst),
                interface_factorizations=int(builds), reused_directions=int(reused),
                clock_trials=int(trials), reused_substeps=int(reused_substeps),
                whole_steps=int(whole), compute_ns=int(elapsed),
                nodal_fallbacks=int(fallbacks))


def output_columns(samples):
    return np.column_stack([samples[:, node] if node is not None else
                            (samples[:, 3] - samples[:, 54]) / 68_000. if k == 1 else
                            (samples[:, 55] - samples[:, 37]) / 680.
                            for k, node in enumerate(CHANNELS)])


def validate(raw, reference, info, stride, adaptive):
    full = np.frombuffer(reference, "<f8").reshape(-1, c.N)
    values = np.frombuffer(raw, "<f8")
    if adaptive:
        records = values.reshape(-1, 1 + 2 * len(CHANNELS))
        steps = records[:, 0].astype(int)
        assert np.array_equal(steps, records[:, 0])
        assert np.isin(steps, [1 << k for k in range(9)]).all()
        candidate = records[:, 1:].reshape(len(steps), 2, len(CHANNELS))
    else:
        candidate = values.reshape(-1, 2, len(CHANNELS))
        steps = np.full(len(candidate), stride)
    ticks = np.cumsum(steps)
    assert ticks[-1] == info["frames"] * 512
    assert np.all(np.searchsorted(ticks, np.arange(stride, ticks[-1] + 1, stride)) < len(ticks))
    assert np.all(ticks[np.searchsorted(ticks, np.arange(stride, ticks[-1] + 1, stride))]
                  == np.arange(stride, ticks[-1] + 1, stride))
    # Compare both fine stages or accepted endpoints at the same fine-grid times.
    both_stages = stride == 1 and not adaptive
    samples = full[1:] if both_stages else full[2 * ticks]
    trial = candidate.reshape(-1, len(CHANNELS)) if both_stages else candidate[:, 1, :]
    want = output_columns(samples)
    error = trial - want
    worst = np.max(abs(error), axis=0)
    initial = full[0, 26] >= full[0, 28]
    sign = np.r_[initial, candidate[:, 1, -2] >= candidate[:, 1, -1]]
    base = info["start_frame"] * 4096
    switches = [[base + int(ticks[i] - steps[i]) * 8, base + int(ticks[i]) * 8, int(sign[i + 1])]
                for i in np.flatnonzero(sign[1:] != sign[:-1])]
    weights = np.ones(len(error)) if both_stages else np.sqrt(steps)
    relative = np.linalg.norm(weights * error[:, 0]) / np.linalg.norm(weights * want[:, 0])
    sizes, counts = np.unique(steps, return_counts=True)
    histogram = dict(zip(map(int, sizes), map(int, counts)))
    nearby = None
    if info["expected_events"]:
        crossing = info["expected_events"][0][0] - base
        nearby = int(np.count_nonzero((ticks * 8 >= crossing - 2048)
                                     & ((ticks - steps) * 8 <= crossing + 2048)))
    return dict(passed=bool(np.isfinite(candidate).all() and switches == info["expected_events"]
                            and max(worst[1:3]) <= 2e-9 and max(worst[3:]) <= 20e-6
                            and relative <= .001 and worst[0] <= .003 * max(abs(want[:, 0]))
                            and abs(np.mean(error[:, 0])) <= 1e-6),
                switches=switches, max_error=worst.tolist(), j7_rms_relative=float(relative),
                stride_histogram=histogram, accepted_steps=len(steps), near_crossing_steps=nearby)


def benchmark_blocks(run, exe, anchor, refs, prior, mode, recover):
    result = {}
    # The local positive map begins just before the switch. The continuous
    # negative case includes both keyboard edges in the same callback.
    for name, branch, start, key in (("positive", "positive", 76, 0.),
                                     ("negative", "negative", 0, -1.)):
        grid = refs[branch][1]
        phase, _, _, state = grid[start]
        anchor.write_bytes(packed(np.r_[state.ravel(), phase]))
        item = result[name] = dict(start_frame=start, frames=BLOCK, budget_ns=BUDGET_NS,
                                   anchor_sha256=c.sha(anchor), completed=False, realtime=False, diagnostic_recovery=recover)
        cmd = [exe, "closed-returns", anchor, key, BLOCK, 256, 8, mode, "true", "true", "true", str(recover).lower()]
        trial = run(cmd)
        item.update(exit_code=trial.returncode, output_sha256=c.digest(trial.stdout))
        stderr = trial.stderr.decode(errors="replace").strip()
        if trial.returncode:
            lines = stderr.splitlines()
            tag, frames, elapsed, fallbacks = lines[0].split(",")
            assert tag == "STOP"
            item.update(completed_frames=int(frames), partial_compute_ns=int(elapsed), nodal_fallbacks=int(fallbacks),
                        error="\n".join(lines[1:]))
            replay = run(cmd)
            assert replay.returncode == trial.returncode and replay.stdout == trial.stdout
            assert replay.stderr.decode(errors="replace").strip().splitlines()[1:] == lines[1:]
            item["unchanged_replay"] = True
        else:
            item.update(telemetry(stderr))
            records = np.frombuffer(trial.stdout, "<f8").reshape(-1, 1 + 2 * len(CHANNELS))
            assert np.isfinite(records).all()
            steps = records[:, 0].astype(int)
            assert np.array_equal(steps, records[:, 0])
            ticks = np.cumsum(steps)
            host = 512 * np.arange(1, BLOCK + 1)
            indices = np.searchsorted(ticks, host)
            assert np.array_equal(ticks[indices], host) and ticks[-1] == host[-1]
            endpoints = records[:, -len(CHANNELS):]
            initial = state[:, [26, 28]].sum(axis=0)
            signs = np.r_[initial[0] >= initial[1], endpoints[:, -2] >= endpoints[:, -1]]
            events = [[start * 4096 + int(ticks[i] - steps[i]) * 8,
                       start * 4096 + int(ticks[i]) * 8, int(signs[i + 1])]
                      for i in np.flatnonzero(signs[1:] != signs[:-1])]
            covered = min(BLOCK, len(grid) - 1 - start)
            samples = np.array([grid[start + k][3].sum(axis=0) for k in range(1, covered + 1)])
            expected = list(prior["windows"]["positive_crossing"]["expected_events"]) if name == "positive" else []
            if covered < BLOCK:
                assert name == "positive"
                suffix_start = start + covered
                phase, _, _, state = grid[suffix_start]
                anchor.write_bytes(packed(np.r_[state.ravel(), phase]))
                ref = run([exe, "contour-endpoints", anchor, suffix_start, BLOCK - covered, key])
                assert ref.returncode == 0, ref.stderr.decode(errors="replace")
                suffix = np.frombuffer(ref.stdout, "<f8").reshape(BLOCK - covered + 1, c.N)
                assert np.array_equal(suffix[0], samples[-1])
                samples = np.vstack((samples, suffix[1:]))
                for line in ref.stderr.decode().splitlines():
                    tag, left, right, order = line.split(",")
                    assert tag == "SWITCH"
                    expected.append([int(left), int(right), int(order)])
                item["reference_suffix"] = dict(start_frame=suffix_start, frames=BLOCK - covered,
                                                sha256=c.digest(ref.stdout), anchor_sha256=c.sha(anchor))
            want = output_columns(samples)
            error = endpoints[indices] - want
            worst = np.max(abs(error), axis=0)
            rms = np.linalg.norm(error[:, 0]) / np.linalg.norm(want[:, 0])
            comparison_passed = bool(events == expected and max(worst[1:3]) <= 2e-9
                                     and max(worst[3:]) <= 20e-6 and rms <= .001
                                     and worst[0] <= .003 * max(abs(want[:, 0]))
                                     and abs(np.mean(error[:, 0])) <= 1e-6)
            item.update(completed=True, compared_frames=len(samples), comparison_passed=comparison_passed,
                        max_error=worst.tolist(), j7_rms_relative=float(rms), switches=events,
                        accepted_steps=len(steps), realtime=not recover and comparison_passed and item["compute_ns"] <= BUDGET_NS)
        print("BLOCK", name, item, flush=True)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blocks", action="store_true", help="time uninterrupted 128-frame solver blocks")
    parser.add_argument("--policy", type=int, choices=(3, 4, 5), default=4)
    parser.add_argument("--diagnostic-recovery", action="store_true")
    args = parser.parse_args()
    assert args.blocks or not args.diagnostic_recovery
    assert not list(c.AREA.iterdir())
    seq = 1
    while (out := c.ROOT / f"evidence/rf_d_pilot_closed_returns{seq:02}.json").exists():
        seq += 1
    sources = Sources((*c.ALL_SOURCES, c.OWN, c.CANDIDATE, c.PROBE, c.PORTS, OWN, MODEL, CLOCK, REDUCED,
                       "tools/check_rf_d_reduced_contour_ports.py", "tools/rf_d_reduced_contour_live.py",
                       "tools/check_rf_d_pilot_split_returns.py", CONTOURS))
    report = dict(passed=False, rack_integrated=False, source_boundary="loaded x2/x4",
                  windows={}, **sources.fields(), compiler_sha256=c.sha(Path(c.COMPILER)),
                  library_sha256=c.sha(c.LIB))
    env = dict(os.environ, PATH="C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;" + os.environ["PATH"])

    def run(args):
        return subprocess.run(list(map(str, args)), cwd=c.ROOT, env=env, capture_output=True, timeout=240)

    try:
        prior = json.loads((c.ROOT / CONTOURS).read_text(encoding="utf8"))
        refs, report["reference_inputs"] = c.references()
        table, *_ = c.materialize(c.read_oracle())
        assert c.digest(table) == c.read(c.MODEL)["table_sha256"]
        table_path = c.AREA / c.TABLE
        table_path.write_bytes(table)
        kernel = c.emit("family-kernel.rs", c.text(c.KERNEL)
                        .replace("H128_VOICE_TABLE_PATH", table_path.as_posix())
                        .replace("VCO_PANEL_PORT_PATH", (c.ROOT / c.PANEL).as_posix()))
        probe = c.component(kernel)
        code = c.once(probe.read_text(encoding="utf8"), '        Some("ports") => ports(),', '''
        Some("ports") => ports(),
        Some("contour-endpoints") if args.len() == 6 =>
            contour_probe::capture_endpoints(&args[2], args[3].parse()?, args[4].parse()?, args[5].parse()?),
        Some("closed-returns") if args.len() == 12 =>
            closed_returns::run(&args[2], args[3].parse()?, args[4].parse()?, args[5].parse()?, args[6].parse()?, args[7].parse()?, args[8].parse()?, args[9].parse()?, args[10].parse()?, args[11].parse()?),''')
        code += f'\n#[path = "{(c.ROOT / MODEL).as_posix()}"] mod closed_returns;\n'
        devices, report["unit_bias_underflow_columns"] = radau_devices()
        report["devices_sha256"] = c.sha(devices)
        code += f'\n#[path = "{devices.as_posix()}"] mod radau_devices;\n'
        probe = c.emit(probe.name, code)
        exe = c.AREA / "pilot-closed-returns.exe"
        built = run([c.COMPILER, "--edition=2021", "-C", "opt-level=3", "-C", "target-feature=+fma",
                     "-C", "link-arg=-Wl,--stack,33554432", "--cfg", "laboratory", "--cfg", "pilot_loaded_filter", "--cfg", "pilot_closed_cv",
                     "-A", "dead_code", probe, "--extern", f"rf_d_circuit={c.LIB}", "-o", exe])
        assert built.returncode == 0, built.stderr.decode(errors="replace")
        anchor = c.AREA / "closed-returns.anchor"
        if args.blocks:
            report["blocks"] = benchmark_blocks(run, exe, anchor, refs, prior, args.policy, args.diagnostic_recovery)
            report["passed"] = all(item.get("comparison_passed", False)
                                   for item in report["blocks"].values())
        else:
            for label, branch, start, frames, key in c.WINDOWS:
                phase, _, _, state = refs[branch][1][start]
                anchor.write_bytes(packed(np.r_[state.ravel(), phase]))
                info = prior["windows"][label]
                assert c.sha(anchor) == info["anchor_sha256"]
                ref = run([exe, "contour-capture", anchor, start, frames, key])
                assert ref.returncode == 0, ref.stderr.decode(errors="replace")
                entry = report["windows"][label] = dict(reference=inspect_reserve(ref.stdout, info), modes={})
                for stride, budget, policy, reduced, reuse, warm in MODES:
                    adaptive = policy != 0
                    cmd = [exe, "closed-returns", anchor, key, frames, stride, budget, policy, str(reduced).lower(), str(reuse).lower(), str(warm).lower(), "false"]
                    trial = run(cmd)
                    stderr = trial.stderr.decode(errors="replace").strip()
                    result = dict(exit_code=trial.returncode, output_sha256=c.digest(trial.stdout), passed=False)
                    mode = POLICIES[policy] if adaptive else f"{stride}_{budget}"
                    if reduced:
                        mode = 'reduced_' + mode
                    if reuse:
                        mode = 'reuse_' + mode
                    if warm:
                        mode = 'warm_' + mode
                    entry["modes"][mode] = result
                    if trial.returncode == 0:
                        result.update(validate(trial.stdout, ref.stdout, info, stride, adaptive))
                        result.update(telemetry(stderr))
                    else:
                        result["error"] = stderr
                    if adaptive or not result["passed"]:
                        replay = run(cmd)
                        assert trial.returncode == replay.returncode and trial.stdout == replay.stdout
                        assert trial.returncode == 0 or trial.stderr == replay.stderr
                        result["unchanged_replay"] = True
                    print(label, mode, result, flush=True)
            report["passed"] = all(entry["modes"]["warm_reuse_reduced_latch_clock"]["passed"] and entry["modes"]["warm_reuse_reduced_collector_clock"]["passed"]
                                   for entry in report["windows"].values())
        sources.unchanged()
    except Exception:
        report["failure"] = traceback.format_exc()
        raise
    finally:
        c.write(out, report)
        for path in c.AREA.iterdir():
            assert path.is_file() and path.resolve().parent == c.AREA.resolve()
            path.unlink()
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
