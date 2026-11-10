"""Benchmark the coupled RF-D positive path through one complete native block."""
import argparse
import os
from pathlib import Path
import subprocess
import traceback

import numpy as np

from affine_evidence import Sources
import check_rf_d_pilot_bistable_handoff as handoff
import check_rf_d_pilot_bistable_return as bistable
import check_rf_d_pilot_contours as c
from check_hybrid_voice import packed
from check_rf_d_pilot_precursor import (
    CALIBRATION, C4_CLOCK, SOURCE_NAMES, STEPS, TICK_S, TIMER_CARRY, TIMER_NATIVE,
    TIMER_NATIVE_PROBE, timer_native_fixture, timing_reference,
)
from check_rf_d_pilot_timer_rc import prepare_reference
from rf_d_pilot_attack_orbit import crossing_profile, landmarks
import rf_d_pilot_audio_readout as audio
from rf_d_pilot_precursor import charge_family, charge_trace
from rf_d_pilot_timer_carry import PORTS, post_family, post_trace

OWN = "tools/check_rf_d_pilot_bistable_block.py"
PREVIOUS = "evidence/rf_d_pilot_bistable_handoff18.json"
ADAPTER = "evidence/rf_d_pilot_bistable_block_adapter01.json"
FRAMES = 128
RATE = 48_000
BUDGET_NS = FRAMES * 1_000_000_000 // (2 * RATE)


