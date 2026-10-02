"""Declared own-history refinement and coarse lifted forcing, without promotion."""
import gzip
import json
from pathlib import Path
import numpy as np
from bjt_charge_ngspice_probes import model_parameters
import loudness_latch_bdf_forcing as force
import loudness_latch_directional_curvature as curvature
from loudness_latch_bdf_static_precision_integrator import CompensatedBdfNetwork
from loudness_latch_bdf_static_precision_forced_windows import SOURCE,PATHS as OLD_PATHS,OUTPUT as FAILED_DATA,SUMMARY as FAILED_SUMMARY
from loudness_latch_bdf_clock_plan import plan
from loudness_latch_bdf_static_precision_windows import candidate
from loudness_latch_bdf_memory_transfer import stamps,node_difference,memory_difference
from loudness_latch_bdf_transfer_solve import solve
from loudness_latch_bdf_static_precision import solved
from loudness_latch_bdf_probes import pack,unpack,publication_check
from loudness_latch_bdf_survey import state_hash
from loudness_latch_bdf_doubling_survey import canonical,store
from loudness_latch_increment_probes import hashes
from loudness_lab_metadata import environment

ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/'evidence/loudness_latch_bdf_static_precision_forced_clock.json.gz'
SUMMARY=ROOT/'evidence/loudness_latch_bdf_static_precision_forced_clock_summary.json'
PROTOCOL=ROOT/'docs/BIESTABLE_FORZAMIENTO_RELOJ_PROTOCOLO.md'
SUBDIVISIONS=(2,4)
AUDIT_INDICES=(0,31,63)
PATHS=tuple(dict.fromkeys((*OLD_PATHS,Path(__file__).resolve(),PROTOCOL,
                         ROOT/'tools/loudness_latch_bdf_forcing.py',ROOT/'tools/loudness_latch_bdf_clock_plan.py',
                         FAILED_DATA,FAILED_SUMMARY,ROOT/'evidence/loudness_latch_bdf_static_precision_forced_windows_validation.json')))


def refine(network,base,subdivisions):
    old=unpack(network,base['initial']);steps=[];samples=[];stop=None;attempts=0
    for index,step in enumerate(base['reference']):
        start=old.time_s;h=step['diagnostics']['actual_dt_s'];target=step['history']['time_s']
        try:schedule=plan(old,target,subdivisions)
        except ValueError as exc:
            stop=dict(index=index,substep=0,error=str(exc),incoming=pack(old),incoming_sha256=state_hash(old),
                      destination_s=target,dt_s=None,candidate=None,diagnostics=None,publication=None)
            break
        for j in range(1,subdivisions+1):
            destination=schedule[j-1]
            dt=destination-old.time_s;snapshot=state_hash(old);new=None;diag=None;pub=None;attempts+=1
            try:
                if not np.isfinite(dt) or dt<1e-12:raise ValueError('interval outside 1 ps domain')
                new,diag=network.advance(old,10.,dt)
                pub=publication_check(network,old,new,dt,diag)
                if state_hash(old)!=snapshot:raise ValueError('incoming history changed')
                if (not pub['round_trip_exact'] or pub['max_published_kcl_a']>=1e-11
                    or pub['max_branch_equation_error_v']>=1e-14 or diag['correction_v']>=1e-8):
                    raise ValueError('unchanged solve/publication gate failed')
                if new.time_s!=destination:raise ValueError('declared subclock changed')
            except (ValueError,OverflowError,np.linalg.LinAlgError) as exc:
                stop=dict(index=index,substep=j,error=str(exc),incoming=pack(old),incoming_sha256=snapshot,
                    destination_s=destination,dt_s=dt,candidate=None if new is None else pack(new),
                    diagnostics=diag,publication=pub)
                break
            steps.append(dict(base_index=index,substep=j,destination_s=destination,dt_minus_nominal_s=dt-h/subdivisions,
                previous_history_sha256=snapshot,history=pack(new),diagnostics=diag,publication=pub,published=False))
            old=new
        if stop is not None:break
        samples.append(dict(base_index=index,fine_step_index=len(steps)-1,history=pack(old)))
    return dict(subdivisions=subdivisions,initial=base['initial'],steps=steps,samples=samples,stop=stop,
        attempted_intervals=attempts,complete=len(samples)==64,final=pack(old),own_fine_histories=True,
        sampled_histories_are_coarse_accepted_states=False,local_adaptive_error_gate_applied=False,published=False)


def compare(actual,predicted):
    error=abs(np.array(actual)-np.array(predicted));scaled=error/(1e-8+1e-3*abs(np.array(predicted)))
    return dict(maximum_error_v=float(np.max(error)),maximum_scaled_error=float(np.max(scaled)),
                index=int(np.argmax(scaled)),passed=bool(np.max(scaled)<1))


