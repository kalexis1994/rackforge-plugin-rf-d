"""Independent uncondensed Python chain equations and finite-difference Newton."""
import json,re,math,subprocess,os,sys,traceback,time
from pathlib import Path
import numpy as np
from prepare_dual_chain import ROOT,sha,write
from affine_evidence import Sources
from check_hybrid_voice import unpack,packed
from check_vco_phase import COMPILER,LIB
from cutoff_j7_vectors import setup
from circuit66_dc_vectors import dc_evaluator
from chain_charge_reference import mass
from vco_family import lagrange
AREA=ROOT/'tmp/lab-current'

def model(r61,load,cv):
    values=SETUPS[r61];f=dc_evaluator(values,values[4]);w,_=lagrange(cv);cc=np.einsum('i,ijck->jck',w,TABLE);ll=w@LOGS;cb=(cc[1]-cc[0])/.25;c0=(cc[1]+cc[0])/2;lb=(ll[1]-ll[0])/.25;l0=(ll[1]+ll[0])/2
    # Keep the R6 cursor as an independent nodal solve in the oracle.
    def source(bus,phase,mean):
        c=c0[0]+cb[0]*bus
        if mean:saw=c[0].real
        else:
            e=np.exp(2j*np.pi*np.arange(129)*(phase%1));e[1:]*=2;saw=float(np.real(c@e))
        cursor=float(np.linalg.solve(np.array([[2/12500.+1/33000.]]),np.array([saw/12500.+bus/33000.]))[0]);return (bus-cursor)/33000.,2**(l0+lb*bus)
    g=1/33000.+(2/39250.+1/17250. if load else 0.)
    def dc(x,mean):
        y=np.zeros(69);y[:66]=f(x[:66].tolist())[0];y[:48]*=-1.;q,freq=source(x[66],x[68],mean);y[66]=q+g*x[66];i=(x[22]-x[67])/25500.;y[22]+=i;y[67]=-i;return y,freq
    return dc,source

def solve(fun,seed):
    x=np.array(seed,float)
    for it in range(64):
        r=fun(x);j=gradient(fun,x);d=np.linalg.solve(j,-r);norm=max(float(np.max(abs(r[:68])))/1e-11,abs(r[68])/1e-11);corr=max(float(np.max(abs(d[:68])))/1e-8,abs(d[68])/1e-11)
        if norm<=1 and corr<=1:return x,dict(iterations=it+1,kcl_a=float(np.max(abs(r[:68]))),phase_residual_cycles=float(abs(r[68])),correction_v=float(np.max(abs(d[:68]))))
        for power in range(24):
            z=x+2.**-power*d
            try:rr=fun(z);nn=max(float(np.max(abs(rr[:68])))/1e-11,abs(rr[68])/1e-11)
            except(OverflowError,ValueError):continue
            if nn<norm or nn<=1:x=z;break
        else:raise AssertionError(('FD line search',it,norm,corr))
    raise AssertionError('FD root iteration budget')
def gradient(fun,x):
    j=np.empty((69,69));eps=1e-6
    for k in range(69):
        a=x.copy();b=x.copy();a[k]+=eps;b[k]-=eps;j[:,k]=(fun(a)-fun(b))/(2*eps)
    return j

