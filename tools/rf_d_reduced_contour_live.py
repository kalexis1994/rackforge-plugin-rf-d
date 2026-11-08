"""Close the nonlinear RF-D contour and H128 loads on an affine audio arm."""
import subprocess

import numpy as np


from recovery_port_input_model import VT, law

# Raw audio nodes 0..61 retain order in the split arm.
LADDER = ((6, 8, 5), (3, 9, 8), (2, 10, 9), (1, 11, 10), (0, None, 11),
          (7, 12, 5), (3, 13, 12), (2, 14, 13), (1, 15, 14), (0, None, 15))
RECOVERY = ((16, 21, 18), (17, None, 19), (18, 21, 20), (19, None, 20))
VCA = ((25, 30, 27), (26, 31, 27), (32, 28, 29), (30, 37, 34), (31, 38, 34))


class Junctions:
    """Inject only the exponential remainder of each retained BE and BC law."""

    def __init__(self, devices, audio, anchor):
        n = len(anchor)
        inject = np.zeros((n, 2 * len(devices)))
        sense = np.zeros((2 * len(devices), n))
        base_v = []
        for k, (base, collector, emitter) in enumerate(devices):
            for col, other in ((2 * k, emitter), (2 * k + 1, collector)):
                sense[col, base] = 1. / VT
                if other is not None:
                    sense[col, other] = -1. / VT
                base_v.append((anchor[base] - (10. if other is None else anchor[other])) / VT)
            for node, forward, reverse in ((base, .01, .2), (collector, 1., -1.2), (emitter, -1.01, 1.)):
                if node is not None:
                    inject[node, 2 * k:2 * k + 2] = (forward, reverse)
        self.base = np.tile(base_v, 2)
        self.model = dict(iexp=1e-14 * np.exp(self.base))
        self.sense = np.kron(np.eye(2), sense)
        d = np.kron(np.eye(2), inject)
        particular, self.return_map = audio.response(-d)
        self.node_map = audio.reconstruct(particular, np.zeros((len(audio.port), d.shape[1])))
        self.p = -(self.sense @ self.node_map)
        zero = np.zeros((len(audio.inner), len(audio.port)))
        self.source_map = self.sense @ audio.reconstruct(zero, np.eye(len(audio.port)))
        self.identity = np.eye(len(self.base))

    def evaluate(self, x):
        z0 = self.sense @ x
        z = z0.copy()
        for _ in range(16):
            if not np.isfinite(z).all() or np.max(self.base + z) > 45.:
                return None
            nonlinear, slope = law(self.model, z)
            residual = z - z0 + self.p @ nonlinear
            linear = self.identity + self.p * slope
            if np.max(abs(residual)) <= 2e-13:
                dz = np.linalg.solve(linear, self.source_map)
                return (x + self.node_map @ nonlinear, self.return_map @ nonlinear,
                        self.return_map @ (slope[:, None] * dz))
            z -= np.linalg.solve(linear, residual)
        return None


def stamps(proc, old, delta, key, h, phase, bus):
    values = np.r_[old.ravel(), delta.ravel(), key, h, phase, bus]
    proc.stdin.write(values.astype("<f8", copy=False).tobytes())
    proc.stdin.flush()
    status = proc.stdout.read(1)
    if status == b"\x01":
        return None
    assert status == b"\x00", (status, proc.poll())
    n = old.shape[1]
    width = 2 * n + 2 * n * n
    result = np.frombuffer(proc.stdout.read((2 * width + 7) * 8), dtype="<f8")
    rows = result[:2 * width].reshape(2, width)
    dc, dq, g, m = np.split(rows, [n, 2 * n, 2 * n + n * n], axis=1)
    return (dc, dq, g.reshape(2, n, n), m.reshape(2, n, n),
            result[-7:-5], result[-5:-1].reshape(2, 2), result[-1])


def run(exe, env, root, exercise):
    with subprocess.Popen([exe, "contour-stages"], cwd=root, env=env,
                          stdin=subprocess.PIPE, stdout=subprocess.PIPE) as proc:
        try:
            result = exercise(proc)
        finally:
            proc.stdin.close()
        assert proc.wait(timeout=10) == 0
    return result


