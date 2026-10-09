"""Independent DC/stage checks and local chain transfer/charge modes.
Uses declared native root points; no independent nonlinear root search.
"""
import argparse,json,time,traceback
from decimal import Decimal,localcontext
import numpy as np
from prepare_vco1_portable import ROOT,sha
from check_joint_reference import vi,ci,D,decode,CONFIG,evaluate
from check_joint_cycles import bank
from vco1_increment_circuit import reference_decimal
from chain_charge_reference import problem,mass,CAPS
from joint_cycles_analysis import require

def dc_check(state):
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
    forcing=-r[43];r[43]=state[43];joint[43,:]=0;joint[43,43]=1
    residual=max(abs(v)/D(2e-10 if 98<=k<133 or k==43 else 2e-11) for k,v in enumerate(r))
    direction=np.linalg.solve(joint,np.array([-float(v) for v in r]));correction=max(abs(v)/(1e-9 if 98<=k<133 else 1e-6) for k,v in enumerate(direction))
    require(residual<=1 and correction<=1,'independent conditioned DC')
    return dict(rows=200,residual_gate_ratio=str(residual),correction_gate_ratio=float(correction),constraint_current_a=str(forcing)),high,g

def transfer(g,c,frequency):
    a=g.astype(complex)+2j*np.pi*frequency*c;a[66,:]=0;a[66,66]=1;b=np.zeros(68,dtype=complex);b[66]=1
    x=np.linalg.solve(a,b);r=a@x-b
    require(np.max(np.abs(r[np.arange(68)!=66]))<=1e-10 and abs(r[66])<=1e-12,'AC residual')
    return x,dict(frequency_hz=frequency,max_residual_a=float(np.max(np.abs(r[np.arange(68)!=66]))),bus_error_v=float(abs(r[66])),j7_gain_abs=float(abs(x[61])),j7_gain_db=float(20*np.log10(abs(x[61]))),j7_phase_deg=float(np.angle(x[61],deg=True)))

