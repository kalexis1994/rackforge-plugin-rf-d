"""Independent proof query on archived rejected rounded exact inverses."""
from fractions import Fraction as F
import gzip,json
from pathlib import Path
import numpy as np
import loudness_latch_bdf_static_precision_descriptor_certificate as prior
import loudness_latch_descriptor_forcing_budget as budget
from loudness_latch_increment_probes import hashes
from loudness_latch_bdf_doubling_survey import store
from loudness_lab_metadata import environment
ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/'evidence/loudness_latch_bdf_static_precision_descriptor_forcing_norm.json.gz'
SUMMARY=ROOT/'evidence/loudness_latch_bdf_static_precision_descriptor_forcing_norm_summary.json'
PROTOCOL=ROOT/'docs/BIESTABLE_FORZAMIENTO_NORMA_PROTOCOLO.md'
PATHS=tuple(dict.fromkeys((*prior.PATHS,prior.OUTPUT,prior.SUMMARY,Path(__file__).resolve(),Path(budget.__file__).resolve(),PROTOCOL)))


def generate():
    before=hashes(PATHS);env=environment();source=json.loads(gzip.decompress(prior.OUTPUT.read_bytes()));cases=[]
    for old in source['cases']:
        row={k:v for k,v in old.items() if k not in ('failure','frozen_budget')}|dict(failure=None,
            prior_uniform_budget_rejected_reason='max_i integral |f_i| is not an upper bound for integral max_i |f_i|')
        certificate=old['inverse_certificate'];q=F(certificate['contraction_upper'])
        scales=list(map(F,certificate['column_scales']));peaks=list(map(F,certificate['error_column_peaks']))
        errors=[[q/(1-q)*v/di for v in peaks] for di in scales]
        v=old['forcing_inputs']
        row['frozen_budget']=budget.frozen_budget(old['inverse_binary'],errors,94,
            list(map(F,v['nodal_l1_c'])),list(map(F,v['constraint_l1_v_s'])),
            list(map(F,v['nodal_point_a'])),list(map(F,v['constraint_point_v'])),F(old['duration_s']))
        cases.append(row)
        print(json.dumps(dict(window=row['window'],subdivisions=row['subdivisions'],failure=row['failure'],
            inverse_certified='inverse_certificate' in row,
            growth_supported=row.get('frozen_budget',{}).get('growth_supported'))),flush=True)
    if hashes(PATHS)!=before:raise ValueError('certificate inputs changed')
    return {k:v for k,v in source.items() if k not in ('environment','source_sha256','cases','schema')}|dict(
        schema='rf-d/bdf-static-descriptor-forcing-norm/v1',environment=env,source_sha256=before,cases=cases,
        rejected_binary_gate_preserved=True,rounded_inverse_numerically_admitted=False,prior_uniform_budgets_valid=False,
        new_exact_linear_systems=0,new_nonlinear_circuit_solves=0)


def save(report):
    storage=store(report,OUTPUT)
    summary={k:v for k,v in report.items() if k!='cases'}|dict(storage=storage,cases=[
        {k:r[k] for k in ('window','subdivisions','index','duration_s','incidence_rank','failure','binary_backward_witness','backward_gate_passed')}|
        dict(inverse_certified='inverse_certificate' in r,
            inverse_contraction_upper=r.get('inverse_certificate',{}).get('contraction_upper'),
            frozen_budget=r.get('frozen_budget')) for r in report['cases']])
    SUMMARY.write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n');return summary


if __name__=='__main__':save(generate())
