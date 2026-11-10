"""Contrast a coarse-clock C4 guard against refined Model D reserves."""
import argparse
import os
import subprocess
import traceback
from pathlib import Path

import numpy as np

from affine_evidence import Sources
import check_rf_d_pilot_contours as c
import rf_d_pilot_return_readout as returns
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
C4_CLOCK = "tools/rf_d_pilot_c4_clock.rs"
C4_PROBE = "tools/rf_d_pilot_c4_clock_probe.rs"
TIMER_CARRY = "tools/rf_d_pilot_timer_carry.py"
TIMER_NATIVE = "tools/rf_d_pilot_timer_carry.rs"
TIMER_NATIVE_PROBE = "tools/rf_d_pilot_timer_carry_probe.rs"
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
                event_time_s=float(time_s), c2_event_error_v=timer_error, max_state_error_v=dict(zip(NODES, errors.tolist())),
                crossing_v=float(cross_v), crossing_state_error_v=abs(np.asarray(values) - target["crossing"]).tolist(),
                modeled_attack_a=float(average), reference_attack_a=float(wanted),
                generated_states=len(states), states_sha256=c.digest(states.astype("<f8").tobytes()),
                input_sha256=c.digest(data), output_sha256=c.digest(output))


def timer_trial(run, native, attack, shape, post, initial, observations, start, expected,
                first, coupled, mode, path_projection, shifted):
    from rf_d_pilot_timer_carry import OHMS, run as render

    def evaluate(latch, timer):
        data = np.stack((latch, timer), axis=-1).astype("<f8").tobytes()
        result = np.frombuffer(run([attack], data), "<f8").reshape(-1, 2, 4)
        return result[:, :, 2]

    def event(guard, time_s):
        data = np.r_[native[1], guard, time_s, 0., 0.].astype("<f8").tobytes()
        raw = run([native[0], "maybe"], data)
        return np.frombuffer(raw, "<f8") if raw else None

    result = render(evaluate, event, shape, post, initial, coupled, mode, path_projection)
    if result is None:
        return dict(passed=False, reason="no event within the supported interval")
    end = first + result["slot"] + 1
    reference = observations[first:end+1]
    timer = result["timer"]
    states = result["states"]
    assert reference.shape[0] == timer.shape[0] and np.isfinite(timer).all()
    error = abs(timer - reference[:, TIMER_NODES])
    tick = start * 4096 + ((end - 1) / CLOCK + result["crossing_s"]) / TICK_S
    current = evaluate(states[:, [0, 9]], timer[:-1])
    ref_attack = (reference[:-1, [8, 44]] - reference[:-1, TIMER_NODES]) / OHMS[:, 0]
    passive = (states[:, 10:14].reshape(-1, 2, 2) - timer[:-1, :, None]) / OHMS[:, 1:]
    ref_passive = ((reference[:-1, [11, 0, 47, 29]].reshape(-1, 2, 2)
                   - reference[:-1, TIMER_NODES, None]) / OHMS[:, 1:])
    current_error = np.concatenate((abs(current - ref_attack)[..., None], abs(passive - ref_passive)), axis=2)
    # The injected capacitor voltages at the original shifted anchor
    # precede the algebraic reinitialization of the reference ports.
    skip = int(shifted and first == 0)
    max_currents = current_error[skip:].max(axis=0)
    bracket = bool(expected[0] <= tick <= expected[1])
    result = dict(passed=bool(bracket and error.max() <= 2e-6 and max_currents.max() <= 2e-9),
                first_slot=first, historical_bracket=bracket, predicted_tick=float(tick),
                max_before_v=error[:-1].max(axis=0).tolist(), event_endpoint_v=error[-1].tolist(),
                end_timers_v=timer[-1].tolist(),
                max_current_error_a=max_currents.tolist(), current_gate=bool(max_currents.max() <= 2e-9),
                generated_before=states.shape[0],
                max_c4_v=float(abs(states[:, 1] - (reference[:-1, 23] - reference[:-1, 25])).max()),
                max_filter_decay_port_v=float(abs(states[:, 12] - reference[:-1, 47]).max()),
                output_sha256=c.digest(timer.astype("<f8").tobytes()),
                modeled_event_attack_a=result["attack"].tolist(), modeled_event_passive_v=result["passive"].tolist())
    if skip:
        result["anchor_algebraic_error_a"] = current_error[0].tolist()
    return result