def audit():
    global SETUPS,TABLE,LOGS
    n=json.loads((ROOT/'evidence/family_filter_native01.json').read_text(encoding='utf8'));assert n['passed'];raw=unpack(n['roots']['stdout']).decode().splitlines();dcs=[];roots=[]
    for line in raw:
        z=line.split(',')
        if z[0]=='DC':assert len(z)==142;dcs.append(z)
        elif z[0]=='ROOT':assert len(z)==284;roots.append(z)
    assert len(dcs)==12 and len(roots)==16
    text=(ROOT/'tools/family_mixer_data128.rs').read_text(encoding='utf8');a,b=text.split('pub const COEFFICIENTS:',1);pattern=r'[-+]?\d+\.\d+e[-+]\d+';LOGS=np.array(list(map(float,re.findall(pattern,a)))).reshape(4,2);q=np.array(list(map(float,re.findall(pattern,b)))).reshape(4,2,7,129,2);TABLE=q[...,0]+1j*q[...,1]
    SETUPS={r:setup(r) for r in [200.,200000.]};M=np.zeros((69,69));M[:68,:68]=mass();dc_results=[];root_results=[];tangent_inputs=[];functors=[]
    for z in dcs:
        r61,load,cv=float(z[1]),int(z[2]),float(z[3]);dc,source=model(r61,load,cv);seed=np.r_[SETUPS[r61][5]['node_v'],-.01,SETUPS[r61][5]['node_v'][22],0.]
        def f(x):
            y,_=dc(x,True);y[68]=x[68];return y
        x,metrics=solve(f,seed);v=np.array(list(map(float,z[4:])));native=v[:69]+v[69:];err=float(np.max(abs(x-native)));assert err<=1e-6,(r61,load,cv,err)
        dc_results.append(dict(r61_ohm=r61,load=load,cv_v=cv,node_error_v=err,root=x.tolist(),**metrics));print('FILTER_FD_DC',r61,load,cv,flush=True)
    for idx,z in enumerate(roots):
        r61,load,cv,h=float(z[1]),int(z[2]),float(z[3]),float(z[5]);old_flat=np.array(list(map(float,z[8:146])));new_flat=np.array(list(map(float,z[146:])));old=old_flat[:69]+old_flat[69:];native=new_flat[:69]+new_flat[69:];dc,source=model(r61,load,cv);old_dc,old_f=dc(old,False)
        def f(delta):
            now=old+delta;y,freq=dc(now,False);y=y+old_dc+2/h*(M@delta);y[68]=delta[68]-h*.5*(old_f+freq);return y
        delta,metrics=solve(f,np.zeros(69));actual=old+delta;err=float(np.max(abs(actual-native)));assert err<=1e-6,(idx,err)
        slope=gradient(f,native-old);functors.append(slope[:,[6,66,68]]);root_results.append(dict(index=idx,r61_ohm=r61,load=load,cv_v=cv,h_s=h,node_error_v=err,root=actual.tolist(),**metrics));tangent_inputs.append(','.join([str(idx),*z[1:8],*z[8:]]));print('FILTER_FD_STEP',idx,flush=True)
    # Derive a read-only tangent caller from the measured native caller.
    original=(ROOT/'tools/family_filter_probe.rs').read_text(encoding='utf8');assert original.count('fn main()->')==1
    addition='''
fn main()->Result<(),Box<dyn std::error::Error>>{
 use std::io::BufRead;
 for line in std::io::stdin().lock().lines(){let line=line?;let z:Vec<_>=line.split(',').collect();let index:usize=z[0].parse()?;let p=parameters(z[1].parse()?,z[2].parse()?);let cv:f64=z[3].parse()?;let h:f64=z[5].parse()?;
 let v:Vec<f64>=z[8..].iter().map(|s|s.parse().unwrap()).collect();assert_eq!(v.len(),276);let old=State{high:std::array::from_fn(|k|v[k]),low:std::array::from_fn(|k|v[69+k])};let delta=State::new(std::array::from_fn(|k|(v[138+k]-v[k])+(v[207+k]-v[69+k])));
 let s=core::linearize(p,cv,old,delta,h,false).map_err(|e|format!("{e:?}"))?;print!("J,{index}");for row in 0..N{for col in [6,66,68]{print!(",{:.17e}",s.j[row][col]);}}println!();
 }Ok(())}
'''
    helper=ROOT/'tools/family_filter_tangent_probe.rs';expected=original.replace('fn main()->','fn historical_main()->',1)+addition
    if helper.exists():assert helper.read_text(encoding='utf8')==expected
    else:helper.write_text(expected,encoding='utf8',newline='\n')
    names=['tools/check_family_filter_reference.py','tools/family_filter_tangent_probe.rs','tools/family_filter_probe.rs','docs/FAMILIA_FILTRO_PROTOCOLO.md']
    for m in list(sys.modules.values()):
        p=getattr(m,'__file__',None)
        if p and Path(p).resolve().is_relative_to(ROOT/'tools') and Path(p).suffix=='.py':names.append(Path(p).resolve().relative_to(ROOT).as_posix())
    sources=Sources(names);assert not list(AREA.iterdir());env=dict(os.environ,PATH='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+os.environ['PATH'])
    try:
        command=[COMPILER,'--edition=2021','-C','opt-level=2','-C','strip=symbols','-C','link-arg=-Wl,--stack,33554432','-A','dead_code','-A','unused_imports',str(helper),'--extern','rf_d_circuit='+str(LIB),'-o',str(AREA/'tangent.exe')];p=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=120);assert p.returncode==0,p.stderr.decode()
        q=subprocess.run([str(AREA/'tangent.exe')],cwd=ROOT,env=env,input=('\n'.join(tangent_inputs)+'\n').encode(),capture_output=True,timeout=240);assert q.returncode==0,q.stderr.decode();tangents=[]
        for line in q.stdout.decode().splitlines():
            z=line.split(',');idx=int(z[1]);a=np.array(list(map(float,z[2:]))).reshape(69,3);b=functors[idx];ratio=float(np.max(abs(a-b)/(1e-10+1e-5*abs(b))));assert ratio<=1,(idx,ratio);tangents.append(ratio)
        assert len(tangents)==16
    finally:
        p=AREA/'tangent.exe'
        if p.exists():assert p.resolve().parent==AREA.resolve();p.unlink()
    sources.unchanged();return dict(passed=True,**sources.fields(),native_sha256=sha(ROOT/'evidence/family_filter_native01.json'),dc=dc_results,roots=root_results,tangent_max_scaled_error=max(tangents),tangent_columns=48,tangent_rows_compared=3312,native_roots_used_as_seed=False,shared_incoming_histories=True,independent_family_oracle=False,temporary_area_empty=not list(AREA.iterdir()),new_spice_processes=0,new_audio=False)
def main():
    try:r=audit()
    except Exception:
        r=dict(passed=False,**Sources(['tools/check_family_filter_reference.py']).fields(),failure=traceback.format_exc())
        try:audit();r['unchanged_replay']='unexpected pass'
        except Exception:r['unchanged_replay']=traceback.format_exc()
        k=1
        while(ROOT/f'evidence/family_filter_reference_failure{k:02d}.json').exists():k+=1
        write(ROOT/f'evidence/family_filter_reference_failure{k:02d}.json',r);raise
    write(ROOT/'evidence/family_filter_reference01.json',r);print('FILTER_REFERENCE',len(r['dc']),len(r['roots']),r['tangent_max_scaled_error'])
if __name__=='__main__':main()
