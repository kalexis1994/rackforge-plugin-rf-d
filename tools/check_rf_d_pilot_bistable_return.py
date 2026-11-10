"""Replay the Q25/Q15/C4 and CR6 block against full Radau stages."""
import argparse
import os
import subprocess
import traceback
from pathlib import Path

import numpy as np

from affine_evidence import Sources
import check_rf_d_pilot_contours as c
from check_hybrid_voice import packed
from check_rf_d_pilot_timer_rc import prepare_reference

OWN = "tools/check_rf_d_pilot_bistable_return.py"
PROBE = "tools/rf_d_pilot_bistable_return_probe.rs"
SOURCES = (OWN, PROBE, "tools/rf_d_pilot_bistable_return.rs", "tools/rf_d_pilot_q15_return.rs",
           "tools/rf_d_pilot_contour_ports.rs", "tools/latch_charge_driver.rs",
           "tools/rf_d_reduced_engine_lu.rs", "crates/rf-d-circuit/src/prepared_volume_residual.rs",
           "crates/rf-d-circuit/src/junction_charge.rs")
NODES = (25, 26, 27, 28, 23, 0, 1, 3, 2, 4)
PORTS = (5, 54, 17, 24, 6, 9)
LABELS = (*[f"x{i}" for i in NODES], "cr6_a", "r59_a")
DIODE_SCALE = 1.5 * (1.380649e-23 * 298.15 / 1.602176634e-19)
RATE = 24_576_000
PILOT_RATE = 96_000
HOST = 48_000
FRAMES = 128
POSITIVE_LOADS = (("positive_crossing", (0., 0.)), ("positive_c2_up", (.05, -.05)),
                  ("positive_c2_down", (-.05, .05)))


def payload(seed, start, stages):
    return np.r_[seed, start, stages.ravel()].astype("<f8").tobytes()


def observe(rows):
    cr6 = 1e-8 * np.expm1((rows[:, 4] - rows[:, 27]) / DIODE_SCALE)
    r59 = (rows[:, 3] - rows[:, 54]) / 68_000.
    return np.column_stack((rows[:, NODES], cr6, r59))