def check(receipt):
    lines=receipt['commands'][-1]['stdout'].splitlines();roots=[];forcing=[];initial=None;native_g=None;native_c=None;ends=[];release=[]
    for i,line in enumerate(lines):
        if line=='INITIAL_HISTORY':initial=decode(lines[i+1])
        if line.startswith('STARTUP_ROOT,'):roots.append(decode(lines[i+1]));forcing.append(float(line.split(',')[-1]))
        if line.startswith('CHAIN_G,'):native_g=np.array(list(map(float,line.split(',')[1:]))).reshape(68,68)
        if line.startswith('CHAIN_C,'):native_c=np.array(list(map(float,line.split(',')[1:]))).reshape(68,68)
        if line.startswith('RELEASE_PROFILE,'):release.append(list(map(float,line.split(',')[1:])));ends.append(decode(lines[i+1]))
    require(len(roots)==2 and len(ends)==2 and initial is not None,'native coverage')
    checks=[];high=None;reference_g=None
    for state,current in zip(roots,forcing):
        result,x,g=dc_check(state);require(abs(D(current)-Decimal(result['constraint_current_a']))<=D(2e-11),'constraint current independent')
        checks.append(result)
        if high is None:high=x;reference_g=g
    c=mass();g_ratio=float(np.max(np.abs(native_g-reference_g)/(1e-8+2e-5*np.abs(reference_g))));c_ratio=float(np.max(np.abs(native_c-c)/(1e-15+1e-12*np.abs(c))))
    require(g_ratio<=1 and c_ratio<=1,'chain G/C independent')
    frequencies=[10.,100.,410.80175922051075,1000.,10000.];ac=[]
    for f in frequencies:
        xn,metric=transfer(native_g,native_c,f);xr,rm=transfer(reference_g,c,f)
        error=float(np.max(np.abs(xn-xr)/(1e-6+1e-4*np.abs(xr))));require(error<=1,'AC independent voltage comparison')
        ac.append(dict(**metric,reference_error_ratio=error,reference_j7_gain_abs=rm['j7_gain_abs']))
    # Physical charge coordinates: 17 old caps and explicit C10.
    caps=[*CAPS,(67,7,10e-6)];inc=np.zeros((68,18));values=[];history=[]
    for k,(a,b,farad) in enumerate(caps):
        b=b if isinstance(b,int) else 66 if b=='BUS' else None;inc[a,k]=1
        if b is not None:inc[b,k]=-1
        values.append(farad);voltage=lambda state:state[ci(a)]-(state[ci(b)] if b is not None else Decimal(0))
        before,after=voltage(initial),voltage(roots[0]);history.append(dict(a=a,b=b,capacitance_f=farad,old_v=str(before),conditioned_v=str(after),difference_v=str(after-before),charge_difference_c=str(D(farad)*(after-before))))
    require(np.max(np.abs(inc@np.diag(values)@inc.T-c))<=1e-15,'incidence reproduces independent C')
    g=native_g.copy();cc=native_c.copy();g[66,:]=0;g[66,66]=1;cc[66,:]=0
    e=inc.copy();e[66,:]=0;z=np.diag(np.sqrt(values));lift=np.linalg.solve(g,e@z);t=z@inc.T@lift;m=np.linalg.solve(g,cc)
    times,vectors=np.linalg.eig(t);modes=[]
    for k,tau in enumerate(times):
        v=vectors[:,k];outer=lift@v
        small=float(np.linalg.norm(t@v-tau*v)/((np.linalg.norm(t,2)+abs(tau))*np.linalg.norm(v)))
        big=float(np.linalg.norm(m@outer-tau*outer)/((np.linalg.norm(m,2)+abs(tau))*np.linalg.norm(outer)))
        require(small<=1e-8 and big<=1e-8 and abs(tau)>0,'charge-mode residual')
        pole=-1/tau;modes.append(dict(tau_real_s=float(tau.real),tau_imag_s=float(tau.imag),pole_real_per_s=float(pole.real),pole_imag_per_s=float(pole.imag),reduced_residual=small,exterior_residual=big,locally_decaying=bool(pole.real<0)))
    # The selected root banks are embedded in stdout using the inherited codec.
    selected=[]
    for i,line in enumerate(lines):
        if line.startswith('JOINT_ROOT,'):
            _,mask,h,res,corr=line.split(',');selected.append((int(mask),float(h),*[decode(s) for s in lines[i+1:i+6]]))
    require(len(selected)==12,'first/last full-mid-end coverage');stages=[evaluate(c) for c in selected];lte=[]
    for i in range(0,len(selected),3):
        full,mid,end=selected[i:i+3];require(full[2]==mid[2] and mid[-1]==end[2] and full[1]==2*mid[1] and mid[1]==end[1],'release histories')
        ratio=max(abs(a-b)/D(2e-9 if 98<=k<133 else 2e-6) for k,(a,b) in enumerate(zip(full[-1],end[-1])));require(ratio<=1,'selected release LTE');lte.append(str(ratio))
    refinement=max(abs(a-b)/D(2e-9 if 98<=k<133 else 2e-6) for k,(a,b) in enumerate(zip(*ends)));require(refinement<=1,'release same-clock refinement')
    return dict(dc_checks=checks,chain_g_gate_ratio=g_ratio,chain_c_gate_ratio=c_ratio,ac=ac,local_modes=modes,algebraic_coordinate_count=50,capacitor_initialization=history,release_stage_checks=stages,release_lte_decimal=lte,release_final_error_ratio=str(refinement),release_profiles=release,native_candidate_points_used=True,independent_root_solve=False,global_settling_bound=False)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--attempt',type=int,required=True);a=parser.parse_args();out=ROOT/f'evidence/voice_joint_startup_reference{a.attempt:02d}.json';require(not out.exists(),'new receipt')
    native='evidence/voice_joint_startup_native01.json';data=json.loads((ROOT/native).read_text());require(data['passed'],'native bank')
    names=[native,'tools/check_joint_startup.py','tools/check_joint_reference.py','tools/vco1_increment_circuit.py','tools/vco1_increment_devices.py','tools/chain_charge_reference.py','tools/circuit66_dc_vectors.py','docs/VOZ_INICIALIZACION_PROTOCOLO.md','docs/VOZ_INICIALIZACION_MATRICES.md']
    before={n:sha(ROOT/n) for n in names};r=dict(schema='rf-d/joint-startup-reference/v1',passed=False,source_sha256=before,new_audio=False,new_spice_processes=0);started=time.perf_counter()
    try:
        with localcontext() as ctx:ctx.prec=100;r.update(check(data))
        r['passed']=True
    except Exception:
        r['failure']=traceback.format_exc();r['failed_source_text']=(ROOT/'tools/check_joint_startup.py').read_text()
        try:
            with localcontext() as ctx:ctx.prec=100;check(data)
            r['replay']='unexpected pass'
        except Exception:r['replay']=traceback.format_exc()
    r['source_sha256_after']={n:sha(ROOT/n) for n in names};require(before==r['source_sha256_after'],'unchanged diagnostic sources');r['wall_s']=time.perf_counter()-started
    out.write_text(json.dumps(r,indent=2)+'\n',encoding='utf8',newline='\n');print('STARTUP_REFERENCE',r['passed'],r.get('failure',''),flush=True)
if __name__=='__main__':main()
