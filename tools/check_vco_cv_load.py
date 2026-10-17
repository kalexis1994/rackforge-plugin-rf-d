"""Bounded CV/BUS campaign; full conditional circuit, no imposed oscillator cycle."""
import argparse,gzip,hashlib,json,os,subprocess,time,traceback
from pathlib import Path
from dataclasses import asdict
import numpy as np
from prepare_dual_chain import ROOT,sha,write
from affine_evidence import Sources
from check_hybrid_voice import packed,unpack
from check_vco_phase import COMPILER,LIB
from prepare_vco_cv_load import images,ORIGINS
from vco_cv_load_analysis import config,capture,decimal_audit,compare,R8,R11
from vco1_circuit_reference import Scenario,netlist,EXPECTED_EXE_SHA
from vco1_stamp_reference import expressions,inventory
from lm741_reference import MODEL,EXE
from render_nominal import safe
BASE='evidence/pitch_render_tests01.json'
OWN=['tools/check_vco_cv_load.py','tools/prepare_vco_cv_load.py','tools/vco_cv_load_analysis.py','tools/vco_cv_load_probe.rs','docs/VCO_CV_CARGA_PROTOCOLO.md','docs/VCO_CV_CARGA_SEMILLA_PROTOCOLO.md',*images(), 'tools/vco1_circuit_reference.py','tools/vco1_circuit_probes.py','tools/vco1_stamp_reference.py','tools/vco1_increment_circuit.py','tools/vco1_radau_reference.py','tools/vco1_native_inventory.py','tools/render_vco1_circuit.py','tools/vco1_increment_devices.py','tools/lm741_port_reference.py','tools/lm741_reference.py','crates/rf-d-circuit/src/vco1_stamp.rs','crates/rf-d-circuit/src/vco1_stamp_data.rs','crates/rf-d-circuit/src/vco1_startup.rs','crates/rf-d-circuit/src/vco1_newton.rs','crates/rf-d-circuit/src/vco_bjt.rs','crates/rf-d-circuit/src/vco_jfet.rs','crates/rf-d-circuit/src/lm741.rs','crates/rf-d-circuit/src/junction_charge.rs','evidence/vco1_circuit_calibration_v1.json.gz']
AREA=ROOT/'tmp/lab-current';NAMES=['vco.lock','vco.exe','stream.bin','dc.cir','dc.txt','transient.cir','transient.txt']
class Laboratory:
    def __enter__(self):
        safe(AREA);assert not list(AREA.iterdir());safe(AREA/NAMES[0]).open('xb').close();return self
    def __exit__(self,*exc):
        for name in reversed(NAMES):
            p=safe(AREA/name)
            if p.exists():assert p.is_file();p.unlink()
        assert not list(AREA.iterdir())
def next_path():
    k=1
    while(ROOT/f'evidence/vco_cv_load_native{k:02d}.json').exists():k+=1
    return ROOT/f'evidence/vco_cv_load_native{k:02d}.json'
LAST_SPICE=None
def spice(scene,dc=False,seed=None):
    global LAST_SPICE
    export=AREA/('dc.txt' if dc else'transient.txt');deck=AREA/('dc.cir' if dc else'transient.cir');text,meta=netlist(scene,export)
    if dc:
        text=text.split('.ic ')[0].replace('reltol=1e-7 abstol=1e-13 vntol=1e-8','reltol=1e-10 abstol=1e-15 vntol=1e-12')+'Vstartup RAMP_C1 0 0\n.control\nop\nset numdgt=17\nset wr_vecnames\nset wr_singlescale\nwrdata '+export.as_posix()+' '+' '.join(expressions(inventory(scene)))+' real(i(vstartup))\nquit\n.endc\n.end\n'
    if dc:
        assert seed is not None and len(seed)==134
        nodes=expressions(inventory(scene))[:98];text=text.replace('Vstartup RAMP_C1 0 0\n','Vstartup RAMP_C1 0 0\n.nodeset '+' '.join(f'{n}={v:.17e}' for n,v in zip(nodes,seed[:98]))+'\n',1)
        text=text.replace('.options temp=25','.options itl1=1000 itl2=1000 temp=25',1)
    deck.write_text(text,encoding='utf8',newline='\n');command=[str(ROOT/EXE),'-n','-b',str(deck)];start=time.monotonic();p=subprocess.run(command,cwd=(ROOT/EXE).parent,capture_output=True,timeout=180);record=dict(command=command,scenario=asdict(scene),deck=packed(text.encode()),stdout=packed(p.stdout),stderr=packed(p.stderr),exit_code=p.returncode,elapsed_s=time.monotonic()-start)
    LAST_SPICE=record
    assert p.returncode==0 and export.exists() and not any(x in(p.stdout+p.stderr).lower() for x in [b'error:',b'aborted',b'timestep too small']),'SPICE rejected; full process retained in spice_failed_original'
    raw=np.loadtxt(export,skiprows=1,ndmin=2);assert np.isfinite(raw).all();record.update(export_sha256=sha(export),export_bytes=export.stat().st_size,rows=len(raw));assert export.stat().st_size<256*1024*1024
    if dc:
        assert raw.shape==(1,136)
        record['original_root']=raw[-1,1:].tolist();record['dc_sweep']=packed(raw.astype('<f8').tobytes())
    else:
        assert raw.shape[1]==17 and raw[0,0]==0 and abs(raw[-1,0]-.03)<=1e-14 and np.all(np.diff(raw[:,0])>0) and max(np.diff(raw[:,0]))<=scene.max_step_s*(1+1e-7)
        record['cycle']=capture(raw)
    export.unlink();return record
