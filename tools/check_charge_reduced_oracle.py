"""Fixed-control full nonlinear chain: DC, G/M, held-out perturbations."""
import json,os,subprocess,time,traceback
from pathlib import Path
import numpy as np
from prepare_dual_chain import ROOT,sha,write
from affine_evidence import Sources
from check_hybrid_voice import packed
from check_vco_phase import COMPILER,LIB
from vco_family import encode_window,decode_window
AREA=ROOT/'tmp/lab-current';OUT=ROOT/'evidence/charge_reduced_oracle02.json';PACK=ROOT/'evidence/charge_reduced_windows01.xz'
OWN=['tools/check_charge_reduced_oracle.py','tools/charge_reduced_oracle.rs','tools/vco_cv_load_linear.rs','crates/rf-d-circuit/src/chain_charge.rs','crates/rf-d-circuit/tests/support/mixer_chain_lab.rs','docs/CHARGE_REDUCED_PROTOCOLO.md']
def main():
    assert not OUT.exists() and not PACK.exists() and not list(AREA.iterdir());prior=json.loads((ROOT/'evidence/mono_voice_tests01.json').read_text(encoding='utf8'));assert sha(Path(COMPILER))==prior['compiler']['sha256'] and sha(LIB)==prior['private_input_sha256'][LIB.relative_to(ROOT).as_posix()]
    sources=Sources(OWN);r=dict(passed=False,**sources.fields(),compiler_sha256=sha(Path(COMPILER)),library_sha256=sha(LIB),pack=PACK.relative_to(ROOT).as_posix(),profiles=[]);exe=AREA/'charge.exe';stream=AREA/'charge.bin';env=dict(os.environ,PATH='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+os.environ['PATH']);command=[]
    def save():write(OUT,r)
    save()
    try:
        command=[COMPILER,'--edition=2021','-C','opt-level=2','-C','strip=symbols','-C','link-arg=-Wl,--stack,33554432','-A','dead_code','-A','unused_imports',str(ROOT/'tools/charge_reduced_oracle.rs'),'--extern','rf_d_circuit='+str(LIB),'-o',str(exe)];q=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=120);r['compile']=dict(exit_code=q.returncode,stdout=packed(q.stdout),stderr=packed(q.stderr));save();assert q.returncode==0,q.stderr.decode()
        command=[str(exe),'export'];q=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=240);r['export']=dict(exit_code=q.returncode,stdout=packed(q.stdout),stderr=packed(q.stderr));save();assert q.returncode==0,q.stderr.decode()
        with PACK.open('xb') as sink:
            for case in [0,1]:
                for amplitude in [1e-5,1e-3]:
                    for step in [500,250]:
                        command=[str(exe),str(case),str(amplitude),str(step)];begin=time.monotonic()
                        with stream.open('xb') as out:q=subprocess.run(command,cwd=ROOT,env=env,stdout=out,stderr=subprocess.PIPE,timeout=240)
                        p=dict(case=case,amplitude_v=amplitude,step_ns=step,exit_code=q.returncode,elapsed_s=time.monotonic()-begin,stderr=packed(q.stderr),stream_sha256=sha(stream),stream_bytes=stream.stat().st_size);r['profiles'].append(p);save();assert q.returncode==0,q.stderr.decode()
                        a=np.fromfile(stream,dtype='<f8').reshape(-1,138);assert np.isfinite(a).all() and a[0,0]==0 and abs(a[-1,0]-.004)<1e-15;p['window']=encode_window(a,sink);p['rows']=len(a);assert decode_window(p['window'],PACK).tobytes()==a.tobytes();stream.unlink();save();print('CHARGE_ORACLE',case,amplitude,step,p['elapsed_s'],flush=True)
        r['passed']=True
    except Exception:
        r['failure']=traceback.format_exc();save()
        if stream.exists():r['failed_stream']=packed(stream.read_bytes());stream.unlink()
        if command:
            q=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=240);r['unchanged_replay']=dict(exit_code=q.returncode,stdout=packed(q.stdout),stderr=packed(q.stderr))
    finally:
        for p in [exe,stream]:
            if p.exists():assert p.resolve().parent==AREA.resolve();p.unlink()
    sources.unchanged();r.update(temporary_area_empty=not list(AREA.iterdir()),pack_sha256=sha(PACK) if PACK.exists() else None,pack_bytes=PACK.stat().st_size if PACK.exists() else 0);save();print('CHARGE_ORACLE_DONE',r['passed'],r.get('failure',''),flush=True)
    if not r['passed']:raise SystemExit(1)
if __name__=='__main__':main()
