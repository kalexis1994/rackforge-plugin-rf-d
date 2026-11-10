"""Probe a C4-clock handoff to the closed Q25/Q15 block at 96 kHz."""
import os
import subprocess
import traceback
from pathlib import Path

import numpy as np

from affine_evidence import Sources
import check_rf_d_pilot_bistable_return as b
import check_rf_d_pilot_contours as c
from check_hybrid_voice import packed
from check_rf_d_pilot_precursor import (
    CALIBRATION, C4_CLOCK, SOURCE_NAMES, STEPS, TICK_S, TIMER_CARRY, TIMER_NATIVE,
    TIMER_NATIVE_PROBE, timer_native_fixture, timing_reference,
)
from check_rf_d_pilot_timer_rc import prepare_reference
from rf_d_pilot_attack_orbit import crossing_profile, landmarks
from rf_d_pilot_precursor import charge_family, charge_trace
from rf_d_pilot_timer_carry import PORTS as TIMER_PORTS, post_at, post_family, post_trace

OWN = "tools/check_rf_d_pilot_bistable_handoff.py"
PREVIOUS = "evidence/rf_d_pilot_bistable_return_seeded01.json"
CLOCK_CONTROL = "evidence/rf_d_pilot_cv_readout_pos03.json"
TIMERS = (5, 38)
NODES = (*b.NODES, *b.LOAD_NODES)
DENSITIES = (33, 129)


def handoff_trace(stages, cross, points):
    time, ports = post_trace(stages, cross, STEPS, NODES, points)
    state = ports[len(TIMER_PORTS):]
    state[4] -= state[0]  # Carry C4 as the voltage across its plates.
    return time, state


def initial_state(model, weights, elapsed):
    time, values = post_at(model, weights, coupled=False)
    assert time[0] <= elapsed <= time[-1]
    state = np.array([np.interp(elapsed, time, row) for row in values])
    state[4] += state[0]
    return state


def assess(got, expected):
    base = b.contrast(got[:, :len(b.LABELS)], b.observe(expected))
    loads = b.load_contrast(got, expected, "loads")
    return dict(passed=base["passed"] and loads["passed"], state=base, loads=loads)