def main():
    offsets = dict(bistable.POSITIVE_LOADS)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scene", choices=offsets, default="positive_c2_down")
    parser.add_argument("--newton-after", nargs="+", type=int, choices=(1, 2, 4, 8), default=[])
    args = parser.parse_args()
    assert len(set(args.newton_after)) == len(args.newton_after)
    assert c.AREA.is_dir() and not list(c.AREA.iterdir())
    seq = 1
    while (out := c.ROOT / f"evidence/rf_d_pilot_bistable_block{seq:02}.json").exists():
        seq += 1
    sources = Sources((*bistable.SOURCES, *c.ALL_SOURCES, c.OWN, c.CANDIDATE, c.PROBE, c.PORTS,
                       OWN, PREVIOUS, ADAPTER, handoff.OWN, *handoff.NATIVE, *SOURCE_NAMES, C4_CLOCK,
                       TIMER_CARRY, TIMER_NATIVE, TIMER_NATIVE_PROBE, *audio.SOURCES,
                       audio.FEEDBACK, *(path for _, path in audio.FEEDBACK_MODULES),
                       "crates/rf-d-circuit/src/prepared_chain_charge.rs",
                       "crates/rf-d-circuit/src/prepared_audio_stamp.rs"))
    report = dict(passed=False, completed=False, realtime=False, rack_integrated=False, frames=FRAMES,
                  sample_rate_hz=RATE, budget_ns=BUDGET_NS, scene=args.scene,
                  imposed_ports=(34, 17, 24, 14), c2_imposed_after_projection=True,
                  **sources.fields(), compiler_sha256=c.sha(Path(c.COMPILER)), library_sha256=c.sha(c.LIB))
    env = dict(os.environ, PATH="C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;" + os.environ["PATH"])
    anchor = c.AREA / "block.anchor"
    standalone = c.AREA / "block-clock.exe"

    def process(command, data=None):
        return subprocess.run(list(map(str, command)), cwd=c.ROOT, env=env, input=data,
                              capture_output=True, timeout=360)

    def run(command, data=None):
        result = process(command, data)
        assert result.returncode == 0, result.stderr.decode(errors="replace")
        return result.stdout

    def replay(command, data):
        result = process(command, data)
        again = process(command, data)
        assert (result.returncode, result.stdout, result.stderr) == (again.returncode, again.stdout, again.stderr)
        return result

    try:
        refs, report["reference_inputs"] = c.references()
        exe, build = prepare_reference(run, report, with_audio=True, stage_feedback=True)
        run([*build, "-A", "dead_code", c.ROOT / TIMER_NATIVE_PROBE,
             "--extern", f"rf_d_circuit={c.LIB}", "-o", standalone])
        _, branch, start, short_frames, key = c.WINDOWS[0]

        def seed(offset):
            phase, _, _, state = refs[branch][1][start]
            state = state.copy()
            state[0, handoff.TIMERS] += offset
            anchor.write_bytes(np.r_[state.ravel(), phase].astype("<f8").tobytes())
            return state, phase

        paths, timers, front, tail = [], [], [], []
        report["calibration"] = []
        for offset in CALIBRATION:
            seed(offset)
            raw = run([exe, "contour-capture-refined", anchor, start, short_frames, key])
            stages = np.frombuffer(raw, "<f8").reshape(-1, c.N)
            assert stages.shape == (1 + short_frames * STEPS * 4, c.N) and np.isfinite(stages).all()
            report["calibration"].append(dict(offset_v=offset, reference_sha256=c.digest(raw),
                                               anchor_sha256=c.sha(anchor)))
            slot, _, event = timing_reference(stages)
            cross = slot / bistable.PILOT_RATE + event["time"]
            paths.append(charge_trace(stages, (*PORTS, 34)))
            timers.append(post_trace(stages, cross, STEPS, (34, 27)))
            front.append(handoff.handoff_trace(stages, cross, 129))
            tail.append(handoff.handoff_trace(stages, cross, 129, intervals=2))
            if offset == (0., 0.):
                nominal = event
                small = run([exe, "contour-capture-audio-stages", anchor, start, short_frames, key])
                indices = 2 * STEPS * np.arange(short_frames * 2)[:, None] + [2 * STEPS // 3, 2 * STEPS]
                assert small == stages[np.r_[0, indices.ravel()]].astype("<f8").tobytes()
                report["compact_capture_control_sha256"] = c.digest(small)
        quarter = np.r_[np.arange(64) / 256., np.arange(32, 129) / 128.]
        grid, timer_model = charge_family(paths, quarter), post_family(timers)
        profiles = handoff.packed_profile(post_family(front)) + handoff.packed_profile(post_family(tail))
        _, post = landmarks(nominal, 24)
        prefix = np.r_[np.column_stack(crossing_profile(nominal)).ravel(), post[24:].ravel()]

        state, phase = seed(offsets[args.scene])
        report.update(start_frame=start, offset_v=offsets[args.scene], anchor_sha256=c.sha(anchor))
        print("Reference capture", args.scene, FRAMES, flush=True)
        result = process([exe, "contour-capture-audio-stages", anchor, start, FRAMES, key])
        assert result.returncode == 0, result.stderr.decode(errors="replace")
        reference = np.frombuffer(result.stdout, "<f8").reshape(-1, c.N)
        assert reference.shape == (1 + FRAMES * 4, c.N) and np.isfinite(reference).all()
        events = []
        for line in result.stderr.decode().splitlines():
            tag, *fields = line.split(",")
            assert tag == "SWITCH"
            events.append(list(map(int, fields)))
        prior = c.read(PREVIOUS)["cases"][args.scene]
        assert events == [prior["expected_event"]]
        report.update(reference_sha256=c.digest(result.stdout), reference_rows=len(reference),
                      reference_rate_hz=STEPS * bistable.PILOT_RATE, expected_events=events)
        expected = reference[1:].reshape(-1, 2, c.N)
        case = audio.Case(exe, env, state, phase, reference, joint=True, closed_cv=True)
        clock_data = timer_native_fixture(prefix, grid, timer_model, reference[0])
        standalone_event = run([standalone, "handoff"], clock_data)
        assert c.digest(standalone_event) == prior["clock"]["output_sha256"]
        # The timed block must build the precursor and cathodes internally.
        inputs = expected[..., (5, 34, 27, 17, 24, 14)].copy()
        inputs[..., 2] = 0.
        event = np.frombuffer(standalone_event, "<f8")
        standalone_slot = int(event[0])
        clock_cv = np.frombuffer(run([standalone, "cv-stages"], clock_data), "<f8").reshape(standalone_slot+1, 3)
        legacy = np.frombuffer(run([standalone], clock_data), "<f8")
        inputs[:standalone_slot+2, :, 0] = 0.
        payload = (case.anchor(0).astype("<f8").tobytes() + clock_data + profiles
                   + inputs.astype("<f8").tobytes())
        short = inputs[:short_frames*2].copy()
        short[:standalone_slot+1, 0, 0] = clock_cv[:, 2]
        short[:standalone_slot+1, 0, 2] = clock_cv[:, 0]
        short[:standalone_slot, 1, 0] = legacy[4:].reshape(standalone_slot+1, 8)[1:, 0]
        short[:standalone_slot, 1, 2] = clock_cv[:-1, 1]
        short_payload = (np.r_[case.anchor(0), event[[0, 1, 2, 5, 6]]].astype("<f8").tobytes()
                         + profiles + short.astype("<f8").tobytes())
        short_output = run([exe, "audio-readout-feedback-vector"], short_payload)
        assert c.digest(short_output) == prior["stage_feedback"]["output_sha256"]
        report["short_receiver_control_sha256"] = c.digest(short_output)
        mode = "audio-readout-feedback-block"
        print("Native block", args.scene, flush=True)
        report["candidates"] = {}
        for threshold in (0, *args.newton_after):
            options = [f"--newton-after={threshold}"] if threshold else []
            item = report if not threshold else dict(passed=False, completed=False, realtime=False,
                                                      newton_after=threshold)
            if threshold:
                report["candidates"][str(threshold)] = item
            got = replay([exe, mode, *options], payload)
            item.update(exit_code=got.returncode, input_sha256=c.digest(payload),
                          output_sha256=c.digest(got.stdout), unchanged_replay=True)
            if got.returncode:
                item.update(error=got.stderr.decode(errors="replace").strip())
                report["failure_input"] = packed(payload)
                print(item["error"], flush=True)
            else:
                item["completed"] = True
                values = np.frombuffer(got.stdout, "<f8")
                assert np.isfinite(values).all()
                slot, seconds, c2, a, b = values[:5]
                np.testing.assert_array_equal(values[:5], event[[0, 1, 2, 5, 6]])
                tick = start * 4096 + (slot / bistable.PILOT_RATE + seconds) / TICK_S
                active = np.arange(FRAMES * 4).reshape(-1, 2) >= 2 * int(slot) + 1
                rows = values[9:].reshape(-1, 55)
                latch = rows[:, 13:].reshape(-1, 2, 21)
                assert not np.any(latch[~active])
                stage_input = expected[..., (5, 34, 27)].copy()
                stage_input[..., 0][active] = latch[active, 20]
                stage_input[..., 2][active] = latch[active, 2]
                # Before the handoff the cathode/C2 diagnostic needs the actual clock stages.
                stage_input[:int(slot)+1, 0, 0] = clock_cv[:, 2]
                stage_input[:int(slot), 1, 0] = legacy[4:].reshape(int(slot)+1, 8)[1:, 0]
                stage_input[..., 2][~active] = clock_cv[:, :2].ravel()[:-1]
                audio_error = audio.assess_readout(rows[:, :13], audio.endpoint_reference(expected[:, 1]),
                                                   expected, stage_input[..., :2], stage_input[..., 2])
                contour_error = handoff.assess(latch[active, :20], expected[active])
                c2_error = float(abs(latch[int(slot)+1, :, 20] - expected[int(slot)+1, :, 5]).max())
                max_iterations, load_error, r59_error, evaluations = values[5:9]
                item.update(predicted_tick=float(tick), event_matches=bool(events[0][0] <= tick <= events[0][1]),
                              order_preserved=bool((latch[active, 1] >= latch[active, 3]).all()),
                              audio=audio_error, latch=contour_error, projected_c2_error_v=c2_error,
                              max_iterations=int(max_iterations), max_load_error_v=float(load_error),
                              r59_mismatch_a=float(r59_error), latch_evaluations=int(evaluations))
                item["passed"] = bool(item["event_matches"] and item["order_preserved"] and audio_error["passed"]
                                        and contour_error["passed"] and c2_error <= 2e-6
                                        and load_error <= 1e-10 and r59_error <= 2e-12)
                if not item["passed"]:
                    report["failure_input"] = packed(payload)
                timing = run([exe, mode + "-bench", *options], payload).decode().strip().splitlines()
                assert len(timing) == (2 if threshold else 1)
                def decode_timing(row):
                    return dict(zip(("blocks", "median_ns", "p99_ns", "max_ns"),
                                    map(int, row.split(",")), strict=True))
                item["timing"] = decode_timing(timing[-1])
                if threshold:
                    item["alternating_control_timing"] = decode_timing(timing[0])
                    item["median_ratio_to_control"] = (item["timing"]["median_ns"] /
                                                          item["alternating_control_timing"]["median_ns"])
                item["realtime"] = item["passed"] and item["timing"]["max_ns"] <= BUDGET_NS
                print("Timing", threshold, item["timing"], "electrical", item["passed"], flush=True)
        report["all_candidates_passed"] = all(item["passed"] for item in report["candidates"].values())
        sources.unchanged()
    except Exception:
        report["failure"] = traceback.format_exc()
        raise
    finally:
        for path in c.AREA.iterdir():
            assert path.is_file() and path.resolve().parent == c.AREA.resolve()
            path.unlink()
        c.write(out, report)
    raise SystemExit(0 if report["passed"] and report["all_candidates_passed"] else 1)


if __name__ == "__main__":
    main()
