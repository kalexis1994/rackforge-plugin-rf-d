"""Audit unchanged electrical reserves and exact-ASIO confirmations for solver SIMD."""

import subprocess
import winreg

from affine_evidence import encode_json, recover
from check_hybrid_voice import unpack
from check_recovery_cost import digest, read
from check_recovery_engine128 import (
    AREA, HOST, PLAN, analyze, cargo_artifacts, column_kernel, engine_fixture, retire_lab, sources_for_build,
)
from check_recovery_engine128_reserve import PHYSICAL, REF, fir_source, probe_source
from check_recovery_engine128_work import REF as ASIO_REF, analyze as analyze_work
from check_recovery_host128 import asio_profile, read_override
from prepare_dual_chain import ROOT, sha, write
from validate_recovery_engine128 import git_blob
from validate_recovery_engine128_broadcast import tail
from validate_recovery_engine128_fuel import HOST_FIXED

BASE = "1a1e65d953fb420086f15ac6f9400afc96e8e74f"
PREFIX = "evidence/recovery_engine128_"
PREVIOUS = PREFIX + "broadcast_tests01.json"
OUT = PREFIX + "hot_tests01.json"
UPDATED = {"tools/check_recovery_engine128.py", "tools/check_recovery_engine128_reserve.py"}


def receipts(kind, first):
    for path in sorted((ROOT / "evidence").glob(f"recovery_engine128_{kind}[0-9][0-9].json")):
        if int(path.stem[-2:]) >= first:
            name = path.relative_to(ROOT).as_posix()
            report = read(name)
            recover(report)
            assert report["measurement_area_retired"], name
            yield name, report


def reserves(reports, prior):
    validated = set()
    tables = (AREA / "reserve-vectors.bin", AREA / "reserve-stress.bin")
    baseline = prior["variants"]["scalar"]["modes"]
    for report in reports:
        assert report["passed"]
        assert report["reference_sha256"] == sha(ROOT / REF)
        assert report["physical_sha256"] == sha(ROOT / PHYSICAL)
        if "results" in report:
            assert encode_json(report["results"]) == encode_json(prior["results"])
        else:
            replay = report["physical_replay"]
            assert replay["path"] == PREFIX + "reserve01.json" and replay["sha256"] == sha(ROOT / replay["path"])
        for variant, item in report["variants"].items():
            assert encode_json(item["modes"]) == encode_json(baseline)
            if variant in ("hot", "model", "columns", "registers"):
                model = variant != "hot"
                kernel = column_kernel(True, True, model, variant == "columns", variant == "registers")
                assert digest(kernel) == item["kernel_sha256"]
                assert digest(probe_source(AREA / "reserve-kernel.rs", tables, model)) == item["probe_sha256"]
                validated.add((item["kernel_sha256"], report.get("wasm_lto", False)))
    return validated


def asio_audit(report, reference, validated, fir):
    assert report["host_checkout"] == HOST_FIXED and report["wasm_opt_level"] == 3
    assert report["column_simd"] and report["broadcast_simd"] and report["split_fir"] and report["hot_simd"]
    assert not report["whole_voice_rt"]
    kernel = column_kernel(True, True, report.get("specialize", False), report.get("column_solve", False),
                           report.get("registers", False))
    identity = digest(kernel), report.get("wasm_lto", False)
    assert report["artifact_sha256"]["engine_kernel_columns.rs"] == identity[0]
    assert identity in validated and identity in fir
    guest, probe = sources_for_build(AREA / "engine_kernel_columns.rs", True)
    assert digest(guest) == report["artifact_sha256"]["engine_guest.rs"]
    assert digest(probe) == report["artifact_sha256"]["engine_probe.rs"]
    for source, expected in report["host_checkout_source_sha256"].items():
        raw = git_blob(f"{HOST_FIXED}:{source}", HOST)
        assert expected in (digest(raw), digest(raw.replace(b"\n", b"\r\n"))), source
    fixture = report["fixtures"]
    raw = unpack(fixture["rows"])
    assert digest(raw) == fixture["sha256"] == reference["fixtures"]["sha256"]
    assert encode_json(engine_fixture(raw)) == encode_json(fixture["metrics"])
    assert encode_json(report["asio_profile"]) == encode_json(reference["asio_profile"])
    assert [(bank["mode"], bank["blocks"]) for bank in report["banks"]] == PLAN
    summary = []
    all_passed = True
    for bank in report["banks"]:
        mode, blocks, runs = bank["mode"], bank["blocks"], bank["runs"]
        count = 2 if blocks == 4800 or not runs[0]["metrics"]["gate_passed"] else 1
        assert len(runs) == count
        for run in runs:
            raw = unpack(run["rows"])
            assert run["exit_code"] == 0 and digest(raw) == run["sha256"]
            metrics = analyze(raw, run["stream"], blocks, mode)
            assert encode_json(metrics) == encode_json(run["metrics"])
            assert metrics["host_allocations"] == metrics["slot_faults"] == 0
            if not metrics["frames_128_confirmed"]:
                assert not metrics["gate_passed"] and not report["rack_128_admitted"]
            all_passed &= metrics["gate_passed"]
            if blocks == 4800:
                summary.append(dict(metrics=metrics, tail=tail(raw, blocks)))
    assert report["rack_128_admitted"] == all_passed
    return summary


