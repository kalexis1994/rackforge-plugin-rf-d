"""Close the receiver under the contour load observations at 96 kHz."""
import subprocess
from dataclasses import dataclass

import numpy as np

import check_rf_d_pilot_contours as c
from check_hybrid_voice import packed
from check_rf_d_pilot_closed_returns import radau_devices
from validate_vco_family_voice_bus import BUS, J7

MODEL = "tools/rf_d_pilot_audio_readout.rs"
PARENT = "tools/rf_d_pilot_closed_returns.rs"
FEEDBACK = "tools/rf_d_pilot_audio_feedback.rs"
FEEDBACK_MODULES = (("attack_cell", "tools/rf_d_pilot_attack_cell.rs"),
                    ("bistable", "tools/rf_d_pilot_bistable_return.rs"),
                    ("handoff", "tools/rf_d_pilot_bistable_handoff.rs"),
                    ("q15", "tools/rf_d_pilot_q15_return.rs"),
                    ("timer", "tools/rf_d_pilot_timer_rc.rs"))
SOURCES = ("tools/rf_d_pilot_audio_readout.py", MODEL, PARENT,
           "tools/check_rf_d_pilot_closed_returns.py", "tools/rf_d_pilot_contour_clock.rs",
           "tools/rf_d_pilot_reduced_audio.rs", "tools/rf_d_reduced_contour_live.py",
           "tools/check_rf_d_reduced_contour_ports.py")
FINE_ROWS = 1536
DRIVES = [5, 34]
LOADS = [54, 55]
CR6_SCALE_V = 1.5 * (1.380649e-23 * 298.15 / 1.602176634e-19)


def prepare(probe, report, stage_feedback=False):
    devices, underflow = radau_devices()
    report["audio_devices"] = dict(sha256=c.sha(devices), unit_bias_underflow_columns=underflow)
    code = c.once(probe.read_text(encoding="utf8"), '        Some("ports") => ports(),', '''
        Some("ports") => ports(),
        Some("audio-readout") => closed_returns::run_audio_readout(false, false, false),
        Some("audio-readout-bench") => closed_returns::run_audio_readout(true, false, false),
        Some("audio-readout-joint") => closed_returns::run_audio_readout(false, true, false),
        Some("audio-readout-compare") => closed_returns::run_audio_readout(true, true, false),
        Some("audio-readout-cv") => closed_returns::run_audio_readout(false, true, true),
        Some("audio-readout-cv-loads") => closed_returns::run_audio_stage_loads(),
        Some("audio-readout-cv-bench") => closed_returns::run_audio_readout(true, true, true),''')
    code += f'\n#[path = "{(c.ROOT / PARENT).as_posix()}"] mod closed_returns;\n'
    code += f'#[path = "{devices.as_posix()}"] mod radau_devices;\n'
    if stage_feedback:
        code = c.once(code, '        Some("ports") => ports(),', '''
        Some("ports") => ports(),
        Some("audio-readout-feedback") => closed_returns::run_audio_feedback(false, false, false),
        Some("audio-readout-feedback-bench") => closed_returns::run_audio_feedback(true, false, false),
        Some("audio-readout-feedback-frozen") => closed_returns::run_audio_feedback(false, true, false),
        Some("audio-readout-feedback-compare") => closed_returns::run_audio_feedback(true, true, true),
        Some("audio-readout-feedback-profile") => closed_returns::run_audio_feedback(true, true, false),
        Some("audio-readout-feedback-packed") => closed_returns::run_audio_feedback_packed(false),
        Some("audio-readout-feedback-packed-bench") => closed_returns::run_audio_feedback_packed(true),
        Some("audio-readout-feedback-seeded") => closed_returns::run_audio_feedback_seeded(false),
        Some("audio-readout-feedback-seeded-bench") => closed_returns::run_audio_feedback_seeded(true),''')
        code += '\nuse latch_charge as latch_charge_driver;\n'
        for name, path in FEEDBACK_MODULES:
            code += f'\n#[path = "{(c.ROOT / path).as_posix()}"] mod {name};\n'
    return c.emit(probe.name, code)