def contrast(got, want):
    delta = abs(got - want)
    maximum = delta.max(axis=0)
    c4 = abs((got[:, 4] - got[:, 0]) - (want[:, 4] - want[:, 0])).max()
    worst = int(np.argmax(delta[:, :10]) // 10)
    return dict(passed=bool(maximum[:10].max() <= 20e-6 and maximum[10:].max() <= 2e-9),
                maximum=dict(zip(LABELS, maximum.tolist(), strict=True)), worst_voltage_row=worst,
                max_c4_charge_c=float(c4 * 10e-9))


def switches(rows, start_tick, step_ticks):
    sign = rows[::2, 1] >= rows[::2, 3]
    return [[start_tick + int(i) * step_ticks, start_tick + (int(i) + 1) * step_ticks, int(sign[i + 1])]
            for i in np.flatnonzero(sign[1:] != sign[:-1])]


def active_drive(name, t):
    w = 2. * np.pi * t * HOST / FRAMES
    c2, vca = (9.15 + .13 * np.sin(w), 4.31 + .04 * np.cos(w)) if name == "forward" else (
        3.12 + .18 * np.sin(w), .70 + .06 * np.cos(w))
    return np.stack((c2, vca, .19 + .055 * np.sin(w + .31), .25 + .05 * np.cos(w),
                     9.04 + .065 * np.sin(w), 8.42 + .04 * np.cos(w + .7)), axis=-1)


def active_fixture(name, rate):
    initial = active_drive(name, 0.)
    c2 = initial[0]
    x3 = c2 - 1.15
    cv = .92 if name == "forward" else (x3 - 10. * 6800. / 16_900.) / (1. + 6800. / 16_900.)
    seed = [.18, 8.76, .75, .18, initial[2], c2 - .06, c2 - .61, x3,
            8.75 if name == "forward" else 9.0, cv]
    ticks = np.arange(FRAMES * rate // HOST)
    return payload(seed, initial, active_drive(name, (ticks[:, None] + [1. / 3., 1.]) / rate))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--active", action="store_true", help="contrast controlled forward and reverse CR6 loads")
    parser.add_argument("--plate", action="store_true", help="eliminate the x23 stage voltages analytically")
    args = parser.parse_args()
    mode = "plate" if args.plate else "split"
    assert c.AREA.is_dir() and not list(c.AREA.iterdir())
    seq = 1
    kind = "active" if args.active else "windows"
    while (out := c.ROOT / f"evidence/rf_d_pilot_bistable_return_{kind}{seq:02}.json").exists():
        seq += 1
    full_sources = () if args.active else (*c.ALL_SOURCES, c.OWN, c.CANDIDATE, c.PROBE, c.PORTS,
                                           "tools/check_rf_d_pilot_timer_rc.py",
                                           "evidence/rf_d_pilot_cv_readout_pos03.json")
    sources = Sources((*SOURCES, *full_sources))
    report = dict(passed=False, rack_integrated=False, mode=kind, plate_eliminated=args.plate, sample_columns=LABELS,
                  **sources.fields(), compiler_sha256=c.sha(Path(c.COMPILER)),
                  library_sha256=c.sha(c.LIB), cases={})
    env = dict(os.environ, PATH="C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;" + os.environ["PATH"])
    target = c.AREA / "bistable-return.exe"

    def process(args, data=None):
        return subprocess.run(list(map(str, args)), cwd=c.ROOT, env=env, input=data,
                              capture_output=True, timeout=180)

    def run(args, data=None):
        raw = process(args, data)
        assert raw.returncode == 0, raw.stderr.decode(errors="replace")
        return raw.stdout

    def evaluate(mode, rate, data, item, settle=False):
        command = [target, mode, rate] + (["dc"] if settle else [])
        raw = process(command, data)
        replay = process(command, data)
        assert (raw.returncode, raw.stdout, raw.stderr) == (replay.returncode, replay.stdout, replay.stderr)
        result = item[f"{mode}_{rate}"] = dict(exit_code=raw.returncode, input_sha256=c.digest(data),
                                               output_sha256=c.digest(raw.stdout), unchanged_replay=True)
        if raw.returncode:
            result.update(error=raw.stderr.decode(errors="replace").strip(), failure_input=packed(data))
            return None
        rows = np.frombuffer(raw.stdout, "<f8").reshape(-1, len(LABELS))
        assert len(rows) == 1 + 2 * ((len(data) // 8 - 16) // 12) and np.isfinite(rows).all()
        return rows

    try:
        run([c.COMPILER, "--edition=2021", "-C", "opt-level=3", "-C", "target-feature=+fma",
             "-A", "dead_code", "--cfg", "pilot_closed_cv", "--cfg", "pilot_audio_readout",
             c.ROOT / PROBE, "--extern", f"rf_d_circuit={c.LIB}", "-o", target])
        if args.active:
            for name in ("reverse", "forward"):
                item = report["cases"][name] = {}
                data = active_fixture(name, PILOT_RATE)
                test = evaluate(mode, PILOT_RATE, data, item, settle=True)
                matched = evaluate("oracle", PILOT_RATE, data, item, settle=True)
                low, high = (evaluate("oracle", rate, active_fixture(name, rate), item, settle=True)
                             for rate in (384_000, 768_000))
                item["passed"] = False
                if all(v is not None for v in (test, matched, low, high)):
                    same = contrast(test, matched)
                    refined = contrast(low[::8], high[::16])
                    fine = contrast(test[::2], high[::16])
                    cr6 = [float(test[:, 10].min()), float(test[:, 10].max())]
                    polarity = cr6[0] > 0. if name == "forward" else cr6[1] < 0.
                    item.update(same_clock=same, refinement=refined, accuracy=fine, cr6_range_a=cr6,
                                passed=all(t["passed"] for t in (same, refined, fine)) and polarity)
                    bench = "bench-plate" if args.plate else "bench"
                    rows = run([target, bench, PILOT_RATE, "dc"], data).decode().splitlines()
                    fields = ("blocks", "median_ns", "p99_ns", "max_ns")
                    timings = [dict(zip(fields, map(int, row.split(",")), strict=True)) for row in rows]
                    if args.plate:
                        before, after = timings
                        item["timing"] = dict(alternating=True, uncondensed=before, condensed=after,
                                              median_speedup=before["median_ns"] / after["median_ns"])
                    else:
                        item["timing"], = timings
                print(name, {k: v for k, v in item.items() if k in
                             ("passed", "accuracy", "cr6_range_a", "timing") or isinstance(v, dict) and "error" in v}, flush=True)
        else:
            refs, report["reference_inputs"] = c.references()
            exe, _ = prepare_reference(run, report)
            anchor = c.AREA / "bistable-return.anchor"
            previous = c.read("evidence/rf_d_pilot_cv_readout_pos03.json")
            label, branch, start, frames, key = c.WINDOWS[0]
            windows = [(name, branch, start, frames, key, offset) for name, offset in POSITIVE_LOADS]
            windows += [(*window, (0., 0.)) for window in c.WINDOWS[1:]]
            for label, branch, start, frames, key, offset in windows:
                phase, _, _, state = refs[branch][1][start]
                state = state.copy()
                state[0, [5, 38]] += offset
                anchor.write_bytes(np.r_[state.ravel(), phase].astype("<f8").tobytes())
                # Refinement by three reproduces the prior positive C2/C5 reserves.
                raw = run([exe, "contour-capture-refined", anchor, start, frames, key])
                full = np.frombuffer(raw, "<f8").reshape(-1, c.N)
                clock = 3 * RATE
                assert full.shape == (1 + 2 * frames * clock // HOST, c.N) and np.isfinite(full).all()
                known = [previous["reserves"][label]["reference_event"]] if branch == "positive" else []
                item = report["cases"][label] = dict(passed=False, expected_events=known, offset_v=offset,
                    reference_sha256=c.digest(raw), anchor_sha256=c.sha(anchor), start_frame=start, frames=frames)
                test = evaluate(mode, clock, payload(full[0, NODES], full[0, PORTS], full[1:, PORTS]), item)
                want = observe(full)
                if test is not None:
                    result = contrast(test, want)
                    # At 3x refinement each endpoint has one-third of an 8-tick step.
                    flips = switches(test, 0, 1)
                    events = [[start * 4096 + (lo // 3) * 8, start * 4096 + (lo // 3 + 1) * 8, sign]
                              for lo, _, sign in flips]
                    assert events == [[start * 4096 + (lo // 3) * 8, start * 4096 + (lo // 3 + 1) * 8, sign]
                                      for lo, _, sign in switches(want, 0, 1)]
                    item.update(fine=result, events=events, passed=result["passed"] and events == known)
                stride = clock // PILOT_RATE
                stage_rows = (2 * stride * np.arange(frames * 2)[:, None] + [2 * stride // 3, 2 * stride])
                assert stride % 3 == 0
                coarse = evaluate(mode, PILOT_RATE, payload(full[0, NODES], full[0, PORTS],
                                  full[stage_rows[:, :, None], PORTS]), item)
                if coarse is not None:
                    item["coarse_diagnostic"] = contrast(coarse[::2], want[::2 * stride])
                print(label, {k: v for k, v in item.items() if k in ("passed", "fine", "events", "coarse_diagnostic")
                              or isinstance(v, dict) and "error" in v}, flush=True)
        report["passed"] = bool(report["cases"]) and all(t["passed"] for t in report["cases"].values())
        sources.unchanged()
    except Exception:
        report["failure"] = traceback.format_exc()
        raise
    finally:
        for path in c.AREA.iterdir():
            assert path.is_file() and path.resolve().parent == c.AREA.resolve()
            path.unlink()
        c.write(out, report)
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
