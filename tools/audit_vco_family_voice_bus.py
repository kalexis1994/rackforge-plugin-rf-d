"""Audit the widened BUS family, charged voice branches and retained failures."""
import json
import subprocess

import numpy as np

from affine_evidence import encode_json, recover
from check_hybrid_voice import unpack
from check_recovery_cost import digest
from check_vco_family_voice_bus import PREFIX
from check_vco_family_voice_bus_model import AREA, ORACLE, read_oracle
from prepare_dual_chain import ROOT, sha, write
from prepare_vco_family_voice_bus import TABLE
from validate_recovery_engine128 import git_blob
from validate_vco_family_voice_bus import BUS, C2, C5, J7, histories, parse_branch, refinement
from vco_family_voice_bus_receipts import ARCHIVE, archive_members, read_receipt, receipt_bytes

OUT = PREFIX + "_tests01.json"
MODEL = PREFIX + "_model01.json"
PREVIOUS = (
    "evidence/recovery_engine128_physical_tests01.json",
    "evidence/recovery_engine128_nvidia_tests01.json",
    "evidence/recovery_engine128_mono_tests01.json",
)
UPDATED = "tools/check_vco_family.py"


def read(name):
    return json.loads((ROOT / name).read_bytes())


def observed_branch(trace, history):
    assert unpack(trace["history"]) == history
    runs = trace["runs"]
    if "reused_coarse" in trace:
        prior = trace["reused_coarse"]
        assert digest(receipt_bytes(prior["path"])) == prior["sha256"]
        old, = read_receipt(prior["path"])["traces"]
        assert old["case"] == trace["case"] and old["history"] == trace["history"]
        runs = [old["runs"][prior["run"]], *runs]
    assert [run["exit_code"] for run in runs] == [0, 0]
    grids = []
    for run in runs:
        metrics, grid = parse_branch(unpack(run["stdout"]))
        assert encode_json(metrics) == encode_json(run["metrics"])
        assert grid[0][3].tobytes() == history
        grids.append(grid)
    observed = refinement(*grids)
    assert encode_json(observed) == encode_json(trace["refinement"])
    fine = np.asarray([entry[3].sum(axis=0) for entry in grids[-1]])
    coarse = np.asarray([entry[3].sum(axis=0) for entry in grids[0]])
    target = fine[:, J7]
    delta = coarse[:, J7] - target
    peak = float(np.max(abs(target)))
    assert peak > 0.
    relative_rms = float(np.linalg.norm(delta) / np.linalg.norm(target))
    relative_peak = float(np.max(abs(delta)) / peak)
    mean = float(abs(np.mean(delta)))
    assert relative_rms <= .001 and relative_peak <= .003 and mean <= 1e-6
    return dict(case=trace["case"], refinement=observed,
                bus_v=[float(min(fine[:, BUS])), float(max(fine[:, BUS]))],
                c2_v=[float(min(fine[:, C2])), float(max(fine[:, C2]))],
                c5_v=[float(min(fine[:, C5])), float(max(fine[:, C5]))],
                j7_rms_relative=relative_rms, j7_peak_relative=relative_peak, j7_mean_error_v=mean,
                profiles=[run["metrics"] for run in runs])


