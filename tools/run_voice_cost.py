"""Baseline cost of assembly versus linear solve on all admitted selected pairs."""
import base64,json,os,subprocess,time,traceback
from prepare_dual_chain import ROOT,sha,write
from run_dual_voice import COMPILER,LIB,OWN
def main():
    out=ROOT/'references-local/voice-cost01';receipt=ROOT/'evidence/voice_cost_profile01.json';assert not receipt.exists()
    names=sorted(set(OWN+['tools/voice_cost_bench.rs','tools/run_voice_cost.py','evidence/voice_cost_inputs01.json']))
    hashes={n:sha(ROOT/n) for n in names};snap={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in names};env=dict(os.environ,PATH='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+os.environ['PATH'])
    def run(cmd,label,timeout):
        start=time.monotonic();p=subprocess.run(cmd,cwd=ROOT,env=env,capture_output=True,timeout=timeout);(out/(label+'.stdout')).write_bytes(p.stdout);(out/(label+'.stderr')).write_bytes(p.stderr)
        return dict(exit_code=p.returncode,wall_s=time.monotonic()-start,command=cmd,stdout_sha256=sha(out/(label+'.stdout')),stderr_sha256=sha(out/(label+'.stderr')))
    exe=out/'bench.exe';cmd=[COMPILER,'--edition=2021','-C','opt-level=2','-C','strip=symbols','-C','link-arg=-Wl,--stack,33554432','-A','unused_imports','-A','dead_code',str(ROOT/'tools/voice_cost_bench.rs'),'--extern','rf_d_circuit='+str(LIB),'-o',str(exe)]
    r=dict(schema='rf-d/voice-cost/profile-v1',passed=False,source_sha256=hashes,library_sha256=sha(LIB));phase='compile'
    try:
        r['compile']=run(cmd,'compile',120);assert r['compile']['exit_code']==0
        phase='profile';cmd=[str(exe),str(out/'pairs.bin')];r['profile']=run(cmd,'profile',600);assert r['profile']['exit_code']==0
        rows=[line.split(',')[1:] for line in (out/'profile.stdout').read_text(encoding='utf8').splitlines() if line.startswith('COST,')];assert len(rows)==24
        r['pairs']=[dict(index=int(v[0]),h_s=float(v[1]),key_v=float(v[2]),parts_s=float(v[3]),solve_s=float(v[4])) for v in rows];r['passed']=True
    except Exception:
        r['failure']=traceback.format_exc();r['failed_phase']=phase;write(out/'failed_sources.json',snap);r['unchanged_replay']=run(cmd,'unchanged-replay',600)
    assert hashes=={n:sha(ROOT/n) for n in names};r['private_sha256']={p.relative_to(ROOT).as_posix():sha(p) for p in out.iterdir() if p.is_file()};write(receipt,r);print('VOICE_COST_PROFILE',r['passed'],r.get('failure',''),r.get('pairs',[]),flush=True)
    if not r['passed']:raise SystemExit(1)
if __name__=='__main__':main()
