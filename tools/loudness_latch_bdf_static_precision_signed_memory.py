"""Frozen seventh-support C7 shift using full archived descriptor certificates."""
from pathlib import Path
from fractions import Fraction as F
import json,sys
import loudness_latch_bdf_static_precision_large_closure as prior
import loudness_latch_signed_memory_shift as law
from loudness_latch_increment_probes import hashes
from loudness_latch_bdf_doubling_survey import store
from loudness_lab_metadata import environment
ROOT=prior.ROOT
OUTPUT=ROOT/'evidence/loudness_latch_bdf_static_precision_signed_memory.json.gz'
SUMMARY=ROOT/'evidence/loudness_latch_bdf_static_precision_signed_memory_summary.json'
PROTOCOL=ROOT/'docs/BIESTABLE_FORCING_C7_PROTOCOLO.md'
MODES=('absolute','signed_c7_shift')
PATHS=tuple(dict.fromkeys((*prior.PATHS,prior.OUTPUT,prior.SUMMARY,
    ROOT/'evidence/loudness_latch_bdf_static_precision_large_closure_validation.json',
    ROOT/'evidence/loudness_latch_bdf_static_precision_directed_prefix_validation.json',
    ROOT/'evidence/loudness_latch_bdf_static_precision_directed_prefix_inputs.json.gz',
    ROOT/'evidence/loudness_latch_bdf_static_precision_directed_prefix_inputs_summary.json',
    ROOT/'evidence/loudness_latch_bdf_static_precision_directed_prefix_inputs_validation.json',
    Path(__file__).resolve(),Path(law.__file__).resolve(),PROTOCOL)))
read=prior.read


def support(source,large):
    previous=source['final_certified_result'];incoming=law.prior.transfer(previous);rec=source['records'][-1]
    if source['accepted_intervals_total']!=6 or source['first_gap_index']!=6 or rec['interval_index']!=6 or rec['selected_trial_index'] is not None:
        raise ValueError('known six-interval prefix and seventh-support gap required')
    if F(rec['start_s'])!=F(source['continuous_actual_error_certified_duration_s']) or rec['incoming_certified_result_sha256']!=law.prior.digest(previous) or rec['incoming_block_error_upper_v']!=incoming:
        raise ValueError('same known incoming memory and certified clock required')
    if source['metric_sha256']!=law.prior.digest(source['fixed_metric']) or source['groups']!=[list(g) for g in law.prior.fine.GROUPS]:
        raise ValueError('same fixed metric and 22 groups required')
    rows=[r for r in large['records'] if r['interval_index']==6]
    if len(rows)!=1 or large['source_prefix_result_sha256']!=law.prior.digest(previous) or rows[0]['source_cells_sha256']!=law.prior.digest(rec['trials'][2]['cells']) or rows[0]['result']['accepted']:
        raise ValueError('identified complete rejected ten-microvolt baseline required')
    return previous,rec,rows[0]['result']


