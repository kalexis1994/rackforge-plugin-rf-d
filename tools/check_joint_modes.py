"""Charge-mode excitation/observation; linear local scope only, no new roots."""
import argparse,json,shutil,sys,time,traceback
from pathlib import Path
import numpy as np
from prepare_vco1_portable import ROOT,sha
from joint_cycles_analysis import require
from check_joint_reference import decode,ci
from chain_charge_reference import CAPS,mass,problem

def complex_pair(z):return [float(z.real),float(z.imag)]

def inputs(receipt):
    lines=receipt['commands'][-1]['stdout'].splitlines();roots=[];g=c=None
    for i,line in enumerate(lines):
        if line.startswith('STARTUP_ROOT,'):roots.append(decode(lines[i+1]))
        if line.startswith('CHAIN_G,'):g=np.array(list(map(float,line.split(',')[1:]))).reshape(68,68)
        if line.startswith('CHAIN_C,'):c=np.array(list(map(float,line.split(',')[1:]))).reshape(68,68)
    require(len(roots)==2 and g is not None and c is not None,'complete native matrices')
    return roots[0],g,c

def direct(g,c,f):
    a=g.astype(complex)+2j*np.pi*f*c;a[66,:]=0;a[66,66]=1
    b=np.zeros(68,dtype=complex);b[66]=1;x=np.linalg.solve(a,b);r=a@x-b
    require(max(abs(r[np.arange(68)!=66]))<=1e-10 and abs(r[66])<=1e-12,'direct nodal residual')
    return x

