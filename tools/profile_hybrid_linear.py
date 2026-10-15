"""Bounded full-trajectory profiling; timers are not a speed admission."""
import base64,json,os,subprocess,time,traceback
from prepare_dual_chain import ROOT,sha,write
from check_vco_phase import COMPILER,LIB
from check_hybrid_voice import packed,unpack,parse,US
from check_hybrid_schur import comparison
from prepare_hybrid_linear import derive
OWN=['tools/prepare_hybrid_linear.py','tools/profile_hybrid_linear.py',*derive()]
def main():
    work=ROOT/'tmp/lab-current';work.mkdir(exist_ok=True);assert not list(work.iterdir())
    r=dict(passed=False,source_sha256={n:sha(ROOT/n) for n in OWN},compiler_sha256=sha(__import__('pathlib').Path(COMPILER)),library_sha256=sha(LIB))
    previous=json.loads((ROOT/'evidence/hybrid_stamp_native09.json').read_text(encoding='utf8'));old=previous['profiles'][2]
    seed=work/'seed.bin';seed.write_bytes(unpack(previous['projected_seed']))
    env=dict(os.environ,PATH='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+os.environ['PATH'])
    command=[COMPILER,'--edition=2021','-C','opt-level=2','-C','strip=symbols','-C','link-arg=-Wl,--stack,33554432','-A','unused_imports','-A','dead_code','--cfg','condensed','--cfg','timings',str(ROOT/'tools/hybrid_linear_probe.rs'),'--extern','rf_d_circuit='+str(LIB),'-o',str(work/'profile.exe')]
    last=None
    try:
        last=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=120);assert last.returncode==0,last.stderr.decode(errors='replace')
        command=[str(work/'profile.exe'),str(seed),str(32*US)];last=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=300)
        r['stdout']=packed(last.stdout);r['stderr']=last.stderr.decode(errors='replace');assert last.returncode==0,r['stderr']
        g,_,f=parse(last.stdout);og,_,_=parse(unpack(old['stdout']));r['comparison']=comparison(g,og,last.stdout,unpack(old['stdout']));r['measurement']=f
        line=next(x for x in last.stdout.decode().splitlines() if x.startswith('PROFILE,'));values=[int(x)/1e9 for x in line.split(',')[1:]]
        r['timed_sections_s']=dict(zip(['newton_full_electrical','newton_matrix_assembly','csr_validation','factorization','initial_triangular_solve','initial_backward','refinement'],values))
        r['timers_include_four_exact_replays']=True;r['unattributed_includes_line_search_and_failed_solves']=True;r['passed']=True
    except Exception:
        r['failure']=traceback.format_exc();r['failed_sources']=packed(json.dumps({n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in OWN},sort_keys=True).encode());r['failed_command']=command
        if last:r['failed_process']=dict(exit_code=last.returncode,stdout=packed(last.stdout),stderr=last.stderr.decode(errors='replace'))
        retry=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=300);r['unchanged_replay']=dict(exit_code=retry.returncode,stdout=packed(retry.stdout),stderr=retry.stderr.decode(errors='replace'))
    for p in work.iterdir():assert p.is_file() and p.resolve().parent==work.resolve();p.unlink()
    r['temporary_area_empty']=not list(work.iterdir());write(ROOT/'evidence/hybrid_linear_profile01.json',r)
    print('LINEAR_PROFILE',r['passed'],r.get('timed_sections_s'),r.get('failure',''),flush=True)
    assert r['passed']
if __name__=='__main__':main()
