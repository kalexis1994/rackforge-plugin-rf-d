"""Recheck anticipation, the independent phase contrast and paired timings."""
import argparse
import subprocess
from pathlib import Path

from affine_evidence import encode_json, recover
from audit_vco_family_voice_bus_hot import OUT as HOT_QA
from audit_vco_family_voice_bus_jacobian import OUT as JACOBIAN_QA
from audit_vco_family_voice_bus_reuse import DEADLINE_S, OUT as REUSE_QA, inherited
from audit_vco_family_voice_bus_scatter import OUT as SCATTER_QA
from check_hybrid_voice import unpack
from check_vco_family_voice_bus_approach import (
    CONTROL, CPU, GUARDS, LATCH, ORDERS, PRIOR_QA, RECIPES, REPORT, held_reference, metrics, paired_stats,
)
from check_vco_family_voice_bus_clock import metrics as old_metrics, stable
from check_vco_family_voice_bus_cost import references
from check_vco_phase import COMPILER, LIB
from prepare_dual_chain import ROOT, sha, write
from validate_recovery_engine128 import git_blob
from validate_vco_family_voice_bus import MODEL, histories, read

OUT = REPORT + "_tests01.json"
FIRST = REPORT + "01.json"


def check_replay(item):
    replay = item["replay"]
    assert item["command"] == replay["command"] and item["exit_code"] == replay["exit_code"]
    assert unpack(item["stderr"]) == unpack(replay["stderr"])
    assert stable(unpack(item["stdout"])) == stable(unpack(replay["stdout"]))


