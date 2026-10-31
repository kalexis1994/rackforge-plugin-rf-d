"""Refine the nonlinear switching reference without altering the candidate."""
import json,os,subprocess,time,traceback
from pathlib import Path
import numpy as np
from prepare_dual_chain import ROOT,sha,write
from affine_evidence import Sources
from check_hybrid_voice import packed
from check_vco_phase import COMPILER,LIB
from check_charge_control import simulate,metrics
from vco_family import encode_window,decode_window
AREA=ROOT/'tmp/lab-current'
def main():
    out=ROOT/'evidence/charge_control_refinement01.json';pack=ROOT/'evidence/charge_control_refined_windows01.xz';assert not out.exists() and not pack.exists() and not list(AREA.iterdir());old=json.loads((ROOT/'evidence/charge_reduced_tests01.json').read_text(encoding='utf8'));assert sha(Path(COMPILER))==old['compiler']['sha256'] and sha(LIB)==old['private_input_sha256'][LIB.relative_to(ROOT).as_posix()];original=json.loads((ROOT/'evidence/charge_control_native01.json').read_text(encoding='utf8'));sources=Sources(['tools/check_charge_control_refinement.py','tools/charge_control_refined_oracle.rs','docs/CHARGE_CONTROL_REFINAMIENTO.md']);r=dict(passed=False,**sources.fields(),compiler_sha256=sha(Path(COMPILER)),library_sha256=sha(LIB),pack=pack.relative_to(ROOT).as_posix(),profiles=[],reference_converged=False);exe=AREA/'fine.exe';stream=AREA/'fine.bin';env=dict(os.environ,PATH='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+os.environ['PATH']);command=[]
    def save():write(out,r)
    save()
    try:
        command=[COMPILER,'--edition=2021','-C','opt-level=2','-C','strip=symbols','-C','link-arg=-Wl,--stack,33554432','-A','dead_code','-A','unused_imports',str(ROOT/'tools/charge_control_refined_oracle.rs'),'--extern','rf_d_circuit='+str(LIB),'-o',str(exe)];q=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=120);r['compile']=dict(exit_code=q.returncode,stdout=packed(q.stdout),stderr=packed(q.stderr));save();assert q.returncode==0,q.stderr.decode();previous=None
        with pack.open('xb') as sink:
            for step in [250,125,62.5,31.25,15.625,7.8125]:
                stride=round(250/step);command=[str(exe),'.5','.01',str(step),'dynamic',str(stride)];begin=time.monotonic()
                with stream.open('xb') as f:q=subprocess.run(command,cwd=ROOT,env=env,stdout=f,stderr=subprocess.PIPE,timeout=240)
                p=dict(step_ns=step,export_stride=stride,elapsed_s=time.monotonic()-begin,exit_code=q.returncode,stderr=packed(q.stderr),full_export_sha256=sha(stream),full_export_bytes=stream.stat().st_size);r['profiles'].append(p);save();assert q.returncode==0,q.stderr.decode();assert p['full_export_bytes']<=32*1024**2;a=np.fromfile(stream,dtype='<f8').reshape(-1,139);full=a[:,3:71]+a[:,71:139];assert np.isfinite(a).all() and len(a)==16001
                if step==250:
                    source=next(x for x in original['profiles'] if x['dynamic'] and x['step_ns']==250);assert p['full_export_sha256']==source['full_stream_sha256'];r['original_250ns_replay_identical']=True
                h=step*1e-9;tt=np.arange(round(.004/h)+1)*h;uu=.01*(np.sin(2*np.pi*137*tt)+.3*np.sin(2*np.pi*1103*tt));candidate,switches=simulate(original['models'],tt,uu,1,True);p['candidate_same_step_metrics']=metrics(full,candidate[::stride]);p['switches']=switches;worst=p['candidate_same_step_metrics']['worst_row'];select=np.unique(np.r_[np.arange(0,len(a),64),len(a)-1,worst,[4000,8000,12000]])
                if previous is not None:
                    p['reference_comparison']=metrics(full,previous);p['reference_comparison']['same_time_grid_max_error_s']=float(max(abs(a[:,0]-previous_time)));assert p['reference_comparison']['same_time_grid_max_error_s']<=1e-15;select=np.unique(np.r_[select,p['reference_comparison']['worst_row']]);r['reference_converged']=p['reference_comparison']['domain_admitted']
                p['state_rows']=select.tolist();p['state_window']=encode_window(a[select],sink);signals=np.column_stack([a[:,:3],full[:,61],full[:,66],full[:,6]]);p['signal_window']=encode_window(signals,sink);sink.flush();assert decode_window(p['state_window'],pack).tobytes()==a[select].tobytes();assert decode_window(p['signal_window'],pack).tobytes()==signals.tobytes();stream.unlink();p['full_grid_retired_after_metrics_and_selected_byte_checks']=True;previous=full;previous_time=a[:,0].copy();save();print('CONTROL_FINE',step,p.get('reference_comparison',{}).get('all_nodes_error_v'),r['reference_converged'],p['candidate_same_step_metrics']['all_nodes_error_v'],flush=True)
                if r['reference_converged']:break
        r['passed']=True
    except Exception:
        r['failure']=traceback.format_exc();save()
        if stream.exists():r['failed_stream']=packed(stream.read_bytes());stream.unlink()
        if command:
            q=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=240);r['unchanged_replay']=dict(exit_code=q.returncode,stdout=packed(q.stdout),stderr=packed(q.stderr))
    finally:
        for p in [exe,stream]:
            if p.exists():assert p.resolve().parent==AREA.resolve();p.unlink()
    sources.unchanged();r.update(temporary_area_empty=not list(AREA.iterdir()),pack_sha256=sha(pack) if pack.exists() else None,pack_bytes=pack.stat().st_size if pack.exists() else 0);save();print('CONTROL_REFINEMENT',r['passed'],r['reference_converged'],r.get('failure',''))
    if not r['passed']:raise SystemExit(1)
if __name__=='__main__':main()
