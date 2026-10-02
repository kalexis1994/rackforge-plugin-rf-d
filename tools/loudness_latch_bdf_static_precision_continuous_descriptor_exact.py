"""Declared exact coefficient solve variant, preserving the failed floating run."""
import gzip,json
from pathlib import Path
import numpy as np
from fractions import Fraction as F
import loudness_latch_bdf_static_precision_continuous_descriptor as prior
from loudness_latch_bdf_rational_solve import solve
from loudness_latch_bdf_transfer_solve import backward_errors
from loudness_latch_increment_probes import hashes
from loudness_latch_bdf_doubling_survey import store
from loudness_lab_metadata import environment
ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/'evidence/loudness_latch_bdf_static_precision_continuous_descriptor_exact.json.gz'
SUMMARY=ROOT/'evidence/loudness_latch_bdf_static_precision_continuous_descriptor_exact_summary.json'
PROTOCOL=ROOT/'docs/BIESTABLE_DESCRIPTOR_EXACTO_PROTOCOLO.md'
PATHS=tuple(dict.fromkeys((*prior.PATHS,prior.OUTPUT,prior.SUMMARY,Path(__file__).resolve(),PROTOCOL,
    ROOT/'tools/loudness_latch_bdf_rational_solve.py')))


def generate():
    before=hashes(PATHS);env=environment();source=json.loads(gzip.decompress(prior.OUTPUT.read_bytes()));cases=[]
    for old in source['cases']:
        row={k:v for k,v in old.items() if k!='failure'}|dict(prior_failure=old['failure'],failure=None)
        h=np.array(old['descriptor_binary']);row_scales=np.max(abs(h),axis=1)
        columns=np.max(abs(h/row_scales[:,None]),axis=0)
        try:
            inverse,exact=solve(h,np.eye(len(h)));_,errors=backward_errors(h,np.eye(len(h)),inverse)
            row.update(inverse_binary=inverse.tolist(),exact_solve=exact,backward_errors=errors,
                backward_gate_passed=max(errors.values())<1e-10)
            if not row['backward_gate_passed']:raise ValueError('rounded rational inverse failed unchanged backward gate')
            bounds,certificate=prior.law.inverse_certificate(h.tolist(),inverse.tolist(),columns.tolist())
            row['inverse_certificate']=certificate;v=old['forcing_inputs']
            row['frozen_budget']=prior.law.frozen_budget(inverse.tolist(),bounds,94,
                list(map(F,v['nodal_l1_c'])),list(map(F,v['constraint_l1_v_s'])),
                list(map(F,v['nodal_point_a'])),list(map(F,v['constraint_point_v'])),F(old['duration_s']))
        except (ValueError,OverflowError,np.linalg.LinAlgError) as exc:row['failure']=str(exc)
        cases.append(row)
        print(json.dumps(dict(window=row['window'],subdivisions=row['subdivisions'],failure=row['failure'],
            inverse_certified='inverse_certificate' in row,
            growth_supported=row.get('frozen_budget',{}).get('growth_supported'))),flush=True)
    if hashes(PATHS)!=before:raise ValueError('exact descriptor sources changed')
    return {k:v for k,v in source.items() if k not in ('environment','source_sha256','cases','schema')}|dict(
        schema='rf-d/bdf-static-continuous-descriptor-exact/v1',environment=env,source_sha256=before,cases=cases,
        prior_failed_cases_preserved=True,coefficient_matrix_changed=False,exact_linear_systems=8)


def save(report):
    storage=store(report,OUTPUT)
    summary={k:v for k,v in report.items() if k!='cases'}|dict(storage=storage,cases=[
        {k:r[k] for k in ('window','subdivisions','index','duration_s','decimal80_100_rounded_descriptor_equal','incidence_rank','failure')}|
        dict(backward_errors=r.get('backward_errors'),exact_solve=r.get('exact_solve'),
             inverse_certified='inverse_certificate' in r,
             inverse_contraction_upper=r.get('inverse_certificate',{}).get('contraction_upper'),
             frozen_budget=r.get('frozen_budget')) for r in report['cases']])
    SUMMARY.write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n');return summary


if __name__=='__main__':save(generate())