def timer_native_fixture(prefix, shape, post, initial):
    from rf_d_pilot_timer_carry import PORTS
    phase, nominal, linear, quadratic, _ = shape
    table = np.column_stack((nominal.T, linear[0].T, linear[1].T, quadratic[0].T, quadratic[1].T))
    time, nominal, linear, quadratic, _ = post
    values = np.array([nominal, *linear, *quadratic])
    after = np.column_stack((time, *(row[1:-1].T for row in values), values[:, -1].T))
    return np.r_[prefix, phase, table.ravel(), after.ravel(), initial[[26, *NODES, *PORTS, 34]]].astype("<f8").tobytes()


def timer_native_trial(run, target, prefix, shape, post, initial, observations, start, expected, first, shifted, python, readout=None, audio=None):
    assert python["passed"]
    data = timer_native_fixture(prefix, shape, post, initial)
    raw = run([target], data)
    assert raw == run([target], data)
    got = np.frombuffer(raw, "<f8")
    assert len(got) >= 12 and np.isfinite(got).all()
    slot, seconds = got[:2]
    before = got[4:].reshape(-1, 8)
    end = first + int(slot) + 1
    assert slot == len(before) - 1
    reference = observations[first:end+1]
    tick = start * 4096 + ((end - 1) / CLOCK + seconds) / TICK_S
    error = abs(np.vstack((before[:, :2], got[2:4])) - reference[:, TIMER_NODES])
    r = reference[:-1, TIMER_NODES, None]
    ref_currents = (reference[:-1, [[8, 11, 0], [44, 47, 29]]] - r) / OHMS
    skip = int(shifted and first == 0)
    current = abs(before[:, 2:].reshape(-1, 2, 3) - ref_currents)[skip:].max(axis=0)
    end_delta = abs(got[2:4] - python["end_timers_v"]).max()
    assert abs(tick - python["predicted_tick"]) * TICK_S <= 1e-12 and end_delta <= 1e-10
    passed = expected[0] <= tick <= expected[1] and error.max() <= 2e-6 and current.max() <= 2e-9
    assert passed
    timing = list(map(int, run([target, "bench"], data).decode().strip().split(",")))
    item = dict(passed=bool(passed), predicted_tick=float(tick), max_before_v=error[:-1].max(axis=0).tolist(),
                event_endpoint_v=error[-1].tolist(), max_current_error_a=current.tolist(),
                max_event_difference_python_v=float(end_delta),
                input_sha256=c.digest(data), output_sha256=c.digest(raw),
                timing=dict(zip(("events", "median_ns", "p99_ns", "max_ns"), timing)))
    if readout is not None:
        command = [target, "returns"]
        with_sum = run(command, data)
        assert with_sum == run(command, data)
        extra = np.frombuffer(with_sum, "<f8")
        body = extra[5:].reshape(-1, 9)
        assert np.array_equal(extra[:4], got[:4]) and np.array_equal(body[:, :8], before)
        drives = np.vstack((body[:, [0, 8]], extra[[2, 4]]))
        item["returns"] = returns.assess(run, readout, reference, drives, skip)
        print("RETURN", start, first, item["returns"], flush=True)
        if audio is not None:
            item["audio_readout"] = audio.compare(first, drives)
            print("AUDIO", start, first, {key: (trial.get("error"), trial.get("max_error"))
                                         for key, trial in item["audio_readout"].items()
                                         if isinstance(trial, dict)}, flush=True)
    return item


