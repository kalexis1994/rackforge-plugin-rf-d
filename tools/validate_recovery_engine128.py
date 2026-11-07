"""Audit the frozen RF-D portable-engine measurements and failed replays."""

import subprocess
import winreg
from pathlib import Path

import numpy as np

from affine_evidence import encode_json, recover
from check_hybrid_voice import unpack
from check_recovery_cost import digest, read
from check_recovery_engine128 import AREA, ENGINE_PROBE, HOST, PLAN, QA, analyze, engine_fixture
from check_recovery_host import COLUMNS
from check_recovery_host128 import asio_profile, read_override
from prepare_dual_chain import ROOT, sha, write

BASE = "e6e6a9085a9b3174c1294e685bd2c513f63f97b0"
PREFIX = "evidence/recovery_engine128_"
OUT = PREFIX + "tests01.json"
ATTR = ".gitattributes"
ATTR_APPEND = b"\n/tools/*recovery_engine128* -text\n/docs/RECOVERY_ENGINE128*.md -text\n/evidence/recovery_engine128* -text\n"
RUNNER = "tools/check_recovery_engine128.py"


def git_blob(ref, root=ROOT):
    return subprocess.check_output(["git", "show", ref], cwd=root)


def callback_split(raw, blocks):
    rows = np.frombuffer(raw, "<u8").reshape(blocks, len(COLUMNS) + 2)
    wall = rows[:, COLUMNS.index("wall_ns")]
    render = rows[:, COLUMNS.index("dsp_ns")]
    assert np.all(render <= wall)
    outside = wall - render
    worst = np.argmax(wall)
    return dict(outside_median_ns=float(np.median(outside)),
                outside_p99_ns=float(np.quantile(outside, 0.99)),
                outside_max_ns=int(np.max(outside)),
                worst_wall_ns=int(wall[worst]), worst_render_ns=int(render[worst]))


