"""Eight declared weighted frozen and ideal time-varying tangent diagnostics."""
from fractions import Fraction as F
import gzip,json
from pathlib import Path
import loudness_latch_weighted_descriptor as law
import loudness_latch_bdf_static_precision_descriptor_forcing_norm as prior
import loudness_latch_bdf_static_precision_dense_charge as dense
from loudness_latch_increment_probes import hashes
from loudness_latch_bdf_doubling_survey import store
from loudness_lab_metadata import environment
ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/'evidence/loudness_latch_bdf_static_precision_weighted_descriptor.json.gz'
SUMMARY=ROOT/'evidence/loudness_latch_bdf_static_precision_weighted_descriptor_summary.json'
PROTOCOL=ROOT/'docs/BIESTABLE_DESCRIPTOR_PONDERADO_PROTOCOLO.md'
PATHS=tuple(dict.fromkeys((*prior.PATHS,prior.OUTPUT,prior.SUMMARY,
    ROOT/'evidence/loudness_latch_bdf_static_precision_descriptor_forcing_norm_validation.json',
    Path(__file__).resolve(),Path(law.__file__).resolve(),PROTOCOL,
    ROOT/'evidence/loudness_latch_bdf_static_precision_weighted_descriptor_parse_attempt.json',
    ROOT/'evidence/loudness_latch_bdf_static_precision_weighted_descriptor_helper_parse_attempt.json')))


def generate():
    before=hashes(PATHS);env=environment();source=json.loads(gzip.decompress(prior.OUTPUT.read_bytes()))
    refs={(w['name'],l['reference']['subdivisions']):l['reference'] for w in
          json.loads(gzip.decompress(dense.previous.proxy.REFERENCE.read_bytes()))['windows'] for l in w['levels']}
    network=dense.CompensatedBdfNetwork(200,dense.model_parameters(1,'finite_transit'));g=dense.curvature.graph(network,10.);cases=[]
    for old in source['cases']:
        row={k:v for k,v in old.items() if k not in ('failure','frozen_budget')}|dict(failure=None,
            prior_unweighted_budget=old['frozen_budget'])
        x=old['inverse_binary'];cert=old['inverse_certificate'];d=list(map(F,cert['column_scales']))
        q=F(cert['contraction_upper']);peaks=list(map(F,cert['error_column_peaks']))
        frozen_errors=[[q/(1-q)*p/di for p in peaks] for di in d]
        w=law.weights(old['descriptor_binary']);row['weights']=list(map(str,w));v=old['forcing_inputs']
        args=[list(map(F,v[k])) for k in ('nodal_l1_c','constraint_l1_v_s','nodal_point_a','constraint_point_v')]
        row['weighted_frozen_budget']=law.weighted_budget(x,frozen_errors,94,w,*args,F(old['duration_s']))
        prepared=dense.prepare(network,refs[old['window'],old['subdivisions']],31)
        if prepared['support_sha256']!=old['support_sha256']:raise ValueError('frozen support identity changed')
        constant,terms=law.compile_terms(network,g,prepared,x,d);cells=[]
        for index in range(law.CELLS):
            _,c=law.preconditioned_cover(constant,terms,F(index,law.CELLS),F(index+1,law.CELLS));cells.append(c)
        row['ideal_temporal_cover']=cells;row['ideal_temporal_inverse_certified']=all(c['strict_contraction'] for c in cells)
        if row['ideal_temporal_inverse_certified']:
            errors=law.temporal_inverse_errors(x,d,cells)
            row['weighted_temporal_budget']=law.weighted_budget(x,errors,94,w,*args,F(old['duration_s']),time_varying=True)
        else:row['temporal_budget_blocked']='preconditioned interval defect >=1 in at least one declared cell'
        cases.append(row)
        print(json.dumps(dict(window=row['window'],subdivisions=row['subdivisions'],ideal_temporal_inverse=row['ideal_temporal_inverse_certified'],
            maximum_q=float(max(F(c['contraction_upper']) for c in cells)),
            frozen_growth_supported=row['weighted_frozen_budget']['growth_supported'])),flush=True)
    if hashes(PATHS)!=before:raise ValueError('weighted descriptor inputs changed')
    return {k:v for k,v in source.items() if k not in ('schema','environment','source_sha256','cases','limitation')}|dict(
        schema='rf-d/bdf-static-weighted-descriptor/v1',environment=env,source_sha256=before,cases=cases,
        cells=law.CELLS,weight_policy='linear=1; junction=dyadic_floor(S/C_mid_binary)',
        weights_constant_on_each_interval=True,weights_fitted_to_response=False,
        ideal_descriptor_coefficients_enclosed=True,nonlinear_remainder_bound=False,
        actual_dae_error_bound=False,initial_error_known=False,full_path_coverage=False,
        temporal_error_bound_admitted=False,physical_trajectory_bound=False,audio_admitted=False,deadline_admitted=False,
        new_exact_linear_systems=0,new_nonlinear_circuit_solves=0,
        limitation='weighted tangent budgets along known reconstructed paths; error needs nonlinear remainder, actual anchor and complete path coverage')


def save(report):
    storage=store(report,OUTPUT)
    summary={k:v for k,v in report.items() if k!='cases'}|dict(storage=storage,cases=[
        {k:r[k] for k in ('window','subdivisions','index','duration_s','weights','ideal_temporal_inverse_certified','weighted_frozen_budget')}|
        dict(temporal_cell_contractions=[c['contraction_upper'] for c in r['ideal_temporal_cover']],
            weighted_temporal_budget=r.get('weighted_temporal_budget'),temporal_budget_blocked=r.get('temporal_budget_blocked')) for r in report['cases']])
    SUMMARY.write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n');return summary


if __name__=='__main__':save(generate())
