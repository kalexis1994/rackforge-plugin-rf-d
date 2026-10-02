"""Archive historical checkout bytes without editing their frozen evidence."""
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
from loudness_lab_metadata import environment
from loudness_latch_bdf_doubling_survey import canonical, store

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "evidence/loudness_latch_bdf_checkout_audit.json.gz"
SUMMARY = ROOT / "evidence/loudness_latch_bdf_checkout_audit_summary.json"
REPORTS = tuple(ROOT / "evidence" / name for name in (
    "loudness_latch_bdf_memory_windows.json.gz",
    "loudness_latch_bdf_memory_fd_audit.json.gz",
    "loudness_latch_bdf_fd_sensitivity.json.gz"))
EXPECTED_EXCEPTIONS = (
    "evidence/loudness_contour_graph.json",
    "evidence/loudness_latch_bdf_doubling_probes.json",
    "evidence/loudness_latch_rejection_audit.json")


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def git_bytes(ref, name):
    return subprocess.run(["git", "show", f"{ref}:{name}"], cwd=ROOT,
        check=True, capture_output=True).stdout


def recover_historical_input(blob, archived):
    """Return exact frozen bytes only for an identified Git blob, never arbitrary normalization."""
    raw = archived["working_copy_source_utf8"].encode("utf-8")
    if sha(raw) != archived["working_copy_sha256"]:
        raise ValueError("archived working bytes do not match their identity")
    if sha(blob) != archived["git_blob_sha256"]:
        raise ValueError("historical Git blob identity mismatch")
    if b"\r" in blob or blob.replace(b"\n", b"\r\n") != raw:
        raise ValueError("historical difference is not the declared LF to CRLF expansion")
    if canonical(json.loads(blob)) != canonical(json.loads(raw)):
        raise ValueError("line ending reconstruction changed canonical JSON")
    return raw


def generate():
    env = environment(); ref = env["git_head"]
    report_hashes = {p.relative_to(ROOT).as_posix(): sha(p.read_bytes()) for p in REPORTS}
    sources = {}; membership = {}
    for path in REPORTS:
        data = json.loads(gzip.decompress(path.read_bytes()))
        for name, expected in data["source_sha256"].items():
            if name in sources and sources[name] != expected:
                raise ValueError("frozen reports disagree about input bytes")
            sources[name] = expected
            membership.setdefault(name, []).append(path.relative_to(ROOT).as_posix())
    entries = []; exceptions = []
    for name, expected in sorted(sources.items()):
        raw = (ROOT / name).read_bytes(); blob = git_bytes(ref, name)
        if sha(raw) != expected:
            raise ValueError(f"current input differs from frozen SHA: {name}")
        row = dict(path=name, working_copy_sha256=expected, git_blob_sha256=sha(blob),
            identical_bytes=blob == raw, frozen_reports=membership[name])
        if raw != blob:
            archive = row | dict(working_copy_source_utf8=raw.decode("utf-8"),
                working_copy_bytes=len(raw), git_blob_bytes=len(blob),
                declared_transform="LF-to-CRLF-only", canonical_json_identical=True)
            if recover_historical_input(blob, archive) != raw:
                raise ValueError("archived historical input must restore exactly")
            exceptions.append(archive)
        entries.append(row)
    if tuple(r["path"] for r in exceptions) != EXPECTED_EXCEPTIONS:
        raise ValueError("unexpected historical checkout differences; no automatic promotion")
    if {p.relative_to(ROOT).as_posix(): sha(p.read_bytes()) for p in REPORTS} != report_hashes:
        raise ValueError("frozen reports changed during checkout audit")
    for name, expected in sources.items():
        if sha((ROOT / name).read_bytes()) != expected:
            raise ValueError("input changed during checkout audit")
    return dict(schema="rf-d/bdf-checkout-audit/v1", environment=env,reference_git_head=ref,
        source_sha256=report_hashes | {Path(__file__).relative_to(ROOT).as_posix(): sha(Path(__file__).read_bytes())},
        original_direct_blob_comparison_passed=False,
        original_direct_blob_mismatches=[r["path"] for r in exceptions],
        entries=entries, archived_inputs=exceptions,all_differences_declared_crlf_expansion=True,
        prior_reports_modified=False,input_files_modified=False,numerical_experiment_repeated=False,
        numerical_gates_changed=False,audio_admitted=False)


def save(report):
    storage = store(report, OUTPUT)
    summary = {k:v for k,v in report.items() if k != "archived_inputs"} | dict(storage=storage,
        archived_inputs=[{k:v for k,v in row.items() if k != "working_copy_source_utf8"}
            for row in report["archived_inputs"]])
    SUMMARY.write_text(json.dumps(summary,indent=2,allow_nan=False)+"\n",encoding="utf-8",newline="\n")
    return summary


if __name__ == "__main__":
    result = save(generate())
    print(json.dumps(dict(inputs=len(result["entries"]),archived_inputs=len(result["archived_inputs"]),
        original_direct_blob_comparison_passed=result["original_direct_blob_comparison_passed"],
        exact_reconstruction_verified=True,storage=result["storage"])))
