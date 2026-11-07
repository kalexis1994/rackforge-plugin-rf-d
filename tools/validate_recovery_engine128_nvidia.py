"""Verify NVIDIA runs and paired ordinals against the frozen O3 package."""

import subprocess
import winreg

from affine_evidence import encode_json, recover
from check_hybrid_voice import unpack
from check_recovery_cost import digest, read
from check_recovery_engine128 import AREA, HOST, analyze, cargo_artifacts, retire_lab
from check_recovery_engine128_endpoint import NVIDIA, snapshot
from check_recovery_engine128_nvidia import BLOCKS, CPU, HISTORY, compare
from check_recovery_engine128_schedule import analyze_markers
from check_recovery_engine128_smt import NVIDIA_ENDPOINT, admitted, analyze_smt, valid_warmup
from check_recovery_host128 import asio_profile, read_override
from prepare_dual_chain import ROOT, sha, write
from validate_recovery_engine128 import git_blob
from validate_recovery_engine128_fuel import HOST_FIXED
from validate_recovery_engine128_physical import check_package, check_reads

PREFIX = "evidence/recovery_engine128_"
PRIOR = PREFIX + "physical_tests01.json"
OUT = PREFIX + "nvidia_tests01.json"
UPDATED = {
    "tools/check_recovery_engine128.py",
    "tools/check_recovery_engine128_smt.py",
    "tools/recovery_engine128_smt.rs",
}


def check_build_rejection(report, diagnostic):
    assert not report["passed"] and report["measurement_area_retired"]
    failure, replay = (report[key] for key in ("failed_output", "unchanged_failure_replay"))
    assert failure["exit_code"] == replay["exit_code"] != 0
    for item in (failure, replay):
        assert diagnostic in unpack(item["stderr"])


def check_confirmation(report):
    assert report["passed"] and report["measurement_area_retired"]
    assert report["host_checkout"] == HOST_FIXED
    assert report["event_campaign"] and report["lean_campaign"] and report["qualification_campaign"]
    assert report["expected_endpoint"] == NVIDIA_ENDPOINT and report["endpoint_available"]
    assert report["endpoint_checks"][-1]["endpoint"] == NVIDIA_ENDPOINT
    assert not report["rack_128_admitted"] and not report["whole_voice_rt"]
    check_package(report)
    profile = report["asio_profile"]
    assert profile["before"] == profile["verified"]
    assert profile["before"].split("\t")[:6] == ["ASIO", "ASIO4ALL v2", "44100", "2", "2", "64"]
    assert profile["original"] == [0, winreg.REG_DWORD]
    fixed_cpu = report.get("event_cpu")
    confirmation, = report["confirmations"]
    control = report["control"]
    runs = confirmation["runs"]
    assert [item["blocks"] for item in (control, *runs)] == [1200, BLOCKS, BLOCKS]
    warmup = report.get("warmup")
    if report.get("warmup_campaign", False):
        assert warmup is not None and warmup["blocks"] == BLOCKS
        assert warmup["label"] == "warmup-quiet-event"
    else:
        assert warmup is None
    summary = []
    items = (control, *runs) if warmup is None else (control, warmup, *runs)
    override = 128 if any("metrics" in item for item in items) else 0
    assert profile["during"] == [override, winreg.REG_DWORD]
    for item in items:
        raw = unpack(item["rows"])
        assert digest(raw) == item["sha256"]
        assert item["policy"] == confirmation["policy"] == "quiet-event" and item["seed"] is None
        if item["exit_code"] != 0:
            assert "metrics" not in item and not raw
            assert NVIDIA_ENDPOINT in item["stream"] and "SMT_QUALIFY_REJECT" in item["stream"]
            summary.append(dict(rejected_preflight=True))
            continue
        metrics = analyze_smt(raw, item["stream"], item["blocks"], "quiet-event", None, report["topology"],
                              analyze, silent=item is control, endpoint=NVIDIA_ENDPOINT, event_cpu=fixed_cpu,
                              event_idle=report.get("event_idle"))
        assert encode_json(metrics) == encode_json(item["metrics"])
        assert metrics["frames_128_confirmed"] and metrics["physical_endpoint_verified"]
        assert metrics["placement_verified"] and metrics["host_allocations"] == metrics["slot_faults"] == 0
        summary.append({key: metrics[key] for key in (
            "initial_cpu", "wall_ns", "margin_exceeded", "deadline_misses", "notices",
            "gap_over_1_5_periods", "first_wall_with_setup_ns", "gate_passed",
        )})
    accepted = (warmup is None or valid_warmup(warmup)) and admitted(control, runs)
    assert report["admitted_policy"] == ("quiet-event" if accepted else None)
    offline = report["offline_comparison"]
    assert offline["exit_code"] == 0 and offline["cpu"] == CPU
    raw = unpack(offline["rows"])
    metrics = analyze_markers(raw, offline["stream"], BLOCKS, "quiet", CPU, None, analyze)
    assert encode_json(metrics) == encode_json(offline["metrics"])
    assert metrics["pinned_verified"] and not metrics["frames_128_confirmed"]
    history = [read(name) for name in HISTORY]
    assert report["ordinal_inputs"] == {name: sha(ROOT / name) for name in HISTORY}
    banks = [item for campaign in (*history, report) for item in campaign["confirmations"][0]["runs"]
             if item.get("metrics", {}).get("physical_endpoint_verified")]
    pairs = compare(banks, offline)
    assert encode_json(pairs) == encode_json(offline["ordinal_comparison"])
    return dict(fixed_cpu=fixed_cpu, fixed_idle=report.get("event_idle"), accepted=accepted,
                warmup_campaign=warmup is not None,
                banks=summary, ordinal_comparison=pairs,
                offline_render_ns=metrics["render_window_ns"])


