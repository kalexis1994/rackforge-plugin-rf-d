"""Probe a C4-clock handoff to the closed Q25/Q15 block at 96 kHz."""
import argparse
import os
import subprocess
import traceback
from pathlib import Path

import numpy as np

from affine_evidence import Sources
import check_rf_d_pilot_bistable_return as b
import check_rf_d_pilot_contours as c
import rf_d_pilot_audio_readout as audio
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
DELAYED_CONTROL = "evidence/rf_d_pilot_bistable_handoff04.json"
NATIVE_CONTROL = "evidence/rf_d_pilot_bistable_handoff05.json"
C2_CONTROL = "evidence/rf_d_pilot_bistable_handoff06.json"
NATIVE = ("tools/rf_d_pilot_bistable_handoff.rs", "tools/rf_d_pilot_bistable_handoff_probe.rs")
TIMERS = (5, 38)
NODES = (*b.NODES, *b.LOAD_NODES)
DENSITIES = (33, 129)


def handoff_trace(stages, cross, points, intervals=1):
    time, ports = post_trace(stages, cross, STEPS, NODES, points, intervals)
    state = ports[len(TIMER_PORTS):]
    state[4] -= state[0]  # Carry C4 as the voltage across its plates.
    return time, state


def initial_state(model, weights, elapsed):
    time, values = post_at(model, weights, coupled=False)
    assert time[0] <= elapsed <= time[-1]
    state = np.array([np.interp(elapsed, time, row) for row in values])
    state[4] += state[0]
    return state


def packed_profile(model):
    time, nominal, linear, quadratic, _ = model
    return np.column_stack((time, nominal.T, linear[0].T, linear[1].T,
                            quadratic[0].T, quadratic[1].T)).astype("<f8").tobytes()


def assess(got, expected):
    base = b.contrast(got[:, :len(b.LABELS)], b.observe(expected))
    loads = b.load_contrast(got, expected, "loads")
    return dict(passed=base["passed"] and loads["passed"], state=base, loads=loads)


