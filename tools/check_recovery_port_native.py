"""Native twelve-junction agreement, transactional rejections and observed cost."""
import json,os,subprocess,traceback,platform
from pathlib import Path
import numpy as np
from prepare_dual_chain import ROOT,sha,write
from affine_evidence import Sources
from check_hybrid_voice import packed
from check_vco_phase import COMPILER,LIB
from recovery_port_input_model import cases,build,simulate
AREA=ROOT/'tmp/lab-current'

def summarize_bench(raw):
    rows=[z.split(',') for z in raw.decode().splitlines() if z.startswith('BLOCK,')]
    # FIR has 384 input-sample latency: first 1024 inputs yield 80, then128.
    assert len(rows)==1200 and all(int(z[1])==k and int(z[3])==0 and int(z[4])==(80 if k==0 else 128) for k,z in enumerate(rows))
    times=np.array([float(z[2]) for z in rows]);budget=128/48000
    return dict(blocks=1200,first_included=True,block_seconds=budget,median_s=float(np.median(times)),p99_s=float(np.quantile(times,.99)),max_s=float(max(times)),deadline_misses=int(sum(times>budget)),target_50_percent_pass=bool(np.all(times<=budget*.5)),heap_allocations=0,includes_kernel_and_fir=True,excludes_vco_contours_generator_and_io=True)

def audit(r):
    old=json.loads((ROOT/'evidence/charge_control_tests01.json').read_text(encoding='utf8'));assert sha(Path(COMPILER))==old['compiler']['sha256'] and sha(LIB)==old['private_input_sha256'][LIB.relative_to(ROOT).as_posix()]
    exe=AREA/'recovery-native.exe';env=dict(os.environ,PATH='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+os.environ['PATH']);r.update(compiler_sha256=sha(Path(COMPILER)),library_sha256=sha(LIB),platform=platform.platform());command=[]
    try:
        command=[COMPILER,'--edition=2021','-C','opt-level=2','-C','strip=symbols','-C','link-arg=-Wl,--stack,33554432','-A','dead_code','-A','unused_imports',str(ROOT/'tools/recovery_port_probe.rs'),'--extern','rf_d_circuit='+str(LIB),'-o',str(exe)]
        p=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=120);r['compile']=dict(exit_code=p.returncode,stderr=packed(p.stderr));assert p.returncode==0,p.stderr.decode()
        command=[str(exe),'vectors'];p=subprocess.run(command,env=env,capture_output=True,timeout=240);r['vectors']=dict(exit_code=p.returncode,stdout=packed(p.stdout),stderr=packed(p.stderr));assert p.returncode==0,p.stderr.decode();a=np.frombuffer(p.stdout,dtype='<f8').reshape(3,1537,93);records=[]
        for index in range(3):
            v=a[index];m=build(cases()[index]);expected,it=simulate(m,v[:,1],v[:,2]);error=float(np.max(abs(expected-v[:,25:])));panel=float(max(abs((expected[:,66]-.5*v[:,2])/39250-v[:,6])));qe=float(np.max(abs((v[:,25:]-m['dc'])@m['a'].T-v[:,7:25])));assert error<=1e-10 and panel<=1e-14 and qe<=1e-11,(error,panel,qe)
            assert np.array_equal(v[:,3:6].view('<u8'),v[:,[25+66,25+6,25+61]].view('<u8'))
            records.append(dict(index=index,node_error_v=error,panel_error_a=panel,charge_error_v=qe,max_root_iterations=it))
        r.update(implementation_comparisons=records,signed_bit_reject_fixtures=24,exact_retries=24,root_budget_rejection_included=True,heap_allocations_vectors=0,ports_match_nodes_by_bits=True)
        command=[str(exe),'bench'];p=subprocess.run(command,env=env,capture_output=True,timeout=240);r['bench']=dict(exit_code=p.returncode,stdout=packed(p.stdout),stderr=packed(p.stderr));assert p.returncode==0,p.stderr.decode()
        r['cost']=summarize_bench(p.stdout)
        r.update(passed=True,whole_voice_rt=False,physical_domain_admission=False)
    except Exception:
        r['failure']=traceback.format_exc()
        if exe.exists() and command and command[0]==str(exe):
            p=subprocess.run(command,env=env,capture_output=True,timeout=240);r['unchanged_replay']=dict(exit_code=p.returncode,stdout=packed(p.stdout),stderr=packed(p.stderr))
    finally:
        if exe.exists():assert exe.resolve().parent==AREA.resolve();exe.unlink()
    r['temporary_area_empty']=not list(AREA.iterdir())

def main():
    names=['tools/check_recovery_port_native.py','tools/recovery_port_probe.rs','tools/recovery_port_kernel.rs','tools/recovery_port_input_data.rs','tools/recovery_port_input_model.py','crates/rf-d-circuit/src/j7_stream_output.rs'];sources=Sources(names);r=dict(passed=False,**sources.fields());audit(r);sources.unchanged();k=1
    while(ROOT/f'evidence/recovery_port_native{k:02d}.json').exists():k+=1
    write(ROOT/f'evidence/recovery_port_native{k:02d}.json',r);print('RECOVERY_NATIVE',r['passed'],r.get('cost'),r.get('failure',''),flush=True)
    if not r['passed']:raise SystemExit(1)
if __name__=='__main__':main()
