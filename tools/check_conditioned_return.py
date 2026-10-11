"""Conditioned root domain and complete own C27 histories from time zero."""
import argparse,json,sys,time,traceback
from decimal import Decimal,localcontext
from pathlib import Path
import numpy as np
from prepare_vco1_portable import ROOT,sha,write
from check_history_propagation import Reader,decoded,bits
from check_history_tangent import mass,stage_jacobian,ratio
from check_history_event import observer
from check_charge_basis import root
from check_joint_charge_seed import incidence,physical_dc,root_check
from check_joint_charge_response import response_error
from prepare_conditioned_return import POINTS,FIXTURES
COLS=list(range(18))
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

def projection(a,b,sa,sb,h):
    alpha,z,ra,rb,aa,bb=observer(a,b);dalpha=[];dz=np.empty((200,18));unprojected=np.empty((200,18))
    for c in range(18):
        v=-((1-alpha)*D(sa[43,c])+alpha*D(sb[43,c]))/(rb-ra);dalpha.append(v)
        for k in range(200):
            weighted=(1-alpha)*D(sa[k,c])+alpha*D(sb[k,c]);unprojected[k,c]=float(weighted);dz[k,c]=float(weighted+(bb[k]-aa[k])*v)
    return alpha,z,np.array(list(map(float,dalpha))),np.array([float(D(h)*v) for v in dalpha]),dz,unprojected

def read_event(r,a,b,h,sa,sb,epsilon):
    alpha=float(r.floats(1)[0]);state=r.floats(400);da=r.floats(18);dt=r.floats(18);dz=r.floats(3600).reshape(200,18)
    oa,oz,oda,odt,odz,_=projection(a,b,sa,sb,h)
    require(abs(alpha-float(oa))<=2e-15,'base event alpha')
    base=checked(list(map(float,decoded(state))),list(map(float,oz)),BASE_GATE,'base event state',0)
    require(abs(float(decoded(state)[43])+2)<=1e-13,'base event section')
    comparisons=[]
    for c in range(18):
        e=epsilon[c];comparisons.append(dict(column=COLS[c],state=checked(e*dz[:,c],e*odz[:,c],GATE,'independent projected state'),time=checked([e*dt[c]],[e*odt[c]],1e-17,'independent event time'),alpha=checked([e*da[c]],[e*oda[c]],1e-17/h,'independent alpha')))
        require(abs(e*dz[43,c])<=1e-18 and abs(e*odz[43,c])<=1e-18,'projected ramp tangent')
    return dict(alpha=alpha,state=state,dt=dt,dz=dz,oracle_dt=odt,oracle_dz=odz,decimal_z=oz,observation=base,comparisons=comparisons)

