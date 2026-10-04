"""Selected support coverage and all fixed norm bridges, without error admission."""
from fractions import Fraction as F
from pathlib import Path
import gzip,json
import loudness_latch_coverage_bridge as law
import loudness_latch_bdf_static_precision_anchor_budget as prior
from loudness_latch_increment_probes import hashes
from loudness_latch_bdf_doubling_survey import canonical,store
from loudness_lab_metadata import environment
ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/'evidence/loudness_latch_bdf_static_precision_coverage_bridge.json.gz'
SUMMARY=ROOT/'evidence/loudness_latch_bdf_static_precision_coverage_bridge_summary.json'
PROTOCOL=ROOT/'docs/BIESTABLE_COBERTURA_METRICAS_PROTOCOLO.md'
FIXED=ROOT/'evidence/loudness_latch_bdf_static_precision_fixed_clock.json.gz'
LONG=ROOT/'evidence/loudness_latch_bdf_static_precision_memory_long.json.gz'
FINE=ROOT/'evidence/loudness_latch_bdf_static_precision_forced_clock.json.gz'
WEIGHTED=ROOT/'evidence/loudness_latch_bdf_static_precision_weighted_descriptor.json.gz'
METRIC=ROOT/'evidence/loudness_latch_bdf_static_precision_junction_metric.json.gz'
MODAL=ROOT/'evidence/loudness_latch_bdf_static_precision_junction_modal.json.gz'
PATHS=tuple(dict.fromkeys((*prior.PATHS,prior.OUTPUT,prior.SUMMARY,
    ROOT/'evidence/loudness_latch_bdf_static_precision_anchor_budget_validation.json',
    ROOT/'evidence/loudness_latch_bdf_static_precision_anchor_inputs.json.gz',
    ROOT/'evidence/loudness_latch_bdf_static_precision_anchor_inputs_summary.json',
    ROOT/'evidence/loudness_latch_bdf_static_precision_anchor_inputs_validation.json',
    FIXED,LONG,FINE,WEIGHTED,METRIC,MODAL,Path(__file__).resolve(),Path(law.__file__).resolve(),PROTOCOL)))
