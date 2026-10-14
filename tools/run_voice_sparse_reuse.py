"""Check reused numerical memory after partial preparation and factor failures."""
import base64,os,subprocess,time,traceback
from prepare_dual_chain import ROOT,sha,write
from run_dual_voice import COMPILER,LIB
def main():
    out=ROOT/'references-local/voice-sparse-reuse01';out.mkdir();receipt=ROOT/'evidence/voice_sparse_reuse01.json';assert not receipt.exists()
    names=['tools/voice_sparse_reuse.rs','tools/run_voice_sparse_reuse.py','crates/rf-d-circuit/src/dual_voice_solver.rs','crates/rf-d-circuit/src/sparse_ordered_voice_solver.rs'];hashes={n:sha(ROOT/n) for n in names}
    env=dict(os.environ,PATH='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+os.environ['PATH'])
    def run(cmd,label,timeout):
        start=time.monotonic();p=subprocess.run(cmd,cwd=ROOT,env=env,capture_output=True,timeout=timeout);(out/(label+'.stdout')).write_bytes(p.stdout);(out/(label+'.stderr')).write_bytes(p.stderr)
        return dict(exit_code=p.returncode,wall_s=time.monotonic()-start,command=cmd,stdout_sha256=sha(out/(label+'.stdout')),stderr_sha256=sha(out/(label+'.stderr')))
    exe=out/'reuse.exe';cmd=[COMPILER,'--edition=2021','-C','opt-level=2','-C','strip=symbols','-C','link-arg=-Wl,--stack,33554432','-A','dead_code',str(ROOT/'tools/voice_sparse_reuse.rs'),'--extern','rf_d_circuit='+str(LIB),'-o',str(exe)]
    r=dict(passed=False,source_sha256=hashes,library_sha256=sha(LIB))
    try:
        r['compile']=run(cmd,'compile',120);assert r['compile']['exit_code']==0
        cmd=[str(exe),str(ROOT/'references-local/dual-voice02/linear-1048576.bin')];r['run']=run(cmd,'run',60);assert r['run']['exit_code']==0
        assert len((out/'run.stdout').read_text(encoding='utf8').splitlines())==5;r['passed']=True;r['rejected_matrices']=5;r['exact_valid_direction_replays']=5
    except Exception:
        r['failure']=traceback.format_exc();r['source_base64']={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in names};r['unchanged_replay']=run(cmd,'unchanged-replay',120)
    assert hashes=={n:sha(ROOT/n) for n in names};r['private_sha256']={p.relative_to(ROOT).as_posix():sha(p) for p in out.iterdir() if p.is_file()};write(receipt,r);print('VOICE_SPARSE_REUSE',r['passed'],r.get('failure',''),flush=True)
    if not r['passed']:raise SystemExit(1)
if __name__=='__main__':main()
