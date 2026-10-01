"""Executable independent ngspice46 comparison of an intrinsic BJT subset.

Downloads are not automated here. Provide the recorded console executable.
All generated decks/logs/tables stay ignored. Only derived evidence is saved.
"""
from dataclasses import asdict
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import numpy as np
from bjt_charge_reference import Parameters,Device
from junction_charge_reference import Depletion
from semiconductor_ideal import thermal_voltage_v
from loudness_lab_metadata import environment

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT/"evidence/bjt_charge_ngspice_probes.json"
EXPECTED_EXE_SHA256 = "86c9ea5f645ca919e305639fa7bdb522355364c424d14e197f1ade617feb3453"
GATES = dict(current_abs_a=2e-14,current_relative=1e-7,charge_abs_c=1e-20,charge_relative=1e-7,
             capacitance_abs_f=1e-19,capacitance_relative=1e-7,admittance_abs_s=1e-12,admittance_relative=1e-7)
NG_VT = 1.38064852e-23*298.15/1.6021766208e-19


def model_parameters(polarity,profile):
    # Synthetic inputs, not identified 2N3392 parameters.
    tf,tr = (0.0,0.0) if profile=="zero_transit" else (1e-9,3e-9)
    vt = thermal_voltage_v(298.15)
    return Parameters(polarity,1e-14,100.0,5.0,vt,vt,Depletion(7e-12,.75,.5,.4),
                      Depletion(5e-12,.7,.33,.4),tf,tr)


def bias_cases():
    source = json.loads((ROOT/"evidence/loudness_junction_domain_audit.json").read_text())
    rows = [dict(label=f"latch-{p['r61_ohm']}-{p['root']}-{p['ref']}",vbe=p["vbe_oriented_v"],
                 vbc=p["vbc_oriented_v"]) for p in source["cases"]]
    for label,be,bc in (("zero",0,0),("forward-active",.65,-1),("reverse-active",-.2,.65),
                        ("both-forward",.65,.62),("knees",.3,.28),("both-reverse",-.2,-1)):
        rows.append(dict(label=label,vbe=be,vbc=bc))
    return rows


def deck(parameters,voltages,outputs):
    p = parameters
    b,c,e = voltages
    be,bc = p.depletion_be,p.depletion_bc
    if any(any(ch.isspace() or ch in '\";$' for ch in path.as_posix()) for path in outputs.values()):
        raise ValueError("ngspice wrdata harness requires paths without spaces or control characters")
    model = (f".model m {'npn' if p.polarity==1 else 'pnp'} (is={p.saturation_a:.17g} bf={p.beta_forward} br={p.beta_reverse} "
        f"nf={p.emission_be_v/NG_VT:.17g} nr={p.emission_bc_v/NG_VT:.17g} "
        f"cje={be.cj0_f:.17g} vje={be.potential_v} mje={be.grading} "
        f"cjc={bc.cj0_f:.17g} vjc={bc.potential_v} mjc={bc.grading} fc={be.forward_fraction} "
        f"tf={p.transit_forward_s:.17g} tr={p.transit_reverse_s:.17g} "
        "rb=0 rc=0 re=0 cjs=0 xcjc=1 xtf=0 ptf=0 ise=0 isc=0 tnom=25)")
    lines = ["RF-D synthetic intrinsic BJT independent probe",f"vb b 0 {b:.17g} ac 1",
             f"vc c 0 {c:.17g}",f"ve e 0 {e:.17g}","q1 c b e m",model,
             ".options temp=25 tnom=25 gmin=0 reltol=1e-10 abstol=1e-16 vntol=1e-12",
             ".control","set numdgt=17","set wr_singlescale","set wr_vecnames","op","ac lin 1 1meg 1meg",
             f'wrdata {outputs["charge"].as_posix()} @q1[qbe] @q1[qbc] @q1[cpi] @q1[cmu] @q1[ib] @q1[ic] @q1[ie]']
    for freq in (1e3,1e6):
        for col,source in enumerate(("vb","vc","ve")):
            lines += [f"alter {name} acmag={1 if name==source else 0}" for name in ("vb","vc","ve")]
            lines += [f"ac lin 1 {freq:.17g} {freq:.17g}",
                f'wrdata {outputs[(freq,col)].as_posix()} '+" ".join(f"real(-i({n})) imag(-i({n}))" for n in ("vb","vc","ve"))]
    return "\n".join(lines+["quit",".endc",".end",""])


def compare(a,b,absolute,relative):
    a,b = np.asarray(a),np.asarray(b)
    error = np.abs(a-b)
    normalized = error/(absolute+relative*np.abs(a))
    return dict(max_abs=float(np.max(error)),max_gate_ratio=float(np.max(normalized)),passed=bool(np.all(normalized<=1)))


