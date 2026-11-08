"""Audit the loaded RF-D contour/audio interface and a frozen event trajectory."""
import os
import subprocess
import traceback
from pathlib import Path

import numpy as np

from affine_evidence import Sources
from check_hybrid_voice import packed
from check_recovery_cost import digest
from check_vco_family_voice_bus_cost import references
from check_vco_family_voice_bus_hot import text
from check_vco_family_voice_bus_latch_lu import SOURCES as REFERENCE_SOURCES, emit, generate
from check_vco_family_voice_bus_model import AREA, materialize, read_oracle
from check_vco_phase import COMPILER, LIB
from prepare_dual_chain import ROOT, sha, write
from recovery_port_input_model import law
from rf_d_reduced_contour_live import (
    CONVERSION, HEADPHONE, LADDER, RECOVERY, VCA, integrate, junction_incidence, run as run_live,
)
from prepare_hybrid_stamp import once
from prepare_vco_family_voice_bus import TABLE
from validate_vco_family_voice_bus import BUS, J7, KERNEL, MODEL, N, PANEL, read

PROBE = "tools/rf_d_reduced_contour_probe.rs"
CLOSE = "tools/rf_d_reduced_contour_ports.rs"
STAMP = "tools/rf_d_reduced_contour_stamp.rs"
PROTOCOL = "docs/VOZ_REDUCIDA_CONTORNOS_PROTOCOLO.md"
SOURCES = (*REFERENCE_SOURCES, PROBE, CLOSE, STAMP, PROTOCOL, "tools/rf_d_reduced_contour_live.py",
           "tools/recovery_port_input_model.py", "tools/prepare_charge_reduced.py",
           "tools/check_rf_d_reduced_contour_ports.py")
CLOCK = "evidence/vco_family_voice_bus_clock_tests01.json"
ANCHORS = dict(negative=(0, 15, 16, 17, 95, 96, 97, 128), positive=(0, 53, 76, 77, 78, 79, 99, 128))
B = np.array([[1.5, .5], [-4.5, 2.5]])
A = np.linalg.inv(B)
PORTS = (54, 55)
R59 = 68_000.
R60 = 680.
STAGE = (1. / 3., 1.)


def chain_index(k):
    if k in (5, 32):
        return 55 if k == 5 else 54
    if 62 <= k < 66:
        return k - 28
    return 56 + k - int(k > 5) - int(k > 32) - 4 * int(k > 65)


AUDIO_ROWS = np.r_[0:62, 66:68]
AUDIO_EXCLUDED = np.arange(62, 66)
NODES = (np.arange(56), np.array([chain_index(k) for k in AUDIO_ROWS]))
LOCAL_PORTS = tuple(np.array([list(nodes).index(p) for p in PORTS]) for nodes in NODES)
SIGNAL = LADDER + RECOVERY + VCA
OUTPUT = SIGNAL + HEADPHONE + CONVERSION


def output_inputs(labels, rows):
    probes = []
    for label, devices, nodes in (("headphone", HEADPHONE, np.arange(50, 60)),
                                   ("conversion", CONVERSION, np.arange(40, 47))):
        columns = NODES[1][nodes]
        for frame in (0, 77):
            anchor = rows[labels.index(("positive", frame))]
            for scale in (.008, -.040):
                point = anchor.copy()
                point[columns] += scale * np.cos(nodes)
                point[N + columns] = 0.
                probes.append((label, devices, frame, anchor, point))
    return probes


def verify_output(probes, matrices, anchor_data):
    checks = {}
    for (label, devices, frame, anchor, point), row in zip(probes, matrices, strict=True):
        new, _, _, _ = unpack_stamp(row)
        audio = anchor_data[f"positive_{frame}"][0][1]
        nodes = NODES[1]
        v = anchor[nodes] + anchor[N + nodes]
        delta = (point[nodes] - anchor[nodes]) + (point[N + nodes] - anchor[N + nodes])
        d, e, bias, iexp = junction_incidence(devices, v)
        z = e @ delta
        assert max(bias + z) < 45.
        current, slope = law(dict(iexp=iexp), z)
        current_error = float(np.max(abs(new[1][0] - audio[0] - audio[1] @ delta - d @ current)))
        jacobian_error = float(np.max(abs(new[1][1] - audio[1] - (d * slope) @ e)))
        assert current_error <= 2e-13 and jacobian_error <= 2e-12
        checks.setdefault(label, []).append(dict(
            frame=frame, voltage_delta_v=float(np.max(abs(delta))),
            current_error_a=current_error, jacobian_error_s=jacobian_error))
    return checks


