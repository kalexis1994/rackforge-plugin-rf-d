"""Contrast the fixed-cost C2/C5 update with the full circuit, at imposed loads."""
import argparse
import os
import subprocess
import traceback
from pathlib import Path

import numpy as np

from affine_evidence import Sources
import check_rf_d_pilot_contours as c

OWN = "tools/check_rf_d_pilot_timer_rc.py"
MODEL = "tools/rf_d_pilot_timer_rc.rs"
PROBE = "tools/rf_d_pilot_timer_rc_probe.rs"
DOC = "docs/VOZ_PILOTO_RETORNOS_PROTOCOLO.md"
ATTACK = "tools/rf_d_pilot_attack_cell.rs"
ATTACK_PROBE = "tools/rf_d_pilot_attack_cell_probe.rs"
ATTACK_ORBIT = "tools/rf_d_pilot_attack_orbit.py"
CROSSING = "tools/rf_d_pilot_crossing.rs"
CROSSING_PROBE = "tools/rf_d_pilot_crossing_probe.rs"
LATCH_CHARGE = "tools/latch_charge_driver.rs"
ORBIT_RESERVES = (("positive_c2_up", "positive", 76, 5, 0., (+.05, -.05)),
                  ("positive_c2_down", "positive", 76, 5, 0., (-.05, +.05)))
ATTACK_INPUTS = [[26, 5], [40, 38]]
ATTACK_BASES = [6, 43]
ATTACK_COLLECTOR_OHM = [1100., 100.]
TIMER_NODES = [5, 38]
LOAD_NODES = [[8, 11, 0], [44, 47, 29]]
OHMS = np.array([[1_000, 10_000, 10_000], [100, 1_000, 10_000]])
TIMER_LIMIT_V = 20e-6
LOAD_LIMIT_A = 2e-9
FINE_TICKS = 8
HALF_FRAME_TICKS = 2048


def fixture(first, ticks, loads):
    return np.r_[first, np.column_stack((ticks, loads.reshape(-1, 6))).ravel()].astype("<f8").tobytes()


def project_loads(stages, first_path=0, ticks=FINE_TICKS):
    """Project the selected load ports with their summed conductance."""
    stage_values = stages[1:, np.array(LOAD_NODES)[:, first_path:]]
    conductance = (1. / OHMS[:, first_path:]).sum(axis=1)
    return project_stages(stage_values, conductance, ticks)


def project_stages(stage_values, conductance, ticks):
    steps = round(HALF_FRAME_TICKS / ticks)
    x = conductance * ticks / (10e-6 * 48_000 * 4096)
    # The original fine oracle uses two-stage Radau. Its final row weights
    # the two load stages in the ratio 4.5:(1.5+x) for this linear network.
    w1 = 4.5 / (6. + x)
    stage_loads = stage_values.reshape(-1, steps, 2, *stage_values.shape[1:])
    local = w1[:, None] * stage_loads[:, :, 0] + (1. - w1[:, None]) * stage_loads[:, :, 1]
    age = np.arange(steps - 1, -1, -1)
    weights = np.exp(-age[:, None] * x)
    weights /= weights.sum(axis=0)
    return np.einsum("st,bstp->btp", weights, local)


def replay(run, target, nodes, indices, projected=None):
    sample = nodes[indices]
    loads = sample[:, LOAD_NODES]
    timers = sample[:, TIMER_NODES]
    held = projected is not None
    data = fixture(np.r_[timers[0], loads[0].ravel()], FINE_TICKS * np.diff(indices),
                   projected if held else loads[1:])
    cmd = [target, "held"] if held else [target]
    return timer_result(run, cmd, data, timers[1:])


def timer_result(run, cmd, data, expected):
    raw = run(cmd, data)
    got = np.frombuffer(raw, "<f8").reshape(-1, 2)
    assert got.shape == expected.shape and np.isfinite(got).all()
    error = abs(got - expected)
    peak = error.max(axis=0)
    # The reference loads are imposed. This reports the change in the six
    # resistor currents due to the timer update with those loads held equal.
    peak_load = peak[:, None] / OHMS
    passes = bool(peak.max() <= TIMER_LIMIT_V and peak_load.max() <= LOAD_LIMIT_A)
    item = dict(passed=passes, max_timer_error_v=peak.tolist(), max_load_error_a=peak_load.tolist(),
                intervals=len(got), input_sha256=c.digest(data), output_sha256=c.digest(raw))
    if not passes:
        assert run(cmd, data) == raw
        item["unchanged_replay"] = True
    return item