def audit(sequence):
    path = REPORT + f"{sequence:02}.json"
    report, prior, release, old = (read(name) for name in (path, PRIOR_QA, LATCH, CONTROL))
    assert report["passed"] and report["temporary_area_empty"]
    assert prior["passed"] and release["passed"] and old["passed"]
    assert report["prior_sha256"] == sha(ROOT / PRIOR_QA)
    assert report["control_sha256"] == sha(ROOT / CONTROL)
    assert report["latch_sha256"] == sha(ROOT / LATCH)
    assert report["compiler_sha256"] == sha(Path(COMPILER)) and report["library_sha256"] == sha(LIB)
    assert report["table_sha256"] == read(MODEL)["table_sha256"]
    assert all(sha(ROOT / name) == expected for name, expected in report["source_sha256"].items())
    recover(report)
    assert report["fma_check"]["exit_code"] == 0 and unpack(report["fma_check"]["stdout"]).strip() == b"True"
    pin = report["affinity"]
    assert pin["cpu"] == CPU and pin["mask"] == 1 << CPU and pin["original_mask"] & pin["mask"]
    assert report["affinity_check"]["exit_code"] == 0
    assert unpack(report["affinity_check"]["stdout"]).strip() == f"AFFINITY,{1 << CPU},{CPU}".encode()
    assert report["guards"]["exit_code"] == 0 and b"\n".join(unpack(report["guards"]["stdout"]).splitlines()) == GUARDS
    assert report["build"]["exit_code"] == 0 and "target-feature=+fma" in report["build"]["command"]

    known, private = inherited()
    recent = {}
    for earlier in (REUSE_QA, HOT_QA, JACOBIAN_QA, LATCH, SCATTER_QA, PRIOR_QA):
        qa = read(earlier)
        assert qa["passed"]
        recent.update(qa["source_sha256"])
    assert all(sha(ROOT / name) == expected for name, expected in recent.items())
    protected = {**known, **recent}
    reference, archived = references()
    states, inputs = histories()
    assert report["reference_inputs"] == archived and report["private_inputs"] == inputs
    assert all(private[name] == expected for name, expected in inputs.items())
    chosen = {}
    trials = {}
    for label, original in reference.items():
        assert original[1][0][3].tobytes() == states[label]
        frozen = release["loaded_branches"][label]["combined"]
        cases = report["trials"][label]
        assert [tuple(case["recipe"]) for case in cases] == RECIPES[:len(cases)]
        trials[label] = []
        for case in cases:
            item, recipe = case["run"], case["recipe"]
            observed = metrics(unpack(item["stdout"]), original, frozen, recipe) if item["exit_code"] == 0 else None
            trials[label].append(dict(recipe=recipe, metrics=observed))
            if observed is not None:
                assert encode_json(observed) == encode_json(item["metrics"])
            if observed and observed["passed"]:
                assert case is cases[-1] and "replay" not in item
                chosen[label] = recipe
            else:
                check_replay(item)
        if label not in chosen:
            assert len(cases) == len(RECIPES)
    assert chosen == report["chosen"]

    first = read(FIRST)
    assert report["hold"] and first["passed"] and not first.get("hold", False)
    assert first["temporary_area_empty"] and not first["held"] and not first["paired"]
    assert first["reference_inputs"] == archived and first["private_inputs"] == inputs
    for key in ("prior_sha256", "control_sha256", "latch_sha256", "compiler_sha256", "library_sha256", "table_sha256"):
        assert first[key] == report[key]
    recover(first)
    assert first["chosen"] == {"negative": list(RECIPES[0])}
    before_hold = {}
    for label, cases in first["trials"].items():
        target = reference[label]
        latch = release["loaded_branches"][label]["combined"]
        assert [tuple(case["recipe"]) for case in cases] == (RECIPES if label == "positive" else RECIPES[:1])
        before_hold[label] = []
        for case in cases:
            recipe, item = case["recipe"], case["run"]
            assert item["exit_code"] == 0
            observed = metrics(unpack(item["stdout"]), target, latch, recipe)
            assert encode_json(observed) == encode_json(item["metrics"])
            assert observed["same_switches"] and observed["passed"] == (label == "negative")
            if label == "positive":
                assert observed["refinement"]["nodal_gate_fraction"] > 1.
                check_replay(item)
            before_hold[label].append(dict(recipe=recipe, metrics=observed))

    held = {}
    if "positive" in chosen:
        fixed, candidate = (report["held"][key] for key in ("fixed", "candidate"))
        assert fixed["exit_code"] == 0
        target, latch, control = held_reference(unpack(fixed["stdout"]))
        assert target[1][0][3].tobytes() == states["positive"]
        assert encode_json(control) == encode_json(fixed["metrics"])
        m = metrics(unpack(candidate["stdout"]), target, latch, chosen["positive"]) if candidate["exit_code"] == 0 else None
        if m is not None:
            assert encode_json(m) == encode_json(candidate["metrics"])
        if not m or not m["passed"]:
            check_replay(candidate)
        held = dict(fixed=control, candidate=m)
    else:
        assert not report["held"]

    comparison = {}
    if len(chosen) == 2 and held["candidate"] and held["candidate"]["passed"]:
        assert set(report["paired"]) == set(chosen)
        for label, pairs in report["paired"].items():
            assert [tuple(pair["order"]) for pair in pairs] == list(ORDERS)
            target = reference[label]
            latch = release["loaded_branches"][label]["combined"]
            archived_old = old["confirmation"][label]["trial"]["stdout"]
            archived_new = report["trials"][label][-1]["run"]["stdout"]
            for pair in pairs:
                for variant, item in pair["runs"].items():
                    assert item["exit_code"] == 0
                    raw = unpack(item["stdout"])
                    if variant == "old":
                        m = old_metrics(raw, target, latch)
                        assert stable(raw) == stable(unpack(archived_old))
                    else:
                        m = metrics(raw, target, latch, chosen[label])
                        assert stable(raw) == stable(unpack(archived_new))
                    assert m["passed"] and m["duration_s"] > DEADLINE_S
                    assert encode_json(m) == encode_json(item["metrics"])
            comparison[label] = paired_stats(pairs)
        assert comparison == report["comparison"]
    else:
        assert not report["paired"]

    staged = subprocess.check_output(["git", "diff", "--cached", "--name-only"], cwd=ROOT, text=True).splitlines()
    assert {FIRST, path, OUT} <= set(staged) and not set(staged).intersection(protected)
    recorded = {}
    failures = {}
    for name in sorted(set(staged) - {OUT}):
        assert "family_voice_bus" in name.lower() or "familia_bus_voz" in name.lower()
        assert git_blob(":" + name) == (ROOT / name).read_bytes(), name
        recorded[name] = sha(ROOT / name)
        if name.startswith(REPORT) and name not in (FIRST, path):
            failed = read(name)
            assert not failed["passed"] and failed["temporary_area_empty"]
            recover(failed)
            first, replay = failed["failed"], failed["unchanged_replay"]
            assert first["exit_code"] == replay["exit_code"] and unpack(first["stderr"]) == unpack(replay["stderr"])
            assert stable(unpack(first["stdout"])) == stable(unpack(replay["stdout"]))
            failures[name] = failed["failure"]
    assert not list((ROOT / "tmp/lab-current").iterdir())
    retained = sum((ROOT / name).stat().st_size for name in staged if name.startswith(REPORT) and name != OUT)
    assert retained <= 12 * 1024**2
    return dict(schema="rf-d/h128-loaded-voice-approach/v1", passed=True,
                prior_sha256=report["prior_sha256"], control_sha256=report["control_sha256"],
                source_sha256=recorded, protected_public_sources=len(protected), protected_private_inputs=len(private),
                trials=trials, before_hold=before_hold, chosen=chosen, held=held, comparison=comparison, failures=failures,
                affinity=pin, deadline_s=DEADLINE_S, physical_passes=0, rt_admitted=False,
                retained_receipt_bytes=retained, temporary_area_empty=True)


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--report", type=int, default=2)
    result = audit(cli.parse_args().report)
    write(ROOT / OUT, result)
    print("H128_VOICE_APPROACH_QA", result["chosen"], result["retained_receipt_bytes"])
