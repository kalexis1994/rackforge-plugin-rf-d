"""Independent full DC roots for zero imposed VCA control sources.

Continuation is a numerical initialization path with all capacitors open,
not a physical envelope, a temporal ramp or a substitute for Note Off.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

from circuit66_dc_vectors import dc_evaluator, fd_direction, solve_dc
from cutoff_j7_vectors import setup

OUTPUT = Path(__file__).resolve().parents[1]/"evidence/circuit66_vca_dc_vectors.json"


def boundary_values(values, first, second):
    result = copy.deepcopy(values)
    vp = result[2]["network_parameters"]
    vp["first_parameters"]["core_parameters"]["loudness_v"] = first
    vp["second_parameters"]["q21_base_v"] = second
    return result


def generate_vectors():
    cases = []
    for r61 in (200,200000):
        values = setup(r61)
        centre,_,_ = solve_dc(list(values[5]["node_v"]),dc_evaluator(values,values[4]))
        for name,first,second in (("first_zero",0,2),("second_zero",2,0),("both_zero",0,0)):
            direct_error = None
            target_values = boundary_values(values,first,second)
            target = dc_evaluator(target_values,values[4])
            try:
                direct,_,_ = solve_dc(centre,target)
            except ValueError as error:
                direct_error = str(error)
                direct = None
            x = centre.copy()
            stages = []
            for stage in range(1,33):
                v1 = 2+(first-2)*stage/32
                v2 = 2+(second-2)*stage/32
                step_values = boundary_values(values,v1,v2)
                x,kcl,correction = solve_dc(x,dc_evaluator(step_values,values[4]))
                stages.append(dict(stage=stage,loudness_v=v1,q21_base_v=v2,
                                   kcl_a=kcl,correction_v=correction,node_v=x))
            r,_ = target(x)
            cases.append(dict(name=name,r61_ohm=r61,loudness_v=first,q21_base_v=second,
                              controls=values[4],centre_node_v=centre,node_v=x,
                              direct_error=direct_error,direct_node_v=direct,
                              max_kcl_a=max(abs(v) for v in r),
                              max_correction_v=max(abs(v) for v in fd_direction(x,r,target)),
                              stages=stages))
    return dict(schema="rf-d/circuit66-vca-dc-vectors/v1",passed=True,
                method="all capacitors open; independent full FD; 32-stage control continuation; offline 40/32 solves",
                gates=dict(node_error_v=1e-6,kcl_a=1e-11,correction_v=1e-8),cases=cases,
                audio_fidelity_claim=False)


if __name__ == "__main__":
    report = generate_vectors()
    OUTPUT.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(dict(cases=len(report["cases"]),direct_failures=sum(c["direct_error"] is not None for c in report["cases"]),
                         max_kcl_a=max(c["max_kcl_a"] for c in report["cases"]),
                         max_correction_v=max(c["max_correction_v"] for c in report["cases"])),indent=2))
