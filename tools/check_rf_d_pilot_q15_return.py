"""Exercise the Q15/CR6 port with continuous charge from one DC seed."""
import argparse
import os
import subprocess
import traceback
from pathlib import Path

import numpy as np

from affine_evidence import Sources
from check_hybrid_voice import packed
from check_recovery_cost import digest
from check_vco_phase import COMPILER, LIB
from prepare_dual_chain import ROOT, sha, write

AREA = ROOT / "tmp/lab-current"
PROBE = "tools/rf_d_pilot_q15_return_probe.rs"
SOURCES = ("tools/check_rf_d_pilot_q15_return.py", PROBE, "tools/rf_d_pilot_q15_return.rs",
           "tools/rf_d_pilot_contour_ports.rs", "tools/latch_charge_driver.rs",
           "tools/rf_d_reduced_engine_lu.rs", "crates/rf-d-circuit/src/prepared_volume_residual.rs",
           "crates/rf-d-circuit/src/junction_charge.rs")
HOST_RATE = 48_000
FRAMES = 128
RATE = 96_000
NAMES = ("reverse", "forward", "both_polarities")
NODES = ("x27", "x28", "x0", "x1", "x3", "x2", "x4", "cr6_a", "r59_a", "delta_q27_c", "delta_q28_c")


def drive(name, t):
    """Smooth imposed ports. Q15 and the loaded follower are solved together."""
    w = 2. * np.pi * t * HOST_RATE / FRAMES
    if name == "reverse":
        c2 = 3.12 + .18 * np.sin(w)
        vca = .70 + .06 * np.cos(w)
    elif name == "forward":
        c2 = 9.15 + .13 * np.sin(w)
        vca = 4.31 + .04 * np.cos(w)
    else:
        c2 = 6.08 - 1.26 * np.cos(w)
        vca = 2.55 + .21 * np.sin(w)
    return np.stack((c2, vca, .63 + .045 * np.sin(w),
                     .32 + .07 * np.sin(w + .35), .22 + .04 * np.cos(w)), axis=-1)


