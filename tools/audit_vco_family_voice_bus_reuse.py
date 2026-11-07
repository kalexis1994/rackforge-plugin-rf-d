"""Recompute the fixed-clock reserves and preserve the rejected adaptive trial."""
import struct
import subprocess
from pathlib import Path

from affine_evidence import encode_json, recover
from audit_vco_family_voice_bus import PREVIOUS
from check_hybrid_voice import unpack
from check_vco_family_voice_bus_cost import BASE_QA, parse_adaptive, profile_metrics, references
from check_vco_family_voice_bus_reuse import MEASUREMENT, TRIAL, compare
from check_vco_phase import COMPILER, LIB
from prepare_dual_chain import ROOT, sha, write
from validate_recovery_engine128 import git_blob
from validate_vco_family_voice_bus import MODEL, histories, parse_branch, read

RUN = MEASUREMENT + "01.json"
OUT = MEASUREMENT + "_tests01.json"
DEADLINE_S = 128 / 48_000 / 2


def inherited():
    physical, nvidia, mono, voice = (read(path) for path in (*PREVIOUS, BASE_QA))
    assert all(item["passed"] for item in (physical, nvidia, mono, voice))
    known = {**physical["source_sha256"], **nvidia["verified_source_sha256"],
             **mono["verified_source_sha256"], **voice["source_sha256"]}
    for path, expected in known.items():
        assert sha(ROOT / path) == expected, path
    private = physical["private_input_sha256"]
    assert len(private) == 8769 and all((ROOT / path).is_file() for path in private)
    listening = physical["new_listening"]
    assert sha(ROOT / listening["path"]) == listening["sha256"]
    return known, private


def audit():
    base = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    known, private = inherited()
    reference, archived = references()
    states, inputs = histories()
    assert all(private[path] == expected for path, expected in inputs.items())
    trial, fixed = read(TRIAL), read(RUN)
    assert trial["passed"] and not trial["reserves_passed"] and not trial["fixed"]
    assert fixed["passed"] and fixed["adaptive_trial_sha256"] == sha(ROOT / TRIAL)
    for receipt in (trial, fixed):
        recover(receipt)
        assert receipt["temporary_area_empty"]
        assert receipt["compiler_sha256"] == sha(Path(COMPILER))
        assert receipt["library_sha256"] == sha(LIB)
        assert receipt["private_inputs"] == inputs and receipt["reference_inputs"] == archived
        assert receipt["table_sha256"] == read(MODEL)["table_sha256"]
        assert receipt["prior_sha256"] == sha(ROOT / BASE_QA)
    for path, expected in fixed["source_sha256"].items():
        assert sha(ROOT / path) == expected, path

    for label, (_, grid) in reference.items():
        profile = trial["profiles"][label]
        last = 20 if label == "negative" else 81
        observed = profile_metrics(unpack(profile["stdout"]), grid[last], last)
        assert observed == profile["metrics"]
    negative, positive = (trial["adaptive"][label] for label in ("negative", "positive"))
    metrics = parse_adaptive(unpack(negative["stdout"]), reference["negative"][1])
    assert metrics["passed"] and encode_json(metrics) == encode_json(negative["metrics"])
    replay = positive["unchanged_replay"]
    assert positive["exit_code"] == replay["exit_code"] != 0
    assert positive["command"] == replay["command"]
    for stream in ("stdout", "stderr"):
        assert unpack(positive[stream]) == unpack(replay[stream])
    assert b"77 59610 span=2: IterationBudget" in unpack(positive["stderr"])

    assert fixed["fma_check"]["exit_code"] == 0 and unpack(fixed["fma_check"]["stdout"]).strip() == b"True"
    assert all(build["exit_code"] == 0 for build in fixed["builds"].values())
    assert "-C" in fixed["builds"]["reuse_fma"]["command"] and "target-feature=+fma" in fixed["builds"]["reuse_fma"]["command"]
    assert "target-feature=+fma" not in fixed["builds"]["fixed"]["command"]
    results = {}
    for label, original in reference.items():
        assert original[1][0][3].tobytes() == states[label]
        measured = {}
        for variant, runs in fixed["runs"].items():
            run = runs[label]
            assert run["exit_code"] == 0
            raw = unpack(run["stdout"])
            metrics = compare(raw, original)
            assert encode_json(metrics) == encode_json(run["metrics"])
            _, grid = parse_branch(b"\n".join(line for line in raw.splitlines() if not line.startswith(b"LATCH,")))
            assert all(struct.pack("<ddd", *a[:3]) == struct.pack("<ddd", *b[:3])
                       for a, b in zip(grid, original[1]))
            measured[variant] = metrics
        candidate, control = measured["reuse_fma"], measured["fixed"]
        assert candidate["latch_events"] == control["latch_events"]
        speedup = control["duration_s"] / candidate["duration_s"]
        assert speedup == fixed["speedup"][label] and speedup > 1
        assert candidate["duration_s"] > DEADLINE_S
        results[label] = dict(**measured, speedup=speedup)
    assert not results["negative"]["reuse_fma"]["latch_events"]
    latch, = results["positive"]["reuse_fma"]["latch_events"]
    assert latch[0] == 0 and latch[-1] == 1
    staged = subprocess.check_output(["git", "diff", "--cached", "--name-only"], cwd=ROOT, text=True).splitlines()
    assert {TRIAL, RUN, OUT} <= set(staged) and not set(staged).intersection(known)
    hashes = {}
    for path in sorted(set(staged) - {OUT}):
        assert "family_voice_bus" in path.lower() or "familia_bus_voz" in path.lower()
        assert git_blob(":" + path) == (ROOT / path).read_bytes(), path
        hashes[path] = sha(ROOT / path)
    retained = sum((ROOT / path).stat().st_size for path in (TRIAL, RUN))
    assert retained <= 8 * 1024**2
    area = ROOT / "tmp/lab-current"
    assert not list(area.iterdir())
    return dict(schema="rf-d/h128-loaded-voice-cost/v1", passed=True, base_commit=base,
                source_sha256=hashes, protected_public_sources=len(known), protected_private_inputs=len(private),
                adaptive_accepted=False, adaptive_replay_identical=True, fixed_reserves_identical=True,
                loaded_branches=results, retained_receipt_bytes=retained, temporary_area_empty=True,
                deadline_s=DEADLINE_S, physical_passes=0, rt_admitted=False)


if __name__ == "__main__":
    result = audit()
    write(ROOT / OUT, result)
    print("H128_VOICE_COST_QA", {key: case["speedup"] for key, case in result["loaded_branches"].items()},
          result["retained_receipt_bytes"])
