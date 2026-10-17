"""Two complete histories; publish only a fully qualified fine-profile candidate."""
import hashlib,json,os,struct,subprocess,time,traceback
from pathlib import Path
import numpy as np
from prepare_dual_chain import ROOT,sha,write
from affine_evidence import Sources
from check_hybrid_voice import packed,unpack
from check_pitch_program import OWN as BASE
from check_long_note_aa import difference,live
from check_vco_phase import COMPILER,LIB
from prepare_pitch_render import images
from export_long_note_aa import wav_bytes
from render_nominal import Laboratory
OWN=list(dict.fromkeys(BASE+list(images())+['tools/prepare_pitch_render.py','tools/pitch_render_main.rs','tools/check_pitch_render.py','docs/PITCH_RENDER_PROTOCOLO.md']))
US=524288
OUT='evidence/pitch_render_native01.json'

def parse_complete(raw):
    lines=raw.decode().splitlines();done=[list(map(int,x.split(',')[1:])) for x in lines if x.startswith('COMPLETE,')];assert len(done)==1
    v=done[0];assert len(v)==10 and v[:2]==[301000*US]*2 and v[2]==v[3]>300000 and v[4:9]==[14401,14400,115585,14400,115584] and v[9]>0
    progress=[list(map(int,x.split(',')[1:])) for x in lines if x.startswith('PROGRESS,')];assert progress and all(len(p)==8 for p in progress)
    assert all(a[0]<=b[0] and a[1]<=b[1] and a[3]<=b[3] and a[5]<=b[5] for a,b in zip(progress,progress[1:]))
    assert all(p[1]<=p[0]<=p[2]==301000*US and p[6]==min(p[5],14400) for p in progress)
    states=[list(map(float,x.split(',')[1:])) for x in lines if x.startswith('STATE,')];assert len(states)==1 and len(states[0])==236 and np.isfinite(states[0]).all()
    return dict(complete=v,progress=progress,state=states[0])

def parse(raw):
    d=parse_complete(raw);a={k:[] for k in ['RAW','AA4','AA8']};audit=[];events=[]
    for line in raw.decode().splitlines():
        z=line.split(',');tag=z[0]
        if tag in a:assert int(z[1])==len(a[tag]);a[tag].append(float(z[2]))
        elif tag=='AUDIT':audit.append(z[1:])
        elif tag=='EVENT':events.append(list(map(float,z[1:])))
    assert len(audit)==1 and len(audit[0])==7
    g=list(map(float,audit[0][:6]));assert g[0]==0 and 0<=g[1]<=1e-12 and 0<=g[2]<=2e-9 and 0<=g[3]<=1 and 0<g[4]<=1e-6 and g[5]==4 and audit[0][6]=='true'
    assert [e[0] for e in events]==[1000*US,100000*US,200000*US,250000*US] and all(len(e)==237 for e in events)
    assert all(len(a[k])==n for k,n in [('RAW',115585),('AA4',14401),('AA8',14401)])
    a={k:np.array(v) for k,v in a.items()};assert all(np.isfinite(v).all() for v in a.values())
    d.update(diagnostics=g,late_cancel_terminal=True,events=events);return d,a

def windows(a,b,rate=False):
    gates=(.0001,.0003,1e-7) if rate else(.001,.003,1e-6)
    out={name:difference(a[lo:hi],b[lo:hi],*gates) for name,lo,hi in [('whole',0,14401),('first',48,4800),('retune_up',4800,9600),('retune_down',9600,12000),('release',12000,14401)]}
    pre=float(max(abs(a[:48]-b[:48])));assert pre<=1e-6;out['pre_key_max_error_v']=pre;return out