def receiver_stages(reference, coarse_rows, clock_rows, legacy, native, slot):
    # C2 and x27 before the edge come from the existing native clock.
    inputs = reference[coarse_rows[..., None], (5, 34, 27)].copy()
    inputs[:slot+1, :, 2] = clock_rows[:, :2]
    inputs[:slot+1, 0, 0] = clock_rows[:, 2]
    inputs[:slot, 1, 0] = legacy[4:].reshape(slot+1, 8)[1:, 0]
    # The native handoff owns the edge and the following stage pairs.
    inputs[slot, 1, [0, 2]] = native[0, [-1, 2]]
    inputs[slot+1:, :, 0] = native[1:, -1].reshape(-1, 2)
    inputs[slot+1:, :, 2] = native[1:, 2].reshape(-1, 2)
    return inputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    reentry = parser.add_mutually_exclusive_group()
    reentry.add_argument("--half-reentry", action="store_true", help="split only the first interval after handoff")
    reentry.add_argument("--delay-reentry", action="store_true", help="carry the post-event surface for one extra interval")
    reentry.add_argument("--native-reentry", action="store_true", help="run the C4 clock and delayed transfer together in Rust")
    reentry.add_argument("--native-c2", action="store_true", help="close C2 during the projected interval in Rust")
    reentry.add_argument("--audio", action="store_true", help="feed the native stages into the loaded audio receiver")
    args = parser.parse_args()
    args.native_c2 |= args.audio
    args.native_reentry |= args.native_c2
    args.delay_reentry |= args.native_reentry
    assert c.AREA.is_dir() and not list(c.AREA.iterdir())
    seq = 1
    while (out := c.ROOT / f"evidence/rf_d_pilot_bistable_handoff{seq:02}.json").exists():
        seq += 1
    native_sources = (*NATIVE, DELAYED_CONTROL) if args.native_reentry else ()
    if args.native_c2:
        native_sources += (NATIVE_CONTROL,)
    if args.audio:
        native_sources += (*audio.SOURCES, C2_CONTROL)
    sources = Sources((*b.SOURCES, *c.ALL_SOURCES, c.OWN, c.CANDIDATE, c.PROBE, c.PORTS,
                       OWN, PREVIOUS, CLOCK_CONTROL, *SOURCE_NAMES, C4_CLOCK, TIMER_CARRY, TIMER_NATIVE,
                       TIMER_NATIVE_PROBE, "tools/rf_d_pilot_timer_rc.rs", *native_sources))
    report = dict(passed=False, rack_integrated=False, rate_hz=b.PILOT_RATE, refinement=STEPS,
                  **sources.fields(), compiler_sha256=c.sha(Path(c.COMPILER)), library_sha256=c.sha(c.LIB),
                  imposed_ports=(5, 54, 17, 24, 14), post_grids=DENSITIES,
                  first_reentry_substeps=2 if args.half_reentry else 1,
                  delayed_reentry=args.delay_reentry, native_reentry=args.native_reentry,
                  closed_c2=args.native_c2, audio_readout=args.audio, calibration=[], cases={})
    if args.audio:
        report["audio_boundaries"] = dict(filter_sum_x34="reference at both stages",
                                          volume_latch_vca_base="reference",
                                          c2_after_projected_interval="reference")
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

    def timings(mode, data):
        results = list(map(int, run([clock, mode], data).decode().strip().split(",")))
        return dict(zip(("passes", "median_ns", "p99_ns", "max_ns"), results, strict=True))

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
        flags = ["--cfg", "pilot_closed_cv", "--cfg", "pilot_audio_readout"]
        native_flags = [*flags, "--cfg", "pilot_native_handoff"] if args.native_reentry else []
        run([*build, *native_flags, c.ROOT / TIMER_NATIVE_PROBE, "-o", clock])
        run([*build, *flags, c.ROOT / b.PROBE, "-o", closed])
        refs, report["reference_inputs"] = c.references()
        exe, _ = prepare_reference(run, report, with_audio=args.audio)
        anchor = c.AREA / "handoff.anchor"
        prior = c.read(PREVIOUS)["cases"]
        clock_control = c.read(CLOCK_CONTROL)["reserves"]
        delayed_control = c.read(DELAYED_CONTROL)["cases"] if args.native_reentry else {}
        native_control = c.read(NATIVE_CONTROL)["cases"] if args.native_c2 else {}
        c2_control = c.read(C2_CONTROL)["cases"] if args.audio else {}

        def receiver(branch, start, offset, stages):
            phase, _, _, state = refs[branch][1][start]
            state = state.copy()
            state[0, TIMERS] += offset
            return audio.Case(exe, env, state, phase, stages, joint=True, closed_cv=True)

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
        paths, timers, delayed_traces, traces = [], [], [], {points: [] for points in DENSITIES}
        for offset in CALIBRATION:
            stages, item = capture(positive, start, frames, key, offset)
            report["calibration"].append(item)
            slot, _, event = timing_reference(stages)
            cross = slot / b.PILOT_RATE + event["time"]
            paths.append(charge_trace(stages, (*TIMER_PORTS, 34)))
            timers.append(post_trace(stages, cross, STEPS, (34, 27)))
            for points, rows in traces.items():
                rows.append(handoff_trace(stages, cross, points))
            if args.delay_reentry:
                delayed_traces.append(handoff_trace(stages, cross, 129, intervals=2))
            if offset == (0., 0.):
                nominal, nominal_event = stages, event
        quarter = np.r_[np.arange(64) / 256., np.arange(32, 129) / 128.]
        grid, timer_model = charge_family(paths, quarter), post_family(timers)
        models = {points: post_family(rows) for points, rows in traces.items()}
        delayed = post_family(delayed_traces) if args.delay_reentry else None
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
                if args.native_reentry:
                    native = replay([clock, "native-handoff"], clock_data, item.setdefault("native", {}))
                    item["passed"] = item["passed"] and native is not None and native.size == 0
                if args.native_c2:
                    native = replay([clock, "native-handoff-c2"], clock_data, item.setdefault("native_c2", {}))
                    item["passed"] = item["passed"] and native is not None and native.size == 0
                if args.audio and item["passed"]:
                    command = [closed, "loads", b.PILOT_RATE]
                    closed_rows = np.frombuffer(run(command, data), "<f8").reshape(-1, 20)
                    assert c.digest(closed_rows.astype("<f8").tobytes()) == item["negative"]["output_sha256"]
                    inputs = stages[coarse_rows[..., None], (5, 34, 27)].copy()
                    inputs[:, :, 2] = closed_rows[1:, 2].reshape(-1, 2)
                    item["audio"] = receiver(branch, start, offset, stages).compare(0, exact_stages=inputs)
                    item["passed"] &= item["audio"]["passed"]
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
            chosen = item["predicted129"]
            if args.half_reentry:
                assert STEPS % 6 == 0
                # Two Radau steps of h/2 have stages at h/6, h/2, 2h/3 and h.
                half_rows = next_index + (STEPS // 3) * np.array([1, 3, 4, 6])
                mixed_rows = np.r_[half_rows, coarse_rows[slot+2:].ravel()]
                mixed_drive = stages[mixed_rows[:, None], port_nodes].copy()
                mixed_drive[:, 4:6] = 0.
                state = initial_state(models[129], weights, 1. / b.PILOT_RATE - seconds)
                data = b.payload(state, boundary, mixed_drive)
                chosen = item["predicted129_half_reentry"] = dict(reference_rows=mixed_rows.tolist())
                chosen["passed"] = restart(data, stages[np.r_[next_index, mixed_rows]], chosen, "loads-handoff-half")
            if args.delay_reentry:
                projected = item["delayed_projection"] = {}
                control_rows = []
                for fraction, row in zip((1. / 3., 1.), coarse_rows[slot+1], strict=True):
                    at = stages[row:row+1]
                    u = at[0, port_nodes].copy()
                    u[4:6] = 0.
                    age = (1. + fraction) / b.PILOT_RATE - seconds
                    state = initial_state(delayed, weights, age)
                    data = b.payload(state, u, np.empty(0))
                    trial = projected[str(fraction)] = dict(reference_row=int(row))
                    got = replay([closed, "loads-handoff", b.PILOT_RATE], data, trial)
                    if got is not None:
                        trial.update(assess(got.reshape(1, -1), at))
                        control_rows.append(got)
                    if not trial.get("passed", False):
                        trial["failure_input"] = packed(data)

                start_row = coarse_rows[slot+1, 1]
                rest_rows = coarse_rows[slot+2:].ravel()
                expected = stages[np.r_[start_row, rest_rows]]
                u = expected[0, port_nodes].copy()
                rest_drive = expected[1:, port_nodes].copy()
                u[4:6] = 0.
                rest_drive[:, 4:6] = 0.
                state = initial_state(delayed, weights, 2. / b.PILOT_RATE - seconds)
                chosen = item["predicted129_delayed_reentry"] = {}
                data = b.payload(state, u, rest_drive)
                passed = restart(data, expected, chosen, "loads-handoff")
                chosen["passed"] = passed and all(trial.get("passed", False) for trial in projected.values())
                if args.native_reentry and chosen["passed"]:
                    assert chosen == delayed_control[name]["predicted129_delayed_reentry"]
                    first_drive = boundary  # Generated C2 at the edge of the event interval.
                    first = initial_state(models[129], weights, 1. / b.PILOT_RATE - seconds)
                    first_data = b.payload(first, first_drive, np.empty(0))
                    command = [closed, "loads-handoff", b.PILOT_RATE]
                    first_row = np.frombuffer(run(command, first_data), "<f8")
                    rest = np.frombuffer(run(command, data), "<f8").reshape(-1, len(first_row))
                    assert np.array_equal(rest[0], control_rows[1])
                    python = np.vstack((first_row, *control_rows, rest[1:]))
                    ports = (*b.PORTS[:4], 14)
                    stage_drives = stages[coarse_rows[..., None], ports].astype("<f8")
                    tables = clock_data + packed_profile(models[129]) + packed_profile(delayed)
                    payload = tables + stage_drives.tobytes()
                    native = item["native"] = {}
                    values = replay([clock, "native-handoff"], payload, native)
                    if values is not None:
                        assert np.array_equal(values[:7], predicted)
                        got = values[7:].reshape(python.shape)
                        want = stages[np.r_[next_index, coarse_rows[slot+1:].ravel()]]
                        native.update(assess(got, want))
                        error = abs(got - python)
                        voltage = float(error[:, [*range(10), *range(12, 17)]].max())
                        current = float(error[:, [10, 11, 17, 18, 19]].max())
                        native.update(python_delta_v=voltage, python_delta_a=current,
                                      passed=native["passed"] and voltage <= 5e-11 and current <= 5e-14)
                        if native["passed"]:
                            if args.native_c2:
                                assert native["output_sha256"] == native_control[name]["native"]["output_sha256"]
                            else:
                                native["timing"] = timings("bench-native-handoff", payload)
                        else:
                            native["failure_input"] = packed(payload)
                    else:
                        native["passed"] = False
                    if args.native_c2 and native["passed"]:
                        stage_drives[slot+1, :, 0] = 0.  # Both projected C2 stages must be generated.
                        payload = tables + stage_drives.tobytes()
                        closed_c2 = item["native_c2"] = {}
                        values = replay([clock, "native-handoff-c2"], payload, closed_c2)
                        closed_c2["passed"] = False
                        if values is not None:
                            assert np.array_equal(values[:7], predicted)
                            rows = values[7:].reshape(len(want), python.shape[1] + 1)
                            closed_c2.update(assess(rows[:, :-1], want))
                            np.testing.assert_array_equal(rows[3:, -1], want[3:, 5])
                            timer = rows[1:3, -1]
                            c2_error = abs(rows[:3, -1] - want[:3, 5])
                            current = ((rows[1:3, [13, 16, 5]] - timer[:, None]) / [1000., 10_000., 10_000.]).sum(axis=1)
                            moved = np.array([(5. * current[0] - current[1]) / 12.,
                                              (3. * current[0] + current[1]) / 4.]) / b.PILOT_RATE
                            charge_error = abs((timer - rows[0, -1]) * 10e-6 - moved)
                            closed_c2.update(c2_error_v=c2_error.tolist(), charge_error_c=charge_error.tolist(),
                                             passed=bool(closed_c2["passed"] and c2_error.max() <= 2e-6
                                                         and charge_error.max() <= 1.01e-17))
                            if closed_c2["passed"]:
                                if args.audio:
                                    assert closed_c2["output_sha256"] == c2_control[name]["native_c2"]["output_sha256"]
                                    clock_cv = item["clock_cv"] = {}
                                    cv = replay([clock, "cv-stages"], clock_data, clock_cv).reshape(slot+1, 3)
                                    inputs = receiver_stages(stages, coarse_rows, cv, np.frombuffer(legacy, "<f8"), rows, slot)
                                    item["audio"] = receiver(branch, start, offset, stages).compare(0, exact_stages=inputs)
                                else:
                                    closed_c2["timing"] = timings("bench-native-handoff-c2", payload)
                            else:
                                closed_c2["failure_input"] = packed(payload)
            item["passed"] = bool(event_matches and timer_error.max() <= 2e-6
                                  and item["predicted129"].get("handoff", {}).get("passed", False)
                                  and chosen["passed"]
                                  and (not args.native_reentry or item.get("native", {}).get("passed", False))
                                  and (not args.native_c2 or item.get("native_c2", {}).get("passed", False))
                                  and (not args.audio or item.get("audio", {}).get("passed", False)))
            print(name, "event error ns", item["event_error_ns"], "timer error V", timer_error,
                  {label: trial["passed"] for label, trial in item.items()
                   if label.startswith("predicted") or label in ("native", "native_c2", "audio")},
                  flush=True)
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
