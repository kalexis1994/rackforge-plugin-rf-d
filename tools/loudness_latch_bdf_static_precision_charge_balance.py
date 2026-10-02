"""Declare charge-law composition and integrated residual; no new circuit solve."""
from decimal import Decimal as D,localcontext
from fractions import Fraction as F
import gzip,json
from pathlib import Path
import loudness_latch_charge_balance as balance
import loudness_latch_bdf_static_precision_dense_charge as dense
import loudness_latch_directional_curvature as curvature
from circuit66_decimal_static import lift
from loudness_latch_bdf_static_precision_integrator import CompensatedBdfNetwork
from bjt_charge_ngspice_probes import model_parameters
from loudness_latch_bdf_doubling_survey import store
from loudness_latch_increment_probes import hashes
from loudness_lab_metadata import environment

ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/'evidence/loudness_latch_bdf_static_precision_charge_balance.json.gz'
SUMMARY=ROOT/'evidence/loudness_latch_bdf_static_precision_charge_balance_summary.json'
PROTOCOL=ROOT/'docs/BIESTABLE_BALANCE_CARGA_PROTOCOLO.md'
PATHS=tuple(dict.fromkeys((*dense.PATHS,Path(__file__).resolve(),Path(balance.__file__).resolve(),PROTOCOL,
    dense.OUTPUT,ROOT/'evidence/loudness_latch_bdf_static_precision_dense_charge_validation.json')))


def evaluated(network,result,precision):
    with localcontext() as ctx:
        ctx.prec=precision
        dp,bp=dense.previous.incidence(network,result['delta_poly_c'])
        dc,bc=dense.previous.incidence(network,result['delta_constitutive_c'])
        difference=[a-b for a,b in zip(dp,dc)];rows=[]
        for row in result['levels']:
            static=row['static_integral_c'];rp=[a+b for a,b in zip(static,dp)];rc=[a+b for a,b in zip(static,dc)]
            vectors=dict(static_integral_c=static,chain_integral_c=row['chain_integral_c'],
                polynomial_balance_c=rp,constitutive_balance_c=rc,
                polynomial_mean_kcl_a=[v/result['duration_s'] for v in rp],
                constitutive_mean_kcl_a=[v/result['duration_s'] for v in rc])
            rows.append(dict(count=row['count'],vectors=vectors,chain_endpoint_gate=row['chain_endpoint_gate'],
                identity=curvature.metrics(rp,[a+b for a,b in zip(rc,difference)])))
        return dict(levels=rows,common=dict(delta_poly_c=result['delta_poly_c'],delta_constitutive_c=result['delta_constitutive_c'],
            bridge_c=result['bridge_c'],dynamic_polynomial_c=dp,dynamic_constitutive_c=dc,
            dynamic_difference_c=difference,mean_branch_v=result['mean_branch_v'],boundary_c=[bp,bc,bp-bc],
            conservation_error_c=[sum(dp,D(0))+bp,sum(dc,D(0))+bc,sum(difference,D(0))+bp-bc]))


def experiment(network,g,prepared,left,right):
    domain=balance.domain_certificate(network,g,prepared,left,right)
    if not domain['passed']:return dict(domain=dense.serialize(domain),failure='whole reconstructed exponential domain not certified')
    a=balance.integrate(network,g,prepared,left,right,80);b=balance.integrate(network,g,prepared,left,right,100)
    aa=evaluated(network,a,80);bb=evaluated(network,b,100);levels=[]
    with localcontext() as ctx:
        ctx.prec=80
        for low,high in zip(aa['levels'],bb['levels']):
            levels.append(dict(count=low['count'],vectors={k:list(map(str,v)) for k,v in low['vectors'].items()},
                precision={k:curvature.metrics(v,high['vectors'][k]) for k,v in low['vectors'].items()},
                identity=low['identity'],chain_endpoint_gate=low['chain_endpoint_gate'],
                static_vs_64=curvature.metrics(aa['levels'][-1]['vectors']['static_integral_c'],low['vectors']['static_integral_c']),
                observed_polynomial_mean_below_10pa=max(map(abs,low['vectors']['polynomial_mean_kcl_a']))<lift(1e-11),
                observed_constitutive_mean_below_10pa=max(map(abs,low['vectors']['constitutive_mean_kcl_a']))<lift(1e-11)))
    return dict(failure=None,domain=dense.serialize(domain),left=dense.serialize(left),right=dense.serialize(right),
        duration_s=str(a['duration_s']),partition=dense.serialize(a['partition']),static_samples_per_precision=a['static_samples'],
        chain_samples_per_precision=a['chain_samples'],levels=levels,
        common={k:list(map(str,v)) for k,v in aa['common'].items()},
        common_precision={k:curvature.metrics(v,bb['common'][k]) for k,v in aa['common'].items()},
        final_quadrature_gate=levels[-2]['static_vs_64']['passed'] and levels[-2]['chain_endpoint_gate']['passed'] and levels[-1]['chain_endpoint_gate']['passed'])


