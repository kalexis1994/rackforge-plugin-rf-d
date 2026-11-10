"""Close R59 against the fast receiver and contrast the joined nodal circuit."""
import argparse
import os
from pathlib import Path
import subprocess
import traceback

import numpy as np

from affine_evidence import Sources
from check_hybrid_voice import packed as pack_bytes
from check_rf_d_pilot_returns import (
    AREA, COMPILER, LIB, ORACLE, ROOT, SOURCES, compare, emit, generate, generate_law,
)
from check_rf_d_pilot_split_returns import OPEN, OPEN_RANGE, CLOSED, BUDGET_NS, packed, drives
from check_rf_d_pilot_off_anchor import RANGE as CLOSED_RANGE, stimulus as off_drives
from check_rf_d_reduced_contour_ports import SOURCES as CONTOUR_SOURCES, chain_index, references
from check_recovery_cost import digest
from prepare_charge_reduced import Y
from prepare_dual_chain import sha, write
from prepare_rf_d_pilot_returns import SPLIT_LAWS, emit_data
from recovery_port_input_model import cases

OWN = "tools/check_rf_d_pilot_fast_r59.py"
MODEL = "tools/rf_d_pilot_fast_r59.rs"
PROBE = "tools/rf_d_pilot_fast_r59_probe.rs"
JOINED = "tools/rf_d_pilot_r59_oracle.rs"
RATE = 96_000
STEPS = 256
CATHODE_V = 0.


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--branch", choices=("positive", "negative"), default="positive")
    args = parser.parse_args()
    negative = args.branch == "negative"
    center, limits = (CLOSED, CLOSED_RANGE) if negative else (OPEN, OPEN_RANGE)
    stimulus = off_drives if negative else drives
    assert AREA.is_dir() and not list(AREA.iterdir())
    seq = 1
    while (out := ROOT / f"evidence/rf_d_pilot_fast_r59{seq:02}.json").exists():
        seq += 1
    modules = dict(fast_r59=MODEL, probe=PROBE, contour_ports="tools/rf_d_pilot_contour_ports.rs",
                   latch_charge="tools/latch_charge_driver.rs", port_lu="tools/rf_d_reduced_engine_lu.rs")
    sources = Sources((*SOURCES, *CONTOUR_SOURCES, OWN, JOINED, *modules.values(),
                       "tools/check_rf_d_pilot_split_returns.py", "tools/check_rf_d_pilot_off_anchor.py",
                       "tools/affine_evidence.py", "tools/check_hybrid_voice.py",
                       "crates/rf-d-circuit/src/loudness_follower.rs"))
    report = dict(passed=False, realtime=False, rack_integrated=False, r59_closed=True, branch=args.branch,
                  internal_rate_hz=RATE, frames=128, warmup_frames=128, budget_ns=BUDGET_NS,
                  imposed_sources=("signal", "C2", "reset base", "R60 collector"),
                  cathode_v=CATHODE_V, receiver_center_v=center, receiver_range_v=limits,
                  **sources.fields(), compiler_sha256=sha(Path(COMPILER)), library_sha256=sha(LIB))
    env = dict(os.environ, PATH="C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;" + os.environ["PATH"])
    flags = [COMPILER, "--edition=2021", "-C", "opt-level=3", "-C", "target-feature=+fma",
             "-A", "dead_code", "-C", "link-arg=-Wl,--stack,33554432"]
    last = None

    def run(command, payload=None, repeat=False):
        nonlocal last
        args = list(map(str, command))
        result = subprocess.run(args, cwd=ROOT, env=env, input=payload, capture_output=True, timeout=240)
        last = args, payload, result
        if repeat:
            again = subprocess.run(args, cwd=ROOT, env=env, input=payload, capture_output=True, timeout=240)
            assert (result.returncode, result.stdout, result.stderr) == (again.returncode, again.stdout, again.stderr)
        assert result.returncode == 0, result.stderr.decode(errors="replace")
        return result.stdout

    def values(command, payload=None, repeat=False):
        raw = run(command, payload, repeat)
        got = np.frombuffer(raw, "<f8")
        assert np.isfinite(got).all()
        return got

    def assess(candidate, reference):
        voltage = abs(candidate[:, 6:] - reference[:, 6:]).max(axis=0)
        audio = compare(candidate[:, :6], reference[:, :6])
        return dict(passed=bool(audio["passed"] and voltage.max() <= 20e-6),
                    audio=audio, maximum_voltage_v=voltage.tolist())

    try:
        isolated, joined = AREA / "r59-isolated.exe", AREA / "r59-joined.exe"
        run([*flags, ROOT / ORACLE, "--extern", f"rf_d_circuit={LIB}", "-o", isolated])
        run([*flags, ROOT / JOINED, "--extern", f"rf_d_circuit={LIB}", "-o", joined])
        baseline = cases()[1]
        seed = baseline["DC"]
        if negative:
            reference, report["reference_inputs"] = references()
            seed = reference["negative"][1][0][3][:, [chain_index(k) for k in range(68)]].ravel()
        dc = values([isolated, "anchor-direct" if negative else "anchor"], packed(np.r_[seed, 0., center]))
        assert 0. <= dc[-1] <= 1e-13
        case = dict(baseline, DC=dc[:136], G=dc[136:-1].reshape(68, 68).copy())
        case["G"][66, 66] -= Y
        bias = values([joined, "bias"], packed([dc[32] + dc[100], center[0], CATHODE_V]), repeat=True)
        assert bias.shape == (6,) and abs(bias[3] - center[0]) <= 1e-12
        report.update(anchor_sha256=digest(packed(dc[:136])), follower_bias_v=bias[:5].tolist(), c2_bias_v=float(bias[5]))
        code, _ = generate(rate=RATE)
        generate_law(SPLIT_LAWS)
        bank = AREA / "pilot-return-maps.rs"
        report["map_checks"] = emit_data(bank, 1. / RATE, split=case, center=center, limits=limits,
                                          split_ladder=True, normalize_defects=negative, state_transfer=True)
        report["map_sha256"] = sha(bank)
        code += 'pub use rf_d_circuit::StepError;\n'
        for name, path in modules.items():
            code += f'#[path = "{(ROOT / path).as_posix()}"] mod {name};\n'
        code += 'use port_lu as reduced_lu;\nfn main() -> Result<(), Box<dyn std::error::Error>> { probe::main() }\n'
        source = emit("r59-fast.rs", code)
        exe = AREA / "r59-fast.exe"
        cfg = ["--cfg", "pilot_returns", "--cfg", "pilot_split_returns", "--cfg", "pilot_block_roots",
               "--cfg", "pilot_receiver_handoff", "--cfg", "pilot_receiver_ports", "--cfg", "pilot_audio_readout",
               "--cfg", "pilot_closed_cv"]
        run([*flags, *cfg, source, "--extern", f"rf_d_circuit={LIB}", "-o", exe])
        header = np.r_[dc[:136], bias[:5]]

        def controls(time):
            original = stimulus(time)
            return np.column_stack((original[:, 0], bias[5] + original[:, 1],
                                    np.full(len(time), CATHODE_V), center[1] + original[:, 2]))

        fine = {}
        for factor in (4, 8):
            tick = np.arange(2 * STEPS * factor)
            stages = np.column_stack((controls((tick + 1. / 3.) / (RATE * factor)),
                                      controls((tick + 1.) / (RATE * factor))))
            raw = run([joined, RATE * factor], packed(np.r_[header, stages.ravel()]))
            fine[factor] = np.frombuffer(raw, "<f8").reshape(-1, 13)[factor - 1::factor]
            report[f"reference_{RATE * factor}_sha256"] = digest(raw)
            print("Reference", RATE * factor, flush=True)
        report["refinement"] = assess(fine[4], fine[8])
        report["reference_r59_source_range_v"] = [float(fine[8][:, 11].min()), float(fine[8][:, 11].max())]
        report["reference_source_domain_passed"] = bool(abs(fine[8][:, 11] - center[0]).max() <= limits[0])
        input = controls(np.arange(1, 2 * STEPS + 1) / RATE)
        payload = packed(np.r_[header, input.ravel()])
        report.update(input_sha256=digest(payload), input=pack_bytes(payload), cases={})
        outputs = {}
        for mode in ("cached", "fresh"):
            raw = run([exe, mode], payload, repeat=True)
            got = np.frombuffer(raw, "<f8")
            assert np.isfinite(got).all()
            stats, rows = got[:4], got[4:].reshape(2 * STEPS, 13)
            result = assess(rows, fine[8])
            item = dict(comparison=result, max_iterations=int(stats[0]), max_closure_v=float(stats[1]),
                        max_r59_mismatch_a=float(stats[2]), tangent_calls=int(stats[3]),
                        output_sha256=digest(raw), unchanged_replay=True)
            item["r59_source_range_v"] = [float(rows[:, 11].min()), float(rows[:, 11].max())]
            item["passed"] = bool(result["passed"] and stats[1] <= 1e-10 and stats[2] <= 2e-12)
            timing = run([exe, mode, "bench"], payload).decode().strip().split(",")
            item["timing"] = dict(zip(("blocks", "median_ns", "p99_ns", "max_ns", "allocations"), map(int, timing), strict=True))
            item["realtime"] = item["passed"] and item["timing"]["max_ns"] <= BUDGET_NS and item["timing"]["allocations"] == 0
            report["cases"][mode] = item
            outputs[mode] = rows
            print(mode, item, flush=True)
        partition = run([exe, "cached", 64], payload, repeat=True)
        report["partition_bit_exact"] = digest(partition) == report["cases"]["cached"]["output_sha256"]
        report["cached_vs_fresh"] = assess(outputs["cached"], outputs["fresh"])
        report["passed"] = bool(report["refinement"]["passed"] and report["reference_source_domain_passed"] and report["partition_bit_exact"]
                                 and report["cached_vs_fresh"]["passed"] and all(v["passed"] for v in report["cases"].values()))
        report["realtime"] = report["passed"] and report["cases"]["cached"]["realtime"]
        sources.unchanged()
    except Exception:
        report["failure"] = traceback.format_exc()
        if last is not None:
            command, payload, result = last
            report.update(last_command=command, last_stderr=result.stderr.decode(errors="replace"))
            if payload is not None:
                assert len(payload) <= 512 * 1024
                report["failure_input"] = pack_bytes(payload)
                again = subprocess.run(command, cwd=ROOT, env=env, input=payload, capture_output=True, timeout=240)
                report["failure_unchanged_replay"] = ((result.returncode, result.stdout, result.stderr)
                                                       == (again.returncode, again.stdout, again.stderr))
        raise
    finally:
        write(out, report)
        for path in AREA.iterdir():
            assert path.is_file() and path.resolve().parent == AREA.resolve()
            path.unlink()
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
