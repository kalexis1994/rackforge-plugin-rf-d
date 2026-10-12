"""Independent algebra, six roots, own directional FD and measured candidate."""
import argparse,json,sys,time,traceback
from decimal import Decimal,localcontext
from pathlib import Path
import numpy as np
from prepare_vco1_portable import ROOT,sha,write
from joint_cycles_analysis import require,TICK
from check_history_propagation import Reader,decoded,bits
from check_joint_reference import D,evaluate
from check_joint_charge_seed import incidence,root_check
from check_charge_basis import root
from check_conditioned_return import checked,branch,GATE,BASE_GATE
from check_history_event import observer
from conditioned_base_bank import bank

ROOT_GATE=np.r_[GATE,np.full(18,1e-11)]

def exact_contract(matrix,direction):
    return np.array([float(sum((D(a)*D(b) for a,b in zip(row,direction)),Decimal(0))) for row in matrix])

def decimal_solve(a,b):
    a=[row.copy() for row in a];b=b.copy();n=len(b)
    for k in range(n):
        pivot=max(range(k,n),key=lambda i:abs(a[i][k]));require(a[pivot][k]!=0,'projected nonsingular system');a[k],a[pivot]=a[pivot],a[k];b[k],b[pivot]=b[pivot],b[k]
        for i in range(k+1,n):
            f=a[i][k]/a[k][k]
            for j in range(k+1,n):a[i][j]-=f*a[k][j]
            b[i]-=f*b[k];a[i][k]=Decimal(0)
    x=[Decimal(0)]*n
    for i in reversed(range(n)):x[i]=(b[i]-sum((a[i][j]*x[j] for j in range(i+1,n)),Decimal(0)))/a[i][i]
    return x

def algebra(proposal):
    active=proposal['active'];require(active==[k for k in range(18) if k!=16],'fixed inactive coordinate');a=np.array(proposal['matrix_v_per_v'])[np.ix_(active,active)];b=np.array(proposal['baseline_drift_v'])[active];u=np.array(proposal['u']);s=np.array(proposal['singular_values']);vt=np.array(proposal['vt']);d=np.array(proposal['direction_v']);keep=s>proposal['relative_cutoff']*s[0]
    require(proposal['relative_cutoff']==1e-8 and np.count_nonzero(keep)==proposal['rank']==16 and d[16]==0 and max(abs(d))<=.1,'rank and bound')
    reconstruction=float(np.max(np.abs(u@np.diag(s)@vt-a)));orthogonality=float(max(np.max(abs(u.T@u-np.eye(17))),np.max(abs(vt@vt.T-np.eye(17)))))
    require(reconstruction<=1e-12 and orthogonality<=1e-12,'SVD identities')
    v=vt[keep].T;av=[[sum((D(a[i,k])*D(v[k,j]) for k in range(17)),Decimal(0)) for j in range(16)] for i in range(17)]
    gram=[[sum((av[i][j]*av[i][k] for i in range(17)),Decimal(0)) for k in range(16)] for j in range(16)]
    rhs=[-sum((av[i][j]*D(b[i]) for i in range(17)),Decimal(0)) for j in range(16)];coordinates=decimal_solve(gram,rhs);independent=np.array([float(sum((D(v[i,j])*coordinates[j] for j in range(16)),Decimal(0))) for i in range(17)])
    expected=proposal['trust_scale']*independent;error=float(np.max(abs(d[active]-expected)));require(error<=1e-10,'independent projected direction')
    residual=[D(b[i])+sum((D(a[i,j])*D(d[active[j]]) for j in range(17)),Decimal(0)) for i in range(17)]
    normal=max(abs(sum((D(a[i,j])*residual[i] for i in range(17)),Decimal(0))) for j in range(17));minimum_norm=abs(sum((D(vt[16,j])*D(d[active[j]]) for j in range(17)),Decimal(0)))
    require(proposal['trust_scale']==1 and normal<=D(1e-12) and minimum_norm<=D(1e-12),'normal equations and minimum norm')
    return dict(rank=16,reconstruction_error=reconstruction,orthogonality_error=orthogonality,independent_direction_error_v=error,normal_equation_error_v=str(normal),null_direction_projection_v=str(minimum_norm),unreachable_residual_v=list(map(float,residual)))

