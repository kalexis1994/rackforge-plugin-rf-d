"""Preserve every fine prefix validation attempt and its exact sources."""
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from time import perf_counter
from loudness_lab_metadata import environment
from loudness_latch_bdf_static_precision_directed_prefix import OUTPUT as DATA,SUMMARY as DATA_SUMMARY,PATHS

ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/"evidence/loudness_latch_bdf_static_precision_directed_prefix_validation.json"
SUITES=(("test_loudness_latch_directed_prefix.py",10),)


def generate():
    tests=[ROOT/"tests"/name for name,_ in SUITES]
    paths=tuple(dict.fromkeys((*PATHS,DATA,DATA_SUMMARY,*tests,
                             Path(__file__).resolve(),ROOT/".gitattributes",ROOT/"evidence/.gitattributes")))
    def snapshots():
        return {p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    before=snapshots();env=environment();results=[]
    for (name,expected),path in zip(SUITES,tests):
        command=[sys.executable,"-B","-m","unittest","discover","-s","tests","-p",name,"-v"]
        print(json.dumps(dict(validation_suite=name,status="started")),flush=True);started=perf_counter()
        run=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,encoding="utf-8")
        counts=re.findall(r"Ran (\d+) tests? in ([\d.]+)s",run.stderr)
        count=int(counts[-1][0]) if counts else None
        passed=run.returncode==0 and count==expected and "\nOK\n" in run.stderr
        row=dict(command=command,expected_tests=expected,reported_tests=count,exit_code=run.returncode,
            wall_s=perf_counter()-started,passed=passed,stdout=run.stdout,stderr=run.stderr,
            test_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        if not passed:row["failed_test_source_utf8"]=path.read_text(encoding="utf-8")
        results.append(row);print(json.dumps(dict(validation_suite=name,passed=passed,tests=count,wall_s=row["wall_s"])),flush=True)
    after=snapshots();unchanged=before==after
    attempt=dict(timestamp_utc=datetime.now(timezone.utc).isoformat(),environment=env,
        source_sha256_before=before,source_sha256_after=after,inputs_unchanged=unchanged,
        suites=results,passed=unchanged and all(r["passed"] for r in results))
    report=json.loads(OUTPUT.read_text(encoding="utf-8")) if OUTPUT.exists() else dict(
        schema="rf-d/bdf-static-directed-prefix-validation/v1",attempts=[])
    report["attempts"].append(attempt)
    OUTPUT.write_text(json.dumps(report,indent=2,allow_nan=False)+"\n",encoding="utf-8",newline="\n")
    return attempt


if __name__=="__main__":sys.exit(0 if generate()["passed"] else 1)
