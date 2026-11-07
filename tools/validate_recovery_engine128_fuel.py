"""Recompute the 128-frame gates after the portable runtime fuel fix."""

import subprocess
import winreg

from affine_evidence import encode_json, recover
from check_hybrid_voice import unpack
from check_recovery_cost import digest, read
from check_recovery_engine128 import AREA, HOST, PLAN, analyze, engine_fixture
from check_recovery_host128 import asio_profile, read_override
from prepare_dual_chain import ROOT, sha, write
from validate_recovery_engine128 import callback_split, git_blob

PREVIOUS = "evidence/recovery_engine128_tests01.json"
PREFIX = "evidence/recovery_engine128_"
OUT = PREFIX + "fuel_tests01.json"
BUILD = PREFIX + "fuel_build01.json"
RUNNER = "tools/check_recovery_engine128.py"
BASE = "819daeedcfc62f06a6b371c182be23130cf2c383"
HOST_BASE = "7a14c68aa208290587d985d606b0dbc17600ee07"
HOST_FIXED = "37e5f8037b9efd2e525786f9a68f9f4e2d02e0f1"
RUNTIME = "crates/rackforge-plugin-runtime/src/native.rs"


def audit():
    prior = read(PREVIOUS)
    assert prior["passed"] and not list(AREA.iterdir())
    sources = dict(prior["source_sha256"])
    for name, expected in sources.items():
        raw = git_blob(f"{BASE}:{name}") if name == RUNNER else (ROOT / name).read_bytes()
        assert digest(raw) == expected, name
    private = prior["private_input_sha256"]
    assert len(private) == 8769 and all((ROOT / name).is_file() for name in private)
    assert sha(ROOT / prior["new_listening"]["path"]) == prior["new_listening"]["sha256"]
    assert subprocess.check_output(
        ["git", "diff", "--name-only", HOST_BASE, HOST_FIXED], cwd=HOST, text=True,
    ).splitlines() == [RUNTIME]

    old = read(PREFIX + "native02.json")
    build = read(BUILD)
    assert build["original_failure"]["toolchain"] == "x86_64-pc-windows-gnu"
    assert build["original_failure"]["exit_code"] == 1 and build["unchanged_replay"]["exit_code"] == 101
    for key in ("original_failure", "unchanged_replay"):
        assert "dlltool.exe" in build[key]["error"]
    assert build["runtime_tests"]["exit_code"] == 0
    assert "fuel_trap_is_measured_and_control_calls_remain_recoverable ... ok" in build["runtime_tests"]["output"]
    assert "an_unmetered_runaway_is_still_cut_off_by_the_epoch ... ok" in build["runtime_tests"]["output"]

    reports = {}
    summary = {}
    cases = {}
    for path in sorted((ROOT / "evidence").glob("recovery_engine128_native*.json")):
        name = path.relative_to(ROOT).as_posix()
        if name in sources:
            continue
        report = read(name)
        recover(report)
        reports[name] = sha(path)
        assert report["measurement_area_retired"]
        if not report["passed"]:
            assert "failure" in report and "unchanged_failure_replay" in report
            continue
        host = report["host_checkout"]
        config = (host, report["wasm_opt_level"], report.get("column_simd", False))
        assert config not in cases
        cases[config] = report
        assert report["host_build"] == build["successful_builds"][host]
        assert report["whole_voice_rt"] is False
        for source, expected in report["host_checkout_source_sha256"].items():
            raw = git_blob(f"{host}:{source}", HOST)
            assert expected in (digest(raw), digest(raw.replace(b"\n", b"\r\n"))), source
        fixture = report["fixtures"]
        raw = unpack(fixture["rows"])
        assert digest(raw) == fixture["sha256"] == old["fixtures"]["sha256"]
        assert encode_json(engine_fixture(raw)) == encode_json(fixture["metrics"])
        assert encode_json(report["asio_profile"]) == encode_json(old["asio_profile"])
        assert [(bank["mode"], bank["blocks"]) for bank in report["banks"]] == PLAN
        all_passed = True
        long_passes = []
        for bank in report["banks"]:
            mode, blocks, runs = bank["mode"], bank["blocks"], bank["runs"]
            assert len(runs) == (1 if runs[0]["metrics"]["gate_passed"] else 2)
            for run in runs:
                raw = unpack(run["rows"])
                assert run["exit_code"] == 0 and digest(raw) == run["sha256"]
                m = analyze(raw, run["stream"], blocks, mode)
                assert encode_json(m) == encode_json(run["metrics"])
                assert m["frames_128_confirmed"] and m["slot_faults"] == 0
                allocated = blocks if host == HOST_BASE and mode != "native" else 0
                assert m["host_allocations"] == m["allocating_blocks"] == allocated
                assert m["first_host_allocations"] == int(allocated > 0)
                if blocks == 4800:
                    long_passes.append(dict(metrics=m, split=callback_split(raw, blocks)))
            all_passed &= runs[0]["metrics"]["gate_passed"]
        assert all_passed == report["rack_128_admitted"]
        summary[name] = long_passes

    base = cases[HOST_BASE, 2, False]
    fixed = cases[HOST_FIXED, 2, False]
    candidate = cases[HOST_FIXED, 3, False]
    columns = cases[HOST_FIXED, 3, True]
    assert not base["rack_128_admitted"] and not fixed["rack_128_admitted"]
    for path in ("engine_guest.rs", "engine_probe.rs", "package-dsp/component.wasm", "package-control/component.wasm"):
        assert fixed["artifact_sha256"][path] == base["artifact_sha256"][path], path
    probe = "engine_probe.rs"
    assert fixed["artifact_sha256"][probe] == candidate["artifact_sha256"][probe] == columns["artifact_sha256"][probe]
    for report in (candidate, columns):
        assert report["build"][0]["command"] == fixed["build"][0]["command"]
        assert report["build"][-1]["command"] == fixed["build"][-1]["command"]
        assert report["dependencies"] == fixed["dependencies"]
    assert fixed["host_build"]["libraries"]["wasmtime"] == base["host_build"]["libraries"]["wasmtime"]
    assert fixed["host_build"]["libraries"]["rackforge_plugin_runtime"] != base["host_build"]["libraries"]["rackforge_plugin_runtime"]
    assert read_override(asio_profile(AREA / "recovery-host128.exe")) == (0, winreg.REG_DWORD)

    staged = subprocess.check_output(["git", "diff", "--cached", "--name-only"], cwd=ROOT, text=True).splitlines()
    assert {OUT, BUILD, RUNNER, *reports} <= set(staged)
    for name in set(staged) - {OUT}:
        assert "recovery_engine128" in name.lower() and (name == RUNNER or name not in sources)
        raw = git_blob(":" + name)
        assert raw == (ROOT / name).read_bytes(), name
        sources[name] = digest(raw)
    sources[PREVIOUS] = sha(ROOT / PREVIOUS)
    retained = sum((ROOT / name).stat().st_size for name in [BUILD, *reports])
    assert retained <= 4 * 1024**2
    result = {key: value for key, value in prior.items() if not key.startswith("new_") or key == "new_listening"}
    result.update(
        schema="rf-d/recovery-engine-effective-128-fuel/v1", passed=True, base_commit=BASE,
        source_sha256=sources, previous_qa=PREVIOUS, previous_qa_sha256=sha(ROOT / PREVIOUS),
        protected_public_sources=len(prior["source_sha256"]), protected_private_inputs=len(private),
        host_fix_commit=HOST_FIXED, rack_128_admitted=fixed["rack_128_admitted"],
        column_simd_rack_128_admitted=columns["rack_128_admitted"], whole_voice_rt=False,
        real_time=False, first_callback_allocation_removed=True, long_confirmation=summary,
        retained_receipt_bytes=retained, recovery_engine128_fuel_reports=reports,
    )
    return result


if __name__ == "__main__":
    result = audit()
    write(ROOT / OUT, result)
    print("FUEL128_QA", result["protected_public_sources"], result["protected_private_inputs"],
          result["retained_receipt_bytes"], result["column_simd_rack_128_admitted"])
