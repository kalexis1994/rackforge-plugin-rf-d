"""Declared correlation-preserving variant of the reconstructed residual bound."""
from fractions import Fraction as F
import json,gzip
from pathlib import Path
import loudness_latch_correlated_enclosure as bound
import loudness_latch_bdf_static_precision_constitutive_enclosure as old
from loudness_latch_increment_probes import hashes
from loudness_latch_bdf_doubling_survey import store
from loudness_lab_metadata import environment
ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/'evidence/loudness_latch_bdf_static_precision_correlated_enclosure.json.gz'
SUMMARY=ROOT/'evidence/loudness_latch_bdf_static_precision_correlated_enclosure_summary.json'
PROTOCOL=ROOT/'docs/BIESTABLE_TASAS_CORRELACIONADAS_PROTOCOLO.md'
PATHS=tuple(dict.fromkeys((*old.PATHS,Path(__file__).resolve(),Path(bound.__file__).resolve(),PROTOCOL,
    old.OUTPUT,ROOT/'evidence/loudness_latch_bdf_static_precision_constitutive_enclosure_validation.json')))


def generate():
    before=hashes(PATHS);env=environment();prior=json.loads(gzip.decompress(old.OUTPUT.read_bytes()))
    source=json.loads(gzip.decompress(old.old.old.old.dense.previous.proxy.REFERENCE.read_bytes()))['windows']
    network=old.old.old.CompensatedBdfNetwork(200,old.old.old.model_parameters(1,'finite_transit'));g=old.old.old.curvature.graph(network,10.)
    windows=[];mixed=[]
    for w,pw in zip(source,prior['windows']):
        if w['name']!=pw['name']:raise ValueError('source order mismatch')
        levels=[]
        for level,pl in zip(w['levels'],pw['levels']):
            rows=[];ref=level['reference']
            for index in range(2,64):
                prepared=old.old.old.old.dense.prepare(network,ref,index);pr=pl['rows'][index-2]
                if prepared['support_sha256']!=pr['support_sha256']:raise ValueError('history identity mismatch')
                result=bound.correlated_bounds(network,g,prepared,F(0),F(1),pr['result'])
                rows.append(dict(index=index,support_sha256=prepared['support_sha256'],result=old.old.packed(result)))
                for m in prior['mixed_supports']:
                    if (m['window'],m['subdivisions'],m['index'])==(w['name'],ref['subdivisions'],index):
                        mixed.append(dict(window=w['name'],subdivisions=ref['subdivisions'],index=index,
                            result=old.old.packed(bound.correlated_bounds(network,g,prepared,prepared['u'][-1],F(1),m['result']))))
            levels.append(dict(subdivisions=ref['subdivisions'],rows=rows));print(json.dumps(dict(window=w['name'],subdivisions=ref['subdivisions'],correlated=62)),flush=True)
        windows.append(dict(name=w['name'],levels=levels))
    if hashes(PATHS)!=before:raise ValueError('correlated sources changed')
    return dict(schema='rf-d/bdf-static-correlated-enclosure/v1',environment=env,source_sha256=before,windows=windows,mixed_supports=mixed,
        capacitance_degree=bound.DEGREE,cells=bound.CELLS,dyadic_bits=bound.old.base.BITS,new_nonlinear_circuit_solves=0,
        inherited_signed_balances_unchanged=True,prior_reports_modified=False,numerical_gates_changed=False,
        full_path_coverage=False,physical_trajectory_bound=False,temporal_error_bound_admitted=False,audio_admitted=False,deadline_admitted=False)


def save(report):
    storage=store(report,OUTPUT);windows=[]
    for w in report['windows']:
        levels=[]
        for l in w['levels']:
            rows=[r['result'] for r in l['rows']]
            levels.append(dict(subdivisions=l['subdivisions'],intervals=len(rows),
                whole_interval_certificates=sum(r['whole_interval_below_10pa'] for r in rows),
                maximum_pointwise_upper_a=max(float(F(r['maximum_pointwise_upper_a'])) for r in rows),
                maximum_rate_mismatch_upper_a=max(float(F(v)) for r in rows for v in r['nonlinear_rate_mismatch_upper_a']),
                nonincreasing_passes=sum(r['bounds_nonincreasing'] for r in rows),
                l1_consistency_passes=sum(r['l1_lower_upper_consistent'] for r in rows)))
        windows.append(dict(name=w['name'],levels=levels))
    summary={k:v for k,v in report.items() if k not in ('windows','mixed_supports')}|dict(storage=storage,windows=windows,
        mixed_supports=[{k:v for k,v in m.items() if k!='result'}|dict(whole_interval_below_10pa=m['result']['whole_interval_below_10pa'],
            smooth_pieces=m['result']['smooth_pieces'],bridges=m['result']['bridges'],maximum_pointwise_upper_a=m['result']['maximum_pointwise_upper_a']) for m in report['mixed_supports']])
    SUMMARY.write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n');return summary


if __name__=='__main__':save(generate())
