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
SOURCES = ("tools/rf_d_pilot_audio_readout.py", MODEL, PARENT,
           "tools/check_rf_d_pilot_closed_returns.py", "tools/rf_d_pilot_contour_clock.rs",
           "tools/rf_d_pilot_reduced_audio.rs", "tools/rf_d_reduced_contour_live.py",
           "tools/check_rf_d_reduced_contour_ports.py")
FINE_ROWS = 1536
DRIVES = [5, 34]
LOADS = [54, 55]


def prepare(probe, report):
    devices, underflow = radau_devices()
    report["audio_devices"] = dict(sha256=c.sha(devices), unit_bias_underflow_columns=underflow)
    code = c.once(probe.read_text(encoding="utf8"), '        Some("ports") => ports(),', '''
        Some("ports") => ports(),
        Some("audio-readout") => closed_returns::run_audio_readout(false),
        Some("audio-readout-bench") => closed_returns::run_audio_readout(true),''')
    code += f'\n#[path = "{(c.ROOT / PARENT).as_posix()}"] mod closed_returns;\n'
    code += f'#[path = "{devices.as_posix()}"] mod radau_devices;\n'
    return c.emit(probe.name, code)


@dataclass
class Case:
    target: object
    env: dict
    state: np.ndarray
    phase: float
    stages: np.ndarray

    def run(self, mode, payload):
        return subprocess.run([str(self.target), mode], cwd=c.ROOT, env=self.env,
                              input=payload, capture_output=True, timeout=60)

    def compare(self, first, generated):
        if first:
            seed = np.r_[self.stages[first * FINE_ROWS], np.zeros(c.N)]
        else:
            seed = self.state.ravel()
        prefix = self.stages[1:first * FINE_ROWS + 1, BUS]
        anchor = np.r_[seed, self.phase, len(prefix) // 2, prefix]
        slot = np.arange(first, first + len(generated) - 1)
        indices = slot[:, None] * FINE_ROWS + np.array([FINE_ROWS // 3, FINE_ROWS])
        reference = self.stages[indices[:, 1]]
        wanted = np.column_stack((reference[:, J7],
                                  (reference[:, 3] - reference[:, 54]) / 68_000.,
                                  (reference[:, 55] - reference[:, 37]) / 680.,
                                  reference[:, [3, 37, *LOADS]]))
        assert np.linalg.norm(wanted[:, 0]) > 0.
        cv = self.stages[indices, 4]
        oracle = self.stages[indices[:, 1] - FINE_ROWS, :][:, DRIVES]
        oracle = np.vstack((oracle, reference[-1, DRIVES]))

        def foh(boundaries):
            return np.stack((boundaries[:-1] + (boundaries[1:] - boundaries[:-1]) / 3.,
                             boundaries[1:]), axis=1)

        def measure(drives, timing=False):
            data = np.r_[anchor, np.concatenate((drives, cv[..., None]), axis=2).ravel()].astype("<f8").tobytes()
            raw = self.run("audio-readout", data)
            replay = self.run("audio-readout", data)
            assert (raw.returncode, raw.stdout, raw.stderr) == (replay.returncode, replay.stdout, replay.stderr)
            result = dict(passed=False, steps=len(reference), unchanged_replay=True,
                          input_sha256=c.digest(data), output_sha256=c.digest(raw.stdout))
            if raw.returncode:
                return dict(result, error=raw.stderr.decode(errors="replace").strip(), failure_input=packed(data))
            values = np.frombuffer(raw.stdout, "<f8")
            rows = values[3:].reshape(-1, 7)
            assert rows.shape == wanted.shape and np.isfinite(values).all()
            error = rows - wanted
            max_error = abs(error).max(axis=0)
            rms = float(np.linalg.norm(error[:, 0]) / np.linalg.norm(wanted[:, 0]))
            peak = float(max_error[0] / abs(wanted[:, 0]).max())
            mean = float(abs(np.mean(error[:, 0])))
            result.update(passed=bool(rms <= .001 and peak <= .003 and mean <= 1e-6
                                      and max_error[1:3].max() <= 2e-9 and max_error[3:].max() <= 20e-6),
                          max_error=max_error.tolist(), j7_rms_relative=rms, j7_peak_relative=peak,
                          j7_mean_v=mean, max_load_iterations=int(values[0]),
                          max_load_mismatch_v=float(values[1]), checked_nodal_proposals=int(values[2]))
            if not result["passed"]:
                result["failure_input"] = packed(data)
            if timing:
                measured = self.run("audio-readout-bench", data)
                assert measured.returncode == 0, measured.stderr.decode(errors="replace")
                times = list(map(int, measured.stdout.decode().strip().split(",")))
                result["timing"] = dict(zip(("windows", "median_ns", "p99_ns", "max_ns"), times, strict=True))
            return result

        results = dict(oracle_stages=measure(self.stages[indices[:, :, None], DRIVES]),
                       oracle_foh=measure(foh(oracle)), generated_foh=measure(foh(generated), timing=True))
        return dict(passed=all(row["passed"] for row in results.values()),
                    first_slot=first, reference_peak_j7_v=float(abs(wanted[:, 0]).max()), **results)
