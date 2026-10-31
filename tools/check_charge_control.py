"""Level/cutoff reserves, conservative rebasing, bounded compact evidence."""
import json,os,subprocess,time,traceback,hashlib
from pathlib import Path
import numpy as np
from prepare_dual_chain import ROOT,sha,write
from affine_evidence import Sources
from check_hybrid_voice import packed,unpack
from check_vco_phase import COMPILER,LIB
from prepare_charge_reduced import derive,Y
from check_charge_reduced_domain import matrices
from vco_family import encode_window,decode_window
AREA=ROOT/'tmp/lab-current';CUT=[.49,.5,.51]
OWN=['tools/check_charge_control.py','tools/charge_control_oracle.rs','tools/prepare_charge_reduced.py','tools/check_charge_reduced_domain.py','docs/CHARGE_CONTROL_PROTOCOLO.md']

def simulate(models,time,u,index,dynamic=False):
    maps=[matrices(m,time[1]-time[0])[:3] for m in models];caps=[np.array(m['incidence'])@np.array(m['dc']) for m in models];xq=[np.array(m['xq']) for m in models];xu=[np.array(m['xu']) for m in models];dc=[np.array(m['dc']) for m in models];q=np.zeros(18);last=index;nodes=np.empty((len(time),68));nodes[0]=dc[index];switches=[]
    for k in range(1,len(time)):
        mid=(time[k-1]+time[k])/2;idx=(1 if mid<.001 or mid>=.003 else 2 if mid<.002 else 0) if dynamic else index
        if idx!=last:
            old=q+caps[last];reset_error=float(max(abs(caps[idx]-old)));q=q+caps[last]-caps[idx];error=float(max(abs(q+caps[idx]-old)));switches.append(dict(time_s=float(time[k-1]),from_index=last,to_index=idx,charge_voltage_continuity_error_v=error,reset_negative_control_error_v=reset_error));assert error<=1e-12 and reset_error>1e-12;last=idx
        f,a,b=maps[idx];q=f@q+a*u[k-1]+b*u[k];nodes[k]=dc[idx]+xq[idx]@q+xu[idx]*u[k]
    return nodes,switches

def metrics(full,reduced):
    error=abs(full-reduced);node=float(np.max(error));idx=np.unravel_index(np.argmax(error),error.shape);dc=full[0,61];d=full[:,61]-reduced[:,61];reference=full[:,61]-dc;rms=float(np.linalg.norm(d)/max(np.linalg.norm(reference),1e-30));peak=float(max(abs(d))/max(max(abs(reference)),1e-30));mean=float(abs(np.mean(d)));maximum=float(max(abs(d)));panel=Y*float(max(abs(full[:,66]-reduced[:,66])));audio=(rms<=.001 and peak<=.003 and mean<=1e-6)or(maximum<=1e-9 and mean<=1e-6)
    return dict(all_nodes_error_v=node,worst_row=int(idx[0]),worst_node=int(idx[1]),node_gate_pass=node<=1e-6,panel_error_a=panel,panel_gate_pass=panel<=2e-9,j7_rms_relative=rms,j7_peak_relative=peak,j7_mean_error_v=mean,j7_max_error_v=maximum,audio_gate_pass=bool(audio),domain_admitted=bool(node<=1e-6 and panel<=2e-9 and audio))

