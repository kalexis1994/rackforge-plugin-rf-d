"""Verify the nominal portable voice and keep its physical rejection separate."""

import subprocess
import winreg

from affine_evidence import encode_json, recover
from check_hybrid_voice import unpack
from check_recovery_cost import digest, read
from check_recovery_engine128 import AREA, HOST, cargo_artifacts, retire_lab
from check_recovery_engine128_endpoint import NVIDIA, snapshot
from check_recovery_engine128_mono import check_electrical_inputs, compare_trajectory, parse_timed_rejection
from check_recovery_engine128_smt import NVIDIA_ENDPOINT
from check_recovery_host128 import asio_profile, read_override
from prepare_dual_chain import ROOT, sha, write
from validate_recovery_engine128 import git_blob
from validate_recovery_engine128_fuel import HOST_FIXED
from validate_recovery_engine128_physical import check_reads

PREFIX = "evidence/recovery_engine128_"
PRIOR = PREFIX + "nvidia_tests01.json"
PHYSICAL = PREFIX + "physical_tests01.json"
OUT = PREFIX + "mono_tests01.json"
UPDATED = "tools/check_recovery_engine128.py"


def audit():
    base = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    assert base.startswith("6a01921")
    prior = read(PRIOR)
    previous = read(PHYSICAL)
    assert prior["passed"] and previous["passed"] and prior["electrical_reserves_preserved"]
    known = {**previous["source_sha256"], **prior["verified_source_sha256"]}
    for name, expected in known.items():
        raw = git_blob(f"{base}:{name}") if name == UPDATED else (ROOT / name).read_bytes()
        assert digest(raw) == expected, name
    private = previous["private_input_sha256"]
    assert len(private) == 8769 and all((ROOT / name).is_file() for name in private)
    listening = previous["new_listening"]
    assert sha(ROOT / listening["path"]) == listening["sha256"]

    names = sorted(path.relative_to(ROOT).as_posix() for path in (ROOT / "evidence").glob(
        "recovery_engine128_mono[0-9][0-9].json"))
    reports = [read(name) for name in names]
    for record in reports:
        recover(record)
        assert record["measurement_area_retired"]
    report = reports[-1]
    assert not report.get("rack_128_admitted", False) and not report.get("whole_voice_rt", False)
    if not report["passed"]:
        assert "incomplete physical rejection pair" in report["failure"]
    assert report["host_checkout"] == HOST_FIXED and report["wasm_opt_level"] == 3 and report["wasm_lto"]
    assert report["electrical_inputs"] == check_electrical_inputs(report["artifact_sha256"])
    node = report["node"]
    first = reports[0]
    assert not first["passed"] and "has no attribute 'read_bytes'" in first["failure"]
    assert first["artifact_sha256"]["package-dsp/component.wasm"] == report["artifact_sha256"]["package-dsp/component.wasm"]
    for name in ("failed_output", "unchanged_failure_replay"):
        result = first[name]
        assert result["exit_code"] == 0
        assert unpack(result["stdout"]) == unpack(node["rows"])
    assert encode_json(compare_trajectory(unpack(node["rows"]))) == encode_json(node["electrical"])
    fence, = [line for line in report["epoch_fence"].splitlines() if line.startswith("MONO_FENCE\t")]
    _, elapsed, _ = fence.split("\t", 2)
    assert 128e9 / 48000 / 2 < int(elapsed) <= 1_000_000_000
    assert "interrupt" in report["epoch_fence"].lower()
    assert report["physical_endpoint"] == NVIDIA_ENDPOINT
    assert len(report["physical_rejections"]) == 2
    rejected = []
    for attempt in report["physical_rejections"]:
        raw = unpack(attempt["rows"])
        assert digest(raw) == attempt["sha256"]
        observed = parse_timed_rejection(raw, attempt["stream"])
        if "metrics" in attempt:
            assert encode_json(observed) == encode_json(attempt["metrics"])
        else:
            assert "engine_blocks == faults == misses == 1" in attempt["analysis_failure"]
        assert attempt["exit_code"] == 0 and not observed["admitted"]
        rejected.append(observed)

    build = report["host_build"]
    log = AREA / build["log"]
    assert sha(log) == build["sha256"]
    assert build["libraries"] == {name: sha(path) for name, path in cargo_artifacts(log).items()}
    for path, expected in report["host_checkout_source_sha256"].items():
        raw = git_blob(f"{HOST_FIXED}:{path}", HOST)
        assert expected in (digest(raw), digest(raw.replace(b"\n", b"\r\n"))), path

    endpoint_path = PREFIX + "endpoint08.json"
    endpoint = read(endpoint_path)
    recover(endpoint)
    assert endpoint["passed"] and endpoint["other_profiles_unchanged"] and endpoint["temporary_probe_retired"]
    assert check_reads(endpoint["reads"], NVIDIA) == [NVIDIA, NVIDIA]
    profile = asio_profile(AREA / "recovery-host128.exe")
    assert endpoint["initial_lab"] == endpoint["final_lab"] == snapshot(profile)
    assert endpoint["final_lab"][""]["SampleRate"] == [44100, winreg.REG_DWORD]
    assert read_override(profile) == (0, winreg.REG_DWORD)
    assert report["asio_profile"]["before"] == report["asio_profile"]["verified"]
    assert report["asio_profile"]["original"] == [0, winreg.REG_DWORD]

    names.append(endpoint_path)
    staged = subprocess.check_output(["git", "diff", "--cached", "--name-only"], cwd=ROOT, text=True).splitlines()
    assert {OUT, *names} <= set(staged)
    recorded = {}
    for name in sorted(set(staged) - {OUT}):
        assert "recovery_engine128" in name.lower() and (name == UPDATED or name not in known)
        raw = git_blob(":" + name)
        assert raw == (ROOT / name).read_bytes(), name
        recorded[name] = digest(raw)
    return dict(schema="rf-d/recovery-engine-128-mono/v1", passed=True, base_commit=base,
                previous_qa=PRIOR, previous_qa_sha256=sha(ROOT / PRIOR), protected_public_sources=len(known),
                protected_private_inputs=len(private), verified_source_sha256=recorded,
                electrical_reference=node["electrical"], electrical_inputs=report["electrical_inputs"],
                rejected_physical_attempts=rejected,
                whole_voice_rt=False, rack_128_admitted=False)


if __name__ == "__main__":
    result = audit()
    write(ROOT / OUT, result)
    retire_lab()
    result["temporary_area_empty"] = not list(AREA.iterdir())
    assert result["temporary_area_empty"]
    write(ROOT / OUT, result)
    print("MONO128_QA", result["electrical_reference"]["samples"], len(result["rejected_physical_attempts"]))
