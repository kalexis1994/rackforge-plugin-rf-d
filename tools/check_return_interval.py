"""Selected independent operators and complete own C27 return histories."""
import argparse,json,sys,time,traceback
from decimal import Decimal,localcontext
from pathlib import Path
import numpy as np
from prepare_vco1_portable import ROOT,sha,write
from check_history_propagation import Reader,decoded,bits
from check_history_tangent import mass,stage_jacobian,ratio,COLS
from check_history_event import observer,projection
from check_joint_reference import D,ci,evaluate
from chain_charge_reference import CAPS
from joint_cycles_analysis import require,TICK,trace
from prepare_history_propagation import OBS

GATE=np.array([1e-11 if 98<=k<133 else 1e-8 for k in range(200)])
BASE_GATE=np.array([1e-16 if 98<=k<133 else 1e-13 for k in range(200)])

def checked(a,b,gate,label,relative=1e-4):
    result=ratio(np.asarray(a),np.asarray(b),gate,relative);require(result['max_ratio']<=1,label);return result

def branch(values):
    out=[]
    for a,b,_ in [*CAPS,(67,7,10e-6)]:
        b=b if isinstance(b,int) else 66 if b=='BUS' else None
        out.append(values[ci(a)]-(values[ci(b)] if b is not None else 0))
    return out

def read_event(r,a,b,h,sa,sb,epsilon):
    alpha=float(r.floats(1)[0]);state=r.floats(400);da=r.floats(9);dt=r.floats(9);dz=r.floats(1800).reshape(200,9)
    oa,oz,oda,odt,odz,_=projection(a,b,sa,sb,h)
    require(abs(alpha-float(oa))<=2e-15,'base event alpha')
    base=checked(list(map(float,decoded(state))),list(map(float,oz)),BASE_GATE,'base event state',0)
    require(abs(float(decoded(state)[43])+2)<=1e-13,'base event section')
    require(da[8]==dt[8]==0 and np.count_nonzero(dz[:,8])==0,'event zero control')
    comparisons=[]
    for c in range(9):
        e=epsilon[c];comparisons.append(dict(column=COLS[c],state=checked(e*dz[:,c],e*odz[:,c],GATE,'independent projected state'),time=checked([e*dt[c]],[e*odt[c]],1e-17,'independent event time'),alpha=checked([e*da[c]],[e*oda[c]],1e-17/h,'independent alpha')))
        require(abs(e*dz[43,c])<=1e-18 and abs(e*odz[43,c])<=1e-18,'projected ramp tangent')
    return dict(alpha=alpha,state=state,dt=dt,dz=dz,oracle_dt=odt,oracle_dz=odz,decimal_z=oz,observation=base,comparisons=comparisons)

