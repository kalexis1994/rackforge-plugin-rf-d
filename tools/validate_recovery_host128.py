"""Audit exact driver sample steps, startup evidence and profile restoration."""

import subprocess
import winreg
from pathlib import Path

from affine_evidence import encode_json, recover
from check_hybrid_voice import unpack
from check_recovery_cost import digest, read
from check_recovery_host128 import (
    AREA, ASIO_DRIVER, ASIO_PLAN, BASE, HOST, PROBE, QA, REALTIME,
    analyze_asio, asio_profile, fixtures, read_override,
)
from prepare_dual_chain import ROOT, sha, write

OUT = "evidence/recovery_host128_tests01.json"


def receipt(number):
    return f"evidence/recovery_host128_native{number:02d}.json"


def audit():
    prior = read(QA)
    assert prior["passed"] and not list(AREA.iterdir())
    sources = dict(prior["source_sha256"])
    for name, expected in sources.items():
        assert sha(ROOT / name) == expected, name
    private = prior["private_input_sha256"]
    assert len(private) == 8769 and all((ROOT / name).is_file() for name in private)
    assert sha(ROOT / prior["new_listening"]["path"]) == prior["new_listening"]["sha256"]

    reports = {n: read(receipt(n)) for n in range(1, 12)}
    for n, r in reports.items():
        snapshots = recover(r)
        assert r["temporary_area_empty"] and r["previous_qa_sha256"] == sha(ROOT / QA)
        assert all(sha(Path(p)) == expected for p, expected in r["input_sha256"].items())
        host_source = subprocess.check_output(
            ["git", "show", f"{r['host_commit']}:{REALTIME}"], cwd=HOST,
        )
        assert r["host_source_sha256"] in {digest(host_source), digest(host_source.replace(b"\n", b"\r\n"))}
        if r["passed"]:
            assert not r["whole_voice_rt"] and not r["physical_128_admitted"]
            raw = unpack(r["fixtures"]["rows"])
            assert digest(raw) == r["fixtures"]["sha256"]
            assert encode_json(fixtures(raw)) == encode_json(r["fixtures"]["metrics"])
        elif n in (1, 2, 9):
            original, replay = r["failed_output"], r["unchanged_failure_replay"]
            assert original["exit_code"] == replay["exit_code"] == 1
            token = {1: b"E0432", 2: b"E0745", 9: b"did not read back"}[n]
            assert token in unpack(original["stderr"]) and token in unpack(replay["stderr"])
        elif n in (6, 7):
            assert "FileNotFoundError" in r["failure"]
            assert r["source_sha256"] == reports[6]["source_sha256"]
        else:
            raise AssertionError(f"Unexpected failure in receipt {n}")
        if n == 11:
            for name, raw in snapshots.items():
                assert raw == (ROOT / name).read_bytes(), name

    discovery = reports[4]["discovery"]
    assert encode_json(discovery[0]) == encode_json(discovery[1])
    fields = [row.split("\t") for row in discovery[0]]
    periods = [row for row in fields if row[0] == "PERIODS"]
    exclusive = [row for row in fields if row[0] == "EXCLUSIVE"]
    assert len(periods) == 7 and all(row[3] == "48000" and row[5:10] == ["480"]*4 + ["false"] for row in periods)
    assert len(exclusive) == 4 and all(row[3] == "30000" for row in exclusive)

    queries = reports[5]["asio_queries"]
    for name, pair in queries.items():
        assert encode_json(pair[0]) == encode_json(pair[1]), name
    original = queries[ASIO_DRIVER][0]["stdout"].strip().split("\t")
    assert original[2] == "44100" and original[5:] == ["64", "2048", "512", "8", "0"]
    confirmed = reports[11]
    restored = reports[10]["asio_preference_restoration"]
    assert restored["previous_value"] == 128 and restored["restored_value"] == 0
    assert restored["verified"].split("\t") == original
    profile = asio_profile(AREA / "recovery-host128.exe")
    assert profile.endswith("\\C1EA3620") and read_override(profile) == (0, winreg.REG_DWORD)
    assert confirmed["asio_preference_restoration"]["before"].split("\t") == original
    assert confirmed["asio_preference_restoration"]["verified"].split("\t") == original
    assert confirmed["asio_preference_restoration"]["observed_value"] == 128
    assert confirmed["asio_preference_restoration"]["original_value"] == 0

    for n in (8, 11):
        r = reports[n]
        assert [(bank["mode"], bank["blocks"]) for bank in r["asio_banks"]] == ASIO_PLAN
        first_pass = []
        for bank in r["asio_banks"]:
            runs = bank["runs"]
            for run in runs:
                raw = unpack(run["rows"])
                assert run["exit_code"] == 0 and digest(raw) == run["sha256"]
                metrics = analyze_asio(raw, run["stream"], bank["mode"], bank["blocks"])
                assert metrics["frames_128_confirmed"]
                assert encode_json(metrics) == encode_json(run["metrics"])
            first = runs[0]["metrics"]
            assert len(runs) == (1 if first["gate_passed"] else 2)
            first_pass.append(first["gate_passed"])
        assert r["asio_128_admitted"] == all(first_pass)
    assert not reports[8]["asio_128_admitted"]
    assert reports[8]["asio_banks"][0]["runs"][0]["metrics"]["notices"] == 8
    assert confirmed["asio_128_admitted"]

    staged = subprocess.check_output(["git", "diff", "--cached", "--name-only"], cwd=ROOT, text=True).splitlines()
    assert OUT in staged and all("recovery_host128" in name.lower() for name in staged)
    for name in set(staged) - {OUT}:
        assert name not in sources
        raw = subprocess.check_output(["git", "show", ":" + name], cwd=ROOT)
        assert raw == (ROOT / name).read_bytes(), name
        sources[name] = digest(raw)
    sources[QA] = sha(ROOT / QA)
    retained = sum((ROOT / name).stat().st_size for name in staged if name.startswith("evidence/") and name != OUT)
    assert retained <= 4 * 1024**2
    result = {key: value for key, value in prior.items() if not key.startswith("new_") or key == "new_listening"}
    result.update(
        schema="rf-d/recovery-host-effective-128/v1", passed=True, base_commit=BASE,
        source_sha256=sources, previous_qa=QA, previous_qa_sha256=sha(ROOT / QA),
        protected_public_sources=len(prior["source_sha256"]), protected_private_inputs=len(private),
        asio_128_confirmed=True, first_campaign_startup_notice_preserved=True,
        asio_confirmed_banks=[dict(mode=bank["mode"], blocks=bank["blocks"], metrics=bank["runs"][0]["metrics"])
                              for bank in confirmed["asio_banks"]],
        asio_preference_restored=True, rackforge_plugin_engine_measured=False,
        whole_voice_rt=False, real_time=False, inherited_tests_reexecuted=False,
        new_unit_tests_executed=0, new_audio=False, retained_receipt_bytes=retained,
        recovery_host128_reports={receipt(n): sha(ROOT / receipt(n)) for n in reports},
    )
    return result


if __name__ == "__main__":
    result = audit()
    write(ROOT / OUT, result)
    print("HOST128_QA", len(result["source_sha256"]), result["protected_private_inputs"],
          result["retained_receipt_bytes"], result["asio_128_confirmed"])
