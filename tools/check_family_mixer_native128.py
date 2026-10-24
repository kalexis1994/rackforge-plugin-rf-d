"""Implicit reduced continuations from the same observed C27 memory."""
import json,os,subprocess,time,traceback
from pathlib import Path
import numpy as np
from prepare_dual_chain import ROOT,sha,write
from affine_evidence import Sources
from check_hybrid_voice import packed
from check_vco_phase import COMPILER
from vco_family import encode_window,decode_window
from family_mixer_analysis import capture_native,compare,C
AREA=ROOT/'tmp/lab-current';PACK=ROOT/'evidence/family_mixer_native128_windows01.xz'
OUT='evidence/family_mixer_native128_01.json';LAST=None
def run(command,env,sink):
    global LAST
    p=AREA/'native.bin';start=time.monotonic()
    with p.open('wb') as f:q=subprocess.run(command,cwd=ROOT,env=env,stdout=f,stderr=subprocess.PIPE,timeout=240)
    r=dict(command=command,elapsed_s=time.monotonic()-start,exit_code=q.returncode,stderr=packed(q.stderr),stream_bytes=p.stat().st_size,stream_sha256=sha(p));LAST=r
    assert q.returncode==0,q.stderr.decode();assert r['stream_bytes']<256*1024**2
    raw=np.fromfile(p,dtype='<f8').reshape(-1,14);assert np.isfinite(raw).all() and raw[0,0]==0 and np.all(np.diff(raw[:,0])>0) and np.all(np.diff(raw[:,1])>0)
    z=q.stderr.decode().strip().split(',');assert z[0]=='COMPLETE' and len(z)==10 and int(z[1])==len(raw)-1 and float(z[2])<=1 and float(z[3])<=1 and float(z[4])<=1e-18 and int(z[7])==0 and z[-2:]==['3','true']
    charge=C*(raw[-1,2]-raw[0,2]);integral=float(np.trapezoid(raw[:,9],raw[:,0]));through=float(np.trapezoid(abs(raw[:,9]),raw[:,0]));err=abs(charge-integral);assert err<=1e-16+through*1e-8,(charge,integral,err)
    assert np.max(abs(raw[:,7]+raw[:,8]+raw[:,9]))<=1e-18 and np.max(raw[:,12:14])<=1
    r.update(measurements=capture_native(raw),window=encode_window(raw,sink),rows=len(raw),charge_error_c=err,charge_throughput_c=through,max_newton_residual_ratio=float(z[2]),max_newton_correction_ratio=float(z[3]),heap_allocations=0,atomic_rejections=3,exact_retry=True);assert decode_window(r['window'],PACK).tobytes()==raw.astype('<f8').tobytes();p.unlink();return r
def main():
    assert not list(AREA.iterdir()) and not PACK.exists();old=json.loads((ROOT/'evidence/vco_family_tests01.json').read_text(encoding='utf8'));assert sha(Path(COMPILER))==old['compiler']['sha256'];oracle=json.loads((ROOT/'evidence/family_mixer_complete01.json').read_text(encoding='utf8'));assert oracle['passed']
    names=['tools/check_family_mixer_native128.py','tools/family_mixer_kernel128.rs','tools/family_mixer_probe128.rs','tools/family_mixer_analysis.py','tools/family_mixer_family128.rs','tools/family_mixer_data128.rs','docs/FAMILIA_MIXER_PROTOCOLO.md']
    sources=Sources(names);r=dict(passed=False,**sources.fields(),oracle_sha256=sha(ROOT/'evidence/family_mixer_complete01.json'),compiler_sha256=sha(Path(COMPILER)),profiles=[],pack=PACK.relative_to(ROOT).as_posix());env=dict(os.environ,PATH='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+os.environ['PATH']);command=[]
    def save():write(ROOT/OUT,r)
    save()
    try:
        command=[COMPILER,'--edition=2021','-C','opt-level=2','-C','strip=symbols',str(ROOT/'tools/family_mixer_probe128.rs'),'-o',str(AREA/'coupled.exe')];p=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=120);r['compile']=dict(exit_code=p.returncode,stdout=packed(p.stdout),stderr=packed(p.stderr));save();assert p.returncode==0,p.stderr.decode()
        with PACK.open('xb') as sink:
            for i,x in enumerate(oracle['cases']):
                pair=[]
                for step in [500,250]:
                    command=[str(AREA/'coupled.exe'),str(x['cv_v']),str(x['load']),format(x['measurements']['start_bus_v'],'.17g'),str(step)]
                    y=run(command,env,sink);y.update(scene=i,step_ns=step,comparison=compare(y['measurements'],x['measurements']));pair.append(y);r['profiles'].append(y);save();print('REDUCED_COUPLED',i,step,flush=True)
                r.setdefault('refinements',[]).append(compare(pair[0]['measurements'],pair[1]['measurements']));save()
        r['passed']=True
    except Exception:
        r.update(failure=traceback.format_exc(),failed_process=LAST);save()
        if command and command[0]==COMPILER:
            p=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=120);r['unchanged_replay']=dict(exit_code=p.returncode,stdout=packed(p.stdout),stderr=packed(p.stderr))
        elif command:
            try:
                with PACK.open('ab') as sink:run(command,env,sink)
                r['unchanged_replay']='process passed; replay gate separately'
                if LAST is not None:compare(LAST['measurements'],x['measurements'])
            except Exception:r.update(unchanged_gate_replay=traceback.format_exc(),replay_process=LAST)
    finally:
        for n in ['native.bin','coupled.exe']:
            p=AREA/n
            if p.exists():assert p.resolve().parent==AREA.resolve();p.unlink()
    sources.unchanged();r.update(temporary_area_empty=not list(AREA.iterdir()),pack_bytes=PACK.stat().st_size if PACK.exists() else 0,pack_sha256=sha(PACK) if PACK.exists() else None);save();print('REDUCED_COUPLED_COMPLETE',r['passed'],r.get('failure',''),flush=True)
    if not r['passed']:raise SystemExit(1)
if __name__=='__main__':main()
