"""Frozen stationary CV/BUS split with source currents, bounded exports and exact windows."""
import json,subprocess,time,traceback,shutil
from dataclasses import asdict
import numpy as np
from prepare_dual_chain import ROOT,sha,write
from affine_evidence import Sources
from check_hybrid_voice import packed
from vco1_circuit_reference import Scenario,netlist,VECTORS,EXPECTED_EXE_SHA
from lm741_reference import MODEL,EXE
from vco_family_raw import read as read_raw
from vco_cv_load_analysis import R8,R11,compare
from vco1_circuit_probes import observations
from vco_family import CV,BUS,cycle,encode_window,decode_window,RESISTANCE
AREA=ROOT/'tmp/lab-current';PACK=ROOT/'evidence/vco_family_windows03.xz'
EXTRA=['v(ic1_sum)','i(vmixer)','i(vbend)','i(vtune)','i(vkeyboard)','i(vmod)','i(vext)','i(vosc1_range)']
OWN=['tools/check_vco_family.py','tools/vco_family.py','docs/VCO_FAMILIA_PROTOCOLO.md','tools/vco1_circuit_reference.py','tools/vco1_circuit_probes.py','tools/render_vco1_circuit.py','tools/vco_cv_load_analysis.py','tools/vco_family_raw.py','docs/VCO_FAMILIA_EXPORT_BINARIO.md','evidence/vco_family_binary_control01.json']
LAST=None

def run(scene,sink):
    global LAST
    export=AREA/'family.raw';deck=AREA/'family.cir';text,meta=netlist(scene,export)
    text=text.replace('.save '+' '.join(VECTORS),'.save '+' '.join(VECTORS+EXTRA),1)
    text=text.replace(f"wrdata {export.as_posix()} {' '.join(VECTORS)}",f"set filetype=binary\nwrite {export.as_posix()} {' '.join(VECTORS+EXTRA)}",1)
    deck.write_text(text,encoding='utf8',newline='\n');command=[str(ROOT/EXE),'-n','-b',str(deck)];start=time.monotonic()
    p=subprocess.run(command,cwd=(ROOT/EXE).parent,capture_output=True,timeout=180)
    r=dict(scenario=asdict(scene),command=command,deck=packed(text.encode()),stdout=packed(p.stdout),stderr=packed(p.stderr),exit_code=p.returncode,elapsed_s=time.monotonic()-start);LAST=r
    assert p.returncode==0 and export.exists() and not any(s in(p.stdout+p.stderr).lower() for s in [b'error:',b'aborted',b'timestep too small']),r
    r.update(export_sha256=sha(export),export_bytes=export.stat().st_size)
    assert export.stat().st_size<256*1024**2
    raw,layout=read_raw(export,VECTORS+EXTRA);r['binary_layout']=layout
    assert raw.shape[1]==25 and np.isfinite(raw).all() and raw[0,0]==0 and abs(raw[-1,0]-.03)<1e-14 and np.all(np.diff(raw[:,0])>0)
    assert np.max(np.diff(raw[:,0]))<=scene.max_step_s*(1+1e-7)
    r.update(export_sha256=sha(export),export_bytes=export.stat().st_size,rows=len(raw),measurements=observations(raw,None))
    m=r['measurements'];assert m['period_spread_relative']<=1e-5 and m['cycle_charge_check']['relative_imbalance']<=.002
    r['reduction'],edges=cycle(raw)
    first=max(0,int(np.searchsorted(raw[:,0],edges[-2]))-2);last=raw[first:].copy()
    r['window']=encode_window(last,sink);r['window_pack']=PACK.relative_to(ROOT).as_posix();assert decode_window(r['window'],PACK).tobytes()==last.astype('<f8').tobytes()
    controls=np.array([-2.1,-2.1,scene.keyboard_v,-2.1,-2.1,-2.1]);cv=(controls-last[:,17,None])/RESISTANCE
    bus=(scene.imposed_mixer_v-last[:,13])/33000.;w=(last[:,3]/12500.+scene.imposed_mixer_v/33000.)/(2/12500.+1/33000.)
    r['original_port_laws']=dict(cv_source_max_error_a=float(np.max(np.abs(cv+last[:,19:25]))),bus_source_max_error_a=float(np.max(np.abs(bus+last[:,18]))),wiper_max_error_v=float(np.max(np.abs(w-last[:,13]))))
    assert r['original_port_laws']['cv_source_max_error_a']<=2e-12 and r['original_port_laws']['bus_source_max_error_a']<=2e-12 and r['original_port_laws']['wiper_max_error_v']<=2e-7,r['original_port_laws']
    export.unlink();return r