def build(kernel):
    probe = generate(kernel, "combined", False, True)
    graph = AREA / "hot-graph.rs"
    emit(graph.name, graph.read_text(encoding="utf8") + "\n" + text(STAMP))
    module = emit("reduced-contour-probe.rs", text(PROBE).replace("PORTS_PATH", (ROOT / CLOSE).as_posix()))
    code = once(probe.read_text(encoding="utf8"), '        Some("ports") => ports(),', '''
        Some("ports") => ports(),
        Some("contour-stamps") if args.len() == 3 => reduced_contour::stamps(&args[2]),
        Some("contour-stages") => reduced_contour::contour_stages(),
        Some("contour-close") if args.len() == 3 => reduced_contour::close(&args[2]),''')
    return emit(probe.name, code + f'\n#[path = "{module.as_posix()}"] mod reduced_contour;\n')


def anchor_input(reference):
    labels, rows = [], []
    for case, frames in ANCHORS.items():
        for frame in frames:
            phase, _, _, state = reference[case][1][frame]
            key = 10. if case == "negative" and 16 < frame <= 96 else 0.
            labels.append((case, frame))
            rows.append(np.r_[state.ravel(), phase, key])
    return labels, np.asarray(rows, dtype="<f8")


def unpack_stamp(row):
    def part(n):
        nonlocal row
        size = n + 2 * n * n
        f, g, mass = np.split(row[:size], [n, n + n * n])
        row = row[size:]
        return f.copy(), g.reshape(n, n).copy(), mass.reshape(n, n).copy()

    dual, raw_audio, full = part(56), part(68), part(N)
    current, dbus, _, _, _ = row
    f, g, mass = raw_audio
    crossing = np.ix_(AUDIO_ROWS, AUDIO_EXCLUDED)
    assert not np.any(g[crossing]) and not np.any(mass[crossing])
    f[66] += current
    g[66, 66] += dbus
    keep = np.ix_(AUDIO_ROWS, AUDIO_ROWS)
    audio = (f[AUDIO_ROWS], g[keep], mass[keep])
    assert dual[1][3, 54] == dual[1][54, 3] == -1. / R59
    assert dual[1][37, 55] == dual[1][55, 37] == -1. / R60

    errors = {}
    for k, label in enumerate(("dc_a", "conductance_s", "capacitance_f")):
        joined = np.zeros_like(full[k])
        for nodes, block in zip(NODES, (dual, audio)):
            joined[nodes if k == 0 else np.ix_(nodes, nodes)] += block[k]
        errors[label] = float(np.max(abs(joined - full[k])))
    assert errors["dc_a"] <= 2e-13 and errors["conductance_s"] <= 1e-12
    assert errors["capacitance_f"] <= 1e-20
    return (dual, audio), full, row, errors


def stage_ids(nodes, n):
    return np.r_[nodes, nodes + n]


def matrix(stamp, h, phase, bus=None):
    _, g, mass = stamp
    result = np.kron(np.eye(2), g) + np.kron(B, mass / h)
    if bus is not None:
        _, _, dphase, _, frequency_dbus = phase
        bus_rows = stage_ids(np.array([bus]), len(g))
        result[np.ix_(bus_rows, bus_rows)] += dphase * h * frequency_dbus * A
    return result


def currents(state):
    return np.stack(((state[..., 3] - state[..., 54]) / R59,
                     (state[..., 55] - state[..., 37]) / R60), axis=-1)


