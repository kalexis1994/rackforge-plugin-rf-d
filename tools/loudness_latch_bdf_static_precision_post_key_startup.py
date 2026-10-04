"""Published high+low event origin and fixed 512-interval own-path startup."""
from pathlib import Path
from fractions import Fraction as F
import json
import numpy as np
import loudness_latch_bdf_static_precision_key_scaled as prior
import loudness_latch_post_key_origin as law
from loudness_latch_bdf_probes import pack,unpack,publication_check
from loudness_latch_bdf_static_precision_fixed_clock import comparison_row
from loudness_latch_increment_probes import hashes
from loudness_latch_bdf_doubling_survey import store,canonical
from loudness_lab_metadata import environment
ROOT=prior.ROOT
OUTPUT=ROOT/'evidence/loudness_latch_bdf_static_precision_post_key_startup.json.gz'
SUMMARY=ROOT/'evidence/loudness_latch_bdf_static_precision_post_key_startup_summary.json'
PROTOCOL=ROOT/'docs/BIESTABLE_POST_KEY_ARRANQUE_PROTOCOLO.md'
COUNT=512
FIXED=prior.prior.prior.prior.FIXED
PATHS=tuple(dict.fromkeys((*prior.PATHS,prior.OUTPUT,prior.SUMMARY,
    ROOT/'evidence/loudness_latch_bdf_static_precision_key_projection_validation.json',
    ROOT/'evidence/loudness_latch_bdf_static_precision_key_inputs.json.gz',
    ROOT/'evidence/loudness_latch_bdf_static_precision_key_inputs_summary.json',
    ROOT/'evidence/loudness_latch_bdf_static_precision_key_inputs_validation.json',
    Path(law.__file__).resolve(),Path(__file__).resolve(),PROTOCOL,
    ROOT/'tools/loudness_latch_bdf_static_precision_fixed_clock.py')))

def generate():
    before=hashes(PATHS);env=environment();projection=prior.prior.prior.read(prior.prior.OUTPUT);scaled=prior.prior.prior.read(prior.OUTPUT)
    fixed=prior.prior.prior.read(FIXED);network=prior.prior.prior.CompensatedBdfNetwork(200,prior.prior.prior.model_parameters(1,'finite_transit'))
    pre=unpack(network,fixed['initial']);origin,errors=law.publish(network,pre,projection['event'])
    initial=law.restore(network,json.loads(json.dumps(origin,allow_nan=False)));event_check=law.event_check(network,projection['graph'],origin)
    nominal_bound=F(scaled['bounds']['node_error_upper_v']);rate_bound=F(scaled['bounds']['rate_error_upper_v_per_s'])
    initial_bound=dict(node_error_upper_v=str(nominal_bound+F(errors['max_node_error_v'])),
        auxiliary_rate_error_upper_v_per_s=str(rate_bound+F(errors['max_rate_error_v_per_s'])),
        event_enclosure_sha256=before[prior.OUTPUT.relative_to(ROOT).as_posix()],
        initial_memory_box_unchanged=law.charge_coordinates(network.network,initial.current)==law.charge_coordinates(network.network,pre.current),
        initial_memory_weights=prior.prior.prior.read(prior.prior.prior.OUTPUT)['memory_enclosure']['weights'])
    initial_passed=event_check['gates_passed'] and initial_bound['initial_memory_box_unchanged'] and scaled['laboratory_post_key_initial_error_known']
    clock=fixed['reference_clock'][:COUNT];rows=[];stop=None;old=initial
    if initial_passed:
        for index,slot in enumerate(clock):
            h=slot['dt_s'];snapshot=law.law.dc.digest(pack(old));incoming=pack(old)
            try:
                new,diag=network.advance(old,10.,h);pub=publication_check(network,old,new,h,diag)
                restored=unpack(network,json.loads(json.dumps(pack(new),allow_nan=False)))
                direct=law.discrete_check(network,projection['graph'],old,restored,h)
                reference=unpack(network,fixed['rows'][index]['history']);comparison=comparison_row(restored,reference)
                accepted=bool(pub['max_published_kcl_a']<1e-11 and pub['max_branch_equation_error_v']<1e-14 and
                    canonical(pack(restored))==canonical(pack(new)) and direct['kcl_passed'] and direct['linear_constraint_passed'] and
                    comparison['reference_time_equal'] and law.law.dc.digest(pack(old))==snapshot)
                row=dict(index=index,dt_s=h,history=pack(restored),diagnostics=diag,publication=pub,
                    independent_discrete=direct,previous_history_sha256=snapshot,accepted=accepted,**comparison)
                rows.append(row)
                if not accepted:stop=dict(index=index,reason='publication-or-independent-discrete-or-clock-failed',incoming=incoming,dt_s=h);break
                old=restored
            except (ValueError,OverflowError,np.linalg.LinAlgError) as error:
                stop=dict(index=index,reason='solve-or-check-failed',error=str(error),incoming=incoming,dt_s=h,
                          incoming_history_unchanged=law.law.dc.digest(pack(old))==snapshot);break
            if len(rows)%64==0:print(json.dumps(dict(accepted=len(rows),time_s=old.time_s)),flush=True)
    else:stop=dict(reason='event-publication-rejected',incoming=pack(initial))
    if hashes(PATHS)!=before:raise ValueError('startup inputs changed')
    complete=len(rows)==COUNT and stop is None
    return dict(schema='rf-d/bdf-static-post-key-startup/v1',environment=env,source_sha256=before,
        origin=origin,pair_publication_errors=errors,event_publication=event_check,initial_bound=initial_bound,
        post_key_published_initial_error_known=bool(initial_passed),initial_history=pack(initial),
        reference_pre_key_history_sha256=law.law.dc.digest(fixed['initial']),clock=clock,rows=rows,final=pack(old),stop=stop,
        planned_intervals=COUNT,accepted_intervals=sum(r['accepted'] for r in rows),complete=complete,
        own_path_origin=True,first_step_backward_euler=True,history_fabricated=False,new_dc_solves=0,new_event_solves=0,
        previous_reports_modified=False,original_integrator_modified=False,prior_parameters_changed=False,
        numerical_gates_changed=False,trajectory_retimed=False,full_path_coverage=False,initial_error_known=False,
        continuous_actual_error_certified_duration_s='0',actual_dae_error_bound=False,nonlinear_remainder_bound=False,
        physical_trajectory_bound=False,audio_admitted=False,deadline_admitted=False,
        limitation='published local event anchor and discrete own-path prefix; temporal error and continuous reconstruction remain unproved')

def save(report):
    if OUTPUT==SUMMARY or OUTPUT in PATHS or SUMMARY in PATHS:raise ValueError('output/input destination collision')
    storage=store(report,OUTPUT);rows=report['rows']
    summary={k:v for k,v in report.items() if k not in ('origin','initial_history','clock','rows','final')}
    summary.update(storage=storage,final_time_s=report['final']['time_s'],
        initial_origin_sha256=law.law.dc.digest(report['origin']),
        max_node_difference_v=max((r['max_node_difference_v'] for r in rows),default=None),
        max_memory_difference_v=max((r['max_memory_coordinate_difference_v'] for r in rows),default=None),
        node_comparison_failures=sum(not r['node_gate_passed'] for r in rows),memory_comparison_failures=sum(not r['memory_gate_passed'] for r in rows),
        max_published_kcl_a=max((r['publication']['max_published_kcl_a'] for r in rows),default=None),
        max_independent_kcl_a=max((float(r['independent_discrete']['decimal100_kcl_upper_a']) for r in rows),default=None))
    SUMMARY.write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n');return summary
if __name__=='__main__':save(generate())
