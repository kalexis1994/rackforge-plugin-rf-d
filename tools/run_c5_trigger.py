"""Freeze inputs, retain original failures/replays, run bounded circuit profiles."""
import base64
import hashlib
import json
import os
import shutil
import subprocess
import time
from pathlib import Path
from c5_trigger_reference import prepare

ROOT=Path(__file__).resolve().parents[1]
COMPILER='C:/Users/kalex/.rustup/toolchains/stable-x86_64-pc-windows-gnu/bin/rustc.exe'
LIB=ROOT/'references-local/voice-assembly-public01/librf_d_circuit.rlib'
OWN=['crates/rf-d-circuit/src/dual_contour.rs','tools/c5_trigger_bank.rs',
     'tools/c5_trigger_reference.py','tools/run_c5_trigger.py','docs/C5_GATILLO_COMPARTIDO_PROTOCOLO.md',
     'crates/rf-d-circuit/src/filter_contour_port.rs','crates/rf-d-circuit/src/conditioned_voice_contour.rs',
     'crates/rf-d-circuit/src/conditioned_voice_latch.rs','tools/loudness_contour_reference.py',
     'tools/filter_ladder_ebers_moll_dc_reference.py','tools/semiconductor_ideal.py',
     'evidence/loudness_contour_graph.json']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n',encoding='utf8',newline='\n')

def main():
    assert shutil.disk_usage(ROOT).free>=1024**3
    assert sha(LIB)=='9dbada9779f30c4972b057befe092524d091d3444ea777206b618d701236385d'
    k=1
    while (ROOT/f'evidence/c5_trigger_native{k:02d}.json').exists():k+=1
    out=ROOT/f'references-local/c5-trigger{k:02d}';out.mkdir()
    sources={n:sha(ROOT/n) for n in OWN}
    snapshots={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in OWN}
    r=dict(schema='rf-d/dual-contour/native-v1',passed=False,source_sha256=sources,
           library_sha256=sha(LIB),output_directory=out.relative_to(ROOT).as_posix(),profiles=[])
    env=dict(os.environ,PATH='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+os.environ['PATH'])
    exe=out/'bank.exe'
    cmd=[COMPILER,'--edition=2021','-C','opt-level=2','-C','strip=symbols',
         '-C','link-arg=-Wl,--stack,33554432','-A','dead_code',str(ROOT/'tools/c5_trigger_bank.rs'),
         '--extern','rf_d_circuit='+str(LIB),'-o',str(exe)]
    def run(command,label,timeout):
        started=time.monotonic();p=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=timeout)
        (out/(label+'.stdout')).write_bytes(p.stdout);(out/(label+'.stderr')).write_bytes(p.stderr)
        result=dict(command=command,exit_code=p.returncode,wall_s=time.monotonic()-started,
                    stdout_sha256=hashlib.sha256(p.stdout).hexdigest(),stderr_sha256=hashlib.sha256(p.stderr).hexdigest())
        return result
    phase='prepare';last_cmd=None;last_label=None
    try:
        inputs=prepare(out)
        write(out/'original_inputs.json',inputs)
        r['original_inputs_sha256']=sha(out/'original_inputs.json')
        phase='compile';last_cmd=cmd;last_label='compile';r['compile']=run(cmd,'compile',120)
        if r['compile']['exit_code']:raise ValueError('compilation rejected')
        phase='profiles'
        for optional in [0,1]:
            for mode in ['key','s']:
                for maximum in [8,4]:
                    last_label=f'profile-{optional}-{mode}-{maximum}'
                    last_cmd=[str(exe),str(out/f'seed{optional}.bin'),str(optional),str(maximum),mode]
                    p=run(last_cmd,last_label,300);p.update(optional=optional,mode=mode,maximum_us=maximum,label=last_label)
                    r['profiles'].append(p)
                    write(ROOT/f'evidence/c5_trigger_progress{k:02d}.json',dict(passed=False,completed_profiles=len(r['profiles']),last=p))
                    if p['exit_code']:raise ValueError('profile rejected '+last_label)
                    assert sum(p.stat().st_size for p in out.iterdir() if p.is_file())<=64*1024**2
        r['passed']=True
    except Exception as e:
        r['failed_phase']=phase;r['error']=repr(e);write(out/'failed_sources.json',snapshots)
        assert sources=={n:sha(ROOT/n) for n in OWN}
        if phase=='prepare':
            try:prepare(out)
            except Exception as replay:r['unchanged_replay']=dict(error=repr(replay),same_error=repr(replay)==repr(e))
            else:raise AssertionError('prepare rejection did not reproduce')
        else:
            repeat=run(last_cmd,'replay',300);r['unchanged_replay']=repeat
            original=r['compile'] if phase=='compile' else r['profiles'][-1]
            r['replay_same_exit']=repeat['exit_code']==original['exit_code']
            r['replay_same_stdout']=repeat['stdout_sha256']==original['stdout_sha256']
    r['source_unchanged']=sources=={n:sha(ROOT/n) for n in OWN}
    r['library_unchanged']=sha(LIB)==r['library_sha256']
    r['private_sha256']={p.relative_to(ROOT).as_posix():sha(p) for p in out.iterdir() if p.is_file()}
    r['private_bytes']=sum(p.stat().st_size for p in out.iterdir() if p.is_file())
    assert r['source_unchanged'] and r['library_unchanged']
    write(ROOT/f'evidence/c5_trigger_native{k:02d}.json',r)
    print(json.dumps({n:v for n,v in r.items() if n not in ('source_sha256','private_sha256')},indent=2))
    if not r['passed']:raise SystemExit(1)
if __name__=='__main__':main()
