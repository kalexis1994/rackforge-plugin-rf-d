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
CHARGES = 17
CHARGE_LIMIT_C = 1e-20
CATHODE_V = 0.
CR6_SCALE_V = 1.5 * 1.380649e-23 * 298.15 / 1.602176634e-19
CR6_SATURATION_A = 1e-8
RETURN_LIMIT_A = 2e-9
PROFILE_STAGES = ("initial_follower", "receiver_history", "receiver_root", "loaded_follower",
                  "follower_response", "receiver_tangent", "receiver_reconstruction")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--branch", choices=("positive", "negative"), default="positive")
    parser.add_argument("--shared-port-exp", action="store_true")
    parser.add_argument("--packed-products", action=argparse.BooleanOptionalAction, default=True,
                        help="use the four-row layout and verify it against the scalar control")
    parser.add_argument("--compare-eager", action="store_true",
                        help="compare with full receiver reconstruction at every closure attempt")
    parser.add_argument("--packed-odd", action="store_true",
                        help="group the odd Newton rows and compare with the original correction")
    parser.add_argument("--profile", action="store_true",
                        help="attribute native cost using a separate instrumented executable")
    parser.add_argument("--schur-follower", action="store_true",
                        help="eliminate the reset node from the follower Newton system")
    parser.add_argument("--predict-follower", action="store_true",
                        help="seed the follower from the preceding accepted load and C2 tangents")
    parser.add_argument("--predict-cathode", action="store_true",
                        help="include the CR6 cathode tangent in the follower prediction")
    cathode_options = parser.add_mutually_exclusive_group()
    cathode_options.add_argument("--vary-cathode", action="store_true",
                                 help="drive the reset cathode around a forward-biased CR6 operating point")
    cathode_options.add_argument("--cross-cathode", action="store_true",
                                 help="drive CR6 across zero bias in both directions")
    parser.add_argument("--tight-follower", action="store_true",
                        help="require a 2e-14 V follower Newton correction in every variant")
    seed_options = parser.add_mutually_exclusive_group()
    seed_options.add_argument("--feedback-seed", action="store_true",
                              help="seed receiver retries with the new predictor and previous trial feedback")
    seed_options.add_argument("--reuse-law", action="store_true",
                              help="reuse the previous trial's law evaluation at the same junctions")
    args = parser.parse_args()
    if args.packed_odd and not args.packed_products:
        parser.error("--packed-odd requires --packed-products")
    if args.predict_cathode and not args.predict_follower:
        parser.error("--predict-cathode requires --predict-follower")
    negative = args.branch == "negative"
    center, limits = (CLOSED, CLOSED_RANGE) if negative else (OPEN, OPEN_RANGE)
    stimulus = off_drives if negative else drives
    moving_cathode = args.vary_cathode or args.cross_cathode
    cathode_v, cathode_amplitude_v = CATHODE_V, 0.
    if moving_cathode:
        r24, r27 = 6800., 16900.
        unloaded_reset = (center[0] / r24 - 10. / r27) / (1. / r24 + 1. / r27)
        cathode_v = unloaded_reset - 0.45 if args.vary_cathode else unloaded_reset
        cathode_amplitude_v = 0.25 * limits[0] if args.vary_cathode else 0.15
    assert AREA.is_dir() and not list(AREA.iterdir())
    seq = 1
    while (out := ROOT / f"evidence/rf_d_pilot_fast_r59{seq:02}.json").exists():
        seq += 1
    modules = dict(fast_r59=MODEL, probe=PROBE, contour_ports="tools/rf_d_pilot_contour_ports.rs",
                   latch_charge="tools/latch_charge_driver.rs", port_lu="tools/rf_d_reduced_engine_lu.rs")
    sources = Sources((*SOURCES, *CONTOUR_SOURCES, OWN, JOINED, *modules.values(),
                       "tools/check_rf_d_pilot_split_returns.py", "tools/check_rf_d_pilot_off_anchor.py",
                       "tools/affine_evidence.py", "tools/check_hybrid_voice.py",
                       "tools/rf_d_pilot_packed_products.rs",
                       "crates/rf-d-circuit/src/loudness_follower.rs"))
    report = dict(passed=False, realtime=False, rack_integrated=False, r59_closed=True, branch=args.branch,
                  internal_rate_hz=RATE, frames=128, warmup_frames=128, budget_ns=BUDGET_NS,
                  imposed_sources=("signal", "C2", "reset base", "R60 collector"),
                  cathode_v=cathode_v, cathode_amplitude_v=cathode_amplitude_v,
                  receiver_center_v=center, receiver_range_v=limits,
                  shared_port_exp=args.shared_port_exp,
                  packed_products=args.packed_products,
                  packed_odd=args.packed_odd,
                  feedback_seed=args.feedback_seed,
                  reuse_law=args.reuse_law,
                  schur_follower=args.schur_follower,
                  predict_follower=args.predict_follower,
                  predict_cathode=args.predict_cathode,
                  cross_cathode=args.cross_cathode,
                  follower_correction_limit_v=2e-14 if args.tight_follower else 2e-12,
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

    def cr6_voltage(rows, cathode):
        return rows[:, 12] - cathode

    def cr6_current(voltage):
        return CR6_SATURATION_A * np.expm1(voltage / CR6_SCALE_V)

    def cr6_crossings(voltage):
        nonzero = np.flatnonzero(voltage)
        sign = voltage[nonzero] > 0.
        return nonzero[1:][sign[1:] != sign[:-1]].tolist()

    def timing(line):
        return dict(zip(("blocks", "median_ns", "p99_ns", "max_ns", "allocations"),
                        map(int, line.split(",")), strict=True))

    def time_blocks(target, mode, payload):
        return timing(run([target, mode, "bench"], payload).decode().strip())

    def profile_blocks(target, payload, expected):
        raw = run([target, "cached", 128, "--charges"], payload, repeat=True)
        charge_bytes = CHARGES * 8
        exact = (digest(raw[:-charge_bytes]) == expected["output_sha256"]
                 and digest(raw[-charge_bytes:]) == expected["final_charge_sha256"])
        lines = run([target, "cached", "bench"], payload).decode().splitlines()
        instrumented = timing(lines[0])
        blocks = instrumented["blocks"]
        stages = {}
        for name, line in zip(PROFILE_STAGES, lines[1:-1], strict=True):
            calls, elapsed_ns = map(int, line.split(","))
            stages[name] = dict(calls=calls, elapsed_ns=elapsed_ns, mean_per_block_ns=elapsed_ns / blocks)
        evaluations, reused, fallbacks, prediction_fallbacks = map(int, lines[-1].split(","))
        assert 0 <= reused <= min(stages["receiver_root"]["calls"], evaluations)
        return dict(bit_exact=exact, instrumented_timing=instrumented, stages=stages,
                    successful_root_evaluations=evaluations, reused_root_evaluations=reused,
                    follower_fallbacks=fallbacks, prediction_fallbacks=prediction_fallbacks)

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
        bias = values([joined, "bias"], packed([dc[32] + dc[100], center[0], cathode_v]), repeat=True)
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
        seed_cfg = []
        if args.feedback_seed:
            seed_cfg = ["--cfg", "pilot_r59_feedback_seed"]
        elif args.reuse_law:
            seed_cfg = ["--cfg", "pilot_r59_reuse_law"]
        if args.shared_port_exp:
            cfg.extend(("--cfg", "pilot_shared_port_exp"))
        if args.tight_follower:
            cfg.extend(("--cfg", "pilot_r59_tight_follower"))
        control_cfg = cfg.copy()
        if args.packed_products:
            cfg.extend(("--cfg", "pilot_receiver_packed"))
        odd_control_cfg = cfg.copy()
        if args.packed_odd:
            cfg.extend(("--cfg", "pilot_receiver_packed_odd"))
        follower_cfg = ["--cfg", "pilot_r59_schur_follower"] if args.schur_follower else []
        prediction_cfg = ["--cfg", "pilot_r59_predict_follower"] if args.predict_follower else []
        prediction_control_cfg = prediction_cfg.copy() if args.predict_cathode else []
        if args.predict_cathode:
            prediction_cfg.extend(("--cfg", "pilot_r59_predict_cathode"))
        candidate_cfg = [*seed_cfg, *follower_cfg, *prediction_cfg]

        def build(target, *config):
            run([*flags, *config, source, "--extern", f"rf_d_circuit={LIB}", "-o", target])

        build(exe, *cfg, *candidate_cfg)
        if args.shared_port_exp or args.schur_follower or args.predict_cathode:
            unit = AREA / "r59-port-tests.exe"
            build(unit, *cfg, *candidate_cfg, "--test")
            report["port_unit_tests"] = run([unit, "contour_ports::tests", "--nocapture"]).decode()
        control = AREA / "r59-scalar.exe"
        if args.packed_products:
            build(control, *control_cfg, *candidate_cfg)
        eager = AREA / "r59-eager.exe"
        if args.compare_eager:
            build(eager, *cfg, *candidate_cfg, "--cfg", "pilot_r59_eager")
        odd_control = AREA / "r59-odd-control.exe"
        if args.packed_odd:
            build(odd_control, *odd_control_cfg, *candidate_cfg)
        seed_control = AREA / "r59-seed-control.exe"
        if seed_cfg:
            build(seed_control, *cfg, *follower_cfg, *prediction_cfg)
        follower_control = AREA / "r59-follower-control.exe"
        if follower_cfg:
            build(follower_control, *cfg, *seed_cfg, *prediction_cfg)
        prediction_control = AREA / "r59-prediction-control.exe"
        if prediction_cfg:
            build(prediction_control, *cfg, *seed_cfg, *follower_cfg, *prediction_control_cfg)
        profile_exe = AREA / "r59-profile.exe"
        seed_control_profile = AREA / "r59-seed-control-profile.exe"
        follower_control_profile = AREA / "r59-follower-control-profile.exe"
        prediction_control_profile = AREA / "r59-prediction-control-profile.exe"
        if args.profile:
            profile_flags = [*cfg, "--cfg", "pilot_r59_profile"]
            build(profile_exe, *profile_flags, *candidate_cfg)
            if seed_cfg:
                build(seed_control_profile, *profile_flags, *follower_cfg, *prediction_cfg)
            if follower_cfg:
                build(follower_control_profile, *profile_flags, *seed_cfg, *prediction_cfg)
            if prediction_cfg:
                build(prediction_control_profile, *profile_flags, *seed_cfg, *follower_cfg, *prediction_control_cfg)
        header = np.r_[dc[:136], bias[:5]]

        def controls(time):
            original = stimulus(time)
            if moving_cathode:
                c2_delta = 0.5 * original[:, 1]
                cathode = cathode_v + cathode_amplitude_v * np.sin(2. * np.pi * 263. * time)
            else:
                c2_delta = original[:, 1]
                cathode = np.full(len(time), cathode_v)
            return np.column_stack((original[:, 0], bias[5] + c2_delta, cathode, center[1] + original[:, 2]))

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
        cr6 = cr6_voltage(fine[8], input[:, 2])
        report["reference_cr6_forward_range_v"] = [float(cr6.min()), float(cr6.max())]
        reference_cr6_current = cr6_current(cr6)
        reference_crossings = cr6_crossings(cr6)
        report["reference_cr6_current_range_a"] = [float(reference_cr6_current.min()), float(reference_cr6_current.max())]
        report["reference_cr6_crossings"] = reference_crossings
        report["reference_cathode_gate"] = bool(
            not args.vary_cathode or (cr6.min() > 0. and np.ptp(input[:, 2]) > 0.)
        )
        if args.cross_cathode:
            report["reference_cathode_gate"] = (
                len(reference_crossings) >= 2 and any(tick >= STEPS for tick in reference_crossings)
            )
        coarse_cr6 = cr6_voltage(fine[4], input[:, 2])
        report["refinement_cr6_error_a"] = float(abs(cr6_current(coarse_cr6) - reference_cr6_current).max())
        report["refinement_cr6_crossings"] = cr6_crossings(coarse_cr6)
        if args.cross_cathode:
            report["reference_cathode_gate"] = (report["reference_cathode_gate"]
                                               and report["refinement_cr6_crossings"] == reference_crossings
                                               and report["refinement_cr6_error_a"] <= RETURN_LIMIT_A)
        payload = packed(np.r_[header, input.ravel()])
        report.update(input_sha256=digest(payload), input=pack_bytes(payload), cases={})
        outputs, charges = {}, {}
        controls_to_compare = {}
        if args.packed_products:
            controls_to_compare["scalar"] = control
        if args.compare_eager:
            controls_to_compare["eager"] = eager
        if args.packed_odd:
            controls_to_compare["odd_control"] = odd_control
        if seed_cfg:
            controls_to_compare["seed_control"] = seed_control
        if follower_cfg:
            controls_to_compare["follower_control"] = follower_control
        if prediction_cfg:
            controls_to_compare["prediction_control"] = prediction_control
        variants = [(name, target, "cached") for name, target in controls_to_compare.items()]
        variants.extend((("cached", exe, "cached"), ("fresh", exe, "fresh")))
        charge_bytes = CHARGES * 8
        for name, target, mode in variants:
            raw = run([target, mode, 128, "--charges"], payload, repeat=True)
            got = np.frombuffer(raw, "<f8")
            assert np.isfinite(got).all()
            stats, rows = got[:4], got[4:-CHARGES].reshape(2 * STEPS, 13)
            result = assess(rows, fine[8])
            item = dict(comparison=result, max_iterations=int(stats[0]), max_closure_v=float(stats[1]),
                        max_r59_mismatch_a=float(stats[2]), tangent_calls=int(stats[3]),
                        output_sha256=digest(raw[:-charge_bytes]),
                        final_charge_sha256=digest(raw[-charge_bytes:]), unchanged_replay=True)
            item["r59_source_range_v"] = [float(rows[:, 11].min()), float(rows[:, 11].max())]
            item["passed"] = bool(result["passed"] and stats[1] <= 1e-10 and stats[2] <= 2e-12)
            if args.cross_cathode:
                voltage = cr6_voltage(rows, input[:, 2])
                item["cr6_current_error_a"] = float(abs(cr6_current(voltage) - reference_cr6_current).max())
                item["cr6_crossings"] = cr6_crossings(voltage)
                item["passed"] = (item["passed"] and item["cr6_current_error_a"] <= RETURN_LIMIT_A
                                  and item["cr6_crossings"] == reference_crossings)
            item["timing"] = time_blocks(target, mode, payload)
            item["realtime"] = item["passed"] and item["timing"]["max_ns"] <= BUDGET_NS and item["timing"]["allocations"] == 0
            report["cases"][name] = item
            outputs[name] = rows
            charges[name] = got[-CHARGES:]
            print(name, item, flush=True)
        partition = run([exe, "cached", 64, "--charges"], payload, repeat=True)
        cached = report["cases"]["cached"]
        report["partition_bit_exact"] = (
            digest(partition[:-charge_bytes]) == cached["output_sha256"]
            and digest(partition[-charge_bytes:]) == cached["final_charge_sha256"]
        )
        report["cached_vs_fresh"] = assess(outputs["cached"], outputs["fresh"])
        report["passed"] = bool(report["refinement"]["passed"] and report["reference_source_domain_passed"]
                                 and report["reference_cathode_gate"] and report["partition_bit_exact"]
                                 and report["cached_vs_fresh"]["passed"] and all(v["passed"] for v in report["cases"].values()))
        if args.profile:
            profiles = {"profile": (profile_exe, cached)}
            if seed_cfg:
                profiles["seed_control_profile"] = (seed_control_profile, report["cases"]["seed_control"])
            if follower_cfg:
                profiles["follower_control_profile"] = (follower_control_profile, report["cases"]["follower_control"])
            if prediction_cfg:
                profiles["prediction_control_profile"] = (prediction_control_profile, report["cases"]["prediction_control"])
            for key, (target, expected) in profiles.items():
                measured = profile_blocks(target, payload, expected)
                report[key] = measured
                report["passed"] = report["passed"] and measured["bit_exact"] and measured["instrumented_timing"]["allocations"] == 0
                print(key.upper(), measured, flush=True)
        report["realtime"] = report["passed"] and report["cases"]["cached"]["realtime"]
        for name, target in controls_to_compare.items():
            exact = all(report["cases"][name][key] == cached[key]
                        for key in ("output_sha256", "final_charge_sha256"))
            pairs = [
                {variant: time_blocks(binary, "cached", payload) for variant, binary in order}
                for order in ((("cached", exe), (name, target)), ((name, target), ("cached", exe)))
            ]
            ratio = float(np.median([pair["cached"]["median_ns"] for pair in pairs])
                          / np.median([pair[name]["median_ns"] for pair in pairs]))
            passed = exact
            if name == "scalar":
                report.update(packed_bit_exact=exact, packed_vs_scalar=assess(outputs["cached"], outputs[name]),
                              paired_timing=pairs, paired_median_ratio=ratio)
            elif name == "eager":
                report.update(eager_bit_exact=exact, eager_paired_timing=pairs, eager_median_ratio=ratio)
            elif name == "odd_control":
                report.update(odd_bit_exact=exact, odd_paired_timing=pairs, odd_median_ratio=ratio)
            elif name == "seed_control":
                difference = assess(outputs["cached"], outputs[name])
                maximum_charge = float(abs(charges["cached"] - charges[name]).max())
                report.update(seed_bit_exact=exact, seed_comparison=difference, seed_paired_timing=pairs,
                              seed_median_ratio=ratio, seed_maximum_charge_difference_c=maximum_charge,
                              seed_charge_limit_c=CHARGE_LIMIT_C)
                if args.feedback_seed:
                    passed = difference["passed"] and maximum_charge <= CHARGE_LIMIT_C
            else:
                difference = assess(outputs["cached"], outputs[name])
                maximum_charge = float(abs(charges["cached"] - charges[name]).max())
                prefix = name.removesuffix("_control")
                report.update({f"{prefix}_{key}": value for key, value in
                               dict(bit_exact=exact, comparison=difference, paired_timing=pairs, median_ratio=ratio,
                                    maximum_charge_difference_c=maximum_charge, charge_limit_c=CHARGE_LIMIT_C).items()})
                passed = difference["passed"] and maximum_charge <= CHARGE_LIMIT_C
            report["passed"] = report["passed"] and passed
            report["realtime"] = bool(report["passed"] and report["realtime"] and all(
                pair["cached"]["max_ns"] <= BUDGET_NS and pair["cached"]["allocations"] == 0
                for pair in pairs))
            print(name.upper(), "passed", passed, "bit exact", exact, "median ratio", ratio, flush=True)
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
