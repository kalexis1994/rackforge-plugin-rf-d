"""Audit endpoint recovery, preserved electrical reserves and physical 128-frame passes."""

import subprocess
import winreg

from affine_evidence import encode_json, recover
from check_hybrid_voice import unpack
from check_recovery_cost import digest, read
from check_recovery_engine128 import AREA, HOST, analyze, cargo_artifacts, engine_fixture, retire_lab
from check_recovery_engine128_endpoint import ENABLED, NVIDIA, PHYSICAL, endpoint_rows, snapshot
from check_recovery_engine128_smt import (
    ARTIFACTS, ENDPOINT, FIR, NVIDIA_ENDPOINT, O3_INPUTS, REFERENCE, RESERVE, admitted, analyze_smt,
)
from check_recovery_host128 import asio_profile, read_override
from prepare_dual_chain import ROOT, sha, write
from validate_recovery_engine128 import git_blob
from validate_recovery_engine128_fuel import HOST_FIXED

PREFIX = "evidence/recovery_engine128_"
PRIOR = PREFIX + "smt_tests01.json"
OUT = PREFIX + "physical_tests01.json"
UPDATED = {
    "tools/check_recovery_engine128.py",
    "tools/check_recovery_engine128_smt.py",
    "tools/recovery_engine128_smt.rs",
}
NVIDIA_KEYS = ("A65359A8", r"A65359A8\8948B95D", r"A65359A8\8948B95D\00000000")


def check_reads(items, expected):
    assert len(items) == 2
    pairs = []
    for item in items:
        metrics = endpoint_rows(unpack(item["output"]), expected)
        assert encode_json(metrics) == encode_json(item["metrics"])
        pairs.append(tuple(channel["name"] for channel in metrics["outputs"][:2]))
    return pairs


def check_endpoints(names, profile):
    first, absent, trials, recovery, *later = [read(name) for name in names]
    assert not later or all(report["passed"] for report in later)
    for report in (first, absent, trials, recovery, *later):
        recover(report)
        assert "failure" not in report and report["build"]["exit_code"] == 0
        assert report["temporary_probe_retired"] and report["other_profiles_unchanged"]
        assert report["profile"] == profile
    assert first["passed"] and first["action"] == "already-present"
    assert check_reads([first["before"], first["after"]], PHYSICAL) == [PHYSICAL, PHYSICAL]
    assert all(len(first[key]["metrics"]["outputs"]) == 8 for key in ("before", "after"))
    rejected = first["link_rejection"]
    for key in ("stderr", "replay_stderr"):
        raw = unpack(rejected[key])
        assert b"__imp_CharLowerBuffA" in raw and b"__imp_RegOpenKey" in raw
    assert rejected["replay_exit_code"] != 0
    assert not read(PREFIX + "smt05.json")["endpoint_available"]

    disconnected = ("Not Connected 1", "Not Connected 2")
    baseline = first["initial_lab"]
    for report in (first, absent, trials):
        assert report["initial_lab"] == report["final_lab"] == baseline
    for report in (absent, trials, recovery):
        expected = tuple(report.get("expected_channels", PHYSICAL))
        assert check_reads(report["reads"], expected) == [disconnected, disconnected]
    assert not absent["passed"] and not trials["passed"]
    nvidia, *realtek = trials["trials"]
    assert len(realtek) == 2
    assert check_reads(nvidia["reads"], PHYSICAL) == [NVIDIA, NVIDIA]
    for trial in trials["trials"]:
        assert not trial["passed"] and trial["restored"]
    for trial in realtek:
        assert check_reads(trial["reads"], PHYSICAL) == [disconnected, disconnected]

    assert recovery["passed"] and tuple(recovery["expected_channels"]) == NVIDIA
    assert recovery["initial_lab"] == baseline
    selection, = recovery["trials"]
    assert selection["passed"] and tuple(selection["keys"]) == NVIDIA_KEYS
    hardware = recovery["active_hardware"][selection["device"]]
    assert NVIDIA_KEYS[0] in hardware["hashes"] and hardware["endpoints"]
    assert check_reads(selection["reads"], NVIDIA) == [NVIDIA, NVIDIA]
    final = dict(baseline)
    final.update({key: {"Flags": [ENABLED, winreg.REG_DWORD]} for key in NVIDIA_KEYS})
    assert recovery["final_lab"] == final
    assert len(later) == 1
    for report in later:
        assert tuple(report["expected_channels"]) == NVIDIA
        assert check_reads(report["reads"], NVIDIA) == [NVIDIA, NVIDIA]
        assert report["initial_lab"] == report["final_lab"]
    current = snapshot(profile)
    if later:
        assert current == later[-1]["final_lab"]
    # Opening a different endpoint can make ASIO4ALL publish new latency offsets.
    # The endpoint selection, other settings, rate and buffer override must match.
    def without_latency(tree):
        return {**tree, "": {key: value for key, value in tree[""].items() if key not in ("LtcyIn", "LtcyOut")}}

    assert without_latency(current) == without_latency(final)
    for key in ("LtcyIn", "LtcyOut"):
        assert current[""][key][1] == winreg.REG_DWORD
    return selection["device"]


