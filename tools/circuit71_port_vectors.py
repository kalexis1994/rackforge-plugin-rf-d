"""Joint C2/reset admittance, FD source perturbations with immutable histories."""
import json
from pathlib import Path
from circuit71_loudness_vectors import evaluator, metrics, solve
from cutoff_j7_vectors import setup

ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/"evidence/circuit71_port_vectors.json"
GATES=dict(node_v=1e-6,current_a=1e-9,admittance_s=1e-9,node_gradient_v_per_v=2e-5,
           refinement_admittance_s=1e-9,refinement_node_gradient_v_per_v=2e-5)


def derivatives(values,x,c2,reset,old,bus,delta):
    current=[[0.0]*2 for _ in range(2)]
    nodes=[[0.0]*2 for _ in range(71)]
    for col in range(2):
        roots=[]
        currents=[]
        for sign in (-1,1):
            source=[c2,reset]
            source[col]+=sign*delta
            root,_=solve(x,evaluator(values,*source,old=old,bus=bus),
                         kcl_gate=1e-13,correction_gate=1e-12)
            m=metrics(root,*source)
            roots.append(root)
            currents.append([m["timing_current_a"],m["reset_current_a"]])
        for row in range(71): nodes[row][col]=(roots[1][row]-roots[0][row])/(2*delta)
        for row in range(2): current[row][col]=(currents[1][row]-currents[0][row])/(2*delta)
    return current,nodes


def generate():
    joint=json.loads((ROOT/"evidence/circuit71_loudness_vectors.json").read_text())
    cases=[]
    for case in joint["cases"]:
        values=setup(case["r61_ohm"])
        points=[("dc",row,None,0.0) for row in case["dc_rows"]]
        for sample in (8,24,40,48):
            row=case["rows"][sample]
            before=case["rows"][sample-1]
            old=dict(node_v=before["node_v"][:66],capacitor_v=before["capacitor_v"],c10_v=before["c10_v"],
                     follower_v=before["node_v"][66:],c2_v=before["c2_v"],reset_base_v=case["reset_base_v"])
            points.append(("transient",row,old,row["bus_v"]))
        for mode,row,old,bus in points:
            c2=row["c2_v"]; reset=case["reset_base_v"]
            x,diag=solve(row["node_v"],evaluator(values,c2,reset,old=old,bus=bus),
                         kcl_gate=1e-13,correction_gate=1e-12)
            coarse,coarse_gradient=derivatives(values,x,c2,reset,old,bus,2e-5)
            port,gradient=derivatives(values,x,c2,reset,old,bus,1e-5)
            refinement=max(abs(a-b) for ra,rb in zip(port,coarse) for a,b in zip(ra,rb))
            grad_refinement=max(abs(a-b) for ra,rb in zip(gradient,coarse_gradient) for a,b in zip(ra,rb))
            m=metrics(x,c2,reset)
            cases.append(dict(mode=mode,r61_ohm=case["r61_ohm"],c2_v=c2,reset_base_v=reset,
                bus_v=bus,old=old,node_v=x,diagnostics=diag,
                current_a=[m["timing_current_a"],m["reset_current_a"]],
                admittance_s=port,node_gradient_v_per_v=gradient,
                refinement_admittance_s=refinement,refinement_node_gradient_v_per_v=grad_refinement))
    passed=all(c["refinement_admittance_s"]<GATES["refinement_admittance_s"] and
               c["refinement_node_gradient_v_per_v"]<GATES["refinement_node_gradient_v_per_v"] for c in cases)
    return dict(schema="rf-d/circuit71-port-vectors/v1",passed=passed,gates=GATES,cases=cases,
        fd_delta_v=1e-5,refinement_delta_v=2e-5,kcl_gate_a=1e-13,correction_gate_v=1e-12,
        audio_admitted=False,physical_contour_switching_admitted=False,
        method="full loaded 71-node roots; central FD of both sources; frozen original histories")


if __name__=="__main__":
    result=generate()
    OUTPUT.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(dict(cases=len(result["cases"]),passed=result["passed"],
        max_refinement_s=max(c["refinement_admittance_s"] for c in result["cases"]),
        max_node_refinement=max(c["refinement_node_gradient_v_per_v"] for c in result["cases"]))))
    if not result["passed"]:raise SystemExit(1)