def check(native):
    require(native['passed'],'passed native');inputs=json.loads((ROOT/'evidence/voice_return_interval_inputs01.json').read_text());inp=Reader(ROOT/inputs['path'])
    require(inp.bytes(8)==b'RFJFINT1','input codec');n=inp.integer('I');start=inp.integer('Q');initial=inp.floats(400);fixtures=[inp.floats(2000).reshape(5,400) for _ in range(4)];count=inp.integer('I');points=[inp.integer('I') for _ in range(count)];require(n==22356 and start==inputs['start_ticks'] and points==inputs['points'] and count==15,'input metadata')
    schedule=[(inp.integer('Q'),inp.integer('I'),inp.floats(7)) for _ in range(n)];inp.end()
    name=next(o['path'] for o in native['outputs'] if o['path'].endswith('/return.bin'));r=Reader(ROOT/name);require(r.bytes(8)==b'RFJRET01' and r.integer('I')==n and r.integer('Q')==start,'output metadata')
    old_trace_name='references-local/joint-corrected-cycles01/0-65536/trace.bin';saved_trace=trace(ROOT/old_trace_name)[inputs['trace_begin_row']:inputs['trace_end_row']];require(len(saved_trace)==n,'complete saved trace');samples={};last=start;deadline=time.perf_counter()+300
    for step,(ticks,half,obs) in enumerate(schedule):
        require(time.perf_counter()<deadline,'reference budget');require(r.integer('I')==step and r.integer('Q')==ticks and r.integer('I')==half and ticks-last==half,'exact complete calendar');last=ticks
        require(bits(r.floats(7),obs) and int(saved_trace[step]['ticks'])==ticks and int(saved_trace[step]['half_ticks'])==half and bits(obs,np.array([saved_trace[step][key] for key,_ in OBS])),'full trace observation bits');flag=r.bytes(1)[0];require(flag==int(step in points),'preselected sample flag')
        if flag:
            states=r.floats(2000).reshape(5,400);u=r.floats(1800).reshape(200,9);s=r.floats(3600).reshape(400,9);samples[step]=(states,u,s)
            require(bits(obs,np.array([states[4,k]+states[4,200+k] for _,k in OBS])),'sample endpoint observations')
    require(last==inputs['end_ticks'] and sorted(samples)==points,'complete interval coverage')
    gain=r.floats(9);epsilon=r.floats(9);base=np.array([1e-10 if 98<=k<133 else 1e-5 for k in COLS]);target=np.tile([1e-8 if 98<=k<133 else 1e-5 for k in range(200)],2)
    require((gain>=1).all() and (epsilon>0).all() and bits(epsilon,base/gain),'native complete gain epsilon');require(bits(samples[0][0][0],initial) and bits(samples[0][1],np.eye(200)[:,COLS]),'initial state and basis')
    for step,fixture in zip([0,1,n-2,n-1],fixtures):require(bits(samples[step][0],fixture),'full fixture bits')
    operators=[];oracles={}
    for step in points:
        require(time.perf_counter()<deadline,'reference budget');states,u,s=samples[step];h=schedule[step][1]*TICK
        if step-1 in samples:require(bits(states[0],samples[step-1][0][4]) and bits(u,samples[step-1][2][200:]),'adjacent saved recurrence bits')
        require(np.count_nonzero(s[:,8])==0 and np.count_nonzero(u[:,8])==(1 if step==0 else 0),'selected zero control');sample_gain=np.max(base*np.abs(s)/target[:,None],axis=0);require((sample_gain<=gain*(1+1e-15)).all(),'all-step native gain bounds selected operators')
        case=(0,h,*[decoded(a) for a in states]);m=mass(case[2],h);oracle=np.linalg.solve(stage_jacobian(case),np.vstack([2*(m@u),-2*(m@u)]));oracles[step]=oracle
        comparisons=[checked(epsilon[c]*s[:,c],epsilon[c]*oracle[:,c],np.tile(GATE,2),'selected independent operator') for c in range(9)]
        operators.append(dict(step=step,h_s=h,comparisons=comparisons,nonlinear_candidate=evaluate(case)));print('RETURN_REFERENCE_OPERATOR',step,flush=True)
    h1=schedule[1][1]*TICK;h2=schedule[-1][1]*TICK;events=[]
    for a,b,h in [(0,1,h1),(n-2,n-1,h2)]:events.append(read_event(r,samples[a][0][4],samples[b][0][4],h,oracles[a][200:],oracles[b][200:],epsilon))
    first,second=events;fixed=D((schedule[-2][0]-schedule[0][0])*TICK);period=float(r.floats(1)[0]);drift=r.floats(200);dt=r.floats(9);dd=r.floats(1800).reshape(200,9)
    require(abs(D(period)-(fixed+D(h2)*D(second['alpha'])-D(h1)*D(first['alpha'])))<=D(1e-17),'base period reconstruction')
    base_drift=[b-a for a,b in zip(decoded(first['state']),decoded(second['state']))];drift_observation=checked(drift,list(map(float,base_drift)),BASE_GATE,'compensated baseline drift',0);independent=[]
    for c in range(9):independent.append(dict(column=COLS[c],period=checked([epsilon[c]*dt[c]],[epsilon[c]*(second['oracle_dt'][c]-first['oracle_dt'][c])],1e-17,'independent selected endpoint period'),drift=checked(epsilon[c]*dd[:,c],epsilon[c]*(second['oracle_dz'][:,c]-first['oracle_dz'][:,c]),GATE,'independent selected endpoint drift')))
    require(dt[8]==0 and np.count_nonzero(dd[:,8])==0,'complete interval zero output');own=[];finite=[]
    for scale in [1.,.5]:
        signs=[]
        for sign in [1.,-1.]:
            require(bits(r.floats(2),np.array([scale,sign])),'own history order');ends=[r.floats(400) for _ in range(4)];zs=[];alphas=[];observations=[]
            for a,b in [(0,1),(2,3)]:
                alpha=float(r.floats(1)[0]);z=r.floats(400);oa,oz,*_=observer(ends[a],ends[b]);require(abs(alpha-float(oa))<=2e-15,'own event alpha');observation=checked(list(map(float,decoded(z))),list(map(float,oz)),BASE_GATE,'own event observation',0);require(abs(float(decoded(z)[43])+2)<=1e-13,'own event section');alphas.append(alpha);zs.append(decoded(z));observations.append(observation)
            own_period=float(r.floats(1)[0]);require(abs(D(own_period)-(fixed+D(h2)*D(alphas[1])-D(h1)*D(alphas[0])))<=D(1e-17),'own period reconstruction');signs.append((alphas,zs));own.append(dict(scale=scale,sign=sign,alphas=alphas,period_s=own_period,observations=observations))
        changes=[np.array([float((a-b)/2) for a,b in zip(signs[0][1][j],signs[1][1][j])]) for j in range(2)];dchanges=np.array([float(((a-b)-(c-d))/2) for a,b,c,d in zip(signs[0][1][1],signs[0][1][0],signs[1][1][1],signs[1][1][0])]);tchange=float((D(h2)*(D(signs[0][0][1])-D(signs[1][0][1]))-D(h1)*(D(signs[0][0][0])-D(signs[1][0][0])))/2);e=scale*epsilon[3]
        finite.append(dict(scale=scale,first_event=checked(changes[0],e*first['dz'][:,3],GATE,'full own first event'),second_event=checked(changes[1],e*second['dz'][:,3],GATE,'full own second event'),period=checked([tchange],[e*dt[3]],1e-17,'complete own period'),drift=checked(dchanges,e*dd[:,3],GATE,'complete own drift'),capacitor_drift=checked(list(map(float,branch(dchanges))),list(map(float,branch(e*dd[:,3]))),2e-8,'complete own capacitor drift')))
    r.end();capacitors=[]
    for i,(cap,voltage,response) in enumerate(zip([*CAPS,(67,7,10e-6)],branch(base_drift),branch(dd[:,3]))):capacitors.append(dict(index=i,nodes=list(cap[:2]),capacitance_f=cap[2],baseline_drift_v=float(voltage),derivative_v_per_v=float(response)))
    j7=194;return dict(input_sha256={name:sha(ROOT/name),inputs['path']:sha(ROOT/inputs['path']),**inputs['private_used_sha256']},operators=operators,events=[{k:v for k,v in event.items() if k in ['alpha','observation','comparisons']} for event in events],epsilon=epsilon.tolist(),native_complete_gain=gain.tolist(),gain_independent_all_steps=False,period_s=period,period_derivative_s_per_v=float(dt[3]),j7_baseline_drift_v=float(base_drift[j7]),j7_derivative_v_per_v=float(dd[j7,3]),capacitors=capacitors,baseline_drift_observation=drift_observation,selected_endpoint_response=independent,own_histories=own,nonlinear_fd=finite,baseline_bit_steps=n,fixture_bit_steps=4,native_columns=COLS,selected_operator_points=15,selected_operator_directions=135,selected_operator_coordinates=54000,independent_nonlinear_rows=6000,perturbed_native_step_solves=4*n,own_event_observations=8,native_zero_control_steps=n,event_zero_controls=2,independent_roots=0,full_interval_fd_columns=[139],full_interval_direction139_admitted=True,independent_all_step_propagation=False,charge_root_basis_admitted=False,period_map_admitted=False,adaptive_derivative_admitted=False,continuous_event_derivative_admitted=False,physical_fidelity=False,real_time=False,new_audio=False)

