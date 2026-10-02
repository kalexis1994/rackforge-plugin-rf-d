"""Independent proof query on archived rejected rounded exact inverses."""
from fractions import Fraction as F
import gzip,json
from pathlib import Path
import numpy as np
import loudness_latch_bdf_static_precision_continuous_descriptor_exact as prior
from loudness_latch_increment_probes import hashes
from loudness_latch_bdf_doubling_survey import store
from loudness_lab_metadata import environment
ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/'evidence/loudness_latch_bdf_static_precision_descriptor_certificate.json.gz'
SUMMARY=ROOT/'evidence/loudness_latch_bdf_static_precision_descriptor_certificate_summary.json'
PROTOCOL=ROOT/'docs/BIESTABLE_DESCRIPTOR_CERTIFICADO_PROTOCOLO.md'
PATHS=tuple(dict.fromkeys((*prior.PATHS,prior.OUTPUT,prior.SUMMARY,Path(__file__).resolve(),PROTOCOL)))


def backward_witness(h,x):
    identity=np.eye(len(h));denominator=abs(h)@abs(x)+identity
    residual=identity-h@x
    ratios=np.divide(abs(residual),denominator,out=np.zeros_like(residual),where=denominator>0)
    i,j=map(int,np.unravel_index(np.argmax(ratios),ratios.shape))
    terms=[F(float(h[i,k]))*F(float(x[k,j])) for k in range(len(h)) if h[i,k] and x[k,j]]
    exact_residual=F(i==j)-sum(terms,F(0));exact_denominator=sum(map(abs,terms),F(0))+F(i==j)
    return dict(row=i,column=j,binary_residual=str(F(float(residual[i,j]))),
        binary_denominator=str(F(float(denominator[i,j]))),binary_ratio=float(ratios[i,j]),
        exact_residual=str(exact_residual),exact_denominator=str(exact_denominator),
        exact_componentwise_ratio=str(abs(exact_residual)/exact_denominator if exact_denominator else F(0)),
        exact_nonzero_products=len(terms))


def generate():
    before=hashes(PATHS);env=environment();source=json.loads(gzip.decompress(prior.OUTPUT.read_bytes()));cases=[]
    for old in source['cases']:
        row={k:v for k,v in old.items() if k!='failure'}|dict(rounded_inverse_failure=old['failure'],failure=None)
        h=np.array(old['descriptor_binary']);x=np.array(old['inverse_binary'])
        scales=np.max(abs(h/np.max(abs(h),axis=1)[:,None]),axis=0)
        row['binary_backward_witness']=backward_witness(h,x)
        try:
            bounds,certificate=prior.prior.law.inverse_certificate(h.tolist(),x.tolist(),scales.tolist())
            row['inverse_certificate']=certificate;v=old['forcing_inputs']
            row['frozen_budget']=prior.prior.law.frozen_budget(x.tolist(),bounds,94,
                list(map(F,v['nodal_l1_c'])),list(map(F,v['constraint_l1_v_s'])),
                list(map(F,v['nodal_point_a'])),list(map(F,v['constraint_point_v'])),F(old['duration_s']))
        except (ValueError,OverflowError) as exc:row['failure']=str(exc)
        cases.append(row)
        print(json.dumps(dict(window=row['window'],subdivisions=row['subdivisions'],failure=row['failure'],
            inverse_certified='inverse_certificate' in row,
            growth_supported=row.get('frozen_budget',{}).get('growth_supported'))),flush=True)
    if hashes(PATHS)!=before:raise ValueError('certificate inputs changed')
    return {k:v for k,v in source.items() if k not in ('environment','source_sha256','cases','schema')}|dict(
        schema='rf-d/bdf-static-descriptor-certificate/v1',environment=env,source_sha256=before,cases=cases,
        rejected_binary_gate_preserved=True,rounded_inverse_numerically_admitted=False,
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
