"""Bounded identity, independent hybrid Newton and reserved physical comparisons."""
import json,os,subprocess,traceback,hashlib
from pathlib import Path
import numpy as np
from prepare_dual_chain import ROOT,sha,write
from affine_evidence import Sources
from check_vco_phase import COMPILER,LIB
from check_hybrid_voice import packed
from vco_family import decode_window
from check_charge_control import metrics
from recovery_port_model import cases,build,law,stage,dense_stage,simulate
AREA=ROOT/'tmp/lab-current'

def audit(r):
    old=json.loads((ROOT/'evidence/charge_control_tests01.json').read_text(encoding='utf8'));assert sha(Path(COMPILER))==old['compiler']['sha256'] and sha(LIB)==old['private_input_sha256'][LIB.relative_to(ROOT).as_posix()]
    r.update(compiler_sha256=sha(Path(COMPILER)),library_sha256=sha(LIB));models=[build(c) for c in cases()];m=models[1];dc=cases()[1]['DC'];vectors=[]
    for k in range(64):
        delta=np.zeros(68);delta[16:24]=(1e-3 if k<32 else .05)*np.sin(np.arange(8)*1.73+k*.91);vectors.append(delta)
    states=np.tile(dc,(65,1));states[1:,:68]+=vectors;exe=AREA/'recovery.exe';env=dict(os.environ,PATH='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+os.environ['PATH'])
    try:
        command=[COMPILER,'--edition=2021','-C','opt-level=2','-C','strip=symbols','-C','link-arg=-Wl,--stack,33554432','-A','dead_code','-A','unused_imports',str(ROOT/'tools/recovery_port_oracle.rs'),'--extern','rf_d_circuit='+str(LIB),'-o',str(exe)]
        p=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=120);r['compile']=dict(exit_code=p.returncode,stderr=packed(p.stderr));assert p.returncode==0,p.stderr.decode()
        raw=states.astype('<f8').tobytes();p=subprocess.run([str(exe)],input=raw,env=env,capture_output=True,timeout=240);assert p.returncode==0,p.stderr.decode();native=np.frombuffer(p.stdout,dtype='<f8').reshape(65,4692);r['native']=dict(input=packed(raw),output_sha256=hashlib.sha256(p.stdout).hexdigest(),output_bytes=len(p.stdout),exit_code=p.returncode)
        base=native[0,:68];g=native[0,68:].reshape(68,68);current_error=0.;jac_error=0.
        for k,delta in enumerate(vectors):
            n,s=law(m,m['e']@delta);expected=base+g@delta+m['d']@n;got=native[k+1,:68];scaled=float(max(abs(expected-got)/(1e-12+1e-10*abs(got))));assert scaled<=1,scaled
            expected_j=g+(m['d']*s)@m['e'];actual_j=native[k+1,68:].reshape(68,68);je=float(np.max(abs(expected_j-actual_j)));assert je<=1e-10,je
            current_error=max(current_error,float(max(abs(expected-got))));jac_error=max(jac_error,je)
        r['native_law_identity']=dict(directions=64,max_current_error_a=current_error,max_jacobian_error_s=jac_error)
    finally:
        if exe.exists():assert exe.resolve().parent==AREA.resolve();exe.unlink()
    records=[]
    for index,m in enumerate(models):
        for k in range(16):
            q=np.sin(np.arange(18)*.73+k*.2)*1e-5;u=.1*np.sin(k*.7);new,x,it,err=stage(m,q,u);dense,kcl=dense_stage(m,q,u);error=float(max(abs(x-dense)));qe=float(max(abs(m['a']@x-new)));assert error<=1e-9 and kcl<=1e-12 and qe<=1e-11
            z=m['e']@x;n,s=law(m,z);j=np.eye(8)+m['p']*s;eps=1e-6;fd=np.column_stack([( (z+np.eye(8)[l]*eps)+m['p']@law(m,z+np.eye(8)[l]*eps)[0]-(z-np.eye(8)[l]*eps)-m['p']@law(m,z-np.eye(8)[l]*eps)[0])/(2*eps) for l in range(8)])
            derivative=float(np.max(abs(j-fd)/(1e-10+1e-5*abs(j))));assert derivative<=1,derivative
            records.append(dict(index=index,node_error_v=error,kcl_a=kcl,charge_error_v=qe,root_iterations=it,jacobian_fd_scaled=derivative))
    r['independent_stages']=records
    # Regenerate maps from own stamp. No parameter fitted to these reservations.
    corpus=json.loads((ROOT/'evidence/charge_control_native01.json').read_text(encoding='utf8'));r['corpus_sha256']=sha(ROOT/'evidence/charge_control_native01.json');r['pack_sha256']=sha(ROOT/corpus['pack']);profiles=[]
    for p in corpus['profiles']:
        if p['dynamic'] or p['step_ns']!=250:continue
        signals=decode_window(p['signal_window'],ROOT/corpus['pack']);states=decode_window(p['state_window'],ROOT/corpus['pack']);full=states[:,3:71]+states[:,71:139]
        model=build(cases()[p['index']],signals[1,0]-signals[0,0]);x,it=simulate(model,signals[:,0],signals[:,1]);selected=x[np.array(p['state_rows'])];values=metrics(full,selected)
        dense_ports=np.zeros((len(signals),68));dense_candidate=dense_ports.copy()
        for col,node in [(3,61),(4,66),(5,6)]:dense_ports[:,node]=signals[:,col];dense_candidate[:,node]=x[:,node]
        ports=metrics(dense_ports,dense_candidate);admitted=bool(values['node_gate_pass'] and ports['panel_gate_pass'] and ports['audio_gate_pass']);row=dict(index=p['index'],amplitude_v=p['amplitude_v'],comparison_step_ns=250,sparse_all_nodes=values,dense_ports=ports,domain_admitted=admitted,max_root_iterations=it,full_node_grid_unavailable=True)
        if not admitted:
            replay,_=simulate(model,signals[:,0],signals[:,1]);row['unchanged_replay_identical']=replay.tobytes()==x.tobytes();assert row['unchanged_replay_identical']
        profiles.append(row);print('RECOVERY_RESERVE',row['index'],row['amplitude_v'],values['all_nodes_error_v'],ports['j7_rms_relative'],admitted,flush=True)
    r['reserved_profiles']=profiles
    # Generated implementation maps: no source-array work inside processing.
    out='//! Own RF-D recovery port condensation. Generated by check_recovery_port.py.\n'
    types={'dc':'[f64;68]','iexp':'[f64;8]','xh':'[[f64;18];68]','xu':'[f64;68]','xd':'[[f64;8];68]','qh':'[[f64;18];18]','qu':'[f64;18]','qd':'[[f64;8];18]','zh':'[[f64;18];8]','zu':'[f64;8]','p':'[[f64;8];8]'}
    def rust(v):return '['+','.join(map(rust,v))+']' if isinstance(v,list) else format(v,'.17e')
    for key,ty in types.items():out+=f'pub const {key.upper()}:[{ty};3]='+rust([m[key].tolist() for m in models])+';\n'
    target=ROOT/'tools/recovery_port_data.rs'
    if target.exists():assert target.read_bytes()==out.encode()
    else:target.write_bytes(out.encode())
    r['generated_sha256']={target.relative_to(ROOT).as_posix():sha(target)}
    r.update(passed=True,static_scope_only=True,retained_charge_coordinates=18,nonlinear_junctions=8,no_ca72_code_or_calibration_copied=True,full_voice_rt=False,hardware_fidelity=False,temporary_area_empty=not list(AREA.iterdir()))

def main():
    sources=Sources(['tools/check_recovery_port.py','tools/recovery_port_model.py','tools/recovery_port_oracle.rs','docs/RECOVERY_PORT_PROTOCOLO.md']);r=dict(passed=False,**sources.fields())
    k=1
    while(ROOT/f'evidence/recovery_port_model{k:02d}.json').exists():k+=1
    try:audit(r)
    except Exception:
        r['failure']=traceback.format_exc()
        try:replay={};audit(replay);r['unchanged_replay']=replay
        except Exception:r['unchanged_replay_failure']=traceback.format_exc()
    sources.unchanged();write(ROOT/f'evidence/recovery_port_model{k:02d}.json',r);print('RECOVERY_MODEL',r['passed'],r.get('failure',''),flush=True)
    if not r['passed']:raise SystemExit(1)
if __name__=='__main__':main()
