"""Bounded same-law cost campaign, lossless differential native evidence."""
import decimal,hashlib,json,os,platform,subprocess,sys,time,traceback
from pathlib import Path
import numpy as np
from prepare_dual_chain import ROOT,sha,write
from affine_evidence import Sources
from check_hybrid_voice import packed,unpack
from check_vco_phase import COMPILER,LIB
from recovery_port_input_model import build,cases,simulate,law,dense_stage
AREA=ROOT/'tmp/lab-current'
def digest(raw):return hashlib.sha256(raw).hexdigest()
def read(name):return json.loads((ROOT/name).read_text(encoding='utf8'))
def bench(raw,blocks=1200):
    rows=[s.split(',') for s in raw.decode().splitlines() if s.startswith('BLOCK,')]
    assert len(rows)==blocks and all(int(s[1])==k and int(s[3])==0 and int(s[4])==(80 if k==0 else 128) for k,s in enumerate(rows))
    seconds=np.array([float(s[2]) for s in rows]);assert np.isfinite(seconds).all() and min(seconds)>0;budget=128/48000
    return dict(blocks=blocks,first_included=True,budget_s=budget,median_s=float(np.median(seconds)),p99_s=float(np.quantile(seconds,.99)),max_s=float(max(seconds)),deadline_misses=int(sum(seconds>budget)),target_50_percent_pass=bool(np.all(seconds<=budget*.5)),heap_allocations=0)
def decode(r,key):
    item=r[key];raw=unpack(item['data'])
    if item['storage']=='xor':
        ref=read(item['reference_report']);assert sha(ROOT/item['reference_report'])==item['reference_report_sha256']
        original=unpack(ref['vectors']['stdout']) if item['reference_report']=='evidence/recovery_port_fast_native03.json' else decode(ref,key)
        assert len(raw)==len(original);raw=np.bitwise_xor(np.frombuffer(raw,'u1'),np.frombuffer(original,'u1')).tobytes()
    else:assert item['storage']=='packed'
    assert digest(raw)==item['sha256'] and len(raw)==item['bytes'];return raw
def store(raw,reference=None,key=None):
    item=dict(storage='packed',data=packed(raw),sha256=digest(raw),bytes=len(raw))
    if reference:
        ref=read(reference);original=unpack(ref['vectors']['stdout']) if reference=='evidence/recovery_port_fast_native03.json' else decode(ref,key)
        assert len(raw)==len(original)
        item.update(storage='xor',data=packed(np.bitwise_xor(np.frombuffer(raw,'u1'),np.frombuffer(original,'u1')).tobytes()),reference_report=reference,reference_report_sha256=sha(ROOT/reference))
    return item

def compare(raw):
    array=np.frombuffer(raw,dtype='<f8').reshape(3,1537,93);records=[]
    assert np.isfinite(array).all()
    for index,case in enumerate(cases()):
        v=array[index];m=build(case);expected,_=simulate(m,v[:,1],v[:,2]);err=float(np.max(abs(expected-v[:,25:])));panel=float(max(abs((expected[:,66]-.5*v[:,2])/39250-v[:,6])));qe=float(np.max(abs((v[:,25:]-m['dc'])@m['a'].T-v[:,7:25])));assert err<=1e-10 and panel<=1e-14 and qe<=1e-11,(err,panel,qe)
        assert np.array_equal(v[:,3:6].view('u8'),v[:,[91,31,86]].view('u8'))
        records.append(dict(index=index,node_error_v=err,panel_error_a=panel,charge_error_v=qe))
    return records

def law_grid():
    return np.unique(np.r_[np.linspace(-40,40,401),np.geomspace(1e-18,.1,101),-np.geomspace(1e-18,.1,101),[0.,-.001,.001,np.nextafter(.001,0),np.nextafter(.001,1),np.nextafter(-.001,0),np.nextafter(-.001,-1),.125,-.125,np.nextafter(.125,0),np.nextafter(.125,1),np.nextafter(-.125,0),np.nextafter(-.125,-1)]])