def check(receipt):
    state,g,c=inputs(receipt);caps=[*CAPS,(67,7,10e-6)];e=np.zeros((68,18));values=[];capacitors=[]
    for k,(a,b,farad) in enumerate(caps):
        b=b if isinstance(b,int) else 66 if b=='BUS' else None;e[a,k]=1
        if b is not None:e[b,k]=-1
        values.append(farad);capacitors.append(dict(index=k,a=a,b=b,capacitance_f=farad))
    require(max(abs((e@np.diag(values)@e.T-c).ravel()))<=1e-15,'native C from physical incidence')
    z=np.diag(np.sqrt(values));ep=e.copy();ep[66,:]=0;gg=g.copy();gg[66,:]=0;gg[66,66]=1;cc=c.copy();cc[66,:]=0
    b=np.zeros(68);b[66]=1;f=np.linalg.solve(gg,b);l=np.linalg.solve(gg,ep@z);t=z@e.T@l
    taus,v=np.linalg.eig(t);inv=np.linalg.solve(v,np.eye(18));a=inv@(z@e.T@f);o=l@v
    inverse_residual=float(np.linalg.norm(v@inv-np.eye(18),2)/(np.linalg.norm(v,2)*np.linalg.norm(inv,2)))
    require(inverse_residual<=1e-10,'modal inverse residual')
    require(np.all(np.isfinite(taus)) and np.all(abs(taus)>0),'18 finite nonzero modes')
    poles=-1/taus;k=o[61,:]*a/taus;whole=o*(a/taus)[None,:];direct_term=f-np.sum(whole,axis=1)
    m=np.linalg.solve(gg,cc);modes=[]
    for n in range(18):
        r1=float(np.linalg.norm(t@v[:,n]-taus[n]*v[:,n])/((np.linalg.norm(t,2)+abs(taus[n]))*np.linalg.norm(v[:,n])))
        r2=float(np.linalg.norm(m@o[:,n]-taus[n]*o[:,n])/((np.linalg.norm(m,2)+abs(taus[n]))*np.linalg.norm(o[:,n])))
        require(r1<=1e-8 and r2<=1e-8,'reduced/exterior mode residual')
        energy=abs(v[:,n])**2;energy/=sum(energy);require(abs(sum(energy)-1)<=1e-12,'energy partition')
        modes.append(dict(index=n,tau_s=complex_pair(taus[n]),pole_per_s=complex_pair(poles[n]),excitation_sqrt_f_v=complex_pair(a[n]),j7_observation=complex_pair(o[61,n]),j7_lowpass_weight_v_per_v=complex_pair(k[n]),j7_s_residue_per_s=complex_pair(k[n]/taus[n]),capacitor_energy_fraction=energy.tolist(),reduced_residual=r1,exterior_residual=r2))
    # Independent Jacobian at the same declared native root; no root search.
    _,gradient,_=problem(200,0,[0.,.2,-.3,.1,.4]);refg=gradient(np.array([float(state[ci(n)]) for n in range(68)]));refc=mass()
    frequencies=[0.,*np.logspace(-2,6,25).tolist(),410.80175922051075];ac=[]
    for hz in sorted(frequencies):
        s=2j*np.pi*hz;xd=direct(g,c,hz);xr=direct(refg,refc,hz)
        xm=f-s*(o@(a/(1+s*taus)));xw=direct_term+whole@(1/(1+s*taus))
        metric=lambda x:float(np.max(abs(x-xd)/(1e-10+1e-8*abs(xd))))
        ratio,weights_ratio=metric(xm),metric(xw);ref_ratio=float(np.max(abs(xd-xr)/(1e-6+1e-4*abs(xr))))
        require(ratio<=1 and weights_ratio<=1 and ref_ratio<=1,'nodal transfer/modal/independent comparison')
        ac.append(dict(frequency_hz=hz,j7_direct=complex_pair(xd[61]),j7_modal=complex_pair(xm[61]),reconstruction_gate_ratio=ratio,weights_gate_ratio=weights_ratio,independent_gate_ratio=ref_ratio))
    steps=[]
    for seconds in [0.,1e-6,.001,.00525,.02,.1,.265,1.3]:
        exponential=np.exp(poles*seconds);x=f-whole@exponential;dx=whole@(-poles*exponential);r=gg@x+cc@dx-b
        physical=float(max(abs(r[np.arange(68)!=66])));boundary=float(abs(r[66]));imag=float(max(abs(x.imag)))
        require(physical<=1e-10 and boundary<=1e-12 and imag<=1e-10,'analytic step DAE residual')
        q=z@e.T@x
        if seconds==0:require(float(max(abs(q)))<=1e-10,'zero incremental capacitor history at 0+')
        error=x[61]-f[61];envelope=float(sum(abs(k)*np.exp(poles.real*seconds)))
        require(abs(error)<=envelope+1e-12,'signed transient inside triangle envelope')
        steps.append(dict(time_s=seconds,j7_step_v_per_v=complex_pair(x[61]),j7_signed_error_v_per_v=complex_pair(error),j7_error_envelope_v_per_v=envelope,max_physical_residual_a=physical,bus_error_v=boundary,max_imaginary_v=imag,max_incremental_sqrt_f_v=float(max(abs(q)))))
    stable=bool(np.all(poles.real<0));settling=None
    if stable:
        envelope=lambda seconds:float(sum(abs(k)*np.exp(poles.real*seconds)))
        lo=0.;hi=max(1.,float(max(taus.real)))
        while envelope(hi)>.001:hi*=2;require(hi<=1e6,'bounded local envelope search')
        if envelope(0)<=.001:hi=0.
        else:
            for _ in range(80):
                mid=(lo+hi)/2
                if envelope(mid)>.001:lo=mid
                else:hi=mid
        settling=dict(formal_step_v=.001,output_threshold_v=1e-6,gain_threshold_v_per_v=.001,time_s=hi,envelope_v_per_v=envelope(hi),linear_local_only=True)
    return dict(modes=modes,capacitors=capacitors,charge_modes=18,algebraic_coordinates=50,modal_vector_condition_2=float(np.linalg.cond(v)),inverse_relative_residual=inverse_residual,j7_dc_gain=complex_pair(f[61]),j7_algebraic_direct=complex_pair(direct_term[61]),j7_weight_sum=complex_pair(sum(k)),sum_absolute_j7_weights=float(sum(abs(k))),ac=ac,step=steps,all_local_poles_decaying=stable,local_envelope=settling,independent_root_search=False,global_settling_bound=False,initialized_cycle_admitted=False,physical_cards_changed=False)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--attempt',type=int,required=True);args=parser.parse_args();out=ROOT/f'evidence/voice_joint_modes_reference{args.attempt:02d}.json';require(not out.exists(),'preserve receipts')
    name='evidence/voice_joint_startup_native01.json';data=json.loads((ROOT/name).read_text());require(data['passed'],'admitted native matrices')
    names={name,'evidence/voice_joint_startup_reference01.json','docs/VOZ_MODOS_PROTOCOLO.md','tools/check_joint_modes.py'}
    for module in list(sys.modules.values()):
        path=getattr(module,'__file__',None)
        if path:
            p=Path(path).resolve()
            if p.is_relative_to(ROOT/'tools') and p.suffix=='.py':names.add(p.relative_to(ROOT).as_posix())
    before={n:sha(ROOT/n) for n in sorted(names)};start=time.perf_counter();free=shutil.disk_usage(ROOT).free
    r=dict(schema='rf-d/joint-modes-reference/v1',passed=False,source_sha256=before,new_audio=False,new_spice_processes=0,new_native_processes=0,available_free_bytes=free,temporal_campaign_reserve_bytes=1073741824,temporal_campaign_launched=False)
    try:r.update(check(data));r['passed']=True
    except Exception:
        r['failure']=traceback.format_exc();r['failed_source_text']=(ROOT/'tools/check_joint_modes.py').read_text()
        try:check(data);r['replay']='unexpected pass'
        except Exception:r['replay']=traceback.format_exc()
    r['source_sha256_after']={n:sha(ROOT/n) for n in sorted(names)};require(before==r['source_sha256_after'],'unchanged input matrices and sources');r['wall_s']=time.perf_counter()-start;r['final_free_bytes']=shutil.disk_usage(ROOT).free
    out.write_text(json.dumps(r,indent=2,allow_nan=False)+'\n',encoding='utf8',newline='\n');print('JOINT_MODES',r['passed'],r.get('failure',''),flush=True)
if __name__=='__main__':main()
