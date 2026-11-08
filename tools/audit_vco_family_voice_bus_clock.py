"""Recheck the collector clock, retained replays and fixed-clock confirmation."""
import argparse
import subprocess
from pathlib import Path

from affine_evidence import encode_json, recover
from audit_vco_family_voice_bus_hot import OUT as HOT_QA
from audit_vco_family_voice_bus_jacobian import OUT as JACOBIAN_QA
from audit_vco_family_voice_bus_reuse import DEADLINE_S, OUT as REUSE_QA, inherited
from audit_vco_family_voice_bus_scatter import OUT as SCATTER_QA
from check_hybrid_voice import unpack
from check_vco_family_voice_bus_clock import CAPS, CONTROL, CPU, GUARDS, PRIOR_QA, REPORT, metrics, stable
from check_vco_family_voice_bus_cost import references
from check_vco_family_voice_bus_latch_lu import verify_run
from check_vco_phase import COMPILER, LIB
from prepare_dual_chain import ROOT, sha, write
from validate_recovery_engine128 import git_blob
from validate_vco_family_voice_bus import MODEL, histories, read

OUT = REPORT + "_tests01.json"
TIMES = {"duration_s", "thread_cpu_s"}


def audit(sequence):
    path = REPORT + f"{sequence:02}.json"
    report, prior = read(path), read(PRIOR_QA)
    assert report["passed"] and report["temporary_area_empty"] and prior["passed"]
    assert report["prior_sha256"] == sha(ROOT / PRIOR_QA)
    assert report["control_sha256"] == sha(ROOT / CONTROL)
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
    for earlier in (REUSE_QA, HOT_QA, JACOBIAN_QA, PRIOR_QA, SCATTER_QA):
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
    confirmation = {}
    for label, original in reference.items():
        assert original[1][0][3].tobytes() == states[label]
        frozen = prior["loaded_branches"][label]["combined"]
        cases = report["trials"][label]
        trials[label] = {}
        assert [int(cap) for cap in cases] == list(CAPS[:len(cases)])
        for cap, item in cases.items():
            raw = unpack(item["stdout"])
            observed = metrics(raw, original, frozen) if item["exit_code"] == 0 else None
            trials[label][cap] = observed
            if observed is not None:
                assert encode_json(observed) == encode_json(item["metrics"])
            if observed and observed["passed"]:
                assert int(cap) == int(list(cases)[-1]) and "replay" not in item
                chosen[label] = int(cap)
                continue
            replay = item["replay"]
            assert item["command"] == replay["command"] and item["exit_code"] == replay["exit_code"]
            assert unpack(item["stderr"]) == unpack(replay["stderr"])
            assert stable(raw) == stable(unpack(replay["stdout"]))
        if label not in chosen:
            assert len(cases) == len(CAPS)
            continue
        checked = report["confirmation"][label]
        fixed, candidate = checked["fixed"], checked["trial"]
        assert fixed["exit_code"] == candidate["exit_code"] == 0
        control = verify_run(unpack(fixed["stdout"]), original, frozen, True)
        actual = metrics(unpack(candidate["stdout"]), original, frozen)
        assert control["duration_s"] > DEADLINE_S and actual["duration_s"] > DEADLINE_S
        assert actual["passed"] and actual["subdivisions"] == chosen[label]
        assert stable(unpack(candidate["stdout"])) == stable(unpack(cases[str(chosen[label])]["stdout"]))
        assert encode_json(control) == encode_json(fixed["metrics"])
        assert encode_json(actual) == encode_json(candidate["metrics"])
        assert checked["speedup"] == control["duration_s"] / actual["duration_s"]
        confirmation[label] = dict(fixed=control, candidate=actual, speedup=checked["speedup"],
                                   cpu_speedup=control["thread_cpu_s"] / actual["thread_cpu_s"])
    assert chosen == report["chosen"] and set(chosen) == set(report["confirmation"])

    staged = subprocess.check_output(["git", "diff", "--cached", "--name-only"], cwd=ROOT, text=True).splitlines()
    assert {path, OUT} <= set(staged) and not set(staged).intersection(protected)
    recorded = {}
    failures = {}
    for name in sorted(set(staged) - {OUT}):
        assert "family_voice_bus" in name.lower() or "familia_bus_voz" in name.lower()
        assert git_blob(":" + name) == (ROOT / name).read_bytes(), name
        recorded[name] = sha(ROOT / name)
        if name.startswith(REPORT) and name != path:
            failed = read(name)
            assert not failed["passed"] and failed["temporary_area_empty"]
            recover(failed)
            first, replay = failed["failed"], failed["unchanged_replay"]
            assert first["exit_code"] == replay["exit_code"] and unpack(first["stderr"]) == unpack(replay["stderr"])
            assert stable(unpack(first["stdout"])) == stable(unpack(replay["stdout"]))
            failures[name] = failed["failure"]
    assert not list((ROOT / "tmp/lab-current").iterdir())
    retained = sum((ROOT / name).stat().st_size for name in staged if name.startswith(REPORT) and name != OUT)
    assert retained <= 8 * 1024**2
    return dict(schema="rf-d/h128-loaded-voice-clock/v1", passed=True,
                prior_sha256=report["prior_sha256"], control_sha256=report["control_sha256"],
                source_sha256=recorded, protected_public_sources=len(protected), protected_private_inputs=len(private),
                trials=trials, chosen=chosen, confirmation=confirmation, failures=failures,
                affinity=pin, deadline_s=DEADLINE_S, physical_passes=0, rt_admitted=False,
                retained_receipt_bytes=retained, temporary_area_empty=True)


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--report", type=int, default=1)
    result = audit(cli.parse_args().report)
    write(ROOT / OUT, result)
    print("H128_VOICE_CLOCK_QA", result["chosen"], result["retained_receipt_bytes"])
