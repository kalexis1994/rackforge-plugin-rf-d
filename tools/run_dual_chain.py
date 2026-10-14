"""Bounded joint run; preserve source/data and unchanged replay on rejection."""
import base64, json, os, shutil, subprocess, sys, time, traceback
from pathlib import Path
from prepare_dual_chain import ROOT,sha,write
from dual_chain_reference import Original
LIB=ROOT/'references-local/voice-assembly-public01/librf_d_circuit.rlib'
COMPILER='C:/Users/kalex/.rustup/toolchains/stable-x86_64-pc-windows-gnu/bin/rustc.exe'
def sources():
    names=['tools/prepare_dual_chain.py','tools/run_dual_chain.py','tools/dual_chain_bank.rs',
           'tools/dual_chain_reference.py','crates/rf-d-circuit/src/dual_chain.rs',
           'crates/rf-d-circuit/src/dual_contour_loaded.rs','crates/rf-d-circuit/src/dual_contour.rs',
           'crates/rf-d-circuit/src/filter_contour_port.rs','crates/rf-d-circuit/src/conditioned_voice_contour.rs',
           'crates/rf-d-circuit/src/conditioned_voice_latch.rs','crates/rf-d-circuit/tests/support/mixer_chain_lab.rs',
           'docs/CONTORNOS_CADENA_PROTOCOLO.md','evidence/loudness_contour_graph.json']
    for module in list(sys.modules.values()):
        f=getattr(module,'__file__',None)
        if f:
            p=Path(f).resolve()
            if p.is_relative_to(ROOT/'tools') and p.suffix=='.py':names.append(p.relative_to(ROOT).as_posix())
    return sorted(set(names))
def main():
    assert shutil.disk_usage(ROOT).free>=1024**3
    assert sha(LIB)=='9dbada9779f30c4972b057befe092524d091d3444ea777206b618d701236385d'
    k=1
    while (ROOT/f'evidence/dual_chain_native{k:02d}.json').exists():k+=1
    out=ROOT/f'references-local/dual-chain{k:02d}';out.mkdir()
    names=sources();hashes={n:sha(ROOT/n) for n in names};snap={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in names}
    r=dict(schema='rf-d/dual-chain/native-v1',passed=False,source_sha256=hashes,library_sha256=sha(LIB),profiles=[],output_directory=out.relative_to(ROOT).as_posix())
    phase='prepare';last=None
    env=dict(os.environ,PATH='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+os.environ['PATH'])
    def prepare():
        oracle=Original();seed=oracle.seed();x,d=oracle.root(seed)
        return dict(seed=seed,original_dc=x,diagnostics=d)
    def run(command,label,timeout):
        start=time.monotonic()
        with (out/(label+'.stdout')).open('wb') as stdout,(out/(label+'.stderr')).open('wb') as stderr:
            try:p=subprocess.run(command,cwd=ROOT,env=env,stdout=stdout,stderr=stderr,timeout=timeout);exit_code=p.returncode
            except subprocess.TimeoutExpired:exit_code=-999
        return dict(command=command,exit_code=exit_code,wall_s=time.monotonic()-start,stdout_sha256=sha(out/(label+'.stdout')),stderr_sha256=sha(out/(label+'.stderr')))
    try:
        start=time.monotonic();inputs=prepare();assert time.monotonic()-start<=300
        write(out/'original_inputs.json',inputs)
        import struct
        (out/'seed.bin').write_bytes(struct.pack('<118d',*inputs['seed'][:118]))
        print('JOINT_ORIGINAL_DC',inputs['diagnostics'],flush=True)
        phase='compile';exe=out/'bank.exe'
        last=[COMPILER,'--edition=2021','-C','opt-level=2','-C','strip=symbols','-C','link-arg=-Wl,--stack,33554432','-A','dead_code',str(ROOT/'tools/dual_chain_bank.rs'),'--extern','rf_d_circuit='+str(LIB),'-o',str(exe)]
        r['compile']=run(last,'compile',120)
        if r['compile']['exit_code']:raise ValueError('compile rejected')
        phase='profiles'
        for maximum in [8,4]:
            last=[str(exe),str(out/'seed.bin'),str(maximum)]
            p=run(last,f'profile-{maximum}',300);p['maximum_us']=maximum;r['profiles'].append(p)
            print('JOINT_PROFILE',maximum,p['exit_code'],p['wall_s'],flush=True)
            if p['exit_code']:raise ValueError('profile rejected '+str(maximum))
            assert sum(p.stat().st_size for p in out.iterdir() if p.is_file())<=32*1024**2
        r['passed']=True
    except Exception:
        r['failure']=traceback.format_exc();r['failed_phase']=phase;write(out/'failed_sources.json',snap)
        assert hashes=={n:sha(ROOT/n) for n in names}
        if phase=='prepare':
            try:prepare();r['unchanged_replay']='unexpected pass'
            except Exception:r['unchanged_replay']=traceback.format_exc()
        else:r['unchanged_replay']=run(last,'unchanged-replay',300)
    r['source_sha256_after']={n:sha(ROOT/n) for n in names};r['source_unchanged']=hashes==r['source_sha256_after'];assert r['source_unchanged']
    r['library_unchanged']=sha(LIB)==r['library_sha256'];assert r['library_unchanged']
    r['private_sha256']={p.relative_to(ROOT).as_posix():sha(p) for p in out.iterdir() if p.is_file()};r['private_bytes']=sum(p.stat().st_size for p in out.iterdir() if p.is_file())
    write(ROOT/f'evidence/dual_chain_native{k:02d}.json',r)
    print('JOINT_NATIVE',r['passed'],r.get('failure',''),flush=True)
    if not r['passed']:raise SystemExit(1)
if __name__=='__main__':main()
