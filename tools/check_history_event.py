"""Decimal crossing observer, phase projection and nonlinear own endpoints."""
import argparse,json,sys,time,traceback
from decimal import Decimal,localcontext
from pathlib import Path
import numpy as np
from prepare_vco1_portable import ROOT,sha,write
from check_history_propagation import Reader,decoded,bits
from check_history_tangent import mass,stage_jacobian,ratio,COLS
from check_joint_reference import D
from joint_cycles_analysis import require,TICK

def prior_brackets():
    receipt=json.loads((ROOT/'evidence/voice_history_propagation_native01.json').read_text());name=next(o['path'] for o in receipt['outputs'] if o['path'].endswith('/propagation.bin'));r=Reader(ROOT/name);require(r.bytes(8)==b'RFJHPRO1' and r.integer('I')==48,'prior codec')
    for k in range(48):require(r.integer('I')==k,'prior scalar index');r.floats(3600)
    require(r.integer('I')==12 and r.integer('I')==64,'prior windows');out={}
    for window in range(12):
        metadata=[r.integer('I') for _ in range(3)];start=r.integer('Q');epsilon=r.floats(9).copy();records=[]
        for step in range(64):
            ticks=r.integer('Q');half=r.integer('I');states=r.floats(2000).reshape(5,400);s=r.floats(3600).reshape(400,9);r.floats(7200)
            if step<2:records.append((ticks,half,states.copy(),s.copy()))
        if metadata[2]:out[window]=(metadata,start,epsilon,records)
    r.end();return out,name

def observer(a,b):
    ra=D(a[43]+a[243]);rb=D(b[43]+b[243]);require(ra<Decimal(-2)<=rb and rb>ra,'same transverse bracket');alpha=(Decimal(-2)-ra)/(rb-ra);require(0<=alpha<=1,'alpha interval');aa=decoded(a);bb=decoded(b);z=[x+alpha*(y-x) for x,y in zip(aa,bb)];return alpha,z,ra,rb,aa,bb

def projection(a,b,sa,sb,h):
    alpha,z,ra,rb,aa,bb=observer(a,b);dalpha=[];dz=np.empty((200,9));unprojected=np.empty((200,9))
    for r in range(9):
        v=-((1-alpha)*D(sa[43,r])+alpha*D(sb[43,r]))/(rb-ra);dalpha.append(v)
        for k in range(200):
            weighted=(1-alpha)*D(sa[k,r])+alpha*D(sb[k,r]);unprojected[k,r]=float(weighted);dz[k,r]=float(weighted+(bb[k]-aa[k])*v)
    return alpha,z,np.array(list(map(float,dalpha))),np.array([float(D(h)*v) for v in dalpha]),dz,unprojected

