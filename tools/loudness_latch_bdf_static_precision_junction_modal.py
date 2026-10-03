"""Frozen-time modal classification of all 64 signed junction generator boxes."""
from fractions import Fraction as F
from pathlib import Path
import gzip,json
import loudness_latch_junction_modal as law
import loudness_latch_bdf_static_precision_junction_spectral as prior
import loudness_latch_bdf_static_precision_weighted_descriptor as weighted
from loudness_latch_increment_probes import hashes
from loudness_latch_bdf_doubling_survey import store
from loudness_lab_metadata import environment
ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/'evidence/loudness_latch_bdf_static_precision_junction_modal.json.gz'
SUMMARY=ROOT/'evidence/loudness_latch_bdf_static_precision_junction_modal_summary.json'
PROTOCOL=ROOT/'docs/BIESTABLE_JUNTURAS_MODAL_PROTOCOLO.md'
PATHS=tuple(dict.fromkeys((*prior.PATHS,prior.OUTPUT,prior.SUMMARY,
    ROOT/'evidence/loudness_latch_bdf_static_precision_junction_spectral_validation.json',
    ROOT/'evidence/loudness_latch_bdf_static_precision_spectral_inputs.json.gz',
    ROOT/'evidence/loudness_latch_bdf_static_precision_spectral_inputs_summary.json',
    ROOT/'evidence/loudness_latch_bdf_static_precision_spectral_inputs_validation.json',
    Path(__file__).resolve(),Path(law.__file__).resolve(),PROTOCOL)))
def read(p):return json.loads(gzip.decompress(p.read_bytes()))

def generate():
    before=hashes(PATHS);env=environment();old=read(prior.OUTPUT);rms=read(prior.prior.OUTPUT);source=read(weighted.OUTPUT);cases=[]
    for previous in old['cases']:
        r=rms['cases'][previous['source_case_index']];c=source['cases'][r['source_case_index']]
        if not c['support_sha256']==r['support_sha256']==previous['support_sha256'] or not c['weights']==r['weights']==previous['weights']:raise ValueError('source coordinates differ')
        q=max(F(v['contraction_upper']) for v in c['ideal_temporal_cover']);cells=[]
        if len(c['ideal_temporal_cover'])!=8 or len(previous['cells'])!=8:raise ValueError('complete frozen cells required')
        for i,cover in enumerate(c['ideal_temporal_cover']):
            inverse=law.inverse_slice(c['inverse_binary'],c['inverse_certificate']['column_scales'],cover,q,range(115,119))
            b=law.generator(inverse,c['weights'][21:]);symmetric=[[law.mul(law.add(b[j][k],b[k][j]),(F(1,2),F(1,2))) for k in range(4)] for j in range(4)]
            if law.pack(symmetric)!=r['cells'][i]['metrics']['junction_symmetric_intervals']:raise ValueError('signed reconstruction differs from spectral source')
            result=law.analyze(b);spectral=previous['cells'][i]['spectral_certificate']
            cells.append(dict(source_cell_index=i,left=cover['left'],right=cover['right'],result=result,
                mu2_lower_per_s=spectral['lambda_lower_per_s'],mu2_upper_per_s=spectral['lambda_upper_per_s']))
        cases.append(dict(window=c['window'],subdivisions=c['subdivisions'],index=c['index'],source_weighted_case_index=r['source_case_index'],
            source_spectral_case_index=previous['source_case_index'],support_sha256=c['support_sha256'],weights=c['weights'],cells=cells,
            binary_backward_gate_still_rejected=previous['binary_backward_gate_still_rejected']))
        print(json.dumps(dict(window=c['window'],subdivisions=c['subdivisions'],rhp_counts=[v['result']['routh_certificate']['right_half_plane_roots'] for v in cells])),flush=True)
    if hashes(PATHS)!=before:raise ValueError('modal inputs changed')
    return dict(schema='rf-d/bdf-static-junction-modal/v1',environment=env,source_sha256=before,cases=cases,
        generator_policy='B_JJ=-W_J H_inverse_JJ W_J^-1; full 119-term Neumann reconstruction for each selected entry',
        isolated_frozen_generator_only=True,all_interval_coefficients_enclosed=True,norm_changed=False,weights_changed=False,
        new_exact_linear_systems=0,new_nonlinear_circuit_solves=0,prior_propagation_modified=False,
        time_varying_stability_certified=False,complete_25_memory_modal_certificate=False,nonlinear_remainder_bound=False,
        initial_error_known=False,actual_dae_error_bound=False,full_path_coverage=False,physical_trajectory_bound=False,
        temporal_error_bound_admitted=False,audio_admitted=False,deadline_admitted=False,numerical_gates_changed=False,
        prior_reports_modified=False,limitation='pointwise frozen internal block classification; no switched/time-varying, coupled or nonlinear trajectory stability')

def save(report):
    if OUTPUT==SUMMARY or OUTPUT in PATHS or SUMMARY in PATHS:raise ValueError('output/input destination collision')
    storage=store(report,OUTPUT)
    summary={k:v for k,v in report.items() if k!='cases'}|dict(storage=storage,cases=[
        {k:c[k] for k in ('window','subdivisions','index')}|dict(routh=[v['result']['routh_certificate'] for v in c['cells']]) for c in report['cases']])
    SUMMARY.write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n');return summary
if __name__=='__main__':save(generate())
