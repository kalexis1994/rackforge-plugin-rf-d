"""One changed RMS diagonal using archived symmetric boxes and exact LDL proofs."""
from fractions import Fraction as F
from pathlib import Path
import gzip,json
import loudness_latch_spectral_junction as law
import loudness_latch_bdf_static_precision_junction_rms as prior
from loudness_latch_increment_probes import hashes
from loudness_latch_bdf_doubling_survey import store
from loudness_lab_metadata import environment
ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/'evidence/loudness_latch_bdf_static_precision_junction_spectral.json.gz'
SUMMARY=ROOT/'evidence/loudness_latch_bdf_static_precision_junction_spectral_summary.json'
PROTOCOL=ROOT/'docs/BIESTABLE_JUNTURAS_ESPECTRO_PROTOCOLO.md'
PATHS=tuple(dict.fromkeys((*prior.PATHS,prior.OUTPUT,prior.SUMMARY,
    ROOT/'evidence/loudness_latch_bdf_static_precision_junction_rms_validation.json',
    ROOT/'evidence/loudness_latch_bdf_static_precision_junction_inputs.json.gz',
    ROOT/'evidence/loudness_latch_bdf_static_precision_junction_inputs_summary.json',
    ROOT/'evidence/loudness_latch_bdf_static_precision_junction_inputs_validation.json',
    Path(__file__).resolve(),Path(law.__file__).resolve(),PROTOCOL)))

def read(p):return json.loads(gzip.decompress(p.read_bytes()))
def generate():
    before=hashes(PATHS);env=environment();source=read(prior.OUTPUT);cases=[]
    for index,old in enumerate(source['cases']):
        packed=[];cells=[]
        if len(old['cells'])!=8:raise ValueError('complete eight-cell RMS source required')
        for i,cell in enumerate(old['cells']):
            metrics,cert=law.refine_metrics(cell['metrics'])
            cells.append(dict(forcing_inputs=cell['forcing_inputs'],metrics=metrics))
            packed.append(dict(source_cell_index=i,spectral_certificate=cert,comparison_per_s=metrics['comparison_per_s']))
        propagation=prior.law.propagate(cells)
        new=F(propagation['peak_zero_anchor_node_upper_v']);baseline=old['propagation']
        c=dict(window=old['window'],subdivisions=old['subdivisions'],index=old['index'],source_case_index=index,
            support_sha256=old['support_sha256'],weights=old['weights'],cells=packed,propagation=propagation,
            prior_rms_peak_zero_anchor_node_upper_v=baseline['peak_zero_anchor_node_upper_v'],
            prior_rms_peak_node_anchor_gain_upper=baseline['peak_node_anchor_gain_upper'],
            peak_node_budget_nonincreasing=new<=F(baseline['peak_zero_anchor_node_upper_v']),
            binary_backward_gate_still_rejected=old['binary_backward_gate_still_rejected'])
        cases.append(c)
        print(json.dumps(dict(window=c['window'],subdivisions=c['subdivisions'],cells=8,
            strictly_narrower=sum(v['spectral_certificate']['strictly_narrower'] for v in packed),
            peak_node_budget_nonincreasing=c['peak_node_budget_nonincreasing'])),flush=True)
    if hashes(PATHS)!=before:raise ValueError('spectral proof inputs changed')
    return dict(schema='rf-d/bdf-static-junction-spectral/v1',environment=env,source_sha256=before,cases=cases,
        bisections=law.BISECTIONS,exact_ldlt_probes=len(cases)*8*(law.BISECTIONS+1),
        prior_metric_components_reused_by_reference=True,only_junction_diagonal_changed=True,
        norm_changed=False,weights_changed=False,block_partition_changed=False,initial_anchor_reference=source['initial_anchor_reference'],
        new_exact_linear_systems=0,new_nonlinear_circuit_solves=0,ideal_time_varying_tangent_bound=True,
        nonlinear_remainder_bound=False,initial_error_known=False,actual_dae_error_bound=False,full_path_coverage=False,
        temporal_error_bound_admitted=False,physical_trajectory_bound=False,audio_admitted=False,deadline_admitted=False,
        numerical_gates_changed=False,prior_reports_modified=False,
        limitation='interval spectral proof in same RMS norm; unknown anchor, nonlinear remainder and noncontiguous selected intervals')

def save(report):
    if OUTPUT==SUMMARY or OUTPUT in PATHS or SUMMARY in PATHS:raise ValueError('output/input destination collision')
    storage=store(report,OUTPUT)
    summary={k:v for k,v in report.items() if k!='cases'}|dict(storage=storage,cases=[
        {k:c[k] for k in ('window','subdivisions','index','propagation','prior_rms_peak_zero_anchor_node_upper_v','peak_node_budget_nonincreasing')}|
        dict(mu2_lower_per_cell=[v['spectral_certificate']['lambda_lower_per_s'] for v in c['cells']],
            mu2_upper_per_cell=[v['spectral_certificate']['lambda_upper_per_s'] for v in c['cells']],
            strictly_narrower_cells=sum(v['spectral_certificate']['strictly_narrower'] for v in c['cells'])) for c in report['cases']])
    SUMMARY.write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n');return summary

if __name__=='__main__':save(generate())