def native(command,env):
    output=AREA/'stream.bin';start=time.monotonic()
    with output.open('wb') as out:
        with subprocess.Popen(command,cwd=ROOT,env=env,stdout=out,stderr=subprocess.PIPE) as p:
            try:
                lines=[]
                for line in p.stderr:
                    lines.append(line)
                    if line.startswith(b'PROGRESS,'):print('VCO_NATIVE',line.decode().strip(),flush=True)
                    if time.monotonic()-start>2400:p.kill();raise TimeoutError('native process budget')
                code=p.wait()
            finally:
                if p.poll() is None:p.kill();p.wait()
    size=output.stat().st_size;r=dict(command=command,exit_code=code,stderr=packed(b''.join(lines)),elapsed_s=time.monotonic()-start,stream_bytes=size,stream_sha256=sha(output));assert size<256*1024*1024
    if code!=0:r['failed_stream']=packed(output.read_bytes());return r
    assert size%(17*8)==0;raw=np.memmap(output,dtype='<f8',mode='r',shape=(size//(17*8),17));assert np.isfinite(raw).all() and np.all(np.diff(raw[:,0])>0) and abs(raw[-1,0]-.03)<=1e-17
    r['cycle']=capture(raw);r['rows']=len(raw);del raw;return r
def main():
    path=next_path();assert not list(AREA.iterdir());old=json.loads((ROOT/BASE).read_text(encoding='utf8'));sources=Sources([*OWN,'docs/VCO_CV_CARGA_DC_CONTINUACION.md','tools/diagnose_vco_cv_load_dc.py','docs/VCO_CV_CARGA_DC_PRESUPUESTO.md']);used={n:sha(ROOT/n) for n in [*ORIGINS.values(),LIB.relative_to(ROOT).as_posix(),MODEL,EXE]}
    for n,h in used.items():assert old['private_input_sha256'][n]==h,n
    assert sha(Path(COMPILER))==old['compiler']['sha256'] and used[EXE]==EXPECTED_EXE_SHA
    for n,s in images().items():assert(ROOT/n).read_bytes()==s.encode()
    r=dict(passed=False,**sources.fields(),private_used_sha256=used,compiler_sha256=sha(Path(COMPILER)),previous_wav_sha256=sha(ROOT/old['new_listening']['path']),dc=[],spice=[],profiles=[],physical_fidelity=False,physical_cv_general=False,real_time=False,new_audio=False)
    def save():write(path,r)
    env=dict(os.environ,PATH='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+os.environ['PATH']);phase='compile';command=[];last=None;save()
    with Laboratory():
        try:
            command=[COMPILER,'--edition=2021','-C','opt-level=2','-C','strip=symbols','-C','link-arg=-Wl,--stack,33554432','-A','unused_imports','-A','dead_code',str(ROOT/'tools/vco_cv_load_probe.rs'),'--extern','rf_d_circuit='+str(LIB),'-o',str(AREA/'vco.exe')];last=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=120);assert last.returncode==0,last.stderr.decode(errors='replace')
            phase='native_roots';command=[str(AREA/'vco.exe'),'roots'];last=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=180);r['roots']=dict(command=command,exit_code=last.returncode,stdout=packed(last.stdout),stderr=packed(last.stderr));save();assert last.returncode==0,last.stderr.decode(errors='replace')
            seeds={int(z[1]):list(map(float,z[2:136])) for z in [line.split(',') for line in last.stdout.decode().splitlines()] if z[0]=='SEED'};assert len(seeds)==12
            phase='spice_dc'
            for i in range(12):
                c=config(i);scene=Scenario(keyboard_v=c[7],r8_fraction=R8,r11_active_ohm=R11,imposed_mixer_v=c[3],duration_s=.03,max_step_s=125e-9);dc_seed=seeds[i];x=spice(scene,True,dc_seed);x['scene']=i;r['dc'].append(x);save();print('VCO_DC',i,flush=True)
            phase='decimal';r['decimal']=decimal_audit(unpack(r['roots']['stdout']),[x['original_root'] for x in r['dc']]);save();print('VCO_DECIMAL_PASS',len(r['decimal']['dc']),len(r['decimal']['local']),flush=True)
            phase='spice_trajectories'
            for i in [0,2,3,5,6,8,9,11,5]:
                method='trap' if len(r['spice'])==8 else'gear';c=config(i);scene=Scenario(keyboard_v=c[7],r8_fraction=R8,r11_active_ohm=R11,imposed_mixer_v=c[3],duration_s=.03,max_step_s=125e-9,method=method);x=spice(scene);x['scene']=i;r['spice'].append(x);save();print('VCO_SPICE',i,method,x['cycle']['measurements']['frequency_hz'],flush=True)
            r['spice_method_comparison']=compare(r['spice'][3]['cycle']['measurements'],r['spice'][8]['cycle']['measurements']);save()
            for maximum in [131072,65536]:
                phase='native_trajectory';command=[str(AREA/'vco.exe'),str(maximum)];x=native(command,env);x['maximum_half_ticks']=maximum;r['profiles'].append(x);save();assert x['exit_code']==0,unpack(x['stderr']).decode();(AREA/'stream.bin').unlink()
                phase='native_comparison';x['spice_comparisons']=[compare(x['cycle']['measurements'],r['spice'][k]['cycle']['measurements']) for k in [3,8]];save();print('VCO_PROFILE_PASS',maximum,x['cycle']['measurements']['frequency_hz'],flush=True)
            phase='refinement';r['temporal_refinement']=compare(*[x['cycle']['measurements'] for x in r['profiles']]);r['passed']=True
        except Exception:
            r.update(failure=traceback.format_exc(),failed_phase=phase,failed_command=command);save()
            if phase.startswith('spice'):r['spice_failed_original']=LAST_SPICE
            if phase in ['compile','native_roots','native_trajectory']:
                if last is not None:r['failed_process']=dict(exit_code=last.returncode,stdout=packed(last.stdout),stderr=packed(last.stderr))
                replay=native(command,env) if phase=='native_trajectory' else subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=180)
                r['unchanged_replay']=replay if isinstance(replay,dict) else dict(exit_code=replay.returncode,stdout=packed(replay.stdout),stderr=packed(replay.stderr))
            else:
                try:
                    if phase=='decimal':decimal_audit(unpack(r['roots']['stdout']),[x['original_root'] for x in r['dc']])
                    elif phase=='refinement':compare(*[x['cycle']['measurements'] for x in r['profiles']])
                    elif phase=='native_comparison':[compare(x['cycle']['measurements'],r['spice'][k]['cycle']['measurements']) for k in [3,8]]
                    else:spice(scene,phase=='spice_dc',dc_seed if phase=='spice_dc' else None)
                    r['unchanged_gate_replay']='unexpected pass'
                except Exception:
                    r['unchanged_gate_replay']=traceback.format_exc()
                    if phase.startswith('spice'):r['spice_unchanged_replay']=LAST_SPICE
    sources.unchanged();assert all(sha(ROOT/n)==h for n,h in used.items());assert sha(ROOT/old['new_listening']['path'])==r['previous_wav_sha256'];r['temporary_area_empty']=not list(AREA.iterdir());save();print('VCO_CV_LOAD',r['passed'],r.get('failure',''),flush=True)
    if not r['passed']:raise SystemExit(1)
if __name__=='__main__':main()
