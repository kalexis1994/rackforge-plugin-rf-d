"""Independent conditioned basis, four propagated operators and own roots."""
import argparse,json,sys,time,traceback
from decimal import localcontext
from pathlib import Path
import numpy as np
from prepare_vco1_portable import ROOT,sha,write
from check_history_propagation import Reader,decoded,bits
from check_joint_reference import D,evaluate
from check_joint_charge_seed import incidence,physical_dc,root_check
from check_joint_charge_response import response_error
from check_history_tangent import mass,stage_jacobian,ratio
from joint_cycles_analysis import require,TICK

def root(r):
    raw=r.floats(436);state=decoded(raw[:400]);current=[D(raw[400+2*k])+D(raw[401+2*k]) for k in range(18)];m=r.floats(5);require(1<=m[0]<=64 and 0<=m[1]<=64*24 and 0<=m[2]<=1 and 0<=m[3]<=1,'native root gates');return raw,state,current,m

def check(native):
    require(native['passed'],'passed native');inputs=json.loads((ROOT/'evidence/voice_charge_basis_inputs01.json').read_text());inp=Reader(ROOT/inputs['path']);require(inp.bytes(8)==b'RFJCBIN1','input header');name=next(o['path'] for o in native['outputs'] if o['path'].endswith('/basis.bin'));r=Reader(ROOT/name);require(r.bytes(8)==b'RFJCBO01','output header');e,caps=incidence();targets=[]
    for line in (ROOT/'evidence/voice_joint_charge_response_targets01.txt').read_text().splitlines():
        values=list(map(float,line.split()));require(len(values)==36,'target codec');targets.append([D(values[2*k])+D(values[2*k+1]) for k in range(18)])
    require(len(targets)==2,'two targets');reports=[];root_checks=[];gate=np.array([1e-11 if 98<=k<133 else 1e-8 for k in range(200)]);deadline=time.perf_counter()+300
    for id in range(2):
        require(r.integer('I')==id,'memory order');expected=inp.floats(436);fixtures=[(inp.integer('Q'),inp.integer('I'),inp.floats(2000).reshape(5,400)) for _ in range(2)];raw,state,current,m=root(r);require(bits(raw,expected),'base root/current bits');root_checks.append(dict(id=id,column=None,size_v=0,sign=0,**root_check(state,current,targets[id],m[4],e,caps)))
        basis=r.floats(3924).reshape(218,18);_,j=physical_dc(state);j[43,:]=0;j[43,43]=1;aug=np.block([[j,e],[e.T,np.zeros((18,18))]]);independent=np.linalg.solve(aug,np.vstack([np.zeros((200,18)),np.eye(18)]));basis_check=response_error(basis,independent);constraint_error=float(np.max(np.abs(e.T@basis[:200]-np.eye(18))));require(constraint_error<=1e-9,'incidence basis identity');require(np.max(np.abs(.000125*basis[43]))<=1e-18 and np.max(np.abs(.000125*independent[43]))<=1e-18,'held phase response')
        naive=np.zeros(200);naive[139]=1.;diff=.000125*(basis[:200,5]-naive);voltage=[k for k in range(200) if not 98<=k<133];positive=float(np.max(np.abs(diff[voltage])));require(positive>1e-8,'C27 node injection positive control')
        u=independent[:200];stages=[];stage_reports=[];last=0
        for step,(ticks,half,fixture) in enumerate(fixtures):
            require(time.perf_counter()<deadline,'reference budget');require(r.integer('Q')==ticks and r.integer('I')==half and ticks-last==half and [ticks,half]==inputs['profiles'][id]['clocks'][step],'exact calendar');last=ticks;states=r.floats(2000).reshape(5,400);s=r.floats(7200).reshape(400,18);require(bits(states,fixture),'selected dynamic fixture bits')
            if step==0:require(bits(states[0],raw[:400]),'release from actual root')
            else:require(bits(states[0],stages[-1][0][4]),'own base continuity')
            case=(0,half*TICK,*[decoded(a) for a in states]);old_mass=mass(case[2],case[1]);oracle=np.linalg.solve(stage_jacobian(case),np.vstack([2*(old_mass@u),-2*(old_mass@u)]));u=oracle[200:];comparisons=[]
            for k in range(18):
                comparison=ratio(.000125*s[:,k],.000125*oracle[:,k],np.tile(gate,2),1e-4);require(comparison['max_ratio']<=1,'independent propagated basis');comparisons.append(comparison)
            stages.append((states,s));stage_reports.append(dict(step=step,h_s=case[1],comparisons=comparisons,nonlinear_candidate=evaluate(case)))
        own={}
        for k in range(18):
            for size in [.000125,.0000625]:
                for sign in [-1.,1.]:
                    require(time.perf_counter()<deadline,'reference budget');require(bits(r.floats(3),np.array([k,size,sign])),'own history ordering');q,qs,qi,qm=root(r);target=targets[id].copy();target[k]+=D(sign)*D(size);root_checks.append(dict(id=id,column=k,size_v=size,sign=sign,**root_check(qs,qi,target,qm[4],e,caps)));ends=[r.floats(400) for _ in range(2)];own[k,size,sign]=(qs+qi,[decoded(a) for a in ends])
            print('BASIS_REFERENCE',id,k,flush=True)
        root_fd=[];prefix_fd=[]
        for size in [.000125,.0000625]:
            columns=[]
            for k in range(18):
                minus,plus=[own[k,size,sign] for sign in [-1.,1.]];columns.append([float((b-a)/(2*D(size))) for a,b in zip(minus[0],plus[0])]);comparisons=[]
                for step in range(2):
                    change=np.array([float((b-a)/2) for a,b in zip(minus[1][step],plus[1][step])]);comparison=ratio(change,size*stages[step][1][200:,k],gate,1e-4);require(comparison['max_ratio']<=1,'complete own conditioned prefix');comparisons.append(comparison)
                prefix_fd.append(dict(column=k,size_v=size,steps=comparisons))
            root_fd.append(dict(size_v=size,**response_error(np.column_stack(columns),basis)))
        ledger=[dict(index=k,capacitance_f=c,target_coordinate_v=str(targets[id][k]),delta_charge_per_delta_target_c_per_v=c,state_charge_response_unit='V/C or A/C by row',retention_charge_response_unit='A/C',conversion='divide column by capacitance') for k,(_,_,c) in enumerate(caps)]
        reports.append(dict(id=id,base_response=basis_check,incidence_identity_error=constraint_error,C27_injection_difference_max_v=positive,C27_bus_response_v_per_v=float(basis[12,5]),C27_j7_response_v_per_v=float(basis[194,5]),stage_reports=stage_reports,root_fd=root_fd,prefix_fd=prefix_fd,ledger=ledger))
    inp.end();r.end();return dict(records=reports,root_checks=root_checks,input_sha256={name:sha(ROOT/name),inputs['path']:sha(ROOT/inputs['path']),**inputs['private_used_sha256']},base_bit_roots=2,base_bit_steps=4,basis_columns=36,basis_entries=7848,augmented_root_count=146,augmented_rows=31828,independent_dynamic_rows=1600,independent_step_directions=72,independent_step_coordinates=28800,batch9_bit_coordinates=28800,zero_history_controls=4,injection_positive_controls=2,perturbed_native_steps=288,own_prefix_histories=144,charge_incidence_rank=18,corrected_initial_basis_admitted=True,two_step_conditioned_release_admitted=True,independent_all_step_prefix=True,independent_roots=0,full_return_from_conditioned_root_admitted=False,period_map_admitted=False,steady_periodicity_admitted=False,adaptive_derivative_admitted=False,new_audio=False,physical_fidelity=False,real_time=False)