def current_fixture(initial, inputs):
    return np.r_[initial, inputs.ravel()].astype("<f8").tobytes()


def attack_fixture(nodes):
    return nodes[:, ATTACK_INPUTS].astype("<f8").tobytes()


def attack_results(run, target, stages, changed=False):
    data = attack_fixture(stages)
    raw = run([target], data)
    ports = np.frombuffer(raw, "<f8").reshape(-1, 2, 4)
    assert len(ports) == len(stages) and np.isfinite(ports).all()
    timer = stages[:, TIMER_NODES]
    port = stages[:, np.array(LOAD_NODES)[:, 0]]
    base = stages[:, ATTACK_BASES]
    control = stages[:, np.array(ATTACK_INPUTS)[:, 0]]
    ref = np.stack((base, port, (port - timer) / OHMS[:, 0],
                    (base - control) / 3300.), axis=2)
    error = abs(ports - ref)
    peak = error[int(changed):].max(axis=0)
    passes = bool(peak[:, :2].max() <= TIMER_LIMIT_V and peak[:, 2:].max() <= LOAD_LIMIT_A)
    item = dict(passed=passes, stages=len(ports), max_error=peak.tolist(),
                input_sha256=c.digest(data), output_sha256=c.digest(raw))
    if changed:
        item["anchor_algebraic_error"] = error[0].tolist()
    if not passes:
        assert run([target], data) == raw
        item["unchanged_replay"] = True
    return ports, item


