"""Audit idle-aware placement, the SMT stimulus and the two-pass 128-frame gate."""

import subprocess
import winreg

from affine_evidence import encode_json, recover
from check_hybrid_voice import unpack
from check_recovery_cost import digest, read
from check_recovery_engine128 import (
    AREA, HOST, SCHEDULE_PROBE, analyze, cargo_artifacts, engine_fixture, retire_lab,
)
from check_recovery_engine128_smt import ARTIFACTS, ENDPOINT, FIR, REFERENCE, RESERVE, SEED, admitted, analyze_smt
from check_recovery_host128 import asio_profile, read_override
from prepare_dual_chain import ROOT, sha, write
from validate_recovery_engine128 import git_blob
from validate_recovery_engine128_fuel import HOST_FIXED

PREFIX = "evidence/recovery_engine128_"
PRIOR = PREFIX + "schedule_tests01.json"
OUT = PREFIX + "smt_tests01.json"
UPDATED = {"tools/check_recovery_engine128.py", SCHEDULE_PROBE}


def measured(item, top, parse_failed=False):
    raw = unpack(item["rows"])
    assert digest(raw) == item["sha256"]
    if not parse_failed and "metrics" not in item:
        assert item["exit_code"] != 0 or item["analysis_failure"]
        return {}
    assert item["exit_code"] == 0
    observed = analyze_smt(raw, item["stream"], item["blocks"], item["policy"], item["seed"], top, analyze,
                           silent=item["label"] == "control")
    if not parse_failed:
        expected = item["metrics"]
        comparison = dict(observed)
        if "background_calls" not in expected:
            assert not comparison.pop("background_calls", []) and comparison.pop("observer_cpu", None) is None
        if "physical_endpoint_verified" not in expected:
            comparison.pop("physical_endpoint_verified")
            comparison["gate_passed"] = comparison.pop("timing_gate_passed")
        assert encode_json(comparison) == encode_json(expected)
    return observed