def read_history(path,id,coefficient,schedule,points,serial,targets,inc,caps,deadline):
    r=Reader(ROOT/path);require(r.bytes(8)==b'RFJDIRO1' and r.integer('I')==id and r.integer('I')==42544,'own header');require(bits(r.floats(1),np.array([coefficient])),'own coefficient');raw,state,current,metrics=root(r);root_report=root_check(state,current,targets,metrics[4],inc,caps);observations=[];samples={};last=0;equations=[]
    for step,(ticks,half,_) in enumerate(schedule):
        require(time.perf_counter()<deadline,'reference budget');require(r.integer('I')==step and r.integer('Q')==ticks and r.integer('I')==half and ticks-last==half,'complete own calendar');last=ticks;obs=r.floats(7);observations.append(obs);flag=r.bytes(1)[0];require(flag==int(step<64 or step in points),'fixed sample flag')
        if flag:
            states=r.floats(2000).reshape(5,400);samples[step]=states
            require(bits(obs,np.array([states[4,k]+states[4,200+k] for k in [43,46,54,44,12,39,194]])),'own sample observations')
            if step<64:require(bits(states,serial[step]),'serial worker prefix all bits')
            if step==0:require(bits(states[0],raw[:400]),'history from own root')
            elif step-1 in samples:require(bits(states[0],samples[step-1][4]),'adjacent own state bits')
            if step in points:
                report=evaluate((0,half*TICK,*[decoded(row) for row in states]));require(report['rows']==400 and report['residual_gate_ratio']<=1 and report['correction_gate_ratio']<=1,'own nonlinear candidate');equations.append(dict(step=step,**report))
    require(r.integer('I')==2,'two own events');events=[]
    for _ in range(2):
        index=r.integer('I');ticks=r.integer('Q');half=r.integer('I');a=r.floats(400);b=r.floats(400);alpha=float(r.floats(1)[0]);z=r.floats(400);native_time=float(r.floats(1)[0]);require(index>0 and (ticks,half)==schedule[index][:2],'own event clock');require(bits(np.array([a[k]+a[200+k] for k in [43,46,54,44,12,39,194]]),observations[index-1]) and bits(np.array([b[k]+b[200+k] for k in [43,46,54,44,12,39,194]]),observations[index]),'event bracket observations')
        if index-1 in samples:require(bits(a,samples[index-1][4]),'event old sample bits')
        if index in samples:require(bits(b,samples[index][4]),'event new sample bits')
        oa,oz,*_=observer(a,b);require(abs(alpha-float(oa))<=2e-15 and abs(float(decoded(z)[43])+2)<=1e-13,'own event observer');observation=checked(list(map(float,decoded(z))),list(map(float,oz)),BASE_GATE,'own projected observation',0);exact_time=D(ticks-half)*D(TICK)+D(half*TICK)*D(alpha);require(abs(D(native_time)-exact_time)<=D(1e-17),'own absolute time');events.append(dict(index=index,ticks=ticks,half_ticks=half,alpha=alpha,z=decoded(z),time=exact_time,native_time=native_time,observation=observation))
    period=float(r.floats(1)[0]);drift=r.floats(200);r.end();exact_period=events[1]['time']-events[0]['time'];require(abs(D(period)-exact_period)<=D(1e-17),'own period reconstruction');exact_drift=[b-a for a,b in zip(events[0]['z'],events[1]['z'])];comparison=checked(drift,list(map(float,exact_drift)),BASE_GATE,'own compensated drift',0)
    return dict(id=id,coefficient=coefficient,root=raw,root_values=state+current,root_report=root_report,samples=samples,observations=np.array(observations),events=events,period=period,exact_period=exact_period,drift=exact_drift,equations=equations,drift_observation=comparison,path=path)