def crossing_charge(ports, stages, regular, changes, orbit=None, ticks=FINE_TICKS,
                    predict=False, native=None):
    """Separate a two-level current model from the need to locate the event."""
    assert len(changes) == 1
    capacitance = 10e-6
    conductance = 1. / OHMS[:, 1:]
    total = conductance.sum(axis=1)
    x = total / (96_000 * capacitance)
    moved = -np.expm1(-x)
    end_weight = (1. - moved / x) / moved
    other = project_loads(stages, first_path=1, ticks=ticks)
    exact_current = project_stages(ports[1:, :, 2, None], total, ticks)[:, :, 0]
    endpoints = ports[regular * 2, :, 2]
    affine_current = endpoints[:-1] + end_weight * np.diff(endpoints, axis=0)
    change = int(changes[0])
    slot = int(np.searchsorted(regular, change, side="right") - 1)
    width = int(regular[slot+1] - regular[slot])
    bracket = (np.array([change, change + 1]) - regular[slot]) / width
    fraction = bracket.mean()
    # Extend the preceding and following 96 kHz ramps into the event interval.
    # The bracket and slopes come from the reference in this diagnostic.
    pre = endpoints[slot]
    post = endpoints[slot+1]
    pre_slope = endpoints[slot] - endpoints[slot-1]
    post_slope = endpoints[slot+2] - endpoints[slot+1]

    def moment(t):
        return np.expm1(x * t) * np.exp(-x) / moved

    def first_moment(t):
        return (x * t * np.exp(x * t) - np.expm1(x * t)) * np.exp(-x) / (x * moved)

    def split_ramps(f):
        before = moment(f)
        weighted_time = first_moment(f)
        return (before * pre + (1. - before) * post
                + weighted_time * pre_slope
                + (end_weight - weighted_time - (1. - before)) * post_slope)

    at_event = affine_current.copy()
    at_event[slot] = split_ramps(fraction)
    # Recover the area-equivalent event time for volume only. The result is
    # a diagnostic of a step-plus-ramps surrogate, not a time estimate at runtime.
    lo, hi = 0., 1.
    assert split_ramps(lo)[0] < exact_current[slot, 0] < split_ramps(hi)[0]
    for _ in range(48):
        middle = (lo + hi) / 2.
        if split_ramps(middle)[0] < exact_current[slot, 0]:
            lo = middle
        else:
            hi = middle
    effective = (lo + hi) / 2.
    at_effective = at_event.copy()
    at_effective[slot, 0] = split_ramps(effective)[0]

    expected = stages[regular * 2][:, TIMER_NODES]
    def error(current):
        state = expected[0].copy()
        errors = []
        for i, (attack, loads) in enumerate(zip(current, other)):
            state += moved / total * (attack + ((loads - state[:, None]) * conductance).sum(axis=1))
            errors.append(abs(state - expected[i+1]))
        peak = np.asarray(errors).max(axis=0)
        load_error = peak[:, None] / OHMS
        return dict(passed=bool(peak.max() <= TIMER_LIMIT_V and load_error.max() <= LOAD_LIMIT_A),
                    max_timer_error_v=peak.tolist(), max_load_error_a=load_error.tolist())

    ideal = error(exact_current)
    assert ideal["passed"]
    report = dict(oracle_projected=ideal, coarse_affine=error(affine_current),
                split_reference_crossing=error(at_event), split_area_equivalent=error(at_effective),
                event_interval=int(slot), reference_fraction=bracket.tolist(),
                area_equivalent_fraction=float(effective),
                area_equivalent_minus_crossing_ns=float((effective - fraction) * 1e9 / 96_000),
                effective_attack_a=exact_current[slot].tolist(),
                predicted_attack_at_reference_event_a=at_event[slot].tolist())
    if orbit is not None:
        from rf_d_pilot_attack_orbit import attack_area, extract
        evaluate, saved = orbit
        local = stages[2 * regular[slot]:2 * regular[slot+1] + 1]
        target = extract(local, width)
        if not saved:
            saved.append(target)
        anchor = target["time"] * 96_000
        base = split_ramps(anchor)
        report["collector_orbit"] = dict(crossing_s=target["time"], crossing_v=target["bounds"][1],
                                         modes={})
        for source_name, source in (("local_landmarks", target), ("nominal_shape", saved[0])):
            trials = report["collector_orbit"]["modes"][source_name] = {}
            for points in (4, 8, 16, 24, 32):
                for post_only in (False, True):
                    trial = attack_area(target, source, points, evaluate, x[0], pre[0], post[0],
                                        pre_slope[0], post_slope[0], post_only=post_only)
                    if "correction_a" in trial:
                        mean = at_event.copy()
                        mean[slot, 0] = base[0] + trial["correction_a"]
                        trial.update(error(mean), modeled_attack_a=float(mean[slot, 0]),
                                     reference_attack_a=float(exact_current[slot, 0]))
                    trials[f"{points}_tail" if post_only else str(points)] = trial
        if predict:
            from rf_d_pilot_attack_orbit import GUARDS, crossing_profile, guard_sample, predict_crossing

            profile = crossing_profile(saved[0])
            endpoints = stages[::2]
            predictions = report["crossing_predictions"] = {}
            tick_s = 1. / (48_000 * 4096)
            reference_s = regular[slot] * ticks * tick_s + target["time"]
            for threshold in GUARDS:
                candidate = predictions[str(threshold)] = {}
                guard = guard_sample(endpoints, threshold)
                if guard is None:
                    candidate.update(reason="no pre-crossing guard observation")
                    continue
                for mode, slope in (("offset", False), ("slope", True)):
                    trial = predict_crossing(profile, endpoints[guard-1], endpoints[guard],
                                              guard * ticks * tick_s, evaluate, slope)
                    candidate[mode] = trial
                    trial["guard_tick"] = float(guard * ticks)
                    if "time" not in trial:
                        continue
                    local_time = trial["time"] - regular[slot] * ticks * tick_s
                    predicted_state = np.asarray(trial["crossing"])
                    trial.update(predicted_tick=float(trial["time"] / tick_s),
                                 time_error_ns=float((trial["time"] - reference_s) * 1e9),
                                 guard_lead_ns=float((reference_s - guard * ticks * tick_s) * 1e9),
                                 state_error_v=abs(predicted_state - target["crossing"]).tolist(),
                                 refined_bracket=bool(change * ticks <= trial["time"] / tick_s
                                                      <= (change + 1) * ticks))
                    if not 0. <= local_time * 96_000 <= 1.:
                        continue
                    predicted = dict(target, bounds=[target["bounds"][0], trial["collector_v"],
                                                      target["bounds"][2]],
                                     time=local_time, crossing=predicted_state)
                    tail = attack_area(predicted, saved[0], 24, evaluate, x[0], pre[0], post[0],
                                       pre_slope[0], post_slope[0], post_only=True)
                    if "correction_a" in tail:
                        mean = at_event.copy()
                        mean[slot, 0] = split_ramps(local_time * 96_000)[0] + tail["correction_a"]
                        tail.update(error(mean))
                    trial["tail"] = tail
                    if native is not None and threshold == .35 and mode == "offset":
                        from rf_d_pilot_attack_orbit import landmarks

                        run, executable, fixtures = native
                        _, tail_knots = landmarks(saved[0], 24)
                        rising = np.column_stack(profile)
                        observation = endpoints[guard, [26, 25, 27, 9, 5, 28]]
                        guard_s = (guard - regular[slot]) * ticks * tick_s
                        data = np.r_[rising.ravel(), tail_knots[24:].ravel(), observation, guard_s,
                                     post[0], post_slope[0]].astype("<f8").tobytes()
                        digest = c.digest(data)
                        fixtures[digest] = data
                        result = run([executable], data)
                        got = np.frombuffer(result, "<f8")
                        assert got.shape == (7,) and np.isfinite(got).all()
                        expected_native = np.r_[local_time, trial["collector_v"],
                                                predicted_state, tail["correction_a"]]
                        diff = abs(got - expected_native)
                        assert diff[0] <= 1e-12 and diff[1:6].max() <= 1e-10 and diff[6] <= 1e-10
                        mean = at_event.copy()
                        mean[slot, 0] = split_ramps(got[0] * 96_000)[0] + got[6]
                        report["native_event"] = dict(
                            error(mean), max_error_against_python=diff.tolist(),
                            predicted_tick=float(regular[slot] * ticks + got[0] / tick_s),
                            input_sha256=digest, output_sha256=c.digest(result))
    return report