def check_package(report):
    level = report["wasm_opt_level"]
    inputs = O3_INPUTS if level == 3 else (REFERENCE, RESERVE, FIR)
    reference, reserve, fir = (read(path) for path in inputs)
    assert reference["wasm_opt_level"] == level and report["wasm_lto"]
    assert reserve["passed"] and fir["passed"] and reserve["wasm_lto"] and fir["wasm_lto"]
    assert report["reference_inputs"] == {path: sha(ROOT / path) for path in inputs}
    assert all(report["artifact_sha256"][key] == reference["artifact_sha256"][key] for key in ARTIFACTS)
    scalar, registers = (reserve["variants"][key] for key in ("scalar", "registers"))
    assert scalar["modes"] == registers["modes"]
    assert all(f"opt-level={level}" in args for args in (scalar["compile"], registers["compile"], fir["compile"]))
    assert report["artifact_sha256"]["engine_kernel_columns.rs"] == registers["kernel_sha256"] == fir["kernel_sha256"]
    assert unpack(fir["fir_check"]).strip() == b"FIR_EXACT,9288,4,48"
    fixture = report["fixtures"]
    raw = unpack(fixture["rows"])
    assert digest(raw) == fixture["sha256"] == reference["fixtures"]["sha256"]
    assert encode_json(engine_fixture(raw)) == encode_json(fixture["metrics"])


def check_banks(report, endpoint):
    assert report["qualification_campaign"]
    fixed = "quiet-hold" if report.get("lean_campaign", False) else "qualified"
    attempts = report["endpoint_checks"]
    assert 1 <= len(attempts) <= 6
    verified = [item["exit_code"] == 0 and item["endpoint"] == endpoint for item in attempts]
    assert not any(verified[:-1]) and verified[-1] == report["endpoint_available"]
    profile = report["asio_profile"]
    assert profile["before"] == profile["verified"]
    assert profile["before"].split("\t")[:4] == ["ASIO", "ASIO4ALL v2", "44100", "2"]
    assert profile["original"] == [0, winreg.REG_DWORD]
    if not report["endpoint_available"]:
        assert len(attempts) == 6 and not {"control", "confirmations"} & report.keys()
        assert profile["during"] == profile["original"] and report["admitted_policy"] is None
        return dict(policy=fixed, endpoint=endpoint, opened=False)

    confirmation, = report["confirmations"]
    assert confirmation["policy"] == fixed
    items = [report["control"], *confirmation["runs"]]
    assert [item["blocks"] for item in items] == [1200, 4800, 4800]
    assert profile["during"] == [128, winreg.REG_DWORD]
    observations = []
    for item in items:
        assert item["policy"] == fixed and item["seed"] is None
        raw = unpack(item["rows"])
        assert digest(raw) == item["sha256"]
        if item["exit_code"] != 0:
            assert not raw and "metrics" not in item
            assert endpoint in item["stream"].splitlines() and "SMT_QUALIFY_REJECT" in item["stream"]
            observations.append(dict(rejected_preflight=True))
            continue
        metrics = analyze_smt(raw, item["stream"], item["blocks"], fixed, None, report["topology"], analyze,
                              silent=item["label"] == "control", endpoint=endpoint)
        assert encode_json(metrics) == encode_json(item["metrics"])
        assert metrics["placement_verified"] and metrics["physical_endpoint_verified"]
        assert metrics["frames_128_confirmed"] and metrics["effective_rate"] == 48000
        assert metrics["host_allocations"] == metrics["slot_faults"] == 0
        observations.append(metrics)
    accepted = admitted(report["control"], confirmation["runs"])
    assert report["admitted_policy"] == (fixed if accepted else None)
    return dict(policy=fixed, endpoint=endpoint, opened=True, control=observations[0], runs=observations[1:])


