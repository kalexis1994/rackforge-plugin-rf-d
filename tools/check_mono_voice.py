"""Full voice block/allocator/deadline probe; no timers inside the engine."""
import json,os,subprocess,time,traceback,platform
from pathlib import Path
import numpy as np
from prepare_dual_chain import ROOT,sha,write
from affine_evidence import Sources
from check_hybrid_voice import packed,unpack
from check_vco_phase import COMPILER,LIB
AREA=ROOT/'tmp/lab-current'
OWN=['tools/check_mono_voice.py','tools/mono_voice_probe.rs','crates/rf-d-circuit/src/monophonic_voice.rs','docs/MONO_VOICE_PROTOCOLO.md']

def parse(raw,reference=False):
    audio={};blocks=[];states={}
    for line in raw.decode().splitlines():
        z=line.split(',')
        if z[0]=='AUDIO':assert int(z[1]) not in audio;audio[int(z[1])]=float(z[2])
        elif z[0]=='BLOCK':
            q=dict(start=int(z[1]),frames=int(z[2]),elapsed_s=float(z[3]),heap=int(z[4]),calls=int(z[5]),attempts=int(z[6]),iterations=int(z[7]),residual_a=float(z[8]),correction_v=float(z[9]),error=float(z[10]));q['budget_s']=q['frames']/48000;q['budget_ratio']=q['elapsed_s']/q['budget_s'];blocks.append(q)
        elif z[0] in ['INITIAL','FINAL']:states[z[0]]=[int(x,16) for x in z[1:]];assert len(states[z[0]])==236
        elif z[0]=='SETUP':setup=dict(elapsed_s=float(z[1]),voice_bytes=int(z[2]),workspace_bytes=int(z[3]),stats_bytes=int(z[4]))
    assert 'COMPLETE,' in raw.decode() and 'FINAL' in states
    if reference:return dict(audio=audio,states=states)
    assert sorted(audio)==list(range(len(audio))) and np.isfinite(list(audio.values())).all()
    assert all(x==0 for i,x in audio.items() if i<48)
    assert sum(b['frames'] for b in blocks)==len(audio) and all(b['heap']==0 and b['residual_a']<=1e-12 and b['correction_v']<=2e-9 and b['error']<=1 for b in blocks)
    return dict(audio=audio,states=states,blocks=blocks,setup=setup)

def main():
    assert not list(AREA.iterdir());prior=json.loads((ROOT/'evidence/family_filter_tests01.json').read_text(encoding='utf8'));assert sha(Path(COMPILER))==prior['compiler']['sha256'] and sha(LIB)==prior['private_input_sha256'][LIB.relative_to(ROOT).as_posix()]
    sources=Sources(OWN);r=dict(passed=False,**sources.fields(),compiler_sha256=sha(Path(COMPILER)),library_sha256=sha(LIB),platform=platform.platform(),profiles=[],real_time=False,physical_cv_general=False,new_audio=False,previous_wav_sha256=sha(ROOT/'artifacts/rf-d-nominal-current.wav'))
    env=dict(os.environ,PATH='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+os.environ['PATH']);exe=AREA/'mono.exe';command=[];phase='metadata'
    def save():write(ROOT/'evidence/mono_voice_native01.json',r)
    save()
    try:
        q=subprocess.run(['powershell','-NoProfile','-Command','Get-CimInstance Win32_Processor | Select-Object Name,NumberOfCores,NumberOfLogicalProcessors | ConvertTo-Json -Compress; powercfg /GETACTIVESCHEME'],capture_output=True,timeout=30);r['machine']=q.stdout.decode(errors='replace');save()
        phase='compile';flags=['--edition=2021','-C','opt-level=2','-C','link-arg=-Wl,--stack,33554432','-A','dead_code','-A','unused_imports',str(ROOT/'tools/mono_voice_probe.rs'),'--extern','rf_d_circuit='+str(LIB),'-o',str(exe)];command=[COMPILER,'--test',*flags];q=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=120);r['test_compile']=dict(command=command,exit_code=q.returncode,stdout=packed(q.stdout),stderr=packed(q.stderr));save();assert q.returncode==0,q.stderr.decode(errors='replace')
        phase='unit';command=[str(exe),'mono_tests::','--test-threads=1'];q=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=60);r['unit']=dict(exit_code=q.returncode,stdout=packed(q.stdout),stderr=packed(q.stderr));save();assert q.returncode==0,q.stdout.decode(errors='replace');exe.unlink()
        phase='compile';command=[COMPILER,*flags,'-C','strip=symbols'];q=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=120);r['compile']=dict(command=command,exit_code=q.returncode,stdout=packed(q.stdout),stderr=packed(q.stderr));save();assert q.returncode==0,q.stderr.decode(errors='replace')
        phase='trajectory'
        for args in [['64','coarse','480'],['128','coarse','480'],['64','refined','480'],['reference','480']]:
            command=[str(exe),*args];begin=time.monotonic();q=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=240);p=dict(args=args,exit_code=q.returncode,elapsed_s=time.monotonic()-begin,stdout=packed(q.stdout),stderr=packed(q.stderr));r['profiles'].append(p);save();assert q.returncode==0,q.stderr.decode(errors='replace');p['measurements']=parse(q.stdout,args[0]=='reference');save();print('MONO_PROFILE',args,p['elapsed_s'],flush=True)
        r['passed']=True
    except Exception:
        r.update(failure=traceback.format_exc(),failed_phase=phase);save()
        if command:
            try:q=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=240);r['unchanged_replay']=dict(exit_code=q.returncode,stdout=packed(q.stdout),stderr=packed(q.stderr))
            except subprocess.TimeoutExpired as e:r['unchanged_replay']=dict(timeout=True,stdout=packed(e.stdout or b''),stderr=packed(e.stderr or b''))
    finally:
        if exe.exists():assert exe.resolve().parent==AREA.resolve();exe.unlink()
    sources.unchanged();r['temporary_area_empty']=not list(AREA.iterdir());r['wav_unchanged']=sha(ROOT/'artifacts/rf-d-nominal-current.wav')==r['previous_wav_sha256'];save();print('MONO_NATIVE',r['passed'],r.get('failure',''),flush=True)
    if not r['passed']:raise SystemExit(1)
if __name__=='__main__':main()
