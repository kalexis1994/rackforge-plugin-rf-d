"""Physical-time refinement with actual loaded-contour histories; stop on rejection."""
from dataclasses import asdict
import json
from pathlib import Path
from loudness_chain94_reference import JointNetwork
from loudness_lab_metadata import environment

ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/"evidence/loudness_chain94_time_survey.json"

def generate():
    rows=[]
    for r61 in (200,200000):
        network=JointNetwork(r61)
        initial,_=network.initial_state()
        for divisor in (1,2,4,8):
            dt=.001/divisor
            state=initial
            samples=[]
            rejected=None
            for sample in range(14*divisor):
                keyboard=10.0 if sample>=10*divisor else 0.0
                before=state
                try:state,diag=network.step(before,keyboard,dt)
                except ValueError as exc:
                    rejected=dict(sample=sample,interval_start_s=sample*dt,error=str(exc))
                    break
                # Keep common integer-ms endpoints plus event-adjacent nodes.
                if (sample+1)%divisor==0 or sample>=10*divisor:
                    samples.append(dict(sample=sample,time_s=(sample+1)*dt,
                        c2_v=state.contour.node_v["TIMING_C2"],out_v=state.contour.node_v["LOUDNESS_OUT"],
                        q25_collector_v=state.contour.node_v["RESET_COLLECTOR"],
                        audio_capacitor_v=state.audio_capacitor_v,c10_v=state.c10_v,
                        contour_capacitor_v=state.contour.capacitor_v,diagnostics=diag))
            rows.append(dict(r61_ohm=r61,divisor=divisor,dt_s=dt,accepted_steps=sample if rejected else sample+1,
                primary_rejection=rejected,samples=samples,final_state=asdict(state),
                selected_alternative=None))
            print(json.dumps(dict(r61=r61,dt=dt,accepted=rows[-1]["accepted_steps"],
                rejected=rejected)),flush=True)
    return dict(schema="rf-d/loudness-chain94-time-survey/v1",cases=rows,
        keyboard_on_s=.01,end_s=.014,method="own initial root and all 21 histories; primary previous-node solve only; no alternative root selection",
        environment=environment(),physical_switching_admitted=False,audio_admitted=False,
        numerical_quality_passed=all(s["diagnostics"]["max_kcl_a"]<1e-11 and s["diagnostics"]["correction_v"]<1e-8 for c in rows for s in c["samples"]))

if __name__=="__main__":
    report=generate()
    OUTPUT.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    if not report["numerical_quality_passed"]:raise SystemExit(1)
