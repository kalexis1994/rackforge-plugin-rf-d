"""Declared Gauss variant; prior underresolved Simpson evidence stays frozen."""
from decimal import Decimal as D,localcontext
from fractions import Fraction as F
import gzip,json
from pathlib import Path
import loudness_latch_charge_gauss as gauss
import loudness_latch_bdf_static_precision_charge_balance as old
import loudness_latch_directional_curvature as curvature
from circuit66_decimal_static import lift
from loudness_latch_bdf_static_precision_integrator import CompensatedBdfNetwork
from bjt_charge_ngspice_probes import model_parameters
from loudness_latch_bdf_doubling_survey import store
from loudness_latch_increment_probes import hashes
from loudness_lab_metadata import environment

ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/'evidence/loudness_latch_bdf_static_precision_charge_gauss.json.gz'
SUMMARY=ROOT/'evidence/loudness_latch_bdf_static_precision_charge_gauss_summary.json'
PROTOCOL=ROOT/'docs/BIESTABLE_BALANCE_GAUSS_PROTOCOLO.md'
PATHS=tuple(dict.fromkeys((*old.PATHS,Path(__file__).resolve(),Path(gauss.__file__).resolve(),PROTOCOL,
    old.OUTPUT,ROOT/'evidence/loudness_latch_bdf_static_precision_charge_balance_validation.json')))


def point(network,g,prepared,left,right,rules,previous):
    a=gauss.integrate(network,g,prepared,left,right,rules[80],80);b=gauss.integrate(network,g,prepared,left,right,rules[100],100)
    aa=old.evaluated(network,a,80);bb=old.evaluated(network,b,100);levels=[]
    with localcontext() as ctx:
        ctx.prec=80
        for lo,hi in zip(aa['levels'],bb['levels']):
            levels.append(dict(order=lo['count'],vectors={k:list(map(str,v)) for k,v in lo['vectors'].items()},
                precision={k:curvature.metrics(v,hi['vectors'][k]) for k,v in lo['vectors'].items()},identity=lo['identity'],
                chain_endpoint_gate=lo['chain_endpoint_gate'],
                static_vs_16=curvature.metrics(aa['levels'][-1]['vectors']['static_integral_c'],lo['vectors']['static_integral_c']),
                observed_polynomial_mean_below_10pa=max(map(abs,lo['vectors']['polynomial_mean_kcl_a']))<lift(1e-11),
                observed_constitutive_mean_below_10pa=max(map(abs,lo['vectors']['constitutive_mean_kcl_a']))<lift(1e-11)))
        simpson=curvature.metrics(aa['levels'][-1]['vectors']['static_integral_c'],list(map(D,previous['levels'][-1]['vectors']['static_integral_c'])))
    return dict(levels=levels,common={k:list(map(str,v)) for k,v in aa['common'].items()},
        common_precision={k:curvature.metrics(v,bb['common'][k]) for k,v in aa['common'].items()},
        partition=old.dense.serialize(a['partition']),simpson64_vs_gauss16=simpson,
        final_quadrature_gate=levels[1]['static_vs_16']['passed'] and all(l['chain_endpoint_gate']['passed'] for l in levels[1:]))


