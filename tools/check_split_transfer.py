"""Bounded metadata, finite-overflow and atomic-publication transfer guards."""
import base64,json,os,subprocess,traceback
from pathlib import Path
from prepare_dual_chain import ROOT,sha,write
from check_vco_phase import COMPILER,LIB
from check_hybrid_voice import packed,unpack
from check_split_ladder import OWN as BASE
OWN=list(dict.fromkeys(BASE+['tools/check_split_transfer.py','tools/split_ladder_transfer.rs','evidence/split_ladder_native01.json']))
def main():
    work=ROOT/'tmp/lab-current';assert not list(work.iterdir());r=dict(passed=False,source_sha256={n:sha(ROOT/n) for n in OWN},compiler_sha256=sha(Path(COMPILER)),library_sha256=sha(LIB));old=json.loads((ROOT/'evidence/split_ladder_native01.json').read_text(encoding='utf8'));data=unpack(old['local_input']).splitlines(keepends=True)[0];r['input']=packed(data)
    env=dict(os.environ,PATH='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+os.environ['PATH']);exe=work/'transfer.exe';command=[COMPILER,'--edition=2021','-C','opt-level=2','-C','strip=symbols','-C','link-arg=-Wl,--stack,33554432','-A','unused_imports','-A','dead_code',str(ROOT/'tools/split_ladder_transfer.rs'),'--extern','rf_d_circuit='+str(LIB),'-o',str(exe)];last=None;stdin=None
    try:
        last=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=120);assert last.returncode==0,last.stderr.decode(errors='replace')
        command=[str(exe)];stdin=data;last=subprocess.run(command,cwd=ROOT,env=env,input=stdin,capture_output=True,timeout=120);assert last.returncode==0,last.stderr.decode(errors='replace')
        keys=['invalid_cases','exact_retries','atomic_rejections','finite_overflow_cases','other_low_point_cases'];r['local']=dict(zip(keys,map(int,last.stdout.decode().strip().split(',')[1:])));r['stdout']=packed(last.stdout);r['passed']=True
    except Exception:
        r.update(failure=traceback.format_exc(),failed_sources=packed(json.dumps({n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in OWN},sort_keys=True).encode()),failed_command=command)
        if last is not None:r['failed_process']=dict(exit_code=last.returncode,stdout=packed(last.stdout),stderr=last.stderr.decode(errors='replace'))
        replay=subprocess.run(command,cwd=ROOT,env=env,input=stdin,capture_output=True,timeout=120);r['unchanged_replay']=dict(exit_code=replay.returncode,stdout=packed(replay.stdout),stderr=replay.stderr.decode(errors='replace'))
    assert all(sha(ROOT/n)==h for n,h in r['source_sha256'].items())
    for p in list(work.iterdir()):assert p.is_file() and p.resolve().parent==work.resolve();p.unlink()
    r['temporary_area_empty']=not list(work.iterdir());k=1
    while(ROOT/f'evidence/split_ladder_transfer{k:02d}.json').exists():k+=1
    write(ROOT/f'evidence/split_ladder_transfer{k:02d}.json',r);print('SPLIT_TRANSFER',r['passed'],r.get('local'),r.get('failure',''),flush=True)
    if not r['passed']:raise SystemExit(1)
if __name__=='__main__':main()