def generate():
    before=hashes(PATHS);env=environment();old_limit=sys.get_int_max_str_digits();sys.set_int_max_str_digits(0)
    source=read(prior.prior.OUTPUT);large=read(prior.OUTPUT);previous,rec,ten=support(source,large)
    weights=source['weights'];scales=list(map(F,source['descriptor_scales']));metric=source['fixed_metric'];trials=[];reused=0
    for k,t in enumerate(rec['trials']):
        baseline=ten if k==2 else t['result'];modes=[dict(mode=MODES[0],result=baseline)];rows=[];certificates=[];p=F(0)
        for base,cover,original in zip(rec['base_cells'],t['covers'],t['cells']):
            inverse,cert=law.prior.real.tube.cells.structured_inverse(base['inverse_binary'],scales,cover['cover'],F(cover['cover']['contraction_upper']))
            digest=law.prior.digest(law.prior.real.tube.cells.packed_matrix(inverse))
            if cert!=cover['inverse_certificate'] or digest!=cover['inverse_intervals_sha256']:raise ValueError('same archived full inverse required')
            row=law.shifted_cell(original,inverse,scales,weights,metric,p);p=F(row['shift']['endpoint_v']);rows.append(row);reused+=1
            certificates.append(dict(index=original['index'],inverse_intervals_sha256=digest,source_cover_sha256=law.prior.digest(cover),
                source_rate_sha256=law.prior.digest(original['rate_certificate']),source_action_sha256=law.prior.digest(original['action'])))
        result=law.close(rows,law.prior.transfer(previous),F(t['radius_v']),F(previous['peak_node_error_upper_v'])) if rows else baseline
        modes.append(dict(mode=MODES[1],cells=rows,result=result));trials.append(dict(radius_v=t['radius_v'],certificates=certificates,modes=modes))
        print(json.dumps(dict(interval=6,radius_v=float(F(t['radius_v'])),mode=MODES[1],accepted=result['accepted'],node_bound_v=prior.prior.diagnostic_bound(result),reason=result['reason'])),flush=True)
    selected=next(([i,j] for i,t in enumerate(trials) for j,m in enumerate(t['modes']) if m['result']['accepted']),None)
    final=previous if selected is None else trials[selected[0]]['modes'][selected[1]]['result']
    if selected is not None:law.prior.transfer(final)
    if hashes(PATHS)!=before:raise ValueError('signed memory inputs changed')
    return dict(schema='rf-d/bdf-static-signed-memory/v1',environment=env,source_sha256=before,integer_text_limit_before=old_limit,integer_text_limit_during=0,
        source_interval_index=6,start_s=rec['start_s'],end_s=rec['end_s'],interface=rec['interface'],source_certified_result_sha256=law.prior.digest(previous),
        incoming_block_error_upper_v=law.prior.transfer(previous),incoming_node_error_upper_v=previous['peak_node_error_upper_v'],metric_sha256=source['metric_sha256'],
        weights=weights,descriptor_scales=source['descriptor_scales'],radius_order=source['radius_order'],mode_order=list(MODES),trials=trials,primary_trial_mode=selected,
        accepted_intervals_total=7 if selected is not None else 6,continuous_actual_error_certified_duration_s=rec['end_s'] if selected is not None else rec['start_s'],
        first_gap_index=None if selected is not None else 6,final_certified_result=final,reused_inverse_enclosures=reused,reused_rate_certificates=reused,
        reused_action_subcell_certificates=reused*law.action.SUBCELLS,new_shift_subcell_certificates=reused*law.action.SUBCELLS,
        new_nonlinear_solves=0,new_preconditioners=0,new_inverse_enclosures=0,new_metric_systems=0,new_rate_ldlt_queries=0,
        trajectory_changed=False,physical_reconstruction_changed=False,junction_norm_changed=False,dc_anchor_reset=False,prior_reports_modified=False,numerical_gates_changed=False,
        small_currents_dropped=False,circuit_regularized=False,independent_remainders_cancelled=False,full_path_coverage=False,global_1mv_gate_closed=False,
        physical_trajectory_bound=False,audio_admitted=False,deadline_admitted=False)


def save(report):
    if OUTPUT==SUMMARY or OUTPUT in PATHS or SUMMARY in PATHS:raise ValueError('output/input destination collision')
    storage=store(report,OUTPUT);summary={k:v for k,v in report.items() if k not in ('trials','final_certified_result')}
    summary.update(storage=storage,final_certified_result={k:v for k,v in report['final_certified_result'].items() if k!='propagation'},
        trials=[dict(radius_v=t['radius_v'],modes=[dict(mode=m['mode'],result={k:v for k,v in m['result'].items() if k!='propagation'}) for m in t['modes']]) for t in report['trials']])
    SUMMARY.write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n');return summary
if __name__=='__main__':save(generate())
