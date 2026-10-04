"""Replay two archived closures with explicit unbounded integer text policy."""
from pathlib import Path
from fractions import Fraction as F
import json,sys
import loudness_latch_bdf_static_precision_directed_prefix as prior
from loudness_latch_increment_probes import hashes
from loudness_latch_bdf_doubling_survey import store
from loudness_lab_metadata import environment
ROOT=prior.ROOT
OUTPUT=ROOT/'evidence/loudness_latch_bdf_static_precision_large_closure.json.gz'
SUMMARY=ROOT/'evidence/loudness_latch_bdf_static_precision_large_closure_summary.json'
PROTOCOL=ROOT/'docs/BIESTABLE_CIERRES_ENTEROS_PROTOCOLO.md'
PATHS=tuple(dict.fromkeys((*prior.PATHS,prior.OUTPUT,prior.SUMMARY,Path(__file__).resolve(),PROTOCOL)))
read=prior.read


def supports(report):
    if report['accepted_intervals_total']!=6 or report['first_gap_index']!=6:
        raise ValueError('frozen six-interval prefix and first uncertified seventh support required')
    targets=[]
    for rec in report['records']:
        for i,t in enumerate(rec['trials']):
            if '4300 digits' in (t['result']['reason'] or ''):
                if i!=2 or F(t['radius_v'])!=F(1,10**5) or len(t['cells'])!=8 or any(not c['inverse_certified'] for c in t['covers']):
                    raise ValueError('full archived ten-microvolt cells required')
                targets.append((rec,i,t))
    if [r['interval_index'] for r,_,_ in targets]!=[5,6]:
        raise ValueError('exactly two identified serialization failures required')
    return targets


def generate():
    before=hashes(PATHS);env=environment();previous_limit=sys.get_int_max_str_digits();sys.set_int_max_str_digits(0)
    report=read(prior.OUTPUT);rows=[]
    for rec,i,t in supports(report):
        result=prior.law.blocks.close(t['cells'],rec['incoming_block_error_upper_v'],F(t['radius_v']),F(rec['incoming_node_error_upper_v']))
        rows.append(dict(interval_index=rec['interval_index'],trial_index=i,radius_v=t['radius_v'],start_s=rec['start_s'],end_s=rec['end_s'],
            source_cells_sha256=prior.law.digest(t['cells']),source_failed_result=t['result'],
            incoming_certified_result_sha256=rec['incoming_certified_result_sha256'],incoming_block_error_upper_v=rec['incoming_block_error_upper_v'],
            incoming_node_error_upper_v=rec['incoming_node_error_upper_v'],result=result))
        print(json.dumps(dict(interval=rec['interval_index'],accepted=result['accepted'],node_bound_v=prior.diagnostic_bound(result),reason=result['reason'])),flush=True)
    if hashes(PATHS)!=before:raise ValueError('large closure inputs changed')
    return dict(schema='rf-d/bdf-static-large-closure/v1',environment=env,source_sha256=before,
        integer_text_limit_before=previous_limit,integer_text_limit_during=0,integer_text_policy='unbounded exact base-ten serialization; mathematical kernel domain unchanged',
        records=rows,source_prefix_result_sha256=prior.law.digest(report['final_certified_result']),
        accepted_intervals_total=report['accepted_intervals_total'],continuous_actual_error_certified_duration_s=report['continuous_actual_error_certified_duration_s'],
        first_gap_index=report['first_gap_index'],source_selections_rewritten=False,source_reports_modified=False,
        new_closures=len(rows),new_preconditioners=0,new_inverse_enclosures=0,new_rate_ldlt_queries=0,new_action_subcell_certificates=0,new_nonlinear_solves=0,
        numerical_gates_changed=False,circuit_changed=False,full_path_coverage=False,global_1mv_gate_closed=False,physical_trajectory_bound=False,audio_admitted=False,deadline_admitted=False)


def save(report):
    if OUTPUT==SUMMARY or OUTPUT in PATHS or SUMMARY in PATHS:raise ValueError('output/input destination collision')
    storage=store(report,OUTPUT);summary={k:v for k,v in report.items() if k!='records'}
    summary.update(storage=storage,records=[row|dict(result={k:v for k,v in row['result'].items() if k!='propagation'}) for row in report['records']])
    SUMMARY.write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n');return summary
if __name__=='__main__':save(generate())