def read(p):return json.loads(gzip.decompress(p.read_bytes()))
def generate():
    before=hashes(PATHS);env=environment();fixed=read(FIXED);long=read(LONG);fine=read(FINE);weighted=read(WEIGHTED);metric=read(METRIC);modal=read(MODAL);anchor=read(prior.OUTPUT)
    chain=law.lineage(fixed['initial'],fixed['rows'])
    if not fixed['complete'] or not fixed['fresh_dc_matches_reference'] or len(fixed['rows'])!=6486 or law.digest(fixed['final'])!=chain['final_sha256']:raise ValueError('complete frozen DC lineage required')
    start,end=map(F,chain['domain_s']);refs={};lineages=[]
    for w in fine['windows']:
        base=next(v for v in long['windows'] if v['name']==w['name']);ci=base['compensated_clock_anchor_index']
        if canonical(base['initial'])!=canonical(fixed['rows'][ci]['history']) or canonical(w['initial'])!=canonical(base['initial']):raise ValueError('window DC anchor differs')
        for level in w['levels']:
            r=level['reference'];n=r['subdivisions'];key=(w['name'],n)
            if key in refs or not r['complete'] or len(r['samples'])!=64 or len(r['steps'])!=64*n or canonical(r['initial'])!=canonical(w['initial']):raise ValueError('complete unique refined window required')
            refs[key]=r;proof=law.lineage(r['initial'],r['steps'])
            if law.digest(r['final'])!=proof['final_sha256']:raise ValueError('refined final state differs')
            lineages.append(dict(window=w['name'],subdivisions=n,dc_anchor_row_index=ci,dc_anchor_sha256=law.digest(fixed['rows'][ci]['history']),lineage=proof))
    cases=[];norms=[]
    for index,c in enumerate(weighted['cases']):
        r=refs[c['window'],c['subdivisions']];fi=r['samples'][c['index']]['fine_step_index'];steps=[r['steps'][j] for j in range(fi,fi-4,-1)]
        support=[law.digest(v['history']) for v in steps];times=[F(v['history']['time_s']) for v in steps];left,right=times[1],times[0]
        a=anchor['cases'][index];m=metric['cases'][index];modes=modal['cases'][index]
        for other in (a,m,modes):
            if any(other[k]!=c[k] for k in ('window','subdivisions','index','support_sha256','weights')):raise ValueError('case identities differ')
        if c['index']!=31 or support!=c['support_sha256'] or right-left!=F(c['duration_s']) or not c['ideal_temporal_inverse_certified']:raise ValueError('selected interval support differs')
        if len(c['ideal_temporal_cover'])!=8 or c['ideal_temporal_cover'][0]['left']!='0' or c['ideal_temporal_cover'][-1]['right']!='1':raise ValueError('complete selected cell partition required')
        record=dict(source_case_index=index,window=c['window'],subdivisions=c['subdivisions'],sample_index=c['index'],fine_step_index=fi,
            support_sha256=support,support_times_s=list(map(str,times)),selected_interval_s=[str(left),str(right)],duration_s=str(right-left),
            window_initial_s=str(F(r['initial']['time_s'])),window_final_s=str(F(r['final']['time_s'])),
            incoming_selected_history_sha256=law.digest(r['steps'][fi-1]['history']),selected_history_sha256=support[0],
            selected_endpoint_matches_full_clock=False,ideal_inverse_cell_count=8,quadratic_metric_accepted=m['metric_candidate']['accepted'],
            frozen_rhp_counts=[v['result']['routh_certificate']['right_half_plane_roots'] for v in modes['cells']],actual_error_coverage=False,
            reset_strategy='retain inverse and modal evidence; use an explicitly frozen noncontractive norm and coupled residual proof before coverage' if c['window']=='reset' else None)
        if m['metric_candidate']['accepted']:norms.append(dict(case_index=index,window=c['window'],subdivisions=c['subdivisions'],prepared=law.gram(m['metric_candidate'],c['weights'])))
        cases.append(record)
    inventories=[]
    for n in (2,4):
        selected=[v for v in cases if v['subdivisions']==n]
        inventories.append(dict(subdivisions=n,ideal_inverse_selected=law.coverage([v['selected_interval_s'] for v in selected],start,end),
            accepted_metric_selected=law.coverage([v['selected_interval_s'] for v in selected if v['quadratic_metric_accepted']],start,end)))
    all_inverse=law.coverage([v['selected_interval_s'] for v in cases],start,end);all_metric=law.coverage([v['selected_interval_s'] for v in cases if v['quadratic_metric_accepted']],start,end)
    bridges=[dict(source_norm_index=i,destination_norm_index=j,certificate=law.bridge(a['prepared'],b['prepared'])) for i,a in enumerate(norms) for j,b in enumerate(norms)]
    if hashes(PATHS)!=before:raise ValueError('coverage and bridge sources changed')
    print(json.dumps(dict(dc_intervals=chain['interval_count'],refined_intervals=sum(v['lineage']['interval_count'] for v in lineages),selected_intervals=len(cases),union_intervals=len(all_inverse['union_s']),norms=len(norms),bridges=len(bridges))),flush=True)
    return dict(schema='rf-d/bdf-static-coverage-bridge/v1',environment=env,source_sha256=before,dc_lineage=chain,refined_lineages=lineages,cases=cases,
        inventories=inventories,combined_ideal_inverse_selected=all_inverse,combined_accepted_metric_selected=all_metric,
        norms=norms,bridges=bridges,exact_bridge_ldlt_queries=sum(len(v['certificate']['probes']) for v in bridges),
        bridge_policy='all ordered pairs and identities; same physical error vector only, no missing-region dynamics',
        numerical_dc_lineage_verified=True,continuous_actual_error_certified_duration_s='0',
        metric_candidates_changed=False,weights_changed=False,norms_changed=False,new_circuit_inverse_systems=0,new_nonlinear_circuit_solves=0,
        initial_error_known=False,nonlinear_remainder_bound=False,actual_dae_error_bound=False,full_path_coverage=False,
        temporal_error_bound_admitted=False,physical_trajectory_bound=False,audio_admitted=False,deadline_admitted=False,
        numerical_gates_changed=False,prior_reports_modified=False,
        limitation='archived numerical lineage and selected tangent support only; norm bridges do not propagate gaps or prove entry errors')
def save(report):
    if OUTPUT==SUMMARY or OUTPUT in PATHS or SUMMARY in PATHS:raise ValueError('output/input destination collision')
    storage=store(report,OUTPUT)
    shorten=lambda p:{k:v for k,v in p.items() if k!='trace'}
    summary={k:v for k,v in report.items() if k not in ('dc_lineage','refined_lineages','norms','bridges')}|dict(storage=storage,
        dc_lineage=shorten(report['dc_lineage']),refined_lineages=[v|dict(lineage=shorten(v['lineage'])) for v in report['refined_lineages']],
        norm_cases=[{k:v for k,v in n.items() if k!='prepared'} for n in report['norms']],
        bridges=[{k:v for k,v in b.items() if k!='certificate'}|dict(certificate={k:v for k,v in b['certificate'].items() if k not in ('probes','final_upper_ldlt')}) for b in report['bridges']])
    SUMMARY.write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n');return summary
if __name__=='__main__':save(generate())
