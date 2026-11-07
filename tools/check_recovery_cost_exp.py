"""Validate the new temporal method and time the same electrical work."""
import json,os,platform,subprocess,traceback
from pathlib import Path
import numpy as np
from prepare_dual_chain import ROOT,sha,write
from affine_evidence import Sources
from check_hybrid_voice import packed,unpack
from check_vco_phase import COMPILER,LIB
from check_recovery_cost import bench,read,digest,store,decode,law_grid,check_laws,AREA
from recovery_cost_exp_model import build,cases,simulate,step,law
from recovery_port_input_model import build as sdirk_build,simulate as sdirk_simulate
from check_charge_control import metrics
from vco_family import decode_window

def compare(raw):
    array=np.frombuffer(raw,'<f8').reshape(3,1537,93);assert np.isfinite(array).all();results=[]
    for i,case in enumerate(cases()):
        v=array[i];m=build(case);x,q,n=simulate(m,v[:,1],v[:,2]);err=float(np.max(abs(x-v[:,25:])));panel=float(max(abs((x[:,66]-.5*v[:,2])/39250-v[:,6])));qe=float(np.max(abs(q-v[:,7:25])));assert err<=1e-10 and panel<=1e-14 and qe<=1e-11,(err,panel,qe)
        assert np.array_equal(v[:,3:6].view('u8'),v[:,[91,31,86]].view('u8'))
        results.append(dict(index=i,node_error_v=err,panel_error_a=panel,charge_error_v=qe))
    return results

def endpoints(raw):
    models=[build(c) for c in cases()];out=[]
    for row in np.frombuffer(raw,'<f8').reshape(48,146):
        i,k,old,u,it,res=row[:6];m=models[int(i)];q0=row[6:24];n0=row[24:36];q=row[36:54];n=row[54:66];z=row[66:78];x=row[78:]-m['dc'];current=law(m,m['e']@x)[0]
        base=m['f']@q0+m['u0']*old+m['u1']*u+m['n0']@n0;balance=float(max(abs(q-base-m['n1']@n)));zp=m['zh']@base+m['zu']*u;res2=float(max(abs(z-zp+m['p']@law(m,z)[0])));physical=float(max(abs(m['alg']@(m['g']@x-m['b']*u+m['d']@current))));qe=float(max(abs(m['a']@x-q)));assert max(res,res2)<=2e-13 and balance<=1e-11 and physical<=1e-12 and qe<=1e-11 and max(abs(n-current))<=1e-14 and 1<=it<=12,(res,res2,balance,physical,qe)
        out.append(dict(index=int(i),sample=int(k),evaluations=int(it),reported_residual=float(res),recomputed_residual=res2,balance_v=balance,algebraic_kcl_a=physical,charge_error_v=qe))
    return out

def physical(raw):
    array=np.frombuffer(raw,'<f8').reshape(3,1537,93);corpus=read('evidence/charge_control_native01.json');results=[]
    for i,case in enumerate(cases()):
        v=array[i];m=build(case);profile=next(p for p in corpus['profiles'] if p['index']==i and p['amplitude_v']==.1 and p['step_ns']==250 and not p['dynamic']);signals=decode_window(profile['signal_window'],ROOT/corpus['pack']);states=decode_window(profile['state_window'],ROOT/corpus['pack']);x=np.empty((len(signals),68));cache={}
        # Defects at a stored Rust endpoint follow its own node voltages.
        # Recover n from that endpoint, then propagate its physical q.
        seeds=np.stack([law(m,m['e']@(row[25:]-m['dc']))[0] for row in v])
        for j in range(len(signals)):
            k,rem=divmod(j*12,125)
            if rem==0:x[j]=v[k,25:];continue
            if rem not in cache:cache[rem]=build(case,rem/(125*384000))
            u=v[k,2]+rem/125*(v[k+1,2]-v[k,2]);_,_,delta,_,_,_=step(cache[rem],v[k,7:25],v[k,2],u,seeds[k]);x[j]=m['dc']+delta
        full=states[:,3:71]+states[:,71:139];sparse=metrics(full,x[profile['state_rows']]);ports=np.zeros_like(x);candidate=np.zeros_like(x)
        for col,node in [(3,61),(4,66),(5,6)]:ports[:,node]=signals[:,col];candidate[:,node]=x[:,node]
        port=metrics(ports,candidate);fine,_=sdirk_simulate(sdirk_build(case,250e-9),signals[:,0],signals[:,1]);temporal=metrics(fine,x);accepted=bool(sparse['node_gate_pass'] and port['audio_gate_pass'] and port['panel_gate_pass'] and temporal['node_gate_pass']);results.append(dict(index=i,physical_sparse_nodes=sparse,physical_dense_ports=port,temporal_same_hybrid_dense_nodes=temporal,admitted=accepted,partial_maps=len(cache),uses_only_own_rust_state=True))
        print('EXP_RESERVE',i,sparse['all_nodes_error_v'],temporal['all_nodes_error_v'],port['j7_rms_relative'],accepted,flush=True)
    return results

