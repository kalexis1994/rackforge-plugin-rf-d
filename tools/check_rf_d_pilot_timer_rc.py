"""Contrast the fixed-cost C2/C5 update with the full circuit, at imposed loads."""
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
TIMER_NODES = [5, 38]
LOAD_NODES = [[8, 11, 0], [44, 47, 29]]
OHMS = np.array([[1_000, 10_000, 10_000], [100, 1_000, 10_000]])
TIMER_LIMIT_V = 20e-6
LOAD_LIMIT_A = 2e-9
FINE_TICKS = 8
HALF_FRAME_TICKS = 2048


def fixture(first, ticks, loads):
    return np.r_[first, np.column_stack((ticks, loads.reshape(-1, 6))).ravel()].astype("<f8").tobytes()


def project_loads(stages):
    """Form six effective hold voltages per 96 kHz interval from reference loads."""
    steps = HALF_FRAME_TICKS // FINE_TICKS
    x = (1. / OHMS).sum(axis=1) * FINE_TICKS / (10e-6 * 48_000 * 4096)
    # The original fine oracle uses two-stage Radau. Its final row weights
    # the two load stages in the ratio 4.5:(1.5+x) for this linear network.
    w1 = 4.5 / (6. + x)
    stage_loads = stages[1:, LOAD_NODES].reshape(-1, steps, 2, 2, 3)
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
    raw = run(cmd, data)
    got = np.frombuffer(raw, "<f8").reshape(-1, 2)
    assert got.shape == timers[1:].shape and np.isfinite(got).all()
    error = abs(got - timers[1:])
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


def main():
    assert c.AREA.is_dir() and not list(c.AREA.iterdir())
    seq = 1
    while (out := c.ROOT / f"evidence/rf_d_pilot_timer_rc{seq:02}.json").exists():
        seq += 1
    sources = Sources((*c.ALL_SOURCES, c.OWN, c.CANDIDATE, c.PROBE, c.PORTS,
                       "tools/rf_d_pilot_step_profile.rs", OWN, MODEL, PROBE, DOC))
    report = dict(passed=False, coupled=False, rack_integrated=False, clock_hz=96_000,
                  timer_nodes=TIMER_NODES, load_nodes=LOAD_NODES, load_ohms=OHMS.tolist(),
                  timer_limit_v=TIMER_LIMIT_V, load_limit_a=LOAD_LIMIT_A,
                  windows={}, **sources.fields(), compiler_sha256=c.sha(Path(c.COMPILER)),
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
            report["windows"][label] = dict(anchor_sha256=c.sha(anchor), reference_sha256=c.digest(raw),
                                             reference_events=events, key_v=key, start_frame=start,
                                             frames=frames, modes=results)
            print(label, results, flush=True)
            if branch == "positive":
                loads = nodes[regular][:, LOAD_NODES]
                inputs = np.tile(projected, (256 // len(projected) + 1, 1, 1))[:256]
                data = fixture(np.r_[nodes[0, TIMER_NODES], loads[0].ravel()],
                               np.full(256, HALF_FRAME_TICKS), inputs)
                measurements = list(map(int, run([timer, "bench-held"], data).decode().strip().split(",")))
                report["isolated_timer_benchmark"] = dict(
                    zip(("blocks", "median_ns", "p99_ns", "max_ns"), measurements),
                    host_frames=128, input_sha256=c.digest(data), includes_audio=False)
        report["passed"] = all(w["modes"]["projected_hold"]["passed"] for w in report["windows"].values())
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
