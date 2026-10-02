"""Certified integral of reconstructed polynomial-memory residual; no circuit solves."""
from fractions import Fraction as F
from decimal import Decimal as D,localcontext
import gzip,json
from pathlib import Path
import loudness_latch_charge_enclosure as bound
import loudness_latch_bdf_static_precision_charge_gauss as old
from loudness_latch_increment_probes import hashes
from loudness_latch_bdf_doubling_survey import store
from loudness_lab_metadata import environment
ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/'evidence/loudness_latch_bdf_static_precision_charge_enclosure.json.gz'
SUMMARY=ROOT/'evidence/loudness_latch_bdf_static_precision_charge_enclosure_summary.json'
PROTOCOL=ROOT/'docs/BIESTABLE_INTEGRAL_ACOTADA_PROTOCOLO.md'
PATHS=tuple(dict.fromkeys((*old.PATHS,Path(__file__).resolve(),Path(bound.__file__).resolve(),PROTOCOL,
    old.OUTPUT,ROOT/'evidence/loudness_latch_bdf_static_precision_charge_gauss_validation.json')))


def packed(x):
    if isinstance(x,F):return str(x.numerator)+'/'+str(x.denominator)
    if isinstance(x,dict):return {k:packed(v) for k,v in x.items()}
    if isinstance(x,(list,tuple)):return [packed(v) for v in x]
    return x


def point(network,g,prepared,left,right,prior):
    static,terms=bound.static_integral(g,prepared['x'],prepared['h'],left,right)
    dynamic,boundary=bound.dynamic_charge(network,prepared['q'],left,right)
    duration=prepared['h']*(right-left);balances=[(a+d,b+d) for (a,b),d in zip(static,dynamic)]
    means=[(a/duration,b/duration) for a,b in balances]
    threshold=F(1e-11)
    lower_abs=lambda ab:F(0) if ab[0]<=0<=ab[1] else min(map(abs,ab))
    upper_abs=lambda ab:max(map(abs,ab))
    maxlow=max(map(lower_abs,means));maxhigh=max(map(upper_abs,means))
    classification='below' if maxhigh<threshold else 'above' if maxlow>=threshold else 'unresolved'
    contrasts=[]
    for j,((a,b),v) in enumerate(zip(static,prior['levels'][-1]['vectors']['static_integral_c'])):
        value=F(D(v));error=max(abs(a-value),abs(b-value));gate=F(D('1e-30'))+F(D('1e-8'))*abs(value)
        contrasts.append(dict(node=j,absolute_error_upper_c=error,gate_c=gate,passed=error<=gate,
                              reported_gauss_value_inside=a<=value<=b))
    return packed(dict(static_integral_c=static,polynomial_balance_c=balances,polynomial_mean_a=means,
        dynamic_boundary_c=boundary,terms=terms,mean_classification_10pa=classification,
        maximum_mean_absolute_lower_a=maxlow,maximum_mean_absolute_upper_a=maxhigh,
        nodal_l1_residual_lower_c=list(map(lower_abs,balances)),
        gauss16_contrast=contrasts,all_gauss16_error_bounds_passed=all(c['passed'] for c in contrasts),
        maximum_static_radius_c=max((b-a)/2 for a,b in static),duration_s=duration))


def generate():
    before=hashes(PATHS);env=environment();source=json.loads(gzip.decompress(old.old.dense.previous.proxy.REFERENCE.read_bytes()))['windows']
    prior=json.loads(gzip.decompress(old.OUTPUT.read_bytes()));network=old.CompensatedBdfNetwork(200,old.model_parameters(1,'finite_transit'))
    g=old.curvature.graph(network,10.);windows=[];mixed=[]
    for w,pw in zip(source,prior['windows']):
        if w['name']!=pw['name']:raise ValueError('source window mismatch')
        levels=[]
        for level,pl in zip(w['levels'],pw['levels']):
            rows=[];ref=level['reference']
            for index in range(2,64):
                prepared=old.old.dense.prepare(network,ref,index)
                pr=pl['rows'][index-2]
                if prepared['support_sha256']!=pr['support_sha256']:raise ValueError('history identity mismatch')
                r=point(network,g,prepared,F(0),F(1),pr['result'])
                rows.append(dict(index=index,support_sha256=prepared['support_sha256'],result=r))
                for m in prior['mixed_supports']:
                    if (m['window'],m['subdivisions'],m['index'])==(w['name'],ref['subdivisions'],index):
                        mixed.append(dict(window=w['name'],subdivisions=ref['subdivisions'],index=index,
                            result=point(network,g,prepared,prepared['u'][-1],F(1),m['result'])))
            levels.append(dict(subdivisions=ref['subdivisions'],rows=rows))
            print(json.dumps(dict(window=w['name'],subdivisions=ref['subdivisions'],enclosed=len(rows))),flush=True)
        windows.append(dict(name=w['name'],levels=levels))
    if hashes(PATHS)!=before:raise ValueError('enclosure sources changed')
    return dict(schema='rf-d/bdf-static-charge-enclosure/v1',environment=env,source_sha256=before,
        windows=windows,mixed_supports=mixed,degree=bound.DEGREE,dyadic_bits=bound.BITS,exp_terms=bound.EXP_TERMS,
        new_nonlinear_circuit_solves=0,ideal_reconstructed_integral_enclosed=True,
        constitutive_memory_residual_enclosed=False,full_path_coverage=False,
        physical_trajectory_bound=False,temporal_error_bound_admitted=False,audio_admitted=False,
        deadline_admitted=False,numerical_gates_changed=False,prior_reports_modified=False)


def save(report):
    storage=store(report,OUTPUT);windows=[]
    for w in report['windows']:
        levels=[]
        for l in w['levels']:
            rows=[v['result'] for v in l['rows']]
            levels.append(dict(subdivisions=l['subdivisions'],intervals=len(rows),
                gauss16_bounded_passes=sum(r['all_gauss16_error_bounds_passed'] for r in rows),
                classifications={k:sum(r['mean_classification_10pa']==k for r in rows) for k in ('below','above','unresolved')},
                maximum_static_radius_c=max(float(F(r['maximum_static_radius_c'])) for r in rows),
                maximum_mean_lower_a=max(float(F(r['maximum_mean_absolute_lower_a'])) for r in rows),
                maximum_mean_upper_a=max(float(F(r['maximum_mean_absolute_upper_a'])) for r in rows)))
        windows.append(dict(name=w['name'],levels=levels))
    summary={k:v for k,v in report.items() if k not in ('windows','mixed_supports')}|dict(storage=storage,windows=windows,
        mixed_supports=[{k:v for k,v in m.items() if k!='result'}|dict(classification=m['result']['mean_classification_10pa'],
            gauss16_bounded_passed=m['result']['all_gauss16_error_bounds_passed']) for m in report['mixed_supports']])
    SUMMARY.write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n');return summary


if __name__=='__main__':save(generate())
