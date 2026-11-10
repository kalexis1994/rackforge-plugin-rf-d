"""Check the bidirectional pilot contours on independent full solver reserves."""
import json
import os
import subprocess
import traceback
from pathlib import Path

import numpy as np

from affine_evidence import Sources
import check_rf_d_pilot_contours as c
from check_rf_d_pilot_split_returns import CONTOURS, inspect_reserve, packed

OWN = "tools/check_rf_d_pilot_closed_returns.py"
MODEL = "tools/rf_d_pilot_closed_returns.rs"
CLOCK = "tools/rf_d_pilot_contour_clock.rs"
MODES = ((256, 8, 0), (256, 8, 3), (1, 3, 0))
POLICIES = {1: 'adaptive', 2: 'port_clock', 3: 'latch_clock'}
CHANNELS = (c.J7, None, None, 5, 38, 3, 37, 54, 55, 26, 28)


def validate(raw, reference, info, stride, adaptive):
    full = np.frombuffer(reference, "<f8").reshape(-1, c.N)
    values = np.frombuffer(raw, "<f8")
    if adaptive:
        records = values.reshape(-1, 1 + 2 * len(CHANNELS))
        steps = records[:, 0].astype(int)
        assert np.array_equal(steps, records[:, 0])
        assert np.isin(steps, [1 << k for k in range(9)]).all()
        candidate = records[:, 1:].reshape(len(steps), 2, len(CHANNELS))
    else:
        candidate = values.reshape(-1, 2, len(CHANNELS))
        steps = np.full(len(candidate), stride)
    ticks = np.cumsum(steps)
    assert ticks[-1] == info["frames"] * 512
    assert np.all(np.searchsorted(ticks, np.arange(stride, ticks[-1] + 1, stride)) < len(ticks))
    assert np.all(ticks[np.searchsorted(ticks, np.arange(stride, ticks[-1] + 1, stride))]
                  == np.arange(stride, ticks[-1] + 1, stride))
    # Compare both fine stages or accepted endpoints at the same fine-grid times.
    both_stages = stride == 1 and not adaptive
    samples = full[1:] if both_stages else full[2 * ticks]
    trial = candidate.reshape(-1, len(CHANNELS)) if both_stages else candidate[:, 1, :]
    want = np.column_stack([samples[:, node] if node is not None else
                            (samples[:, 3] - samples[:, 54]) / 68_000. if k == 1 else
                            (samples[:, 55] - samples[:, 37]) / 680.
                            for k, node in enumerate(CHANNELS)])
    error = trial - want
    worst = np.max(abs(error), axis=0)
    initial = full[0, 26] >= full[0, 28]
    sign = np.r_[initial, candidate[:, 1, -2] >= candidate[:, 1, -1]]
    base = info["start_frame"] * 4096
    switches = [[base + int(ticks[i] - steps[i]) * 8, base + int(ticks[i]) * 8, int(sign[i + 1])]
                for i in np.flatnonzero(sign[1:] != sign[:-1])]
    weights = np.ones(len(error)) if both_stages else np.sqrt(steps)
    relative = np.linalg.norm(weights * error[:, 0]) / np.linalg.norm(weights * want[:, 0])
    sizes, counts = np.unique(steps, return_counts=True)
    histogram = dict(zip(map(int, sizes), map(int, counts)))
    return dict(passed=bool(np.isfinite(candidate).all() and switches == info["expected_events"]
                            and max(worst[1:3]) <= 2e-9 and max(worst[3:]) <= 20e-6
                            and relative <= .001 and worst[0] <= .003 * max(abs(want[:, 0]))
                            and abs(np.mean(error[:, 0])) <= 1e-6),
                switches=switches, max_error=worst.tolist(), j7_rms_relative=float(relative),
                stride_histogram=histogram)