def fixture(name, rate):
    initial = drive(name, 0.)
    c2 = initial[0]
    x3 = c2 - 1.15
    cv = (x3 - 10. * 6800. / 16_900.) / (1. + 6800. / 16_900.)
    forward = name == "forward"
    seed = [.75 if forward else .33, .08 if forward else 4.9,
            c2 - .06, c2 - .61, x3, 8.75 if forward else 9.0,
            .9 if forward else cv]
    t = np.arange(FRAMES * rate // HOST_RATE)
    stages = drive(name, (t[:, None] + [1. / 3., 1.]) / rate)
    return np.r_[seed, initial, stages.ravel()].astype("<f8").tobytes()


def contrast(candidate, reference, charge_gate=False):
    assert candidate.shape == reference.shape
    error = abs(candidate - reference).max(axis=0)
    passed = max(error[:7]) <= 20e-6 and max(error[7:9]) <= 2e-9
    if charge_gate:
        passed &= max(error[9:]) <= 2e-20
    return dict(passed=bool(passed), maximum=dict(zip(NODES, error.tolist(), strict=True)))


def switches(rows, name, rate):
    t = np.arange(len(rows)) / rate
    sign = rows[:, 1] <= drive(name, t)[:, 3]
    return np.flatnonzero(sign[1:] != sign[:-1]).tolist()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mixed-refined", action="store_true",
                        help="close the mixed-polarity trajectory at a finer laboratory clock")
    parser.add_argument("--mixed-rate", type=int, choices=(3_072_000, 6_144_000),
                        default=3_072_000, help="candidate clock for the refined laboratory trajectory")
    parser.add_argument("--port-audit", action="store_true",
                        help="compare all Schur, charge and mass entries against the full stamp")
    args = parser.parse_args()
    assert not (args.port_audit and args.mixed_refined)
    clock = args.mixed_rate if args.mixed_refined else RATE
    low, high = (2 * clock, 4 * clock) if args.mixed_refined else (384_000, 768_000)
    names = ("both_polarities",) if args.mixed_refined else NAMES
    assert AREA.is_dir() and not list(AREA.iterdir())
    seq = 1
    prefix = "rf_d_pilot_q15_audit" if args.port_audit else "rf_d_pilot_q15_return"
    while (out := ROOT / f"evidence/{prefix}{seq:02}.json").exists():
        seq += 1
    sources = Sources(SOURCES)
    report = dict(passed=False, rack_integrated=False, host_frames=FRAMES, host_rate_hz=HOST_RATE,
                  candidate_rate_hz=clock, reference_rates_hz=[low, high], sample_columns=NODES, **sources.fields(),
                  compiler_sha256=sha(Path(COMPILER)), library_sha256=sha(LIB), cases={})
    env = dict(os.environ, PATH="C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;" + os.environ["PATH"])
    target = AREA / "q15-return.exe"

    def run(args, data=None):
        return subprocess.run(list(map(str, args)), cwd=ROOT, env=env, input=data,
                              capture_output=True, timeout=120)

    try:
        compiled = run([COMPILER, "--edition=2021", "-C", "opt-level=3", "-C", "target-feature=+fma",
                        "-A", "dead_code", "--cfg", "pilot_closed_cv", "--cfg", "pilot_audio_readout",
                        ROOT / PROBE, "--extern", f"rf_d_circuit={LIB}", "-o", target])
        assert compiled.returncode == 0, compiled.stderr.decode(errors="replace")
        for name in names:
            case = report["cases"][name] = {}
            if args.port_audit:
                data = fixture(name, clock)
                result = run([target, "audit", clock], data)
                replay = run([target, "audit", clock], data)
                assert (result.returncode, result.stdout, result.stderr) == (replay.returncode, replay.stdout, replay.stderr)
                case.update(passed=False, unchanged_replay=True, input_sha256=digest(data),
                            output_sha256=digest(result.stdout))
                if result.returncode:
                    case.update(error=result.stderr.decode(errors="replace").strip(),
                                failure_input=packed(data))
                else:
                    values = list(map(float, result.stdout.decode().strip().split(",")))
                    limits = [2e-13, 2e-12, 2e-20, 2e-18, 2e-13]
                    assert len(values) == len(limits) and np.isfinite(values).all()
                    case.update(passed=all(v <= lim for v, lim in zip(values, limits, strict=True)),
                                maxima=dict(zip(("current_a", "schur_s", "charge_c", "mass_f",
                                                "follower_current_a"), values, strict=True)), limits=limits)
                print(name, case, flush=True)
                continue
            arrays = {}
            for mode, rate in (("split", clock), ("oracle", clock), ("oracle", low), ("oracle", high)):
                data = fixture(name, rate)
                result = run([target, mode, rate], data)
                replay = run([target, mode, rate], data)
                assert (result.returncode, result.stdout, result.stderr) == (replay.returncode, replay.stdout, replay.stderr)
                key = f"{mode}_{rate}"
                meta = case[key] = dict(exit_code=result.returncode, unchanged_replay=True,
                                        input_sha256=digest(data), output_sha256=digest(result.stdout))
                if result.returncode:
                    meta.update(error=result.stderr.decode(errors="replace").strip(),
                                failure_input=packed(data))
                    continue
                rows = np.frombuffer(result.stdout, "<f8").reshape(-1, len(NODES))
                assert np.isfinite(rows).all() and len(rows) == 1 + 2 * FRAMES * rate // HOST_RATE
                arrays[key] = rows
            if len(arrays) != 4:
                case["passed"] = False
                print(name, {k: v.get("error") for k, v in case.items() if isinstance(v, dict) and "error" in v}, flush=True)
                continue
            coarse = arrays[f"split_{clock}"]
            middle = arrays[f"oracle_{low}"][::(2 * low // clock)]
            fine = arrays[f"oracle_{high}"][::(2 * high // clock)]
            same = contrast(coarse, arrays[f"oracle_{clock}"], charge_gate=True)
            refined = contrast(middle, fine)
            accuracy = contrast(coarse[::2], fine)
            current = coarse[:, 7]
            polarity = (max(current) < 0. if name == "reverse" else min(current) > 0. if name == "forward"
                        else min(current) < 0. and max(current) > 0.)
            events = switches(coarse[::2], name, clock)
            event_match = events == switches(fine, name, clock)
            case.update(passed=same["passed"] and refined["passed"] and accuracy["passed"] and bool(polarity) and event_match,
                        same_clock=same, refinement=refined, accuracy=accuracy,
                        cr6_range_a=[float(min(current)), float(max(current))],
                        collector_switch_intervals=events, event_match=event_match)
            if not args.mixed_refined:
                measured = run([target, "bench", clock], fixture(name, clock))
                assert measured.returncode == 0, measured.stderr.decode(errors="replace")
                times = list(map(int, measured.stdout.decode().strip().split(",")))
                case["timing"] = dict(zip(("blocks", "median_ns", "p99_ns", "max_ns"), times, strict=True))
            if not case["passed"]:
                case["failure_coarse_input"] = packed(fixture(name, clock))
            print(name, {k: case.get(k) for k in ("passed", "same_clock", "refinement", "accuracy", "cr6_range_a",
                                                 "collector_switch_intervals", "event_match", "timing")}, flush=True)
        report["passed"] = len(report["cases"]) == len(names) and all(row["passed"] for row in report["cases"].values())
        sources.unchanged()
    except Exception:
        report["failure"] = traceback.format_exc()
        raise
    finally:
        write(out, report)
        if target.exists():
            assert target.is_file() and target.resolve().parent == AREA.resolve()
            target.unlink()
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
