"""Compile four public API/allocator tests against the new library, without Cargo."""
import base64,json,os,re,subprocess,time,traceback
from pathlib import Path
from prepare_vco1_portable import ROOT,sha,write
from joint_cycles_analysis import require
from conditioned_portable_native import LIB

def main():
    work=ROOT/'references-local/conditioned-portable-tests01';require(not work.exists(),'exclusive public tests');work.mkdir();exe=work/'tests.exe';build=json.loads((ROOT/'evidence/voice_conditioned_portable_library01.json').read_text(encoding='utf8'));require(build['passed'] and sha(ROOT/LIB)==build['outputs'][0]['sha256'],'library identity');compiler=build['compiler'];env=os.environ.copy();env['PATH']='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+env['PATH'];env['RUST_MIN_STACK']='33554432';names=['tools/test_conditioned_portable.py','crates/rf-d-circuit/tests/conditioned_portable.rs','crates/rf-d-circuit/tests/support/conditioned_seed.rs','crates/rf-d-circuit/tests/support/mixer_chain_lab.rs','docs/CONJUNTO_PORTABLE_PROTOCOLO.md','evidence/voice_conditioned_portable_library01.json'];before={n:sha(ROOT/n) for n in names};used={LIB:sha(ROOT/LIB)};commands=[];r=dict(passed=False,source_sha256=before,private_used_sha256=used,compiler=compiler,lab_stack_bytes=33554432)
    def run(cmd,limit):
        t=time.perf_counter();q=subprocess.run(cmd,cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf8',timeout=limit,creationflags=subprocess.CREATE_NO_WINDOW);out=dict(command=cmd,exit_code=q.returncode,stdout=q.stdout,stderr=q.stderr,wall_s=time.perf_counter()-t);commands.append(out);return out
    try:
        q=run([compiler['path'],'--edition=2021','--test','-C','opt-level=2','-C','strip=symbols','-C','link-arg=-Wl,--stack,33554432','crates/rf-d-circuit/tests/conditioned_portable.rs','--extern','rf_d_circuit='+str(ROOT/LIB),'-o',str(exe)],120)
        if q['exit_code']:run(q['command'],120);require(False,'public test compile rejection')
        q=run([str(exe),'--nocapture','--test-threads=1'],600)
        if q['exit_code']:run(q['command'],600);require(False,'public API test rejection')
        m=re.search(r'PORTABLE_MEMORY,stamp=(\d+),workspace=(\d+),engine=(\d+),checkpoint=(\d+)',q['stdout']);require(m is not None and 'test result: ok. 4 passed; 0 failed' in q['stdout'],'four public tests');stamp,workspace,engine,checkpoint=map(int,m.groups());require(workspace==2*stamp and workspace<=4*1024**2 and stamp<=2*1024**2 and max(engine,checkpoint)<=16*1024,'measured memory')
        for s in ['PORTABLE_HEAP,workspace_successes=4,workspace_rejections=1,allocations=0','PORTABLE_HEAP,temporal_successes=2,temporal_rejections=2,allocations=0','PORTABLE_SHARED_SCRATCH,successes=3,restore_matches=1,allocations=0']:require(s in q['stdout'],'heap scope '+s)
        r.update(passed=True,native_test_count=4,stamp_bytes=stamp,workspace_bytes=workspace,engine_bytes=engine,checkpoint_bytes=checkpoint,heap_measured=True,measured_successful_processing_calls=9,measured_rejected_processing_calls=3,processing_allocations=0,deadline_measured=False,real_time=False)
    except Exception:r['failure']=traceback.format_exc();r['failed_source_base64']={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in names}
    r.update(commands=commands,source_sha256_after={n:sha(ROOT/n) for n in names},private_used_sha256_after={LIB:sha(ROOT/LIB)},outputs=[dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p),bytes=p.stat().st_size) for p in sorted(work.iterdir()) if p.is_file()]);require(before==r['source_sha256_after'] and used==r['private_used_sha256_after'],'stable API tests');write('evidence/voice_conditioned_portable_tests_native01.json',r);print('PUBLIC_API_TESTS',r['passed'],r.get('failure',''),flush=True)
if __name__=='__main__':main()