def main():
    assert not list(c.AREA.iterdir())
    seq = 1
    while (out := c.ROOT / f"evidence/rf_d_pilot_closed_returns{seq:02}.json").exists():
        seq += 1
    sources = Sources((*c.ALL_SOURCES, c.OWN, c.CANDIDATE, c.PROBE, c.PORTS, OWN, MODEL, CLOCK,
                       "tools/check_rf_d_pilot_split_returns.py", CONTOURS))
    report = dict(passed=False, rack_integrated=False, source_boundary="loaded x2/x4",
                  windows={}, **sources.fields(), compiler_sha256=c.sha(Path(c.COMPILER)),
                  library_sha256=c.sha(c.LIB))
    env = dict(os.environ, PATH="C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;" + os.environ["PATH"])

    def run(args):
        return subprocess.run(list(map(str, args)), cwd=c.ROOT, env=env, capture_output=True, timeout=240)

    try:
        prior = json.loads((c.ROOT / CONTOURS).read_text(encoding="utf8"))
        refs, report["reference_inputs"] = c.references()
        table, *_ = c.materialize(c.read_oracle())
        assert c.digest(table) == c.read(c.MODEL)["table_sha256"]
        table_path = c.AREA / c.TABLE
        table_path.write_bytes(table)
        kernel = c.emit("family-kernel.rs", c.text(c.KERNEL)
                        .replace("H128_VOICE_TABLE_PATH", table_path.as_posix())
                        .replace("VCO_PANEL_PORT_PATH", (c.ROOT / c.PANEL).as_posix()))
        probe = c.component(kernel)
        code = c.once(probe.read_text(encoding="utf8"), '        Some("ports") => ports(),', '''
        Some("ports") => ports(),
        Some("closed-returns") if args.len() == 8 =>
            closed_returns::run(&args[2], args[3].parse()?, args[4].parse()?, args[5].parse()?, args[6].parse()?, args[7].parse()?),''')
        code += f'\n#[path = "{(c.ROOT / MODEL).as_posix()}"] mod closed_returns;\n'
        probe = c.emit(probe.name, code)
        exe = c.AREA / "pilot-closed-returns.exe"
        built = run([c.COMPILER, "--edition=2021", "-C", "opt-level=3", "-C", "target-feature=+fma",
                     "-C", "link-arg=-Wl,--stack,33554432", "--cfg", "laboratory", "--cfg", "pilot_loaded_filter", "--cfg", "pilot_closed_cv",
                     "-A", "dead_code", probe, "--extern", f"rf_d_circuit={c.LIB}", "-o", exe])
        assert built.returncode == 0, built.stderr.decode(errors="replace")
        anchor = c.AREA / "closed-returns.anchor"
        for label, branch, start, frames, key in c.WINDOWS:
            phase, _, _, state = refs[branch][1][start]
            anchor.write_bytes(packed(np.r_[state.ravel(), phase]))
            info = prior["windows"][label]
            assert c.sha(anchor) == info["anchor_sha256"]
            ref = run([exe, "contour-capture", anchor, start, frames, key])
            assert ref.returncode == 0, ref.stderr.decode(errors="replace")
            entry = report["windows"][label] = dict(reference=inspect_reserve(ref.stdout, info), modes={})
            for stride, budget, policy in MODES:
                adaptive = policy != 0
                cmd = [exe, "closed-returns", anchor, key, frames, stride, budget, policy]
                trial = run(cmd)
                stderr = trial.stderr.decode(errors="replace").strip()
                result = dict(exit_code=trial.returncode, output_sha256=c.digest(trial.stdout), passed=False)
                mode = POLICIES[policy] if adaptive else f"{stride}_{budget}"
                entry["modes"][mode] = result
                if trial.returncode == 0:
                    tag, time, outer, audio, mismatch, solve, defect, switch, worst = stderr.split(",")
                    assert tag == "PORTS"
                    result.update(validate(trial.stdout, ref.stdout, info, stride, adaptive))
                    result.update(max_frame_ns=int(time), max_outer_iterations=int(outer),
                                  max_audio_iterations=int(audio), max_port_mismatch_v=float(mismatch),
                                  rejections=dict(solve=int(solve), defect=int(defect), switch=int(switch)),
                                  max_accepted_defect=float(worst))
                else:
                    result["error"] = stderr
                if adaptive or not result["passed"]:
                    replay = run(cmd)
                    assert trial.returncode == replay.returncode and trial.stdout == replay.stdout
                    assert trial.returncode == 0 or trial.stderr == replay.stderr
                    result["unchanged_replay"] = True
                print(label, mode, result, flush=True)
        report["passed"] = all(entry["modes"]["1_3"]["passed"] and entry["modes"]["latch_clock"]["passed"]
                               for entry in report["windows"].values())
        sources.unchanged()
    except Exception:
        report["failure"] = traceback.format_exc()
        raise
    finally:
        c.write(out, report)
        for path in c.AREA.iterdir():
            assert path.is_file() and path.resolve().parent == c.AREA.resolve()
            path.unlink()
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