def check(native):
    require(native['passed'],'passed native');inputs=json.loads((ROOT/'evidence/voice_conditioned_return_inputs01.json').read_text());inp=Reader(ROOT/inputs['path'])
    require(inp.bytes(8)==b'RFJCRIN1','input codec');n=inp.integer('I');initial=inp.floats(436);initial_basis=inp.floats(3924).reshape(218,18);fixtures=[inp.floats(2000).reshape(5,400) for _ in range(6)];prefix=[inp.floats(7200).reshape(400,18) for _ in range(2)];count=inp.integer('I');points=[inp.integer('I') for _ in range(count)];start=0;require(n==42544 and points==POINTS==inputs['points'] and count==20,'input metadata')
    schedule=[(inp.integer('Q'),inp.integer('I'),inp.floats(7)) for _ in range(n)];inp.end()
    name=next(o['path'] for o in native['outputs'] if o['path'].endswith('/return.bin'));r=Reader(ROOT/name);require(r.bytes(8)==b'RFJCRO01' and r.integer('I')==n,'output metadata')
    raw,state,current,metrics=root(r);basis=r.floats(3924).reshape(218,18);require(bits(raw,initial) and bits(basis,initial_basis),'base root and basis bits');inc,caps=incidence()
    values=list(map(float,(ROOT/'evidence/voice_joint_charge_response_targets01.txt').read_text().splitlines()[0].split()));targets=[D(values[2*k])+D(values[2*k+1]) for k in range(18)]
    roots=[root_check(state,current,targets,metrics[4],inc,caps)];_,j=physical_dc(state);j[43,:]=0;j[43,43]=1;aug=np.block([[j,inc],[inc.T,np.zeros((18,18))]]);independent_basis=np.linalg.solve(aug,np.vstack([np.zeros((200,18)),np.eye(18)]));basis_comparison=response_error(basis,independent_basis);require(np.max(np.abs(inc.T@basis[:200]-np.eye(18)))<=1e-9,'incidence identity');independent_u=independent_basis[:200]
    old_trace_name='references-local/joint-corrected-cycles01/0-65536/trace.bin';saved_trace=trace(ROOT/old_trace_name)[:n];require(len(saved_trace)==n,'complete saved trace');samples={};last=start;deadline=time.perf_counter()+300
    for step,(ticks,half,obs) in enumerate(schedule):
        require(time.perf_counter()<deadline,'reference budget');require(r.integer('I')==step and r.integer('Q')==ticks and r.integer('I')==half and ticks-last==half,'exact complete calendar');last=ticks
        require(bits(r.floats(7),obs) and int(saved_trace[step]['ticks'])==ticks and int(saved_trace[step]['half_ticks'])==half and bits(obs,np.array([saved_trace[step][key] for key,_ in OBS])),'full trace observation bits');flag=r.bytes(1)[0];require(flag==int(step in points),'preselected sample flag')
        if flag:
            states=r.floats(2000).reshape(5,400);u=r.floats(3600).reshape(200,18);s=r.floats(7200).reshape(400,18);samples[step]=(states,u,s)
            require(bits(obs,np.array([states[4,k]+states[4,200+k] for _,k in OBS])),'sample endpoint observations')
    require(last==inputs['end_ticks'] and sorted(samples)==points,'complete interval coverage')
    gain=r.floats(18);epsilon=r.floats(18);base=np.full(18,1e-5);target=np.tile([1e-8 if 98<=k<133 else 1e-5 for k in range(200)],2)
    require((gain>=1).all() and (epsilon>0).all() and bits(epsilon,base/gain),'native complete gain epsilon');require(bits(samples[0][0][0],initial[:400]) and bits(samples[0][1],basis[:200]),'initial state and basis')
    require(np.max(np.abs(epsilon*basis[43]))<=1e-18 and np.max(np.abs(epsilon*independent_basis[43]))<=1e-18,'initial held phase response')
    for step,fixture in zip(FIXTURES,fixtures):require(bits(samples[step][0],fixture),'full fixture bits')
    require(all(bits(samples[k][2],prefix[k]) for k in range(2)),'inherited two prefix sensitivities');require((np.max(base*np.abs(basis[:200])/target[:200,None],axis=0)<=gain*(1+1e-15)).all(),'initial gain bounds')
    operators=[];oracles={}
    for step in points:
        require(time.perf_counter()<deadline,'reference budget');states,u,s=samples[step];h=schedule[step][1]*TICK
        if step-1 in samples:require(bits(states[0],samples[step-1][0][4]) and bits(u,samples[step-1][2][200:]),'adjacent saved recurrence bits')
        sample_gain=np.max(base*np.abs(s)/target[:,None],axis=0);require((sample_gain<=gain*(1+1e-15)).all(),'all-step native gain bounds selected operators')
        case=(0,h,*[decoded(a) for a in states]);m=mass(case[2],h);oracle=np.linalg.solve(stage_jacobian(case),np.vstack([2*(m@(independent_u if step<2 else u)),-2*(m@(independent_u if step<2 else u))]));oracles[step]=oracle
        if step<2:independent_u=oracle[200:]
        comparisons=[checked(epsilon[c]*s[:,c],epsilon[c]*oracle[:,c],np.tile(GATE,2),'selected independent operator') for c in range(18)]
        operators.append(dict(step=step,h_s=h,comparisons=comparisons,nonlinear_candidate=evaluate(case)));print('RETURN_REFERENCE_OPERATOR',step,flush=True)
    h1=schedule[20189][1]*TICK;h2=schedule[-1][1]*TICK;events=[]
    for a,b,h in [(20188,20189,h1),(n-2,n-1,h2)]:events.append(read_event(r,samples[a][0][4],samples[b][0][4],h,oracles[a][200:],oracles[b][200:],epsilon))
    first,second=events;fixed=D((schedule[-2][0]-schedule[20188][0])*TICK);period=float(r.floats(1)[0]);drift=r.floats(200);dt=r.floats(18);dd=r.floats(3600).reshape(200,18)
    require(abs(D(period)-(fixed+D(h2)*D(second['alpha'])-D(h1)*D(first['alpha'])))<=D(1e-17),'base period reconstruction')
    base_drift=[b-a for a,b in zip(decoded(first['state']),decoded(second['state']))];drift_observation=checked(drift,list(map(float,base_drift)),BASE_GATE,'compensated baseline drift',0);independent=[]
    for c in range(18):independent.append(dict(column=COLS[c],period=checked([epsilon[c]*dt[c]],[epsilon[c]*(second['oracle_dt'][c]-first['oracle_dt'][c])],1e-17,'independent selected endpoint period'),drift=checked(epsilon[c]*dd[:,c],epsilon[c]*(second['oracle_dz'][:,c]-first['oracle_dz'][:,c]),GATE,'independent selected endpoint drift')))
    own=[];finite=[];root_fd=[]
    for scale in [1.,.5]:
        signs=[]
        for sign in [1.,-1.]:
            size=scale*epsilon[5];require(bits(r.floats(3),np.array([scale,sign,size])),'own history order');own_raw,own_state,own_current,own_metrics=root(r);own_target=targets.copy();own_target[5]+=D(sign)*D(size);roots.append(root_check(own_state,own_current,own_target,own_metrics[4],inc,caps));ends=[r.floats(400) for _ in range(4)];zs=[];alphas=[];observations=[]
            for a,b in [(0,1),(2,3)]:
                alpha=float(r.floats(1)[0]);z=r.floats(400);oa,oz,*_=observer(ends[a],ends[b]);require(abs(alpha-float(oa))<=2e-15,'own event alpha');observation=checked(list(map(float,decoded(z))),list(map(float,oz)),BASE_GATE,'own event observation',0);require(abs(float(decoded(z)[43])+2)<=1e-13,'own event section');alphas.append(alpha);zs.append(decoded(z));observations.append(observation)
            own_period=float(r.floats(1)[0]);require(abs(D(own_period)-(fixed+D(h2)*D(alphas[1])-D(h1)*D(alphas[0])))<=D(1e-17),'own period reconstruction');signs.append((alphas,zs,own_state+own_current));own.append(dict(scale=scale,sign=sign,alphas=alphas,period_s=own_period,observations=observations))
        changes=[np.array([float((a-b)/2) for a,b in zip(signs[0][1][j],signs[1][1][j])]) for j in range(2)];dchanges=np.array([float(((a-b)-(c-d))/2) for a,b,c,d in zip(signs[0][1][1],signs[0][1][0],signs[1][1][1],signs[1][1][0])]);tchange=float((D(h2)*(D(signs[0][0][1])-D(signs[1][0][1]))-D(h1)*(D(signs[0][0][0])-D(signs[1][0][0])))/2);e=scale*epsilon[5]
        own_basis=np.array([float((a-b)/(2*D(e))) for a,b in zip(signs[0][2],signs[1][2])])[:,None];root_fd.append(dict(scale=scale,**response_error(own_basis,basis[:,5:6])))
        time_changes=[float(D(h)*(D(signs[0][0][j])-D(signs[1][0][j]))/2) for j,h in enumerate([h1,h2])]
        finite.append(dict(scale=scale,first_event=checked(changes[0],e*first['dz'][:,5],GATE,'full own first event'),second_event=checked(changes[1],e*second['dz'][:,5],GATE,'full own second event'),first_time=checked([time_changes[0]],[e*first['dt'][5]],1e-17,'full own first time'),second_time=checked([time_changes[1]],[e*second['dt'][5]],1e-17,'full own second time'),period=checked([tchange],[e*dt[5]],1e-17,'complete own period'),drift=checked(dchanges,e*dd[:,5],GATE,'complete own drift'),capacitor_drift=checked(list(map(float,branch(dchanges))),list(map(float,branch(e*dd[:,5]))),2e-8,'complete own capacitor drift')))
        finite[-1]['effect_ledger']=dict(j7_change_v=float(dchanges[194]),predicted_j7_change_v=float(e*dd[194,5]),j7_predicted_to_absolute_floor=float(abs(e*dd[194,5])/GATE[194]),period_change_s=tchange,predicted_period_change_s=float(e*dt[5]),period_predicted_to_absolute_floor=float(abs(e*dt[5])/1e-17),capacitor_changes_v=list(map(float,branch(dchanges))),predicted_capacitor_changes_v=list(map(float,branch(e*dd[:,5]))),capacitor_predicted_to_absolute_floor=[abs(float(v))/2e-8 for v in branch(e*dd[:,5])])
    r.end();capacitors=[]
    for i,(cap,voltage,response) in enumerate(zip([*CAPS,(67,7,10e-6)],branch(base_drift),branch(dd[:,5]))):capacitors.append(dict(index=i,nodes=list(cap[:2]),capacitance_f=cap[2],baseline_drift_v=float(voltage),derivative_v_per_v=float(response)))
    j7=194;return dict(native_capacitor_drift_derivative_v_per_target_v=np.column_stack([branch(dd[:,c]) for c in range(18)]).tolist(),native_period_derivative_s_per_target_v=dt.tolist(),native_event_derivative_s_per_target_v=[first['dt'].tolist(),second['dt'].tolist()],all_target_fd_admitted=False,input_sha256={name:sha(ROOT/name),inputs['path']:sha(ROOT/inputs['path']),**inputs['private_used_sha256']},operators=operators,events=[{k:v for k,v in event.items() if k in ['alpha','observation','comparisons']} for event in events],epsilon=epsilon.tolist(),native_complete_gain=gain.tolist(),gain_independent_all_steps=False,period_s=period,period_derivative_s_per_target_v=float(dt[5]),first_reset_derivative_s_per_target_v=float(first['dt'][5]),second_reset_derivative_s_per_target_v=float(second['dt'][5]),j7_baseline_drift_v=float(base_drift[j7]),j7_derivative_v_per_target_v=float(dd[j7,5]),capacitors=capacitors,baseline_drift_observation=drift_observation,selected_endpoint_response=independent,own_histories=own,nonlinear_fd=finite,root_checks=roots,root_fd=root_fd,basis_comparison=basis_comparison,baseline_bit_steps=n,fixture_bit_steps=6,prefix_sensitivity_bit_coordinates=14400,base_bit_roots=1,basis_columns=18,basis_entries=3924,augmented_root_count=5,augmented_rows=1090,native_columns=COLS,selected_operator_points=20,selected_operator_directions=360,selected_operator_coordinates=144000,independent_nonlinear_rows=8000,perturbed_native_step_solves=4*n,own_event_observations=8,native_zero_control_steps=20,event_zero_controls=2,batch9_event_bit_coordinates=7272,independent_roots=0,full_interval_fd_target_columns=[5],full_return_from_conditioned_root_admitted=True,independent_all_step_propagation=False,independent_two_step_prefix=True,charge_root_basis_admitted=True,period_map_admitted=False,steady_periodicity_admitted=False,adaptive_derivative_admitted=False,continuous_event_derivative_admitted=False,physical_fidelity=False,real_time=False,new_audio=False)


