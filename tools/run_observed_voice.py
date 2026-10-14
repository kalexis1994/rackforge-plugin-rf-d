"""Bounded genuine VCO/dual-contour run using the frozen public circuit library."""
import base64,json,os,shutil,subprocess,time,traceback,sys
from prepare_dual_chain import ROOT,sha,write
from run_dual_chain import COMPILER,LIB
OWN=['docs/VOZ_PASO_OBSERVABLE_PROTOCOLO.md','crates/rf-d-circuit/src/observed_voice.rs','tools/prepare_voice_sparse.py','tools/prepare_voice_order.py','docs/VOZ_COSTO_TRAYECTORIA_PROTOCOLO.md','tools/assembly_vco_helper.rs','crates/rf-d-circuit/src/vco1_stamp_data.rs','tools/run_observed_voice.py','tools/observed_voice_trajectory.rs','tools/prepare_dual_voice.py',
     'crates/rf-d-circuit/src/sparse_ordered_voice.rs','crates/rf-d-circuit/src/dual_voice_chain.rs','crates/rf-d-circuit/src/sparse_ordered_voice_solver.rs',
     'crates/rf-d-circuit/src/dual_contour_loaded.rs','crates/rf-d-circuit/src/filter_contour_port.rs','crates/rf-d-circuit/src/conditioned_voice_contour.rs','crates/rf-d-circuit/src/conditioned_voice_latch.rs','crates/rf-d-circuit/tests/support/mixer_chain_lab.rs','docs/VOZ_DOS_CONTORNOS_PROTOCOLO.md']
def main():
    assert shutil.disk_usage(ROOT).free>=1024**3 and sha(LIB)=='9dbada9779f30c4972b057befe092524d091d3444ea777206b618d701236385d'
    duration=int(sys.argv[1]) if len(sys.argv)>1 else 24000
    gate_end=int(sys.argv[2]) if len(sys.argv)>2 else 6000
    assert 6000<=duration<=500000 and 6000<=gate_end<=duration
    k=1
    while (ROOT/f'evidence/observed_voice_native{k:02d}.json').exists():k+=1
    out=ROOT/f'references-local/observed-voice{k:02d}';out.mkdir();hashes={n:sha(ROOT/n) for n in OWN};snap={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in OWN}
    r=dict(schema='rf-d/observed-voice/native-v1',passed=False,source_sha256=hashes,library_sha256=sha(LIB),profiles=[],duration_us=duration,gate_end_us=gate_end,output_directory=out.relative_to(ROOT).as_posix())
    inputs=ROOT/'references-local/dual-chain04/original_inputs.json';old=json.loads((ROOT/'evidence/dual_chain_tests01.json').read_text(encoding='utf8'));assert sha(inputs)==old['private_input_sha256'][inputs.relative_to(ROOT).as_posix()]
    r['private_used_sha256']={inputs.relative_to(ROOT).as_posix():sha(inputs)}
    import struct
    (out/'seed.bin').write_bytes(struct.pack('<118d',*json.loads(inputs.read_text(encoding='utf8'))['original_dc'][:118]))
    env=dict(os.environ,PATH='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+os.environ['PATH'])
    def run(cmd,label,timeout):
        start=time.monotonic()
        with (out/(label+'.stdout')).open('wb') as stdout,(out/(label+'.stderr')).open('wb') as stderr:
            try:p=subprocess.run(cmd,cwd=ROOT,env=env,stdout=stdout,stderr=stderr,timeout=timeout);code=p.returncode
            except subprocess.TimeoutExpired:code=-999
        return dict(command=cmd,exit_code=code,wall_s=time.monotonic()-start,stdout_sha256=sha(out/(label+'.stdout')),stderr_sha256=sha(out/(label+'.stderr')))
    exe=out/'bank.exe';last=[COMPILER,'--edition=2021','-C','opt-level=2','-C','strip=symbols','-C','link-arg=-Wl,--stack,33554432','-A','unused_imports','-A','dead_code',str(ROOT/'tools/observed_voice_trajectory.rs'),'--extern','rf_d_circuit='+str(LIB),'-o',str(exe)]
    phase='compile'
    try:
        r['compile']=run(last,'compile',120)
        if r['compile']['exit_code']:raise ValueError('compile rejected')
        phase='profiles'
        for maximum in [16777216,8388608]:
            label=f'profile-{maximum}';last=[str(exe),str(out/'seed.bin'),str(maximum),str(out/f'linear-{maximum}.bin'),str(duration),str(gate_end)]
            p=run(last,label,600);p['maximum_half_ticks']=maximum;r['profiles'].append(p);print('DUAL_VOICE_PROFILE',maximum,p['exit_code'],p['wall_s'],flush=True)
            if p['exit_code']:raise ValueError('profile rejected '+label)
            assert sum(p.stat().st_size for p in out.iterdir() if p.is_file())<=32*1024**2
        r['passed']=True
    except Exception:
        r['failure']=traceback.format_exc();r['failed_phase']=phase;write(out/'failed_sources.json',snap);assert hashes=={n:sha(ROOT/n) for n in OWN}
        # Keep the original trace and replay binary separate.
        if phase=='profiles':last=[*last[:3],str(out/'linear-unchanged-replay.bin'),*last[4:]]
        r['unchanged_replay']=run(last,'unchanged-replay',120 if phase=='compile' else 600)
    r['source_unchanged']=hashes=={n:sha(ROOT/n) for n in OWN};r['library_unchanged']=sha(LIB)==r['library_sha256'];assert r['source_unchanged'] and r['library_unchanged']
    r['private_sha256']={p.relative_to(ROOT).as_posix():sha(p) for p in out.iterdir() if p.is_file()};r['private_bytes']=sum(p.stat().st_size for p in out.iterdir() if p.is_file());write(ROOT/f'evidence/observed_voice_native{k:02d}.json',r)
    print('DUAL_VOICE_NATIVE',r['passed'],r.get('failure',''),flush=True)
    if not r['passed']:raise SystemExit(1)
if __name__=='__main__':main()
