"""Temporal closure of loaded BJT subset against separately integrated ngspice."""
from dataclasses import asdict
import argparse
import hashlib
import gzip
import json
import math
from pathlib import Path
import subprocess
import shutil
import numpy as np
from bjt_loaded_transient_reference import Circuit,PWL,input_voltage
from bjt_charge_ngspice_probes import model_card,model_parameters,EXPECTED_EXE_SHA256
from loudness_lab_metadata import environment

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT/"evidence/bjt_loaded_transient_probes.json"
GATES = dict(native_node_error_v=2e-3,independent_refinement_error_v=2e-4,
             fine_over_coarse_error=.3,max_kcl_a=1e-12,correction_v=1e-9)
OBSERVATION_S = np.arange(501,dtype=float)*4e-9
OBSERVATION_S[-1] = PWL[-1][0]


def transient_deck(p,max_step,output):
    if any(ch.isspace() or ch in '\";$' for ch in output.as_posix()):
        raise ValueError("wrdata harness requires output path without spaces/control characters")
    pulse = " ".join(f"{t:.17g} {p.polarity*v:.17g}" for t,v in PWL)
    return "\n".join(["RF-D synthetic loaded BJT transient",
        f"vin input 0 pwl({pulse})",f"vs supply 0 {5*p.polarity}","rb input b 10k","rc supply c 3.3k","re e 0 1k",
        "q1 c b e m",model_card(p),
        ".options temp=25 tnom=25 gmin=0 method=gear maxord=1 reltol=1e-6 abstol=1e-14 vntol=1e-9 trtol=7",
        ".save v(b) v(c) v(e) @q1[qbe] @q1[qbc]",
        ".control","set numdgt=17","set wr_singlescale","set wr_vecnames",
        f"tran {max_step:.17g} {PWL[-1][0]:.17g} 0 {max_step:.17g}",
        f"wrdata {output.as_posix()} v(b) v(c) v(e) @q1[qbe] @q1[qbc]","quit",".endc",".end",""])


def run_independent(executable,p,h,work,label):
    output = work/f"{label}-{h:.3e}.txt"
    if output.exists():
        output.unlink()
    text = transient_deck(p,h,output)
    deck = work/f"{label}-{h:.3e}.cir"
    deck.write_text(text,encoding="utf-8")
    run = subprocess.run([str(executable),"-n","-b",str(deck)],cwd=executable.parent,capture_output=True,text=True,timeout=60)
    (work/f"{label}-{h:.3e}.log").write_text(run.stdout+run.stderr,encoding="utf-8")
    if run.returncode or any(w in (run.stdout+run.stderr).lower() for w in ("error", "aborted", "timestep too small")):
        raise ValueError("independent transient failed; inspect ignored log")
    raw = np.loadtxt(output,skiprows=1,ndmin=2)
    if raw.shape[1]!=6 or not np.isfinite(raw).all() or np.any(np.diff(raw[:,0])<=0):
        raise ValueError("finite increasing transient time and five state exports required")
    if raw[0,0]!=0 or raw[-1,0]<PWL[-1][0]-1e-18 or np.max(np.diff(raw[:,0]))>h*(1+1e-7):
        raise ValueError("complete independent time domain at declared maximum step required")
    observed = np.column_stack([np.interp(OBSERVATION_S,raw[:,0],raw[:,k]) for k in range(1,6)])
    raw_hash = hashlib.sha256(output.read_bytes()).hexdigest()
    # Preserve full simulator data, compressed, after complete export validation.
    with output.open("rb") as source,gzip.open(output.with_suffix(".txt.gz"),"wb",compresslevel=3) as dest:
        shutil.copyfileobj(source,dest)
    output.unlink()
    return dict(max_step_s=h,raw_rows=len(raw),observed=observed.tolist(),deck_sha256=hashlib.sha256(text.encode()).hexdigest(),
                raw_export_sha256=raw_hash,max_actual_step_s=float(np.max(np.diff(raw[:,0]))),
                initial_charge_export_valid=False,
                initial_charge_limitation="device Q fields at t=0 exported as zero; not an independently measured initial charge or integration history")


def run_primary(p,h,*,use_fd=False):
    if not math.isfinite(h) or h<=0 or not math.isclose(4e-9/h,round(4e-9/h),abs_tol=1e-9,rel_tol=0) or h>4e-9:
        raise ValueError("positive mesh must divide the 4ns observation interval")
    circuit = Circuit(p)
    state,diag = circuit.initial(use_fd=use_fd)
    count = int(round(PWL[-1][0]/h))
    stride = int(round(4e-9/h))
    observations = [dict(time_s=0.0,node_v=state.node_v,be_c=state.charge.be_c,bc_c=state.charge.bc_c,diagnostics=diag)]
    accepted = 0
    max_error,max_correction = diag["max_kcl_a"],diag["correction_v"]
    forward_count = 0
    for index in range(1,count+1):
        time = PWL[-1][0] if index==count else index*h
        old = state
        state,diag = circuit.solve(state.node_v,input_voltage(time,p.polarity),old,h,use_fd=use_fd)
        accepted += 1
        max_error,max_correction = max(max_error,diag["max_kcl_a"]),max(max_correction,diag["correction_v"])
        b,c,e = state.node_v
        forward_count += p.polarity*(b-e)>0 and p.polarity*(b-c)>0
        if index%stride==0:
            observations.append(dict(time_s=time,node_v=state.node_v,be_c=state.charge.be_c,bc_c=state.charge.bc_c,diagnostics=diag,
                previous=dict(node_v=old.node_v,be_c=old.charge.be_c,bc_c=old.charge.bc_c)))
    return dict(dt_s=h,steps=accepted,observed=observations,max_kcl_a=max_error,correction_v=max_correction,
                both_junctions_forward_steps=forward_count,history_reset_count=0,use_fd=use_fd)


