"""Bounded 69-unknown native caller; all processing isolated from IO/allocation."""
import json,os,subprocess,time,traceback
from pathlib import Path
import numpy as np
from prepare_dual_chain import ROOT,sha,write
from affine_evidence import Sources
from check_hybrid_voice import packed
from check_vco_phase import COMPILER,LIB
from vco_family import encode_window,decode_window
AREA=ROOT/'tmp/lab-current';PACK=ROOT/'evidence/family_filter_sdirk_windows01.xz'
def main():
    assert not list(AREA.iterdir()) and not PACK.exists();old=json.loads((ROOT/'evidence/family_mixer_tests01.json').read_text(encoding='utf8'));assert sha(Path(COMPILER))==old['compiler']['sha256'] and sha(LIB)==old['private_input_sha256'][LIB.relative_to(ROOT).as_posix()]
    sources=Sources(['tools/check_family_filter_sdirk_native.py','tools/family_filter_sdirk_probe.rs','tools/family_filter_sdirk_kernel.rs','tools/vco_cv_load_linear.rs','tools/family_mixer_data128.rs','tools/family_mixer_family128.rs','crates/rf-d-circuit/src/chain_charge.rs','crates/rf-d-circuit/tests/support/mixer_chain_lab.rs','docs/FAMILIA_FILTRO_PROTOCOLO.md']);r=dict(passed=False,**sources.fields(),compiler_sha256=sha(Path(COMPILER)),library_sha256=sha(LIB),pack=PACK.relative_to(ROOT).as_posix(),profiles=[]);env=dict(os.environ,PATH='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+os.environ['PATH']);command=[]
    def save():write(ROOT/'evidence/family_filter_sdirk_native01.json',r)
    save();phase='compile'
    try:
        command=[COMPILER,'--edition=2021','-C','opt-level=2','-C','strip=symbols','-C','link-arg=-Wl,--stack,33554432','-A','dead_code','-A','unused_imports',str(ROOT/'tools/family_filter_sdirk_probe.rs'),'--extern','rf_d_circuit='+str(LIB),'-o',str(AREA/'filter.exe')];q=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=120);r['compile']=dict(exit_code=q.returncode,stdout=packed(q.stdout),stderr=packed(q.stderr));save();assert q.returncode==0,q.stderr.decode()
        phase='roots';command=[str(AREA/'filter.exe'),'roots'];q=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=240);r['roots']=dict(exit_code=q.returncode,stdout=packed(q.stdout),stderr=packed(q.stderr));save();assert q.returncode==0,q.stderr.decode()
        phase='walk'
        with PACK.open('xb') as sink:
            for cv in [-2.6,-.6]:
                for step in [500,250]:
                    command=[str(AREA/'filter.exe'),str(cv),str(step)];path=AREA/'stream.bin';start=time.monotonic()
                    with path.open('wb') as out:q=subprocess.run(command,cwd=ROOT,env=env,stdout=out,stderr=subprocess.PIPE,timeout=240)
                    x=dict(cv_v=cv,step_ns=step,elapsed_s=time.monotonic()-start,exit_code=q.returncode,stderr=packed(q.stderr),stream_sha256=sha(path),stream_bytes=path.stat().st_size);r['profiles'].append(x);save();assert q.returncode==0,q.stderr.decode();assert x['stream_bytes']<256*1024**2
                    a=np.fromfile(path,dtype='<f8').reshape(-1,11);assert np.isfinite(a).all() and a[0,0]==0 and np.all(np.diff(a[:,0])>0) and np.all(np.diff(a[:,1])>0) and a[-1,1]>=1 and np.max(abs(a[:,2]))<=.125
                    x['window']=encode_window(a,sink);x['rows']=len(a);assert decode_window(x['window'],PACK).tobytes()==a.astype('<f8').tobytes();path.unlink();save();print('FILTER_CYCLE',cv,step,len(a),flush=True)
        r['passed']=True
    except Exception:
        r.update(failure=traceback.format_exc(),failed_phase=phase);save()
        if phase!='walk':
            q=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=240);r['unchanged_replay']=dict(exit_code=q.returncode,stdout=packed(q.stdout),stderr=packed(q.stderr))
        else:
            path=AREA/'stream.bin';r['failed_stream']=packed(path.read_bytes())
            with path.open('wb') as out:q=subprocess.run(command,cwd=ROOT,env=env,stdout=out,stderr=subprocess.PIPE,timeout=240)
            r['unchanged_replay']=dict(exit_code=q.returncode,stderr=packed(q.stderr),stream=packed(path.read_bytes()))
    finally:
        for n in ['filter.exe','stream.bin']:
            p=AREA/n
            if p.exists():assert p.resolve().parent==AREA.resolve();p.unlink()
    sources.unchanged();r.update(temporary_area_empty=not list(AREA.iterdir()),pack_sha256=sha(PACK) if PACK.exists() else None,pack_bytes=PACK.stat().st_size if PACK.exists() else 0);save();print('FILTER_NATIVE',r['passed'],r.get('failure',''),flush=True)
    if not r['passed']:raise SystemExit(1)
if __name__=='__main__':main()
