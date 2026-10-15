"""Evaluation phases before Stage return; profile is not an admission benchmark."""
import base64,json,os,subprocess,traceback
from pathlib import Path
from prepare_dual_chain import ROOT,sha,write
from check_vco_phase import COMPILER,LIB
from check_hybrid_voice import packed,unpack,parse
from check_hybrid_schur import comparison
from check_split_ladder import OWN as BASE
OWN=list(dict.fromkeys(BASE+['tools/profile_split_ladder.py','tools/split_ladder_profile.rs','crates/rf-d-circuit/src/profiled_split_ladder_voice.rs','evidence/split_ladder_native01.json']))
def main():
    work=ROOT/'tmp/lab-current';assert not list(work.iterdir());r=dict(passed=False,source_sha256={n:sha(ROOT/n) for n in OWN},compiler_sha256=sha(Path(COMPILER)),library_sha256=sha(LIB));old=json.loads((ROOT/'evidence/split_ladder_native01.json').read_text(encoding='utf8'));assert old['numerical_integration_verified']
    seed=work/'seed.bin';seed.write_bytes(unpack(old['projected_seed']));env=dict(os.environ,PATH='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+os.environ['PATH']);exe=work/'profile.exe'
    command=[COMPILER,'--edition=2021','--cfg','condensed','-C','opt-level=2','-C','strip=symbols','-C','link-arg=-Wl,--stack,33554432','-A','unused_imports','-A','dead_code',str(ROOT/'tools/split_ladder_profile.rs'),'--extern','rf_d_circuit='+str(LIB),'-o',str(exe)];last=None
    try:
        last=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=120);assert last.returncode==0,last.stderr.decode(errors='replace')
        command=[str(exe),str(seed),'16777216'];last=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=300);assert last.returncode==0,last.stderr.decode(errors='replace')
        raw=last.stdout;g,_,f=parse(raw);control=unpack(old['profiles'][3]['stdout']);og,_,_=parse(control);r['comparison']=comparison(g,og,raw,control);r['measurement']=f;r['stdout']=packed(raw)
        values=list(map(int,next(x for x in raw.decode().splitlines() if x.startswith('PROFILE,')).split(',')[1:]));assert len(values)==8
        r['timed_sections_s']=dict(zip(['coordinates','local_kernel','physical_increment','parent','parent_validation','reduced_projection','physical_transfer'],[v*1e-9 for v in values[:7]]));r['evaluations']=values[7];r['timing_includes_exact_replays']=True;r['timers_end_before_stage_return']=True;r['admission_benchmark']=False;r['passed']=True
    except Exception:
        r.update(failure=traceback.format_exc(),failed_sources=packed(json.dumps({n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in OWN},sort_keys=True).encode()),failed_command=command)
        if last is not None:r['failed_process']=dict(exit_code=last.returncode,stdout=packed(last.stdout),stderr=last.stderr.decode(errors='replace'))
        replay=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=300);r['unchanged_replay']=dict(exit_code=replay.returncode,stdout=packed(replay.stdout),stderr=replay.stderr.decode(errors='replace'))
    assert all(sha(ROOT/n)==h for n,h in r['source_sha256'].items())
    for p in list(work.iterdir()):assert p.is_file() and p.resolve().parent==work.resolve();p.unlink()
    r['temporary_area_empty']=not list(work.iterdir());k=1
    while (ROOT/f'evidence/split_ladder_profile{k:02d}.json').exists():k+=1
    write(ROOT/f'evidence/split_ladder_profile{k:02d}.json',r);print('SPLIT_PROFILE_DETAIL',r['passed'],r.get('timed_sections_s'),r.get('failure',''),flush=True)
    if not r['passed']:raise SystemExit(1)
if __name__=='__main__':main()
