"""Audit the calibrated phase timings, SMT control and 128-frame ASIO gate."""

import subprocess
import winreg

import numpy as np

from affine_evidence import encode_json, recover
from check_hybrid_voice import unpack
from check_recovery_cost import digest, read
from check_recovery_engine128 import AREA, HOST, analyze, cargo_artifacts, engine_fixture, retire_lab
from check_recovery_engine128_schedule import (
    ASIO, FIR_O2, OFFLINE, REFERENCE, RESERVE_O2, SELECTED,
    analyze_markers, calibration, placements, select_placement, topology,
)
from check_recovery_host import COLUMNS
from check_recovery_host128 import asio_profile, read_override
from prepare_dual_chain import ROOT, sha, write
from validate_recovery_engine128 import git_blob
from validate_recovery_engine128_fuel import HOST_FIXED

BASE = "5163d9bdce8d6e090a037c1656566491c9c78903"
PREFIX = "evidence/recovery_engine128_"
PRIOR = PREFIX + "hot_tests01.json"
OUT = PREFIX + "schedule_tests01.json"
RUNNER = "tools/check_recovery_engine128.py"
UPDATED = {RUNNER, "tools/check_recovery_engine128_reserve.py"}
RESERVE = PREFIX + "reserve07.json"
FIR = PREFIX + "broadcast_fir07.json"


def verify_rows(item):
    raw = unpack(item["rows"])
    assert digest(raw) == item["sha256"]
    if item["exit_code"] == 0 and "metrics" in item:
        m = analyze_markers(raw, item["stream"], item["blocks"], item["mode"],
                            item["cpu"], item["helper"], analyze)
        assert encode_json(m) == encode_json(item["metrics"])
        return m
    return {}


def contrast(items):
    def cycles(mode):
        rows = [np.frombuffer(unpack(item["rows"]), "<u8").reshape(1200, len(COLUMNS) + 6)
                for item in items if item["mode"] == mode]
        return np.stack([row[:, -3] for row in rows]).astype("f8")

    quiet = cycles("quiet")
    sibling = cycles("sibling")
    remote = cycles("remote")
    return dict(sibling_over_quiet_cycle_ratio=float(np.median(sibling / quiet)),
                remote_over_quiet_cycle_ratio=float(np.median(remote / quiet)),
                sibling_rows_above_quiet=int(np.count_nonzero(sibling > quiet)),
                remote_rows_above_quiet=int(np.count_nonzero(remote > quiet)))


