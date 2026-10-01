"""Fixed-history prototype and exact cubic counterexample to divide-by-three."""
import gzip
import json
from pathlib import Path
from loudness_latch_bdf_doubling import estimate,cubic_error_factors
from loudness_latch_bdf_reference import BdfNetwork,coefficients
from loudness_latch_bdf_probes import pack,unpack
from loudness_latch_bdf_refinement import OUTPUT as STRICT
from loudness_latch_bdf_observation_domain import PATHS as DOMAIN_PATHS
from loudness_latch_increment_probes import hashes
from bjt_charge_ngspice_probes import model_parameters
from loudness_lab_metadata import environment

ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/"evidence/loudness_latch_bdf_doubling_probes.json"
ANCHOR_LIMITS_S=(.0023,.00242,.00244205)
RATIOS=(.25,.5,1.,2.)
PATHS=tuple(dict.fromkeys((*DOMAIN_PATHS,Path(__file__).resolve(),ROOT/"tools/loudness_latch_bdf_doubling.py")))


def cubic_step(old,older,time,h,k):
    c=coefficients(h,k)
    return (h*3*(time+h)**2-c["a1"]*old-c["a2"]*older)/c["a0"]


def cubic_case(r):
    h=1.;k=h/r;old=0.;older=-k**3
    full=cubic_step(old,older,0.,h,k)
    middle=cubic_step(old,older,0.,h/2,k)
    fine=cubic_step(middle,old,h/2,h/2,h/2)
    return dict(ratio=r,full_v=full,middle_v=middle,fine_v=fine,exact_destination_v=h**3,
        full_error_v=full-h**3,fine_error_v=fine-h**3,full_minus_fine_v=full-fine,
        divided_by_three_v=(full-fine)/3,analytic_error_factors=cubic_error_factors(r),synthetic=True)


def generate():
    before=hashes(PATHS)
    strict=json.loads(gzip.decompress(STRICT.read_bytes()))
    steps=[s for a in strict["case"]["accepted"] for s in a["steps"]]
    network=BdfNetwork(200,model_parameters(1,"finite_transit"));rows=[]
    for limit in ANCHOR_LIMITS_S:
        index=max(i for i,s in enumerate(steps) if s["history"]["time_s"]<=limit)
        old=unpack(network,steps[index]["history"])
        for ratio in RATIOS:
            h=ratio*old.previous_dt_s
            full,d,fine,diag=estimate(network,old,10.,h)
            rows.append(dict(anchor_limit_s=limit,source_interval_index=index,previous=pack(old),ratio=ratio,dt_s=h,
                             full=pack(full),full_diagnostics=d,fine=pack(fine),diagnostics=diag))
    if hashes(PATHS)!=before:raise ValueError("doubling probe inputs changed during execution")
    return dict(schema="rf-d/bdf-doubling-probes/v1",source_sha256=before,environment=environment(),
        probes=rows,cubic=[cubic_case(r) for r in RATIOS],minimum_step_s=1e-12,
        kcl_gate_a=1e-11,branch_gate_v=1e-14,fd_gate_v=1e-8,
        adaptive_trajectory_generated=False,temporal_refinement_admitted=False,temporal_error_bound_admitted=False,
        physical_switching_admitted=False,audio_admitted=False,
        limitation="restricted hypotheses; full and half paths share the spatial solver; cubic formula does not calibrate nonlinear DAE error")


if __name__=="__main__":
    report=generate();OUTPUT.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(dict(probes=len(report["probes"]),maximum_raw_node_difference_v=max(r["diagnostics"]["maximum_node_difference_v"] for r in report["probes"]),
                         cubic_fine_over_difference=[r["analytic_error_factors"]["fine_over_difference"] for r in report["cubic"]])))
