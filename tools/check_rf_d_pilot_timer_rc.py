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


def project_loads(stages, first_path=0):
    """Project the selected load ports with their summed conductance."""
    stage_values = stages[1:, np.array(LOAD_NODES)[:, first_path:]]
    conductance = (1. / OHMS[:, first_path:]).sum(axis=1)
    return project_stages(stage_values, conductance)


def project_stages(stage_values, conductance):
    steps = HALF_FRAME_TICKS // FINE_TICKS
    x = conductance * FINE_TICKS / (10e-6 * 48_000 * 4096)
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


def attack_results(run, target, stages):
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
    peak = abs(ports - ref).max(axis=0)
    passes = bool(peak[:, :2].max() <= TIMER_LIMIT_V and peak[:, 2:].max() <= LOAD_LIMIT_A)
    item = dict(passed=passes, stages=len(ports), max_error=peak.tolist(),
                input_sha256=c.digest(data), output_sha256=c.digest(raw))
    if not passes:
        assert run([target], data) == raw
        item["unchanged_replay"] = True
    return ports, item


def crossing_charge(ports, stages, regular, changes):
    """Separate a two-level current model from the need to locate the event."""
    assert len(changes) == 1
    capacitance = 10e-6
    conductance = 1. / OHMS[:, 1:]
    total = conductance.sum(axis=1)
    x = total / (96_000 * capacitance)
    moved = -np.expm1(-x)
    end_weight = (1. - moved / x) / moved
    other = project_loads(stages, first_path=1)
    exact_current = project_stages(ports[1:, :, 2, None], total)[:, :, 0]
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
    return dict(oracle_projected=ideal, coarse_affine=error(affine_current),
                split_reference_crossing=error(at_event), split_area_equivalent=error(at_effective),
                event_interval=int(slot), reference_fraction=bracket.tolist(),
                area_equivalent_fraction=float(effective),
                area_equivalent_minus_crossing_ns=float((effective - fraction) * 1e9 / 96_000),
                effective_attack_a=exact_current[slot].tolist(),
                predicted_attack_at_reference_event_a=at_event[slot].tolist())


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
    args = parser.parse_args()
    assert not args.crossing_charge or args.attack_cells
    assert c.AREA.is_dir() and not list(c.AREA.iterdir())
    seq = 1
    while (out := c.ROOT / f"evidence/rf_d_pilot_timer_rc{seq:02}.json").exists():
        seq += 1
    added_sources = (ATTACK, ATTACK_PROBE) if args.attack_cells else ()
    sources = Sources((*c.ALL_SOURCES, c.OWN, c.CANDIDATE, c.PROBE, c.PORTS,
                       "tools/rf_d_pilot_step_profile.rs", OWN, MODEL, PROBE, DOC, *added_sources))
    report = dict(passed=False, coupled=False, rack_integrated=False, clock_hz=96_000,
                  timer_nodes=TIMER_NODES, load_nodes=LOAD_NODES, load_ohms=OHMS.tolist(),
                  timer_limit_v=TIMER_LIMIT_V, load_limit_a=LOAD_LIMIT_A,
                  attack_cells=args.attack_cells, crossing_charge=args.crossing_charge, windows={}, **sources.fields(), compiler_sha256=c.sha(Path(c.COMPILER)),
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
        for label, branch, start, frames, key in c.WINDOWS:
            phase, _, _, state = references[branch][1][start]
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
            assert events == expected
            regular = np.arange(0, len(nodes), HALF_FRAME_TICKS // FINE_TICKS)
            modes = dict(fine_affine=np.arange(len(nodes)), fixed_affine=regular,
                         split_at_reference_bracket=np.unique(np.r_[regular, changes, changes + 1]))
            results = {mode: replay(run, timer, nodes, indices) for mode, indices in modes.items()}
            projected = project_loads(stages)
            results["projected_hold"] = replay(run, timer, nodes, regular, projected)
            item = report["windows"][label] = dict(anchor_sha256=c.sha(anchor), reference_sha256=c.digest(raw),
                                             reference_events=events, key_v=key, start_frame=start,
                                             frames=frames, modes=results)
            if args.attack_cells:
                ports, item["attack_ports"] = attack_results(run, attack, stages)
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
                    charge = crossing_charge(ports, stages, regular, changes)
                    assert charge == crossing_charge(ports, stages, regular, changes)
                    item["crossing_charge"] = dict(charge, unchanged_replay=True)
                    print("CROSSING_CHARGE", charge, flush=True)
                print(label, item["attack_ports"]["passed"], results["generated_attack_projection"]["passed"],
                      results["generated_attack_current"], flush=True)
            else:
                print(label, results, flush=True)
            if branch == "positive":
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