def endpoint_reference(reference):
    return np.column_stack((reference[:, J7], (reference[:, 3] - reference[:, 54]) / 68_000.,
                            (reference[:, 55] - reference[:, 37]) / 680., reference[:, [3, 37, *LOADS]]))


def assess_readout(rows, wanted, expected_stages, drives, cathode=None):
    assert rows[:, :7].shape == wanted.shape and np.isfinite(rows).all()
    error = rows[:, :7] - wanted
    max_error = abs(error).max(axis=0)
    rms = float(np.linalg.norm(error[:, 0]) / np.linalg.norm(wanted[:, 0]))
    peak = float(max_error[0] / abs(wanted[:, 0]).max())
    mean = float(abs(np.mean(error[:, 0])))
    result = dict(passed=bool(rms <= .001 and peak <= .003 and mean <= 1e-6
                              and max_error[1:3].max() <= 2e-9 and max_error[3:].max() <= 20e-6),
                  max_error=max_error.tolist(), j7_rms_relative=rms, j7_peak_relative=peak, j7_mean_v=mean)
    if cathode is not None:
        cv, wanted_cathode = expected_stages[..., 4], expected_stages[..., 27]
        wanted_cr6 = 1e-8 * np.expm1((cv - wanted_cathode) / CR6_SCALE_V)
        voltage_error = float(abs(rows[:, 7:9] - cv).max())
        current_error = float(abs(rows[:, 9:11] - wanted_cr6).max())
        result.update(max_x4_error_v=voltage_error, max_cr6_error_a=current_error,
                      max_stage_c2_error_v=float(abs(drives[:, 0, 0] - expected_stages[:, 0, 5]).max()),
                      max_x27_error_v=float(abs(cathode - wanted_cathode).max()),
                      reference_cr6_range_a=[float(wanted_cr6.min()), float(wanted_cr6.max())])
        result["passed"] &= voltage_error <= 20e-6 and current_error <= 2e-9
    return result