def main():
    p=argparse.ArgumentParser();p.add_argument('--native',type=int,required=True);p.add_argument('--attempt',type=int,required=True);a=p.parse_args();name=f'evidence/voice_charge_basis_native{a.native:02d}.json';out=f'evidence/voice_charge_basis_reference{a.attempt:02d}.json';require(not (ROOT/out).exists(),'exclusive reference');names={name,'evidence/voice_charge_basis_inputs01.json','evidence/voice_joint_charge_response_targets01.txt','docs/VOZ_BASE_CARGAS_CORREGIDAS_PROTOCOLO.md','tools/check_charge_basis.py'}
    for module in list(sys.modules.values()):
        f=getattr(module,'__file__',None)
        if f:
            path=Path(f).resolve()
            if path.is_relative_to(ROOT/'tools') and path.suffix=='.py':names.add(path.relative_to(ROOT).as_posix())
    before={n:sha(ROOT/n) for n in sorted(names)};report=dict(schema='rf-d/charge-basis-reference/v1',passed=False,source_sha256=before);started=time.perf_counter();native=json.loads((ROOT/name).read_text())
    try:
        with localcontext() as ctx:ctx.prec=100;report.update(check(native))
        require(time.perf_counter()-started<=300,'reference total budget');report['passed']=True
    except Exception:
        report['failure']=traceback.format_exc();report['failed_source_text']=(ROOT/'tools/check_charge_basis.py').read_text()
        try:
            with localcontext() as ctx:ctx.prec=100;check(native)
            report['replay']='unexpected pass'
        except Exception:report['replay']=traceback.format_exc()
    report['source_sha256_after']={n:sha(ROOT/n) for n in sorted(names)};require(before==report['source_sha256_after'],'unchanged sources');report['wall_s']=time.perf_counter()-started;write(out,report);print('BASIS_REFERENCE_PASSED',report['passed'],report.get('failure',''),flush=True)
if __name__=='__main__':main()
