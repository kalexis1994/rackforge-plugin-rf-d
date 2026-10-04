"""Separate fixed scale bank for the already frozen clock-free event candidate."""
from pathlib import Path
from fractions import Fraction as F
import json
import loudness_latch_bdf_static_precision_key_projection as prior
from loudness_latch_bdf_doubling_survey import store
from loudness_latch_increment_probes import hashes
from loudness_lab_metadata import environment
law=prior.law
ROOT=prior.ROOT
OUTPUT=ROOT/'evidence/loudness_latch_bdf_static_precision_key_scaled.json.gz'
SUMMARY=ROOT/'evidence/loudness_latch_bdf_static_precision_key_scaled_summary.json'
PROTOCOL=ROOT/'docs/BIESTABLE_POST_KEY_ESCALAS_PROTOCOLO.md'
RATE_WEIGHTS=(F(1,10**9),F(1,10**12),F(1,10**15))
PATHS=(*prior.PATHS,prior.OUTPUT,prior.SUMMARY,Path(__file__).resolve(),PROTOCOL,
       ROOT/'evidence/loudness_latch_bdf_static_precision_key_launch_attempts.json')

def generate():
    before=hashes(PATHS);env=environment();r=prior.prior.read(prior.OUTPUT)
    primary=r['primary_candidate_index']
    if primary is None:raise ValueError('frozen converged event candidate required')
    network=prior.prior.CompensatedBdfNetwork(200,prior.prior.model_parameters(1,'finite_transit'))
    center=list(map(F,r['candidates'][primary]['values']));certificates=[]
    for weight in RATE_WEIGHTS:
        compiled=law.compile_event(network,r['graph'],center,r['targets_coordinate_v'],r['inverse_binary'],[F(1)]*94+[weight]*25)
        for radius in prior.RADII:
            cert=law.certify(compiled,radius,r['dc_charge_deviation_intervals_v'])
            certificates.append(cert|dict(rate_weight_s=str(weight)))
            print(json.dumps(dict(rate_weight_s=float(weight),radius_v=float(radius),accepted=cert['accepted'],q=float(F(cert['contraction_upper'])),eta_v=float(F(cert['weighted_eta_upper_v'])))),flush=True)
    selected=next((i for i,c in enumerate(certificates) if c['accepted']),None);bounds=None
    if selected is not None:
        cert=certificates[selected];error=F(cert['weighted_posterior_error_upper_v']);weight=F(cert['rate_weight_s'])
        bounds=dict(node_error_upper_v=str(error),rate_error_upper_v_per_s=str(error/weight),
            uniform_dc_charge_box=True,local_unique_root_for_each_charge=True,rate_weight_s=str(weight),
            node77_interval_v=list(map(str,(center[77]-error,center[77]+error))),
            laboratory_event_center_sha256=law.dc.digest(r['event']),binary_integrator_publication_error_included=False)
    if hashes(PATHS)!=before:raise ValueError('scaled event proof sources changed')
    return dict(schema='rf-d/bdf-static-key-scaled/v1',environment=env,source_sha256=before,
        projection_data_sha256=before[prior.OUTPUT.relative_to(ROOT).as_posix()],certificates=certificates,
        primary_certificate_index=selected,bounds=bounds,new_nonlinear_solves=0,new_preconditioners=0,
        post_key_local_root_enclosure_proven=selected is not None,post_key_charge_sensitivity_bound_proven=selected is not None,
        laboratory_post_key_initial_error_known=selected is not None,binary_integrator_initial_error_known=False,
        prior_failed_scale_report_preserved=True,scales_fixed_before_measurement=True,
        clock_advanced=False,initial_error_known=False,full_path_coverage=False,actual_dae_error_bound=False,
        physical_trajectory_bound=False,audio_admitted=False,deadline_admitted=False,numerical_gates_changed=False,
        prior_parameters_changed=False,prior_reports_modified=False,
        limitation='uniform local right-limit event enclosure; separate voltage and derivative units; no temporal or binary integrator publication proof')

def save(report):
    if OUTPUT==SUMMARY or OUTPUT in PATHS or SUMMARY in PATHS:raise ValueError('output/input destination collision')
    storage=store(report,OUTPUT);summary={k:v for k,v in report.items() if k!='certificates'}
    summary.update(storage=storage,certificates=[{k:v for k,v in c.items() if k not in ('defect_intervals','exponent_ranges','preconditioned_residual_intervals','weighted_row_image_radius_v')} for c in report['certificates']])
    SUMMARY.write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n');return summary
if __name__=='__main__':save(generate())
