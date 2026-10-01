"""Postprocessing sampled transition times; no trajectory retiming or admission."""
import hashlib
import gzip
import json
from pathlib import Path
import numpy as np
from bjt_charge_ngspice_probes import model_parameters
from loudness_latch_increment_reference import IncrementNetwork
from loudness_latch_increment_survey import trace

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"evidence/loudness_latch_increment_survey.json.gz"
OUTPUT=ROOT/"evidence/loudness_latch_transition_observations.json"
THRESHOLDS_V=(6.,4.,2.,.5)
ATTACK_THRESHOLDS_V=(2.,4.,6.,8.)
WINDOW_S=10e-6


def sampled_crossings(times,values,index,threshold,direction="falling"):
    if direction not in ("falling","rising"):raise ValueError("explicit crossing direction required")
    found=[]
    for k in range(1,len(times)):
        a,b=values[k-1,index],values[k,index]
        if (a>threshold>=b if direction=="falling" else a<threshold<=b):
            fraction=(a-threshold)/(a-b)
            found.append(dict(left_s=float(times[k-1]),right_s=float(times[k]),
                left_v=float(a),right_v=float(b),interpolated_time_s=float(times[k-1]+fraction*(times[k]-times[k-1])),
                sampled_slope_v_per_s=float((b-a)/(times[k]-times[k-1]))))
    return found


def aligned_difference(ta,va,tb,vb,event_a,event_b,window=WINDOW_S):
    a=ta-event_a;b=tb-event_b
    start=max(-window,float(a[0]),float(b[0]));end=min(window,float(a[-1]),float(b[-1]))
    times=np.unique(np.concatenate((a,b)));times=times[(times>=start)&(times<=end)]
    if len(times)==0:return dict(available=False,reason="no-common-event-window")
    av=np.column_stack([np.interp(times,a,va[:,k]) for k in range(94)])
    bv=np.column_stack([np.interp(times,b,vb[:,k]) for k in range(94)])
    diff=np.abs(av-bv);loc=np.unravel_index(np.argmax(diff),diff.shape)
    return dict(available=True,window_s=window,common_start_relative_s=start,common_end_relative_s=end,
        points=len(times),maximum_node_difference_v=float(np.max(diff)),
        maximum_difference_node=int(loc[1]),maximum_difference_relative_time_s=float(times[loc[0]]),
        diagnostic_only=True,published_trajectory_retimed=False)


def generate():
    original=SOURCE.read_bytes();data=json.loads(gzip.decompress(original))
    n=IncrementNetwork(200,model_parameters(1,"finite_transit"))
    index=66+n.joint.contour.index[n.joint.contour.alias["RESET_COLLECTOR"]]
    ta,va=trace(data["cases"][0]);tb,vb=trace(data["cases"][1])
    crossings=[]
    for threshold in THRESHOLDS_V:
        a=sampled_crossings(ta,va,index,threshold);b=sampled_crossings(tb,vb,index,threshold)
        crossings.append(dict(node="Q25 collector / RESET_COLLECTOR",node_index=index,threshold_v=threshold,
            policy_a2=a,policy_b2=b,unique_in_both=len(a)==len(b)==1,
            interpolated_time_difference_s=b[0]["interpolated_time_s"]-a[0]["interpolated_time_s"] if len(a)==len(b)==1 else None))
    anchor=next(row for row in crossings if row["threshold_v"]==4.)
    alignment=(aligned_difference(ta,va,tb,vb,anchor["policy_a2"][0]["interpolated_time_s"],
                 anchor["policy_b2"][0]["interpolated_time_s"]) if anchor["unique_in_both"] else
               dict(available=False,reason="anchor-crossing-not-unique-in-both"))
    attack_index=66+n.joint.contour.index[n.joint.contour.alias["ATTACK_OUT"]]
    attack=[]
    for threshold in ATTACK_THRESHOLDS_V:
        a=sampled_crossings(ta,va,attack_index,threshold,"rising")
        b=sampled_crossings(tb,vb,attack_index,threshold,"rising")
        attack.append(dict(node="ATTACK_OUT",node_index=attack_index,threshold_v=threshold,
            policy_a2=a,policy_b2=b,unique_in_both=len(a)==len(b)==1,
            interpolated_time_difference_s=b[0]["interpolated_time_s"]-a[0]["interpolated_time_s"] if len(a)==len(b)==1 else None))
    attack_anchor=next(row for row in attack if row["threshold_v"]==4.)
    attack_alignment=(aligned_difference(ta,va,tb,vb,attack_anchor["policy_a2"][0]["interpolated_time_s"],
        attack_anchor["policy_b2"][0]["interpolated_time_s"]) if attack_anchor["unique_in_both"] else
        dict(available=False,reason="attack-anchor-not-unique-in-both"))
    fast=[]
    for threshold in (.5,.1,.05):
        a=sampled_crossings(ta,va,index,threshold);b=sampled_crossings(tb,vb,index,threshold)
        fast.append(dict(threshold_v=threshold,policy_a2=a,policy_b2=b,
            interpolated_time_difference_s=b[0]["interpolated_time_s"]-a[0]["interpolated_time_s"] if len(a)==len(b)==1 else None))
    widths=[]
    for k,times in enumerate((ta,tb)):
        lo=crossings[0][("policy_a2","policy_b2")[k]];hi=crossings[-1][("policy_a2","policy_b2")[k]]
        widths.append(hi[0]["interpolated_time_s"]-lo[0]["interpolated_time_s"] if len(lo)==len(hi)==1 else None)
    paths=(Path(__file__).resolve(),ROOT/"tools/loudness_latch_increment_survey.py",SOURCE)
    if SOURCE.read_bytes()!=original:raise ValueError("survey changed during observation")
    return dict(schema="rf-d/latch-transition-observations/v1",crossings=crossings,
        attack_out_crossings=attack,attack_event_aligned_shape=attack_alignment,fast_collector_crossings=fast,
        six_to_half_volt_interpolated_duration_s=widths,event_aligned_shape=alignment,
        original_same_time_refinement=data["refinement"],
        source_sha256={str(p.relative_to(ROOT)).replace("\\","/"):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
        trajectory_modified=False,temporal_refinement_admitted=False,physical_switching_admitted=False,audio_admitted=False,
        limitation="crossings and shapes interpolate stored samples; brackets are sampled intervals, not a continuous trajectory error bound; alignment is diagnostic only")


if __name__=="__main__":
    report=generate();OUTPUT.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(dict(time_differences_s=[r["interpolated_time_difference_s"] for r in report["crossings"]],
        attack_time_differences_s=[r["interpolated_time_difference_s"] for r in report["attack_out_crossings"]],
        alignment=report["event_aligned_shape"],attack_alignment=report["attack_event_aligned_shape"])))
