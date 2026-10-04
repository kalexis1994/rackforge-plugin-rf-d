"""Conditional common-anchor target; no entry error or nonlinear remainder proof."""
from fractions import Fraction as F
from pathlib import Path
import gzip,json
import loudness_latch_anchor_budget as law
import loudness_latch_bdf_static_precision_junction_balanced as prior
from loudness_latch_increment_probes import hashes
from loudness_latch_bdf_doubling_survey import store
from loudness_lab_metadata import environment
ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/'evidence/loudness_latch_bdf_static_precision_anchor_budget.json.gz'
SUMMARY=ROOT/'evidence/loudness_latch_bdf_static_precision_anchor_budget_summary.json'
PROTOCOL=ROOT/'docs/BIESTABLE_PRESUPUESTO_ANCLAJE_PROTOCOLO.md'
THRESHOLD=F(1,1000)
RESERVES=(F(0),THRESHOLD/4,THRESHOLD/2)
PATHS=tuple(dict.fromkeys((*prior.PATHS,prior.OUTPUT,prior.SUMMARY,
    ROOT/'evidence/loudness_latch_bdf_static_precision_junction_balanced_validation.json',
    ROOT/'evidence/loudness_latch_bdf_static_precision_balanced_inputs.json.gz',
    ROOT/'evidence/loudness_latch_bdf_static_precision_balanced_inputs_summary.json',
    ROOT/'evidence/loudness_latch_bdf_static_precision_balanced_inputs_validation.json',
    Path(__file__).resolve(),Path(law.__file__).resolve(),PROTOCOL)))
def read(p):return json.loads(gzip.decompress(p.read_bytes()))
def generate():
    before=hashes(PATHS);env=environment();source=read(prior.OUTPUT);directed=read(prior.prior.OUTPUT);metric=read(prior.prior.prior.OUTPUT);cases=[]
    for index,old in enumerate(source['cases']):
        c={k:old[k] for k in ('window','subdivisions','index','support_sha256','weights','metric_accepted','metric_candidate_sha256','binary_backward_gate_still_rejected')}|dict(source_balanced_case_index=index,affine_constraints=[],budgets=[],propagation_sha256=None)
        if old['metric_accepted']:
            previous=directed['cases'][old['source_directed_case_index']];fixed=metric['cases'][previous['source_metric_case_index']]
            if c['metric_candidate_sha256']!=prior.law.box.digest(fixed['metric_candidate']) or c['weights']!=fixed['weights'] or c['support_sha256']!=fixed['support_sha256']:raise ValueError('source metric or coordinates differ')
            if len(old['propagation']['trace'])!=8 or len(fixed['cells'])!=8:raise ValueError('complete frozen eight-cell proof required')
            maps=[v['metrics'] for v in fixed['cells']];rows=law.constraints(old['propagation']['trace'],maps);c['affine_constraints']=rows
            if len(rows)!=752:raise ValueError('complete 94-node eight-cell affine family required')
            c['propagation_sha256']=prior.law.box.digest(old['propagation'])
            for reserve in RESERVES:
                paired=law.capacity(rows,THRESHOLD,reserve);separated=law.separated_capacity(rows,THRESHOLD,reserve)
                if paired['status']!='finite' or separated['status']!='finite':raise ValueError('frozen selected case lacks finite conditional capacity')
                c['budgets'].append(dict(reserve_v=str(reserve),paired=paired,separated=separated,paired_nonworse=F(paired['anchor_upper_v'])>=F(separated['anchor_upper_v'])))
        cases.append(c);print(json.dumps(dict(window=c['window'],subdivisions=c['subdivisions'],metric_accepted=c['metric_accepted'],constraints=len(c['affine_constraints']))),flush=True)
    if hashes(PATHS)!=before:raise ValueError('anchor budget sources changed')
    return dict(schema='rf-d/bdf-static-anchor-budget/v1',environment=env,source_sha256=before,cases=cases,
        nodal_gate_v=str(THRESHOLD),hypothetical_reserves_v=list(map(str,RESERVES)),affine_constraint_count=sum(len(c['affine_constraints']) for c in cases),
        initial_anchor_reference='common weighted infinity',conditional_sufficient_target_only=True,exact_for_archived_affine_majorants=True,
        nonlinear_reserve_proven=False,metric_changed=False,norm_changed=False,anchor_changed=False,weights_changed=False,block_partition_changed=False,
        new_circuit_inverse_systems=0,new_nonlinear_circuit_solves=0,new_rate_certificates=0,
        initial_error_known=False,nonlinear_remainder_bound=False,actual_dae_error_bound=False,full_path_coverage=False,
        temporal_error_bound_admitted=False,physical_trajectory_bound=False,audio_admitted=False,deadline_admitted=False,
        numerical_gates_changed=False,prior_reports_modified=False,
        limitation='capacity of frozen affine upper bounds only; reserves hypothetical, no measured incoming error, no global coverage')
def save(report):
    if OUTPUT==SUMMARY or OUTPUT in PATHS or SUMMARY in PATHS:raise ValueError('output/input destination collision')
    storage=store(report,OUTPUT);summary={k:v for k,v in report.items() if k!='cases'}|dict(storage=storage,cases=[{k:v for k,v in c.items() if k!='affine_constraints'}|dict(constraint_count=len(c['affine_constraints'])) for c in report['cases']])
    SUMMARY.write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n');return summary
if __name__=='__main__':save(generate())