def check(native):
    require(native['passed'],'passed native');inputs=json.loads((ROOT/'evidence/voice_dynamic_direction_inputs01.json').read_text(encoding='utf8'));proposal=inputs['proposal'];algebra_report=algebra(proposal);base=bank();d=np.array(proposal['direction_v']);epsilon=proposal['epsilon_a'];require(bits(np.array([epsilon]),np.array([1e-5/float(np.dot(base['gain'],abs(d)))])),'conservative epsilon')
    inp=Reader(ROOT/inputs['path']);require(inp.bytes(8)==b'RFJDIRI1' and inp.integer('I')==42544 and bits(inp.floats(436),base['root'][:436]) and bits(inp.floats(19),np.r_[d,epsilon]),'frozen input');count=inp.integer('I');points=[inp.integer('I') for _ in range(count)];require(points==inputs['points']==sorted(base['samples']) and count==20,'operator points');schedule=[]
    for ticks,half,obs in base['schedule']:require(inp.integer('Q')==ticks and inp.integer('I')==half and bits(inp.floats(7),obs),'inherited calendar bits');schedule.append((ticks,half,obs))
    inp.end();directory=next(Path(o['path']).parent for o in native['outputs'] if o['path'].endswith('/base.bin'));r=Reader(ROOT/directory/'base.bin');require(r.bytes(8)==b'RFJDBAS1','base root codec');raw,state,current,metrics=root(r);r.end();require(bits(raw,base['root'][:436]),'cold base root bits');inc,caps=incidence();values=list(map(float,(ROOT/'evidence/voice_joint_charge_response_targets01.txt').read_text(encoding='utf8').splitlines()[0].split()));targets=[D(values[2*k])+D(values[2*k+1]) for k in range(18)];root_base=root_check(state,current,targets,metrics[4],inc,caps)
    serial_path=(directory/'serial-prefix.bin').as_posix();s=Reader(ROOT/serial_path);require(s.bytes(8)==b'RFJDSP01' and s.integer('I')==5,'serial prefix header');histories=[];deadline=time.perf_counter()+300
    for id,coefficient in enumerate([epsilon,-epsilon,epsilon/2,-epsilon/2,1.]):
        require(s.integer('I')==id,'serial prefix order');prefix=[s.floats(2000).reshape(5,400) for _ in range(64)];target=[v+D(coefficient*d[k]) for k,v in enumerate(targets)];path=(directory/f'own-{id}.bin').as_posix();histories.append(read_history(path,id,coefficient,schedule,points,prefix,target,inc,caps,deadline));print('DIRECTION_REFERENCE_HISTORY',id,flush=True)
    s.end();root_direction=exact_contract(base['basis'],d);stage_direction={step:exact_contract(base['samples'][step][2],d) for step in points};old_direction={step:exact_contract(base['samples'][step][1],d) for step in points};event_direction=[dict(state=exact_contract(e['response'],d),time=float(sum((D(a)*D(b) for a,b in zip(e['dt'],d)),Decimal(0)))) for e in base['events']];dt_direction=event_direction[1]['time']-event_direction[0]['time'];dd_direction=event_direction[1]['state']-event_direction[0]['state'];finite=[]
    for scale,plus,minus in [(1.,histories[0],histories[1]),(.5,histories[2],histories[3])]:
        e=scale*epsilon;root_change=np.array([float((a-b)/2) for a,b in zip(plus['root_values'],minus['root_values'])]);root_fd=checked(root_change,e*root_direction,ROOT_GATE,'own root direction');stages=[]
        for step in points:
            ps,ms=plus['samples'][step],minus['samples'][step];old_change=np.array([float((a-b)/2) for a,b in zip(decoded(ps[0]),decoded(ms[0]))]);changes=np.r_[[float((a-b)/2) for a,b in zip(decoded(ps[3]),decoded(ms[3]))],[float((a-b)/2) for a,b in zip(decoded(ps[4]),decoded(ms[4]))]];stages.append(dict(step=step,old=checked(old_change,e*old_direction[step],GATE,'own old state direction'),stages=checked(changes,e*stage_direction[step],np.tile(GATE,2),'own full stage direction')))
        event_fd=[]
        for j in range(2):
            change=np.array([float((a-b)/2) for a,b in zip(plus['events'][j]['z'],minus['events'][j]['z'])]);time_change=float((plus['events'][j]['time']-minus['events'][j]['time'])/2);event_fd.append(dict(state=checked(change,e*event_direction[j]['state'],GATE,'own event direction'),time=checked([time_change],[e*event_direction[j]['time']],1e-17,'own event time direction')));require(abs(e*event_direction[j]['state'][43])<=1e-18,'direction projected ramp')
        delta=np.array([float((a-b)/2) for a,b in zip(plus['drift'],minus['drift'])]);time_change=float((plus['exact_period']-minus['exact_period'])/2);predicted=e*dd_direction
        finite.append(dict(scale=scale,root=root_fd,stage_reports=stages,events=event_fd,period=checked([time_change],[e*dt_direction],1e-17,'own direction period'),drift=checked(delta,predicted,GATE,'own direction drift'),capacitors=checked(list(map(float,branch(delta))),list(map(float,branch(predicted))),2e-8,'own direction capacitor drift'),effect_ledger=dict(period_observed_s=time_change,period_predicted_s=e*dt_direction,period_predicted_to_floor=abs(e*dt_direction)/1e-17,j7_observed_v=float(delta[194]),j7_predicted_v=float(predicted[194]),j7_predicted_to_floor=abs(float(predicted[194]))/1e-8)))
    candidate=histories[4];cb=np.array(list(map(float,branch(candidate['drift']))));bb=np.array(proposal['baseline_drift_v']);pred=np.array(proposal['predicted_drift_v']);j7=float(candidate['drift'][194]);base_j7=float(base['drift'][194]);l2=float(np.linalg.norm(cb)/np.linalg.norm(bb));maximum=float(np.max(abs(cb))/np.max(abs(bb)));improved=l2<=.5 and maximum<=.5 and abs(j7)<=abs(base_j7);observations=base['schedule'];base_obs=np.array([row[2] for row in observations]);clock_change=np.max(abs(candidate['observations']-base_obs),axis=0)
    summary=[dict(id=h['id'],coefficient=h['coefficient'],root_report=h['root_report'],equations=h['equations'],events=[{k:(str(v) if k=='time' else v) for k,v in e.items() if k not in ['z']} for e in h['events']],period_s=h['period'],drift_observation=h['drift_observation']) for h in histories]
    private={inputs['path']:sha(ROOT/inputs['path']),**inputs['private_used_sha256']}
    for output in native['outputs']:
        if output['path'].endswith('.bin'):private[output['path']]=sha(ROOT/output['path'])
    return dict(algebra=algebra_report,proposal=proposal,input_sha256=private,base_root=root_base,histories=summary,nonlinear_fd=finite,candidate=dict(improvement_admitted=improved,l2_ratio=l2,maximum_ratio=maximum,j7_baseline_drift_v=base_j7,j7_drift_v=j7,predicted_j7_drift_v=proposal['predicted_j7_drift_v'],baseline_capacitor_drift_v=bb.tolist(),capacitor_drift_v=cb.tolist(),predicted_capacitor_drift_v=pred.tolist(),prediction_error_v=(cb-pred).tolist(),worsened_branches=[k for k in range(18) if abs(cb[k])>abs(bb[k])+2e-8],same_clock_max_observable_change_v=clock_change.tolist(),baseline_period_s=base['period'],period_s=candidate['period'],event_indices=[e['index'] for e in candidate['events']]),augmented_root_count=6,augmented_rows=1308,own_native_step_solves=212720,serial_prefix_step_solves=320,serial_prefix_bit_coordinates=640000,independent_nonlinear_rows=40000,independent_nonlinear_points=100,selected_points_per_history=20,stored_points_per_history=81,own_event_observations=10,full_direction_fd_admitted=True,all_target_fd_admitted=False,independent_roots=0,independent_all_step_propagation=False,period_map_admitted=False,steady_periodicity_admitted=False,adaptive_derivative_admitted=False,physical_fidelity=False,real_time=False,new_audio=False)

