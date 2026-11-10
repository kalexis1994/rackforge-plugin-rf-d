"""Validate the C7-clocked negative timer carry with held-out C2/C5 loads."""
import argparse
import os
import subprocess
import traceback
from pathlib import Path

import numpy as np

from affine_evidence import Sources
import check_rf_d_pilot_contours as c
import rf_d_pilot_return_readout as returns
from check_rf_d_pilot_timer_rc import ATTACK, ATTACK_PROBE, MODEL, OHMS, TIMER_NODES, prepare_reference
from rf_d_pilot_negative_timers import family, key_side, run as render, trace

CALIBRATION = ((0., 0.), (.01, 0.), (-.01, 0.), (0., .01), (0., -.01))
RESERVES = ((0., 0.), (.005, -.005), (-.005, .005))
SOURCE_NAMES = (
    "tools/check_rf_d_pilot_negative_timers.py", "tools/rf_d_pilot_negative_timers.py",
    "tools/rf_d_pilot_timer_carry.py", "tools/rf_d_pilot_precursor.py",
    "tools/check_rf_d_pilot_timer_rc.py", ATTACK, ATTACK_PROBE, MODEL,
)
NATIVE = "tools/rf_d_pilot_negative_timers_probe.rs"
NATIVE_SOURCES = (NATIVE, "tools/rf_d_pilot_negative_timers.rs", "tools/rf_d_pilot_timer_carry.rs",
                  "tools/rf_d_pilot_c4_clock.rs", "tools/rf_d_pilot_crossing.rs",
                  "tools/rf_d_pilot_precursor.rs", "tools/latch_charge_driver.rs")


