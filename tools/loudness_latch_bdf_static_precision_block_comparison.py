"""Fixed physical blocks on the previously certified 64 temporal cells."""
from fractions import Fraction as F
import gzip,json
from pathlib import Path
import loudness_latch_block_comparison as law
import loudness_latch_bdf_static_precision_cell_propagation as prior
from loudness_latch_increment_probes import hashes
from loudness_latch_bdf_doubling_survey import store
from loudness_lab_metadata import environment
ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/'evidence/loudness_latch_bdf_static_precision_block_comparison.json.gz'
SUMMARY=ROOT/'evidence/loudness_latch_bdf_static_precision_block_comparison_summary.json'
PROTOCOL=ROOT/'docs/BIESTABLE_COMPARACION_BLOQUES_PROTOCOLO.md'
PATHS=tuple(dict.fromkeys((*prior.PATHS,prior.OUTPUT,prior.SUMMARY,
    ROOT/'evidence/loudness_latch_bdf_static_precision_cell_propagation_validation.json',
    ROOT/'evidence/loudness_latch_bdf_static_precision_cell_inputs.json.gz',
    ROOT/'evidence/loudness_latch_bdf_static_precision_cell_inputs_summary.json',
    ROOT/'evidence/loudness_latch_bdf_static_precision_cell_inputs_validation.json',
    Path(__file__).resolve(),Path(law.__file__).resolve(),PROTOCOL)))

def read(p):return json.loads(gzip.decompress(p.read_bytes()))
def generate():
    before=hashes(PATHS);env=environment();source=read(prior.OUTPUT);weighted=read(prior.prior.OUTPUT);cases=[]
    for old in source['cases']:
        c=weighted['cases'][old['source_case_index']];q=max(F(v['contraction_upper']) for v in c['ideal_temporal_cover']);cells=[]
        if c['support_sha256']!=old['support_sha256'] or c['weights']!=old['weights']:raise ValueError('frozen supports or weights differ')
        for cover,cell in zip(c['ideal_temporal_cover'],old['cells']):
            inverse,cert=prior.law.structured_inverse(c['inverse_binary'],c['inverse_certificate']['column_scales'],cover,q)
            if cert!=cell['inverse_certificate']:raise ValueError('prior inverse reconstruction differs')
            cells.append(dict(forcing_inputs=cell['forcing_inputs'],inverse_certificate=cert,
                metrics=law.block_metrics(inverse,94,c['weights'],cell['forcing_inputs'])))
        if len(cells)!=8:raise ValueError('complete eight-cell reconstruction required')
        propagation=law.propagate(cells);baseline=old['propagation']
        new=F(propagation['peak_zero_anchor_node_upper_v']);previous=F(baseline['peak_zero_anchor_node_upper_v'])
        row=dict(window=old['window'],subdivisions=old['subdivisions'],index=old['index'],source_case_index=old['source_case_index'],
            support_sha256=old['support_sha256'],weights=old['weights'],cells=cells,propagation=propagation,
            prior_scalar_propagation=baseline,peak_node_budget_nonincreasing=new<=previous,
            binary_backward_gate_still_rejected=old['binary_backward_gate_still_rejected'])
        cases.append(row)
        print(json.dumps(dict(window=row['window'],subdivisions=row['subdivisions'],cells=8,
            peak_node_budget_nonincreasing=row['peak_node_budget_nonincreasing'])),flush=True)
    if hashes(PATHS)!=before:raise ValueError('block comparison inputs changed')
    return dict(schema='rf-d/bdf-static-block-comparison/v1',environment=env,source_sha256=before,cases=cases,
        blocks=[list(v) for v in law.BLOCKS],block_names=list(law.NAMES),block_partition_fitted=False,
        exponential_terms=law.TERMS,outward_bits=256,weights_changed=False,new_exact_linear_systems=0,new_nonlinear_circuit_solves=0,
        ideal_time_varying_tangent_bound=True,nonlinear_remainder_bound=False,initial_error_known=False,actual_dae_error_bound=False,
        full_path_coverage=False,temporal_error_bound_admitted=False,physical_trajectory_bound=False,audio_admitted=False,deadline_admitted=False,
        numerical_gates_changed=False,prior_reports_modified=False,
        limitation='six fixed physical blocks; noncontiguous selected intervals, unknown anchor and nonlinear remainder')

def save(report):
    if OUTPUT==SUMMARY or OUTPUT in PATHS or SUMMARY in PATHS:raise ValueError('output/input destination collision')
    storage=store(report,OUTPUT)
    summary={k:v for k,v in report.items() if k!='cases'}|dict(storage=storage,cases=[
        {k:c[k] for k in ('window','subdivisions','index','weights','propagation','peak_node_budget_nonincreasing')}|
        dict(prior_peak_zero_anchor_node_upper_v=c['prior_scalar_propagation']['peak_zero_anchor_node_upper_v']) for c in report['cases']])
    SUMMARY.write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n');return summary

if __name__=='__main__':save(generate())