class Interior:
    def __init__(self, lhs, ports):
        self.port = ports
        self.inner = np.setdiff1d(np.arange(len(lhs)), ports)
        ii, pp = self.inner, self.port
        self.factor = lhs[np.ix_(ii, ii)]
        self.feedback = lhs[np.ix_(pp, ii)]
        self.lift = np.linalg.solve(self.factor, lhs[np.ix_(ii, pp)])
        self.schur = lhs[np.ix_(pp, pp)] - self.feedback @ self.lift

    def response(self, rhs):
        particular = np.linalg.solve(self.factor, rhs[self.inner])
        return particular, self.feedback @ particular - rhs[self.port]

    def reconstruct(self, particular, shared):
        x = np.empty((len(self.inner) + len(self.port), shared.shape[1]))
        x[self.port] = shared
        x[self.inner] = particular - self.lift @ shared
        return x


def history(mass, h):
    return np.kron(B.sum(axis=1).reshape(2, 1), mass / h)


def prepare_reserve(blocks, full, phase):
    h = 1. / 192_000.
    lhs = matrix(full, h, phase, BUS)
    rhs = np.zeros((2 * N, 4))
    reactions, records = [], []
    perturbation = 1e-6 * np.sin(np.arange(N))
    for k, (nodes, ports, block) in enumerate(zip(NODES, LOCAL_PORTS, blocks)):
        n = len(nodes)
        local = np.zeros((2 * n, 4))
        bus = None
        if k == 0:
            local[ports[0], 0] = 1e-9
            local[n + ports[1], 1] = -1e-9
        else:
            bus = int(np.flatnonzero(nodes == BUS)[0])
            local[[bus, n + bus], 2] = [1e-9, -1e-9]
        local[:, 3] = history(block[2], h) @ perturbation[nodes]
        ids = stage_ids(nodes, N)
        rhs[ids] += local
        interior = Interior(matrix(block, h, phase, bus), stage_ids(ports, n))
        particular, affine = interior.response(local)
        reactions.append(np.column_stack((np.tile(interior.schur.ravel(), (4, 1)), affine.T)))
        records.append((ids, interior, particular))
    return np.column_stack(reactions), (lhs, rhs, records)


def verify_reserve(case, shared):
    lhs, rhs, records = case
    split = np.empty_like(rhs)
    for ids, interior, particular in records:
        split[ids] = interior.reconstruct(particular, shared.T)
    full = np.linalg.solve(lhs, rhs)
    difference = (split - full).T.reshape(-1, 2, N)
    residual = abs(lhs @ split - rhs)
    scale = abs(lhs) @ abs(split) + abs(rhs)
    backward = np.divide(residual, scale, out=np.zeros_like(residual), where=scale > 0.)
    worst = np.unravel_index(np.argmax(backward), backward.shape)
    resolved_scale = scale + 2e-9 * abs(lhs).sum(axis=1, keepdims=True)
    resolved = np.divide(residual, resolved_scale, out=np.zeros_like(residual), where=resolved_scale > 0.)
    result = dict(worst_component=[int(v) for v in worst], worst_component_a=float(residual[worst]),
                  worst_component_scale_a=float(scale[worst]), nodal_direction_error_v=float(np.max(abs(difference))),
                  r59_error_a=float(np.max(abs(currents(difference)[..., 0]))),
                  r60_error_a=float(np.max(abs(currents(difference)[..., 1]))),
                  raw_componentwise_backward=float(np.max(backward)),
                  componentwise_backward=float(np.max(resolved)))
    result["passed"] = (result["nodal_direction_error_v"] <= 20e-9
                        and max(result["r59_error_a"], result["r60_error_a"]) <= 2e-9
                        and result["componentwise_backward"] <= 1e-10)
    return result


