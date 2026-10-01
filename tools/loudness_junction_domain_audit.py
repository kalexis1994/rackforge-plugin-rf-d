"""Bias/domain inventory of the three frozen loaded roots; no parameter fitting."""
from dataclasses import asdict
import hashlib
import json
import math
from pathlib import Path
from loudness_chain94_reference import JointNetwork
from loudness_lab_metadata import environment

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT/"evidence/loudness_junction_domain_audit.json"


def generate():
    survey = json.loads((ROOT/"evidence/loudness_chain94_root_survey.json").read_text())
    cases = []
    for case in survey["cases"]:
        network = JointNetwork(case["r61_ohm"])
        d, vt = network.contour.devices, network.contour.vt
        ordered = sorted(case["roots"], key=lambda r: r["state"]["contour"]["node_v"]["RESET_COLLECTOR"])
        for label, root in zip(("lower", "middle", "upper"), ordered):
            v = root["state"]["contour"]["node_v"]
            for p in network.contour.bjts:
                if p["ref"] not in ("Q25", "Q15"):
                    continue
                pol = 1 if p["kind"] == "NPN" else -1
                vb, vc, ve = (v[p[k]] for k in ("base", "collector", "emitter"))
                vbe, vbc = pol*(vb-ve), pol*(vb-vc)
                f, r = d.is_a*math.expm1(vbe/vt), d.is_a*math.expm1(vbc/vt)
                gf, gr = d.is_a*math.exp(vbe/vt)/vt, d.is_a*math.exp(vbc/vt)/vt
                ib, ic = pol*(f/d.beta_forward+r/d.beta_reverse), pol*(f-r*(1+1/d.beta_reverse))
                cases.append(dict(r61_ohm=case["r61_ohm"],root=label,ref=p["ref"],kind=p["kind"],
                    terminal_v=dict(base=vb,collector=vc,emitter=ve),vbe_oriented_v=vbe,vbc_oriented_v=vbc,
                    vcb_v=vc-vb,vce_v=vc-ve,both_junctions_forward=vbe>0 and vbc>0,
                    hypothetical_forward_a=f,hypothetical_reverse_a=r,
                    outgoing_current_a=dict(base=ib,collector=ic,emitter=-ib-ic),
                    derivative_s=dict(forward=gf,reverse=gr),
                    diffusion_f_per_1ns_unit=dict(forward=gf*1e-9,reverse=gr*1e-9),
                    transit_time_assigned=False,semiconductor_hypothesis=asdict(d),
                    cob_test=dict(source_ids=["DS-3392-C","DS-3392-F"],vcb_v=10.0,frequency_hz=1e6,
                        temperature_k=298.15,measurement_frequency_present=False,
                        bias_matches=math.isclose(vc-vb,10.0,abs_tol=1e-9,rel_tol=0),
                        temperature_matches=d.temperature_k==298.15,physical_capacitance_identified=False)))
    paths = [ROOT/"tools/loudness_junction_domain_audit.py",ROOT/"tools/loudness_contour_reference.py",
             ROOT/"evidence/loudness_contour_graph.json",ROOT/"evidence/loudness_chain94_root_survey.json"]
    return dict(schema="rf-d/loudness-junction-domain/v1",cases=cases,environment=environment(),
        source_sha256={str(p.relative_to(ROOT)).replace("\\","/"):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
        unit_normalization_s=1e-9,normalization_is_transit_fit=False,
        domain="six frozen loaded backward-Euler roots at KEY=10V, dt=1ms; no trajectory or AC experiment",
        physical_charge_identified=False,physical_switching_admitted=False,audio_admitted=False,selected=None)


if __name__ == "__main__":
    report = generate()
    OUTPUT.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    for ref in ("Q25", "Q15"):
        rows = [r for r in report["cases"] if r["ref"]==ref]
        print(json.dumps(dict(ref=ref,cases=len(rows),vcb_range_v=[min(r["vcb_v"] for r in rows),max(r["vcb_v"] for r in rows)],
            cob_bias_matches=sum(r["cob_test"]["bias_matches"] for r in rows),
            both_junctions_forward=sum(r["both_junctions_forward"] for r in rows))))
