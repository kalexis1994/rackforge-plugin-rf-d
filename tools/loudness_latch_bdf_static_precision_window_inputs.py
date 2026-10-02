"""Reconstruct frozen window/continuation inputs and their validation inputs."""
import gzip
import json
from pathlib import Path
from loudness_latch_bdf_checkout_audit import recover_historical_input,git_bytes,sha,EXPECTED_EXCEPTIONS
from loudness_latch_bdf_doubling_survey import store
from loudness_lab_metadata import environment

ROOT=Path(__file__).resolve().parents[1]
REPORTS=tuple(ROOT/"evidence"/name for name in (
    "loudness_latch_bdf_static_precision_windows.json.gz",
    "loudness_latch_bdf_static_precision_continuation.json.gz",
    "loudness_latch_bdf_static_precision_windows_validation.json",
    "loudness_latch_bdf_static_precision_continuation_validation.json"))
OUTPUT=ROOT/"evidence/loudness_latch_bdf_static_precision_window_inputs.json.gz"
SUMMARY=ROOT/"evidence/loudness_latch_bdf_static_precision_window_inputs_summary.json"


def validation_versions(data):
    """Recover an earlier test version only from its identified failed receipt."""
    if "attempts" not in data:return []
    latest=data["attempts"][-1]["source_sha256_before"];versions=[]
    for index,attempt in enumerate(data["attempts"]):
        if attempt["source_sha256_before"]!=attempt["source_sha256_after"]:
            raise ValueError("validation inputs changed: retain separately before archival")
        for name,expected in attempt["source_sha256_before"].items():
            if latest.get(name)==expected:continue
            matches=[]
            for suite in attempt["suites"]:
                command=suite["command"]
                if "-p" not in command:continue
                test_name="tests/"+command[command.index("-p")+1]
                source=suite.get("failed_test_source_utf8")
                if name==test_name and expected==suite["test_sha256"] and source is not None:
                    if sha(source.encode("utf-8"))!=expected:raise ValueError("failed test source identity mismatch")
                    matches.append(dict(path=name,source_sha256=expected,source_utf8=source,
                        attempt_index=index,command=command))
            if len(matches)!=1:raise ValueError("unidentified prior validation input: "+name)
            versions.extend(matches)
    return versions


def identities(data):
    if "source_sha256" in data:return [data["source_sha256"]]
    versions=validation_versions(data)
    excluded={(v["attempt_index"],v["path"]):v["source_sha256"] for v in versions}
    result=[]
    for index,attempt in enumerate(data["attempts"]):
        result.append({name:expected for name,expected in attempt["source_sha256_before"].items()
            if (index,name) not in excluded})
    return result


def read(path):
    raw=path.read_bytes()
    return json.loads(gzip.decompress(raw) if path.suffix==".gz" else raw)


def generate():
    env=environment();ref=env["git_head"];sources={};membership={};versions=[]
    report_hashes={p.relative_to(ROOT).as_posix():sha(p.read_bytes()) for p in REPORTS}
    for p in REPORTS:
        data=read(p)
        versions.extend(v|dict(receipt=p.relative_to(ROOT).as_posix()) for v in validation_versions(data))
        for group in identities(data):
            for name,expected in group.items():
                if name in sources and sources[name]!=expected:raise ValueError("input identity conflict: "+name)
                sources[name]=expected
                members=membership.setdefault(name,[])
                if p.relative_to(ROOT).as_posix() not in members:members.append(p.relative_to(ROOT).as_posix())
    entries=[];archives=[]
    for name,expected in sorted(sources.items()):
        raw=(ROOT/name).read_bytes();blob=git_bytes(ref,name)
        if sha(raw)!=expected:raise ValueError("frozen input mismatch: "+name)
        row=dict(path=name,working_copy_sha256=expected,git_blob_sha256=sha(blob),
            identical_bytes=raw==blob,frozen_reports=membership[name])
        if raw!=blob:
            if name not in EXPECTED_EXCEPTIONS:raise ValueError("undeclared materialization difference: "+name)
            archive=row|dict(working_copy_source_utf8=raw.decode("utf-8"),working_copy_bytes=len(raw),
                git_blob_bytes=len(blob),declared_transform="LF-to-CRLF-only",canonical_json_identical=True)
            if recover_historical_input(blob,archive)!=raw:raise ValueError("failed historical reconstruction")
            archives.append(archive)
        entries.append(row)
    if tuple(v["path"] for v in archives)!=EXPECTED_EXCEPTIONS:raise ValueError("historical exception set changed")
    for name,expected in sources.items():
        if sha((ROOT/name).read_bytes())!=expected:raise ValueError("input changed during archival")
    if {p.relative_to(ROOT).as_posix():sha(p.read_bytes()) for p in REPORTS}!=report_hashes:
        raise ValueError("reports changed during archival")
    return dict(schema="rf-d/bdf-static-window-inputs/v1",environment=env,reference_git_head=ref,
        entries=entries,archived_inputs=archives,archived_validation_test_versions=versions,source_sha256=report_hashes|{
            Path(__file__).relative_to(ROOT).as_posix():sha(Path(__file__).read_bytes()),
            "tools/loudness_latch_bdf_checkout_audit.py":sha((ROOT/"tools/loudness_latch_bdf_checkout_audit.py").read_bytes())},
        original_direct_blob_comparison_passed=False,all_differences_declared_crlf_expansion=True,
        prior_reports_modified=False,input_files_modified=False,numerical_experiment_repeated=False,
        numerical_gates_changed=False,audio_admitted=False)


def save(report):
    storage=store(report,OUTPUT)
    summary={k:v for k,v in report.items() if k not in ("archived_inputs","archived_validation_test_versions")}|dict(storage=storage,
        archived_inputs=[{k:v for k,v in r.items() if k!="working_copy_source_utf8"} for r in report["archived_inputs"]],
        archived_validation_test_versions=[{k:v for k,v in r.items() if k!="source_utf8"}
            for r in report["archived_validation_test_versions"]])
    SUMMARY.write_text(json.dumps(summary,indent=2,allow_nan=False)+"\n",encoding="utf-8",newline="\n")
    return summary


if __name__=="__main__":
    result=save(generate())
    print(json.dumps(dict(inputs=len(result["entries"]),archives=len(result["archived_inputs"]),storage=result["storage"])))
