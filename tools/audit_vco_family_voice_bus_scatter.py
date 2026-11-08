"""Recompute the sparse matrix, loaded reserves and nested timing evidence."""
import argparse
import subprocess
from pathlib import Path

from affine_evidence import encode_json, recover
from audit_vco_family_voice_bus_hot import OUT as HOT_QA
from audit_vco_family_voice_bus_jacobian import OUT as JACOBIAN_QA
from audit_vco_family_voice_bus_reuse import DEADLINE_S, OUT as REUSE_QA, inherited
from check_hybrid_voice import unpack
from check_vco_family_voice_bus_cost import references
from check_vco_family_voice_bus_scatter import (
    CONTROL, CPU, GUARDS, ORDERS, PRIOR_QA, REPORT, VARIANTS, WINDOWS, medians, profile, reserve,
)
from check_vco_phase import COMPILER, LIB
from prepare_dual_chain import ROOT, sha, write
from validate_recovery_engine128 import git_blob
from validate_vco_family_voice_bus import MODEL, histories, read

OUT = REPORT + "_tests01.json"
FIRST = REPORT + "01.json"


def check_report(report, prior, reference, archived, inputs):
    assert report["passed"] and report["temporary_area_empty"]
    assert report["prior_sha256"] == sha(ROOT / PRIOR_QA)
    assert report["control_sha256"] == sha(ROOT / CONTROL)
    assert report["compiler_sha256"] == sha(Path(COMPILER)) and report["library_sha256"] == sha(LIB)
    assert report["table_sha256"] == read(MODEL)["table_sha256"]
    assert encode_json(report["windows"]) == encode_json(WINDOWS)
    assert report["reference_inputs"] == archived and report["private_inputs"] == inputs
    recover(report)
    assert report["fma_check"]["exit_code"] == 0 and unpack(report["fma_check"]["stdout"]).strip() == b"True"
    pin = report["affinity"]
    assert pin["cpu"] == CPU and pin["mask"] == 1 << CPU and pin["original_mask"] & pin["mask"]
    builds = {*VARIANTS, *(variant + "-profile" for variant in VARIANTS)}
    assert set(report["builds"]) == set(report["affinities"]) == builds
    for name, item in report["builds"].items():
        assert item["exit_code"] == 0 and "target-feature=+fma" in item["command"] and "laboratory" in item["command"]
        mask = report["affinities"][name]
        assert mask["exit_code"] == 0 and unpack(mask["stdout"]).strip() == f"AFFINITY,{1 << CPU},{CPU}".encode()
    guards = GUARDS + b"\nBITROW_GUARD,4096,1,1" if report.get("layout") == "bits" else GUARDS
    assert set(report["guards"]) == set(VARIANTS)
    for item in report["guards"].values():
        assert item["exit_code"] == 0 and b"\n".join(unpack(item["stdout"]).splitlines()) == guards

    branches = {}
    omit = {"duration_s", "thread_cpu_s"}
    for label, original in reference.items():
        observed = {}
        for variant in VARIANTS:
            item = report["reserves"][variant][label]
            assert item["exit_code"] == 0
            metrics = reserve(unpack(item["stdout"]), original, prior["loaded_branches"][label]["combined"])
            assert encode_json(metrics) == encode_json(item["metrics"]) and metrics["duration_s"] > DEADLINE_S
            observed[variant] = metrics
        a, b = observed["control"], observed["candidate"]
        assert {key: value for key, value in a.items() if key not in omit} == {
            key: value for key, value in b.items() if key not in omit}
        ratios = {key: b[key] / a[key] for key in omit}
        assert ratios == report["ratios"][label]
        branches[label] = dict(**observed, ratios=ratios)
    assert [tuple(batch["order"]) for batch in report["profiles"]] == list(ORDERS)
    for batch in report["profiles"]:
        for variant in VARIANTS:
            for window, (label, _, end) in WINDOWS.items():
                item = batch["runs"][variant][window]
                assert item["exit_code"] == 0
                assert profile(unpack(item["stdout"]), reference[label][1], end) == item["metrics"]
    profile_ns = medians(report["profiles"])
    assert profile_ns == report["median_profile_ns"]
    return dict(loaded_branches=branches, median_profile_ns=profile_ns, affinity=pin,
                matrix_entries=sum(case["candidate"]["matrix_entries"] for case in branches.values()))


def audit(sequence):
    name = REPORT + f"{sequence:02}.json"
    report, prior, first = (read(path) for path in (name, PRIOR_QA, FIRST))
    assert prior["passed"] and report["layout"] == "bits" and first.get("layout", "fused") == "fused"
    assert all(sha(ROOT / path) == expected for path, expected in report["source_sha256"].items())
    known, private = inherited()
    recent = {}
    for earlier in (REUSE_QA, HOT_QA, JACOBIAN_QA, PRIOR_QA):
        qa = read(earlier)
        assert qa["passed"]
        recent.update(qa["source_sha256"])
    assert all(sha(ROOT / path) == expected for path, expected in recent.items())
    protected = {**known, **recent}
    reference, archived = references()
    states, inputs = histories()
    assert all(private[path] == expected for path, expected in inputs.items())
    assert all(original[1][0][3].tobytes() == states[label] for label, original in reference.items())
    fused = check_report(first, prior, reference, archived, inputs)
    bits = check_report(report, prior, reference, archived, inputs)

    staged = subprocess.check_output(["git", "diff", "--cached", "--name-only"], cwd=ROOT, text=True).splitlines()
    assert {FIRST, name, OUT} <= set(staged) and not set(staged).intersection(protected)
    recorded = {}
    failures = {}
    for path in sorted(set(staged) - {OUT}):
        assert "family_voice_bus" in path.lower() or "familia_bus_voz" in path.lower()
        assert git_blob(":" + path) == (ROOT / path).read_bytes(), path
        recorded[path] = sha(ROOT / path)
        if path.startswith(REPORT) and path not in (FIRST, name):
            failed = read(path)
            assert not failed["passed"] and failed["temporary_area_empty"]
            recover(failed)
            original, replay = failed["failed"], failed["unchanged_replay"]
            assert original["exit_code"] == replay["exit_code"]
            assert all(unpack(original[key]) == unpack(replay[key]) for key in ("stdout", "stderr"))
            failures[path] = failed["failure"]
    assert not list((ROOT / "tmp/lab-current").iterdir())
    retained = sum((ROOT / path).stat().st_size for path in staged if path.startswith(REPORT) and path != OUT)
    assert retained <= 8 * 1024**2
    return dict(schema="rf-d/h128-loaded-voice-scatter/v1", passed=True,
                prior_sha256=report["prior_sha256"], control_sha256=report["control_sha256"],
                source_sha256=recorded, protected_public_sources=len(protected), protected_private_inputs=len(private),
                fused=fused, **bits, failures=failures, capacity_guard=True, nonfinite_product_guard=True,
                bitrow_capacity_guard=True, deadline_s=DEADLINE_S, physical_passes=0, rt_admitted=False,
                retained_receipt_bytes=retained, temporary_area_empty=True)


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--report", type=int, default=2)
    result = audit(cli.parse_args().report)
    write(ROOT / OUT, result)
    print("H128_VOICE_SCATTER_QA", result["matrix_entries"], result["retained_receipt_bytes"])
