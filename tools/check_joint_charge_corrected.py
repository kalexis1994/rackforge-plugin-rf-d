"""Independent augmented residuals, fixed charges and short free releases."""
import argparse,json,sys,time,traceback
from pathlib import Path
from decimal import Decimal,localcontext
import numpy as np
from prepare_vco1_portable import ROOT,sha
from check_joint_reference import vi,ci,D,decode,CONFIG,evaluate
from chain_charge_reference import problem,CAPS,mass
from vco1_increment_circuit import reference_decimal
from joint_cycles_analysis import require

def incidence():
    e=np.zeros((200,18));caps=[]
    for k,(a,b,c) in enumerate([*CAPS,(67,7,10e-6)]):
        b=b if isinstance(b,int) else 66 if b=='BUS' else None
        e[ci(a),k]=1
        if b is not None:e[ci(b),k]=-1
        caps.append((ci(a),ci(b) if b is not None else None,c))
    require(np.linalg.matrix_rank(e)==18,'independent incidence rank')
    local=e[[ci(k) for k in range(68)],:]
    require(np.max(abs(local@np.diag([c for a,b,c in caps])@local.T-mass()))<=1e-15,'physical incidence reproduces mass')
    return e,caps

def physical_dc(state):
    v=[Decimal(0) if vi(k) is None else state[vi(k)] for k in range(134)]
    f,j,_=reference_decimal(v,v,None,CONFIG);dc,gradient,_=problem(200,0,[0.,.2,-.3,.1,.4])
    high=np.array([float(state[ci(k)]) for k in range(68)]);low=np.array([float(state[ci(k)]-D(high[k])) for k in range(68)])
    g=gradient(high);ff=dc(high);r=[Decimal(0)]*200;joint=np.zeros((200,200))
    for a in range(134):
        i=vi(a)
        if i is None:continue
        r[i]+=f[a]
        for b in range(134):
            k=vi(b)
            if k is not None:joint[i,k]+=float(j[a][b])
    for a in range(68):
        i=ci(a);r[i]+=D(ff[a])+sum(D(g[a,b])*D(low[b]) for b in range(68))
        for b in range(68):joint[i,ci(b)]+=g[a,b]
    return r,joint

def root_check(state,current,target,forcing,e,caps):
    f,j=physical_dc(state);require(abs(-f[43]-D(forcing))<=D(2e-11),'phase retention current')
    f[43]=state[43];j[43,:]=0;j[43,43]=1
    r=f+[Decimal(0)]*18;matrix=np.block([[j,e],[e.T,np.zeros((18,18))]])
    for k,(a,b,c) in enumerate(caps):
        r[a]+=current[k]
        if b is not None:r[b]-=current[k]
        r[200+k]=state[a]-(state[b] if b is not None else 0)-target[k]
    norm=max(abs(v)/D(1e-11 if k==43 or k>=200 else 2e-10 if 98<=k<133 else 2e-11) for k,v in enumerate(r))
    direction=np.linalg.solve(matrix,np.array([-float(v) for v in r]));correction=max(abs(v)/(1e-9 if k>=200 or 98<=k<133 else 1e-6) for k,v in enumerate(direction))
    require(norm<=1 and correction<=1,'independent 218-row conditioned charge root')
    return dict(rows=218,residual_gate_ratio=str(norm),correction_gate_ratio=float(correction),max_charge_voltage_error_v=str(max(abs(x) for x in r[200:])),phase_error_v=str(abs(state[43])),phase_retention_a=str(-physical_dc(state)[0][43]),chain_capacitor_current_a=list(map(str,current)),chain_capacitor_voltage_derivative_v_per_s=[str(i/D(c)) for i,(a,b,c) in zip(current,caps)])