def main():
    out=ROOT/'evidence/charge_control_native01.json';pack=ROOT/'evidence/charge_control_windows01.xz';assert not out.exists() and not pack.exists() and not list(AREA.iterdir());old=json.loads((ROOT/'evidence/charge_reduced_tests01.json').read_text(encoding='utf8'));assert sha(Path(COMPILER))==old['compiler']['sha256'] and sha(LIB)==old['private_input_sha256'][LIB.relative_to(ROOT).as_posix()];sources=Sources(OWN);r=dict(passed=False,**sources.fields(),compiler_sha256=sha(Path(COMPILER)),library_sha256=sha(LIB),cutoff_values=CUT,profiles=[],pack=pack.relative_to(ROOT).as_posix());exe=AREA/'control.exe';stream=AREA/'control.bin';env=dict(os.environ,PATH='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+os.environ['PATH']);command=[]
    def save():write(out,r)
    save()
    try:
        command=[COMPILER,'--edition=2021','-C','opt-level=2','-C','strip=symbols','-C','link-arg=-Wl,--stack,33554432','-A','dead_code','-A','unused_imports',str(ROOT/'tools/charge_control_oracle.rs'),'--extern','rf_d_circuit='+str(LIB),'-o',str(exe)];q=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=120);r['compile']=dict(exit_code=q.returncode,stdout=packed(q.stdout),stderr=packed(q.stderr));save();assert q.returncode==0,q.stderr.decode()
        command=[str(exe),'export'];q=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=240);r['export']=dict(exit_code=q.returncode,stdout=packed(q.stdout),stderr=packed(q.stderr));save();assert q.returncode==0,q.stderr.decode();cases=[{} for _ in CUT]
        for line in q.stdout.decode().splitlines():
            z=line.split(',');v=np.array(list(map(float,z[2:])));cases[int(z[1])][z[0]]=v if z[0]=='DC' else v.reshape(68,68)
        models=[derive(c) for c in cases];r['models']=models;save();spec=[(i,a,False) for i in range(3) for a in [.01,.1,1.]]+[(1,.01,True)]
        with pack.open('xb') as sink:
            for index,amplitude,dynamic in spec:
                for step in [500,250]:
                    command=[str(exe),str(CUT[index]),str(amplitude),str(step),'dynamic' if dynamic else 'static'];start=time.monotonic()
                    with stream.open('xb') as f:q=subprocess.run(command,cwd=ROOT,env=env,stdout=f,stderr=subprocess.PIPE,timeout=240)
                    p=dict(index=index,cutoff=CUT[index],amplitude_v=amplitude,dynamic=dynamic,step_ns=step,elapsed_s=time.monotonic()-start,exit_code=q.returncode,stderr=packed(q.stderr),full_stream_sha256=sha(stream),full_stream_bytes=stream.stat().st_size);r['profiles'].append(p);save();assert q.returncode==0,q.stderr.decode();assert stream.stat().st_size<=32*1024**2;a=np.fromfile(stream,dtype='<f8').reshape(-1,139);full=a[:,3:71]+a[:,71:139];assert np.isfinite(a).all();reduced,switches=simulate(models,a[:,0],a[:,1],index,dynamic);p.update(metrics(full,reduced));p['switches']=switches
                    select=np.unique(np.r_[np.arange(0,len(a),64),len(a)-1,p['worst_row'],[int(round(t/(step*1e-9))) for t in [.001,.002,.003]]]);p['state_rows']=select.tolist();p['state_window']=encode_window(a[select],sink);signals=np.column_stack([a[:,:3],full[:,61],full[:,66],full[:,6]]);p['signal_window']=encode_window(signals,sink);sink.flush();assert decode_window(p['state_window'],pack).tobytes()==a[select].tobytes();assert decode_window(p['signal_window'],pack).tobytes()==signals.tobytes()
                    if not p['domain_admitted']:
                        replay=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=240);p['unchanged_native_replay']=dict(exit_code=replay.returncode,stdout_sha256=hashlib.sha256(replay.stdout).hexdigest(),stderr=packed(replay.stderr),identical=replay.returncode==0 and replay.stdout==stream.read_bytes());assert p['unchanged_native_replay']['identical']
                    stream.unlink();p['full_grid_retired_after_metrics_and_selected_byte_checks']=True;save();print('CONTROL_RESERVE',index,amplitude,dynamic,step,p['all_nodes_error_v'],p['domain_admitted'],flush=True)
        r['passed']=True
    except Exception:
        r['failure']=traceback.format_exc();save()
        if stream.exists():r['failed_stream']=packed(stream.read_bytes());stream.unlink()
        if command:
            q=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=240);r['unchanged_failure_replay']=dict(exit_code=q.returncode,stdout=packed(q.stdout),stderr=packed(q.stderr))
    finally:
        for p in [exe,stream]:
            if p.exists():assert p.resolve().parent==AREA.resolve();p.unlink()
    sources.unchanged();r.update(temporary_area_empty=not list(AREA.iterdir()),pack_sha256=sha(pack) if pack.exists() else None,pack_bytes=pack.stat().st_size if pack.exists() else 0);save();print('CONTROL_DONE',r['passed'],r.get('failure',''))
    if not r['passed']:raise SystemExit(1)
if __name__=='__main__':main()
