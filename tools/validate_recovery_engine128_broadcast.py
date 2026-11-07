"""Audit reserved electrical cases and matched ASIO timings for broadcast SIMD."""

import subprocess
import winreg

import numpy as np

from affine_evidence import encode_json, recover
from check_hybrid_voice import unpack
from check_recovery_cost import check_laws, decode, digest, read
from check_recovery_cost_exp import endpoints
from check_recovery_engine128 import (
    AREA, EXP_KERNEL, HOST, PLAN, analyze, cargo_artifacts, column_kernel, engine_fixture, retire_lab,
    sources_for_build,
)
from check_recovery_engine128_reserve import MODES, PHYSICAL, PROTOCOL, REF, VARIANTS, fir_source, probe_source
from check_recovery_host import COLUMNS
from check_recovery_host128 import asio_profile, read_override
from prepare_dual_chain import ROOT, sha, write
from validate_recovery_engine128 import callback_split, git_blob
from validate_recovery_engine128_fuel import HOST_FIXED

BASE = "5f81e5dba7c7f5e9ca7057f20fd5b205d56ca740"
RUNNER = "tools/check_recovery_engine128.py"
PREFIX = "evidence/recovery_engine128_"
PREVIOUS = PREFIX + "fuel_tests01.json"
OUT = PREFIX + "broadcast_tests01.json"


def reserve_audit(receipt):
    recover(receipt)
    assert receipt["passed"] and receipt["measurement_area_retired"]
    assert receipt["reference_sha256"] == sha(ROOT / REF)
    assert receipt["physical_sha256"] == sha(ROOT / PHYSICAL)
    reference = read(REF)
    assert reference["physical_admitted"]
    variants = receipt["variants"]
    assert set(variants) == set(VARIANTS)
    scalar = variants["scalar"]["modes"]
    assert set(scalar) == set(MODES)
    tables = (AREA / "reserve-vectors.bin", AREA / "reserve-stress.bin")
    for variant, item in variants.items():
        assert encode_json(item["modes"]) == encode_json(scalar)
        kernel = ROOT / EXP_KERNEL if variant == "scalar" else AREA / "reserve-kernel.rs"
        expected = sha(kernel) if variant == "scalar" else digest(column_kernel(variant == "broadcast"))
        assert item["kernel_sha256"] == expected
        assert item["probe_sha256"] == digest(probe_source(kernel, tables))
    results = receipt["results"]
    for mode in ("vectors", "stress"):
        got = results[mode]
        raw = decode(reference, mode)
        table = np.frombuffer(raw, "<f8").reshape(3, 1537, 93)[0, :, 2].tobytes()
        assert digest(table) == receipt["input_sha256"][mode]
        assert got["native_bit_exact"] and decode({mode: got["saved"]}, mode) == raw
        assert got["full_state_sha256"] == scalar[mode]["sha256"]
        assert scalar[mode]["bytes"] == 3 * 1537 * 137 * 8
        assert got["max_residual"] <= 2e-13 and 1 <= got["max_iterations"] <= 12
    for name, check in (("stages", endpoints), ("laws", check_laws)):
        item = results[name]
        raw = unpack(item["raw"])
        assert digest(raw) == scalar[name]["sha256"]
        assert encode_json(check(raw)) == encode_json(item["comparisons"])
    assert len(results["stages"]["comparisons"]) == 48
    assert len(results["physical"]) == 3
    for case, previous in zip(results["physical"], reference["physical"]):
        assert case["admitted"] and previous["admitted"] and case["index"] == previous["index"]
        assert case["physical_sparse_nodes"]["all_nodes_error_v"] <= 1e-6
        assert case["physical_dense_ports"]["j7_rms_relative"] <= 0.001
        assert case["temporal_same_hybrid_dense_nodes"]["all_nodes_error_v"] <= 1e-6
    return variants


def tail(raw, blocks):
    rows = np.frombuffer(raw, "<u8").reshape(blocks, len(COLUMNS) + 2)
    wall = rows[:, COLUMNS.index("wall_ns")]
    cycles = rows[:, COLUMNS.index("cycles")]
    margin = wall > 128e9 / 48000 / 2
    peers = cycles[~margin & (cycles > 0)]
    p99 = float(np.quantile(peers, 0.99)) if len(peers) >= 20 else None
    migrated = rows[:, COLUMNS.index("cpu_before")] != rows[:, COLUMNS.index("cpu_after")]
    return dict(
        **callback_split(raw, blocks),
        margin_overruns_with_cpu_change=int(np.count_nonzero(margin & migrated)),
        margin_overruns_above_peer_cycles_p99=int(np.count_nonzero(margin & (cycles > p99))) if p99 else None,
        peer_cycles_p99=p99,
    )