def check(native):
    require(native['passed'],'passed native');inputs=json.loads((ROOT/'evidence/voice_history_event_inputs01.json').read_text());old,old_name=prior_brackets();name=next(o['path'] for o in native['outputs'] if o['path'].endswith('/event.bin'));r=Reader(ROOT/name);require(r.bytes(8)==b'RFJHEVT1' and r.integer('I')==8,'event codec');records=[];gate=np.array([1e-11 if 98<=k<133 else 1e-8 for k in range(200)]);base_gate=np.array([1e-16 if 98<=k<133 else 1e-13 for k in range(200)]);deadline=time.perf_counter()+300
    for event in inputs['events']:
        require(time.perf_counter()<deadline,'reference budget');eid=event['id'];ids=[r.integer('I') for _ in range(4)];start=r.integer('Q');epsilon=r.floats(9);metadata,old_start,old_epsilon,previous=old[event['window']]
        require(ids==[eid,*metadata] and start==event['start_ticks']==old_start and bits(epsilon,old_epsilon) and bits(epsilon,event['epsilon']),'frozen event metadata/epsilon');u=np.eye(200)[:,COLS];baseline=[];independent=[];stage_checks=[]
        for step in range(2):
            ticks=r.integer('Q');half=r.integer('I');states=r.floats(2000).reshape(5,400);s=r.floats(3600).reshape(400,9);old_ticks,old_half,old_states,old_s=previous[step]
            require(ticks==old_ticks and half==old_half and bits(states,old_states) and bits(s,old_s),'prior states and sensitivity bits');case=(0,half*TICK,*[decoded(a) for a in states]);m=mass(case[2],case[1]);rhs=np.vstack([2*(m@u),-2*(m@u)]);oracle=np.linalg.solve(stage_jacobian(case),rhs);u=oracle[200:];independent.append(oracle[200:]);baseline.append(states[4]);checks=[]
            for direction in range(9):
                comparison=ratio(epsilon[direction]*s[:,direction],epsilon[direction]*oracle[:,direction],np.tile(gate,2),1e-4);require(comparison['max_ratio']<=1,'independent stage response');checks.append(comparison)
            stage_checks.append(checks)
        h=event['half_ticks'][1]*TICK;alpha=float(r.floats(1)[0]);z=r.floats(400);dalpha=r.floats(9);dt=r.floats(9);dz=r.floats(1800).reshape(200,9);oa,oz,oda,odt,odz,unprojected=projection(*baseline,*independent,h)
        require(abs(alpha-float(oa))<=2e-15,'baseline alpha independent');base=ratio(np.array(list(map(float,decoded(z)))),np.array(list(map(float,oz))),base_gate,0);require(base['max_ratio']<=1,'base interpolated state');require(abs(float(decoded(z)[43])+2)<=1e-13,'base section ramp');require(dalpha[8]==dt[8]==0 and np.count_nonzero(dz[:,8])==0 and oda[8]==odt[8]==0 and np.count_nonzero(odz[:,8])==0,'event negative control')
        responses=[]
        for direction,col in enumerate(COLS):
            e=float(epsilon[direction]);state_check=ratio(e*dz[:,direction],e*odz[:,direction],gate,1e-4);time_check=ratio(np.array([e*dt[direction]]),np.array([e*odt[direction]]),1e-17,1e-4);alpha_check=ratio(np.array([e*dalpha[direction]]),np.array([e*oda[direction]]),1e-17/h,1e-4);require(max(state_check['max_ratio'],time_check['max_ratio'],alpha_check['max_ratio'])<=1,'independent phase/time response');require(abs(e*dz[43,direction])<=1e-18 and abs(e*odz[43,direction])<=1e-18,'section tangent zero');finite=[];observations=[]
            for scale in [1.,.5]:
                signs=[];observation_checks=[]
                for sign in [1.,-1.]:
                    own_alpha=float(r.floats(1)[0]);a=r.floats(400);b=r.floats(400);own_z=r.floats(400);expected_alpha,expected_z,*_=observer(a,b);require(abs(own_alpha-float(expected_alpha))<=2e-15,'own alpha independent');observed=ratio(np.array(list(map(float,decoded(own_z)))),np.array(list(map(float,expected_z))),base_gate,0);require(observed['max_ratio']<=1 and abs(float(decoded(own_z)[43])+2)<=1e-13,'own interpolated state');signs.append((own_alpha,decoded(own_z)));observation_checks.append(observed)
                # Use Decimal subtraction of the full HIGH/LOW own states.
                change=np.array([float((a-b)/2) for a,b in zip(signs[0][1],signs[1][1])]);time_change=h*(signs[0][0]-signs[1][0])/2;state_fd=ratio(change,scale*e*dz[:,direction],gate,1e-4);time_fd=ratio(np.array([time_change]),np.array([scale*e*dt[direction]]),1e-17,1e-4);require(max(state_fd['max_ratio'],time_fd['max_ratio'])<=1,'own projected state/time response');finite.append(dict(scale=scale,state=state_fd,time=time_fd));observations.append(observation_checks)
            responses.append(dict(column=col,epsilon=e,state_independent=state_check,time_independent=time_check,alpha_independent=alpha_check,nonlinear_fd=finite,own_state_observations=observations))
        omitted_ramp_change=float(epsilon[0]*unprojected[43,0]);require(abs(omitted_ramp_change)>gate[43],'positive control needs phase term')
        records.append(dict(**event,h_s=h,alpha=alpha,offset_from_bracket_s=h*alpha,stage_checks=stage_checks,baseline_observation=base,omitted_time_term_ramp_change_v=omitted_ramp_change,responses=responses));print('EVENT_REFERENCE',eid,flush=True)
    r.end();return dict(records=records,input_sha256={name:sha(ROOT/name),old_name:sha(ROOT/old_name),inputs['path']:sha(ROOT/inputs['path']),**inputs['private_used_sha256']},baseline_bit_reproductions=16,baseline_sensitivity_bit_coordinates=57600,event_directions=72,event_state_coordinates=14400,perturbed_native_step_solves=576,own_event_observations=288,negative_controls=8,positive_controls=8,independent_roots=0,local_interpolated_event_derivative_admitted=True,continuous_event_derivative_admitted=False,adaptive_derivative_admitted=False,period_map_admitted=False,new_audio=False,physical_fidelity=False,real_time=False)

def main():
    a=argparse.ArgumentParser();a.add_argument('--native',type=int,required=True);a.add_argument('--attempt',type=int,required=True);args=a.parse_args();name=f'evidence/voice_history_event_native{args.native:02d}.json';out=f'evidence/voice_history_event_reference{args.attempt:02d}.json';require(not (ROOT/out).exists(),'exclusive receipt');names={name,'evidence/voice_history_event_inputs01.json','docs/VOZ_EVENTO_HISTORIA_PROTOCOLO.md','tools/check_history_event.py'}
    for module in list(sys.modules.values()):
        f=getattr(module,'__file__',None)
        if f:
            p=Path(f).resolve()
            if p.is_relative_to(ROOT/'tools') and p.suffix=='.py':names.add(p.relative_to(ROOT).as_posix())
    before={n:sha(ROOT/n) for n in sorted(names)};report=dict(schema='rf-d/history-event-reference/v1',passed=False,source_sha256=before);started=time.perf_counter();native=json.loads((ROOT/name).read_text())
    try:
        with localcontext() as ctx:ctx.prec=100;report.update(check(native))
        report['passed']=True
    except Exception:
        report['failure']=traceback.format_exc();report['failed_source_text']=(ROOT/'tools/check_history_event.py').read_text()
        try:
            with localcontext() as ctx:ctx.prec=100;check(native)
            report['replay']='unexpected pass'
        except Exception:report['replay']=traceback.format_exc()
    report['source_sha256_after']={n:sha(ROOT/n) for n in sorted(names)};require(before==report['source_sha256_after'],'unchanged reference sources');report['wall_s']=time.perf_counter()-started;write(out,report);print('EVENT_REFERENCE_PASSED',report['passed'],report.get('failure',''),flush=True)
if __name__=='__main__':main()