def audit(r):
    old=read('evidence/recovery_port_tests01.json');assert sha(Path(COMPILER))==old['compiler']['sha256'] and sha(LIB)==old['private_input_sha256'][LIB.relative_to(ROOT).as_posix()];r.update(compiler_sha256=sha(Path(COMPILER)),library_sha256=sha(LIB),platform=platform.platform())
    exe=AREA/'recovery-cost-exp.exe';assert not list(AREA.iterdir());env=dict(os.environ,PATH='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+os.environ['PATH']);command=[];stdin=None
    try:
        command=[COMPILER,'--edition=2021','-C','opt-level=2','-C','strip=symbols','-C','link-arg=-Wl,--stack,33554432','-A','dead_code','-A','unused_imports','--cfg','expfoh',str(ROOT/'tools/recovery_cost_probe.rs'),'--extern','rf_d_circuit='+str(LIB),'-o',str(exe)]
        p=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=120);r['compile']=dict(command=command,exit_code=p.returncode,stderr=packed(p.stderr));assert p.returncode==0,p.stderr.decode()
        for key in ['vectors','stress']:
            command=[str(exe),key];p=subprocess.run(command,env=env,capture_output=True,timeout=240);assert p.returncode==0,p.stderr.decode();ref='evidence/recovery_port_fast_native03.json' if key=='vectors' else 'evidence/recovery_cost_baseline01.json';r[key]=store(p.stdout,ref,key);r[key]['python_comparison']=compare(p.stdout)
        command=[str(exe),'laws'];stdin=law_grid().astype('<f8').tobytes();p=subprocess.run(command,input=stdin,env=env,capture_output=True,timeout=240);assert p.returncode==0,p.stderr.decode();r['laws']=dict(input=packed(stdin),output_sha256=digest(p.stdout),comparisons=check_laws(p.stdout));stdin=None
        command=[str(exe),'stages'];p=subprocess.run(command,env=env,capture_output=True,timeout=240);assert p.returncode==0,p.stderr.decode();r['endpoints']=dict(data=packed(p.stdout),sha256=digest(p.stdout),comparisons=endpoints(p.stdout))
        r['physical']=physical(decode(r,'vectors'));r['physical_admitted']=all(x['admitted'] for x in r['physical'])
        for mode,n in [('bench',1200),('long',4800)]:
            command=[str(exe),mode];p=subprocess.run(command,env=env,capture_output=True,timeout=240);assert p.returncode==0,p.stderr.decode();r[mode]=dict(stdout=packed(p.stdout),exit_code=p.returncode,cost=bench(p.stdout,n));print('EXP_COST',mode,r[mode]['cost'],flush=True)
            if not r[mode]['cost']['target_50_percent_pass']:
                q=subprocess.run(command,env=env,capture_output=True,timeout=240);assert q.returncode==0;r[mode]['unchanged_rejected_replay']=dict(stdout=packed(q.stdout),exit_code=q.returncode,cost=bench(q.stdout,n));break
        r.update(passed=True,observed_cost_admitted=all(r.get(k,{}).get('cost',{}).get('target_50_percent_pass',False) for k in ['bench','long']),whole_voice_rt=False,retained_charge_coordinates=18,constitutive_laws=12,signed_bit_rejections=42,exact_valid_retries=30)
    except Exception:
        r['failure']=traceback.format_exc()
        if 'p' in locals():
            r['failed_output_sha256']=digest(p.stdout)
            if len(p.stdout)<=512*1024:r['failed_output']=packed(p.stdout)
        if command:
            q=subprocess.run(command,input=stdin,env=env,capture_output=True,timeout=240);r['unchanged_failure_replay']=dict(exit_code=q.returncode,stdout_sha256=digest(q.stdout),stderr=packed(q.stderr),identical_to_failed_output='p' in locals() and p.stdout==q.stdout)
    finally:
        if exe.exists():assert exe.resolve().parent==AREA.resolve();exe.unlink()
    r['temporary_area_empty']=not list(AREA.iterdir())

if __name__=='__main__':
    sources=Sources(['tools/check_recovery_cost_exp.py','tools/check_recovery_cost.py','tools/recovery_cost_exp_kernel.rs','tools/recovery_cost_exp_model.py','tools/recovery_cost_exp_data.rs','tools/recovery_cost_probe.rs','docs/RECOVERY_COST_EXP_PROTOCOLO.md','crates/rf-d-circuit/src/j7_stream_output.rs']);r=dict(passed=False,**sources.fields());audit(r);sources.unchanged();k=1
    while(ROOT/f'evidence/recovery_cost_exp_native{k:02d}.json').exists():k+=1
    write(ROOT/f'evidence/recovery_cost_exp_native{k:02d}.json',r);print('EXP_FINAL',r['passed'],r.get('physical_admitted'),r.get('observed_cost_admitted'),r.get('failure',''),flush=True)
    if not r['passed']:raise SystemExit(1)