def main():
    p=argparse.ArgumentParser();p.add_argument('--native',type=int,required=True);p.add_argument('--attempt',type=int,required=True);args=p.parse_args();name=f'evidence/voice_return_interval_native{args.native:02d}.json';out=f'evidence/voice_return_interval_reference{args.attempt:02d}.json';require(not (ROOT/out).exists(),'exclusive receipt');names={name,'evidence/voice_return_interval_inputs01.json','docs/VOZ_INTERVALO_RETORNO_PROTOCOLO.md','tools/check_return_interval.py'}
    for module in list(sys.modules.values()):
        f=getattr(module,'__file__',None)
        if f:
            path=Path(f).resolve()
            if path.is_relative_to(ROOT/'tools') and path.suffix=='.py':names.add(path.relative_to(ROOT).as_posix())
    before={n:sha(ROOT/n) for n in sorted(names)};report=dict(schema='rf-d/return-interval-reference/v1',passed=False,source_sha256=before);started=time.perf_counter();native=json.loads((ROOT/name).read_text())
    try:
        with localcontext() as ctx:ctx.prec=100;report.update(check(native))
        require(time.perf_counter()-started<=300,'reference total budget');report['passed']=True
    except Exception:
        report['failure']=traceback.format_exc();report['failed_source_text']=(ROOT/'tools/check_return_interval.py').read_text()
        try:
            with localcontext() as ctx:ctx.prec=100;check(native)
            report['replay']='unexpected pass'
        except Exception:report['replay']=traceback.format_exc()
    report['source_sha256_after']={n:sha(ROOT/n) for n in sorted(names)};require(before==report['source_sha256_after'],'unchanged reference sources');report['wall_s']=time.perf_counter()-started;write(out,report);print('RETURN_REFERENCE_PASSED',report['passed'],report.get('failure',''),flush=True)
if __name__=='__main__':main()
