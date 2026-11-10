"""Contrast a coarse-clock C4 guard against refined Model D reserves."""
import argparse
import os
import subprocess
import traceback
from pathlib import Path

import numpy as np

from affine_evidence import Sources
import check_rf_d_pilot_contours as c
from check_rf_d_pilot_timer_rc import (
    ATTACK, ATTACK_ORBIT, ATTACK_PROBE, CROSSING, CROSSING_PROBE, LATCH_CHARGE, MODEL,
    OHMS, TIMER_NODES, prepare_reference, project_stages,
)
from rf_d_pilot_attack_orbit import crossing_profile, extract, landmarks
from rf_d_pilot_precursor import (
    CLOCK, GUARD, NODES, advance, carry, carry_charge, charge_family, charge_trace, family, trace,
)

CALIBRATION = ((0., 0.), (.075, 0.), (-.075, 0.), (0., .075), (0., -.075),
               (.075, -.075), (-.075, .075))
RESERVES = ((.05, -.05), (-.05, .05))
NAMES = ("positive_crossing", "positive_c2_up", "positive_c2_down")
STEPS = 768
TICK_S = 1. / (48_000 * 4096)
TICKS = 8. / 3.
C2_GAIN = (1. / OHMS[0, 1:]).sum()
X = C2_GAIN / (10e-6 * CLOCK)
MOVED = -np.expm1(-X)
NATIVE = "tools/rf_d_pilot_precursor.rs"
NATIVE_PROBE = "tools/rf_d_pilot_precursor_probe.rs"
SOURCE_NAMES = ("tools/check_rf_d_pilot_precursor.py", "tools/rf_d_pilot_precursor.py",
                "tools/check_rf_d_pilot_timer_rc.py", ATTACK, ATTACK_ORBIT, CROSSING,
                CROSSING_PROBE, LATCH_CHARGE)


def timing_reference(stages):
    nodes = stages[::2]
    sign = nodes[:, 26] >= nodes[:, 28]
    changes = np.flatnonzero(sign[:-1] != sign[1:])
    assert len(changes) == 1 and sign[changes[0] + 1]
    edge = int(changes[0])
    slot = edge // STEPS
    inside = stages[2 * slot * STEPS:2 * (slot + 1) * STEPS + 1]
    return slot, edge, extract(inside, STEPS)


def compare(run, native, shape, observations, stages, slot, edge, target, start, expected,
            order, quadratic_anchor, reference_guard_s):
    events = []
    skipped = []
    states = np.column_stack((stages[1:, 8] - stages[1:, 5],
                              stages[1:, 44] - stages[1:, 38])) / OHMS[:, 0]
    ref = project_stages(states[..., None], (1. / OHMS[:, 1:]).sum(axis=1), TICKS)[slot, 0, 0]
    for i in range(1, len(observations) - 1):
        observed = observations[i]
        guard = advance(shape, observed, order, quadratic_anchor)
        if guard is None:
            continue
        data = np.r_[native[1], guard["point"], guard["time_s"], 0., 0.].astype("<f8").tobytes()
        output = run([native[0], "maybe"], data)
        if not output:
            skipped.append(dict(slot=i, **guard))
            continue
        assert output == run([native[0], "maybe"], data)
        time_s, cross_v, *values, tail_a = np.frombuffer(output, "<f8")
        tick = (i / CLOCK + time_s) / TICK_S
        absolute_tick = start * 4096 + tick
        # The pre-event ramp uses only two preceding boundary observations.
        pre = (observations[i-1:i+1, 8] - observations[i-1:i+1, 5]) / OHMS[0, 0]
        fraction = time_s * CLOCK
        m0 = np.expm1(X * fraction) * np.exp(-X) / MOVED
        m1 = (X * fraction * np.exp(X * fraction) - np.expm1(X * fraction)) * np.exp(-X) / (X * MOVED)
        average = m0 * pre[1] + m1 * (pre[1] - pre[0]) + tail_a
        timer_error = abs(average - ref) * MOVED / C2_GAIN if i == slot else None
        time_error = (i / CLOCK + time_s - (slot / CLOCK + target["time"])) * 1e9
        guard_error = (i / CLOCK + guard["time_s"] - reference_guard_s) * 1e9
        events.append(dict(slot=i, guard=guard, predicted_tick=float(absolute_tick),
                           guard_error_ns=float(guard_error),
                           time_error_ns=float(time_error), crossing_v=float(cross_v),
                           historical_bracket=bool(expected[0] <= absolute_tick <= expected[1]),
                           refined_bracket=bool(edge * TICKS <= tick <= (edge + 1) * TICKS),
                           crossing_state_error_v=abs(np.asarray(values) - target["crossing"]).tolist(),
                           c2_error_v=timer_error, modeled_attack_a=float(average),
                           event_time_s=float(time_s), tail_a=float(tail_a),
                           reference_attack_a=float(ref), input_sha256=c.digest(data),
                           output_sha256=c.digest(output)))
    passes = len(events) == 1 and events[0]["historical_bracket"] and events[0]["c2_error_v"] is not None and events[0]["c2_error_v"] <= 2e-6
    return dict(passed=bool(passes), events=events, incomplete_guards=skipped)