def generate(executable):
    executable = Path(executable).resolve()
    if hashlib.sha256(executable.read_bytes()).hexdigest()!=EXPECTED_EXE_SHA256:
        raise ValueError("recorded independent ngspice46 executable required")
    work = ROOT/"references-local/ngspice46/loaded-probes"
    work.mkdir(parents=True,exist_ok=True)
    cases = []
    for polarity in (1,-1):
        for profile in ("zero_transit","finite_transit"):
            p = model_parameters(polarity,profile)
            label = f"{polarity}-{profile}"
            independent = [run_independent(executable,p,h,work,label) for h in (.0078125e-9,.00390625e-9)]
            coarse,fine = [np.asarray(r["observed"]) for r in independent]
            refinement = float(np.max(np.abs(coarse[:,:3]-fine[:,:3])))
            native = []
            for h in (2e-9,1e-9,.5e-9,.25e-9,.125e-9,.0625e-9):
                result = run_primary(p,h)
                observed = np.array([r["node_v"] for r in result["observed"]])
                result["max_node_error_vs_independent_v"] = float(np.max(np.abs(observed-fine[:,:3])))
                result["per_terminal_error_v"] = np.max(np.abs(observed-fine[:,:3]),axis=0).tolist()
                q = np.array([[r["be_c"],r["bc_c"]] for r in result["observed"]])
                result["max_charge_error_vs_independent_c"] = float(np.max(np.abs(q[1:]-fine[1:,3:])))
                native.append(result)
                print(json.dumps(dict(polarity=polarity,profile=profile,dt=h,steps=result["steps"],
                                     error_v=result["max_node_error_vs_independent_v"])),flush=True)
            cases.append(dict(polarity=polarity,profile=profile,parameters=asdict(p),independent=independent,native=native,
                independent_refinement_error_v=refinement,
                fine_over_coarse_error=native[-1]["max_node_error_vs_independent_v"]/native[0]["max_node_error_vs_independent_v"]))
    paths = [ROOT/"tools/bjt_loaded_transient_reference.py",ROOT/"tools/bjt_loaded_transient_probes.py",
             ROOT/"tools/bjt_charge_reference.py",ROOT/"tools/bjt_charge_ngspice_probes.py"]
    return dict(schema="rf-d/bjt-loaded-transient/v1",cases=cases,gates=GATES,environment=environment(),
        source_sha256={str(p.relative_to(ROOT)).replace("\\","/"):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
        executable_sha256=EXPECTED_EXE_SHA256,observation_time_s=OBSERVATION_S.tolist(),synthetic_parameters_only=True,
        method="primary fixed-step backward Euler and ngspice gear maxord1 adaptive backward Euler; shared input knots",
        physical_charge_identified=False,physical_switching_admitted=False,audio_admitted=False,
        oracle_rejected_attempts=[dict(polarity=1,profile="zero_transit",max_step_s=.25e-9,
            reltol=1e-10,abstol_a=1e-16,vntol_v=1e-12,trtol=1,returncode=0,
            status="TRAN aborted: timestep too small",last_time_s=9.012845433134894e-8,export_rows=547739,
            admitted=False,detected_by="incomplete final time; not a valid independent trajectory")],
        rejected_accuracy_surveys=[dict(native_dt_s=.25e-9,independent_max_steps_s=[.25e-9,.125e-9],
            primary_steps=60000,admitted=False,
            zero_transit=dict(node_error_v=.00536878417531117,independent_refinement_error_v=.0012317085759163682),
            finite_transit=dict(node_error_v=.004725198606267966,independent_refinement_error_v=.001204995977629908),
            correction="refine both integrations while preserving the original voltage gates"),
            dict(native_dt_s=.0625e-9,independent_max_steps_s=[.015625e-9,.0078125e-9],primary_steps=252000,
                admitted=False,native_voltage_gate_passed=True,independent_refinement_gate_passed=False,
                zero_transit_independent_refinement_error_v=.0002162086334251967,
                finite_transit_independent_refinement_error_v=.00023541909364865887,
                correction="refine independent integration once more; preserve its 200uV gate")],
        selected_latch_branch=None,limitation="loaded single transistor is not the Model D bistable; observations only, not an inter-sample error bound")


def passes(report):
    g = report["gates"]
    if g!=GATES or len(report["cases"])!=4 or {(c["polarity"],c["profile"]) for c in report["cases"]}!={(p,s) for p in (1,-1) for s in ("zero_transit","finite_transit")}:
        return False
    if any(len(c["native"])!=6 or len(c["independent"])!=2 for c in report["cases"]):
        return False
    return all(c["independent_refinement_error_v"]<=g["independent_refinement_error_v"]
        and c["fine_over_coarse_error"]<=g["fine_over_coarse_error"]
        and c["native"][-1]["max_node_error_vs_independent_v"]<=g["native_node_error_v"]
        and all(r["max_kcl_a"]<g["max_kcl_a"] and r["correction_v"]<g["correction_v"] for r in c["native"])
        for c in report["cases"])


if __name__=="__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ngspice",type=Path,required=True)
    report = generate(parser.parse_args().ngspice)
    OUTPUT.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(dict(passed=passes(report),cases=len(report["cases"]),steps=sum(r["steps"] for c in report["cases"] for r in c["native"]))))
    if not passes(report):
        raise SystemExit(1)