def generate():
    before=hashes(PATHS);env=environment();source=json.loads(gzip.decompress(dense.previous.proxy.REFERENCE.read_bytes()))['windows']
    certificates=json.loads(gzip.decompress(dense.OUTPUT.read_bytes()))['windows']
    network=CompensatedBdfNetwork(200,model_parameters(1,'finite_transit'));g=curvature.graph(network,10.);windows=[];mixed=[]
    for w,cw in zip(source,certificates):
        if w['name']!=cw['name']:raise ValueError('frozen window order changed')
        levels=[]
        for level,cl in zip(w['levels'],cw['levels']):
            rows=[];ref=level['reference']
            if not ref['complete'] or len(ref['samples'])!=64:raise ValueError('frozen coverage absent')
            for index in range(2,64):
                prepared=dense.prepare(network,ref,index);row=experiment(network,g,prepared,F(0),F(1))
                rows.append(dict(index=index,support_sha256=prepared['support_sha256'],result=row))
                certificate=cl['rows'][index-2]['certificate']
                if any(k['intervals'][1]['zero_cover']['brackets'] or k['intervals'][1]['zero_cover']['exact_points'] or
                       k['intervals'][1]['zero_cover']['coincident'] for k in certificate['knees']):
                    mixed.append(dict(window=w['name'],subdivisions=ref['subdivisions'],index=index,
                        result=experiment(network,g,prepared,prepared['u'][-1],F(1))))
            levels.append(dict(subdivisions=ref['subdivisions'],rows=rows,skipped_indices=[0,1]))
        windows.append(dict(name=w['name'],levels=levels));print(json.dumps(dict(window=w['name'],intervals=124)),flush=True)
    if hashes(PATHS)!=before:raise ValueError('charge-balance sources changed')
    return dict(schema='rf-d/bdf-static-charge-balance/v1',environment=env,source_sha256=before,windows=windows,mixed_supports=mixed,
        quadrature_counts=list(balance.COUNTS),final_quadrature_counts=[32,64],root_cover_depth=40,new_nonlinear_solves=0,
        diagnostic_only=True,bridge_is_constitutive_endpoint_difference=True,prior_reports_modified=False,
        integrator_changed=False,physical_trajectory_bound=False,exact_temporal_defect_known=False,
        independent_error_estimator=False,temporal_error_bound_admitted=False,physical_switching_admitted=False,
        audio_admitted=False,deadline_admitted=False,
        limitation='selected noncontiguous reconstructed intervals, not a new trajectory; integrated residual is not a voltage error bound; quadrature differences are not certified remainder bounds')


def row_summary(result):
    if result['failure']:return dict(failure=result['failure'])
    return dict(failure=None,final_quadrature_gate=result['final_quadrature_gate'],
        smooth_pieces=len(result['partition']['smooth']),bridges=len(result['partition']['bridges']),
        levels=[dict(count=l['count'],chain_passed=l['chain_endpoint_gate']['passed'],
            chain_scaled_error=l['chain_endpoint_gate']['maximum_scaled_error'],static_passed=l['static_vs_64']['passed'],
            static_scaled_error=l['static_vs_64']['maximum_scaled_error'],
            maximum_mean_polynomial_a=max(abs(float(v)) for v in l['vectors']['polynomial_mean_kcl_a']),
            maximum_mean_constitutive_a=max(abs(float(v)) for v in l['vectors']['constitutive_mean_kcl_a'])) for l in result['levels']])


def save(report):
    storage=store(report,OUTPUT);windows=[]
    for w in report['windows']:
        levels=[]
        for level in w['levels']:
            rows=[r['result'] for r in level['rows']];valid=[r for r in rows if not r['failure']]
            levels.append(dict(subdivisions=level['subdivisions'],intervals=len(rows),failures=len(rows)-len(valid),
                final_quadrature_passes=sum(r['final_quadrature_gate'] for r in valid),
                common_precision_passes=sum(all(v['passed'] for v in r['common_precision'].values()) for r in valid),
                levels=[dict(count=count,precision_passes=sum(all(v['passed'] for v in r['levels'][j]['precision'].values()) for r in valid),
                    identity_passes=sum(r['levels'][j]['identity']['passed'] for r in valid),
                    static_quadrature_passes=sum(r['levels'][j]['static_vs_64']['passed'] for r in valid),
                    chain_endpoint_passes=sum(r['levels'][j]['chain_endpoint_gate']['passed'] for r in valid),
                    observed_polynomial_mean_passes=sum(r['levels'][j]['observed_polynomial_mean_below_10pa'] for r in valid),
                    observed_constitutive_mean_passes=sum(r['levels'][j]['observed_constitutive_mean_below_10pa'] for r in valid),
                    maximum_mean_polynomial_a=max(abs(float(v)) for r in valid for v in r['levels'][j]['vectors']['polynomial_mean_kcl_a']),
                    maximum_mean_constitutive_a=max(abs(float(v)) for r in valid for v in r['levels'][j]['vectors']['constitutive_mean_kcl_a'])) for j,count in enumerate(balance.COUNTS)]))
        windows.append(dict(name=w['name'],levels=levels))
    summary={k:v for k,v in report.items() if k not in ('windows','mixed_supports')}|dict(storage=storage,windows=windows,
        mixed_supports=[{k:v for k,v in row.items() if k!='result'}|dict(result=row_summary(row['result'])) for row in report['mixed_supports']])
    SUMMARY.write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n');return summary


if __name__=='__main__':save(generate())
