"""Revalidate preserved VCO bank after explicit HIGH/negative duty correction."""
from dataclasses import asdict
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

import numpy as np

from vco1_circuit_reference import ROOT, sha
from vco1_circuit_probes import validate, observations, scenarios, comparison

DATA = ROOT/"evidence/vco1_circuit_convergence_v1.json.gz"
STORAGE = ROOT/"evidence/vco1_circuit_convergence_storage.json"
OUTPUT = ROOT/"evidence/vco1_circuit_validation.json"


def load():
    info = json.loads(STORAGE.read_text(encoding="utf-8"))
    packed = DATA.read_bytes()
    raw = gzip.decompress(packed)
    if hashlib.sha256(packed).hexdigest()!=info["compressed_sha256"] or hashlib.sha256(raw).hexdigest()!=info["uncompressed_sha256"]:
        raise ValueError("frozen bank archive changed")
    return json.loads(raw)


def audit(report, *, replay_private=False):
    validate(report)
    if report["source_sha256"]!=report["source_sha256_after"]:
        raise ValueError("bank source changed during measurement")
    for prefix in ("c4-10","c4-100"):
        for name,a,b in (("refinement","gear250","gear125"),("method","gear125","trap125")):
            actual=comparison(report["cases"][prefix+"-"+a]["measurements"],report["cases"][prefix+"-"+b]["measurements"])
            if actual!=report["comparisons"][prefix+"-"+name]:
                raise ValueError("comparison does not reproduce saved measurements")
    if replay_private:
        for label,scene in scenarios().items():
            work=ROOT/"references-local/vco1-circuit"/report["bank"]
            raw=work/f"{label}.txt"
            if sha(raw)!=report["cases"][label]["receipt"]["raw_export_sha256"]:
                raise ValueError("private complete trace changed")
            measured=observations(np.loadtxt(raw,skiprows=1),scene)
            if measured!=report["cases"][label]["measurements"]:
                raise ValueError("raw observations do not reproduce archived metrics")
    duties={str(i):dict(negative=report["cases"][f"pulse-{i}"]["measurements"]["pulse_negative_duty"],
                       high=1-report["cases"][f"pulse-{i}"]["measurements"]["pulse_negative_duty"]) for i in (10,11,12)}
    return dict(scenes=14,gates=report["gates"],comparisons=report["comparisons"],pulse_duties=duties,
                same_traces=True,new_solver_runs=0,raw_trace_replay=replay_private,
                original_validator_passed=report["gates_passed"],original_error=report.get("error"),
                correction="HIGH width = 1 - measured negative-state width; original failure preserved, circuit and numerical gates unchanged",
                physical_fidelity=False,native_voice=False,realtime=False)


if __name__=="__main__":
    if OUTPUT.exists():
        raise SystemExit("preserve previous validation receipt")
    paths=[DATA,STORAGE,Path(__file__),ROOT/"tools/vco1_circuit_probes.py",
           ROOT/"tools/vco1_circuit_reference.py",ROOT/"docs/VCO1_ORACULO_CIRCUITO.md"]
    before={p.relative_to(ROOT).as_posix():sha(p) for p in paths}
    start=time.perf_counter()
    receipt=dict(schema="rf-d/vco1-circuit-validation/v1",source_sha256=before,
        git_commit=subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip(),
        command=[sys.executable,"-B","tools/validate_vco1_circuit_bank.py"],passed=False)
    try:
        receipt["result"]=audit(load(),replay_private=True)
        receipt["passed"]=True
    except Exception as error:
        receipt.update(error_type=type(error).__name__,error=str(error))
        raise
    finally:
        receipt["source_sha256_after"]={p.relative_to(ROOT).as_posix():sha(p) for p in paths}
        receipt["wall_s"]=time.perf_counter()-start
        OUTPUT.write_text(json.dumps(receipt,indent=2)+"\n",encoding="utf-8",newline="\n")
    print(json.dumps(receipt["result"],indent=2))