def frozen_trajectory(blocks, phase, reference, expected):
    start, end = 77, 79
    subdivisions = reference[0]["subdivisions"]
    h = 1. / (48_000 * subdivisions)
    _, _, dphase, frequency, frequency_dbus = phase
    x0 = reference[1][start][3].sum(axis=0)
    # Precompute the port response for all history coordinates and phase forcing.
    maps = []
    for nodes, ports, block in zip(NODES, LOCAL_PORTS, blocks):
        n = len(nodes)
        bus_index = np.flatnonzero(nodes == BUS)
        bus = int(bus_index[0]) if bus_index.size else None
        lhs = matrix(block, h, phase, bus)
        rhs = np.zeros((2 * n, N + 3))
        rhs[:, nodes] = history(block[2], h)
        rhs[:, N] = -np.tile(block[0], 2)
        if bus is not None:
            rhs[bus, N + 1] = -dphase
            rhs[n + bus, N + 2] = -dphase
        interior = Interior(lhs, stage_ids(ports, n))
        part, current = interior.response(rhs)
        maps.append((interior, part, current))
    shared = np.linalg.solve(sum(item[0].schur for item in maps),
                             -sum(item[2] for item in maps))
    endpoint = np.empty((N, N + 3))
    for nodes, (interior, part, _) in zip(NODES, maps):
        endpoint[nodes] = interior.reconstruct(part, shared)[len(nodes):]
    delta = np.zeros(N)
    phase_offset = 0.
    pairs = np.array([[26, 28], [40, 42]])
    previous = x0[pairs[:, 0]] >= x0[pairs[:, 1]]
    ticks_per_substep = 4096 // subdivisions
    assert ticks_per_substep * subdivisions == 4096
    switches, endpoints = [], []
    for k in range((end - start) * subdivisions):
        phase_stages = phase_offset + h * frequency * np.array(STAGE)
        new_delta = endpoint @ np.r_[delta, 1., phase_stages]
        # The phase feedback uses both Radau stages, so retain their BUS values.
        audio, part, _ = maps[1]
        n = len(NODES[1])
        bus = int(np.flatnonzero(NODES[1] == BUS)[0])
        if k == 0:
            bus_stages = audio.reconstruct(part, shared)[[bus, n + bus]]
        phase_offset = phase_stages[-1] + h * frequency_dbus * (A[-1] @ (bus_stages @ np.r_[delta, 1., phase_stages]))
        delta = new_delta
        nodes = x0 + delta
        present = nodes[pairs[:, 0]] >= nodes[pairs[:, 1]]
        tick = start * 4096 + k * ticks_per_substep
        switches.extend([int(pair), tick, tick + ticks_per_substep, int(present[pair])]
                        for pair in np.flatnonzero(previous != present))
        previous = present
        if (k + 1) % subdivisions == 0:
            frame = start + (k + 1) // subdivisions
            endpoints.append(endpoint_errors(frame, nodes, reference[1][frame]))
    return dict(start_frame=start, end_frame=end, subdivisions=subdivisions, switches=switches,
                expected_switches=expected, endpoints=endpoints, passed=switches == expected and all(
                    row["nodal_gate_fraction"] <= 1. and row["contour_return_gate_fraction"] <= 1.
                    for row in endpoints))


def endpoint_errors(frame, nodes, target):
    ref = target[3].sum(axis=0)
    error = abs(nodes - ref)
    gate = error / (20e-6 + 2e-6 * abs(ref))
    load = abs(currents(nodes) - target[1:3])
    load_gate = load / (2e-9 + 2e-5 * abs(np.asarray(target[1:3])))
    return dict(frame=frame, nodal_gate_fraction=float(np.max(gate)), worst_node=int(np.argmax(gate)),
                max_nodal_error_v=float(np.max(error)), contour_return_gate_fraction=float(np.max(load_gate)),
                r59_error_a=float(load[0]), r60_error_a=float(load[1]), j7_error_v=float(error[J7]),
                j7_delta_v=float(nodes[J7] - ref[J7]))


def endpoint_passed(errors):
    return errors["nodal_gate_fraction"] <= 1. and errors["contour_return_gate_fraction"] <= 1.


def compare_audio(endpoints, reference):
    target = np.array([reference[1][item["frame"]][3][:, J7].sum() for item in endpoints])
    delta = np.array([item["j7_delta_v"] for item in endpoints])
    rms = float(np.linalg.norm(delta) / np.linalg.norm(target))
    peak = float(max(abs(delta)) / max(abs(target)))
    mean = float(abs(np.mean(delta)))
    return dict(rms_relative=rms, peak_relative=peak, mean_error_v=mean,
                passed=rms <= .001 and peak <= .003 and mean <= 1e-6)