def audit():
    prior = read(PRIOR)
    assert prior["passed"]
    sources = dict(prior["source_sha256"])
    for name, expected in sources.items():
        raw = git_blob(f"{BASE}:{name}") if name in UPDATED else (ROOT / name).read_bytes()
        assert digest(raw) == expected, name
    private = prior["private_input_sha256"]
    assert len(private) == 8769 and all((ROOT / name).is_file() for name in private)
    assert sha(ROOT / prior["new_listening"]["path"]) == prior["new_listening"]["sha256"]

    names = [PREFIX + f"schedule{number:02}.json" for number in (1, 2, 3, 4, 5)]
    first, replayed, report, survey, confirm = [read(name) for name in names]
    reference = read(REFERENCE)
    for item in (first, replayed, report, survey, confirm):
        recover(item)
        assert item["measurement_area_retired"] and item["host_checkout"] == HOST_FIXED
        assert item["reference_sha256"] == sha(ROOT / REFERENCE)
        assert item["topology"] == topology(f"SCHED_TOPOLOGY\t{item['topology']['allowed']}\t{item['topology']['cores']}")
        if item is not survey and item is not confirm:
            wpr = item["wpr"]
            assert len(wpr["runs"]) == 2 and "WPR is not recording" in wpr["final"]
            for attempt in wpr["runs"]:
                assert attempt["exit_code"] & 0xffffffff == 0xc5585011
                assert b"0xc5585011" in (unpack(attempt["stdout"]) + unpack(attempt["stderr"])).lower()
        cal = item["calibration"]
        assert encode_json(calibration(unpack(cal["raw"]))) == encode_json(cal["metrics"])
        assert not cal["metrics"]["cpu_clock_useful"]

    assert not first["passed"] and not replayed["passed"] and report["passed"] and survey["passed"] and confirm["passed"]
    assert "pinned_verified" in first["failure"]
    assert "Offline capture did not confirm" in replayed["failure"]
    for item in (replayed["offline"][0], replayed["unchanged_pin_replay"]):
        m = verify_rows(item)
        assert item["mode"] == "quiet" and m["scheduling"] == 1
        assert not m["pinned_verified"] and len(m["observed_cpus"]) > 1

    top = report["topology"]
    assert [item["mode"] for item in report["offline"]] == list(OFFLINE)
    assert [item["mode"] for item in report["asio"]] == list(ASIO)
    for item in report["offline"]:
        assert item["cpu"] == top["cpu"] and item["helper"] == top.get(item["mode"])
        m = verify_rows(item)
        assert m["pinned_verified"] and m["observed_cpus"] == [top["cpu"]]
    for item in report["asio"]:
        assert item["cpu"] == (top["cpu"] if item["mode"] == "pinned" else None)
        assert item["helper"] is None
        verify_rows(item)
    for mode in ("free", "pinned"):
        gate = report["asio"][0]["metrics"]["gate_passed"] and all(
            item.get("metrics", {}).get("gate_passed", False)
            for item in report["asio"] if item["mode"] == mode
        )
        assert report[mode + "_128_admitted"] == gate
    assert report["rack_128_admitted"] == report["free_128_admitted"]
    assert not report["whole_voice_rt"]
    assert encode_json(report["asio_profile"]) == encode_json(reference["asio_profile"])
    assert encode_json(survey["asio_profile"]) == encode_json(reference["asio_profile"])
    assert report["host_build"] == survey["host_build"] and report["dependencies"] == survey["dependencies"]
    assert report["artifact_sha256"]["engine_probe.rs"] == survey["artifact_sha256"]["engine_probe.rs"]
    assert survey["topology"] == top
    assert [item["cpu"] for item in survey["survey"]] == placements(top)
    for item in survey["survey"]:
        assert item["mode"] == "survey" and item["blocks"] == 1200 and item["helper"] is None
        verify_rows(item)
    chosen = select_placement(survey["survey"])
    assert survey["selected_cpu"] == chosen and chosen is not None
    assert [item["mode"] for item in survey["asio"]] == ["control", "selected", "selected"]
    for item in survey["asio"]:
        verify_rows(item)
        if item["mode"] == "selected":
            assert item["cpu"] == chosen and item["blocks"] == 4800 and item["helper"] is None
    assert survey["selected_128_admitted"] == all(
        item.get("metrics", {}).get("gate_passed", False) for item in survey["asio"]
    )
    assert not survey["rack_128_admitted"] and not survey["whole_voice_rt"]
    assert confirm["placement_inputs"] == {path: sha(ROOT / path) for path in (SELECTED, RESERVE_O2, FIR_O2)}
    assert confirm["selected_cpu"] == chosen and confirm["topology"] == top
    assert confirm["host_build"] == survey["host_build"] and confirm["dependencies"] == survey["dependencies"]
    assert confirm["artifact_sha256"]["engine_probe.rs"] == survey["artifact_sha256"]["engine_probe.rs"]
    assert confirm["wasm_opt_level"] == 2 and confirm["wasm_lto"]
    assert [item["mode"] for item in confirm["asio"]] == ["control", "selected", "selected"]
    for item in confirm["asio"]:
        verify_rows(item)
        if item["mode"] == "selected":
            assert item["cpu"] == chosen and item["blocks"] == 4800 and item["helper"] is None
    assert confirm["selected_128_admitted"] == all(
        item.get("metrics", {}).get("gate_passed", False) for item in confirm["asio"]
    )
    assert not confirm["rack_128_admitted"] and not confirm["whole_voice_rt"]
    assert encode_json(confirm["asio_profile"]) == encode_json(reference["asio_profile"])
    assert read_override(asio_profile(AREA / "recovery-host128.exe")) == (0, winreg.REG_DWORD)

    for name in ("engine_kernel_columns.rs", "engine_guest.rs", "package-dsp/component.wasm",
                 "package-control/component.wasm"):
        assert report["artifact_sha256"][name] == survey["artifact_sha256"][name] == reference["artifact_sha256"][name], name
    kernel = report["artifact_sha256"]["engine_kernel_columns.rs"]
    reserve, fir = read(RESERVE), read(FIR)
    assert reserve["passed"] and fir["passed"] and reserve["wasm_lto"] and fir["wasm_lto"]
    assert kernel == reserve["variants"]["registers"]["kernel_sha256"] == fir["kernel_sha256"]
    assert reserve["variants"]["registers"]["modes"] == reserve["variants"]["scalar"]["modes"]
    assert unpack(fir["fir_check"]).strip() == b"FIR_EXACT,9288,4,48"
    reserve_o2, fir_o2 = read(RESERVE_O2), read(FIR_O2)
    for item in (reserve_o2, fir_o2):
        recover(item)
        assert item["passed"] and item["measurement_area_retired"] and item["wasm_opt_level"] == 2
    assert reserve_o2["variants"]["registers"]["modes"] == reserve["variants"]["registers"]["modes"]
    assert kernel == reserve_o2["variants"]["registers"]["kernel_sha256"] == fir_o2["kernel_sha256"]
    assert kernel == confirm["artifact_sha256"]["engine_kernel_columns.rs"]
    assert unpack(fir_o2["fir_check"]) == unpack(fir["fir_check"])
    assert confirm["artifact_sha256"]["package-dsp/component.wasm"] != reference["artifact_sha256"]["package-dsp/component.wasm"]
    fixture = report["fixtures"]
    raw = unpack(fixture["rows"])
    assert digest(raw) == fixture["sha256"] == reference["fixtures"]["sha256"]
    assert encode_json(engine_fixture(raw)) == encode_json(fixture["metrics"])
    assert fixture["sha256"] == survey["fixtures"]["sha256"] == digest(unpack(survey["fixtures"]["rows"]))
    assert fixture["sha256"] == confirm["fixtures"]["sha256"] == digest(unpack(confirm["fixtures"]["rows"]))
    for path, expected in report["host_checkout_source_sha256"].items():
        raw = git_blob(f"{HOST_FIXED}:{path}", HOST)
        assert expected in (digest(raw), digest(raw.replace(b"\n", b"\r\n"))), path
    build = report["host_build"]
    log = AREA / build["log"]
    assert sha(log) == build["sha256"]
    assert build["libraries"] == {name: sha(path) for name, path in cargo_artifacts(log).items()}

    staged = subprocess.check_output(["git", "diff", "--cached", "--name-only"], cwd=ROOT, text=True).splitlines()
    names += [RESERVE_O2, FIR_O2]
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
        schema="rf-d/recovery-engine-effective-128-schedule/v1", passed=True, base_commit=BASE,
        source_sha256=sources, previous_qa=PRIOR, previous_qa_sha256=sha(ROOT / PRIOR),
        protected_public_sources=len(prior["source_sha256"]), protected_private_inputs=len(private),
        smt_contrast=contrast(report["offline"]), rack_128_admitted=report["free_128_admitted"],
        pinned_lab_128_admitted=report["pinned_128_admitted"], whole_voice_rt=False, real_time=False,
        selected_cpu=chosen, selected_lab_128_admitted=survey["selected_128_admitted"],
        selected_o2_lab_128_admitted=confirm["selected_128_admitted"],
        wpr_available=False, per_callback_cpu_clock_admitted=False,
        retained_receipt_bytes=retained,
        recovery_engine128_schedule_reports={name: sha(ROOT / name) for name in names},
    )
    return result


if __name__ == "__main__":
    result = audit()
    write(ROOT / OUT, result)
    retire_lab()
    result["temporary_area_empty"] = not list(AREA.iterdir())
    assert result["temporary_area_empty"]
    write(ROOT / OUT, result)
    print("SCHEDULE128_QA", result["protected_public_sources"], result["protected_private_inputs"],
          result["smt_contrast"], result["rack_128_admitted"], result["pinned_lab_128_admitted"],
          result["selected_lab_128_admitted"], result["selected_o2_lab_128_admitted"])