def audit():
    prior = read(PREVIOUS)
    assert prior["passed"]
    source_hashes = dict(prior["source_sha256"])
    for name, expected in source_hashes.items():
        raw = git_blob(f"{BASE}:{name}") if name == RUNNER else (ROOT / name).read_bytes()
        assert digest(raw) == expected, name
    private = prior["private_input_sha256"]
    assert len(private) == 8769 and all((ROOT / name).is_file() for name in private)
    assert sha(ROOT / prior["new_listening"]["path"]) == prior["new_listening"]["sha256"]

    reserve_name = PREFIX + "reserve01.json"
    variants = reserve_audit(read(reserve_name))
    fir_name = PREFIX + "broadcast_fir01.json"
    fir = read(fir_name)
    recover(fir)
    assert fir["passed"] and fir["measurement_area_retired"]
    assert fir["kernel_sha256"] == variants["broadcast"]["kernel_sha256"]
    assert fir["probe_sha256"] == digest(fir_source(AREA / "reserve-kernel.rs"))
    assert unpack(fir["fir_check"]).strip() == b"FIR_EXACT,9288,4,48"
    old = read(PREFIX + "native05.json")
    names = [PREFIX + f"native{n:02}.json" for n in (7, 8, 9)]
    reports = [read(name) for name in names]
    summary = {}
    configurations = ((False, False), (True, False), (True, True))
    early_sources = reports[0]["source_sha256"]
    for (broadcast, split_fir), report, name in zip(configurations, reports, names):
        for source, raw in recover(report).items():
            if not split_fir and source in (RUNNER, PROTOCOL):
                assert digest(raw) == early_sources[source], source
            else:
                assert raw == (ROOT / source).read_bytes(), source
        assert report["passed"] and report["measurement_area_retired"] and not report["whole_voice_rt"]
        assert report["host_checkout"] == HOST_FIXED and report["wasm_opt_level"] == 3
        assert report["column_simd"] and report["broadcast_simd"] == broadcast
        assert report.get("split_fir", False) == split_fir
        assert report["host_build"] == reports[0]["host_build"]
        assert report["dependencies"] == reports[0]["dependencies"]
        for source, expected in report["host_checkout_source_sha256"].items():
            raw = git_blob(f"{HOST_FIXED}:{source}", HOST)
            assert expected in (digest(raw), digest(raw.replace(b"\n", b"\r\n"))), source
        kernel_hash = variants["broadcast" if broadcast else "pairs"]["kernel_sha256"]
        assert report["artifact_sha256"]["engine_kernel_columns.rs"] == kernel_hash
        guest, probe = sources_for_build(AREA / "engine_kernel_columns.rs", split_fir)
        assert report["artifact_sha256"]["engine_guest.rs"] == digest(guest)
        assert report["artifact_sha256"]["engine_probe.rs"] == digest(probe)
        fixture = report["fixtures"]
        raw = unpack(fixture["rows"])
        assert digest(raw) == fixture["sha256"] == old["fixtures"]["sha256"]
        assert encode_json(engine_fixture(raw)) == encode_json(fixture["metrics"])
        assert encode_json(report["asio_profile"]) == encode_json(old["asio_profile"])
        assert [(bank["mode"], bank["blocks"]) for bank in report["banks"]] == PLAN
        long_passes = []
        for bank in report["banks"]:
            mode, blocks, runs = bank["mode"], bank["blocks"], bank["runs"]
            assert len(runs) == (1 if runs[0]["metrics"]["gate_passed"] else 2)
            for run in runs:
                raw = unpack(run["rows"])
                assert run["exit_code"] == 0 and digest(raw) == run["sha256"]
                m = analyze(raw, run["stream"], blocks, mode)
                assert encode_json(m) == encode_json(run["metrics"])
                assert m["frames_128_confirmed"]
                assert m["host_allocations"] == m["slot_faults"] == m["notices"] == 0
                if blocks == 4800:
                    long_passes.append(dict(metrics=m, tail=tail(raw, blocks)))
        assert report["rack_128_admitted"] == all(b["runs"][0]["metrics"]["gate_passed"] for b in report["banks"])
        summary[name] = long_passes
    assert reports[0]["artifact_sha256"]["package-dsp/component.wasm"] == old["artifact_sha256"]["package-dsp/component.wasm"]
    for report in reports[1:]:
        for position in (0, -1):
            assert reports[0]["build"][position]["command"] == report["build"][position]["command"]
    build = reports[0]["host_build"]
    log = AREA / build["log"]
    assert sha(log) == build["sha256"]
    assert build["libraries"] == {name: sha(path) for name, path in cargo_artifacts(log).items()}
    assert read_override(asio_profile(AREA / "recovery-host128.exe")) == (0, winreg.REG_DWORD)

    staged = subprocess.check_output(["git", "diff", "--cached", "--name-only"], cwd=ROOT, text=True).splitlines()
    assert {OUT, PROTOCOL, reserve_name, fir_name, *names} <= set(staged)
    for name in set(staged) - {OUT}:
        assert "recovery_engine128" in name.lower() and (name == RUNNER or name not in source_hashes)
        raw = git_blob(":" + name)
        assert raw == (ROOT / name).read_bytes(), name
        source_hashes[name] = digest(raw)
    source_hashes[PREVIOUS] = sha(ROOT / PREVIOUS)
    receipt_paths = [reserve_name, fir_name, *names]
    retained = sum((ROOT / name).stat().st_size for name in receipt_paths)
    assert retained <= 4 * 1024**2
    result = {key: value for key, value in prior.items() if not key.startswith("new_") or key == "new_listening"}
    result.update(
        schema="rf-d/recovery-engine-effective-128-broadcast/v1", passed=True, base_commit=BASE,
        source_sha256=source_hashes, previous_qa=PREVIOUS, previous_qa_sha256=sha(ROOT / PREVIOUS),
        protected_public_sources=len(prior["source_sha256"]), protected_private_inputs=len(private),
        electrical_reserves_admitted=True, same_laws_bit_exact=True, long_confirmation=summary,
        rack_128_admitted=any(report["rack_128_admitted"] for report in reports[1:]),
        whole_voice_rt=False, real_time=False, fir_split_bit_exact=True,
        retained_receipt_bytes=retained,
        recovery_engine128_broadcast_reports={name: sha(ROOT / name) for name in receipt_paths},
    )
    return result


if __name__ == "__main__":
    result = audit()
    write(ROOT / OUT, result)
    retire_lab()
    result["temporary_area_empty"] = not list(AREA.iterdir())
    assert result["temporary_area_empty"]
    write(ROOT / OUT, result)
    print("BROADCAST128_QA", result["protected_public_sources"], result["protected_private_inputs"],
          result["retained_receipt_bytes"], result["rack_128_admitted"])