def main():
    p=argparse.ArgumentParser();p.add_argument('--native',type=int,required=True);p.add_argument('--attempt',type=int,required=True);args=p.parse_args();name=f'evidence/voice_conditioned_return_native{args.native:02d}.json';out=f'evidence/voice_conditioned_return_reference{args.attempt:02d}.json';require(not (ROOT/out).exists(),'exclusive receipt');names={name,'evidence/voice_conditioned_return_inputs01.json','docs/VOZ_RETORNO_CONDICIONADO_PROTOCOLO.md','tools/check_conditioned_return.py','evidence/voice_joint_charge_response_targets01.txt'}
    for module in list(sys.modules.values()):
        f=getattr(module,'__file__',None)
        if f:
            path=Path(f).resolve()
            if path.is_relative_to(ROOT/'tools') and path.suffix=='.py':names.add(path.relative_to(ROOT).as_posix())
    before={n:sha(ROOT/n) for n in sorted(names)};report=dict(schema='rf-d/conditioned-return-reference/v1',passed=False,source_sha256=before);started=time.perf_counter();native=json.loads((ROOT/name).read_text())
    try:
        with localcontext() as ctx:ctx.prec=100;report.update(check(native))
        require(time.perf_counter()-started<=300,'reference total budget');report['passed']=True
    except Exception:
        report['failure']=traceback.format_exc();report['failed_source_text']=(ROOT/'tools/check_conditioned_return.py').read_text()
        try:
            with localcontext() as ctx:ctx.prec=100;check(native)
            report['replay']='unexpected pass'
        except Exception:report['replay']=traceback.format_exc()
    report['source_sha256_after']={n:sha(ROOT/n) for n in sorted(names)};require(before==report['source_sha256_after'],'unchanged reference sources');report['wall_s']=time.perf_counter()-started;write(out,report);print('RETURN_REFERENCE_PASSED',report['passed'],report.get('failure',''),flush=True)
if __name__=='__main__':main()