def generate(executable):
    executable = Path(executable).resolve()
    exe_hash = hashlib.sha256(executable.read_bytes()).hexdigest()
    if exe_hash != EXPECTED_EXE_SHA256:
        raise ValueError("independent executable hash differs from recorded ngspice46 binary")
    version = subprocess.run([str(executable),"--version"],capture_output=True,text=True,timeout=15,check=True).stdout
    if "ngspice-46" not in version:
        raise ValueError("recorded ngspice46 required")
    work = ROOT/"references-local/ngspice46/bjt-probes"
    work.mkdir(parents=True,exist_ok=True)
    cases = []
    for bias in bias_cases():
        for polarity in (1,-1):
            for profile in ("zero_transit","finite_transit"):
                index = len(cases)
                p = model_parameters(polarity,profile)
                # Nonzero common mode, plus mirrored intrinsic biases for PNP.
                e = .17
                b = e+polarity*bias["vbe"]
                c = b-polarity*bias["vbc"]
                v = (b,c,e)
                outputs = {"charge":work/f"case-{index}-charge.txt"}
                outputs.update({(f,k):work/f"case-{index}-y-{int(f)}-{k}.txt" for f in (1e3,1e6) for k in range(3)})
                # Reuse is permitted, but stale results must never survive a failed run.
                for path in outputs.values():
                    if path.exists():
                        path.unlink()
                input_deck = work/f"case-{index}.cir"
                text = deck(p,v,outputs)
                input_deck.write_text(text,encoding="utf-8")
                run = subprocess.run([str(executable),"-n","-b",str(input_deck)],cwd=executable.parent,
                                     capture_output=True,text=True,timeout=15)
                (work/f"case-{index}.log").write_text(run.stdout+run.stderr,encoding="utf-8")
                if run.returncode or "Error" in run.stdout+run.stderr:
                    raise ValueError(f"independent simulator rejected case {index}; see ignored log")
                raw = np.loadtxt(outputs["charge"],skiprows=1,ndmin=2)[0]
                if raw.shape!=(8,) or not np.isfinite(raw).all():
                    raise ValueError("complete finite charge/current export required")
                ref = Device(p).evaluate(v)
                cap = np.asarray(ref.capacitance_f)
                charge_checks = compare([ref.candidate.be_c,ref.candidate.bc_c],raw[1:3],GATES["charge_abs_c"],GATES["charge_relative"])
                cap_checks = compare([cap[2,2],cap[1,1]],raw[3:5],GATES["capacitance_abs_f"],GATES["capacitance_relative"])
                current_checks = compare(ref.current_a,raw[5:8],GATES["current_abs_a"],GATES["current_relative"])
                ac = []
                for freq in (1e3,1e6):
                    columns = []
                    for col in range(3):
                        values = np.loadtxt(outputs[(freq,col)],skiprows=1,ndmin=2)[0]
                        if values.shape!=(7,) or not np.isfinite(values).all() or values[0]!=freq:
                            raise ValueError("complete finite AC export at declared frequency required")
                        columns.append(values[1::2]+1j*values[2::2])
                    y = np.column_stack(columns)
                    target = np.asarray(ref.jacobian_s)+1j*2*np.pi*freq*cap
                    check = compare(target,y,GATES["admittance_abs_s"],GATES["admittance_relative"])
                    ac.append(dict(frequency_hz=freq,ngspice_real_s=y.real.tolist(),ngspice_imag_s=y.imag.tolist(),check=check))
                cases.append(dict(label=bias["label"],profile=profile,parameters=asdict(p),terminal_v=v,
                    ngspice_oriented_charge_c=raw[1:3].tolist(),ngspice_junction_cap_f=raw[3:5].tolist(),
                    ngspice_current_a=raw[5:8].tolist(),charge_check=charge_checks,capacitance_check=cap_checks,
                    current_check=current_checks,ac=ac,deck_sha256=hashlib.sha256(text.encode()).hexdigest()))
                if len(cases)%12==0:
                    print(json.dumps(dict(cases=len(cases))),flush=True)
    paths = [ROOT/"tools/bjt_charge_reference.py",ROOT/"tools/junction_charge_reference.py",
             ROOT/"tools/bjt_charge_ngspice_probes.py",ROOT/"evidence/loudness_junction_domain_audit.json"]
    return dict(schema="rf-d/bjt-charge-ngspice-probes/v1",cases=cases,gates=GATES,environment=environment(),
        executable_sha256=exe_hash,simulator_version=version.strip(),
        source_sha256={str(p.relative_to(ROOT)).replace("\\","/"):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
        thermal_scale=dict(si_vt_v=thermal_voltage_v(298.15),ngspice_legacy_vt_v=NG_VT,
            nf_nr_for_same_emission_scale=thermal_voltage_v(298.15)/NG_VT,temperature_c=25,tnom_c=25),
        scope="qb=1, XTF/PTF=0, XCJC=1; no Early, high injection, internal resistance, leakage or substrate",
        reverse_tail_difference="ngspice uses cubic continuation below -3*n*VT; reference retains Shockley; discrepancy retained within declared absolute gates",
        synthetic_parameters_only=True,physical_charge_identified=False,physical_switching_admitted=False,audio_admitted=False)


if __name__=="__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ngspice",type=Path,required=True)
    report = generate(parser.parse_args().ngspice)
    OUTPUT.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    checks = [c[k] for c in report["cases"] for k in ("charge_check","capacitance_check","current_check")]
    checks += [a["check"] for c in report["cases"] for a in c["ac"]]
    print(json.dumps(dict(cases=len(report["cases"]),checks=len(checks),failed=sum(not c["passed"] for c in checks),
                         max_gate_ratio=max(c["max_gate_ratio"] for c in checks))))
    if not all(c["passed"] for c in checks):
        raise SystemExit(1)