def generate():
    before=hashes(PATHS);env=environment();source=json.loads(gzip.decompress(old.dense.previous.proxy.REFERENCE.read_bytes()))['windows']
    prior=json.loads(gzip.decompress(old.OUTPUT.read_bytes()));network=CompensatedBdfNetwork(200,model_parameters(1,'finite_transit'))
    g=curvature.graph(network,10.);rules={p:{n:gauss.rule(n,p) for n in gauss.ORDERS} for p in (80,100)};windows=[];mixed=[]
    for w,pw in zip(source,prior['windows']):
        if w['name']!=pw['name']:raise ValueError('frozen order changed')
        levels=[]
        for level,pl in zip(w['levels'],pw['levels']):
            rows=[];ref=level['reference']
            for index in range(2,64):
                prepared=old.dense.prepare(network,ref,index);pr=pl['rows'][index-2]['result']
                if pr['failure'] or not pr['domain']['passed']:raise ValueError('inherited domain certificate absent')
                r=point(network,g,prepared,F(0),F(1),rules,pr)
                rows.append(dict(index=index,support_sha256=prepared['support_sha256'],result=r))
                for m in prior['mixed_supports']:
                    if (m['window'],m['subdivisions'],m['index'])==(w['name'],ref['subdivisions'],index):
                        mixed.append(dict(window=w['name'],subdivisions=ref['subdivisions'],index=index,
                            result=point(network,g,prepared,prepared['u'][-1],F(1),rules,m['result'])))
            levels.append(dict(subdivisions=ref['subdivisions'],rows=rows))
        windows.append(dict(name=w['name'],levels=levels));print(json.dumps(dict(window=w['name'],gauss_intervals=124)),flush=True)
    if hashes(PATHS)!=before:raise ValueError('Gauss variant sources changed')
    return dict(schema='rf-d/bdf-static-charge-gauss/v1',environment=env,source_sha256=before,windows=windows,mixed_supports=mixed,
        rules={str(p):{str(n):dict(points=[[str(x),str(w)] for x,w in v['points']],iterations=v['iterations'],moments=v['moments']) for n,v in rr.items()} for p,rr in rules.items()},
        orders=list(gauss.ORDERS),final_orders=[8,16],legendre_scalar_root_solves=28,new_nonlinear_circuit_solves=0,
        diagnostic_only=True,prior_reports_modified=False,integrator_changed=False,physical_trajectory_bound=False,
        exact_temporal_defect_known=False,independent_error_estimator=False,temporal_error_bound_admitted=False,
        physical_switching_admitted=False,audio_admitted=False,deadline_admitted=False,
        limitation='Gauss agreement on reconstructed selected intervals, not a certified quadrature remainder, voltage error or trajectory from DC')


def save(report):
    storage=store(report,OUTPUT);windows=[]
    for w in report['windows']:
        levels=[]
        for level in w['levels']:
            rows=[r['result'] for r in level['rows']]
            levels.append(dict(subdivisions=level['subdivisions'],intervals=len(rows),
                final_quadrature_passes=sum(r['final_quadrature_gate'] for r in rows),
                simpson64_gauss16_passes=sum(r['simpson64_vs_gauss16']['passed'] for r in rows),
                common_precision_passes=sum(all(v['passed'] for v in r['common_precision'].values()) for r in rows),
                levels=[dict(order=n,precision_passes=sum(all(v['passed'] for v in r['levels'][j]['precision'].values()) for r in rows),
                    identity_passes=sum(r['levels'][j]['identity']['passed'] for r in rows),
                    static_passes=sum(r['levels'][j]['static_vs_16']['passed'] for r in rows),
                    chain_passes=sum(r['levels'][j]['chain_endpoint_gate']['passed'] for r in rows),
                    observed_mean_passes=sum(r['levels'][j]['observed_constitutive_mean_below_10pa'] for r in rows),
                    maximum_mean_constitutive_a=max(abs(float(v)) for r in rows for v in r['levels'][j]['vectors']['constitutive_mean_kcl_a'])) for j,n in enumerate(gauss.ORDERS)]))
        windows.append(dict(name=w['name'],levels=levels))
    summary={k:v for k,v in report.items() if k not in ('windows','mixed_supports')}|dict(storage=storage,windows=windows,
        mixed_supports=[{k:v for k,v in m.items() if k!='result'}|dict(final_quadrature_passed=m['result']['final_quadrature_gate'],
            simpson64_vs_gauss16=m['result']['simpson64_vs_gauss16']) for m in report['mixed_supports']])
    SUMMARY.write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n');return summary


if __name__=='__main__':save(generate())