def analyse(profiles):
    assert [p['maximum_ticks'] for p in profiles]==[US,US//2];decoded=[parse(unpack(p['stdout'])) for p in profiles]
    result=dict(temporal_refinement=windows(decoded[0][1]['AA8'],decoded[1][1]['AA8']),rate_refinement=[windows(a['AA4'],a['AA8'],True) for d,a in decoded])
    for p,(d,a) in zip(profiles,decoded):assert p['measurements']==d and p['wav_sha256']==hashlib.sha256(wav_bytes(a['AA8'][:14400])).hexdigest()
    return result

def main():
    k=1
    while(ROOT/f'evidence/pitch_render_native{k:02d}.json').exists():k+=1
    out=f'evidence/pitch_render_native{k:02d}.json'
    for n,s in images().items():assert(ROOT/n).read_bytes()==s.encode(),n
    old=json.loads((ROOT/'evidence/pitch_program_tests01.json').read_text(encoding='utf8'));assert sha(Path(COMPILER))==old['compiler']['sha256'] and sha(LIB)==old['public_assembly_library_sha256']
    sources=Sources(OWN);r=dict(passed=False,**sources.fields(),compiler_sha256=sha(Path(COMPILER)),library_sha256=sha(LIB),profiles=[],physical_fidelity=False,physical_cv_model=False,real_time=False,new_original_equation_rows=0,previous_wav_sha256=sha(ROOT/'artifacts/rf-d-nominal-current.wav'))
    env=dict(os.environ,PATH='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+os.environ['PATH']);phase='compile';last=None;command=[];error=None
    with Laboratory() as lab:
        exe=lab.own('renderer.exe');stage=lab.own('render.wav.part');cancel=lab.own('cancel.request')
        flags=['--edition=2021','-C','opt-level=2','-C','link-arg=-Wl,--stack,33554432','-A','unused_imports','-A','dead_code',str(ROOT/'tools/pitch_render_main.rs'),'--extern','rf_d_circuit='+str(LIB),'-o',str(exe)]
        try:
            command=[COMPILER,'--test',*flags];last=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=120);assert last.returncode==0,last.stderr.decode(errors='replace')
            phase='unit';command=[str(exe),'render_tests::','--test-threads=1'];last=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=120);r['unit_tests']=dict(exit_code=last.returncode,stdout=packed(last.stdout),stderr=last.stderr.decode(errors='replace'));assert last.returncode==0,last.stdout.decode(errors='replace');exe.unlink()
            phase='compile';command=[COMPILER,*flags,'-C','strip=symbols'];last=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=120);assert last.returncode==0,last.stderr.decode(errors='replace')
            for profile,ticks,quota in [('1',US,127),('0.5',US//2,61)]:
                phase='trajectory';command=[str(exe),str(stage),str(cancel),str(quota),profile,'audit'];print('PITCH_RENDER_START',profile,flush=True);start=time.monotonic();last=live(command,env,3600)
                item=dict(maximum_ticks=ticks,quota=quota,command=command,exit_code=last.returncode,stdout=packed(last.stdout),stderr=last.stderr.decode(errors='replace'),elapsed_s=time.monotonic()-start);r['profiles'].append(item);assert last.returncode==0,item['stderr']
                phase='parse';d,a=parse(last.stdout);assert stage.read_bytes()==wav_bytes(a['AA8'][:14400]);item.update(measurements=d,wav_sha256=sha(stage),wav_bytes=stage.stat().st_size);stage.unlink();print('PITCH_RENDER_PROFILE_PASS',profile,d['complete'][:4],flush=True)
            phase='analysis';r['analysis']=analyse(r['profiles']);r['passed']=True
        except Exception:
            error=traceback.format_exc();r.update(failure=error,failed_phase=phase,failed_command=command)
            if phase in ['analysis','parse']:
                try:
                    if phase=='analysis':analyse(r['profiles'])
                    else:parse(last.stdout)
                    r['unchanged_gate_replay']='unexpected pass'
                except Exception:r['unchanged_gate_replay']=traceback.format_exc()
            else:
                if last is not None:r['failed_process']=dict(exit_code=last.returncode,stdout=packed(last.stdout),stderr=last.stderr.decode(errors='replace'))
                if stage.exists():r['failed_candidate']=packed(stage.read_bytes());stage.unlink()
                retry=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=3600);r['unchanged_replay']=dict(exit_code=retry.returncode,stdout=packed(retry.stdout),stderr=retry.stderr.decode(errors='replace'))
    sources.unchanged();r['temporary_area_empty']=not list((ROOT/'tmp/lab-current').iterdir());assert sha(ROOT/'artifacts/rf-d-nominal-current.wav')==r['previous_wav_sha256'];write(ROOT/out,r);print('PITCH_RENDER',r['passed'],r.get('analysis'),error,flush=True)
    if not r['passed']:raise SystemExit(1)
if __name__=='__main__':main()
