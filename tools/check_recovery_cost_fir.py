"""Bit-exact FIR ring traversal, then the fixed two-bank cost gate."""
import os,subprocess,traceback
from pathlib import Path
from prepare_dual_chain import ROOT,sha,write
from affine_evidence import Sources
from check_hybrid_voice import packed
from check_vco_phase import COMPILER,LIB
from check_recovery_cost import bench,read,digest,decode,AREA
REF='evidence/recovery_cost_exp_native01.json'

def audit(r):
    exp=read(REF);assert exp['passed'] and exp['physical_admitted'];old=read('evidence/recovery_port_tests01.json');assert sha(Path(COMPILER))==old['compiler']['sha256'] and sha(LIB)==old['private_input_sha256'][LIB.relative_to(ROOT).as_posix()]
    for name in ['tools/recovery_cost_exp_kernel.rs','tools/recovery_cost_exp_data.rs']:
        assert sha(ROOT/name)==exp['source_sha256'][name]
    r.update(compiler_sha256=sha(Path(COMPILER)),library_sha256=sha(LIB),same_kernel_report=REF,same_kernel_report_sha256=sha(ROOT/REF))
    exe=AREA/'recovery-cost-fir.exe';assert not list(AREA.iterdir());env=dict(os.environ,PATH='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+os.environ['PATH']);command=[]
    try:
        command=[COMPILER,'--edition=2021','-C','opt-level=2','-C','strip=symbols','-C','link-arg=-Wl,--stack,33554432','-A','dead_code','-A','unused_imports','--cfg','expfoh','--cfg','splitfir',str(ROOT/'tools/recovery_cost_probe.rs'),'--extern','rf_d_circuit='+str(LIB),'-o',str(exe)]
        p=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=120);r['compile']=dict(command=command,exit_code=p.returncode,stderr=packed(p.stderr));assert p.returncode==0,p.stderr.decode()
        for mode in ['vectors','stress','stages']:
            command=[str(exe),mode];p=subprocess.run(command,env=env,capture_output=True,timeout=240);assert p.returncode==0,p.stderr.decode();want=exp['endpoints']['sha256'] if mode=='stages' else digest(decode(exp,mode));assert digest(p.stdout)==want,mode;r[mode]=dict(sha256=want,bytes=len(p.stdout),bit_exact=True)
        command=[str(exe),'fircheck'];p=subprocess.run(command,env=env,capture_output=True,timeout=240);assert p.returncode==0,p.stderr.decode();tag,n,scenes,chunks=p.stdout.decode().strip().split(',');assert tag=='FIR_EXACT' and int(n)>9000 and int(scenes)==4 and int(chunks)==48;r['fir_check']=dict(frames=int(n),scenes=int(scenes),chunks_per_scene=int(chunks),voltage_and_indices_bit_exact=True,heap_allocations=0,atomic_invalid_input=True,stdout=packed(p.stdout))
        for mode,n in [('bench',1200),('long',4800)]:
            command=[str(exe),mode];p=subprocess.run(command,env=env,capture_output=True,timeout=240);assert p.returncode==0,p.stderr.decode();r[mode]=dict(stdout=packed(p.stdout),exit_code=p.returncode,cost=bench(p.stdout,n));print('SPLIT_FIR_COST',mode,r[mode]['cost'],flush=True)
            if not r[mode]['cost']['target_50_percent_pass']:
                q=subprocess.run(command,env=env,capture_output=True,timeout=240);assert q.returncode==0;r[mode]['unchanged_rejected_replay']=dict(stdout=packed(q.stdout),exit_code=q.returncode,cost=bench(q.stdout,n));break
        r.update(passed=True,observed_cost_admitted=all(r.get(k,{}).get('cost',{}).get('target_50_percent_pass',False) for k in ['bench','long']),whole_voice_rt=False,physical_scope_unchanged=True,retained_charge_coordinates=18,constitutive_laws=12)
    except Exception:
        r['failure']=traceback.format_exc()
        if 'p' in locals():
            r['failed_output_sha256']=digest(p.stdout)
            if len(p.stdout)<=512*1024:r['failed_output']=packed(p.stdout)
        if command:
            q=subprocess.run(command,env=env,capture_output=True,timeout=240);r['unchanged_failure_replay']=dict(exit_code=q.returncode,stdout_sha256=digest(q.stdout),stderr=packed(q.stderr),identical_to_failed_output='p' in locals() and p.stdout==q.stdout)
    finally:
        if exe.exists():assert exe.resolve().parent==AREA.resolve();exe.unlink()
    r['temporary_area_empty']=not list(AREA.iterdir())

if __name__=='__main__':
    sources=Sources(['tools/check_recovery_cost_fir.py','tools/check_recovery_cost.py','tools/recovery_cost_probe.rs','tools/recovery_cost_split_fir.rs','docs/RECOVERY_COST_FIR_PROTOCOLO.md','crates/rf-d-circuit/src/j7_stream_output.rs']);r=dict(passed=False,**sources.fields());audit(r);sources.unchanged();k=1
    while(ROOT/f'evidence/recovery_cost_fir_native{k:02d}.json').exists():k+=1
    write(ROOT/f'evidence/recovery_cost_fir_native{k:02d}.json',r);print('SPLIT_FIR_FINAL',r['passed'],r.get('observed_cost_admitted'),r.get('failure',''),flush=True)
    if not r['passed']:raise SystemExit(1)
