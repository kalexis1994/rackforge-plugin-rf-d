"""Two-trim laboratory calibration of the solved VCO, not a MIDI mapping.

B-TUNE table 5-3 uses 220/1760 Hz over three octaves and iterates frequency
and scale trims. Here board CVs are explicit laboratory boundaries; no real
panel setup or vintage trim position is claimed.
"""
from dataclasses import replace
import argparse
import json
import math
from pathlib import Path
import subprocess

import numpy as np

from vco1_circuit_reference import ROOT, Scenario, run, sha
from vco1_circuit_probes import observations

TARGETS=(220.0,1760.0)
KEYBOARD=(-3.1,-.1)
GATES=dict(endpoint_cents=.1,reserved_note_cents=5.0,maximum_iterations=5)


def bounded_update(x, delta):
    proposed=np.asarray(x)+np.asarray(delta)
    if proposed.shape!=(2,) or not np.isfinite(proposed).all() or np.any(proposed<0) or np.any(proposed>1):
        raise ValueError("calibration leaves documented trim tracks")
    return proposed


def validate(report):
    if report["gates"]!=GATES or report["targets_hz"]!=list(TARGETS) or report["keyboard_endpoints_v"]!=list(KEYBOARD):
        raise ValueError("calibration contract changed")
    if not 0<=report["r11_active_ohm"]<=1000 or not 0<=report["r8_fraction"]<=1:
        raise ValueError("invalid trim result")
    if set(report["verification"])!={"low","middle1","middle2","high"}:
        raise ValueError("four final reserved scenes required")
    for label,index in (("low",0),("middle1",1),("middle2",2),("high",3)):
        case=report["verification"][label]
        expected=220*2**index
        error=abs(1200*math.log2(case["measurements"]["frequency_hz"]/expected))
        limit=GATES["endpoint_cents"] if index in (0,3) else GATES["reserved_note_cents"]
        if error>limit or error!=case["error_cents"]:
            raise ValueError("pitch gate failed")
        scene=case["receipt"]["scenario"]
        if scene["keyboard_v"]!=KEYBOARD[0]+index or scene["r11_active_ohm"]!=report["r11_active_ohm"] or scene["r8_fraction"]!=report["r8_fraction"] or scene["max_step_s"]!=125e-9:
            raise ValueError("final scene changed")
        if not case["receipt"]["trajectory_complete"] or case["receipt"]["source_sha256"]!=case["receipt"]["source_sha256_after"]:
            raise ValueError("invalid final solver trace")


def generate(bank):
    work=ROOT/"references-local/vco1-circuit"/bank
    if work.exists(): raise ValueError("preserve previous calibration bank")
    work.mkdir(parents=True)
    exe=ROOT/"references-local/ngspice46/runtime/Spice64/bin/ngspice_con.exe"
    base=Scenario(duration_s=.03)
    report=dict(schema="rf-d/vco1-circuit-calibration/v1",bank=bank,gates=GATES,
        targets_hz=list(TARGETS),keyboard_endpoints_v=list(KEYBOARD),trials=[],verification={},passed=False,
        source_sha256={p.relative_to(ROOT).as_posix():sha(p) for p in (Path(__file__),ROOT/"docs/VCO1_CALIBRACION_PROTOCOLO.md")},
        git_commit=subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip(),
        scope="Documentary nominal two-trim calibration with laboratory CVs; not real front-panel setup, MIDI law or physical tuning")
    counter=0

    def evaluate(x, voltages=KEYBOARD, step=500e-9):
        nonlocal counter
        cases=[]
        for cv in voltages:
            scene=replace(base,r11_active_ohm=float(x[0]*1000),r8_fraction=float(x[1]),keyboard_v=cv,max_step_s=step)
            raw,receipt=run(scene,f"trial-{counter:03d}",work,exe)
            counter+=1
            metrics=observations(raw,scene)
            case=dict(receipt=receipt,measurements=metrics)
            cases.append(case);report["trials"].append(case)
            (work/"partial-report.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8",newline="\n")
            print(json.dumps(dict(trial=counter,cv=cv,r11=scene.r11_active_ohm,r8=scene.r8_fraction,f=metrics["frequency_hz"])),flush=True)
        return cases

    def residual(cases):
        return np.log([c["measurements"]["frequency_hz"]/f for c,f in zip(cases,TARGETS)])

    try:
        x=np.array([.55,.31])
        cases=evaluate(x);f=residual(cases)
        jacobian=np.empty((2,2))
        for column,step in enumerate((.005,.01)):
            perturbed=x.copy();perturbed[column]+=step
            jacobian[:,column]=(residual(evaluate(perturbed))-f)/step
        for iteration in range(GATES["maximum_iterations"]):
            if np.max(np.abs(f))*1200/math.log(2)<=GATES["endpoint_cents"]:
                break
            delta=np.linalg.solve(jacobian,-f)
            proposed=bounded_update(x,delta)
            next_f=residual(evaluate(proposed))
            if np.linalg.norm(next_f)>=np.linalg.norm(f):
                raise ValueError("calibration update did not improve both-point residual norm")
            # Reuse a secant Jacobian; no change to any physical device parameter.
            jacobian+=np.outer(next_f-f-jacobian@delta,delta)/(delta@delta)
            x,f=proposed,next_f
        else:
            raise ValueError("calibration iteration budget exhausted")
        report.update(r11_active_ohm=float(x[0]*1000),r8_fraction=float(x[1]))
        verification=evaluate(x,voltages=tuple(KEYBOARD[0]+i for i in range(4)),step=125e-9)
        for i,(label,case) in enumerate(zip(("low","middle1","middle2","high"),verification)):
            case["error_cents"]=abs(1200*math.log2(case["measurements"]["frequency_hz"]/(220*2**i)))
            report["verification"][label]=case
        validate(report)
        report["passed"]=True
    except Exception as error:
        report.update(error_type=type(error).__name__,error=str(error))
        raise
    finally:
        report["source_sha256_after"]={p:sha(ROOT/p) for p in report["source_sha256"]}
        (work/"report.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8",newline="\n")
    return report


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--bank",required=True)
    args=p.parse_args()
    if not args.bank or any(c not in "abcdefghijklmnopqrstuvwxyz0123456789_-" for c in args.bank): p.error("safe fresh name required")
    r=generate(args.bank)
    print(json.dumps(dict(passed=r["passed"],r11_active_ohm=r["r11_active_ohm"],r8_fraction=r["r8_fraction"],verification={k:dict(f=v["measurements"]["frequency_hz"],error_cents=v["error_cents"]) for k,v in r["verification"].items()}),indent=2))
