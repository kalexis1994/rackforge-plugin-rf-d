"""Q(v) endpoint and absolute-residual bounds, frozen reconstructed intervals."""
from fractions import Fraction as F
from decimal import Decimal as D
import json,gzip
from pathlib import Path
import loudness_latch_constitutive_enclosure as bound
import loudness_latch_bdf_static_precision_charge_enclosure as old
from loudness_latch_increment_probes import hashes
from loudness_latch_bdf_doubling_survey import store
from loudness_lab_metadata import environment
ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/'evidence/loudness_latch_bdf_static_precision_constitutive_enclosure.json.gz'
SUMMARY=ROOT/'evidence/loudness_latch_bdf_static_precision_constitutive_enclosure_summary.json'
PROTOCOL=ROOT/'docs/BIESTABLE_MAGNITUD_RESIDUAL_PROTOCOLO.md'
PATHS=tuple(dict.fromkeys((*old.PATHS,Path(__file__).resolve(),Path(bound.__file__).resolve(),PROTOCOL,
    old.OUTPUT,ROOT/'evidence/loudness_latch_bdf_static_precision_charge_enclosure_validation.json')))


def point(network,g,prepared,left,right,prior,gauss):
    result=bound.residual_bounds(network,g,prepared,left,right);duration=prepared['h']*(right-left)
    static=[tuple(map(F,ab)) for ab in prior['static_integral_c']]
    balances=[bound.add(a,b) for a,b in zip(static,result['dynamic_constitutive_c'])]
    means=[bound.scale(ab,1/duration) for ab in balances]
    low=max(map(bound.minimum_magnitude,means));high=max(map(bound.magnitude,means));threshold=F(1e-11)
    classification='below' if high<threshold else 'above' if low>=threshold else 'unresolved'
    lower=[bound.minimum_magnitude(ab) for ab in balances];poly_lower=list(map(F,prior['nodal_l1_residual_lower_c']))
    comparisons=[]
    for j,(ab,v) in enumerate(zip(balances,gauss['levels'][-1]['vectors']['constitutive_balance_c'])):
        value=F(D(v));error=max(abs(t-value) for t in ab);gate=F(D('1e-30'))+F(D('1e-8'))*abs(value)
        comparisons.append(dict(node=j,error_upper_c=error,gate_c=gate,passed=error<=gate))
    consistency=all(a<=b for a,b in zip(lower,result['constitutive_l1_upper_c'])) and all(a<=b for a,b in zip(poly_lower,result['polynomial_l1_upper_c']))
    return old.packed(result|dict(constitutive_balance_c=balances,constitutive_mean_a=means,constitutive_l1_lower_c=lower,
        polynomial_l1_lower_c=poly_lower,maximum_mean_absolute_lower_a=low,maximum_mean_absolute_upper_a=high,
        mean_classification_10pa=classification,gauss16_contrast=comparisons,
        all_gauss16_error_bounds_passed=all(c['passed'] for c in comparisons),l1_lower_upper_consistent=consistency,
        duration_s=duration))


def generate():
    before=hashes(PATHS);env=environment()
    source=json.loads(gzip.decompress(old.old.old.dense.previous.proxy.REFERENCE.read_bytes()))['windows']
    prior=json.loads(gzip.decompress(old.OUTPUT.read_bytes()));gauss=json.loads(gzip.decompress(old.old.OUTPUT.read_bytes()))
    network=old.old.CompensatedBdfNetwork(200,old.old.model_parameters(1,'finite_transit'));g=old.old.curvature.graph(network,10.)
    windows=[];mixed=[]
    for w,pw,gw in zip(source,prior['windows'],gauss['windows']):
        if not w['name']==pw['name']==gw['name']:raise ValueError('source order mismatch')
        levels=[]
        for level,pl,gl in zip(w['levels'],pw['levels'],gw['levels']):
            rows=[];ref=level['reference']
            for index in range(2,64):
                prepared=old.old.old.dense.prepare(network,ref,index);pr=pl['rows'][index-2];gr=gl['rows'][index-2]
                if prepared['support_sha256']!=pr['support_sha256'] or pr['support_sha256']!=gr['support_sha256']:raise ValueError('history identity mismatch')
                rows.append(dict(index=index,support_sha256=prepared['support_sha256'],result=point(network,g,prepared,F(0),F(1),pr['result'],gr['result'])))
                for m,gm in zip(prior['mixed_supports'],gauss['mixed_supports']):
                    if (m['window'],m['subdivisions'],m['index'])==(w['name'],ref['subdivisions'],index):
                        mixed.append(dict(window=w['name'],subdivisions=ref['subdivisions'],index=index,
                            result=point(network,g,prepared,prepared['u'][-1],F(1),m['result'],gm['result'])))
            levels.append(dict(subdivisions=ref['subdivisions'],rows=rows));print(json.dumps(dict(window=w['name'],subdivisions=ref['subdivisions'],bounded=62)),flush=True)
        windows.append(dict(name=w['name'],levels=levels))
    if hashes(PATHS)!=before:raise ValueError('constitutive enclosure sources changed')
    return dict(schema='rf-d/bdf-static-constitutive-enclosure/v1',environment=env,source_sha256=before,windows=windows,mixed_supports=mixed,
        static_taylor_degree=bound.DEGREE,cells=bound.CELLS,log_terms=bound.LOG_TERMS,dyadic_bits=bound.base.BITS,
        new_nonlinear_circuit_solves=0,constitutive_reconstructed_balance_enclosed=True,reconstructed_l1_upper_enclosed=True,
        full_path_coverage=False,physical_trajectory_bound=False,temporal_error_bound_admitted=False,audio_admitted=False,
        deadline_admitted=False,numerical_gates_changed=False,prior_reports_modified=False)


def save(report):
    storage=store(report,OUTPUT);windows=[]
    for w in report['windows']:
        levels=[]
        for l in w['levels']:
            rows=[r['result'] for r in l['rows']]
            levels.append(dict(subdivisions=l['subdivisions'],intervals=len(rows),
                gauss16_bounded_passes=sum(r['all_gauss16_error_bounds_passed'] for r in rows),
                l1_consistency_passes=sum(r['l1_lower_upper_consistent'] for r in rows),
                classifications={k:sum(r['mean_classification_10pa']==k for r in rows) for k in ('below','above','unresolved')},
                maximum_mean_upper_a=max(float(F(r['maximum_mean_absolute_upper_a'])) for r in rows),
                maximum_constitutive_pointwise_upper_a=max(float(F(v)) for r in rows for v in r['constitutive_pointwise_upper_a']),
                maximum_polynomial_remainder_a=max(float(F(v)) for r in rows for v in r['polynomial_uniform_remainder_a']),
                maximum_rate_mismatch_upper_a=max(float(F(v)) for r in rows for v in r['nonlinear_rate_mismatch_upper_a'])) )
        windows.append(dict(name=w['name'],levels=levels))
    summary={k:v for k,v in report.items() if k not in ('windows','mixed_supports')}|dict(storage=storage,windows=windows,
        mixed_supports=[{k:v for k,v in m.items() if k!='result'}|dict(classification=m['result']['mean_classification_10pa'],
            gauss16_bounded_passed=m['result']['all_gauss16_error_bounds_passed'],l1_consistent=m['result']['l1_lower_upper_consistent']) for m in report['mixed_supports']])
    SUMMARY.write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n');return summary


if __name__=='__main__':save(generate())
