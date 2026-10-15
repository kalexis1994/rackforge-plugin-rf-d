"""Exercise the moved stage boundary in both full and residual modes."""
import base64,json,os,subprocess,traceback
from prepare_dual_chain import ROOT,sha,write
from check_vco_phase import COMPILER,LIB
from check_hybrid_voice import packed,unpack
def main():
    out=ROOT/'evidence/hybrid_stamp_guards01.json';assert not out.exists();work=ROOT/'tmp/lab-current';assert not list(work.iterdir())
    names=['tools/check_hybrid_stamp_guards.py','tools/hybrid_stamp_guards.rs','tools/prepare_shared_candidate.py','crates/rf-d-circuit/src/prepared_hybrid_voice.rs','crates/rf-d-circuit/src/prepared_voice_chain.rs','crates/rf-d-circuit/src/prepared_contour_residual.rs','crates/rf-d-circuit/src/prepared_chain_charge.rs','evidence/hybrid_schur_native04.json']
    r=dict(passed=False,source_sha256={n:sha(ROOT/n) for n in names});old=json.loads((ROOT/'evidence/hybrid_schur_native04.json').read_text(encoding='utf8'));seed=work/'seed.bin';seed.write_bytes(unpack(old['projected_seed']))
    env=dict(os.environ,PATH='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+os.environ['PATH']);exe=work/'guards.exe'
    command=[COMPILER,'--edition=2021','-C','opt-level=2','-C','strip=symbols','-C','link-arg=-Wl,--stack,33554432','-A','unused_imports','-A','dead_code',str(ROOT/'tools/hybrid_stamp_guards.rs'),'--extern','rf_d_circuit='+str(LIB),'-o',str(exe)];last=None
    try:
        last=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=120);assert last.returncode==0,last.stderr.decode(errors='replace');command=[str(exe),str(seed)];last=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=120);assert last.returncode==0,last.stderr.decode(errors='replace');assert last.stdout==b'GUARDS,26,exact_retry=true\n',last.stdout;r.update(passed=True,invalid_stage_cases=26,exact_retries=26,stdout=packed(last.stdout))
    except Exception:
        r.update(failure=traceback.format_exc(),failed_sources=packed(json.dumps({n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in names},sort_keys=True).encode()),failed_command=command)
        if last:r['failed_process']=dict(exit_code=last.returncode,stdout=packed(last.stdout),stderr=last.stderr.decode(errors='replace'))
        p=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=120);r['unchanged_replay']=dict(exit_code=p.returncode,stdout=packed(p.stdout),stderr=p.stderr.decode(errors='replace'))
    assert all(sha(ROOT/n)==h for n,h in r['source_sha256'].items())
    for p in list(work.iterdir()):assert p.is_file() and p.resolve().parent==work.resolve();p.unlink()
    r['temporary_area_empty']=not list(work.iterdir());write(out,r);print('STAMP_GUARDS',r['passed'],r.get('failure',''),flush=True)
    if not r['passed']:raise SystemExit(1)
if __name__=='__main__':main()
