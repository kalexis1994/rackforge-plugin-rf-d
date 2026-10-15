"""New-dimension solver guards; same temporary area and unchanged replays."""
import base64,json,os,subprocess,traceback
from pathlib import Path
from prepare_dual_chain import ROOT,sha,write
from check_vco_phase import COMPILER,LIB
from check_hybrid_voice import packed
OWN=['tools/check_ladder_voice_guard.py','tools/ladder_voice_guard.rs','crates/rf-d-circuit/src/ladder_voice_solver.rs','docs/LADDER_VOZ_PROTOCOLO.md','tools/check_hybrid_voice.py','tools/check_vco_phase.py','tools/prepare_dual_chain.py']
def main():
    work=ROOT/'tmp/lab-current';assert not list(work.iterdir());r=dict(passed=False,source_sha256={n:sha(ROOT/n) for n in OWN},compiler_sha256=sha(Path(COMPILER)),library_sha256=sha(LIB));exe=work/'guard.exe'
    env=dict(os.environ,PATH='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+os.environ['PATH']);command=[COMPILER,'--edition=2021','--cfg','laboratory','-C','opt-level=2','-C','strip=symbols','-C','link-arg=-Wl,--stack,33554432','-A','unused_imports','-A','dead_code',str(ROOT/'tools/ladder_voice_guard.rs'),'--extern','rf_d_circuit='+str(LIB),'-o',str(exe)];last=None
    try:
        last=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=120);assert last.returncode==0,last.stderr.decode(errors='replace')
        command=[str(exe)];last=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=120);assert last.returncode==0,last.stderr.decode(errors='replace')
        keys=['invalid_cases','exact_invalid_retries','coefficient_entries','fill_swap_rhs_fixtures','capacity_retries','factor_overflow_retries','legal_edge_retries'];r['local']=dict(zip(keys,map(int,last.stdout.decode().strip().split(',')[1:])));r['stdout']=packed(last.stdout);r['passed']=True
    except Exception:
        r.update(failure=traceback.format_exc(),failed_sources=packed(json.dumps({n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in OWN},sort_keys=True).encode()),failed_command=command)
        if last is not None:r['failed_process']=dict(exit_code=last.returncode,stdout=packed(last.stdout),stderr=last.stderr.decode(errors='replace'))
        replay=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=120);r['unchanged_replay']=dict(exit_code=replay.returncode,stdout=packed(replay.stdout),stderr=replay.stderr.decode(errors='replace'))
    assert all(sha(ROOT/n)==h for n,h in r['source_sha256'].items())
    for p in list(work.iterdir()):assert p.is_file() and p.resolve().parent==work.resolve();p.unlink()
    r['temporary_area_empty']=not list(work.iterdir());k=1
    while(ROOT/f'evidence/ladder_voice_guard{k:02d}.json').exists():k+=1
    write(ROOT/f'evidence/ladder_voice_guard{k:02d}.json',r);print('LADDER_VOICE_GUARD',r['passed'],r.get('local'),r.get('failure',''),flush=True)
    if not r['passed']:raise SystemExit(1)
if __name__=='__main__':main()