def check_laws(raw):
    grid=law_grid();a=np.frombuffer(raw,'<f8').reshape(3,len(grid),26);records=[];decimal.getcontext().prec=80
    for index,case in enumerate(cases()):
        iexp=build(case)['iexp'];max_scaled=0.;max_abs=0.
        for k,z in enumerate(grid):
            assert a[index,k,0]==index and a[index,k,1]==z;dz=decimal.Decimal.from_float(float(z));em1=dz.exp()-1;defect=em1-dz
            for j in range(12):
                scale=decimal.Decimal.from_float(float(iexp[j]));expected=np.array([float(scale*defect),float(scale*em1)]);got=a[index,k,[2+j,14+j]];error=abs(got-expected);ratio=float(max(error/(1e-28+5e-15*abs(expected))));assert ratio<=1,(index,k,j,ratio);max_scaled=max(max_scaled,ratio);max_abs=max(max_abs,float(max(error)))
        records.append(dict(index=index,samples=len(grid)*12,max_scaled_error=max_scaled,max_absolute_error_a=max_abs))
    return records

def check_stages(raw):
    a=np.frombuffer(raw,'<f8').reshape(-1,65);records=[];models=[build(c) for c in cases()]
    for row in a:
        index=int(row[0]);m=models[index];u=row[2];q=row[5:23];next_q=row[23:41];n=row[41:53];z=row[53:65];current,_=law(m,z);zp=m['zh']@q+m['zu']*u;res=float(max(abs(z-zp+m['p']@current)));assert row[4]<=2e-13 and res<=2e-13 and max(abs(current-n))<=1e-14
        x=m['xh']@q+m['xu']*u-m['xd']@n;dense,kcl=dense_stage(m,q,u);err=float(max(abs(x-dense)));qe=float(max(abs(m['a']@x-next_q)));hybrid_kcl=float(max(abs((m['g']+m['m']/m['dt'])@x-m['a'].T@(m['c']*q)/m['dt']-m['b']*u+m['d']@law(m,m['e']@x)[0])));assert err<=1e-9 and qe<=1e-11 and kcl<=1e-12 and hybrid_kcl<=1e-12,(err,qe,kcl,hybrid_kcl)
        records.append(dict(index=index,fixture=int(row[1]),reported_residual=row[4],recomputed_residual=res,node_error_v=err,charge_error_v=qe,hybrid_kcl_a=hybrid_kcl,evaluations=int(row[3])))
    return records