def audit():
    prior = read(QA)
    assert prior["passed"] and not list(AREA.iterdir())
    sources = dict(prior["source_sha256"])
    for name, expected in sources.items():
        if name != ATTR:
            assert sha(ROOT / name) == expected, name
    baseline_attrs = git_blob(f"{BASE}:{ATTR}")
    assert digest(baseline_attrs) == sources[ATTR]
    assert (ROOT / ATTR).read_bytes() == baseline_attrs + ATTR_APPEND
    private = prior["private_input_sha256"]
    assert len(private) == 8769 and all((ROOT / name).is_file() for name in private)
    assert sha(ROOT / prior["new_listening"]["path"]) == prior["new_listening"]["sha256"]

    labels = ["native01", "native02", "alloc01", "timeout01"]
    names = {label: f"{PREFIX}{label}.json" for label in labels}
    failed, measured, trace, timeout = [read(names[label]) for label in labels]
    for report in (failed, measured, trace):
        images = recover(report)
        assert report["previous_qa_sha256"] == sha(ROOT / QA)
        for name, raw in images.items():
            if report is not trace and name in (RUNNER, ENGINE_PROBE):
                assert b"engine_alloc_trace" not in raw
            elif report is not failed:
                assert raw == (ROOT / name).read_bytes(), name
        for name, expected in report["host_checkout_source_sha256"].items():
            raw = git_blob(f"{report['host_checkout']}:{name}", HOST)
            assert expected in (digest(raw), digest(raw.replace(b"\n", b"\r\n"))), name
        assert all(sha(Path(p)) == expected for p, expected in report["dependencies"].items())
    assert failed["passed"] is False and "engine-fixtures" in failed["failure"]
    assert timeout["report"] == names["native01"] and timeout["exit_code"] == 1
    assert timeout["original_timeout_s"] == timeout["unchanged_replay_timeout_s"] == 95
    assert timeout["launcher_output"].count("timed out after 95 seconds") == 2
    assert measured["passed"] and measured["temporary_area_empty"]
    assert measured["rack_128_admitted"] is measured["whole_voice_rt"] is False
    assert trace["passed"] and trace["temporary_area_empty"] and "asio_profile" not in trace
    stack = trace["allocation_trace"]
    assert "ENGINE_ALLOC 24\n" in stack.replace("\r\n", "\n")
    assert "StoreOpaque>::get_fuel" in stack and "PortableInstance>::process_interleaved_with_midi2" in stack
    control_wasm = "package-control/component.wasm"
    assert trace["artifact_sha256"][control_wasm] == measured["artifact_sha256"][control_wasm]

    fixture = measured["fixtures"]
    raw = unpack(fixture["rows"])
    assert digest(raw) == fixture["sha256"]
    assert encode_json(engine_fixture(raw)) == encode_json(fixture["metrics"])
    assert fixture["metrics"]["native_instance_bit_exact"] and fixture["metrics"]["rack_instance_bit_exact"]
    assert sum(name.endswith(".wasm") for name in measured["cached_artifacts"]) == 2
    profile = measured["asio_profile"]
    assert profile["before"] == profile["verified"]
    assert profile["before"].split("\t")[2:] == ["44100", "2", "8", "64", "2048", "512", "8", "0"]
    assert tuple(profile["original"]) == (0, winreg.REG_DWORD)
    assert tuple(profile["during"]) == (128, winreg.REG_DWORD)
    assert read_override(asio_profile(AREA / "recovery-host128.exe")) == tuple(profile["original"])

    banks = measured["banks"]
    assert [(bank["mode"], bank["blocks"]) for bank in banks] == PLAN
    splits = []
    for bank in banks:
        mode, blocks, runs = bank["mode"], bank["blocks"], bank["runs"]
        assert len(runs) == (1 if mode == "native" else 2)
        for index, run in enumerate(runs):
            raw = unpack(run["rows"])
            assert run["exit_code"] == 0 and digest(raw) == run["sha256"]
            metrics = analyze(raw, run["stream"], blocks, mode)
            assert encode_json(metrics) == encode_json(run["metrics"])
            assert metrics["frames_128_confirmed"] and metrics["notices"] == metrics["slot_faults"] == 0
            assert metrics["gate_passed"] == (mode == "native")
            expected_allocs = 0 if mode == "native" else blocks
            assert metrics["host_allocations"] == metrics["allocating_blocks"] == expected_allocs
            assert metrics["first_host_allocations"] == int(expected_allocs > 0)
            assert metrics["margin_exceeded"] == (blocks if mode in ("instance", "rack") else 0)
            splits.append(dict(mode=mode, blocks=blocks, replay=bool(index), **callback_split(raw, blocks)))
    assert [run["metrics"]["deadline_misses"] for run in banks[-1]["runs"]] == [32, 8]
    assert [run["metrics"]["rack_deadline_misses"] for run in banks[-1]["runs"]] == [28, 8]

    staged = subprocess.check_output(["git", "diff", "--cached", "--name-only"], cwd=ROOT, text=True).splitlines()
    assert {OUT, ATTR, *names.values()} <= set(staged)
    for name in set(staged) - {OUT}:
        assert name == ATTR or ("recovery_engine128" in name.lower() and name not in sources), name
        raw = git_blob(":" + name)
        assert raw == (ROOT / name).read_bytes(), name
        sources[name] = digest(raw)
    sources[QA] = sha(ROOT / QA)
    retained = sum((ROOT / name).stat().st_size for name in names.values())
    assert retained <= 4 * 1024**2
    result = {key: value for key, value in prior.items() if not key.startswith("new_") or key == "new_listening"}
    result.update(
        schema="rf-d/recovery-engine-effective-128/v1", passed=True, base_commit=BASE,
        source_sha256=sources, previous_qa=QA, previous_qa_sha256=sha(ROOT / QA),
        protected_public_sources=len(prior["source_sha256"]), protected_private_inputs=len(private),
        rackforge_plugin_engine_measured=True, rack_128_admitted=False, asio_128_confirmed=True,
        asio_preference_restored=True, allocation_stack_confirmed=True, callback_splits=splits,
        whole_voice_rt=False, real_time=False, inherited_tests_reexecuted=False,
        new_unit_tests_executed=0, new_audio=False, retained_receipt_bytes=retained,
        recovery_engine128_reports={name: sha(ROOT / name) for name in names.values()},
    )
    return result


if __name__ == "__main__":
    result = audit()
    write(ROOT / OUT, result)
    print("ENGINE128_QA", len(result["source_sha256"]), result["protected_private_inputs"],
          result["retained_receipt_bytes"], result["asio_128_confirmed"], result["rack_128_admitted"])