def main():
    assert c.AREA.is_dir() and not list(c.AREA.iterdir())
    seq = 1
    while (out := c.ROOT / f"evidence/rf_d_pilot_bistable_handoff{seq:02}.json").exists():
        seq += 1
    sources = Sources((*b.SOURCES, *c.ALL_SOURCES, c.OWN, c.CANDIDATE, c.PROBE, c.PORTS,
                       OWN, PREVIOUS, CLOCK_CONTROL, *SOURCE_NAMES, C4_CLOCK, TIMER_CARRY, TIMER_NATIVE,
                       TIMER_NATIVE_PROBE, "tools/rf_d_pilot_timer_rc.rs"))
    report = dict(passed=False, rack_integrated=False, rate_hz=b.PILOT_RATE, refinement=STEPS,
                  **sources.fields(), compiler_sha256=c.sha(Path(c.COMPILER)), library_sha256=c.sha(c.LIB),
                  imposed_ports=(5, 54, 17, 24, 14), post_grids=DENSITIES, calibration=[], cases={})
    env = dict(os.environ, PATH="C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;" + os.environ["PATH"])
    clock = c.AREA / "handoff-clock.exe"
    closed = c.AREA / "handoff-return.exe"

    def process(command, data=None):
        return subprocess.run(list(map(str, command)), cwd=c.ROOT, env=env, input=data,
                              capture_output=True, timeout=180)

    def run(command, data=None):
        result = process(command, data)
        assert result.returncode == 0, result.stderr.decode(errors="replace")
        return result.stdout

    def replay(command, data, item):
        result = process(command, data)
        again = process(command, data)
        assert (result.returncode, result.stdout, result.stderr) == (again.returncode, again.stdout, again.stderr)
        item.update(exit_code=result.returncode, input_sha256=c.digest(data),
                    output_sha256=c.digest(result.stdout), unchanged_replay=True)
        if result.returncode:
            item.update(error=result.stderr.decode(errors="replace").strip(), failure_input=packed(data))
            return None
        values = np.frombuffer(result.stdout, "<f8")
        assert np.isfinite(values).all()
        return values

    def restart(data, expected, item, mode):
        got = replay([closed, mode, b.PILOT_RATE], data, item)
        if got is None:
            return False
        got = got.reshape(len(expected), len(b.LABELS) + len(b.LOAD_LABELS))
        first, rest = assess(got[:1], expected[:1]), assess(got[1:], expected[1:])
        item.update(handoff=first, continuation=rest)
        passed = first["passed"] and rest["passed"]
        if not passed:
            item["failure_input"] = packed(data)
        return passed

    try:
        build = [c.COMPILER, "--edition=2021", "-C", "opt-level=3", "-C", "target-feature=+fma",
                 "-A", "dead_code", "--extern", f"rf_d_circuit={c.LIB}"]
        run([*build, c.ROOT / TIMER_NATIVE_PROBE, "-o", clock])
        run([*build, "--cfg", "pilot_closed_cv", "--cfg", "pilot_audio_readout", c.ROOT / b.PROBE, "-o", closed])
        refs, report["reference_inputs"] = c.references()
        exe, _ = prepare_reference(run, report)
        anchor = c.AREA / "handoff.anchor"
        prior = c.read(PREVIOUS)["cases"]
        clock_control = c.read(CLOCK_CONTROL)["reserves"]

        def capture(branch, start, frames, key, offset):
            phase, _, _, state = refs[branch][1][start]
            state = state.copy()
            state[0, TIMERS] += offset
            anchor.write_bytes(np.r_[state.ravel(), phase].astype("<f8").tobytes())
            raw = run([exe, "contour-capture-refined", anchor, start, frames, key])
            stages = np.frombuffer(raw, "<f8").reshape(-1, c.N)
            assert stages.shape == (1 + frames * STEPS * 4, c.N) and np.isfinite(stages).all()
            return stages, dict(anchor_sha256=c.sha(anchor), reference_sha256=c.digest(raw),
                                offset_v=offset, start_frame=start, frames=frames, key_v=key)

        _, positive, start, frames, key = c.WINDOWS[0]
        paths, timers, traces = [], [], {points: [] for points in DENSITIES}
        for offset in CALIBRATION:
            stages, item = capture(positive, start, frames, key, offset)
            report["calibration"].append(item)
            slot, _, event = timing_reference(stages)
            cross = slot / b.PILOT_RATE + event["time"]
            paths.append(charge_trace(stages, (*TIMER_PORTS, 34)))
            timers.append(post_trace(stages, cross, STEPS, (34, 27)))
            for points, rows in traces.items():
                rows.append(handoff_trace(stages, cross, points))
            if offset == (0., 0.):
                nominal, nominal_event = stages, event
        quarter = np.r_[np.arange(64) / 256., np.arange(32, 129) / 128.]
        grid, timer_model = charge_family(paths, quarter), post_family(timers)
        models = {points: post_family(rows) for points, rows in traces.items()}
        _, tail = landmarks(nominal_event, 24)
        prefix = np.r_[np.column_stack(crossing_profile(nominal_event)).ravel(), tail[24:].ravel()]

        windows = [(name, positive, start, frames, key, offset) for name, offset in b.POSITIVE_LOADS]
        windows += [(*window, (0., 0.)) for window in c.WINDOWS[1:]]
        for name, branch, start, frames, key, offset in windows:
            if name == b.POSITIVE_LOADS[0][0]:
                stages, item = nominal, report["calibration"][0].copy()
            else:
                stages, item = capture(branch, start, frames, key, offset)
            assert item["reference_sha256"] == prior[name]["reference_sha256"]
            report["cases"][name] = item
            coarse_rows = 2 * STEPS * np.arange(frames * 2)[:, None] + [2 * STEPS // 3, 2 * STEPS]
            clock_data = timer_native_fixture(prefix, grid, timer_model, stages[0])
            predicted = replay([clock, "handoff"], clock_data, item.setdefault("clock", {}))
            if branch != positive:
                assert predicted is not None and predicted.size == 0
                expected = stages[np.r_[0, coarse_rows.ravel()]]
                data = b.window_payload(stages, coarse_rows, "loads")
                item["passed"] = restart(data, expected, item.setdefault("negative", {}), "loads")
                print(name, "negative", item["passed"], flush=True)
                continue
            if predicted is None or predicted.shape != (7,):
                item.update(passed=False, reason="C4 clock did not produce an event", failure_input=packed(clock_data))
                continue

            slot, _, reference = timing_reference(stages)
            predicted_slot, seconds, c2, c5 = predicted[:4]
            weights = predicted[5:]
            legacy = run([clock], clock_data)
            legacy_hash = c.digest(legacy)
            assert legacy_hash == clock_control[name]["native_timers"][0]["output_sha256"]
            assert legacy[:32] == predicted[:4].astype("<f8").tobytes()
            item["legacy_clock_output_sha256"] = legacy_hash
            assert slot == predicted_slot
            predicted_tick = start * 4096 + (slot / b.PILOT_RATE + seconds) / TICK_S
            bracket, = prior[name]["expected_events"]
            event_matches = bracket[0] <= predicted_tick <= bracket[1]
            next_index = coarse_rows[slot, 1]
            next_rows = coarse_rows[slot+1:].ravel()
            expected = stages[np.r_[next_index, next_rows]]
            timer_error = abs(np.array([c2, c5]) - expected[0, TIMERS])
            item.update(event_tick=float(predicted_tick), expected_event=bracket, event_matches=bool(event_matches),
                        event_error_ns=float((seconds - reference["time"]) * 1e9), load_weights=weights.tolist(),
                        handoff_timer_error_v=timer_error.tolist())
            port_nodes = (*b.PORTS, 14)
            boundary = expected[0, port_nodes].copy()
            drive = stages[next_rows[:, None], port_nodes].copy()
            boundary[4:6] = 0.
            drive[:, 4:6] = 0.
            control = b.payload(expected[0, NODES], boundary, drive)
            item["oracle_handoff_passed"] = restart(control, expected, item.setdefault("oracle_handoff", {}),
                                                    "loads-handoff")
            boundary[0] = c2
            for label, model, crossing in (
                ("predicted33", models[33], seconds),
                ("predicted129", models[129], seconds),
                ("reference_time129", models[129], reference["time"]),
            ):
                state = initial_state(model, weights, 1. / b.PILOT_RATE - crossing)
                data = b.payload(state, boundary, drive)
                item[label] = trial = {}
                trial["passed"] = restart(data, expected, trial, "loads-handoff")
            item["passed"] = bool(event_matches and timer_error.max() <= 2e-6 and item["predicted129"]["passed"])
            print(name, "event error ns", item["event_error_ns"], "timer error V", timer_error,
                  {label: item[label].get("passed", item[label].get("error")) for label in
                   ("predicted33", "predicted129", "reference_time129")}, flush=True)
        report["passed"] = bool(report["cases"]) and all(item["passed"] for item in report["cases"].values())
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
