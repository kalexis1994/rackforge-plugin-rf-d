"""Expanded memory audit including prior window receipts and identified test versions."""
import json,sys
from pathlib import Path
from loudness_latch_bdf_static_precision_curved_reference_inputs import REPORTS as OLD_REPORTS,read,identities,validation_versions
from loudness_latch_bdf_checkout_audit import sha,git_bytes,recover_historical_input,EXPECTED_EXCEPTIONS
from loudness_latch_bdf_doubling_survey import store
from loudness_lab_metadata import environment

ROOT=Path(__file__).resolve().parents[1]
PREFIX_PATH=ROOT/"evidence/loudness_latch_bdf_static_precision_curved_prefix.json.gz"
PREFIX=read(PREFIX_PATH)
REPORTS=(*OLD_REPORTS,*(ROOT/"evidence"/name for name in (
    "loudness_latch_bdf_static_precision_curved_reference_inputs_validation.json",
    "loudness_latch_bdf_static_precision_curved_prefix.json.gz",
    "loudness_latch_bdf_static_precision_curved_prefix_validation.json")),
    *(ROOT/row['storage']['path'] for row in PREFIX['records']))
OUTPUT=ROOT/"evidence/loudness_latch_bdf_static_precision_curved_prefix_inputs.json.gz"
SUMMARY=ROOT/"evidence/loudness_latch_bdf_static_precision_curved_prefix_inputs_summary.json"


def generate():
    sys.set_int_max_str_digits(0);env=environment();ref=env["git_head"];sources={};membership={};versions=[]
    report_hashes={p.relative_to(ROOT).as_posix():sha(p.read_bytes()) for p in REPORTS}
    for p in REPORTS:
        data=read(p)
        versions.extend(v|dict(receipt=p.relative_to(ROOT).as_posix()) for v in validation_versions(data))
        for group in identities(data):
            for name,expected in group.items():
                if name in sources and sources[name]!=expected:raise ValueError("expanded input identity conflict: "+name)
                sources[name]=expected;members=membership.setdefault(name,[])
                if p.relative_to(ROOT).as_posix() not in members:members.append(p.relative_to(ROOT).as_posix())
    entries=[];archives=[]
    for name,expected in sorted(sources.items()):
        raw=(ROOT/name).read_bytes();blob=git_bytes(ref,name)
        if sha(raw)!=expected:raise ValueError("expanded frozen input mismatch: "+name)
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
        if sha((ROOT/name).read_bytes())!=expected:raise ValueError("expanded input changed during archival")
    if {p.relative_to(ROOT).as_posix():sha(p.read_bytes()) for p in REPORTS}!=report_hashes:
        raise ValueError("expanded reports changed during archival")
    own_paths=(Path(__file__).resolve(),ROOT/"tools/loudness_latch_bdf_static_precision_curved_reference_inputs.py",ROOT/"tools/loudness_latch_bdf_static_precision_signed_memory_inputs.py",ROOT/"tools/loudness_latch_bdf_static_precision_directed_prefix_inputs.py",ROOT/"tools/loudness_latch_bdf_static_precision_residual_action_inputs.py",ROOT/"tools/loudness_latch_bdf_static_precision_fine_prefix_inputs.py",ROOT/"tools/loudness_latch_bdf_static_precision_coordinate_memory_inputs.py",ROOT/"tools/loudness_latch_bdf_static_precision_certified_prefix_inputs.py",ROOT/"tools/loudness_latch_bdf_static_precision_startup_blocks_inputs.py",ROOT/"tools/loudness_latch_bdf_static_precision_startup_tube_inputs.py",ROOT/"tools/loudness_latch_bdf_static_precision_post_key_inputs.py",ROOT/"tools/loudness_latch_bdf_static_precision_key_inputs.py",ROOT/"tools/loudness_latch_bdf_static_precision_dc_inputs.py",ROOT/"tools/loudness_latch_bdf_static_precision_coverage_inputs.py",ROOT/"tools/loudness_latch_bdf_static_precision_anchor_inputs.py",ROOT/"tools/loudness_latch_bdf_static_precision_balanced_inputs.py",ROOT/"tools/loudness_latch_bdf_static_precision_directed_inputs.py",ROOT/"tools/loudness_latch_bdf_static_precision_metric_inputs.py",ROOT/"tools/loudness_latch_bdf_static_precision_modal_inputs.py",ROOT/"tools/loudness_latch_bdf_static_precision_spectral_inputs.py",ROOT/"tools/loudness_latch_bdf_static_precision_junction_inputs.py",ROOT/"tools/loudness_latch_bdf_static_precision_block_inputs.py",ROOT/"tools/loudness_latch_bdf_static_precision_cell_inputs.py",ROOT/"tools/loudness_latch_bdf_static_precision_weighted_inputs.py",ROOT/"tools/loudness_latch_bdf_static_precision_descriptor_inputs.py",ROOT/"tools/loudness_latch_bdf_static_precision_correlated_inputs.py",ROOT/"tools/loudness_latch_bdf_static_precision_constitutive_inputs.py",ROOT/"tools/loudness_latch_bdf_static_precision_enclosure_inputs.py",ROOT/"tools/loudness_latch_bdf_static_precision_balance_inputs.py",ROOT/"tools/loudness_latch_bdf_static_precision_dense_inputs.py",ROOT/"tools/loudness_latch_bdf_static_precision_continuous_inputs.py",ROOT/"tools/loudness_latch_bdf_static_precision_charge_inputs.py",ROOT/"tools/loudness_latch_bdf_static_precision_forced_inputs.py",ROOT/"tools/loudness_latch_bdf_static_precision_memory_quadratic_inputs.py",ROOT/"tools/loudness_latch_bdf_static_precision_memory_response_inputs.py",
        ROOT/"tools/loudness_latch_bdf_static_precision_memory_inputs.py",
        ROOT/"tools/loudness_latch_bdf_static_precision_path_inputs.py",
        ROOT/"tools/loudness_latch_bdf_static_precision_window_inputs.py",
        ROOT/"tools/loudness_latch_bdf_checkout_audit.py")
    return dict(schema="rf-d/bdf-static-curved-prefix-inputs/v1",environment=env,reference_git_head=ref,integer_text_limit_during=0,
        entries=entries,archived_inputs=archives,archived_validation_test_versions=versions,
        source_sha256=report_hashes|{p.relative_to(ROOT).as_posix():sha(p.read_bytes()) for p in own_paths},
        original_direct_blob_comparison_passed=False,all_differences_declared_crlf_expansion=True,
        prior_reports_modified=False,input_files_modified=False,numerical_experiment_repeated=False,
        numerical_gates_changed=False,audio_admitted=False)


def save(report):
    if OUTPUT==SUMMARY or OUTPUT in REPORTS or SUMMARY in REPORTS:raise ValueError("output/input destination collision")
    storage=store(report,OUTPUT)
    summary={k:v for k,v in report.items() if k not in ("archived_inputs","archived_validation_test_versions")}|dict(storage=storage,
        archived_inputs=[{k:v for k,v in r.items() if k!="working_copy_source_utf8"} for r in report["archived_inputs"]],
        archived_validation_test_versions=[{k:v for k,v in r.items() if k!="source_utf8"}
            for r in report["archived_validation_test_versions"]])
    SUMMARY.write_text(json.dumps(summary,indent=2,allow_nan=False)+"\n",encoding="utf-8",newline="\n")
    return summary


if __name__=="__main__":
    result=save(generate());print(json.dumps(dict(inputs=len(result["entries"]),archives=len(result["archived_inputs"]),
        test_versions=len(result["archived_validation_test_versions"]),storage=result["storage"])))