def audit():
    base = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    assert base.startswith("380eff1")
    physical, nvidia, mono = (read(path) for path in PREVIOUS)
    assert physical["passed"] and nvidia["passed"] and mono["passed"]
    known = {**physical["source_sha256"], **nvidia["verified_source_sha256"], **mono["verified_source_sha256"]}
    for name, expected in known.items():
        data = git_blob(f"{base}:{name}") if name == UPDATED else (ROOT / name).read_bytes()
        assert digest(data) == expected, name
    private = physical["private_input_sha256"]
    assert len(private) == 8769 and all((ROOT / name).is_file() for name in private)
    listening = physical["new_listening"]
    assert sha(ROOT / listening["path"]) == listening["sha256"]

    oracle = read_oracle()
    model = read(MODEL)
    assert oracle["passed"] and oracle["temporary_area_empty"] and model["passed"]
    recover(oracle)
    recover(model)
    assert not (ROOT / ORACLE).exists()
    assert digest(receipt_bytes(ORACLE)) == model["oracle_sha256"]
    assert oracle["pack_sha256"] == model["oracle_pack_sha256"] == sha(ROOT / oracle["pack"])
    assert len(model["validation"]) == 8 and all(case["passed"] for case in model["validation"])
    assert not model["reserved_data_used_for_fit"]
    assert model["anchor_hermite_voltage_error_bound_v"] < 2e-6

    attempts = sorted(name for name in archive_members() if "_coupled" in name)
    assert len(attempts) == 4
    reports = [read_receipt(name) for name in attempts]
    for report in reports:
        recover(report)
        assert report["runtime_retired"]
    rejected = reports[0]
    assert not rejected["passed"] and "NoDecrease" in rejected["failure"]
    initial, replay = (rejected[key] for key in ("failed_process", "unchanged_replay"))
    assert initial["exit_code"] == replay["exit_code"] != 0
    assert unpack(initial["stderr"]) == unpack(replay["stderr"])
    assert unpack(initial["stdout"]) == unpack(replay["stdout"])

    _, wide_steps, refined, accepted = reports
    assert wide_steps["passed"] and not wide_steps["loaded_reserves_passed"]
    assert refined["passed"] and not refined["loaded_reserves_passed"]
    assert accepted["passed"] and accepted["loaded_reserves_passed"]
    for report in (wide_steps, refined, accepted):
        assert not report["rt_admitted"] and report["model_sha256"] == sha(ROOT / MODEL)
        assert report["table_sha256"] == model["table_sha256"] == sha(AREA / TABLE)
    states, reference_inputs = histories()
    assert accepted["private_input_sha256"] == reference_inputs
    assert all(private[path] == expected for path, expected in reference_inputs.items())
    negative, rejected_positive = wide_steps["traces"]
    positive, = accepted["traces"]
    assert not rejected_positive["refinement"]["passed"]
    observed = [observed_branch(trace, states[trace["case"]]) for trace in (negative, positive)]
    assert [branch["case"] for branch in observed] == ["negative", "positive"]
    assert all(branch["refinement"]["passed"] for branch in observed)
    assert all(profile["duration_s"] > 128. / 48000. / 2.
               for branch in observed for profile in branch["profiles"])

    staged = subprocess.check_output(["git", "diff", "--cached", "--name-only"], cwd=ROOT, text=True).splitlines()
    evidence = {ARCHIVE, MODEL, oracle["pack"]}
    assert {OUT, *evidence} <= set(staged)
    recorded = {}
    for name in sorted(set(staged) - {OUT}):
        assert name == UPDATED or ("family_voice_bus" in name.lower() or "familia_bus_voz" in name.lower())
        data = git_blob(":" + name)
        assert data == (ROOT / name).read_bytes(), name
        recorded[name] = digest(data)
    retained = sum((ROOT / path).stat().st_size for path in evidence)
    assert retained <= 32 * 1024**2, retained
    return dict(schema="rf-d/h128-loaded-voice-bus/v1", passed=True, base_commit=base,
                source_sha256=recorded, inherited_inputs={path: sha(ROOT / path) for path in PREVIOUS},
                protected_public_sources=len(known), protected_private_inputs=len(private), bus_domain_v=[-1., 1.],
                stationary_reserves=len(model["validation"]), reserved_locations=6,
                loaded_branches=observed, physical_passes=0, rt_admitted=False,
                retained_receipt_bytes=retained,
                archived_receipt_sha256={name: digest(receipt_bytes(name)) for name in sorted(archive_members())})


if __name__ == "__main__":
    result = audit()
    table = AREA / TABLE
    assert set(AREA.iterdir()) == {table} and table.resolve().parent == AREA.resolve()
    table.unlink()
    result["temporary_area_empty"] = not list(AREA.iterdir())
    write(ROOT / OUT, result)
    print("H128_VOICE_BUS_QA", result["stationary_reserves"], result["loaded_branches"],
          result["retained_receipt_bytes"])
