"""Compare new factorization against the unchanged voice and its measured histories."""
import base64,json,os,subprocess,time,traceback,statistics
from prepare_dual_chain import ROOT,sha,write
from run_dual_voice import COMPILER,LIB,OWN
def main():
    out=ROOT/'references-local/voice-sparse01';out.mkdir();receipt=ROOT/'evidence/voice_sparse_bench01.json';assert not receipt.exists()
    names=sorted(set(OWN+['tools/voice_sparse_bench.rs','tools/run_voice_sparse.py','tools/prepare_voice_sparse.py','crates/rf-d-circuit/src/sparse_ordered_voice.rs','crates/rf-d-circuit/src/sparse_ordered_voice_solver.rs','evidence/voice_sparse_recipe01.json']))
    hashes={n:sha(ROOT/n) for n in names};snap={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in names};env=dict(os.environ,PATH='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+os.environ['PATH'])
    def run(cmd,label,timeout):
        start=time.monotonic();p=subprocess.run(cmd,cwd=ROOT,env=env,capture_output=True,timeout=timeout);(out/(label+'.stdout')).write_bytes(p.stdout);(out/(label+'.stderr')).write_bytes(p.stderr)
        return dict(exit_code=p.returncode,wall_s=time.monotonic()-start,command=cmd,stdout_sha256=sha(out/(label+'.stdout')),stderr_sha256=sha(out/(label+'.stderr')))
    exe=out/'bench.exe';cmd=[COMPILER,'--edition=2021','-C','opt-level=2','-C','strip=symbols','-C','link-arg=-Wl,--stack,33554432','-A','unused_imports','-A','dead_code',str(ROOT/'tools/voice_sparse_bench.rs'),'--extern','rf_d_circuit='+str(LIB),'-o',str(exe)]
    r=dict(schema='rf-d/voice-cost/ordered-bench-v1',passed=False,source_sha256=hashes,library_sha256=sha(LIB));phase='compile'
    try:
        r['compile']=run(cmd,'compile',120);assert r['compile']['exit_code']==0
        phase='bench';cmd=[str(exe),str(ROOT/'references-local/voice-cost01/pairs.bin')];r['bench']=run(cmd,'bench',600);assert r['bench']['exit_code']==0
        checks=[];rounds=[]
        for line in (out/'bench.stdout').read_text(encoding='utf8').splitlines():
            tag,*v=line.split(',')
            if tag=='CHECK':checks.append(dict(index=int(v[0]),direction_fraction=float(v[1]),stage_fraction=float(v[2])))
            if tag=='ROUND':rounds.append(dict(index=int(v[0]),round=int(v[1]),baseline_s=float(v[2]),candidate_s=float(v[3])))
        assert len(checks)==24 and len(rounds)==120
        r.update(checks=checks,rounds=rounds,median_ratio=statistics.median(p['candidate_s']/p['baseline_s'] for p in rounds),worst_ratio=max(p['candidate_s']/p['baseline_s'] for p in rounds));r['passed']=True
    except Exception:
        r['failure']=traceback.format_exc();r['failed_phase']=phase;write(out/'failed_sources.json',snap);r['unchanged_replay']=run(cmd,'unchanged-replay',600)
    assert hashes=={n:sha(ROOT/n) for n in names};r['private_sha256']={p.relative_to(ROOT).as_posix():sha(p) for p in out.iterdir() if p.is_file()};write(receipt,r);print('VOICE_ORDER_BENCH',r['passed'],r.get('failure',''),r.get('median_ratio'),r.get('worst_ratio'),flush=True)
    if not r['passed']:raise SystemExit(1)
if __name__=='__main__':main()
