"""Reaudit the positive release, charge boundaries and active-row LU timings."""
import argparse
import subprocess
from pathlib import Path

from affine_evidence import encode_json, recover
from audit_vco_family_voice_bus_hot import OUT as HOT_QA
from audit_vco_family_voice_bus_reuse import DEADLINE_S, OUT as REUSE_QA, inherited
from check_hybrid_voice import unpack
from check_vco_family_voice_bus_cost import profile_metrics, references
from check_vco_family_voice_bus_hot import ORDERS, VARIANTS
from check_vco_family_voice_bus_latch_lu import CONTROL, CPU, GUARDS, PRIOR_QA, REPORT, WINDOWS, summary, verify_run
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
    assert report["compiler_sha256"] == sha(Path(COMPILER))
    assert report["library_sha256"] == sha(LIB)
    assert report["table_sha256"] == read(MODEL)["table_sha256"]
    assert encode_json(report["windows"]) == encode_json(WINDOWS)
    assert report["reference_inputs"] == archived and report["private_inputs"] == inputs
    recover(report)
    assert report["fma_check"]["exit_code"] == 0 and unpack(report["fma_check"]["stdout"]).strip() == b"True"
    assert all(item["exit_code"] == 0 and "target-feature=+fma" in item["command"]
               for item in report["builds"].values())
    confirm = report.get("confirm", False)
    variants = ("control", "combined", "linear") if confirm else ("control", "combined")
    assert set(report["guards"]) == set(report["reserves"]) == set(variants)
    for guard in report["guards"].values():
        assert guard["exit_code"] == 0 and b"\n".join(unpack(guard["stdout"]).splitlines()) == GUARDS
    if confirm:
        pin = report["affinity"]
        assert pin["cpu"] == CPU and pin["mask"] == 1 << CPU and pin["original_mask"] & pin["mask"]
        assert set(report["affinities"]) == set(variants)
        for item in report["affinities"].values():
            assert item["exit_code"] == 0 and unpack(item["stdout"]).strip() == f"AFFINITY,{1 << CPU},{CPU}".encode()

    branches = {}
    for label, original in reference.items():
        observed = {}
        for variant in variants:
            item = report["reserves"][variant][label]
            assert item["exit_code"] == 0
            metrics = verify_run(unpack(item["stdout"]), original, prior["loaded_branches"][label]["combined"], confirm)
            assert encode_json(metrics) == encode_json(item["metrics"])
            observed[variant] = metrics
        control = observed["control"]
        for metrics in observed.values():
            exclude = {"duration_s", "thread_cpu_s"}
            assert {k: v for k, v in metrics.items() if k not in exclude} == {
                k: v for k, v in control.items() if k not in exclude}
            assert metrics["duration_s"] > DEADLINE_S
        ratio = observed["combined"]["duration_s"] / control["duration_s"]
        assert ratio == report["ratios"][label]
        if confirm:
            thread = observed["combined"]["thread_cpu_s"] / control["thread_cpu_s"]
            isolated = observed["linear"]["duration_s"] / control["duration_s"]
            assert thread == report["thread_ratios"][label] and isolated == report["isolated_linear_ratios"][label]
        branches[label] = dict(**observed, duration_ratio=ratio)
    assert [tuple(batch["order"]) for batch in report["profiles"]] == list(ORDERS)
    for batch in report["profiles"]:
        for variant in VARIANTS:
            for window, (label, _, end) in WINDOWS.items():
                item = batch["runs"][variant][window]
                assert item["exit_code"] == 0
                assert profile_metrics(unpack(item["stdout"]), reference[label][1][end], end) == item["metrics"]
    medians = summary(report["profiles"])
    assert medians == report["median_profile_ns"]
    paired = {
        window: {section: [batch["runs"][variant][window]["metrics"][section]["ns"]
                           / batch["runs"]["control"][window]["metrics"][section]["ns"] for batch in report["profiles"]]
                 for variant, section in (("assembly", "full_stage"), ("linear", "linear_solve"))}
        for window in WINDOWS
    }
    return dict(loaded_branches=branches, median_profile_ns=medians, paired_ratios=paired)


def audit(number):
    name = REPORT + f"{number:02}.json"
    report, prior, first = (read(path) for path in (name, PRIOR_QA, FIRST))
    assert prior["passed"] and report["confirm"] and not first.get("confirm", False)
    assert all(sha(ROOT / path) == expected for path, expected in report["source_sha256"].items())
    known, private = inherited()
    recent = {}
    for path in (REUSE_QA, HOT_QA, PRIOR_QA):
        qa = read(path)
        assert qa["passed"]
        recent.update(qa["source_sha256"])
    assert all(sha(ROOT / path) == expected for path, expected in recent.items())
    protected = {**known, **recent}
    reference, archived = references()
    states, inputs = histories()
    assert all(private[path] == expected for path, expected in inputs.items())
    assert all(original[1][0][3].tobytes() == states[label] for label, original in reference.items())
    unpinned = check_report(first, prior, reference, archived, inputs)
    assert all(case["duration_ratio"] > 1 for case in unpinned["loaded_branches"].values())
    confirmed = check_report(report, prior, reference, archived, inputs)
    assert all(0 < ratio < 1 for ratio in report["ratios"].values())
    assert all(0 < ratio < 1 for ratio in report["isolated_linear_ratios"].values())
    assert all(0 < ratio < 1 for ratio in report["thread_ratios"].values())
    for window in ("before", "positive", "after"):
        assert all(0 < ratio < 1 for runs in confirmed["paired_ratios"][window].values() for ratio in runs)

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
    branches = confirmed["loaded_branches"]
    return dict(schema="rf-d/h128-loaded-voice-release/v1", passed=True,
                prior_sha256=report["prior_sha256"], control_sha256=report["control_sha256"],
                source_sha256=recorded, protected_public_sources=len(protected), protected_private_inputs=len(private),
                unpinned=unpinned, **confirmed, failures=failures, affinity=report["affinity"],
                local_audits=sum(len(case["combined"]["local"]) for case in branches.values()),
                contact_stages=sum(case["combined"]["contact_stages"] for case in branches.values()),
                guards=dict(junction_cases=162, junction_rejections=6, linear_directions=8, linear_rejections=2),
                deadline_s=DEADLINE_S, physical_passes=0, rt_admitted=False,
                retained_receipt_bytes=retained, temporary_area_empty=True)


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--report", type=int, default=2)
    result = audit(cli.parse_args().report)
    write(ROOT / OUT, result)
    print("H128_VOICE_RELEASE_QA", result["local_audits"], result["contact_stages"], result["retained_receipt_bytes"])