def integrate(proc, *, anchor, phase, controls, subdivisions, topology, devices, stop_if=None):
    """Local hybrid with exact contour stamps and the original H128 table."""
    B, nodes, ports, bus, matrix, history, interior, stage_ids = topology
    audio_block, anchor_state, panel_dc, panel_slope = anchor
    n = len(nodes)
    length = 56
    h = 1. / (48_000 * subdivisions)
    local_bus = int(np.flatnonzero(nodes == bus)[0])
    bus_stages = stage_ids(np.array([local_bus]), n)
    contour_ports = stage_ids(np.array([54, 55]), length)
    f, g, m = (item.copy() for item in audio_block)
    f[local_bus] -= panel_dc
    g[local_bus, local_bus] -= panel_slope
    terminals = np.r_[stage_ids(ports, n), bus_stages]
    audio = interior(matrix((f, g, m), h, None), terminals)
    history_rhs = np.column_stack((history(m, h), -np.tile(f, 2)))
    history_part, history_reaction = audio.response(history_rhs)
    audio_anchor = anchor_state[:, nodes].sum(axis=0)
    bus_anchor = audio_anchor[local_bus]
    junctions = Junctions(devices, audio, audio_anchor)
    current = anchor_state.copy()
    pairs = np.array([[26, 28], [40, 42]])
    switches, samples = [], []
    max_iterations, max_residual = 0, 0.
    for k in range(len(controls) * subdivisions):
        old_audio = current[:, nodes].sum(axis=0) - audio_anchor
        state = np.r_[old_audio, 1.]
        part = (history_part @ state)[:, None]
        intercept = history_reaction @ state
        old = current[:, :length].copy()
        old_ports = old[:, [54, 55]].sum(axis=0) - audio_anchor[ports]
        key = controls[k // subdivisions]
        trial = np.zeros((2, length))
        if key - old[0, 22] - old[1, 22] > .5:
            trial[:, 22] = key - .5 - old[0, 22] - old[1, 22]
        bus_delta = np.full(2, old_audio[local_bus])
        def loads(shared):
            affine = audio.reconstruct(part, shared[:, None])[:, 0]
            response = junctions.evaluate(affine)
            if response is None:
                return None
            x, extra_current, extra_j = response
            return x, audio.schur @ shared + intercept + extra_current, audio.schur + extra_j

        stamp = stamps(proc, old, trial, key, h, phase, bus_anchor + bus_delta)
        if stamp is None:
            return dict(completed=False, failed_substep=k, failure="initial stamp domain")
        for i in range(80):
            dc, dq, g, m, panel_current, panel_j, end_phase = stamp
            contour_current = (dc + B @ dq).ravel()
            lhs = np.block([[B[0, 0] * m[0] + g[0], B[0, 1] * m[1]],
                            [B[1, 0] * m[0], B[1, 1] * m[1] + g[1]]])
            shared = np.r_[np.tile(old_ports, 2) + trial.ravel()[contour_ports], bus_delta]
            tested_audio = loads(shared)
            if tested_audio is None:
                return dict(completed=False, failed_substep=k, failure="junction budget")
            x_audio, load, shared_j = tested_audio
            load[4:] += panel_current
            residual = contour_current.copy()
            residual[contour_ports] += load[:4]
            norm = float(max(np.max(abs(residual)), np.max(abs(load[4:]))))
            c = interior(lhs, contour_ports)
            particular, reaction = c.response(-contour_current[:, None])
            shared_j[:4, :4] += c.schur
            shared_j[4:, 4:] += panel_j
            load[:4] += reaction[:, 0]
            shared_step = np.linalg.solve(shared_j, -load)
            step = c.reconstruct(particular, shared_step[:4, None]).reshape(2, length)
            correction = float(max(np.max(abs(step)), np.max(abs(shared_step[4:]))))
            if correction <= 2e-9 and norm <= 1e-12:
                max_iterations = max(max_iterations, i + 1)
                max_residual = max(max_residual, norm)
                break
            for half in range(24):
                factor = 2. ** -half
                candidate = trial + factor * step
                candidate_bus = bus_delta + factor * shared_step[4:]
                tested = stamps(proc, old, candidate, key, h, phase, bus_anchor + candidate_bus)
                if tested is None:
                    continue
                tested_audio = loads(shared + factor * shared_step)
                if tested_audio is None:
                    continue
                _, tested_load, _ = tested_audio
                tested_residual = (tested[0] + B @ tested[1]).ravel()
                tested_residual[contour_ports] += tested_load[:4]
                tested_norm = max(np.max(abs(tested_residual)), np.max(abs(tested_load[4:] + tested[4])))
                if tested_norm < max(norm, 1e-12):
                    stamp = tested
                    trial = candidate
                    bus_delta = candidate_bus
                    break
            else:
                return dict(completed=False, failed_substep=k, failed_iteration=i, failure="no decrease",
                            correction_v=correction, residual_a=norm)
        else:
            return dict(completed=False, failed_substep=k, failure="Newton budget",
                        correction_v=correction, residual_a=norm)
        x_audio = x_audio.reshape(2, n)
        phase = end_phase
        old_order = old[0, pairs[:, 0]] + old[1, pairs[:, 0]] >= old[0, pairs[:, 1]] + old[1, pairs[:, 1]]
        # Keep the compensated previous state supplied to the charge law.
        upper = old[0] + trial[-1]
        tmp = upper - old[0]
        lower = (old[0] - (upper - tmp)) + (trial[-1] - tmp) + old[1]
        current[0, nodes] = audio_anchor + x_audio[-1]
        current[1, nodes] = 0.
        high = upper + lower
        tmp = high - upper
        current[0, :length] = high
        current[1, :length] = (upper - (high - tmp)) + (lower - tmp)
        x = current.sum(axis=0)
        new_order = x[pairs[:, 0]] >= x[pairs[:, 1]]
        width = 4096 // subdivisions
        tick = k * width
        switches.extend([int(pair), tick, tick + width, int(new_order[pair])]
                        for pair in np.flatnonzero(new_order != old_order))
        if (k + 1) % subdivisions == 0:
            samples.append((x, phase))
            if stop_if is not None and stop_if(len(samples), x):
                return dict(completed=False, switches=switches, samples=samples,
                            failed_substep=k, failure="electrical trajectory gate")
    return dict(completed=True, switches=switches, max_iterations=max_iterations,
                max_residual_a=max_residual, samples=samples)
