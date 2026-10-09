"""Contrast augmented sensitivities and gate a static memory predictor."""
import argparse,json,struct,sys,time,traceback
from pathlib import Path
from decimal import Decimal,localcontext
import numpy as np
from prepare_vco1_portable import ROOT,sha
from check_joint_reference import D,decode
from check_joint_charge_seed import incidence,physical_dc,root_check
from joint_cycles_analysis import require

def targets():
    rows=[]
    for line in (ROOT/'evidence/voice_joint_charge_seed_targets01.txt').read_text().splitlines():
        raw=list(map(float,line.split()));require(len(raw)==36,'target codec');rows.append([D(raw[k])+D(raw[k+1]) for k in range(0,36,2)])
    require(len(rows)==2,'two targets');return rows

def bank(native):
    lines=native['commands'][-1]['stdout'].splitlines();roots=[];columns={}
    for k,line in enumerate(lines):
        row=line.split(',')
        if row[0] in ['RESPONSE_BASE','RESPONSE_PERTURB']:
            label,id,index,h,iterations,trials,res,corr,forcing=row
            raw=list(map(float,lines[k+2].split(',')[1:]));require(len(raw)==36,'retention currents codec')
            roots.append(dict(label=label,id=int(id),index=int(index),h=float(h),iterations=int(iterations),trials=int(trials),native_residual=float(res),native_correction=float(corr),forcing=float(forcing),state=decode(lines[k+1]),current=[D(raw[j])+D(raw[j+1]) for j in range(0,36,2)],raw_state=lines[k+1],raw_current=lines[k+2]))
        elif row[0]=='RESPONSE_COLUMN':
            id,index=map(int,row[1:3]);require((id,index) not in columns and len(row)==221,'complete unique response column');columns[id,index]=np.array(list(map(float,row[3:])))
    require(len(roots)==146 and set(columns)=={(i,k) for i in range(2) for k in range(18)},'native coverage')
    require({(r['id'],r['index'],r['h']) for r in roots if r['label']=='RESPONSE_PERTURB'}=={(i,k,h) for i in range(2) for k in range(18) for h in [-.001,.001,-.0005,.0005]},'both central perturbations')
    return roots,columns

def response_error(observed,expected):
    floors=np.array([1e-10 if 98<=k<133 or k>=200 else 1e-6 for k in range(218)])[:,None]
    ratio=np.abs(observed-expected)/(floors+3e-4*np.abs(expected));worst=np.unravel_index(np.argmax(ratio),ratio.shape)
    require(float(ratio[worst])<=1,'response comparison '+str((float(ratio[worst]),worst)))
    return dict(max_gate_ratio=float(ratio[worst]),worst_row=int(worst[0]),worst_column=int(worst[1]))

def mean_drift(cycle):
    events=cycle['events'];period=Decimal(events[1]['interpolated_time_s'])-Decimal(events[0]['interpolated_time_s']);require(period>0,'phase period')
    return [D(c['capacitance_f'])*Decimal(c['interpolated_phase_voltage_change_v'])/period for c in cycle['capacitor_changes']]