def compare(evaluate, model, stages, seed, key, frames, native=None, readout=None, audio=None):
    reference = stages[::1536]
    output = render(evaluate, model, reference[0], seed, key, frames)
    if output is None:
        return dict(passed=False, reason="outside negative C7 path")
    timers, nodes, c7 = output
    attack = evaluate(nodes[:, 1:3], timers)
    passive = (nodes[:, 5:9].reshape(-1, 2, 2) - timers[:, :, None]) / OHMS[:, 1:]
    currents = np.concatenate((attack[..., None], passive), axis=2)
    wanted = (reference[:, [[8, 11, 0], [44, 47, 29]]] - reference[:, TIMER_NODES, None]) / OHMS
    # Compare the first resolved 96 kHz boundary and all later ones.
    current = abs(currents[1:] - wanted[1:]).max(axis=0)
    timer = abs(timers - reference[:, TIMER_NODES]).max(axis=0)
    c7_error = float(abs(c7 - reference[:, 21]).max())
    x22_error = float(abs(key_side(c7, key)[1:] - reference[1:, 22]).max())
    quiet = bool((nodes[:, 1] > nodes[:, 3]).all() and (nodes[:, 2] > nodes[:, 4]).all())
    item = dict(passed=bool(quiet and timer.max() <= 2e-6 and current.max() <= 2e-9 and c7_error <= 20e-6),
                no_crossing=quiet, max_timer_error_v=timer.tolist(), max_current_error_a=current.tolist(),
                max_c7_error_v=c7_error, max_key_port_error_v=x22_error,
                output_sha256=c.digest(np.column_stack((timers, c7, nodes[:, :9])).astype("<f8").tobytes()))
    if native is not None:
        run, target = native
        direction, progress, center, linear, quadratic = model
        table = np.column_stack((progress, center.T, linear[0].T, linear[1].T,
                                 quadratic[0].T, quadratic[1].T))
        initial = reference[0, [5, 38, 21, 26, 28, 40, 42]]
        data = np.r_[direction, seed[TIMER_NODES], table.ravel(), initial, key, frames * 2].astype("<f8").tobytes()
        raw = run([target], data)
        assert raw == run([target], data)
        got = np.frombuffer(raw, "<f8").reshape(-1, 10)
        expected = np.column_stack((timers, c7, key_side(c7, key), currents.reshape(-1, 6)))
        assert got.shape == expected.shape and np.isfinite(got).all()
        delta = abs(got - expected).max(axis=0)
        assert delta[:4].max() <= 1e-12 and delta[4:].max() <= 1e-14
        solved_current = abs(got[1:, 4:].reshape(-1, 2, 3) - wanted[1:]).max()
        assert solved_current <= 2e-9
        assert abs(got[:, :2] - reference[:, TIMER_NODES]).max() <= 2e-6
        timing = list(map(int, run([target, "bench"], data).decode().strip().split(",")))
        item["native"] = dict(passed=True, max_difference_python=delta.tolist(),
                              input_sha256=c.digest(data), output_sha256=c.digest(raw),
                              timing=dict(zip(("edges", "median_ns", "p99_ns", "max_ns"), timing)))
        if readout is not None:
            cmd = [target, "returns"]
            with_sum = run(cmd, data)
            assert with_sum == run(cmd, data)
            rows = np.frombuffer(with_sum, "<f8").reshape(-1, 11)
            assert np.array_equal(rows[:, :10], got)
            assert abs(rows[:, 10] - nodes[:, 9]).max() <= 1e-12
            drives = rows[:, [0, 10]]
            item["returns"] = returns.assess(run, readout, reference, drives, 1)
            if audio is not None:
                command = [target, "stage-sum"]
                raw_sum = run(command, data)
                assert raw_sum == run(command, data)
                stage_sum = np.frombuffer(raw_sum, "<f8")
                assert stage_sum.shape == (len(drives) - 1,) and np.isfinite(stage_sum).all()
                cathode = None
                if audio.closed_cv:
                    command = [target, "cv-stages"]
                    raw_cv = run(command, data)
                    assert raw_cv == run(command, data)
                    cathode = np.frombuffer(raw_cv, "<f8").reshape(len(drives) - 1, 2)
                item["audio_readout"] = audio.compare(0, drives, stage_sum, cathode)
    return item


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--native", action="store_true", help="verify and time the bounded Rust C7 clock")
    parser.add_argument("--returns", action="store_true", help="contrast return readout at imposed receiver loads")
    parser.add_argument("--audio", action="store_true", help="close base and TAIL with the reduced audio receiver")
    parser.add_argument("--audio-joint", action="store_true", help="compare the joint and nested audio loops")
    parser.add_argument("--audio-cv", action="store_true", help="close R24/R27 and CR6 with generated x27")
    args = parser.parse_args()
    assert not args.audio_cv or args.audio_joint
    assert not args.audio_joint or args.audio
    assert not args.audio or args.returns
    assert not args.returns or args.native
    assert c.AREA.is_dir() and not list(c.AREA.iterdir())
    seq = 1
    prefix = "rf_d_pilot_audio_readout_neg" if args.audio else "rf_d_pilot_negative_timers"
    if args.audio_cv:
        prefix = "rf_d_pilot_cv_readout_neg"
    while (out := c.ROOT / f"evidence/{prefix}{seq:02}.json").exists():
        seq += 1
    native_sources = NATIVE_SOURCES if args.native else ()
    if args.returns:
        native_sources += ("tools/rf_d_pilot_return_readout.py", *returns.SOURCES)
    if args.audio:
        import rf_d_pilot_audio_readout as audio
        native_sources += audio.SOURCES
    sources = Sources((*c.ALL_SOURCES, c.OWN, c.CANDIDATE, c.PROBE, c.PORTS,
                       "tools/rf_d_pilot_step_profile.rs", *SOURCE_NAMES, *native_sources))
    report = dict(passed=False, rack_integrated=False, clock_hz=96_000, native=args.native, returns=args.returns, edges={},
                  **sources.fields(), compiler_sha256=c.sha(Path(c.COMPILER)), library_sha256=c.sha(c.LIB))
    env = dict(os.environ, PATH="C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;" + os.environ["PATH"])

    def run(command, data=None):
        proc = subprocess.run(list(map(str, command)), cwd=c.ROOT, env=env, input=data,
                              capture_output=True, timeout=240)
        assert proc.returncode == 0, proc.stderr.decode(errors="replace")
        return proc.stdout

    try:
        refs, report["reference_inputs"] = c.references()
        oracle, build = prepare_reference(run, report, args.audio)
        attack = c.AREA / "pilot-negative-attack.exe"
        run([*build, "-A", "dead_code", c.ROOT / ATTACK_PROBE, "-o", attack])
        native = None
        if args.native:
            executable = c.AREA / "pilot-negative-timers.exe"
            run([*build, "-A", "dead_code", c.ROOT / NATIVE, "--extern",
                 f"rf_d_circuit={c.LIB}", "-o", executable])
            native = run, executable
        readout = returns.prepare(run, build) if args.returns else None
        anchor = c.AREA / "negative-timers.bin"

        def evaluate(latch, timer):
            data = np.stack((latch, timer), axis=-1).astype("<f8").tobytes()
            result = np.frombuffer(run([attack], data), "<f8").reshape(-1, 2, 4)
            return result[:, :, 2]

        def capture(branch, start, frames, key, offset):
            phase, _, _, state = refs[branch][1][start]
            state = state.copy()
            state[0, TIMER_NODES] += offset
            anchor.write_bytes(np.asarray(np.r_[state.ravel(), phase], "<f8").tobytes())
            raw = run([oracle, "contour-capture-refined", anchor, start, frames, key])
            stages = np.frombuffer(raw, "<f8").reshape(-1, c.N)
            assert stages.shape[0] == 1 + frames * 3072 and np.isfinite(stages).all()
            return stages, dict(anchor_sha256=c.sha(anchor), reference_sha256=c.digest(raw), offset_v=offset,
                                start_frame=start, frames=frames, key_v=key)

        for label, branch, start, frames, key in c.WINDOWS[1:]:
            item = report["edges"][label] = dict(calibration=[], trials=[])
            curves = []
            for offset in CALIBRATION:
                stages, meta = capture(branch, start, frames + 1, key, offset)
                curves.append(trace(stages))
                item["calibration"].append(meta)
                if offset == (0., 0.):
                    seed = stages[0].copy()
            model = family(curves)
            for offset in RESERVES:
                stages, meta = capture(branch, start, frames, key, offset)
                trace(stages)  # Preserve the reference branch on the held-out scene.
                result = compare(evaluate, model, stages, seed, key, frames)
                assert result == compare(evaluate, model, stages, seed, key, frames)
                if native is not None:
                    audio_case = None
                    if args.audio:
                        phase, _, _, state = refs[branch][1][start]
                        state = state.copy()
                        state[0, TIMER_NODES] += offset
                        audio_case = audio.Case(oracle, env, state, phase, stages, args.audio_joint, args.audio_cv)
                    result = compare(evaluate, model, stages, seed, key, frames, native, readout, audio_case)
                item["trials"].append(dict(meta, **result, unchanged_replay=True))
                print(label, offset, result, flush=True)
        report["passed"] = all(trial["passed"] for edge in report["edges"].values() for trial in edge["trials"])
        if args.returns:
            report["return_readout_passed"] = all(
                trial["returns"]["passed"] for edge in report["edges"].values() for trial in edge["trials"])
            report["passed"] &= report["return_readout_passed"]
        if args.audio:
            report["audio_readout_passed"] = all(
                trial["audio_readout"]["passed"] for edge in report["edges"].values() for trial in edge["trials"])
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
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