def audit():
    prior = read(PRIOR)
    assert prior["passed"]
    base = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    assert base.startswith("13b7099")
    sources = dict(prior["source_sha256"])
    for name, expected in sources.items():
        raw = git_blob(f"{base}:{name}") if name in UPDATED else (ROOT / name).read_bytes()
        assert digest(raw) == expected, name
    private = prior["private_input_sha256"]
    assert len(private) == 8769 and all((ROOT / name).is_file() for name in private)
    assert sha(ROOT / prior["new_listening"]["path"]) == prior["new_listening"]["sha256"]

    names = [path.relative_to(ROOT).as_posix() for path in sorted((ROOT / "evidence").glob("recovery_engine128_smt[0-9][0-9].json"))]
    reports = [read(name) for name in names]
    assert len(reports) == 5
    reference, reserve, fir = (read(path) for path in (REFERENCE, RESERVE, FIR))
    assert reserve["passed"] and fir["passed"] and reserve["wasm_opt_level"] == fir["wasm_opt_level"] == 2
    kernel = reference["artifact_sha256"]["engine_kernel_columns.rs"]
    assert kernel == reserve["variants"]["registers"]["kernel_sha256"] == fir["kernel_sha256"]
    assert reserve["variants"]["registers"]["modes"] == reserve["variants"]["scalar"]["modes"]
    assert unpack(fir["fir_check"]).strip() == b"FIR_EXACT,9288,4,48"
    original, inline = reports[:2]
    assert not original["passed"] and inline["passed"]
    rejected = original["pressure"][0]
    assert "JSONDecodeError" in rejected["analysis_failure"]
    assert "JSONDecodeError" in rejected["unchanged_replay"]["analysis_failure"]
    for item in (rejected, rejected["unchanged_replay"]):
        m = measured(item, original["topology"], parse_failed=True)
        assert m["frames_128_confirmed"] and m["placement_verified"] and m["initial_cpu"] == SEED

    results = {}
    accepted = {}
    for name, report in zip(names, reports):
        recover(report)
        assert report["measurement_area_retired"] and report["host_checkout"] == HOST_FIXED
        assert report["reference_inputs"] == {path: sha(ROOT / path) for path in (REFERENCE, RESERVE, FIR)}
        assert report["host_build"] == inline["host_build"] and report["dependencies"] == inline["dependencies"]
        assert report["wasm_opt_level"] == 2 and report["wasm_lto"]
        assert all(report["artifact_sha256"][key] == reference["artifact_sha256"][key] for key in ARTIFACTS)
        fixture = report["fixtures"]
        raw = unpack(fixture["rows"])
        assert digest(raw) == fixture["sha256"] == reference["fixtures"]["sha256"]
        assert encode_json(engine_fixture(raw)) == encode_json(fixture["metrics"])
        profile = report["asio_profile"]
        assert profile["before"] == profile["verified"]
        before = profile["before"].split("\t")
        previous = reference["asio_profile"]["before"].split("\t")
        assert before[:4] == previous[:4] and before[5:] == previous[5:]
        assert encode_json(profile["original"]) == encode_json(reference["asio_profile"]["original"])
        if report.get("endpoint_available") is False:
            assert encode_json(profile["during"]) == encode_json(profile["original"])
        else:
            assert encode_json(profile["during"]) == encode_json(reference["asio_profile"]["during"])
        if not report["passed"]:
            assert report["failure"]
            continue
        if "endpoint_checks" in report:
            attempts = report["endpoint_checks"]
            assert 1 <= len(attempts) <= 6
            available = attempts[-1]["exit_code"] == 0 and attempts[-1]["endpoint"] == ENDPOINT
            assert report["endpoint_available"] == available
            assert not any(attempt["exit_code"] == 0 and attempt["endpoint"] == ENDPOINT for attempt in attempts[:-1])
            if not available:
                assert len(attempts) == 6 and report["admitted_policy"] is None and "control" not in report
                results[name] = dict(endpoint_available=False, attempts=attempts)
                continue
        top = report["topology"]
        control = measured(report["control"], top)
        if report.get("qualification_campaign", False):
            confirmation, = report["confirmations"]
            assert confirmation["policy"] == "qualified"
            runs = confirmation["runs"]
            assert len(runs) == 2 and all(item["policy"] == "qualified" and item["blocks"] == 4800
                                          and item["seed"] is None for item in runs)
            observed = [measured(item, top) for item in runs]
            for item, metrics in zip([report["control"], *runs], [control, *observed]):
                if metrics:
                    assert "qualification" in metrics and metrics["placement_verified"]
                else:
                    assert item["exit_code"] != 0 and "SMT_QUALIFY_REJECT" in item["stream"]
            if control.get("gate_passed", False) and all(metrics.get("gate_passed", False) for metrics in observed):
                accepted[name] = "qualified"
            assert accepted.get(name) == report["admitted_policy"]
            results[name] = dict(qualifications=[control, *observed])
            continue
        assert control["frames_128_confirmed"]
        first, second = report["pressure"]
        policy = "background" if report.get("background_campaign", False) else "adaptive"
        assert first["policy"] == "hold" and second["policy"] == policy
        assert first["seed"] == second["seed"] == SEED
        for item in (first, second):
            m = measured(item, top)
            assert m["frames_128_confirmed"] and m["placement_verified"] and m["host_allocations"] == 0
        fixed, moved = first["metrics"], second["metrics"]
        assert moved["settled_wall_ns"]["median"] < fixed["settled_wall_ns"]["median"]
        assert moved["observed_changes"][1][1] != SEED
        summaries = []
        for confirmation in report["confirmations"]:
            runs = confirmation["runs"]
            assert len(runs) == 2
            assert all(run["blocks"] == 4800 and run["seed"] is None
                       and run["policy"] == confirmation["policy"] for run in runs)
            summaries.append(dict(policy=confirmation["policy"],
                                  runs=[measured(run, top) for run in runs]))
            if admitted(report["control"], runs):
                accepted[name] = confirmation["policy"]
        assert accepted.get(name) == report["admitted_policy"]
        results[name] = dict(
            pressure_hold_median_ns=fixed["settled_wall_ns"]["median"],
            pressure_adaptive_median_ns=moved["settled_wall_ns"]["median"],
            blocks_to_move=moved["observed_changes"][1][0] - moved["load_at"],
            confirmations=summaries,
        )
    assert not inline["admitted_policy"]
    assert max(item["metrics"]["affinity_ns"]["max"] for bank in inline["confirmations"]
               if bank["policy"] == "adaptive" for item in bank["runs"]) > 128e9 / 48000 / 2
    build = inline["host_build"]
    log = AREA / build["log"]
    assert sha(log) == build["sha256"]
    assert build["libraries"] == {name: sha(path) for name, path in cargo_artifacts(log).items()}
    for path, expected in inline["host_checkout_source_sha256"].items():
        raw = git_blob(f"{HOST_FIXED}:{path}", HOST)
        assert expected in (digest(raw), digest(raw.replace(b"\n", b"\r\n"))), path
    assert read_override(asio_profile(AREA / "recovery-host128.exe")) == (0, winreg.REG_DWORD)

    staged = subprocess.check_output(["git", "diff", "--cached", "--name-only"], cwd=ROOT, text=True).splitlines()
    assert {OUT, *names} <= set(staged)
    for name in set(staged) - {OUT}:
        assert "recovery_engine128" in name.lower() and (name in UPDATED or name not in sources)
        raw = git_blob(":" + name)
        assert raw == (ROOT / name).read_bytes(), name
        sources[name] = digest(raw)
    sources[PRIOR] = sha(ROOT / PRIOR)
    retained = sum((ROOT / name).stat().st_size for name in names)
    assert retained <= 5 * 1024**2
    result = {key: value for key, value in prior.items() if not key.startswith("new_") or key == "new_listening"}
    result.update(
        schema="rf-d/recovery-engine-effective-128-smt/v1", passed=True, base_commit=base,
        source_sha256=sources, previous_qa=PRIOR, previous_qa_sha256=sha(ROOT / PRIOR),
        protected_public_sources=len(prior["source_sha256"]), protected_private_inputs=len(private),
        electrical_reserves_preserved=True, smt_results=results, admitted_lab_policies=accepted,
        rack_128_admitted=False, whole_voice_rt=False, real_time=False,
        audit_adapter_corrections=[
            "KeyError background_calls on the silent control without an SMT policy",
            "Device enumeration changed from eight outputs to two with the measured pair Not Connected",
        ],
        retained_receipt_bytes=retained,
        recovery_engine128_smt_reports={name: sha(ROOT / name) for name in names},
    )
    return result


if __name__ == "__main__":
    result = audit()
    write(ROOT / OUT, result)
    retire_lab()
    result["temporary_area_empty"] = not list(AREA.iterdir())
    assert result["temporary_area_empty"]
    write(ROOT / OUT, result)
    print("SMT128_QA", result["protected_public_sources"], result["protected_private_inputs"],
          result["admitted_lab_policies"])