def main():
    p=argparse.ArgumentParser();p.add_argument('--native',type=int,required=True);p.add_argument('--attempt',type=int,required=True);args=p.parse_args();name=f'evidence/voice_dynamic_direction_native{args.native:02d}.json';out=f'evidence/voice_dynamic_direction_reference{args.attempt:02d}.json';require(not (ROOT/out).exists(),'exclusive reference');names={name,'tools/check_dynamic_direction.py','evidence/voice_dynamic_direction_inputs01.json','evidence/voice_joint_charge_response_targets01.txt','docs/VOZ_CORRECCION_DINAMICA_PROTOCOLO.md'}
    for module in list(sys.modules.values()):
        f=getattr(module,'__file__',None)
        if f:
            path=Path(f).resolve()
            if path.is_relative_to(ROOT/'tools') and path.suffix=='.py':names.add(path.relative_to(ROOT).as_posix())
    before={n:sha(ROOT/n) for n in sorted(names)};report=dict(schema='rf-d/dynamic-direction-reference/v1',passed=False,source_sha256=before);start=time.perf_counter();native=json.loads((ROOT/name).read_text(encoding='utf8'))
    try:
        with localcontext() as ctx:ctx.prec=100;report.update(check(native))
        require(time.perf_counter()-start<=300,'total reference budget');report['passed']=True
    except Exception:
        report['failure']=traceback.format_exc();report['failed_source_text']=(ROOT/'tools/check_dynamic_direction.py').read_text(encoding='utf8')
        try:
            with localcontext() as ctx:ctx.prec=100;check(native)
            report['replay']='unexpected pass'
        except Exception:report['replay']=traceback.format_exc()
    report['wall_s']=time.perf_counter()-start;report['source_sha256_after']={n:sha(ROOT/n) for n in sorted(names)};require(before==report['source_sha256_after'],'stable sources');write(out,report);print('DIRECTION_REFERENCE',report['passed'],report.get('failure',''),flush=True)
if __name__=='__main__':main()