def live_trajectory(exe, env, blocks, phase, reference, expected, devices, start, controls, bounded=False):
    topology = (B, NODES[1], LOCAL_PORTS[1], BUS, matrix, history, Interior, stage_ids)
    def outside_gate(offset, nodes):
        errors = endpoint_errors(start + offset, nodes, reference[1][start + offset])
        return not endpoint_passed(errors)

    result = run_live(exe, env, ROOT, lambda proc: integrate(
        proc, anchor=(blocks[1], reference[1][start][3], phase[0], phase[1]),
        phase=reference[1][start][0],
        controls=controls, subdivisions=reference[0]["subdivisions"],
        topology=topology, devices=devices, stop_if=outside_gate if bounded else None))
    result.update(retained_devices=len(devices), start_frame=start, controls=list(controls),
                  subdivisions=reference[0]["subdivisions"])
    if "samples" not in result:
        return dict(result, passed=False)
    samples = result.pop("samples")
    endpoints = []
    for frame, (nodes, angle) in enumerate(samples, start + 1):
        target = reference[1][frame]
        errors = endpoint_errors(frame, nodes, target)
        errors["phase_error_cycles"] = float(abs((angle - target[0] + .5) % 1. - .5))
        endpoints.append(errors)
    switches = [[pair, lo + start * 4096, hi + start * 4096, state]
                for pair, lo, hi, state in result["switches"]]
    result.update(switches=switches, expected_switches=expected, endpoints=endpoints,
                  passed=result["completed"] and switches == expected and all(map(endpoint_passed, endpoints)))
    return result