def carried_trial(run, native, attack, model, shape, initial, stages, slot, edge, target, start, expected, guard_s, first):
    result = model(shape, initial)
    if result is None:
        return dict(passed=False, reason="initial state outside rising C4 path")
    states = result.pop("state")
    event_slot = first + result["slot"]
    data = np.r_[native[1], result["point"], result["time_s"], 0., 0.].astype("<f8").tobytes()
    output = run([native[0], "maybe"], data)
    assert output == run([native[0], "maybe"], data)
    if not output or len(states) < 2:
        return dict(passed=False, reason="incomplete event or missing causal attack slope", guard=result)
    time_s, cross_v, *values, tail_a = np.frombuffer(output, "<f8")
    tick = (event_slot / CLOCK + time_s) / TICK_S
    absolute = start * 4096 + tick
    # Generate both attack currents from the carried C2 and x26, with C5
    # and x40 as the companion cell's inputs.
    pre = states[-2:]
    control = np.column_stack((pre[:, 0], pre[:, 6], np.full(2, 8.3), pre[:, 8]))
    raw = run([attack], control.astype("<f8").tobytes())
    currents = np.frombuffer(raw, "<f8").reshape(2, 2, 4)[:, 0, 2]
    fraction = time_s * CLOCK
    m0 = np.expm1(X * fraction) * np.exp(-X) / MOVED
    m1 = (X * fraction * np.exp(X * fraction) - np.expm1(X * fraction)) * np.exp(-X) / (X * MOVED)
    average = m0 * currents[1] + m1 * (currents[1] - currents[0]) + tail_a
    stage_current = np.column_stack((stages[1:, 8] - stages[1:, 5],
                                     stages[1:, 44] - stages[1:, 38])) / OHMS[:, 0]
    wanted = project_stages(stage_current[..., None], (1. / OHMS[:, 1:]).sum(axis=1), TICKS)[slot, 0, 0]
    timer_error = abs(average - wanted) * MOVED / C2_GAIN if event_slot == slot else None
    reference = stages[2 * STEPS * first:2 * STEPS * (event_slot + 1):2 * STEPS, NODES].copy()
    reference[:, 0] -= reference[:, 1]
    errors = abs(states[:, 1:] - reference).max(axis=0)
    event_error = (event_slot / CLOCK + time_s - (slot / CLOCK + target["time"])) * 1e9
    guard_error = (event_slot / CLOCK + result["time_s"] - guard_s) * 1e9
    bracket = bool(expected[0] <= absolute <= expected[1])
    return dict(passed=bool(bracket and timer_error is not None and timer_error <= 2e-6),
                first_slot=first, event_slot=event_slot, guard=result, predicted_tick=float(absolute),
                historical_bracket=bracket, refined_bracket=bool(edge * TICKS <= tick <= (edge + 1) * TICKS),
                guard_error_ns=float(guard_error), time_error_ns=float(event_error),
                c2_event_error_v=timer_error, max_state_error_v=dict(zip(NODES, errors.tolist())),
                crossing_v=float(cross_v), crossing_state_error_v=abs(np.asarray(values) - target["crossing"]).tolist(),
                modeled_attack_a=float(average), reference_attack_a=float(wanted),
                generated_states=len(states), states_sha256=c.digest(states.astype("<f8").tobytes()),
                input_sha256=c.digest(data), output_sha256=c.digest(output))