def propagate_forced(network,g,base,reference):
    old=unpack(network,base['initial']);last_ref=old.current;prior_ref=old.previous
    cur1=np.zeros(25);prev1=np.zeros(25);cur2=np.zeros(25);prev2=np.zeros(25)
    rows=[];stop=None
    for index,(step,sample) in enumerate(zip(base['reference'],reference['samples'])):
        new=unpack(network,step['history']);ref=unpack(network,sample['history']).current
        virtual,c,_=candidate(old,step,network);dt=c['effective_dt_s'];gamma=c['gamma']
        current=force.difference(last_ref,old.current)['memory_v']
        previous=force.difference(prior_ref,old.previous)['memory_v']
        vref=force.virtual(current,previous,gamma)
        f=force.forcing(network,g,new,ref,vref,dt,80);f100=force.forcing(network,g,new,ref,vref,dt,100)
        precision={key:curvature.metrics(f[key],f100[key]) for key in ('residual_a','publication_offset_v')}
        v1=(1+gamma)*cur1-gamma*prev1;v2=(1+gamma)*cur2-gamma*prev2
        _,j=network.network.increment_evaluator(10.,virtual,dt)(np.array(step['diagnostics']['increment_v']))
        b,p,direct=stamps(network,new,dt);rhs1=b@v1+force.floats(f['residual_a'])
        hterms=None;rhs2=None;first_audit=None
        try:
            n1,first_audit=solve(j,rhs1[:,None]);n1=n1[:,0];m1=p@n1+direct@v1+force.floats(f['publication_offset_v'])
            hterms=curvature.evaluate(network,g,force.nodes(new.current),n1,dt,80)
            h100=curvature.evaluate(network,g,force.nodes(new.current),n1,dt,100)
            hprecision={key:curvature.metrics(hterms[key],h100[key]) for key in ('residual_a','publication_coordinate_v')}
            rhs2=b@v2-curvature.floats(hterms['residual_a'])
            n2,second_audit=solve(j,rhs2[:,None]);n2=n2[:,0]
            m2=p@n2+direct@v2+curvature.floats(hterms['publication_coordinate_v'])
            if not all(np.isfinite(a).all() for a in (n1,m1,n2,m2)):raise ValueError('nonfinite forced variation')
        except (ValueError,OverflowError,np.linalg.LinAlgError) as exc:
            stop=dict(index=index,error=str(exc),forcing=force.serial(f),rhs_first_a=rhs1.tolist(),
                rhs_second_a=None if rhs2 is None else rhs2.tolist(),first_solve=first_audit,
                curvature=None if hterms is None else force.serial(hterms),
                incoming_first_current_v=cur1.tolist(),incoming_first_previous_v=prev1.tolist(),
                incoming_second_current_v=cur2.tolist(),incoming_second_previous_v=prev2.tolist())
            break
        predictions=dict(linear_node_v=n1,linear_memory_v=m1,quadratic_node_v=n1+n2/2,quadratic_memory_v=m1+m2/2)
        metrics={}
        for order in ('linear','quadratic'):
            metrics[order]={name:compare(force.floats(f[name+'_difference_v']),predictions[order+'_'+name+'_v'])
                            for name in ('node','memory')}
        row=dict(index=index,time_s=new.time_s,coefficients=c,virtual_reference_difference_v=[str(v) for v in vref],
            forcing=force.serial(f),forcing_precision=precision,curvature=force.serial(hterms),curvature_precision=hprecision,
            node_first_v=n1.tolist(),memory_first_v=m1.tolist(),node_second_v=n2.tolist(),memory_second_v=m2.tolist(),
            rhs_first_a=rhs1.tolist(),rhs_second_a=rhs2.tolist(),first_solve=first_audit,second_solve=second_audit,
            predictions={k:v.tolist() for k,v in predictions.items()},comparisons=metrics)
        if index in AUDIT_INDICES:
            exact=solved(j,np.column_stack((rhs1,rhs2)))
            if exact['passed']:
                rounded=np.array(exact['node_map']);computed=np.column_stack((n1,n2))
                exact['maximum_scaled_map_difference']=float(np.max(abs(computed-rounded)/(1+abs(rounded))))
                exact['map_gate_passed']=exact['maximum_scaled_map_difference']<1e-8
            else:exact['map_gate_passed']=False
            row['exact_audit']=exact
        rows.append(row);old=new;prior_ref,last_ref=last_ref,ref
        prev1,cur1=cur1,m1;prev2,cur2=cur2,m2
    return dict(rows=rows,stop=stop,complete=len(rows)==64,forcing_from_reference=True,
        homogeneous_zero_prediction_v=0.,independent_error_estimator=False)