def audit():
    previous = read(PRIOR)
    assert previous["passed"] and previous["electrical_reserves_preserved"]
    base = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    assert base.startswith("105ca4b")
    for name, expected in previous["source_sha256"].items():
        raw = git_blob(f"{base}:{name}") if name in UPDATED else (ROOT / name).read_bytes()
        assert digest(raw) == expected, name
    private = previous["private_input_sha256"]
    assert len(private) == 8769 and all((ROOT / name).is_file() for name in private)
    listening = previous["new_listening"]
    assert sha(ROOT / listening["path"]) == listening["sha256"]

    names = sorted(path.relative_to(ROOT).as_posix()
                   for path in (ROOT / "evidence").glob("recovery_engine128_smt[0-9][0-9].json")
                   if int(path.stem[-2:]) >= 11)
    failed_binding, failed_handle, *campaigns = [read(name) for name in names]
    assert len(campaigns) >= 2
    for name in names:
        recover(read(name))
    check_build_rejection(failed_binding, b"error[E0255]")
    check_build_rejection(failed_handle, b"expected `*mut c_void`, found `isize`")
    assert [report.get("event_cpu") for report in campaigns] == [None, CPU, CPU, CPU, CPU, 9]
    summary = {name: check_confirmation(report) for name, report in zip(names[2:], campaigns)}
    assert [name for name, item in summary.items() if item["accepted"]] == [PREFIX + "smt18.json"]
    build = campaigns[0]["host_build"]
    assert all(report["host_build"] == build and report["dependencies"] == campaigns[0]["dependencies"]
               for report in campaigns)
    log = AREA / build["log"]
    assert sha(log) == build["sha256"]
    assert build["libraries"] == {name: sha(path) for name, path in cargo_artifacts(log).items()}
    for path, expected in campaigns[0]["host_checkout_source_sha256"].items():
        raw = git_blob(f"{HOST_FIXED}:{path}", HOST)
        assert expected in (digest(raw), digest(raw.replace(b"\n", b"\r\n"))), path

    profile = asio_profile(AREA / "recovery-host128.exe")
    for number in (6, 7):
        endpoint_path = PREFIX + f"endpoint{number:02}.json"
        endpoint = read(endpoint_path)
        recover(endpoint)
        assert endpoint["passed"] and endpoint["other_profiles_unchanged"] and endpoint["temporary_probe_retired"]
        assert check_reads(endpoint["reads"], NVIDIA) == [NVIDIA, NVIDIA]
        assert endpoint["initial_lab"] == endpoint["final_lab"] == snapshot(profile)
        assert endpoint["final_lab"][""]["SampleRate"] == [44100, winreg.REG_DWORD]
        names.append(endpoint_path)
    assert read_override(profile) == (0, winreg.REG_DWORD)

    staged = subprocess.check_output(["git", "diff", "--cached", "--name-only"], cwd=ROOT, text=True).splitlines()
    assert {OUT, *names} <= set(staged)
    recorded = {}
    for name in sorted(set(staged) - {OUT}):
        assert "recovery_engine128" in name.lower()
        assert name in UPDATED or name not in previous["source_sha256"]
        raw = git_blob(":" + name)
        assert raw == (ROOT / name).read_bytes(), name
        recorded[name] = digest(raw)
    retained_bytes = sum((ROOT / name).stat().st_size for name in names)
    assert retained_bytes <= 4 * 1024**2
    return dict(schema="rf-d/recovery-engine-128-nvidia/v1", passed=True, base_commit=base,
                previous_qa=PRIOR, previous_qa_sha256=sha(ROOT / PRIOR),
                verified_source_sha256=recorded, protected_public_sources=len(previous["source_sha256"]),
                protected_private_inputs=len(private), electrical_reserves_preserved=True,
                physical_confirmations=summary, retained_receipt_bytes=retained_bytes,
                rack_128_admitted=False, whole_voice_rt=False)


if __name__ == "__main__":
    result = audit()
    write(ROOT / OUT, result)
    retire_lab()
    result["temporary_area_empty"] = not list(AREA.iterdir())
    assert result["temporary_area_empty"]
    write(ROOT / OUT, result)
    print("NVIDIA128_QA", [(name, item["accepted"]) for name, item in result["physical_confirmations"].items()])