def audit():
    prior = read(PREVIOUS)
    assert prior["passed"]
    source_hashes = dict(prior["source_sha256"])
    for name, expected in source_hashes.items():
        raw = git_blob(f"{BASE}:{name}") if name in UPDATED else (ROOT / name).read_bytes()
        assert digest(raw) == expected, name
    private = prior["private_input_sha256"]
    assert len(private) == 8769 and all((ROOT / name).is_file() for name in private)
    assert sha(ROOT / prior["new_listening"]["path"]) == prior["new_listening"]["sha256"]
    reference = read(ASIO_REF)
    observed = {}
    failed_work, work = list(receipts("work", 1))
    for name, report in (failed_work, work):
        observed[name] = sha(ROOT / name)
    failed = failed_work[1]
    assert not failed["passed"]
    for key in ("failed_output", "unchanged_replay"):
        assert failed[key]["exit_code"] == 1 and b"E0753" in unpack(failed[key]["stderr"])
    work = work[1]
    assert work["passed"] and work["reference_sha256"] == sha(ROOT / ASIO_REF)
    assert work["kernel_sha256"] == reference["artifact_sha256"]["engine_kernel_columns.rs"]
    assert encode_json(analyze_work(unpack(work["raw"]), reference)) == encode_json(work["metrics"])

    all_reserves = list(receipts("reserve", 2))
    all_firs = list(receipts("broadcast_fir", 2))
    for name, _ in [*all_reserves, *all_firs]:
        observed[name] = sha(ROOT / name)
    accepted = reserves([r for _, r in all_reserves if r["passed"]], read(PREFIX + "reserve01.json"))
    fir = set()
    for _, report in all_firs:
        if report["passed"]:
            assert digest(fir_source(AREA / "reserve-kernel.rs")) == report["probe_sha256"]
            assert unpack(report["fir_check"]).strip() == b"FIR_EXACT,9288,4,48"
            fir.add((report["kernel_sha256"], report.get("wasm_lto", False)))
    for _, report in [*all_reserves, *all_firs]:
        if not report["passed"]:
            assert report["failure"] and "unchanged_replay" in report
    summary, admitted, build = {}, [], None
    for name, report in receipts("native", 10):
        observed[name] = sha(ROOT / name)
        if not report["passed"]:
            assert report["failure"] and "unchanged_failure_replay" in report
            continue
        build = build or report["host_build"]
        assert report["host_build"] == build
        summary[name] = asio_audit(report, reference, accepted, fir)
        if report["rack_128_admitted"]:
            admitted.append(name)
    assert len(summary) >= 3
    log = AREA / build["log"]
    assert sha(log) == build["sha256"]
    assert build["libraries"] == {name: sha(path) for name, path in cargo_artifacts(log).items()}
    assert read_override(asio_profile(AREA / "recovery-host128.exe")) == (0, winreg.REG_DWORD)

    staged = subprocess.check_output(["git", "diff", "--cached", "--name-only"], cwd=ROOT, text=True).splitlines()
    assert {OUT, *observed} <= set(staged)
    for name in set(staged) - {OUT}:
        assert "recovery_engine128" in name.lower() and (name in UPDATED or name not in source_hashes)
        raw = git_blob(":" + name)
        assert raw == (ROOT / name).read_bytes(), name
        source_hashes[name] = digest(raw)
    source_hashes[PREVIOUS] = sha(ROOT / PREVIOUS)
    retained = sum((ROOT / name).stat().st_size for name in observed)
    assert retained <= 5 * 1024**2
    result = {key: value for key, value in prior.items() if not key.startswith("new_") or key == "new_listening"}
    result.update(
        schema="rf-d/recovery-engine-effective-128-hot/v1", passed=True, base_commit=BASE,
        source_sha256=source_hashes, previous_qa=PREVIOUS, previous_qa_sha256=sha(ROOT / PREVIOUS),
        protected_public_sources=len(prior["source_sha256"]), protected_private_inputs=len(private),
        solver_work=work["metrics"], electrical_reserves_admitted=True, same_laws_bit_exact=True,
        long_confirmation=summary, rack_128_admitted=bool(admitted), admitted_reports=admitted,
        whole_voice_rt=False, real_time=False, retained_receipt_bytes=retained,
        recovery_engine128_hot_reports=observed,
    )
    return result


if __name__ == "__main__":
    result = audit()
    write(ROOT / OUT, result)
    retire_lab()
    result["temporary_area_empty"] = not list(AREA.iterdir())
    assert result["temporary_area_empty"]
    write(ROOT / OUT, result)
    print("HOT128_QA", result["protected_public_sources"], result["protected_private_inputs"],
          result["retained_receipt_bytes"], result["admitted_reports"])
