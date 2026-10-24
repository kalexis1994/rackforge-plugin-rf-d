"""Full documentary VCO with free mixer BUS/C27, fixed BASE boundary."""
import json,subprocess,time,traceback,shutil
from dataclasses import asdict
import numpy as np
from prepare_dual_chain import ROOT,sha,write
from affine_evidence import Sources
from check_hybrid_voice import packed
from vco1_circuit_reference import Scenario,netlist,VECTORS,EXPECTED_EXE_SHA
from lm741_reference import EXE,MODEL
from vco_cv_load_analysis import R8,R11
from vco_family_receipts import read
from vco_family import encode_window,decode_window
from vco_family_raw import read as read_raw
from family_mixer_analysis import CVS,initial_bus,capture_spice,compare
AREA=ROOT/'tmp/lab-current';PACK=ROOT/'evidence/family_mixer_scaled_windows01.xz'
V=['v(ramp_c1)','v(saw_output_9b)','v(tri_output_21b)','v(rect_output_20b)','v(r6_wiper)','v(mix_bus_board4_pin4)','i(vbase)','v(ic1_sum)','i(vkeyboard)']
OWN=['tools/family_mixer_scaled_oracle.py','docs/FAMILIA_MIXER_COORDENADA.md','tools/check_family_mixer_oracle.py','tools/family_mixer_analysis.py','docs/FAMILIA_MIXER_PROTOCOLO.md','tools/vco_family.py','tools/vco_family_raw.py','tools/vco1_circuit_reference.py','evidence/mixer_panel_bus.json','crates/rf-d-circuit/src/mixer_c27.rs']
LAST=None
def run(cv,load,method,step,sink,training):
    global LAST
    export=AREA/'coupled.raw';deck=AREA/'coupled.cir';scene=Scenario(keyboard_v=cv,r8_fraction=R8,r11_active_ohm=R11,duration_s=.03,max_step_s=step,method=method);text,meta=netlist(scene,export)
    marker='Vmixer MIX_BUS_BOARD4_PIN4 0 0';assert text.count(marker)==1
    lines=['Rmix_ext MIX_BUS_BOARD4_PIN4 0 33000','C27_state C27_STATE 0 1e-9','Ecap MIX_BUS_BOARD4_PIN4 BASE_Q29_boundary C27_STATE 0 .01','Fcap C27_STATE 0 Ecap -.01','Vbase BASE_Q29_boundary 0 0']
    if load:
        for name,r in [('osc2',33000),('osc3',33000),('noise',11000)]:lines.extend([f'Rmix_{name}_hi 0 mix_{name}_w 12500',f'Rmix_{name}_lo mix_{name}_w 0 12500',f'Rmix_{name}_series mix_{name}_w MIX_BUS_BOARD4_PIN4 {r}'])
    start=initial_bus(training,cv,load);text=text.replace(marker,'\n'.join(lines),1).replace('.ic v(RAMP_C1)=0',f'.ic v(RAMP_C1)=0 v(C27_STATE)={start/.01:.17e}',1)
    text=text.replace('.save '+' '.join(VECTORS),'.save '+' '.join(V),1).replace(f"wrdata {export.as_posix()} {' '.join(VECTORS)}",f"set filetype=binary\nwrite {export.as_posix()} {' '.join(V)}",1)
    deck.write_text(text,encoding='utf8',newline='\n');tic=time.monotonic();p=subprocess.run([str(ROOT/EXE),'-n','-b',str(deck)],cwd=(ROOT/EXE).parent,capture_output=True,timeout=180)
    r=dict(cv_v=cv,load=load,scenario=asdict(scene),initial_bus_v=start,deck=packed(text.encode()),stdout=packed(p.stdout),stderr=packed(p.stderr),exit_code=p.returncode,elapsed_s=time.monotonic()-tic);LAST=r
    assert p.returncode==0 and export.exists() and not any(x in(p.stdout+p.stderr).lower() for x in [b'error:',b'aborted',b'timestep too small'])
    r.update(export_sha256=sha(export),export_bytes=export.stat().st_size);assert r['export_bytes']<256*1024**2
    raw,layout=read_raw(export,V);assert abs(raw[-1,0]-.03)<1e-14 and np.max(np.diff(raw[:,0]))<=step*(1+1e-7);r.update(binary_layout=layout,rows=len(raw))
    tail,m=capture_spice(raw,load);r.update(measurements=m,window=encode_window(tail,sink));assert decode_window(r['window'],PACK).tobytes()==tail.astype('<f8').tobytes();export.unlink();return r
def main():
    assert not list(AREA.iterdir()) and not PACK.exists() and shutil.disk_usage(ROOT).free>1024**3
    old=read('evidence/vco_family_tests01.json');assert sha(ROOT/EXE)==EXPECTED_EXE_SHA==old['private_input_sha256'][EXE] and sha(ROOT/MODEL)==old['private_input_sha256'][MODEL]
    sources=Sources(OWN);r=dict(passed=False,**sources.fields(),cases=[],method=[],pack=PACK.relative_to(ROOT).as_posix(),private_used_sha256={n:sha(ROOT/n) for n in [EXE,MODEL]},family_data_sha256=sha(ROOT/'tools/vco_family_data.rs'));training=read('evidence/vco_family_oracle03.json')['training']
    def save():write(ROOT/'evidence/family_mixer_scaled_oracle01.json',r)
    save()
    try:
        with PACK.open('xb') as sink:
            for cv in CVS:
                for load in [0,1]:
                    args=(cv,load,'gear',125e-9);r['cases'].append(run(*args,sink,training));save();print('COUPLED_ORACLE',cv,load,flush=True)
            for method,step in [('trap',125e-9),('gear',62.5e-9)]:
                args=(-1.6,1,method,step);x=run(*args,sink,training);x['comparison']=compare(x['measurements'],r['cases'][3]['measurements']);r['method'].append(x);save();print('COUPLED_METHOD',method,step,flush=True)
        r['passed']=True
    except Exception:
        r.update(failure=traceback.format_exc(),failed_process=LAST);save()
        try:
            with PACK.open('ab') as sink:run(*args,sink,training)
            r['unchanged_replay']='unexpected pass'
        except Exception:r.update(unchanged_replay=traceback.format_exc(),replay_process=LAST)
    finally:
        for name in ['coupled.raw','coupled.cir']:
            p=AREA/name
            if p.exists():assert p.resolve().parent==AREA.resolve();p.unlink()
    sources.unchanged();r.update(pack_sha256=sha(PACK),pack_bytes=PACK.stat().st_size,temporary_area_empty=not list(AREA.iterdir()));save();print('COUPLED_ORACLE_COMPLETE',r['passed'],r.get('failure',''),flush=True)
    if not r['passed']:raise SystemExit(1)
if __name__=='__main__':main()
