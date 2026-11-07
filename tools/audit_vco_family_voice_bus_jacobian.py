"""Recheck the direct Jacobian, LU guards and loaded voice receipts."""
import argparse
import subprocess
from pathlib import Path

from affine_evidence import encode_json, recover
from audit_vco_family_voice_bus_reuse import DEADLINE_S, OUT as REUSE_QA, inherited
from check_hybrid_voice import unpack
from check_vco_family_voice_bus_cost import profile_metrics, references
from check_vco_family_voice_bus_hot import ORDERS, VARIANTS, profile_summary
from check_vco_family_voice_bus_jacobian import CONTROL, PRIOR_QA, REPORT, verify
from check_vco_phase import COMPILER, LIB
from prepare_dual_chain import ROOT, sha, write
from validate_recovery_engine128 import git_blob
from validate_vco_family_voice_bus import MODEL, histories, read

OUT = REPORT + "_tests01.json"
FIRST = REPORT + "01.json"


def check_report(report, reference, prior, archived, inputs):
    assert report["passed"] and report["temporary_area_empty"]
    assert report["prior_sha256"] == sha(ROOT / PRIOR_QA)
    assert report["control_sha256"] == sha(ROOT / CONTROL)
    assert report["compiler_sha256"] == sha(Path(COMPILER))
    assert report["library_sha256"] == sha(LIB)
    assert report["table_sha256"] == read(MODEL)["table_sha256"]
    assert report["reference_inputs"] == archived and report["private_inputs"] == inputs
    recover(report)
    assert report["fma_check"]["exit_code"] == 0 and unpack(report["fma_check"]["stdout"]).strip() == b"True"
    assert all(item["exit_code"] == 0 and "target-feature=+fma" in item["command"]
               for item in report["builds"].values())
    assert set(report["guards"]) == {"control", "combined"}
    for guard in report["guards"].values():
        assert guard["exit_code"] == 0 and unpack(guard["stdout"]).strip() == b"LINEAR_GUARD,4,2"

    branches = {}
    for label, original in reference.items():
        observed = {}
        for variant in ("control", "combined"):
            item = report["reserves"][variant][label]
            assert item["exit_code"] == 0
            metrics = verify(unpack(item["stdout"]), original, prior["loaded_branches"][label]["combined"])
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
            assert len({batch["runs"][variant][label]["metrics"][section]["calls"]
                        for batch in report["profiles"] for variant in VARIANTS}) == 1
    return dict(loaded_branches=branches, median_profile_ns=medians,
                local_audits=sum(len(case["combined"]["local"]) for case in branches.values()),
                contact_stages=sum(case["combined"]["contact_stages"] for case in branches.values()))


def audit(number):
    name = REPORT + f"{number:02}.json"
    report, prior, reuse = (read(path) for path in (name, PRIOR_QA, REUSE_QA))
    assert prior["passed"] and reuse["passed"] and report["linear"] == "zero-cross"
    assert all(sha(ROOT / path) == expected for path, expected in report["source_sha256"].items())
    known, private = inherited()
    recent = {**reuse["source_sha256"], **prior["source_sha256"]}
    protected = {**known, **recent}
    for path, expected in recent.items():
        assert sha(ROOT / path) == expected, path
    reference, archived = references()
    states, inputs = histories()
    assert all(private[path] == expected for path, expected in inputs.items())
    assert all(original[1][0][3].tobytes() == states[label] for label, original in reference.items())
    bounded = check_report(read(FIRST), reference, prior, archived, inputs)
    result = check_report(report, reference, prior, archived, inputs)
    paired_ratios = {}
    for label in reference:
        paired_ratios[label] = {}
        for variant, section in (("assembly", "full_stage"), ("linear", "linear_solve")):
            ratios = [
                batch["runs"][variant][label]["metrics"][section]["ns"]
                / batch["runs"]["control"][label]["metrics"][section]["ns"]
                for batch in report["profiles"]
            ]
            assert all(0 < ratio < 1 for ratio in ratios)
            paired_ratios[label][section] = ratios

    staged = subprocess.check_output(["git", "diff", "--cached", "--name-only"], cwd=ROOT, text=True).splitlines()
    assert {FIRST, name, OUT} <= set(staged) and not set(staged).intersection(protected)
    recorded = {}
    rejected = {}
    for path in sorted(set(staged) - {OUT}):
        assert "family_voice_bus" in path.lower() or "familia_bus_voz" in path.lower()
        assert git_blob(":" + path) == (ROOT / path).read_bytes(), path
        recorded[path] = sha(ROOT / path)
        if path.startswith(REPORT) and path not in (FIRST, name):
            failed = read(path)
            assert not failed["passed"] and failed["temporary_area_empty"]
            recover(failed)
            first, replay = failed["failed"], failed["unchanged_replay"]
            assert first["exit_code"] == replay["exit_code"]
            assert all(unpack(first[key]) == unpack(replay[key]) for key in ("stdout", "stderr"))
            rejected[path] = failed["failure"]
    assert not list((ROOT / "tmp/lab-current").iterdir())
    retained = sum((ROOT / path).stat().st_size for path in staged if path.startswith(REPORT) and path != OUT)
    assert retained <= 8 * 1024**2
    return dict(schema="rf-d/h128-loaded-voice-jacobian/v1", passed=True,
                prior_sha256=report["prior_sha256"], control_sha256=report["control_sha256"],
                source_sha256=recorded, protected_public_sources=len(protected), protected_private_inputs=len(private),
                bounded=bounded, **result, paired_ratios=paired_ratios, rejected=rejected,
                linear_guard=dict(bit_identical_directions=4, matching_rejections=2),
                deadline_s=DEADLINE_S, physical_passes=0, rt_admitted=False,
                retained_receipt_bytes=retained, temporary_area_empty=True)


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--report", type=int, default=2)
    result = audit(cli.parse_args().report)
    write(ROOT / OUT, result)
    print("H128_VOICE_JACOBIAN_QA", result["local_audits"], result["contact_stages"], result["retained_receipt_bytes"])