def main():
    assert not list(AREA.iterdir()) and not PACK.exists() and shutil.disk_usage(ROOT).free>1024**3
    old=json.loads((ROOT/'evidence/vco_cv_load_tests01.json').read_text(encoding='utf8'));assert sha(ROOT/EXE)==EXPECTED_EXE_SHA==old['private_input_sha256'][EXE] and sha(ROOT/MODEL)==old['private_input_sha256'][MODEL]
    sources=Sources(OWN);k=1
    while(ROOT/f'evidence/vco_family_oracle{k:02d}.json').exists():k+=1
    out=ROOT/f'evidence/vco_family_oracle{k:02d}.json';r=dict(passed=False,**sources.fields(),pack=PACK.relative_to(ROOT).as_posix(),private_used_sha256={n:sha(ROOT/n) for n in [EXE,MODEL]},training=[],reserved=[],method=[],current_listening_sha256=sha(ROOT/old['new_listening']['path']),new_audio=False,physical_fidelity=False,real_time=False)
    def save():write(out,r)
    prior=json.loads((ROOT/'evidence/vco_family_oracle02.json').read_text(encoding='utf8'));control=json.loads((ROOT/'evidence/vco_family_binary_control01.json').read_text(encoding='utf8'));assert control['passed'] and prior['temporary_area_empty'] and len(prior['training'])==6 and sha(ROOT/prior['pack'])==prior['pack_sha256']
    r['reused_training_reference']=dict(path='evidence/vco_family_oracle02.json',sha256=sha(ROOT/'evidence/vco_family_oracle02.json'),count=6,pack=prior['pack'],pack_sha256=prior['pack_sha256'])
    r['training']=[dict(x,window_pack=prior['pack']) for x in prior['training']]
    save()
    try:
        with PACK.open('xb') as sink:
            for cv in CV:
                for bus in BUS:
                    if len(r['training'])<6:raise AssertionError('reused prefix lost')
                    if (float(cv),float(bus)) in [(x['scenario']['keyboard_v'],x['scenario']['imposed_mixer_v']) for x in r['training']]:continue
                    s=Scenario(keyboard_v=float(cv),imposed_mixer_v=float(bus),r8_fraction=R8,r11_active_ohm=R11,duration_s=.03,max_step_s=125e-9);r['training'].append(run(s,sink));save();print('TRAIN',cv,bus,r['training'][-1]['reduction']['frequency_hz'],flush=True)
            for cv in [-2.6,-1.6,-.6]:
                s=Scenario(keyboard_v=cv,imposed_mixer_v=.0625,r8_fraction=R8,r11_active_ohm=R11,duration_s=.03,max_step_s=125e-9);r['reserved'].append(run(s,sink));save();print('RESERVED',cv,flush=True)
            for method,step in [('trap',125e-9),('gear',62.5e-9)]:
                s=Scenario(keyboard_v=-1.6,imposed_mixer_v=.0625,r8_fraction=R8,r11_active_ohm=R11,duration_s=.03,max_step_s=step,method=method);r['method'].append(run(s,sink));save();print('METHOD',method,step,flush=True)
        r['passed']=True
    except Exception:
        r['failure']=traceback.format_exc();r['failed_process']=LAST;save()
        try:
            with PACK.open('ab') as sink:run(s,sink)
            r['unchanged_replay']='unexpected pass'
        except Exception:r['unchanged_replay']=traceback.format_exc();r['replay_process']=LAST
    finally:
        for name in ['family.txt','family.raw','family.cir']:
            p=(AREA/name).resolve();assert p.parent==AREA.resolve()
            if p.exists():assert p.is_file();p.unlink()
    sources.unchanged();r.update(temporary_area_empty=not list(AREA.iterdir()),pack_sha256=sha(PACK),pack_bytes=PACK.stat().st_size);save()
    print('FAMILY_ORACLES',r['passed'],r.get('failure',''),flush=True)
    if not r['passed']:raise SystemExit(1)
if __name__=='__main__':main()
