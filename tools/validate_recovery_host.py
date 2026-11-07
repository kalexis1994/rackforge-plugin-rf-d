"""Recompute host timing summaries and preserve the prior RF-D inventory."""

import subprocess
from pathlib import Path

import numpy as np

from affine_evidence import encode_json, recover
from check_hybrid_voice import unpack
from check_recovery_host import AREA, CAMPAIGN, COLUMNS, HOST, PRIOR, QA, calibration, fixtures, summarize
from check_recovery_cost import digest, read
from prepare_dual_chain import ROOT, sha, write

OUT = "evidence/recovery_host_tests01.json"
BASE = "12189abbb2cf6e8f625eeff4a9d0cc135c3f08ca"
ATTRIBUTES = (
    b"\n/tools/*recovery_host* -text\n"
    b"/docs/RECOVERY_HOST*.md -text\n"
    b"/evidence/recovery_host* -text\n"
)


def gap_context(raw):
    rows = np.frombuffer(raw, "<u8").reshape(-1, len(COLUMNS))
    start, wall, _, frames, _, _, _, _, _, _, setup = rows.T[:11]
    gap = np.diff(start)
    budget = frames[1:] * (1e9 / 48000)
    late = gap > 1.5 * budget
    untimed = gap.astype(np.int64) - wall[:-1].astype(np.int64)
    assert np.all(untimed >= 0)
    worst = int(np.argmax(gap / budget))
    return dict(
        elapsed_between_starts_ns=int(start[-1] - start[0]),
        nominal_current_frames_ns=float(sum(budget)),
        late_calls=int(sum(late)),
        late_with_previous_processing_in_budget=int(sum(late & (wall[:-1] <= frames[:-1] * (1e9 / 48000)))),
        worst_gap_ns=int(gap[worst]), worst_gap_frames=int(frames[worst + 1]),
        worst_gap_previous_processing_ns=int(wall[worst]),
        worst_gap_outside_previous_timed_section_ns=int(untimed[worst]),
        first_including_setup_ns=int(wall[0] + setup[0]),
        first_including_setup_over_deadline=bool(wall[0] + setup[0] > frames[0] * (1e9 / 48000)),
    )


