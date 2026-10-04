"""Frozen two-seed, no-time-step KEY consistency experiment and enclosure."""
from pathlib import Path
from fractions import Fraction as F
from decimal import localcontext
import json
import numpy as np
import loudness_latch_bdf_static_precision_dc_anchor as prior
import loudness_latch_key_projection as law
from loudness_latch_bdf_transfer_solve import solve
from loudness_latch_bdf_doubling_survey import store
from loudness_latch_increment_probes import hashes
from loudness_lab_metadata import environment
ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/'evidence/loudness_latch_bdf_static_precision_key_projection.json.gz'
SUMMARY=ROOT/'evidence/loudness_latch_bdf_static_precision_key_projection_summary.json'
PROTOCOL=ROOT/'docs/BIESTABLE_POST_KEY_PROTOCOLO.md'
RADII=prior.RADII
SEEDS=(F(19,2),F(9))
PATHS=tuple(dict.fromkeys((*prior.PATHS,prior.OUTPUT,prior.SUMMARY,
    ROOT/'evidence/loudness_latch_bdf_static_precision_dc_anchor_validation.json',
    ROOT/'evidence/loudness_latch_bdf_static_precision_dc_inputs.json.gz',
    ROOT/'evidence/loudness_latch_bdf_static_precision_dc_inputs_summary.json',
    ROOT/'evidence/loudness_latch_bdf_static_precision_dc_inputs_validation.json',
    Path(law.__file__).resolve(),Path(__file__).resolve(),PROTOCOL,
    ROOT/'tools/loudness_latch_continuous_descriptor.py',ROOT/'tools/loudness_latch_bdf_transfer_solve.py')))

def generate():
    before=hashes(PATHS);env=environment();dc=prior.read(prior.OUTPUT);network=prior.CompensatedBdfNetwork(200,prior.model_parameters(1,'finite_transit'))
    g=prior.graph(network,10.);rows=dc['memory_enclosure']['rows'];targets=[F(r['stored_charge_c'])/F(r['scale_c_per_v']) for r in rows]
    uncertainty=[tuple(F(v)/F(r['scale_c_per_v'])-y for v in r['ideal_charge_interval_c']) for r,y in zip(rows,targets)]
    candidates=[]
    for seed in SEEDS:
        x=list(map(F,dc['center_node_v']))+[F(0)]*25;x[77]=seed
        candidate=law.newton(network,g,x,targets)|dict(seed_node77_v=str(seed),seed_values=list(map(str,x)))
        candidates.append(candidate);print(json.dumps(dict(seed_v=float(seed),converged=candidate['converged'],iterations=len(candidate['iterations']))),flush=True)
    primary=next((i for i,c in enumerate(candidates) if c['converged']),None);certificates=[];binary=None;event=None;inverse=None;publication=None
    if primary is not None:
        center=list(map(F,candidates[primary]['values']))
        with localcontext() as ctx:
            ctx.prec=100;r,h=law.residual(network,g,center,targets,100)
        # Candidate only; exact interval proof below does not assume inversion accuracy.
        hb=np.array(h,dtype=float);inverse=np.linalg.inv(hb).tolist()
        try:
            _,diag=solve(hb,np.eye(119));binary=dict(accepted=True,diagnostics=diag)
        except ValueError as error:binary=dict(accepted=False,reason=str(error),gate=1e-10)
        compiled=law.compile_event(network,g,center,targets,inverse)
        for radius in RADII:
            nominal=law.certify(compiled,radius);robust=law.certify(compiled,radius,uncertainty)
            certificates.append(dict(nominal=nominal,dc_charge_box=robust))
            print(json.dumps(dict(radius_v=float(radius),nominal=nominal['accepted'],robust=robust['accepted'],q=float(F(robust['contraction_upper'])),eta=float(F(robust['weighted_eta_upper_v'])))),flush=True)
        event=dict(schema='rf-d/clock-free-key-event/v1',time_s=0,key_before_v=0,key_after_v=10,
            pre_history_sha256=dc['initial_history_sha256'],node_v=[str(v) for v in center[:94]],
            charge_coordinates_v=list(map(str,targets)),charge_coordinate_rates_v_per_s=[str(v) for v in center[94:]],
            previous_history=None,previous_dt_s=None,dc_state=False,consistent_candidate=True)
        restored=json.loads(json.dumps(event,allow_nan=False));values=list(map(F,restored['node_v']+restored['charge_coordinate_rates_v_per_s']))
        with localcontext() as ctx:
            ctx.prec=100;rp,_=law.residual(network,g,values,list(map(F,restored['charge_coordinates_v'])),100,False)
        publication=dict(decimal100_residual=list(map(str,rp)),**law.diagnostics(rp),
            canonical_round_trip=law.dc.digest(restored)==law.dc.digest(event),clock_advanced=False,history_fabricated=False,
            branch_coordinate_gate_v='1e-14',kcl_gate_a='1e-11',
            gates_passed=max(map(abs,rp[:94]))<law.D('1e-11') and max(map(abs,rp[94:]))<law.D('1e-14'))
    selected=next((i for i,c in enumerate(certificates) if c['dc_charge_box']['accepted']),None)
    if hashes(PATHS)!=before:raise ValueError('projection sources changed')
    return dict(schema='rf-d/bdf-static-key-projection/v1',environment=env,source_sha256=before,graph=g,
        targets_coordinate_v=list(map(str,targets)),dc_charge_deviation_intervals_v=[list(map(str,v)) for v in uncertainty],
        candidates=candidates,primary_candidate_index=primary,inverse_binary=inverse,binary_algebra=binary,
        certificates=certificates,primary_certificate_index=selected,event=event,publication=publication,
        post_key_local_root_enclosure_proven=selected is not None,post_key_charge_sensitivity_bound_proven=selected is not None,
        post_key_initial_error_known=selected is not None,initial_error_known=False,
        clock_advanced=False,new_dc_nonlinear_solves=0,post_event_nonlinear_solves=2,
        full_path_coverage=False,actual_dae_error_bound=False,nonlinear_remainder_bound=False,
        physical_trajectory_bound=False,audio_admitted=False,deadline_admitted=False,
        binary_preconditioner_audio_admitted=False,prior_parameters_changed=False,prior_norms_changed=False,
        numerical_gates_changed=False,prior_reports_modified=False,
        limitation='local event at t=0 only; no new time trajectory, global bound, hardware identification or native promotion')

def save(report):
    if OUTPUT==SUMMARY or OUTPUT in PATHS or SUMMARY in PATHS:raise ValueError('output/input destination collision')
    storage=store(report,OUTPUT)
    summary={k:v for k,v in report.items() if k not in ('graph','candidates','inverse_binary','certificates')}
    summary.update(storage=storage,candidates=[{k:v for k,v in c.items() if k not in ('values','iterations','seed_values')}|dict(iterations=len(c['iterations'])) for c in report['candidates']],
        certificates=[{name:{k:v for k,v in c[name].items() if k not in ('defect_intervals','exponent_ranges','preconditioned_residual_intervals','weighted_row_image_radius_v')} for name in ('nominal','dc_charge_box')} for c in report['certificates']])
    SUMMARY.write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n');return summary
if __name__=='__main__':save(generate())
