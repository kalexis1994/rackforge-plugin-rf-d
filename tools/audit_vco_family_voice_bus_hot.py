"""Reaudit loaded states, electrical rows, factor directions and separated timing."""
import argparse
import subprocess
from pathlib import Path

from affine_evidence import encode_json, recover
from audit_vco_family_voice_bus_reuse import DEADLINE_S, OUT as PRIOR_QA, RUN as PRIOR_RUN, inherited
from check_hybrid_voice import unpack
from check_vco_family_voice_bus_cost import profile_metrics, references
from check_vco_family_voice_bus_hot import ORDERS, REPORT, VARIANTS, profile_summary, reserve
from check_vco_phase import COMPILER, LIB
from prepare_dual_chain import ROOT, sha, write
from validate_recovery_engine128 import git_blob
from validate_vco_family_voice_bus import MODEL, histories, read

OUT = REPORT + "_tests01.json"
FIRST = REPORT + "01.json"


def receipt(name, reference, archived, inputs, prior, check_current):
    report = read(name)
    assert report["passed"] and report["temporary_area_empty"]
    assert report["prior_sha256"] == sha(ROOT / PRIOR_QA)
    assert report["control_sha256"] == sha(ROOT / PRIOR_RUN)
    assert report["compiler_sha256"] == sha(Path(COMPILER))
    assert report["library_sha256"] == sha(LIB)
    assert report["table_sha256"] == read(MODEL)["table_sha256"]
    assert report["reference_inputs"] == archived and report["private_inputs"] == inputs
    if check_current:
        assert all(sha(ROOT / path) == expected for path, expected in report["source_sha256"].items())
    recover(report)
    assert unpack(report["fma_check"]["stdout"]).strip() == b"True"
    assert all(item["exit_code"] == 0 and "target-feature=+fma" in item["command"]
               for item in report["builds"].values())
    branches = {}
    for label, original in reference.items():
        observed = {}
        for variant in ("control", "combined"):
            item = report["reserves"][variant][label]
            assert item["exit_code"] == 0
            metrics = reserve(unpack(item["stdout"]), original, prior["loaded_branches"][label]["reuse_fma"])
            assert encode_json(metrics) == encode_json(item["metrics"])
            observed[variant] = metrics
        a, b = observed["control"], observed["combined"]
        assert {k: v for k, v in a.items() if k != "duration_s"} == {k: v for k, v in b.items() if k != "duration_s"}
        ratio = b["duration_s"] / a["duration_s"]
        assert ratio == report["ratios"][label] and b["duration_s"] > DEADLINE_S
        branches[label] = dict(**observed, duration_ratio=ratio)

    assert [tuple(batch["order"]) for batch in report["profiles"]] == list(ORDERS)
    for batch in report["profiles"]:
        for variant in VARIANTS:
            for label, (_, grid) in reference.items():
                item = batch["runs"][variant][label]
                assert item["exit_code"] == 0
                end = 20 if label == "negative" else 81
                assert profile_metrics(unpack(item["stdout"]), grid[end], end) == item["metrics"]
    medians = profile_summary(report["profiles"])
    assert medians == report["median_profile_ns"]
    for label in reference:
        for section in ("full_stage", "residual_stage", "linear_solve"):
            assert len({batch["runs"][v][label]["metrics"][section]["calls"]
                        for batch in report["profiles"] for v in VARIANTS}) == 1
    return dict(loaded_branches=branches, median_profile_ns=medians,
                local_audits=sum(len(case["combined"]["local"]) for case in branches.values()))


def audit(number):
    run_name = REPORT + f"{number:02}.json"
    prior = read(PRIOR_QA)
    known, private = inherited()
    for path, expected in prior["source_sha256"].items():
        assert sha(ROOT / path) == expected, path
    reference, archived = references()
    states, inputs = histories()
    assert all(private[path] == expected for path, expected in inputs.items())
    assert all(original[1][0][3].tobytes() == states[label] for label, original in reference.items())
    previous = receipt(FIRST, reference, archived, inputs, prior, False)
    assert all(case["duration_ratio"] > 1. for case in previous["loaded_branches"].values())
    result = receipt(run_name, reference, archived, inputs, prior, True)
    staged = subprocess.check_output(["git", "diff", "--cached", "--name-only"], cwd=ROOT, text=True).splitlines()
    assert {FIRST, run_name, OUT} <= set(staged)
    protected = {**known, **prior["source_sha256"]}
    assert not set(staged).intersection(protected)
    recorded = {}
    for path in sorted(set(staged) - {OUT}):
        assert "family_voice_bus" in path.lower() or "familia_bus_voz" in path.lower()
        assert git_blob(":" + path) == (ROOT / path).read_bytes(), path
        recorded[path] = sha(ROOT / path)
    assert not list((ROOT / "tmp/lab-current").iterdir())
    retained = sum((ROOT / path).stat().st_size for path in staged if path.startswith(REPORT) and path != OUT)
    assert retained <= 8 * 1024**2
    return dict(schema="rf-d/h128-loaded-voice-hot-path/v1", passed=True,
                prior_sha256=sha(ROOT / PRIOR_QA), control_sha256=sha(ROOT / PRIOR_RUN),
                source_sha256=recorded, protected_public_sources=len(protected), protected_private_inputs=len(private),
                rejected_permutation=previous, **result, deadline_s=DEADLINE_S,
                physical_passes=0, rt_admitted=False, retained_receipt_bytes=retained, temporary_area_empty=True)


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--report", type=int, default=2)
    result = audit(cli.parse_args().report)
    write(ROOT / OUT, result)
    print("H128_VOICE_HOT_QA", result["local_audits"], result["retained_receipt_bytes"])
