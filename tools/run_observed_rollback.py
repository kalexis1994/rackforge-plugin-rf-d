"""Electrical-domain rollback followed by a valid solve in reused workspace."""
import base64,json,os,struct,subprocess
from prepare_dual_chain import ROOT,sha,write
from run_dual_chain import COMPILER,LIB
def main():
    k=1
    while (ROOT/f'evidence/observed_voice_rollback{k:02d}.json').exists():k+=1
    out=ROOT/f'references-local/observed-rollback{k:02d}';out.mkdir()
    used='references-local/observed-voice02/profile-8388608.stdout'
    line=(ROOT/used).read_text(encoding='utf8').splitlines()[0]
    values=list(map(float,line.split(',')[5:]));assert len(values)==500
    (out/'seed.bin').write_bytes(struct.pack('<500d',*values))
    names=['tools/run_observed_rollback.py','tools/observed_voice_rollback.rs','crates/rf-d-circuit/src/observed_voice.rs','crates/rf-d-circuit/src/sparse_ordered_voice.rs','crates/rf-d-circuit/src/sparse_ordered_voice_solver.rs','crates/rf-d-circuit/tests/support/mixer_chain_lab.rs']
    r=dict(passed=False,source_sha256={n:sha(ROOT/n) for n in names},private_used_sha256={used:sha(ROOT/used)},compiler_sha256=sha(__import__('pathlib').Path(COMPILER)),library_sha256=sha(LIB))
    assert r['library_sha256']=='9dbada9779f30c4972b057befe092524d091d3444ea777206b618d701236385d'
    assert r['compiler_sha256']=='fd6232f90a981e28472ce6900232946a1f1bcad8ec8270cd5ae6a3a357208b98'
    env=dict(os.environ,PATH='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+os.environ['PATH'])
    cmd=[COMPILER,'--edition=2021','-C','opt-level=2','-C','strip=symbols','-C','link-arg=-Wl,--stack,33554432','-A','unused_imports','-A','dead_code',str(ROOT/'tools/observed_voice_rollback.rs'),'--extern','rf_d_circuit='+str(LIB),'-o',str(out/'probe.exe')]
    r['commands']=[]
    for phase,command in [('compile',cmd),('probe',[str(out/'probe.exe'),str(out/'seed.bin')])]:
        p=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=120);r['commands'].append(command)
        (out/(phase+'.stdout')).write_bytes(p.stdout);(out/(phase+'.stderr')).write_bytes(p.stderr);r[phase+'_exit_code']=p.returncode
        if p.returncode:
            r['failed_phase']=phase;r['source_base64']={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in names}
            replay=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=120)
            (out/'replay.stdout').write_bytes(replay.stdout);(out/'replay.stderr').write_bytes(replay.stderr);r['unchanged_replay_exit_code']=replay.returncode
            break
    else:r.update(passed=True,domain_atomic_rejections=2,exact_valid_candidate_replays=1)
    r['private_sha256']={p.relative_to(ROOT).as_posix():sha(p) for p in out.iterdir() if p.is_file()}
    assert all(sha(ROOT/n)==h for n,h in r['source_sha256'].items())
    write(ROOT/f'evidence/observed_voice_rollback{k:02d}.json',r);print('OBSERVED_ROLLBACK',r['passed'],r.get('failed_phase',''))
    if not r['passed']:raise SystemExit(1)
if __name__=='__main__':main()
