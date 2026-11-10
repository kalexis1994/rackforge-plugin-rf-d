"""Generate and check the split receiver's quiet DC branch."""
import os
import subprocess
import traceback
from pathlib import Path

import numpy as np

from affine_evidence import Sources
from check_rf_d_pilot_returns import (
    AREA, COMPILER, LIB, ORACLE, PROBE, ROOT, SOURCES, compare, emit, generate, generate_law,
)
from check_rf_d_pilot_split_returns import ANCHOR_SOURCE, CLOSED, packed
from check_rf_d_reduced_contour_ports import chain_index, references
from check_recovery_cost import digest
from prepare_charge_reduced import Y
from prepare_dual_chain import sha, write
from prepare_rf_d_pilot_returns import SPLIT_LAWS, emit_data
from recovery_port_input_model import cases

OWN = "tools/check_rf_d_pilot_off_anchor.py"
RANGE = (.005, .001)
RATE = 96_000
SAMPLES = 256


def stimulus(t):
    w = 2. * np.pi * t
    return np.column_stack((.055 * np.sin(211 * w) + .015 * np.sin(817 * w),
                            RANGE[0] * .98 * np.sin(331 * w), RANGE[1] * .98 * np.sin(407 * w)))


def main():
    assert not list(AREA.iterdir())
    sequence = 1
    while (out := ROOT / f"evidence/rf_d_pilot_off_anchor{sequence:02}.json").exists():
        sequence += 1
    sources = Sources((*SOURCES, OWN, ANCHOR_SOURCE, "tools/check_rf_d_pilot_split_returns.py",
                       "tools/check_rf_d_reduced_contour_ports.py", "tools/check_vco_family_voice_bus_cost.py"))
    report = dict(passed=False, rack_integrated=False, dc_passed=False, rate_hz=RATE,
                  source_v=CLOSED, voltage_range_v=RANGE, **sources.fields(),
                  compiler_sha256=sha(Path(COMPILER)), library_sha256=sha(LIB))
    env = dict(os.environ, PATH="C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;" + os.environ["PATH"])
    flags = [COMPILER, "--edition=2021", "-C", "opt-level=3", "-C", "target-feature=+fma",
             "-A", "dead_code", "-C", "link-arg=-Wl,--stack,33554432"]

    def run(args, data=None, repeat=False):
        command = list(map(str, args))
        payload = None if data is None else packed(data)
        def call():
            return subprocess.run(command, cwd=ROOT, env=env, input=payload, capture_output=True, timeout=180)
        result = call()
        if repeat:
            replay = call()
            assert (result.returncode, result.stdout, result.stderr) == (
                replay.returncode, replay.stdout, replay.stderr)
        return result

    def require(result):
        assert result.returncode == 0, result.stderr.decode(errors="replace")
        return np.frombuffer(result.stdout, "<f8")

    try:
        oracle = AREA / "split-off-oracle.exe"
        require(run([*flags, ROOT / ORACLE, "--extern", f"rf_d_circuit={LIB}", "-o", oracle]))
        baseline = cases()[1]
        target = [0., *CLOSED]
        legacy = run([oracle, "anchor"], np.r_[baseline["DC"], target], repeat=True)
        report["positive_seed_continuation"] = dict(exit_code=legacy.returncode,
                                                    error=legacy.stderr.decode().strip(), unchanged_replay=True)
        ref, report["reference_inputs"] = references()
        _, _, _, full_seed = ref["negative"][1][0]
        seed = full_seed[:, [chain_index(k) for k in range(68)]].ravel()
        report["negative_seed_sha256"] = digest(packed(seed))
        dc = require(run([oracle, "anchor-direct"], np.r_[seed, target], repeat=True))
        assert np.isfinite(dc).all() and 0. <= dc[-1] <= 1e-13
        report.update(dc_passed=True, dc_residual=float(dc[-1]), dc_sha256=digest(packed(dc[:136])))
        print("OFF_DC", report["dc_residual"], report["dc_sha256"], flush=True)

        case = dict(baseline, DC=dc[:136], G=dc[136:-1].reshape(68, 68).copy())
        case["G"][66, 66] -= Y
        bank = AREA / "split-off-map.rs"
        options = dict(split=case, center=CLOSED, limits=RANGE, split_ladder=True)
        failures = []
        for _ in range(2):
            try:
                emit_data(bank, 1. / RATE, **options)
            except AssertionError as error:
                failures.append(list(error.args[0]))
        assert len(failures) == 2 and failures[0] == failures[1]
        report["unit_current_projection_rejection"] = failures[0]
        checks = emit_data(bank, 1. / RATE, normalize_defects=True, **options)
        report["maps"] = dict(checks=checks, sha256=sha(bank), bias_normalized_defects=True)
        print("OFF_MAP", checks, flush=True)
        code, _ = generate(rate=RATE)
        code = code.replace((AREA / "pilot-return-maps.rs").as_posix(), bank.as_posix())
        generate_law(SPLIT_LAWS)
        probe = emit("split-off-probe.rs", code + f'#[path = "{(ROOT / PROBE).as_posix()}"] mod probe;\n'
                     "fn main() -> Result<(), Box<dyn std::error::Error>> { probe::main() }\n")
        exe = AREA / "split-off-probe.exe"
        require(run([*flags, "--cfg", "pilot_returns", "--cfg", "pilot_pi",
                     "--cfg", "pilot_split_returns", probe, "-o", exe]))
        drives = stimulus(np.arange(1, SAMPLES + 1) / RATE)
        candidate = require(run([exe, "electrical"], drives, repeat=True)).reshape(-1, 6)
        assert np.isfinite(candidate).all()
        fine = {}
        for factor in (4, 8):
            clock = RATE * factor
            tick = np.arange(SAMPLES * factor)
            stages = np.column_stack((stimulus((tick + 1. / 3.) / clock) + target,
                                      stimulus((tick + 1.) / clock) + target))
            fine[factor] = require(run([oracle, clock, "split"], np.r_[case["DC"], stages.ravel()]))
            fine[factor] = fine[factor].reshape(-1, 6)[factor - 1::factor]
            assert np.isfinite(fine[factor]).all()
        report["reference_max_j7_v"] = float(np.max(abs(fine[8][:, 0])))
        report["refinement"] = compare(fine[4], fine[8])
        report["comparison"] = compare(candidate, fine[8])
        report["passed"] = report["refinement"]["passed"] and report["comparison"]["passed"]
        print("OFF_TRANSIENT", report["reference_max_j7_v"], report["refinement"], report["comparison"], flush=True)
        sources.unchanged()
    except Exception:
        report["failure"] = traceback.format_exc()
        raise
    finally:
        write(out, report)
        for path in AREA.iterdir():
            assert path.is_file() and path.resolve().parent == AREA.resolve()
            path.unlink()
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