def attack_sweep(run, target):
    collector, timer = np.meshgrid(np.linspace(0., 9.3, 151), np.linspace(0., 8., 81))
    inputs = np.tile(np.column_stack((collector.ravel(), timer.ravel())), (1, 2))
    data = inputs.astype("<f8").tobytes()
    raw = run([target], data)
    base, timer_port, into_timer, into_latch = np.frombuffer(raw, "<f8").reshape(-1, 2, 4).transpose(2, 0, 1)
    collector = collector.reshape(-1, 1)
    timer = timer.reshape(-1, 1)
    junction_collector = timer + ATTACK_COLLECTOR_OHM * into_timer
    vt = 1.380649e-23 * 298.15 / 1.602176634e-19
    forward = 1e-14 * np.expm1((9.3 - base) / vt)
    reverse = 1e-14 * np.expm1((junction_collector - base) / vt)
    base_kcl = (base - 9.3) / 560. + into_latch - forward / 100. - reverse / 5.
    collector_kcl = into_timer - forward + 1.2 * reverse
    port_kcl = (timer_port - timer) / OHMS[:, 0] - into_timer
    latch_kcl = (base - collector) / 3300. - into_latch
    peak = [float(abs(x).max()) for x in (base_kcl, collector_kcl, port_kcl, latch_kcl)]
    return dict(passed=max(peak) <= 2e-13, points_per_cell=len(inputs), max_kcl_a=peak,
                input_sha256=c.digest(data), output_sha256=c.digest(raw))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attack-cells", action="store_true",
                        help="generate the attack branches from latch and timer voltages")
    parser.add_argument("--crossing-charge", action="store_true",
                        help="diagnose current area versus the eight-tick reference event")
    parser.add_argument("--collector-orbit", action="store_true",
                        help="evaluate a sparse collector KCL path on nominal and loaded reserves")
    parser.add_argument("--refine-orbit", action="store_true",
                        help="repeat the collector comparison at one-third the reference step")
    parser.add_argument("--predict-crossing", action="store_true",
                        help="derive the event from a pre-crossing collector observation")
    parser.add_argument("--native-crossing", action="store_true",
                        help="contrast and time the fixed-budget Rust event kernel")
    args = parser.parse_args()
    assert not args.native_crossing or args.predict_crossing
    assert not args.predict_crossing or args.refine_orbit
    assert not args.refine_orbit or args.collector_orbit
    assert not args.crossing_charge or args.attack_cells
    assert not args.collector_orbit or args.crossing_charge
    assert c.AREA.is_dir() and not list(c.AREA.iterdir())
    seq = 1
    while (out := c.ROOT / f"evidence/rf_d_pilot_timer_rc{seq:02}.json").exists():
        seq += 1
    added_sources = (ATTACK, ATTACK_PROBE) if args.attack_cells else ()
    if args.collector_orbit:
        added_sources += (ATTACK_ORBIT,)
    if args.native_crossing:
        added_sources += (CROSSING, CROSSING_PROBE, LATCH_CHARGE)
    sources = Sources((*c.ALL_SOURCES, c.OWN, c.CANDIDATE, c.PROBE, c.PORTS,
                       "tools/rf_d_pilot_step_profile.rs", OWN, MODEL, PROBE, DOC, *added_sources))
    report = dict(passed=False, coupled=False, rack_integrated=False, clock_hz=96_000,
                  timer_nodes=TIMER_NODES, load_nodes=LOAD_NODES, load_ohms=OHMS.tolist(),
                  timer_limit_v=TIMER_LIMIT_V, load_limit_a=LOAD_LIMIT_A,
                  attack_cells=args.attack_cells, crossing_charge=args.crossing_charge,
                  collector_orbit=args.collector_orbit, refine_orbit=args.refine_orbit,
                  predict_crossing=args.predict_crossing, native_crossing=args.native_crossing, windows={}, **sources.fields(), compiler_sha256=c.sha(Path(c.COMPILER)),
                  library_sha256=c.sha(c.LIB))
    env = dict(os.environ, PATH="C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;" + os.environ["PATH"])

    def run(command, data=None):
        proc = subprocess.run(list(map(str, command)), cwd=c.ROOT, env=env, input=data,
                              capture_output=True, timeout=240)
        assert proc.returncode == 0, proc.stderr.decode(errors="replace")
        return proc.stdout

    try:
        references, report["reference_inputs"] = c.references()
        table, *_ = c.materialize(c.read_oracle())
        table_path = c.AREA / c.TABLE
        report["table_sha256"] = c.digest(table)
        assert report["table_sha256"] == c.read(c.MODEL)["table_sha256"]
        table_path.write_bytes(table)
        kernel = c.emit("family-kernel.rs", c.text(c.KERNEL)
                        .replace("H128_VOICE_TABLE_PATH", table_path.as_posix())
                        .replace("VCO_PANEL_PORT_PATH", (c.ROOT / c.PANEL).as_posix()))
        exe, timer = (c.AREA / name for name in ("pilot-reference.exe", "pilot-timer.exe"))
        build = [c.COMPILER, "--edition=2021", "-C", "opt-level=3", "-C", "target-feature=+fma"]
        run([*build, "-C", "link-arg=-Wl,--stack,33554432", "--cfg", "laboratory",
             "--cfg", "pilot_loaded_filter", "-A", "dead_code", c.component(kernel),
             "--extern", f"rf_d_circuit={c.LIB}", "-o", exe])
        run([*build, "-A", "dead_code", c.ROOT / PROBE, "-o", timer])
        if args.attack_cells:
            attack = c.AREA / "pilot-attack-cells.exe"
            run([*build, c.ROOT / ATTACK_PROBE, "-o", attack])
            report["attack_sweep"] = attack_sweep(run, attack)
        anchor = c.AREA / "timer-anchor.bin"
        archived = c.read(c.CLOCK)["trials"]["positive"]["64"]["expected_brackets"]
        windows = [(*case, (0., 0.)) for case in c.WINDOWS]
        if args.collector_orbit:
            windows.extend(ORBIT_RESERVES)
        saved_orbits = []
        refined_orbits = []
        native = None
        if args.native_crossing:
            executable = c.AREA / "pilot-crossing.exe"
            run([*build, "-A", "dead_code", c.ROOT / CROSSING_PROBE, "--extern",
                 f"rf_d_circuit={c.LIB}", "-o", executable])
            native = (run, executable, {})

        def evaluate_volume(collector, capacitor):
            data = np.column_stack((collector, capacitor, np.full_like(collector, 8.3), capacitor)).astype("<f8")
            raw = run([attack], data.tobytes())
            return np.frombuffer(raw, "<f8").reshape(-1, 2, 4)[:, 0, :]

        for label, branch, start, frames, key, offset in windows:
            phase, _, _, state = references[branch][1][start]
            changed = any(offset)
            if changed:
                state = state.copy()
                state[0, TIMER_NODES] += offset
            anchor.write_bytes(np.asarray(np.r_[state.ravel(), phase], "<f8").tobytes())
            raw = run([exe, "contour-capture", anchor, start, frames, key])
            stages = np.frombuffer(raw, "<f8").reshape(-1, c.N)
            assert stages.shape[0] == 1 + frames * 1024 and np.isfinite(stages).all()
            nodes = stages[::2]
            assert np.array_equal(nodes[0], state.sum(axis=0))
            signs = nodes[:, 26] >= nodes[:, 28]
            changes = np.flatnonzero(signs[1:] != signs[:-1])
            base = start * 4096
            events = [[base + 8 * int(i), base + 8 * int(i + 1), int(signs[i + 1])] for i in changes]
            expected = [[lo, hi, sign] for pair, lo, hi, sign in archived if pair == 0] if branch == "positive" else []
            if changed:
                assert len(events) == 1 and events[0][-1] == 1, events
            else:
                assert events == expected
            regular = np.arange(0, len(nodes), HALF_FRAME_TICKS // FINE_TICKS)
            modes = dict(fine_affine=np.arange(len(nodes)), fixed_affine=regular,
                         split_at_reference_bracket=np.unique(np.r_[regular, changes, changes + 1]))
            results = {mode: replay(run, timer, nodes, indices) for mode, indices in modes.items()}
            projected = project_loads(stages)
            results["projected_hold"] = replay(run, timer, nodes, regular, projected)
            item = report["windows"][label] = dict(anchor_sha256=c.sha(anchor), reference_sha256=c.digest(raw),
                                             reference_events=events, capacitor_offset_v=offset, key_v=key, start_frame=start,
                                             frames=frames, modes=results)
            if args.predict_crossing and not events:
                from rf_d_pilot_attack_orbit import GUARDS, guard_sample
                item["false_guard"] = any(guard_sample(nodes, threshold) is not None for threshold in GUARDS)
                assert not item["false_guard"]
            if args.attack_cells:
                ports, item["attack_ports"] = attack_results(run, attack, stages, changed)
                mixed = stages.copy()
                mixed[:, np.array(LOAD_NODES)[:, 0]] = ports[:, :, 1]
                generated = project_loads(mixed)
                results["generated_attack_projection"] = replay(run, timer, nodes, regular, generated)
                # A separate check on a causal held boundary per interval.
                # Only the two generated attack voltages differ from the
                # ideal projection of the original six loads.
                held = projected.copy()
                held[:, :, 0] = ports[regular[:-1] * 2, :, 1]
                results["generated_attack_held_at_start"] = replay(run, timer, nodes, regular, held)
                controls = nodes[regular[:-1]][:, np.array(ATTACK_INPUTS)[:, 0], None]
                inputs = np.concatenate((controls, project_loads(stages, first_path=1)), axis=2)
                initial = nodes[0, TIMER_NODES]
                data = current_fixture(initial, inputs)
                results["generated_attack_current"] = timer_result(
                    run, [attack, "current"], data, nodes[regular[1:]][:, TIMER_NODES])
                if args.crossing_charge and len(changes):
                    orbit = (evaluate_volume, saved_orbits) if args.collector_orbit else None
                    charge = crossing_charge(ports, stages, regular, changes, orbit)
                    assert charge == crossing_charge(ports, stages, regular, changes, orbit)
                    item["crossing_charge"] = dict(charge, unchanged_replay=True)
                    if args.refine_orbit:
                        refined = run([exe, "contour-capture-refined", anchor, start, frames, key])
                        fine = np.frombuffer(refined, "<f8").reshape(-1, c.N)
                        assert fine.shape[0] == 1 + frames * 3072 and np.isfinite(fine).all()
                        signs = fine[::2, 26] >= fine[::2, 28]
                        edges = np.flatnonzero(signs[1:] != signs[:-1])
                        assert len(edges) == 1 and signs[edges[0] + 1]
                        fine_ports, fine_check = attack_results(run, attack, fine, changed)
                        assert fine_check["passed"]
                        args_fine = (fine_ports, fine, 3 * regular, edges,
                                     (evaluate_volume, refined_orbits), FINE_TICKS / 3, args.predict_crossing, native)
                        refined_charge = crossing_charge(*args_fine)
                        assert refined_charge == crossing_charge(*args_fine)
                        item["refined_crossing_charge"] = dict(
                            sha256=c.digest(refined), metrics=refined_charge, unchanged_replay=True,
                            bracket_ticks=[base + FINE_TICKS / 3 * (int(edges[0]) + k) for k in (0, 1)])
                        lo, hi = item["refined_crossing_charge"]["bracket_ticks"]
                        assert events[0][0] <= lo < hi <= events[0][1]
                        if args.native_crossing:
                            event = refined_charge["native_event"]
                            tick = base + event["predicted_tick"]
                            event["historical_bracket"] = events[0][0] <= tick <= events[0][1]
                            assert event["passed"] and event["historical_bracket"]
                            data = native[2][event["input_sha256"]]
                            cost = list(map(int, run([native[1], "bench"], data).decode().strip().split(",")))
                            event["isolated_timing"] = dict(zip(("events", "median_ns", "p99_ns", "max_ns"), cost))
                            print("NATIVE_EVENT", label, event, flush=True)
                        if args.predict_crossing:
                            prediction = refined_charge["crossing_predictions"]
                            for modes in prediction.values():
                                for trial in modes.values():
                                    if isinstance(trial, dict) and "predicted_tick" in trial:
                                        trial["historical_bracket"] = (
                                            events[0][0] <= base + trial["predicted_tick"] <= events[0][1])
                            print("PREDICT", label,
                                  {guard: {mode: (round(trial["time_error_ns"], 2),
                                                  trial["historical_bracket"],
                                                  trial.get("tail", {}).get("passed"))
                                           if "time_error_ns" in trial else trial.get("reason")
                                           for mode, trial in modes.items() if isinstance(trial, dict)}
                                   for guard, modes in prediction.items()}, flush=True)
                    if args.collector_orbit and not args.predict_crossing:
                        for tag, result in (("8tick", charge),
                                            ("refined", item.get("refined_crossing_charge", {}).get("metrics"))):
                            if result is not None:
                                modes = result["collector_orbit"]["modes"]
                                print("ORBIT", label, tag, {key: {name: item.get("max_timer_error_v", item.get("reason"))
                                                                 for name, item in trials.items()}
                                                           for key, trials in modes.items()}, flush=True)
                    elif not args.predict_crossing:
                        print("CROSSING_CHARGE", charge, flush=True)
                print(label, item["attack_ports"]["passed"], results["generated_attack_projection"]["passed"],
                      results["generated_attack_current"], flush=True)
            else:
                print(label, results, flush=True)
            if branch == "positive" and not changed:
                loads = nodes[regular][:, LOAD_NODES]
                bench_ports = np.tile(projected, (256 // len(projected) + 1, 1, 1))[:256]
                data = fixture(np.r_[nodes[0, TIMER_NODES], loads[0].ravel()],
                               np.full(256, HALF_FRAME_TICKS), bench_ports)
                measurements = list(map(int, run([timer, "bench-held"], data).decode().strip().split(",")))
                if args.attack_cells:
                    branch_data = np.tile(nodes[regular][:-1, ATTACK_INPUTS], (26, 1, 1))[:256].astype("<f8").tobytes()
                    cell_cost = list(map(int, run([attack, "bench"], branch_data).decode().strip().split(",")))
                    report["attack_benchmark"] = dict(
                        zip(("blocks", "median_ns", "p99_ns", "max_ns"), cell_cost),
                        host_frames=128, input_sha256=c.digest(branch_data), includes_audio=False)
                    bench_data = current_fixture(initial, np.tile(inputs, (26, 1, 1))[:256])
                    combined = list(map(int, run([attack, "bench-current"], bench_data).decode().strip().split(",")))
                    report["attack_timer_benchmark"] = dict(
                        zip(("blocks", "median_ns", "p99_ns", "max_ns"), combined),
                        host_frames=128, input_sha256=c.digest(bench_data), includes_audio=False)
                report["isolated_timer_benchmark"] = dict(
                    zip(("blocks", "median_ns", "p99_ns", "max_ns"), measurements),
                    host_frames=128, input_sha256=c.digest(data), includes_audio=False)
        report["passed"] = all(w["modes"]["projected_hold"]["passed"] for w in report["windows"].values())
        if args.attack_cells:
            report["passed"] &= report["attack_sweep"]["passed"] and all(
                w["attack_ports"]["passed"] and w["modes"]["generated_attack_projection"]["passed"]
                for w in report["windows"].values())
            report["passed"] &= all(
                report["windows"][name]["modes"]["generated_attack_current"]["passed"]
                for name in ("negative_key_on", "negative_key_off"))
        if args.refine_orbit:
            report["refined_tail_reserves_passed"] = {
                str(points): all(
                    window["refined_crossing_charge"]["metrics"]["collector_orbit"]["modes"]
                    ["nominal_shape"][f"{points}_tail"]["passed"]
                    for window in report["windows"].values() if "refined_crossing_charge" in window)
                for points in (4, 8, 16, 24, 32)}
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