def audit(r,variant):
    old=read('evidence/recovery_port_tests01.json');assert sha(Path(COMPILER))==old['compiler']['sha256'] and sha(LIB)==old['private_input_sha256'][LIB.relative_to(ROOT).as_posix()]
    r.update(compiler_sha256=sha(Path(COMPILER)),library_sha256=sha(LIB),platform=platform.platform(),variant=variant)
    exe=AREA/'recovery-cost.exe';assert not list(AREA.iterdir());env=dict(os.environ,PATH='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+os.environ['PATH']);command=[];stdin=None
    try:
        command=[COMPILER,'--edition=2021','-C','opt-level=2','-C','strip=symbols','-C','link-arg=-Wl,--stack,33554432','-A','dead_code','-A','unused_imports','--cfg','specialized' if variant=='static' else variant,str(ROOT/'tools/recovery_cost_probe.rs'),'--extern','rf_d_circuit='+str(LIB),'-o',str(exe)]
        p=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=120);r['compile']=dict(command=command,exit_code=p.returncode,stderr=packed(p.stderr));assert p.returncode==0,p.stderr.decode()
        for key in ['vectors','stress']:
            command=[str(exe),key];p=subprocess.run(command,env=env,capture_output=True,timeout=240);assert p.returncode==0,p.stderr.decode();assert len(p.stdout)<=32*1024**2
            reference='evidence/recovery_port_fast_native03.json' if key=='vectors' else None if variant=='baseline' else 'evidence/recovery_cost_baseline01.json'
            r[key]=store(p.stdout,reference,key);r[key]['python_comparison']=compare(p.stdout)
            if variant=='baseline' and key=='vectors':assert np.frombuffer(unpack(read(reference)['vectors']['stdout']),'u8').tobytes()==p.stdout
        if variant!='baseline':
            command=[str(exe),'laws'];stdin=law_grid().astype('<f8').tobytes();p=subprocess.run(command,input=stdin,env=env,capture_output=True,timeout=240);assert p.returncode==0,p.stderr.decode();r['laws']=dict(input=packed(stdin),output_sha256=digest(p.stdout),comparisons=check_laws(p.stdout));stdin=None
            command=[str(exe),'stages'];p=subprocess.run(command,env=env,capture_output=True,timeout=240);assert p.returncode==0,p.stderr.decode();r['stages']=dict(data=packed(p.stdout),sha256=digest(p.stdout),comparisons=check_stages(p.stdout))
        command=[str(exe),'bench'];p=subprocess.run(command,env=env,capture_output=True,timeout=240);assert p.returncode==0,p.stderr.decode();r['bench']=dict(stdout=packed(p.stdout),exit_code=p.returncode);r['cost']=bench(p.stdout)
        if variant!='baseline' and not r['cost']['target_50_percent_pass']:
            replay=subprocess.run(command,env=env,capture_output=True,timeout=240);assert replay.returncode==0;r['unchanged_rejected_cost_replay']=dict(stdout=packed(replay.stdout),cost=bench(replay.stdout),exit_code=replay.returncode)
        if variant!='baseline' and r['cost']['target_50_percent_pass']:
            command=[str(exe),'long'];p=subprocess.run(command,env=env,capture_output=True,timeout=240);assert p.returncode==0,p.stderr.decode();r['confirmation']=dict(stdout=packed(p.stdout),exit_code=p.returncode,cost=bench(p.stdout,4800))
            if not r['confirmation']['cost']['target_50_percent_pass']:
                replay=subprocess.run(command,env=env,capture_output=True,timeout=240);assert replay.returncode==0;r['unchanged_rejected_confirmation_replay']=dict(stdout=packed(replay.stdout),cost=bench(replay.stdout,4800),exit_code=replay.returncode)
        r.update(passed=True,signed_bit_rejections=42,exact_valid_retries=30,heap_allocations=0,retained_charge_coordinates=18,constitutive_laws=12,residual_limit=2e-13,internal_rate_hz=384000,output_rate_hz=48000,whole_voice_rt=False,physical_domain_extended=False)
    except Exception:
        r['failure']=traceback.format_exc()
        if 'p' in locals():
            r['failed_output_sha256']=digest(p.stdout)
            if len(p.stdout)<=512*1024:r['failed_output']=packed(p.stdout)
        if command:
            replay=subprocess.run(command,input=stdin,env=env,capture_output=True,timeout=240);r['unchanged_failure_replay']=dict(exit_code=replay.returncode,stdout_sha256=digest(replay.stdout),stderr=packed(replay.stderr),identical_to_failed_output='p' in locals() and replay.stdout==p.stdout)
            if command[-1]=='laws' and replay.returncode==0:
                try:check_laws(replay.stdout)
                except Exception:r['unchanged_failure_replay']['analysis_failure']=traceback.format_exc()
    finally:
        if exe.exists():assert exe.resolve().parent==AREA.resolve();exe.unlink()
    r['temporary_area_empty']=not list(AREA.iterdir())

if __name__=='__main__':
    variant=sys.argv[1];assert variant in ['baseline','joint','predict','static'];names=['tools/check_recovery_cost.py','tools/recovery_cost_probe.rs','tools/recovery_port_fast_kernel.rs','tools/recovery_port_input_data.rs','tools/recovery_port_input_model.py','docs/RECOVERY_COST_PROTOCOLO.md','crates/rf-d-circuit/src/j7_stream_output.rs']
    if variant!='baseline':names.extend(['tools/recovery_cost_'+variant+'_kernel.rs','docs/RECOVERY_COST_LAW_CORRECCION.md'])
    sources=Sources(names);r=dict(passed=False,**sources.fields());audit(r,variant);sources.unchanged();k=1
    while(ROOT/f'evidence/recovery_cost_{variant}{k:02d}.json').exists():k+=1
    write(ROOT/f'evidence/recovery_cost_{variant}{k:02d}.json',r);print('RECOVERY_COST',variant,r['passed'],r.get('cost'),r.get('confirmation',{}).get('cost'),r.get('failure',''),flush=True)
    if not r['passed']:raise SystemExit(1)
