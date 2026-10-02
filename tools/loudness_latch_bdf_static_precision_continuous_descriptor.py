"""Eight declared frozen continuous descriptor diagnostics, no orbit solve."""
from fractions import Fraction as F
import gzip,json
from pathlib import Path
import numpy as np
import loudness_latch_continuous_descriptor as law
import loudness_latch_bdf_static_precision_dense_charge as dense
import loudness_latch_bdf_static_precision_correlated_enclosure as prior
from loudness_latch_increment_probes import hashes
from loudness_latch_bdf_doubling_survey import store
from loudness_lab_metadata import environment

ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/'evidence/loudness_latch_bdf_static_precision_continuous_descriptor.json.gz'
SUMMARY=ROOT/'evidence/loudness_latch_bdf_static_precision_continuous_descriptor_summary.json'
PROTOCOL=ROOT/'docs/BIESTABLE_DESCRIPTOR_CONTINUO_PROTOCOLO.md'
PATHS=tuple(dict.fromkeys((*prior.PATHS,prior.OUTPUT,
    ROOT/'evidence/loudness_latch_bdf_static_precision_correlated_enclosure_validation.json',
    Path(__file__).resolve(),Path(law.__file__).resolve(),PROTOCOL)))
INDEX=31
QUERY=F(1,2)


def generate():
    before=hashes(PATHS);env=environment()
    source=json.loads(gzip.decompress(dense.previous.proxy.REFERENCE.read_bytes()))['windows']
    previous=json.loads(gzip.decompress(prior.OUTPUT.read_bytes()))['windows']
    network=dense.CompensatedBdfNetwork(200,dense.model_parameters(1,'finite_transit'));g=dense.curvature.graph(network,10.)
    cases=[]
    for w,pw in zip(source,previous):
        if w['name']!=pw['name']:raise ValueError('frozen window mismatch')
        for level,pl in zip(w['levels'],pw['levels']):
            prepared=dense.prepare(network,level['reference'],INDEX);r=pl['rows'][INDEX-2]
            if prepared['support_sha256']!=r['support_sha256']:raise ValueError('frozen support mismatch')
            with dense.localcontext() as ctx:
                ctx.prec=120
                x=[dense.law.decimal_fraction(dense.poly.evaluate(p,QUERY)) for p in prepared['x']]
            h80,meta=law.descriptor(network,g,x,80);h100,_=law.descriptor(network,g,x,100)
            h=np.array([[float(v) for v in row] for row in h100])
            comparison=np.array_equal(h,np.array([[float(v) for v in row] for row in h80]))
            row=dict(window=w['name'],subdivisions=level['reference']['subdivisions'],index=INDEX,
                query=str(QUERY),duration_s=str(prepared['h']),support_sha256=prepared['support_sha256'],
                node_query_v=list(map(str,x)),descriptor_binary=h.tolist(),metadata=meta,
                decimal80_100_rounded_descriptor_equal=comparison,
                incidence_rank=law.exact_rank(np.array(meta['incidence_columns']).T.tolist()),failure=None)
            result=r['result'];r_l1=list(map(F,result['constitutive_l1_upper_c']));r_point=list(map(F,result['constitutive_pointwise_upper_a']))
            d_point=[max(map(abs,dense.poly.bernstein(p))) for p in prepared['equations']]+[F(0)]*4
            d_l1=[prepared['h']*v for v in d_point]
            row['forcing_inputs']=dict(nodal_l1_c=list(map(str,r_l1)),nodal_point_a=list(map(str,r_point)),
                constraint_l1_v_s=list(map(str,d_l1)),constraint_point_v=list(map(str,d_point)),
                nonlinear_charge_reconstruction_replaced_by_constitutive_law=True)
            try:
                inverse,audit=law.solve(h,np.eye(len(h)))
                row.update(inverse_binary=inverse.tolist(),linear_solve=audit)
                errors,certificate=law.inverse_certificate(h.tolist(),inverse.tolist(),audit['column_scales'])
                row['inverse_certificate']=certificate
                row['frozen_budget']=law.frozen_budget(inverse.tolist(),errors,94,r_l1,d_l1,r_point,d_point,prepared['h'])
            except (ValueError,OverflowError,np.linalg.LinAlgError) as exc:
                row['failure']=str(exc)
            cases.append(row)
            print(json.dumps(dict(window=row['window'],subdivisions=row['subdivisions'],failure=row['failure'],
                inverse_certified='inverse_certificate' in row,
                growth_supported=row.get('frozen_budget',{}).get('growth_supported'))),flush=True)
    if hashes(PATHS)!=before:raise ValueError('descriptor inputs changed during measurement')
    return dict(schema='rf-d/bdf-static-continuous-descriptor/v1',environment=env,source_sha256=before,cases=cases,
        index=INDEX,query=str(QUERY),node_count=94,memory_count=25,descriptor_dimension=119,
        new_nonlinear_circuit_solves=0,prior_reports_modified=False,integrator_changed=False,numerical_gates_changed=False,
        nonlinear_charge_interpolants_replaced_in_diagnostic=True,physical_trajectory_bound=False,
        full_path_coverage=False,actual_time_varying_propagation_bound=False,temporal_error_bound_admitted=False,
        audio_admitted=False,deadline_admitted=False,
        limitation='exact inverse and Gronwall bound only for each frozen binary coefficient descriptor; no coefficient rounding enclosure, time variation, nonlinear remainder or known initial error')


def save(report):
    storage=store(report,OUTPUT)
    summary={k:v for k,v in report.items() if k!='cases'}|dict(storage=storage,cases=[
        {k:r[k] for k in ('window','subdivisions','index','duration_s','decimal80_100_rounded_descriptor_equal','incidence_rank','failure')}|
        dict(inverse_certified='inverse_certificate' in r,
             inverse_contraction_upper=r.get('inverse_certificate',{}).get('contraction_upper'),
             frozen_budget=r.get('frozen_budget')) for r in report['cases']])
    SUMMARY.write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n');return summary


if __name__=='__main__':save(generate())