def native_trial(run, target, prefix, model, observations, result):
    assert result["passed"] and len(result["events"]) == 1
    event = result["events"][0]
    columns, nominal, linear, quadratic, _ = model
    table = np.column_stack((columns, nominal.T, linear[0].T, linear[1].T,
                             quadratic[0].T, quadratic[1].T))
    source = observations[1:, [26, *NODES]]
    rows = np.vstack((source, np.tile(source[-1], (256 - len(source), 1))))
    data = np.r_[prefix, table.ravel(), rows.ravel()].astype("<f8").tobytes()
    output = run([target], data)
    assert output == run([target], data)
    got = np.frombuffer(output, "<f8")
    wanted = np.array([event["slot"] - 1, event["guard"]["time_s"],
                       event["event_time_s"], event["tail_a"]])
    assert got.shape == wanted.shape and np.isfinite(got).all()
    error = abs(got - wanted)
    assert error[0] == 0 and error[1:3].max() <= 1e-12 and error[3] <= 1e-10
    timing = list(map(int, run([target, "bench"], data).decode().strip().split(",")))
    return dict(passed=True, max_error=error.tolist(), host_frames=128, includes_audio=False,
                input_sha256=c.digest(data), output_sha256=c.digest(output),
                timing=dict(zip(("blocks", "median_ns", "p99_ns", "max_ns"), timing)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--native", action="store_true", help="verify and time the bounded Rust guard and event")
    parser.add_argument("--carry", action="store_true", help="advance C4 from one initial state")
    args_main = parser.parse_args()
    assert c.AREA.is_dir() and not list(c.AREA.iterdir())
    seq = 1
    while (out := c.ROOT / f"evidence/rf_d_pilot_precursor{seq:02}.json").exists():
        seq += 1
    previous = "evidence/rf_d_pilot_timer_rc10.json"
    native_sources = (NATIVE, NATIVE_PROBE) if args_main.native else ()
    if args_main.carry:
        native_sources += (ATTACK_PROBE, MODEL)
    sources = Sources((*c.ALL_SOURCES, c.OWN, c.CANDIDATE, c.PROBE, c.PORTS,
                       "tools/rf_d_pilot_step_profile.rs", previous, *SOURCE_NAMES, *native_sources))
    report = dict(passed=False, rack_integrated=False, clock_hz=CLOCK, native=args_main.native, carry=args_main.carry, calibration=[],
                  reserves={}, **sources.fields(), compiler_sha256=c.sha(Path(c.COMPILER)),
                  library_sha256=c.sha(c.LIB))
    env = dict(os.environ, PATH="C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;" + os.environ["PATH"])

    def run(command, data=None):
        proc = subprocess.run(list(map(str, command)), cwd=c.ROOT, env=env, input=data,
                              capture_output=True, timeout=240)
        assert proc.returncode == 0, proc.stderr.decode(errors="replace")
        return proc.stdout

    try:
        refs, report["reference_inputs"] = c.references()
        exe, build = prepare_reference(run, report)
        native = c.AREA / "pilot-crossing.exe"
        run([*build, "-A", "dead_code", c.ROOT / CROSSING_PROBE, "--extern",
             f"rf_d_circuit={c.LIB}", "-o", native])
        native_guard = c.AREA / "pilot-precursor.exe"
        if args_main.native:
            run([*build, "-A", "dead_code", c.ROOT / NATIVE_PROBE, "--extern",
                 f"rf_d_circuit={c.LIB}", "-o", native_guard])
        attack = c.AREA / "pilot-attack.exe"
        if args_main.carry:
            run([*build, "-A", "dead_code", c.ROOT / ATTACK_PROBE, "-o", attack])
        anchor = c.AREA / "precursor-anchor.bin"

        def capture(branch, start, frames, key, offset):
            phase, _, _, state = refs[branch][1][start]
            state = state.copy()
            state[0, TIMER_NODES] += offset
            anchor.write_bytes(np.asarray(np.r_[state.ravel(), phase], "<f8").tobytes())
            raw = run([exe, "contour-capture-refined", anchor, start, frames, key])
            stages = np.frombuffer(raw, "<f8").reshape(-1, c.N)
            assert stages.shape[0] == 1 + frames * 3072 and np.isfinite(stages).all()
            return stages, dict(anchor_sha256=c.sha(anchor), reference_sha256=c.digest(raw),
                                offset_v=offset, start_frame=start, frames=frames, key_v=key)

        start, frames, key = c.WINDOWS[0][2:]
        paths = []
        charge_paths = []
        for offset in CALIBRATION:
            stages, item = capture("positive", start, frames, key, offset)
            report["calibration"].append(item)
            paths.append(trace(stages))
            if args_main.carry:
                charge_paths.append(charge_trace(stages))
            if offset == (0., 0.):
                nominal = stages
        model = family(paths)
        dense = family(paths, 257)
        if args_main.carry:
            phase_model = charge_family(charge_paths)
            phase_dense = charge_family(charge_paths, 257)
            carry_modes = (
                ("65", carry, model), ("257", carry, dense),
                ("q65_axis", lambda m, s: carry_charge(m, s, False), phase_model),
                ("q65_coupled", lambda m, s: carry_charge(m, s, True), phase_model),
                ("q257_axis", lambda m, s: carry_charge(m, s, False), phase_dense),
                ("q257_coupled", lambda m, s: carry_charge(m, s, True), phase_dense),
            )
        _, _, path = timing_reference(nominal)
        rise = np.column_stack(crossing_profile(path))
        _, tail = landmarks(path, 24)
        native_args = native, np.r_[rise.ravel(), tail[24:].ravel()]
        prior = c.read(previous)["windows"]
        for name, offset in zip(NAMES, ((0., 0.), *RESERVES)):
            if name == NAMES[0]:
                stages, item = nominal, report["calibration"][0].copy()
            else:
                stages, item = capture("positive", start, frames, key, offset)
            slot, edge, target = timing_reference(stages)
            expected = prior[name]["reference_events"][0]
            assert expected[0] <= start * 4096 + edge * TICKS < start * 4096 + (edge + 1) * TICKS <= expected[1]
            observations = stages[::2 * STEPS]
            guard_row = int(np.flatnonzero(stages[:, 26] >= GUARD)[0])
            pair = stages[guard_row-1:guard_row+1]
            fraction = (GUARD - pair[0, 26]) / (pair[1, 26] - pair[0, 26])
            timeline = np.r_[0., (np.arange(len(stages) // 2)[:, None] + [1. / 3., 1.]).ravel()] / (STEPS * CLOCK)
            guard_s = timeline[guard_row-1] + fraction * (timeline[guard_row] - timeline[guard_row-1])
            guard_point = pair[0] + fraction * (pair[1] - pair[0])
            guard_data = np.r_[native_args[1], guard_point[[26, 25, 27, 9, 5, 28]],
                               guard_s - slot / CLOCK, 0., 0.].astype("<f8").tobytes()
            conditional = np.frombuffer(run([native, "maybe"], guard_data), "<f8")
            assert conditional.shape == (7,)
            item["refined_guard_to_event_error_ns"] = float((conditional[0] - target["time"]) * 1e9)
            cases = (("nominal_offset", model, 0, False), ("linear_load", model, 1, False),
                     ("quadratic_load", model, 2, False), ("linear_dense", dense, 1, False),
                     ("linear_local_quadratic", model, 1, True),
                     ("quadratic_local_quadratic", model, 2, True),
                     ("coupled_local_quadratic", model, 3, True))
            modes = item["modes"] = {}
            for label, shape, order, local_quad in cases:
                args = run, native_args, shape, observations, stages, slot, edge, target, start, expected, order, local_quad, guard_s
                modes[label] = compare(*args)
                assert modes[label] == compare(*args)
            if args_main.native:
                item["native_trial"] = native_trial(run, native_guard, native_args[1], model, observations,
                                                   modes["quadratic_local_quadratic"])
                print("NATIVE_C4", name, item["native_trial"], flush=True)
            if args_main.carry:
                trials = item["carried"] = {}
                for mode, advance_model, shape in carry_modes:
                    series = trials[mode] = []
                    for first in range(2):
                        carried_args = (run, native_args, attack, advance_model, shape, observations[first], stages,
                                        slot, edge, target, start, expected, guard_s, first)
                        trial = carried_trial(*carried_args)
                        assert trial == carried_trial(*carried_args)
                        series.append(trial)
                print("CARRY", name, {mode: [(x.get("time_error_ns"), x.get("c2_event_error_v"), x["passed"])
                                            for x in group] for mode, group in trials.items()}, flush=True)
            item.update(reference_event=expected, reference_slot=slot, unchanged_replay=True)
            report["reserves"][name] = item
            print(name, {label: [(round(e["time_error_ns"], 3), e["historical_bracket"],
                                  None if e["c2_error_v"] is None else round(1e6 * e["c2_error_v"], 3))
                                 for e in trial["events"]] for label, trial in modes.items()}, flush=True)
        for label, branch, start, frames, key in c.WINDOWS[1:]:
            stages, item = capture(branch, start, frames, key, (0., 0.))
            observations = stages[::2 * STEPS]
            item["false_guard"] = any(advance(shape, x, order, local_quad) is not None
                                      for x in observations for _, shape, order, local_quad in cases)
            assert not item["false_guard"]
            if args_main.carry:
                item["false_carried"] = any(advance_model(shape, observations[0]) is not None for _, advance_model, shape in carry_modes)
                assert not item["false_carried"]
            report["reserves"][label] = item
        report["passed"] = True
        report["modes_admitted_in_bank"] = [label for label, *_ in cases
                                            if all(report["reserves"][name]["modes"][label]["passed"]
                                                   for name in NAMES)]
        if args_main.carry:
            report["carried_modes_admitted"] = [
                mode for mode, _, _ in carry_modes
                if all(report["reserves"][name]["carried"][mode][0]["passed"] for name in NAMES)]
        sources.unchanged()
    except Exception:
        report["failure"] = traceback.format_exc()
        raise
    finally:
        for path in c.AREA.iterdir():
            assert path.is_file() and path.resolve().parent == c.AREA.resolve()
            path.unlink()
        c.write(out, report)


if __name__ == "__main__":
    main()
