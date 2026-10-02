"""Archive exact materialized input exceptions for the expanded static audit."""
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
from loudness_latch_bdf_checkout_audit import recover_historical_input
from loudness_latch_bdf_doubling_survey import store
from loudness_lab_metadata import environment

ROOT=Path(__file__).resolve().parents[1]
REPORTS=tuple(ROOT/"evidence"/name for name in (
    "loudness_latch_bdf_static_precision.json.gz","loudness_latch_bdf_static_precision_binary.json.gz"))
OUTPUT=ROOT/"evidence/loudness_latch_bdf_static_precision_inputs.json.gz"
SUMMARY=ROOT/"evidence/loudness_latch_bdf_static_precision_inputs_summary.json"


def sha(raw):return hashlib.sha256(raw).hexdigest()


def generate():
    env=environment();ref=env["git_head"];sources={};membership={}
    identities={p.relative_to(ROOT).as_posix():sha(p.read_bytes()) for p in REPORTS}
    for report in REPORTS:
        data=json.loads(gzip.decompress(report.read_bytes()))
        for name,expected in data["source_sha256"].items():
            if name in sources and sources[name]!=expected:raise ValueError("input reports disagree about source bytes")
            sources[name]=expected;membership.setdefault(name,[]).append(report.relative_to(ROOT).as_posix())
    entries=[];archives=[]
    for name,expected in sorted(sources.items()):
        raw=(ROOT/name).read_bytes()
        if sha(raw)!=expected:raise ValueError("frozen input SHA mismatch: "+name)
        blob=subprocess.run(["git","show",f"{ref}:{name}"],cwd=ROOT,check=True,capture_output=True).stdout
        row=dict(path=name,working_copy_sha256=expected,git_blob_sha256=sha(blob),
                 identical_bytes=blob==raw,frozen_reports=membership[name])
        if blob!=raw:
            if not name.endswith(".json"):raise ValueError("undeclared non-JSON materialization difference: "+name)
            archive=row|dict(working_copy_source_utf8=raw.decode("utf-8"),working_copy_bytes=len(raw),
                git_blob_bytes=len(blob),declared_transform="LF-to-CRLF-only",canonical_json_identical=True)
            if recover_historical_input(blob,archive)!=raw:raise ValueError("historical input reconstruction failed")
            archives.append(archive)
        entries.append(row)
    for name,expected in sources.items():
        if sha((ROOT/name).read_bytes())!=expected:raise ValueError("input changed during archival")
    if {p.relative_to(ROOT).as_posix():sha(p.read_bytes()) for p in REPORTS}!=identities:
        raise ValueError("numerical reports changed during archival")
    return dict(schema="rf-d/bdf-static-inputs/v1",environment=env,reference_git_head=ref,entries=entries,
        archived_inputs=archives,source_sha256=identities|{
            Path(__file__).relative_to(ROOT).as_posix():sha(Path(__file__).read_bytes()),
            "tools/loudness_latch_bdf_checkout_audit.py":sha((ROOT/"tools/loudness_latch_bdf_checkout_audit.py").read_bytes())},
        original_direct_blob_comparison_passed=not archives,
        all_differences_declared_crlf_expansion=True,prior_reports_modified=False,input_files_modified=False,
        numerical_experiment_repeated=False,numerical_gates_changed=False,audio_admitted=False)


def save(report):
    storage=store(report,OUTPUT)
    summary={k:v for k,v in report.items() if k!="archived_inputs"}|dict(storage=storage,
        archived_inputs=[{k:v for k,v in row.items() if k!="working_copy_source_utf8"} for row in report["archived_inputs"]])
    SUMMARY.write_text(json.dumps(summary,indent=2,allow_nan=False)+"\n",encoding="utf-8",newline="\n")
    return summary


if __name__=="__main__":
    result=save(generate())
    print(json.dumps(dict(inputs=len(result["entries"]),archived_inputs=len(result["archived_inputs"]),storage=result["storage"])))