def audit():
    prior = read(PRIOR)
    assert prior["passed"]
    base = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    assert base.startswith("91b6ed9")
    source_hashes = dict(prior["source_sha256"])
    for name, expected in source_hashes.items():
        raw = git_blob(f"{base}:{name}") if name in UPDATED else (ROOT / name).read_bytes()
        assert digest(raw) == expected, name
    private = prior["private_input_sha256"]
    assert len(private) == 8769 and all((ROOT / name).is_file() for name in private)
    assert sha(ROOT / prior["new_listening"]["path"]) == prior["new_listening"]["sha256"]

    endpoint_names = sorted(path.relative_to(ROOT).as_posix()
                            for path in (ROOT / "evidence").glob("recovery_engine128_endpoint[0-9][0-9].json"))
    names = sorted(path.relative_to(ROOT).as_posix() for path in (ROOT / "evidence").glob("recovery_engine128_smt[0-9][0-9].json")
                   if int(path.stem[-2:]) >= 6)
    profile = asio_profile(AREA / "recovery-host128.exe")
    assert read_override(profile) == (0, winreg.REG_DWORD)
    device = check_endpoints(endpoint_names, profile)

    reports = [read(name) for name in names]
    assert len(reports) == 5
    summary = {}
    accepted = {}
    for name, report in zip(names, reports):
        recover(report)
        assert report["passed"] and report["measurement_area_retired"] and report["host_checkout"] == HOST_FIXED
        assert report["host_build"] == reports[0]["host_build"] and report["dependencies"] == reports[0]["dependencies"]
        assert not report["whole_voice_rt"] and not report["rack_128_admitted"]
        check_package(report)
        endpoint = report.get("expected_endpoint", ENDPOINT)
        assert endpoint in (ENDPOINT, NVIDIA_ENDPOINT)
        summary[name] = check_banks(report, endpoint)
        if report["admitted_policy"]:
            accepted[name] = report["admitted_policy"]
    first_nvidia, repeated_nvidia = reports[-2:]
    for report in (first_nvidia, repeated_nvidia):
        assert report["wasm_opt_level"] == 3 and report["expected_endpoint"] == NVIDIA_ENDPOINT
        assert report["lean_campaign"]
    original_hashes = first_nvidia["artifact_sha256"]
    repeated_hashes = repeated_nvidia["artifact_sha256"]
    assert original_hashes.keys() == repeated_hashes.keys()
    rebuilt_native = {key: [value, repeated_hashes[key]] for key, value in original_hashes.items()
                      if value != repeated_hashes[key]}
    # The first audit required identical native executables as well as packages.
    # Both native binaries were rebuilt. Require identical inputs and Wasm.
    assert set(rebuilt_native) == {"recovery-host128.exe", "recovery-host-dsp.dll"}
    assert first_nvidia["host_checkout_source_sha256"] == repeated_nvidia["host_checkout_source_sha256"]
    assert [item["command"] for item in first_nvidia["build"]] == [
        item["command"] for item in repeated_nvidia["build"]
    ]
    build = reports[0]["host_build"]
    log = AREA / build["log"]
    assert sha(log) == build["sha256"]
    assert build["libraries"] == {name: sha(path) for name, path in cargo_artifacts(log).items()}
    for path, expected in reports[0]["host_checkout_source_sha256"].items():
        raw = git_blob(f"{HOST_FIXED}:{path}", HOST)
        assert expected in (digest(raw), digest(raw.replace(b"\n", b"\r\n"))), path

    names.extend(endpoint_names)
    staged = subprocess.check_output(["git", "diff", "--cached", "--name-only"], cwd=ROOT, text=True).splitlines()
    assert {OUT, *names} <= set(staged)
    for name in set(staged) - {OUT}:
        assert "recovery_engine128" in name.lower() and (name in UPDATED or name not in source_hashes)
        raw = git_blob(":" + name)
        assert raw == (ROOT / name).read_bytes(), name
        source_hashes[name] = digest(raw)
    source_hashes[PRIOR] = sha(ROOT / PRIOR)
    retained = sum((ROOT / name).stat().st_size for name in names)
    assert retained <= 4 * 1024**2
    result = {key: value for key, value in prior.items() if not key.startswith("new_") or key == "new_listening"}
    result.update(
        schema="rf-d/recovery-engine-effective-128-physical/v1", passed=True, base_commit=base,
        source_sha256=source_hashes, previous_qa=PRIOR, previous_qa_sha256=sha(ROOT / PRIOR),
        protected_public_sources=len(prior["source_sha256"]), protected_private_inputs=len(private),
        electrical_reserves_preserved=True, restored_endpoint=device, physical_confirmations=summary,
        rejected_native_identity=dict(assertion='first_nvidia["artifact_sha256"] == repeated_nvidia["artifact_sha256"]',
                                      rebuilt_sha256=rebuilt_native),
        admitted_lab_policies=accepted, rack_128_admitted=False, whole_voice_rt=False, real_time=False,
        retained_receipt_bytes=retained,
        recovery_engine128_physical_reports={name: sha(ROOT / name) for name in names},
    )
    return result


if __name__ == "__main__":
    result = audit()
    write(ROOT / OUT, result)
    retire_lab()
    result["temporary_area_empty"] = not list(AREA.iterdir())
    assert result["temporary_area_empty"]
    write(ROOT / OUT, result)
    print("PHYSICAL128_QA", result["protected_public_sources"], result["protected_private_inputs"],
          result["admitted_lab_policies"])
