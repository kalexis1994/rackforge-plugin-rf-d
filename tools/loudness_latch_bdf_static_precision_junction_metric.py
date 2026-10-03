"""Common within-interval quadratic metric, certified cells and complete conversions."""
from fractions import Fraction as F
from pathlib import Path
import gzip,json
import loudness_latch_junction_metric as law
import loudness_latch_bdf_static_precision_junction_modal as prior
from loudness_latch_cell_propagation import structured_inverse
from loudness_latch_increment_probes import hashes
from loudness_latch_bdf_doubling_survey import store
from loudness_lab_metadata import environment
ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/'evidence/loudness_latch_bdf_static_precision_junction_metric.json.gz'
SUMMARY=ROOT/'evidence/loudness_latch_bdf_static_precision_junction_metric_summary.json'
PROTOCOL=ROOT/'docs/BIESTABLE_JUNTURAS_METRICA_PROTOCOLO.md'
PATHS=tuple(dict.fromkeys((*prior.PATHS,prior.OUTPUT,prior.SUMMARY,
    ROOT/'evidence/loudness_latch_bdf_static_precision_junction_modal_validation.json',
    ROOT/'evidence/loudness_latch_bdf_static_precision_modal_inputs.json.gz',
    ROOT/'evidence/loudness_latch_bdf_static_precision_modal_inputs_summary.json',
    ROOT/'evidence/loudness_latch_bdf_static_precision_modal_inputs_validation.json',
    Path(__file__).resolve(),Path(law.__file__).resolve(),PROTOCOL)))
def read(p):return json.loads(gzip.decompress(p.read_bytes()))

def generate():
    before=hashes(PATHS);env=environment();modal=read(prior.OUTPUT);weighted=read(prior.weighted.OUTPUT);rms=read(prior.prior.prior.OUTPUT);spectral=read(prior.prior.OUTPUT);cases=[]
    for index,old in enumerate(modal['cases']):
        generators=[cell['result']['generator_intervals_per_s'] for cell in old['cells']];metric=law.candidate(generators)
        result={k:old[k] for k in ('window','subdivisions','index','support_sha256','weights','binary_backward_gate_still_rejected')}|dict(source_modal_case_index=index,metric_candidate=metric,cells=[],propagation=None)
        baseline=spectral['cases'][old['source_spectral_case_index']]['propagation'];result['prior_spectral_propagation']=baseline
        if metric['accepted']:
            source=weighted['cases'][old['source_weighted_case_index']];previous=rms['cases'][old['source_spectral_case_index']]
            if not source['support_sha256']==old['support_sha256']==previous['support_sha256'] or not source['weights']==old['weights']==previous['weights']:raise ValueError('common source coordinates differ')
            q=max(F(v['contraction_upper']) for v in source['ideal_temporal_cover']);cells=[]
            for i,(cover,cell) in enumerate(zip(source['ideal_temporal_cover'],old['cells'])):
                certificate=law.rate(metric,generators[i]);inverse,cert=structured_inverse(source['inverse_binary'],source['inverse_certificate']['column_scales'],cover,q)
                if cert!=previous['cells'][i]['inverse_certificate']:raise ValueError('frozen inverse reconstruction differs')
                rebuilt=law.box.generator([[inverse[j][k] for k in range(115,119)] for j in range(115,119)],source['weights'][21:])
                if law.box.pack(rebuilt)!=generators[i]:raise ValueError('signed junction generator differs')
                forcing=previous['cells'][i]['forcing_inputs'];metrics=law.metrics(inverse,source['weights'],forcing,previous['cells'][i]['metrics'],metric,certificate)
                cells.append(dict(forcing_inputs=forcing,metrics=metrics))
                result['cells'].append(dict(source_cell_index=i,rate_certificate=certificate,metrics=metrics))
            if len(cells)!=8:raise ValueError('complete eight-cell common metric required')
            result['propagation']=law.propagate(cells)
            result['peak_node_budget_nonincreasing']=F(result['propagation']['peak_zero_anchor_node_upper_v'])<=F(baseline['peak_zero_anchor_node_upper_v'])
            result['all_internal_cells_contracting']=all(c['rate_certificate']['internal_time_varying_contraction_certified'] for c in result['cells'])
        else:result.update(peak_node_budget_nonincreasing=None,all_internal_cells_contracting=False)
        cases.append(result)
        print(json.dumps(dict(window=old['window'],subdivisions=old['subdivisions'],metric_accepted=metric['accepted'],all_internal_cells_contracting=result['all_internal_cells_contracting'],peak_node_budget_nonincreasing=result['peak_node_budget_nonincreasing'])),flush=True)
    if hashes(PATHS)!=before:raise ValueError('quadratic metric sources changed')
    return dict(schema='rf-d/bdf-static-junction-metric/v1',environment=env,source_sha256=before,cases=cases,
        candidate_policy='one Lyapunov candidate from rounded center of whole generator hull, no search or alternate metric',
        candidate_bits=law.CANDIDATE_BITS,bisections=law.BISECTIONS,metric_constant_within_each_interval=True,
        metric_common_across_all_intervals=False,initial_anchor_reference='common weighted infinity',
        norm_changed=True,weights_changed=False,block_partition_changed=False,metric_systems_attempted=len(cases),
        circuit_inverse_systems=0,new_nonlinear_circuit_solves=0,comparison_variants_intersected=False,
        complete_coupled_contraction_certified=False,nonlinear_remainder_bound=False,initial_error_known=False,
        actual_dae_error_bound=False,full_path_coverage=False,temporal_error_bound_admitted=False,
        physical_trajectory_bound=False,audio_admitted=False,deadline_admitted=False,numerical_gates_changed=False,prior_reports_modified=False,
        limitation='fixed metric per noncontiguous interval; interval rate proofs and coupled tangent bounds only, unknown anchor and nonlinear remainder')

def save(report):
    if OUTPUT==SUMMARY or OUTPUT in PATHS or SUMMARY in PATHS:raise ValueError('output/input destination collision')
    storage=store(report,OUTPUT)
    summary={k:v for k,v in report.items() if k!='cases'}|dict(storage=storage,cases=[
        {k:c[k] for k in ('window','subdivisions','index','all_internal_cells_contracting','peak_node_budget_nonincreasing','propagation','prior_spectral_propagation')}|
        dict(metric_accepted=c['metric_candidate']['accepted'],rejection=c['metric_candidate']['rejection'],
             rate_uppers_per_s=[v['rate_certificate']['mu_metric_upper_per_s'] for v in c['cells']]) for c in report['cases']])
    SUMMARY.write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n');return summary
if __name__=='__main__':save(generate())