def audit():
    prior = read(QA)
    assert prior["passed"] and not list(AREA.iterdir())
    source = dict(prior["source_sha256"])
    original_attributes = subprocess.check_output(
        ["git", "show", f"{BASE}:.gitattributes"], cwd=ROOT,
    )
    assert digest(original_attributes) == source[".gitattributes"]
    assert (ROOT / ".gitattributes").read_bytes() == original_attributes + ATTRIBUTES
    for name, expected in source.items():
        if name != ".gitattributes":
            assert sha(ROOT / name) == expected, name
    private = prior["private_input_sha256"]
    assert len(private) == 8769 and all((ROOT / name).is_file() for name in private)
    listening = prior["new_listening"]
    assert sha(ROOT / listening["path"]) == listening["sha256"]

    failures = {}
    campaigns = []
    for path in sorted((ROOT / "evidence").glob("recovery_host_*[0-9].json")):
        if path.name == Path(OUT).name:
            continue
        name = path.relative_to(ROOT).as_posix()
        report = read(name)
        snapshots = recover(report)
        if not report["passed"]:
            assert report.get("unchanged_replay") or report.get("unchanged_failure_replay")
            failures[name] = sha(path)
            continue
        assert report["columns"] == COLUMNS and report["temporary_area_empty"]
        assert report["previous_qa_sha256"] == sha(ROOT / QA)
        assert report["prior_sha256"] == sha(ROOT / PRIOR)
        assert not report["whole_voice_rt"] and not report["cost_admitted"]
        assert all(sha(Path(path)) == expected for path, expected in report["input_sha256"].items())
        for name_in_host, expected in report["host_source"].items():
            frozen = subprocess.check_output(
                ["git", "show", f"{report['host_commit']}:{name_in_host}"], cwd=HOST,
            )
            assert expected in {digest(frozen), digest(frozen.replace(b"\n", b"\r\n"))}
        for source_name, data in snapshots.items():
            if source_name != "tools/check_recovery_host.py":
                assert (ROOT / source_name).read_bytes() == data, source_name
        assert encode_json(calibration(unpack(report["calibration"]["rows"]))) == encode_json(
            report["calibration"]["medians"]
        )
        raw = unpack(report["fixtures"]["rows"])
        assert digest(raw) == report["fixtures"]["sha256"]
        assert encode_json(fixtures(raw)) == encode_json(report["fixtures"]["metrics"])
        discovery = report["endpoint_discovery"]
        assert discovery["attempts"][-1]["name"] == discovery["selected"]
        for item in discovery["attempts"][:-1]:
            assert item["exit_code"] != 0 and item["unchanged_replay"]["exit_code"] != 0
        summarize(unpack(discovery["attempts"][-1]["rows"]), "control", 16)
        sequence = [(b["mode"], b["blocks"]) for b in report["banks"]]
        assert sequence in (CAMPAIGN, CAMPAIGN[1:], [("control", 4800)])
        banks = []
        for bank in report["banks"]:
            mode, blocks = bank["mode"], bank["blocks"]
            results = []
            for run in bank["runs"]:
                raw = unpack(run["rows"])
                assert digest(raw) == run["sha256"]
                metrics = summarize(raw, mode, blocks)
                assert encode_json(metrics) == encode_json(run["metrics"])
                if mode != "native":
                    assert f"\t{discovery['selected']}\t" in run["stream"]
                    assert run["stream"].endswith(f"\t{blocks}\t0")
                results.append(dict(metrics=metrics, gap_context=gap_context(raw) if mode != "native" else None))
            assert len(results) == (2 if results[0]["metrics"]["margin_exceeded"] else 1)
            banks.append(dict(mode=mode, blocks=blocks, runs=results))
        campaigns.append(dict(report=name, sha256=sha(path), endpoint=discovery["selected"], banks=banks))
    assert len(campaigns) >= 2 and len(failures) >= 2
    staged = subprocess.check_output(["git", "diff", "--cached", "--name-only"], cwd=ROOT, text=True).splitlines()
    assert OUT in staged
    assert all(n == ".gitattributes" or "recovery_host" in n.lower() for n in staged)
    for name in set(staged) - {OUT}:
        assert name == ".gitattributes" or name not in source
        raw = subprocess.check_output(["git", "show", ":" + name], cwd=ROOT)
        assert raw == (ROOT / name).read_bytes(), name
        source[name] = digest(raw)
    source[QA] = sha(ROOT / QA)
    retained = sum((ROOT / name).stat().st_size for name in staged if name.startswith("evidence/") and name != OUT)
    assert retained <= 4 * 1024**2
    inherited = {key: value for key, value in prior.items() if not key.startswith("new_") or key == "new_listening"}
    inherited.update(
        schema="rf-d/recovery-host-latency/v1", passed=True, source_sha256=source,
        base_commit=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        previous_qa=QA, previous_qa_sha256=sha(ROOT / QA),
        protected_public_sources=len(prior["source_sha256"]), protected_private_inputs=len(private),
        experimental_recovery_cost_origin_commit=BASE,
        experimental_recovery_cost_origin_commit_pending_self_commit=False,
        experimental_recovery_host_cost_admitted=False, real_time=False,
        recovery_host_campaigns=campaigns, recovery_host_failures=failures, retained_receipt_bytes=retained,
        inherited_tests_reexecuted=False, new_unit_tests_executed=0, new_audio=False,
    )
    return inherited


if __name__ == "__main__":
    result = audit()
    write(ROOT / OUT, result)
    print("HOST_QA", len(result["source_sha256"]), len(result["recovery_host_campaigns"]),
          result["protected_private_inputs"], result["retained_receipt_bytes"])