def main():
    assert not list(AREA.iterdir())
    sequence = 1
    while (output := ROOT / f"evidence/rf_d_reduced_contour_ports{sequence:02}.json").exists():
        sequence += 1
    sources = Sources(SOURCES)
    report = dict(passed=False, rackforge_measured=False, **sources.fields(),
                  compiler_sha256=sha(Path(COMPILER)), library_sha256=sha(LIB))
    env = dict(os.environ, PATH="C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;" + os.environ["PATH"])

    def run(name, args, binary=False):
        command = list(map(str, args))
        proc = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, timeout=180)
        report[name] = dict(command=command, exit_code=proc.returncode, stderr=packed(proc.stderr),
                            stdout=dict(bytes=len(proc.stdout), sha256=digest(proc.stdout)) if binary else packed(proc.stdout))
        assert proc.returncode == 0, proc.stderr.decode(errors="replace")
        return proc.stdout

    try:
        reference, report["reference_inputs"] = references()
        report["clock_reference_sha256"] = sha(ROOT / CLOCK)
        clock = read(CLOCK)
        assert clock["passed"]
        expected = clock["trials"]["positive"]["64"]["expected_brackets"]
        table, *_ = materialize(read_oracle())
        report["table_sha256"] = digest(table)
        assert report["table_sha256"] == read(MODEL)["table_sha256"]
        path = AREA / TABLE
        path.write_bytes(table)
        kernel = emit("family-kernel.rs", text(KERNEL).replace("H128_VOICE_TABLE_PATH", path.as_posix())
                      .replace("VCO_PANEL_PORT_PATH", (ROOT / PANEL).as_posix()))
        exe = AREA / "reduced-contour.exe"
        run("build", [COMPILER, "--edition=2021", "-C", "opt-level=3", "-C", "target-feature=+fma",
                      "-C", "link-arg=-Wl,--stack,33554432", "--cfg", "laboratory", "-A", "dead_code",
                      build(kernel), "--extern", f"rf_d_circuit={LIB}", "-o", exe])
        labels, rows = anchor_input(reference)
        state = AREA / "anchors.bin"
        output_probes = output_inputs(labels, rows)
        np.vstack((rows, [item[-1] for item in output_probes])).astype("<f8").tofile(state)
        report["anchor_sha256"] = sha(state)
        raw = run("stamps", [exe, "contour-stamps", state], binary=True)
        width = sum(n + 2 * n * n for n in (56, 68, N)) + 5
        matrices = np.frombuffer(raw, dtype="<f8").reshape(len(labels) + len(output_probes), width)
        inputs, checks, anchor_data = [], [], {}
        report["reserves"] = {}
        for (case, frame), row in zip(labels, matrices):
            blocks, full, phase, errors = unpack_stamp(row)
            reaction, check = prepare_reserve(blocks, full, phase)
            name = f"{case}_{frame}"
            report["reserves"][name] = dict(stamp_errors=errors)
            inputs.append(reaction)
            checks.append(check)
            anchor_data[name] = (blocks, phase)
        report["output_stamp_checks"] = verify_output(output_probes, matrices[len(labels):], anchor_data)
        print("OUTPUT_STAMPS", {label: len(items) for label, items in report["output_stamp_checks"].items()}, flush=True)
        ports = AREA / "reactions.bin"
        np.asarray(inputs, dtype="<f8").tofile(ports)
        report["reactions_sha256"] = sha(ports)
        result = run("close", [exe, "contour-close", ports], binary=True)
        solutions = np.frombuffer(result, dtype="<f8").reshape(len(labels), 4, 4)
        for entry, check, solution in zip(report["reserves"].values(), checks, solutions):
            entry.update(verify_reserve(check, solution))
        report["local_port_checks_passed"] = all(item["passed"] for item in report["reserves"].values())
        report["frozen_trajectory"] = frozen_trajectory(*anchor_data["positive_77"], reference["positive"], expected)
        report["live_contour_trajectory"] = {}
        for name, devices in (("ladder", LADDER), ("ladder_recovery_vca", SIGNAL),
                              ("headphone", SIGNAL + HEADPHONE), ("output", OUTPUT)):
            result = live_trajectory(exe, env, *anchor_data["positive_77"], reference["positive"], expected,
                                     devices, 77, (0., 0.))
            report["live_contour_trajectory"][name] = result
        report["independent_windows"] = {}
        windows = (
            ("key_rise", "negative", 15, (0., 10., 10.), clock["trials"]["negative"]["32"]["expected_brackets"]),
            ("key_fall", "negative", 95, (10., 0., 0.), clock["trials"]["negative"]["32"]["expected_brackets"]),
            ("long_release", "positive", 76, (0.,) * 5, expected),
        )
        for name, branch, start, key, switches in windows:
            result = live_trajectory(exe, env, *anchor_data[f"{branch}_{start}"], reference[branch],
                                     switches, OUTPUT, start, key)
            report["independent_windows"][name] = result
        report["continuous_128"] = {}
        for branch, switches in (("negative", windows[0][-1]), ("positive", expected)):
            keys = tuple(10. if branch == "negative" and 16 <= i < 96 else 0. for i in range(128))
            print("CONTINUOUS_START", branch, flush=True)
            report["continuous_128"][branch] = live_trajectory(
                exe, env, *anchor_data[f"{branch}_0"], reference[branch], switches,
                OUTPUT, 0, keys, bounded=True)
        report["passed"] = (report["local_port_checks_passed"]
                            and report["live_contour_trajectory"]["ladder_recovery_vca"]["passed"]
                            and report["live_contour_trajectory"]["headphone"]["passed"]
                            and report["live_contour_trajectory"]["output"]["passed"]
                            and all(item["passed"] for item in report["independent_windows"].values()))
        positive = report["continuous_128"]["positive"]
        if positive["completed"]:
            positive["audio"] = compare_audio(positive["endpoints"], reference["positive"])
        report["continuous_128_passed"] = (all(item["passed"] for item in report["continuous_128"].values())
                                            and positive["audio"]["passed"])
        assert report["passed"]
        sources.unchanged()
    except Exception:
        report["failure"] = traceback.format_exc()
        raise
    finally:
        write(output, report)
        for path in AREA.iterdir():
            path.unlink()
    print("CONTOUR_PORTS", len(report["reserves"]), report["local_port_checks_passed"])
    print("FROZEN", report["frozen_trajectory"])
    print("LIVE_CONTOURS", report["live_contour_trajectory"])
    print("INDEPENDENT", {name: item["passed"] for name, item in report["independent_windows"].items()})
    for name, item in report["continuous_128"].items():
        print("CONTINUOUS_128", name, item["passed"], item.get("failure"), item.get("endpoints", [])[-1:])


if __name__ == "__main__":
    main()
