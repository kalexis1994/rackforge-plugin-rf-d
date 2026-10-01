"""Nonlinear Q25/Q15 mass audit and charged 94-node ambiguous-step replay."""
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import numpy as np
from bjt_charge_ngspice_probes import model_parameters,compare
from loudness_chain94_reference import State as JointState
from loudness_contour_reference import State as ContourState
from loudness_descriptor_stability import joint_static,reduced_modes,pole_matching_error
from loudness_latch_charge_reference import ChargedNetwork,LatchCharge
from loudness_lab_metadata import environment

ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/"evidence/loudness_latch_charge_probes.json"
GATES=dict(capacitance_abs_f=1e-19,capacitance_relative=1e-6,
           fd_capacitance_abs_f=1e-18,fd_capacitance_relative=1e-5,
           coordinate_error=1e-12,eigen_residual=1e-9,pole_matching_relative=5e-3,
           replay_kcl_a=1e-11,replay_correction_v=1e-8,replay_fd_error_v=1e-6)


def joint_state(value):
    return JointState(tuple(value["node_v"]),tuple(value["audio_capacitor_v"]),value["c10_v"],ContourState(**value["contour"]))


def stamp_terminal_matrix(latch,matrices):
    result=np.zeros((latch.n,latch.n))
    for terminals,local in zip(latch.terminals,matrices):
        for a,(i,_) in enumerate(terminals):
            if i is None:continue
            for b,(j,_) in enumerate(terminals):
                if j is not None:result[i,j]+=local[a][b]
    return result