def generate():
    before=hashes(PATHS);env=environment();source=json.loads(gzip.decompress(SOURCE.read_bytes()))
    network=CompensatedBdfNetwork(200,model_parameters(1,'finite_transit'));g=curvature.graph(network);windows=[]
    for base in source['windows']:
        levels=[]
        for n in SUBDIVISIONS:
            refined=refine(network,base,n);forced=propagate_forced(network,g,base,refined)
            levels.append(dict(reference=refined,forced=forced))
            print(json.dumps(dict(window=base['name'],subdivisions=n,fine_intervals=len(refined['steps']),
                fine_complete=refined['complete'],forced_intervals=len(forced['rows']),forced_complete=forced['complete'])),flush=True)
        contrasts=[]
        for a,b in zip(levels[0]['reference']['samples'],levels[1]['reference']['samples']):
            x=unpack(network,a['history']).current;y=unpack(network,b['history']).current
            contrasts.append(dict(index=a['base_index'],time_s=a['history']['time_s'],
                node_difference_4_minus_2_v=node_difference(y,x).tolist(),
                memory_difference_4_minus_2_v=memory_difference(y,x).tolist()))
        windows.append(dict(name=base['name'],initial=base['initial'],levels=levels,refinement_4_minus_2=contrasts))
    if hashes(PATHS)!=before:raise ValueError('forced-window sources changed')
    return dict(schema='rf-d/bdf-static-forced-clock/v1',environment=env,source_sha256=before,
        windows=windows,subdivisions=SUBDIVISIONS,audit_indices=AUDIT_INDICES,absolute_response_gate_v=1e-8,
        relative_response_gate=1e-3,precision_absolute_gate=1e-30,precision_relative_gate=1e-8,
        solve_backward_gate=1e-10,rational_map_gate=1e-8,minimum_interval_s=1e-12,
        charge_coordinate_scale_c_per_v=1e-12,diagnostic_only=True,clock_plan='exact-ULP-ticks/ratio-capped/v1',prior_failed_attempt_modified=False,reference_defects_are_exact_temporal_defects=False,
        fresh_dc_new=False,history_reset_count=0,coefficients_fitted=False,integrator_changed=False,
        independent_error_estimator=False,temporal_error_bound_admitted=False,temporal_refinement_admitted=False,
        physical_switching_admitted=False,audio_admitted=False,deadline_admitted=False,
        limitation='lifted coarse-equation and publication differences extracted from conditional own-history refinements; not exact temporal defect or independently available estimator')


def save(report):
    storage=store(report,OUTPUT);windows=[]
    for w in report['windows']:
        levels=[]
        for level in w['levels']:
            ref=level['reference'];forced=level['forced'];rows=forced['rows']
            metrics={order:{name:dict(passes=sum(row['comparisons'][order][name]['passed'] for row in rows),
                maximum_scaled_error=max((row['comparisons'][order][name]['maximum_scaled_error'] for row in rows),default=None),
                maximum_error_v=max((row['comparisons'][order][name]['maximum_error_v'] for row in rows),default=None))
                for name in ('node','memory')} for order in ('linear','quadratic')}
            levels.append(dict(subdivisions=ref['subdivisions'],fine_intervals=len(ref['steps']),attempts=ref['attempted_intervals'],
                fine_complete=ref['complete'],fine_stop=ref['stop'],forced_intervals=len(rows),forced_complete=forced['complete'],
                forced_stop=forced['stop'],comparisons=metrics,
                maximum_kcl_a=max((s['publication']['max_published_kcl_a'] for s in ref['steps']),default=None),
                maximum_clock_interval_adjustment_s=max((abs(s['dt_minus_nominal_s']) for s in ref['steps']),default=None),
                forcing_precision_passes=sum(all(v['passed'] for v in r['forcing_precision'].values()) for r in rows),
                curvature_precision_passes=sum(all(v['passed'] for v in r['curvature_precision'].values()) for r in rows),
                exact_audits=[dict(index=r['index'],passed=r['exact_audit']['passed'],map_gate_passed=r['exact_audit']['map_gate_passed'],
                    maximum_scaled_map_difference=r['exact_audit'].get('maximum_scaled_map_difference')) for r in rows if 'exact_audit' in r]))
        windows.append(dict(name=w['name'],anchor_time_s=w['initial']['time_s'],levels=levels,
            refinement_sample_count=len(w['refinement_4_minus_2']),maximum_refinement_node_difference_v=max(
                (max(abs(v) for v in row['node_difference_4_minus_2_v']) for row in w['refinement_4_minus_2']),default=None)))
    summary={k:v for k,v in report.items() if k!='windows'}|dict(storage=storage,windows=windows)
    SUMMARY.write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')
    return summary


if __name__=='__main__':save(generate())