@dataclass
class Case:
    target: object
    env: dict
    state: np.ndarray
    phase: float
    stages: np.ndarray
    joint: bool = False
    closed_cv: bool = False

    def run(self, mode, payload):
        return subprocess.run([str(self.target), mode], cwd=c.ROOT, env=self.env,
                              input=payload, capture_output=True, timeout=60)

    def anchor(self, first):
        if first:
            seed = np.r_[self.stages[first * FINE_ROWS], np.zeros(c.N)]
        else:
            seed = self.state.ravel()
        prefix = self.stages[1:first * FINE_ROWS + 1, BUS]
        return np.r_[seed, self.phase, len(prefix) // 2, prefix]

    def stage_payload(self, first, stages):
        return np.r_[self.anchor(first), stages.ravel()].astype("<f8").tobytes()

    def compare(self, first, generated=None, stage_sum=None, stage_cathode=None, stage_c2=None, *,
                exact_stages=None, time_exact=True):
        anchor = self.anchor(first)
        count = len(exact_stages) if exact_stages is not None else len(generated) - 1
        slot = np.arange(first, first + count)
        indices = slot[:, None] * FINE_ROWS + np.array([FINE_ROWS // 3, FINE_ROWS])
        reference = self.stages[indices[:, 1]]
        wanted = endpoint_reference(reference)
        assert np.linalg.norm(wanted[:, 0]) > 0.
        cv = self.stages[indices, 4]
        oracle = self.stages[indices[:, 1] - FINE_ROWS, :][:, DRIVES]
        oracle = np.vstack((oracle, reference[-1, DRIVES]))

        def foh(boundaries):
            return np.stack((boundaries[:-1] + (boundaries[1:] - boundaries[:-1]) / 3.,
                             boundaries[1:]), axis=1)

        def measure(drives, timing=False, joint=False, cathode=None):
            drive = cv if cathode is None else cathode
            data = np.r_[anchor, np.concatenate((drives, drive[..., None]), axis=2).ravel()].astype("<f8").tobytes()
            mode = "audio-readout-joint" if joint else "audio-readout"
            if cathode is not None:
                mode = "audio-readout-cv"
            raw = self.run(mode, data)
            replay = self.run(mode, data)
            assert (raw.returncode, raw.stdout, raw.stderr) == (replay.returncode, replay.stdout, replay.stderr)
            result = dict(passed=False, steps=len(reference), unchanged_replay=True,
                          input_sha256=c.digest(data), output_sha256=c.digest(raw.stdout))
            if raw.returncode:
                return dict(result, error=raw.stderr.decode(errors="replace").strip(), failure_input=packed(data))
            values = np.frombuffer(raw.stdout, "<f8")
            rows = values[3:].reshape(-1, 7 if cathode is None else 11)
            result.update(assess_readout(rows, wanted, self.stages[indices], drives, cathode),
                          max_load_iterations=int(values[0]), max_load_mismatch_v=float(values[1]),
                          checked_nodal_proposals=int(values[2]))
            if not result["passed"]:
                result["failure_input"] = packed(data)
            if timing:
                mode = "audio-readout-compare" if joint else "audio-readout-bench"
                if cathode is not None:
                    mode = "audio-readout-cv-bench"
                measured = self.run(mode, data)
                assert measured.returncode == 0, measured.stderr.decode(errors="replace")
                labels = ("windows", "median_ns", "p99_ns", "max_ns")
                timings = [dict(zip(labels, map(int, row.split(",")), strict=True))
                           for row in measured.stdout.decode().splitlines()]
                if joint and cathode is None:
                    before, after = timings
                    result["timing"] = dict(alternating=True, nested=before, joint=after,
                                            median_speedup=before["median_ns"] / after["median_ns"])
                else:
                    result["timing"], = timings
            return result

        if exact_stages is not None:
            assert self.closed_cv and exact_stages.shape == (count, 2, 3) and np.isfinite(exact_stages).all()
            control = measure(self.stages[indices[:, :, None], DRIVES], joint=True, cathode=self.stages[indices, 27])
            trial = measure(exact_stages[:, :, :2], timing=time_exact, joint=True, cathode=exact_stages[:, :, 2])
            return dict(passed=control["passed"] and trial["passed"], first_slot=first,
                        reference_peak_j7_v=float(abs(wanted[:, 0]).max()),
                        closed_cv_oracle=control, closed_cv_generated=trial)

        results = dict(oracle_stages=measure(self.stages[indices[:, :, None], DRIVES]),
                       oracle_foh=measure(foh(oracle)), generated_foh=measure(foh(generated), timing=True))
        stages = foh(generated)
        if stage_sum is None:
            passed = all(row["passed"] for row in results.values())
        else:
            stages[:, 0, 1] = stage_sum
            results["generated_c7_stage"] = measure(stages, timing=True)
            passed = results["oracle_stages"]["passed"] and results["generated_c7_stage"]["passed"]
        if self.joint:
            results["generated_joint"] = measure(stages, timing=True, joint=True)
            passed &= results["generated_joint"]["passed"]
        if self.closed_cv:
            assert stage_cathode.shape == cv.shape and np.isfinite(stage_cathode).all()
            results["closed_cv_oracle"] = measure(
                self.stages[indices[:, :, None], DRIVES], joint=True, cathode=self.stages[indices, 27])
            if stage_c2 is not None:
                assert stage_c2.shape == cv[:, 0].shape and np.isfinite(stage_c2).all()
                stages[:, 0, 0] = stage_c2
            results["closed_cv_generated"] = measure(stages, timing=True, joint=True, cathode=stage_cathode)
            passed &= results["closed_cv_oracle"]["passed"] and results["closed_cv_generated"]["passed"]
        return dict(passed=passed, first_slot=first,
                    reference_peak_j7_v=float(abs(wanted[:, 0]).max()), **results)