def generate():
    survey=json.loads((ROOT/"evidence/loudness_chain94_root_survey.json").read_text())
    fold=json.loads((ROOT/"evidence/loudness_chain94_fold.json").read_text())
    ng=json.loads((ROOT/"evidence/bjt_charge_ngspice_probes.json").read_text())
    cases=[]
    for group in survey["cases"]:
        r61=group["r61_ohm"]
        initial=next(c for c in fold["cases"] if c["r61_ohm"]==r61)["prefix"][-1]["state"]
        roots=sorted(group["roots"],key=lambda c:c["state"]["contour"]["node_v"]["RESET_COLLECTOR"])
        for profile in ("zero_transit","finite_transit"):
            parameters=model_parameters(1,profile)
            charged=ChargedNetwork(r61,parameters)
            previous=charged.prepare(joint_state(initial))
            for label,root in zip(("lower","middle","upper"),roots):
                x=root["state"]["node_v"]
                g,caps=joint_static(charged.joint,x,10.0)
                gf,_=joint_static(charged.joint,x,10.0,use_fd=True)
                # Explicit series midpoint of C10 retained as node 94.
                extended=np.array(x+[x[7]])
                latch=LatchCharge(charged.joint.contour,66,len(g),parameters)
                evaluated=latch.evaluate(extended)
                capacitance=evaluated["capacitance_f"]
                fd=np.zeros_like(capacitance)
                for col in range(len(g)):
                    a=extended.copy();b=extended.copy();a[col]+=1e-6;b[col]-=1e-6
                    fd[:,col]=(latch.evaluate(a)["charge_c"]-latch.evaluate(b)["charge_c"])/2e-6
                matched=[]
                for ref,terminals in zip(("Q25","Q15"),latch.terminals):
                    case=next(c for c in ng["cases"] if c["label"]==f"latch-{r61}-{label}-{ref}"
                              and c["profile"]==profile and c["parameters"]["polarity"]==1)
                    native_v=[extended[i] if i is not None else fixed for i,fixed in terminals]
                    # ngspice fixture has a common-mode offset, not different biases.
                    assert np.allclose(np.array(native_v[:2])-native_v[2],
                                       np.array(case["terminal_v"][:2])-case["terminal_v"][2],rtol=0,atol=1e-14)
                    matched.append(case)
                checks=[]
                for frequency in (1e3,1e6):
                    matrices=[np.array(next(a for a in c["ac"] if a["frequency_hz"]==frequency)["ngspice_imag_s"])/(2*np.pi*frequency)
                              for c in matched]
                    independent=stamp_terminal_matrix(latch,matrices)
                    checks.append(dict(frequency_hz=frequency,check=compare(capacitance,independent,
                        GATES["capacitance_abs_f"],GATES["capacitance_relative"])))
                independent_caps=[]
                for terminals,ng_case in zip(latch.terminals,matched):
                    b,c,e=[i for i,_ in terminals]
                    be,bc=ng_case["ngspice_junction_cap_f"]
                    independent_caps.extend(((b,e,be),(c,b,bc)))
                augmented=caps+latch.capacitors(extended)
                analytic=reduced_modes(g,augmented,.001)
                independent_modes=reduced_modes(gf,caps+independent_caps,.001)
                solved,diag=charged.solve(x,10.0,previous,.001)
                fd_seed=np.array(solved.joint.node_v)+1e-4
                reproduced,fd_diag=charged.solve(fd_seed,10.0,previous,.001,use_fd=True)
                difference=max(abs(a-b) for a,b in zip(solved.joint.node_v,reproduced.joint.node_v))
                rows=dict(r61_ohm=r61,root=label,profile=profile,parameters=asdict(parameters),
                    frozen_node_v=x,q25_collector_v=root["state"]["contour"]["node_v"]["RESET_COLLECTOR"],
                    junction_cap_f=evaluated["junction_cap_f"],independent_ac_checks=checks,
                    fd_capacitance_check=compare(capacitance,fd,GATES["fd_capacitance_abs_f"],GATES["fd_capacitance_relative"]),
                    analytic=analytic,independent_fd_ngspice_mass=independent_modes,
                    max_relative_pole_matching_error=pole_matching_error(analytic["poles"],independent_modes["poles"]),
                    replay=dict(keyboard_v=10.0,dt_s=.001,previous=asdict(previous),state=asdict(solved),diagnostics=diag,
                        full_fd_diagnostics=fd_diag,full_fd_error_v=difference,full_fd_seed_offset_v=1e-4,
                        displacement_from_uncharged_root_v=max(abs(a-b) for a,b in zip(x,solved.joint.node_v)),selected=None),
                    growing_modes_damped_by_1ms_backward_euler=sum(p["real_per_s"]>1e-6 and p["implicit_euler_amplification_abs"]<1
                                                                 for p in analytic["poles"]),selected=None)
                cases.append(rows)
                print(json.dumps(dict(r61=r61,profile=profile,root=label,growing=analytic["growing_modes"],
                    max_real=analytic["max_real_per_s"],matching=rows["max_relative_pole_matching_error"],replay_error_v=difference)),flush=True)
    paths=[ROOT/"tools/loudness_latch_charge_reference.py",ROOT/"tools/loudness_latch_charge_probes.py",
           ROOT/"tools/bjt_charge_reference.py",ROOT/"tools/bjt_charge_ngspice_probes.py",ROOT/"tools/junction_charge_reference.py",
           ROOT/"tools/loudness_chain94_reference.py",ROOT/"tools/loudness_contour_reference.py",
           ROOT/"tools/loudness_descriptor_stability.py",ROOT/"evidence/loudness_contour_graph.json",
           ROOT/"evidence/loudness_chain94_root_survey.json",ROOT/"evidence/loudness_chain94_fold.json",
           ROOT/"evidence/bjt_charge_ngspice_probes.json"]
    return dict(schema="rf-d/loudness-latch-charge/v1",cases=cases,gates=GATES,environment=environment(),
        source_sha256={str(p.relative_to(ROOT)).replace("\\","/"):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
        method="two nonlinear conservative charge laws, full 95-node frozen descriptor and simultaneous 94-node one-interval replay",
        dynamic_rank=25,original_capacitor_histories=21,additional_oriented_junction_histories=4,
        independent_scope="NG46 device AC masses at frozen original biases, not an independent simulation of the complete loaded circuit",
        starting_state="last previously accepted uncharged joint prefix, with new Q25/Q15 charges prepared from its declared voltages",
        omitted_contour_dynamic_bjts=[p["ref"] for p in charged.joint.contour.bjts if p["ref"] not in ("Q25","Q15")],
        all_audio_semiconductor_charge_omitted=True,enumeration_exhaustive=False,trajectory_refinement_admitted=False,
        synthetic_parameters_only=True,physical_charge_identified=False,physical_switching_admitted=False,audio_admitted=False,selected=None,
        limitation="coarse 1ms replay does not resolve growing fast modes or select a physical root; frozen roots are not DC equilibria")


def passes(report):
    if report["gates"]!=GATES or len(report["cases"])!=12:return False
    expected={(r,s,p) for r in (200,200000) for s in ("lower","middle","upper") for p in ("zero_transit","finite_transit")}
    if {(c["r61_ohm"],c["root"],c["profile"]) for c in report["cases"]}!=expected:return False
    return all(c["fd_capacitance_check"]["passed"] and all(a["check"]["passed"] for a in c["independent_ac_checks"])
        and c["max_relative_pole_matching_error"]<GATES["pole_matching_relative"]
        and all(c[k]["coordinate_error"]<GATES["coordinate_error"] and c[k]["max_eigen_residual"]<GATES["eigen_residual"]
                for k in ("analytic","independent_fd_ngspice_mass"))
        and c["replay"]["diagnostics"]["max_kcl_a"]<GATES["replay_kcl_a"]
        and c["replay"]["diagnostics"]["correction_v"]<GATES["replay_correction_v"]
        and c["replay"]["full_fd_diagnostics"]["max_kcl_a"]<GATES["replay_kcl_a"]
        and c["replay"]["full_fd_diagnostics"]["correction_v"]<GATES["replay_correction_v"]
        and c["replay"]["full_fd_error_v"]<GATES["replay_fd_error_v"] for c in report["cases"])


if __name__=="__main__":
    report=generate()
    OUTPUT.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(dict(cases=len(report["cases"]),numerical_gates_passed=passes(report))))
    raise SystemExit(0 if passes(report) else 1)
