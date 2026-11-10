"""Resume either fast receiver branch from a charged nonlinear circuit snapshot."""
import argparse
import os
from pathlib import Path
import subprocess
import traceback

import numpy as np

from affine_evidence import Sources
from check_hybrid_voice import packed as pack_failure
from check_rf_d_pilot_returns import (
    AREA, COMPILER, LIB, ORACLE, PROBE, ROOT, SOURCES, compare, emit, generate, generate_law,
)
from check_rf_d_pilot_split_returns import (
    ANCHOR_SOURCE, BUDGET_NS, CLOSED, HOST_FRAMES, LOAD_LIMIT_V, OPEN, OPEN_RANGE, drives, packed,
)
from check_rf_d_pilot_off_anchor import OWN as OFF_OWN, RANGE as CLOSED_RANGE, stimulus as off_drives
from check_rf_d_reduced_contour_ports import SOURCES as CONTOUR_SOURCES, chain_index, references
from check_recovery_cost import digest
from prepare_charge_reduced import Y
from prepare_dual_chain import sha, write
from prepare_rf_d_pilot_returns import SPLIT_LAWS, emit_data
from recovery_port_input_model import cases

OWN = "tools/check_rf_d_pilot_receiver_handoff.py"
RATE = 96_000
STEPS = 2 * HOST_FRAMES
CHARGES = 17
CHARGE_LIMIT_C = 1e-20


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--branch", choices=("positive", "negative"), default="positive")
    args = parser.parse_args()
    negative = args.branch == "negative"
    center, limits = (CLOSED, CLOSED_RANGE) if negative else (OPEN, OPEN_RANGE)
    stimulus = off_drives if negative else drives
    assert AREA.is_dir() and not list(AREA.iterdir())
    seq = 1
    while (out := ROOT / f"evidence/rf_d_pilot_receiver_handoff{seq:02}.json").exists():
        seq += 1
    extra_sources = (*CONTOUR_SOURCES, OFF_OWN, "tools/check_vco_family_voice_bus_cost.py") if negative else ()
    sources = Sources((*SOURCES, OWN, ANCHOR_SOURCE, "tools/check_rf_d_pilot_split_returns.py",
                       "tools/affine_evidence.py", "tools/check_hybrid_voice.py", *extra_sources))
    report = dict(passed=False, native_receiver_realtime=False, rack_integrated=False,
                  contour_feedback=False, internal_rate_hz=RATE, frames=HOST_FRAMES,
                  warmup_frames=HOST_FRAMES, budget_ns=BUDGET_NS,
                  charge_limit_c=CHARGE_LIMIT_C, load_limit_v=LOAD_LIMIT_V,
                  branch=args.branch, bias_v=center, drive_range_v=limits,
                  normalized_defects=negative,
                  imposed_sources=("signal", "R59 voltage", "R60 voltage"),
                  **sources.fields(), compiler_sha256=sha(Path(COMPILER)), library_sha256=sha(LIB))
    env = dict(os.environ, PATH="C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;" + os.environ["PATH"])
    flags = [COMPILER, "--edition=2021", "-C", "opt-level=3", "-C", "target-feature=+fma",
             "-A", "dead_code", "-C", "link-arg=-Wl,--stack,33554432"]
    last = None

    def run(command, payload=None, repeat=False):
        nonlocal last
        args = list(map(str, command))
        result = subprocess.run(args, cwd=ROOT, env=env, input=payload, capture_output=True, timeout=180)
        last = args, payload, result
        if repeat:
            again = subprocess.run(args, cwd=ROOT, env=env, input=payload, capture_output=True, timeout=180)
            assert (result.returncode, result.stdout, result.stderr) == (again.returncode, again.stdout, again.stderr)
        return result

    def floats(command, payload, repeat=False):
        result = run(command, payload, repeat)
        assert result.returncode == 0, result.stderr.decode(errors="replace")
        values = np.frombuffer(result.stdout, "<f8")
        assert np.isfinite(values).all()
        return values

    try:
        oracle = AREA / "receiver-handoff-oracle.exe"
        floats([*flags, ROOT / ORACLE, "--extern", f"rf_d_circuit={LIB}", "-o", oracle], None)
        baseline = cases()[1]
        seed = baseline["DC"]
        if negative:
            reference, report["reference_inputs"] = references()
            _, _, _, full_seed = reference["negative"][1][0]
            seed = full_seed[:, [chain_index(k) for k in range(68)]].ravel()
            report["negative_seed_sha256"] = digest(packed(seed))
        dc = floats([oracle, "anchor-direct" if negative else "anchor"], packed(np.r_[seed, 0., center]))
        assert 0. <= dc[-1] <= 1e-13
        case = dict(baseline, DC=dc[:136], G=dc[136:-1].reshape(68, 68).copy())
        case["G"][66, 66] -= Y
        report.update(anchor_sha256=digest(packed(case["DC"])), anchor_residual_a=float(dc[-1]))

        code, _ = generate(rate=RATE)
        generate_law(SPLIT_LAWS)
        bank = AREA / "pilot-return-maps.rs"
        checks = emit_data(bank, 1. / RATE, split=case, center=center, limits=limits,
                           split_ladder=True, normalize_defects=negative, state_transfer=True)
        report["maps"] = dict(checks=checks, sha256=sha(bank))
        src = emit("receiver-handoff.rs", code + f'#[path = "{(ROOT / PROBE).as_posix()}"] mod probe;\n'
                   "fn main() -> Result<(), Box<dyn std::error::Error>> { probe::main() }\n")
        exe = AREA / "receiver-handoff.exe"
        floats([*flags, "--cfg", "pilot_returns", "--cfg", "pilot_split_returns",
                "--cfg", "pilot_receiver_handoff", "--cfg", "pilot_block_roots", src, "-o", exe], None)

        fine, prefixes = {}, {}
        for factor in (4, 8):
            clock = RATE * factor
            ticks = np.arange(2 * STEPS * factor)
            stages = np.column_stack((stimulus((ticks + 1. / 3.) / clock) + [0., *center],
                                      stimulus((ticks + 1.) / clock) + [0., *center]))
            payload = packed(np.r_[case["DC"], stages.ravel()])
            values = floats([oracle, clock, "split"], payload)
            fine[factor] = values.reshape(-1, 6)[factor - 1::factor]
            prefixes[factor] = packed(np.r_[case["DC"], stages[:STEPS * factor].ravel()])
            report[f"reference_{clock}_sha256"] = digest(packed(values))
        snapshot = floats([oracle, RATE * 8, "split-snapshot"], prefixes[8], repeat=True)
        assert snapshot.shape == (136,)
        node = snapshot[:68] + snapshot[68:]
        initial_drive = stimulus(np.array([STEPS / RATE]))[0]
        actual_drive = initial_drive[1:] + center
        observed = np.array([node[61], node[66], node[6] - node[66],
                             (node[66] - .5 * initial_drive[0]) / 39_250.,
                             (actual_drive[0] - node[32]) / 68_000.,
                             (node[5] - actual_drive[1]) / 680.])
        np.testing.assert_array_equal(observed, fine[8][STEPS - 1])
        report.update(snapshot_sha256=digest(packed(snapshot)), snapshot_observations_bit_exact=True)

        coarse = stimulus(np.arange(1, 2 * STEPS + 1) / RATE)
        suffix = packed(coarse[STEPS:])
        header = np.r_[snapshot, initial_drive]
        payload = packed(header) + suffix
        resumed = floats([exe, "electrical-resume"], payload, repeat=True)
        charge, rows = resumed[:CHARGES], resumed[CHARGES:].reshape(STEPS, 8)
        keep = np.r_[0:62, 66:68]
        retained = np.flatnonzero(np.any(case["a"][:, keep] != 0., axis=1))
        assert len(retained) == CHARGES
        offset = (snapshot[:68] - case["DC"][:68]) + (snapshot[68:] - case["DC"][68:])
        wanted_charge = (case["a"][retained] @ offset) * case["c"][retained]
        charge_error = abs(charge - wanted_charge)
        report["charge"] = dict(passed=bool(charge_error.max() <= CHARGE_LIMIT_C),
                                 retained_rows=retained.tolist(), maximum_c=charge_error.tolist(),
                                 initial_offset_c=wanted_charge.tolist())
        report["refinement"] = compare(fine[4][STEPS:], fine[8][STEPS:])
        report["comparison"] = compare(rows[:, :6], fine[8][STEPS:])
        endpoint = coarse[STEPS:, 1:] + center
        wanted_load = np.column_stack((endpoint[:, 0] - 68_000. * fine[8][STEPS:, 4],
                                       endpoint[:, 1] + 680. * fine[8][STEPS:, 5]))
        load_error = abs(rows[:, 6:] - wanted_load).max(axis=0)
        closure = np.column_stack(((endpoint[:, 0] - rows[:, 6]) / 68_000.,
                                   (rows[:, 7] - endpoint[:, 1]) / 680.))
        closure_error = abs(closure - rows[:, 4:6]).max(axis=0)
        report["loads"] = dict(passed=bool(load_error.max() <= LOAD_LIMIT_V and closure_error.max() <= 2e-12),
                                maximum_v=load_error.tolist(), closure_error_a=closure_error.tolist())
        report.update(input_sha256=digest(payload), output_sha256=digest(packed(resumed)), unchanged_replay=True)

        continuous = floats([exe, "electrical-ports"], packed(coarse)).reshape(-1, 8)
        report["resume_vs_uninterrupted"] = compare(rows[:, :6], continuous[STEPS:, :6])
        zero_header = np.r_[case["DC"], 0., 0., 0.]
        zero = floats([exe, "electrical-resume"], packed(zero_header) + packed(coarse))
        assert np.all(zero[:CHARGES] == 0.)
        assert np.array_equal(zero[CHARGES:].reshape(-1, 8), continuous)
        report["dc_import_bit_exact"] = True
        reset = floats([exe, "electrical-ports"], suffix).reshape(-1, 8)
        report["reset_control"] = compare(reset[:, :6], fine[8][STEPS:])
        assert not report["reset_control"]["passed"], "The fixture must detect a lost history"

        report["guards"] = {}
        for name, index, value, error in (("nonfinite_node", 0, np.nan, "Input"),
                                         ("nonfinite_signal", 136, np.nan, "Input"),
                                         ("drive_domain", 137, limits[0] + .001, "Input"),
                                         ("junction_domain", 6, header[6] + 2., "Domain")):
            bad = header.copy()
            bad[index] = value
            rejected = run([exe, "electrical-resume"], packed(bad), repeat=True)
            assert rejected.returncode and not rejected.stdout and error in rejected.stderr.decode()
            report["guards"][name] = dict(exit_code=rejected.returncode,
                                          error=rejected.stderr.decode().strip(), unchanged_replay=True,
                                          input=pack_failure(packed(bad)))
        timing = run([exe, "electrical-resume-bench", RATE], payload)
        assert timing.returncode == 0, timing.stderr.decode(errors="replace")
        report["timing"] = dict(zip(("blocks", "median_ns", "p99_ns", "max_ns", "allocations"),
                                    map(int, timing.stdout.decode().strip().split(",")), strict=True))
        report["timed_scope"] = "128-frame receiver continuation from imported state, excluding state import"
        report["passed"] = all(report[key]["passed"] for key in
                               ("charge", "refinement", "comparison", "loads", "resume_vs_uninterrupted"))
        report["native_receiver_realtime"] = (report["passed"] and report["timing"]["allocations"] == 0
                                               and report["timing"]["max_ns"] <= BUDGET_NS)
        if not report["passed"]:
            report["failure_input"] = pack_failure(payload)
        print("HANDOFF", report["passed"], report["comparison"], report["loads"], report["timing"], flush=True)
        sources.unchanged()
    except Exception:
        report["failure"] = traceback.format_exc()
        if last is not None:
            command, payload, result = last
            report["last_command"] = command
            report["last_stderr"] = result.stderr.decode(errors="replace")
            if payload is not None:
                assert len(payload) <= 256 * 1024
                report["failure_input"] = pack_failure(payload)
                replay = run(command, payload)
                report["failure_unchanged_replay"] = ((result.returncode, result.stdout, result.stderr)
                                                       == (replay.returncode, replay.stdout, replay.stderr))
        raise
    finally:
        write(out, report)
        for path in AREA.iterdir():
            assert path.is_file() and path.resolve().parent == AREA.resolve()
            path.unlink()
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