def carried_fixture(prefix, model, initial):
    _, nominal, linear, quadratic, _ = model
    table = np.column_stack((nominal.T, linear[0].T, linear[1].T,
                             quadratic[0].T, quadratic[1].T))
    return np.r_[prefix, table.ravel(), initial[[26, *NODES]]].astype("<f8").tobytes()


def carried_native(run, target, prefix, model, initial, expected):
    data = carried_fixture(prefix, model, initial)
    raw = run([target], data)
    assert raw == run([target], data)
    got = np.frombuffer(raw, "<f8")
    oracle = carry_charge(model, initial, False)
    want = np.r_[oracle["slot"], oracle["time_s"], expected["event_time_s"],
                 expected["modeled_attack_a"], oracle["state"].ravel()]
    assert got.shape == want.shape and np.isfinite(got).all()
    difference = abs(got - want)
    assert difference[0] == 0 and difference[1:3].max() <= 1e-12 and difference[3:].max() <= 1e-10
    timing = list(map(int, run([target, "bench"], data).decode().strip().split(",")))
    return dict(passed=expected["passed"], max_error=difference[:4].tolist(),
                max_state_error_v=float(difference[4:].max()),
                input_sha256=c.digest(data), output_sha256=c.digest(raw),
                timing=dict(zip(("events", "median_ns", "p99_ns", "max_ns"), timing)))


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
    parser.add_argument("--carry-native", action="store_true", help="verify and time the stateful Rust C4 clock")
    parser.add_argument("--timers", action="store_true", help="advance C2 and C5 with generated currents and passive loads")
    parser.add_argument("--timer-grid-refine", action="store_true",
                        help="contrast startup-refined timer paths and pre-event load projection")
    parser.add_argument("--timers-native", action="store_true",
                        help="run the Rust timer carry and the reference C4 replay")
    parser.add_argument("--returns", action="store_true", help="contrast return readout at imposed receiver loads")
    parser.add_argument("--audio", action="store_true", help="close base and TAIL with the reduced audio receiver")
    parser.add_argument("--audio-joint", action="store_true", help="compare the joint and nested audio loops")
    args_main = parser.parse_args()
    assert not args_main.audio_joint or args_main.audio
    assert not args_main.audio or args_main.returns
    assert not args_main.returns or args_main.timers_native
    assert not args_main.timers_native or args_main.timer_grid_refine
    assert not args_main.timer_grid_refine or args_main.timers
    assert not args_main.carry_native or args_main.carry
    assert c.AREA.is_dir() and not list(c.AREA.iterdir())
    seq = 1
    prefix = "rf_d_pilot_audio_readout_pos" if args_main.audio else "rf_d_pilot_precursor"
    while (out := c.ROOT / f"evidence/{prefix}{seq:02}.json").exists():
        seq += 1
    previous = "evidence/rf_d_pilot_timer_rc10.json"
    native_sources = (NATIVE, NATIVE_PROBE) if args_main.native else ()
    if args_main.carry:
        native_sources += (ATTACK_PROBE, MODEL)
    if args_main.carry_native:
        native_sources += (C4_CLOCK, C4_PROBE, NATIVE)
    if args_main.timers:
        native_sources += (TIMER_CARRY, ATTACK_PROBE, MODEL)
    if args_main.timers_native:
        native_sources += (TIMER_NATIVE, TIMER_NATIVE_PROBE, C4_CLOCK, NATIVE)
    if args_main.returns:
        native_sources += ("tools/rf_d_pilot_return_readout.py", *returns.SOURCES)
    if args_main.audio:
        import rf_d_pilot_audio_readout as audio
        native_sources += audio.SOURCES
    sources = Sources((*c.ALL_SOURCES, c.OWN, c.CANDIDATE, c.PROBE, c.PORTS,
                       "tools/rf_d_pilot_step_profile.rs", previous, *SOURCE_NAMES, *native_sources))
    report = dict(passed=False, rack_integrated=False, clock_hz=CLOCK, native=args_main.native, carry=args_main.carry, carry_native=args_main.carry_native, timers=args_main.timers, timer_grid_refine=args_main.timer_grid_refine, timers_native=args_main.timers_native, calibration=[],
                  returns=args_main.returns, reserves={}, **sources.fields(), compiler_sha256=c.sha(Path(c.COMPILER)),
                  library_sha256=c.sha(c.LIB))
    env = dict(os.environ, PATH="C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;" + os.environ["PATH"])

    def run(command, data=None):
        proc = subprocess.run(list(map(str, command)), cwd=c.ROOT, env=env, input=data,
                              capture_output=True, timeout=240)
        assert proc.returncode == 0, proc.stderr.decode(errors="replace")
        return proc.stdout

    try:
        refs, report["reference_inputs"] = c.references()
        exe, build = prepare_reference(run, report, args_main.audio)
        native = c.AREA / "pilot-crossing.exe"
        run([*build, "-A", "dead_code", c.ROOT / CROSSING_PROBE, "--extern",
             f"rf_d_circuit={c.LIB}", "-o", native])
        native_guard = c.AREA / "pilot-precursor.exe"
        if args_main.native:
            run([*build, "-A", "dead_code", c.ROOT / NATIVE_PROBE, "--extern",
                 f"rf_d_circuit={c.LIB}", "-o", native_guard])
        attack = c.AREA / "pilot-attack.exe"
        if args_main.carry or args_main.timers:
            run([*build, "-A", "dead_code", c.ROOT / ATTACK_PROBE, "-o", attack])
        clock = c.AREA / "pilot-c4-clock.exe"
        if args_main.carry_native:
            run([*build, "-A", "dead_code", c.ROOT / C4_PROBE, "--extern",
                 f"rf_d_circuit={c.LIB}", "-o", clock])
        native_timer = c.AREA / "pilot-timer-carry.exe"
        if args_main.timers_native:
            run([*build, "-A", "dead_code", c.ROOT / TIMER_NATIVE_PROBE, "--extern",
                 f"rf_d_circuit={c.LIB}", "-o", native_timer])
        readout = returns.prepare(run, build) if args_main.returns else None
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
        if args_main.timers:
            from rf_d_pilot_timer_carry import PORTS, post_family, post_trace
            timer_paths, post_paths = [], []
            native_paths, native_post = [], []
        for offset in CALIBRATION:
            stages, item = capture("positive", start, frames, key, offset)
            report["calibration"].append(item)
            paths.append(trace(stages))
            if args_main.carry:
                charge_paths.append(charge_trace(stages))
            if args_main.timers:
                timer_paths.append(charge_trace(stages, PORTS))
                slot, _, at = timing_reference(stages)
                time, values = post_trace(stages, slot / CLOCK + at["time"], STEPS, (34,))
                post_paths.append((time, values[:-1]))
                if args_main.timers_native:
                    native_paths.append(charge_trace(stages, (*PORTS, 34)))
                    native_post.append((time, values))
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
        if args_main.timers:
            timer_shape = charge_family(timer_paths)
            timer_mid = charge_family(timer_paths, 129)
            timer_dense = charge_family(timer_paths, 257)
            post_shape = post_family(post_paths)
            timer_modes = (("held", timer_shape, False, "hold", False),
                           ("axis", timer_shape, False, "projected", False),
                           ("coupled", timer_shape, True, "projected", False),
                           ("path", timer_shape, False, "projected", True),
                           ("path129", timer_mid, False, "projected", True),
                           ("path257", timer_dense, False, "projected", True))
            if args_main.timer_grid_refine:
                quarter = np.r_[np.arange(64) / 256., np.arange(32, 129) / 128.]
                half = np.r_[np.arange(128) / 256., np.arange(64, 129) / 128.]
                grid25 = charge_family(timer_paths, quarter)
                grid50 = charge_family(timer_paths, half)
                timer_modes = (
                    ("path257", timer_dense, False, "projected", True),
                    ("event257", timer_dense, False, "projected_path", True),
                    ("startup25", grid25, False, "projected", True),
                    ("startup50", grid50, False, "projected", True),
                    ("startup25_event", grid25, False, "projected_path", True),
                    ("startup50_event", grid50, False, "projected_path", True),
                )
                if args_main.timers_native:
                    timer_modes = (timer_modes[-2],)
                    native_grid = charge_family(native_paths, quarter)
                    native_after = post_family(native_post)
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
                if args_main.carry_native:
                    item["carried_native"] = [
                        carried_native(run, clock, native_args[1], phase_model, observations[i], result)
                        for i, result in enumerate(trials["q65_axis"])]
                    print("NATIVE_CARRY", name, item["carried_native"], flush=True)
                print("CARRY", name, {mode: [(x.get("time_error_ns"), x.get("c2_event_error_v"), x["passed"])
                                            for x in group] for mode, group in trials.items()}, flush=True)
            if args_main.timers:
                timers = item["own_timers"] = {}
                for mode, model_timers, coupled, strategy, path_projection in timer_modes:
                    timers[mode] = []
                    for first in range(2):
                        args = (run, native_args, attack, model_timers, post_shape, observations[first],
                                observations, start, expected, first, coupled, strategy, path_projection, any(offset))
                        result = timer_trial(*args)
                        assert result == timer_trial(*args)
                        timers[mode].append(result)
                if args_main.timers_native:
                    audio_case = None
                    if args_main.audio:
                        phase, _, _, state = refs["positive"][1][start]
                        state = state.copy()
                        state[0, TIMER_NODES] += offset
                        audio_case = audio.Case(exe, env, state, phase, stages, args_main.audio_joint)
                    item["native_timers"] = [
                        timer_native_trial(run, native_timer, native_args[1], native_grid, native_after,
                                           observations[i], observations, start, expected, i, any(offset), result, readout, audio_case)
                        for i, result in enumerate(timers["startup25_event"])]
                    print("NATIVE_TIMERS", name, item["native_timers"], flush=True)
                print("OWN_TIMERS", name,
                      {mode: [(x.get("max_before_v"), x.get("event_endpoint_v"),
                               x.get("current_gate"), x["passed"]) for x in group]
                       for mode, group in timers.items()}, flush=True)
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
            if args_main.carry_native:
                data = carried_fixture(native_args[1], phase_model, observations[0])
                item["native_false_carried"] = bool(run([clock], data))
                assert not item["native_false_carried"]
            if args_main.timers_native:
                data = timer_native_fixture(native_args[1], native_grid, native_after, observations[0])
                item["native_false_timer_event"] = bool(run([native_timer], data))
                assert not item["native_false_timer_event"]
            report["reserves"][label] = item
        report["passed"] = True
        report["modes_admitted_in_bank"] = [label for label, *_ in cases
                                            if all(report["reserves"][name]["modes"][label]["passed"]
                                                   for name in NAMES)]
        if args_main.carry:
            report["carried_modes_admitted"] = [
                mode for mode, _, _ in carry_modes
                if all(report["reserves"][name]["carried"][mode][0]["passed"] for name in NAMES)]
        if args_main.timers:
            report["own_timer_modes_admitted"] = [
                mode for mode, *_ in timer_modes
                if all(trial["passed"] for name in NAMES for trial in report["reserves"][name]["own_timers"][mode])]
        if args_main.returns:
            report["return_readout_passed"] = all(
                trial["returns"]["passed"] for name in NAMES for trial in report["reserves"][name]["native_timers"])
            report["passed"] &= report["return_readout_passed"]
        if args_main.audio:
            report["audio_readout_passed"] = all(
                trial["audio_readout"]["passed"] for name in NAMES for trial in report["reserves"][name]["native_timers"])
            report["passed"] &= report["audio_readout_passed"]
        sources.unchanged()
    except Exception:
        report["failure"] = traceback.format_exc()
        raise
    finally:
        for path in c.AREA.iterdir():
            assert path.is_file() and path.resolve().parent == c.AREA.resolve()
            path.unlink()
        c.write(out, report)
    if args_main.audio and not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