def check(native):
    require(native['passed'],'passed native');e,caps=incidence();ts=targets();roots,columns=bank(native);checks=[];base={}
    old=json.loads((ROOT/'evidence/voice_joint_charge_seed_native02.json').read_text());lines=old['commands'][-1]['stdout'].splitlines();old_raw={}
    for k,line in enumerate(lines):
        if line.startswith('CHARGE_ROOT,'):
            id,guess=map(int,line.split(',')[1:3])
            if guess==0:old_raw[id]=(lines[k+1],lines[k+2])
    for r in roots:
        require(r['native_residual']<=1 and r['native_correction']<=1 and r['iterations']<=64 and r['trials']<=64*24,'native root gates')
        target=ts[r['id']].copy()
        if r['label']=='RESPONSE_PERTURB':target[r['index']]+=D(r['h'])
        else:
            require((r['raw_state'],r['raw_current'])==old_raw[r['id']],'base root and retention currents byte reproduction');require(r['id'] not in base,'unique base');base[r['id']]=r
        result=root_check(r['state'],r['current'],target,r['forcing'],e,caps)
        checks.append(dict(id=r['id'],index=r['index'],perturbation_v=r['h'],kind=r['label'],**result))
    require(set(base)=={0,1},'two base roots');records=[];cycle_data=json.loads((ROOT/'evidence/voice_joint_seed_cycles_reference01.json').read_text());require(cycle_data['passed'],'admitted cycle observations')
    for id in range(2):
        state=base[id]['state'];_,j=physical_dc(state);j[43,:]=0;j[43,43]=1
        a=np.block([[j,e],[e.T,np.zeros((18,18))]]);rhs=np.vstack([np.zeros((200,18)),np.eye(18)])
        independent=np.linalg.solve(a,rhs);native_matrix=np.column_stack([columns[id,k] for k in range(18)]);linear=response_error(native_matrix,independent)
        finite=[];central=[]
        for h in [.001,.0005]:
            vectors=[]
            for k in range(18):
                pair=[next(r for r in roots if r['id']==id and r['label']=='RESPONSE_PERTURB' and r['index']==k and r['h']==sign*h) for sign in [-1,1]]
                delta=[float((b-a)/(D(2)*D(h))) for a,b in zip(pair[0]['state']+pair[0]['current'],pair[1]['state']+pair[1]['current'])];vectors.append(delta)
            fd=np.column_stack(vectors);central.append(fd);finite.append(dict(half_perturbation_v=h,**response_error(fd,native_matrix)))
        s=native_matrix[200:];u,singular,vh=np.linalg.svd(s);rank=int(np.count_nonzero(singular>singular[0]*1e-10));condition=float(singular[0]/singular[-1]) if singular[-1]>0 else None
        coarse,fine=[next(c for c in cycle_data['cycles'] if c['seed_id']==id and c['maximum_half_ticks']==m) for m in [65536,32768]];m0,m1=mean_drift(coarse),mean_drift(fine)
        difference=max(abs(a-b) for a,b in zip(m0,m1));require(difference<=D(1e-10),'18 charge drift refinement')
        vector=np.array(list(map(float,m1)));prediction=dict(admitted=False,reason='rank or condition exceeds direct inversion gate')
        if rank==18 and condition is not None and condition<=1e10:
            delta=np.linalg.solve(s,-vector);error=float(np.max(np.abs(s@delta+vector)));require(error<=1e-12,'static predictor residual')
            maximum=float(np.max(np.abs(delta)));alpha=min(1.,.1/maximum) if maximum else 1.;step=alpha*delta;new_targets=[];packed=[]
            for target,change in zip(ts[id],step):
                value=target+D(float(change));high=float(value);low=float(value-D(high));new_targets.append(str(value));packed.extend([high,low])
            prediction=dict(admitted=True,unscaled_delta_target_v=delta.tolist(),alpha=alpha,applied_delta_target_v=step.tolist(),linear_predicted_drift_current_a=(vector+s@step).tolist(),solve_residual_a=error,target_voltages_decimal=new_targets,packed_target_pairs=packed,not_a_periodic_root=True,nonlinear_closure_pending=True,own_cycles_pending=True)
        records.append(dict(id=id,native_response=native_matrix.tolist(),independent_response_gate=linear,central_response_gates=finite,central_refinement_max_voltage_ratio_v_per_v=float(np.max(abs(central[1]-central[0]))),retention_response_a_per_v=s.tolist(),singular_values_a_per_v=singular.tolist(),relative_rank_cutoff=1e-10,rank=rank,condition=condition,smallest_right_singular_vector=vh[-1].tolist(),smallest_left_singular_vector=u[:,-1].tolist(),measured_drift_projection_on_smallest_left_a=float(u[:,-1]@vector),coarse_drift_current_a=list(map(str,m0)),fine_drift_current_a=list(map(str,m1)),drift_refinement_max_a=str(difference),drift_is_phase_charge_observation_not_radau_quadrature=True,predictor=prediction))
    return dict(root_checks=checks,augmented_rows=sum(c['rows'] for c in checks),base_bit_reproductions=2,response_columns=36,response_entries=218*36,records=records,charge_incidence_rank=18,held_phase_response_admitted=True,not_a_period_map_jacobian=True,new_trajectories=0,independent_root_search=False,physical_cards_changed=False,steady_periodicity_admitted=False,new_audio=False,new_spice_processes=0)

def main():
    p=argparse.ArgumentParser();p.add_argument('--attempt',type=int,required=True);a=p.parse_args();out=ROOT/f'evidence/voice_joint_charge_response_reference{a.attempt:02d}.json';require(not out.exists(),'exclusive receipt')
    n='evidence/voice_joint_charge_response_native01.json';native=json.loads((ROOT/n).read_text());names={n,'tools/check_joint_charge_response.py','evidence/voice_joint_seed_cycles_reference01.json','evidence/voice_joint_charge_seed_native02.json','evidence/voice_joint_charge_seed_targets01.txt','docs/VOZ_CARGAS_RESPUESTA_PROTOCOLO.md'}
    for module in list(sys.modules.values()):
        f=getattr(module,'__file__',None)
        if f:
            path=Path(f).resolve()
            if path.is_relative_to(ROOT/'tools') and path.suffix=='.py':names.add(path.relative_to(ROOT).as_posix())
    before={n:sha(ROOT/n) for n in sorted(names)};r=dict(schema='rf-d/joint-charge-response-reference/v1',passed=False,source_sha256=before);started=time.perf_counter()
    try:
        with localcontext() as ctx:ctx.prec=100;r.update(check(native))
        r['passed']=True
    except Exception:
        r['failure']=traceback.format_exc();r['failed_source_text']=(ROOT/'tools/check_joint_charge_response.py').read_text()
        try:
            with localcontext() as ctx:ctx.prec=100;check(native)
            r['replay']='unexpected pass'
        except Exception:r['replay']=traceback.format_exc()
    r['wall_s']=time.perf_counter()-started;r['source_sha256_after']={n:sha(ROOT/n) for n in sorted(names)};require(before==r['source_sha256_after'],'unchanged checker sources');out.write_text(json.dumps(r,indent=2,allow_nan=False)+'\n',encoding='utf8',newline='\n');print('CHARGE_RESPONSE_REFERENCE',r['passed'],r.get('failure',''),flush=True)

if __name__=='__main__':main()
