"""Balanced proof radii, unchanged fixed metric and conversion maps."""
from fractions import Fraction as F
from pathlib import Path
import gzip,json
import loudness_latch_junction_balanced as law
import loudness_latch_bdf_static_precision_junction_directed as prior
from loudness_latch_increment_probes import hashes
from loudness_latch_bdf_doubling_survey import store
from loudness_lab_metadata import environment
ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/'evidence/loudness_latch_bdf_static_precision_junction_balanced.json.gz'
SUMMARY=ROOT/'evidence/loudness_latch_bdf_static_precision_junction_balanced_summary.json'
PROTOCOL=ROOT/'docs/BIESTABLE_JUNTURAS_BALANCEADA_PROTOCOLO.md'
PATHS=tuple(dict.fromkeys((*prior.PATHS,prior.OUTPUT,prior.SUMMARY,
    ROOT/'evidence/loudness_latch_bdf_static_precision_junction_directed_validation.json',
    ROOT/'evidence/loudness_latch_bdf_static_precision_directed_inputs.json.gz',
    ROOT/'evidence/loudness_latch_bdf_static_precision_directed_inputs_summary.json',
    ROOT/'evidence/loudness_latch_bdf_static_precision_directed_inputs_validation.json',
    Path(__file__).resolve(),Path(law.__file__).resolve(),PROTOCOL)))
def read(p):return json.loads(gzip.decompress(p.read_bytes()))

def generate():
    before=hashes(PATHS);env=environment();source=read(prior.OUTPUT);metric=read(prior.prior.OUTPUT);modal=read(prior.prior.prior.OUTPUT);rms=read(prior.prior.prior.prior.prior.OUTPUT);cases=[]
    for index,old in enumerate(source['cases']):
        c={k:old[k] for k in ('window','subdivisions','index','support_sha256','weights','binary_backward_gate_still_rejected','metric_accepted','metric_candidate_sha256')}|dict(source_directed_case_index=index,balance=None,cells=[],propagation=None,peak_node_budget_nonincreasing=None,all_internal_cells_contracting=False)
        if old['metric_accepted']:
            c['balance']=law.balance(old['basis']);fixed=metric['cases'][old['source_metric_case_index']];m=modal['cases'][fixed['source_modal_case_index']]
            if law.box.digest(fixed['metric_candidate'])!=old['metric_candidate_sha256'] or m['support_sha256']!=old['support_sha256'] or m['weights']!=old['weights']:raise ValueError('fixed metric or coordinates differ')
            if len(old['cells'])!=8 or len(fixed['cells'])!=8:raise ValueError('complete frozen cells required')
            cells=[]
            for cell in old['cells']:
                i=cell['source_cell_index'];certificate=law.rate(old['basis'],cell['rate_certificate'],c['balance'])
                metrics=law.refine_metrics(fixed['cells'][i]['metrics'],certificate)
                forcing=rms['cases'][m['source_spectral_case_index']]['cells'][i]['forcing_inputs']
                cells.append(dict(forcing_inputs=forcing,metrics=metrics));c['cells'].append(dict(source_cell_index=i,rate_certificate=certificate,comparison_per_s=metrics['comparison_per_s']))
            c['propagation']=prior.prior.law.propagate(cells)
            c['peak_node_budget_nonincreasing']=F(c['propagation']['peak_zero_anchor_node_upper_v'])<=F(old['propagation']['peak_zero_anchor_node_upper_v'])
            c['all_internal_cells_contracting']=all(v['rate_certificate']['internal_time_varying_contraction_certified'] for v in c['cells'])
        cases.append(c)
        print(json.dumps(dict(window=c['window'],subdivisions=c['subdivisions'],metric_accepted=c['metric_accepted'],all_internal_cells_contracting=c['all_internal_cells_contracting'],peak_node_budget_nonincreasing=c['peak_node_budget_nonincreasing'])),flush=True)
    if hashes(PATHS)!=before:raise ValueError('balanced proof inputs changed')
    return dict(schema='rf-d/bdf-static-junction-balanced/v1',environment=env,source_sha256=before,cases=cases,
        balance_bits=law.BALANCE_BITS,bisections=law.BISECTIONS,exact_rate_ldlt_queries=sum(len(c['cells']) for c in cases)*(law.BISECTIONS+1),
        proof_weights_constant_within_each_interval=True,proof_weights_fitted_to_results=False,
        only_junction_diagonal_changed=True,prior_metric_components_reused_by_reference=True,
        metric_changed=False,norm_changed=False,anchor_changed=False,weights_changed=False,block_partition_changed=False,
        new_metric_candidates=0,new_circuit_inverse_systems=0,new_nonlinear_circuit_solves=0,initial_anchor_reference='common weighted infinity',
        metric_common_across_all_intervals=False,complete_coupled_contraction_certified=False,nonlinear_remainder_bound=False,
        initial_error_known=False,actual_dae_error_bound=False,full_path_coverage=False,temporal_error_bound_admitted=False,
        physical_trajectory_bound=False,audio_admitted=False,deadline_admitted=False,numerical_gates_changed=False,prior_reports_modified=False,
        limitation='fixed proof balance only; same metric and conversions, unknown anchor and nonlinear remainder')

def save(report):
    if OUTPUT==SUMMARY or OUTPUT in PATHS or SUMMARY in PATHS:raise ValueError('output/input destination collision')
    storage=store(report,OUTPUT)
    summary={k:v for k,v in report.items() if k!='cases'}|dict(storage=storage,cases=[
        {k:c[k] for k in ('window','subdivisions','index','metric_accepted','all_internal_cells_contracting','peak_node_budget_nonincreasing','propagation')}|
        dict(rate_uppers_per_s=[v['rate_certificate']['mu_metric_upper_per_s'] for v in c['cells']],strictly_narrower_cells=sum(v['rate_certificate']['strictly_narrower'] for v in c['cells'])) for c in report['cases']])
    SUMMARY.write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n');return summary
if __name__=='__main__':save(generate())