def check(native):
    lines=native['commands'][-1]['stdout'].splitlines();targets=[]
    for line in (ROOT/'evidence/voice_joint_charge_response_targets01.txt').read_text().splitlines():
        raw=list(map(float,line.split()));require(len(raw)==36,'target codec');targets.append([D(raw[k])+D(raw[k+1]) for k in range(0,36,2)])
    e,caps=incidence();initial=decode(lines[lines.index('INITIAL_HISTORY')+1]);oldvolts=[initial[a]-(initial[b] if b is not None else 0) for a,b,c in caps]
    prediction=json.loads((ROOT/'evidence/voice_joint_charge_response_fine_reference01.json').read_text());require(prediction['passed'],'admitted predictor')
    for id in range(2):require(max(abs(a-Decimal(b)) for a,b in zip(targets[id],prediction['records'][id]['predictor']['target_voltages_decimal']))<=Decimal('1e-28'),'exact predicted targets')
    roots=[];root_states={};currents={};ends={};profiles=[];cases=[];rejections=0
    for i,line in enumerate(lines):
        if line=='INPUT_REJECTIONS,2':rejections+=2
        if line.startswith('CHARGE_ROOT,'):
            _,id,guess,iterations,trials,res,corr,forcing=line.split(',');id=int(id);guess=int(guess);state=decode(lines[i+1]);raw=list(map(float,lines[i+2].split(',')[1:]));require(len(raw)==36,'current codec');current=[D(raw[k])+D(raw[k+1]) for k in range(0,36,2)]
            require(float(res)<=1 and float(corr)<=1 and int(iterations)<=64 and int(trials)<=64*24,'native augmented gates')
            roots.append(dict(id=id,guess=guess,**root_check(state,current,targets[id],float(forcing),e,caps)));root_states[id,guess]=state;currents[id,guess]=current
        if line.startswith('JOINT_ROOT,'):
            _,mask,h,res,corr=line.split(',');cases.append((int(mask),float(h),*[decode(s) for s in lines[i+1:i+6]]))
        if line.startswith('RELEASE_PROFILE,'):
            _,id,maximum,steps,lte,bus,c1,restore=line.split(',');id=int(id);maximum=int(maximum);require(int(steps)<=512 and float(lte)<=1 and max(float(bus),float(c1))<=1e-12 and restore=='restore=exact','free release gates')
            profiles.append(dict(id=id,maximum_half_ticks=maximum,intervals=int(steps),max_lte=float(lte),bus_kcl_a=float(bus),c1_kcl_a=float(c1),restore_exact=True));ends[id,maximum]=decode(lines[i+1])
    require(len(roots)==4 and set(root_states)=={(a,b) for a in range(2) for b in range(2)} and len(ends)==4 and len(cases)==24 and rejections==2,'complete conditioning/release coverage')
    guesses=[];refinement=[]
    for id in range(2):
        ratio=max(abs(a-b)/D(1e-9 if 98<=k<133 else 1e-6) for k,(a,b) in enumerate(zip(root_states[id,0],root_states[id,1])))
        cur=max(abs(a-b)/D(1e-9) for a,b in zip(currents[id,0],currents[id,1]));require(max(ratio,cur)<=1,'two guesses converge')
        guesses.append(dict(id=id,state_error_ratio=str(ratio),capacitor_current_error_ratio=str(cur)))
        ratio=max(abs(a-b)/D(2e-9 if 98<=k<133 else 2e-6) for k,(a,b) in enumerate(zip(ends[id,65536],ends[id,32768])));require(ratio<=1,'200-coordinate release refinement')
        refinement.append(dict(id=id,error_ratio=str(ratio)))
    stages=[evaluate(c) for c in cases];lte=[]
    for k in range(0,len(cases),3):
        full,mid,end=cases[k:k+3];require(full[2]==mid[2] and mid[-1]==end[2] and full[1]==2*mid[1] and mid[1]==end[1],'selected release histories')
        ratio=max(abs(a-b)/D(2e-9 if 98<=k<133 else 2e-6) for k,(a,b) in enumerate(zip(full[-1],end[-1])));require(ratio<=1,'selected LTE');lte.append(str(ratio))
    states=[]
    for id in range(2):
        s=root_states[id,0];states.append(dict(id=id,bus_v=str(s[12]),saw_v=str(s[46]),j7_v=str(s[194]),c27_v=str(s[ci(6)]-s[12]),charge_targets_v=list(map(str,targets[id])),difference_from_lift=[str(a-b) for a,b in zip(s,initial)]))
    return dict(augmented_root_checks=roots,charge_incidence_rank=18,physical_capacitors=18,jointly_corrected_targets=2,static_predictor_is_not_a_periodic_root=True,guess_comparisons=guesses,release_profiles=profiles,release_stage_checks=stages,release_lte=lte,release_refinement=refinement,conditioned_states=states,restore_replays=4,accepted_intervals=sum(p['intervals'] for p in profiles),duration_per_profile_s=2e-6,final_ticks=1048576,input_rejections=2,independent_root_search=False,steady_periodicity_admitted=False,own_joint_power_on=False,physical_cards_changed=False,physical_fidelity=False,real_time=False,new_audio=False,new_spice_processes=0)

def main():
    p=argparse.ArgumentParser();p.add_argument('--attempt',type=int,required=True);a=p.parse_args();out=ROOT/f'evidence/voice_joint_charge_corrected_reference{a.attempt:02d}.json';require(not out.exists(),'preserve receipt')
    n='evidence/voice_joint_charge_corrected_native01.json';native=json.loads((ROOT/n).read_text());require(native['passed'],'passed native')
    names={n,'tools/check_joint_charge_corrected.py','evidence/voice_joint_charge_response_targets01.txt','docs/VOZ_CARGAS_CORREGIDAS_PROTOCOLO.md','evidence/voice_joint_charge_response_fine_reference01.json'}
    for module in list(sys.modules.values()):
        f=getattr(module,'__file__',None)
        if f:
            path=Path(f).resolve()
            if path.is_relative_to(ROOT/'tools') and path.suffix=='.py':names.add(path.relative_to(ROOT).as_posix())
    before={n:sha(ROOT/n) for n in sorted(names)};r=dict(schema='rf-d/joint-charge-seed-reference/v1',passed=False,source_sha256=before);start=time.perf_counter()
    try:
        with localcontext() as ctx:ctx.prec=100;r.update(check(native))
        r['passed']=True
    except Exception:
        r['failure']=traceback.format_exc();r['failed_source_text']=(ROOT/'tools/check_joint_charge_corrected.py').read_text()
        try:
            with localcontext() as ctx:ctx.prec=100;check(native)
            r['replay']='unexpected pass'
        except Exception:r['replay']=traceback.format_exc()
    r['source_sha256_after']={n:sha(ROOT/n) for n in sorted(names)};require(before==r['source_sha256_after'],'unchanged independent source');r['wall_s']=time.perf_counter()-start;out.write_text(json.dumps(r,indent=2,allow_nan=False)+'\n',encoding='utf8',newline='\n');print('CHARGE_SEED_REFERENCE',r['passed'],r.get('failure',''),flush=True)
if __name__=='__main__':main()
