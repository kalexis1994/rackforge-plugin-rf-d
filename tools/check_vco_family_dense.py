"""Refine four held-out output oracles, without fitting a new family."""
import math,subprocess,time,traceback,shutil
import numpy as np
from prepare_dual_chain import ROOT,sha,write
from affine_evidence import Sources
from check_hybrid_voice import packed
from vco1_circuit_reference import Scenario,netlist,VECTORS,crossings
from lm741_reference import EXE,MODEL
from vco_cv_load_analysis import R8,R11
from vco_family import H,coefficients,encode_window,decode_window
from vco_family_raw import read as read_raw
AREA=ROOT/'tmp/lab-current';PACK=ROOT/'evidence/vco_family_dense_windows01.xz'
V=[*VECTORS[:5],VECTORS[12],'i(vmixer)']
LAST=None
def run(s,sink):
    global LAST
    p=AREA/'dense.raw';deck=AREA/'dense.cir';text,_=netlist(s,p)
    text=text.replace('.save '+' '.join(VECTORS),'.save '+' '.join(V),1).replace(f"wrdata {p.as_posix()} {' '.join(VECTORS)}",f"set filetype=binary\nwrite {p.as_posix()} {' '.join(V)}",1)
    deck.write_text(text,encoding='utf8',newline='\n');start=time.monotonic();process=subprocess.run([str(ROOT/EXE),'-n','-b',str(deck)],cwd=(ROOT/EXE).parent,capture_output=True,timeout=180)
    from dataclasses import asdict
    r=dict(scenario=asdict(s),deck=packed(text.encode()),exit_code=process.returncode,stdout=packed(process.stdout),stderr=packed(process.stderr),elapsed_s=time.monotonic()-start);LAST=r
    assert process.returncode==0 and p.exists() and not any(x in(process.stdout+process.stderr).lower() for x in [b'error:',b'aborted',b'timestep too small'])
    r.update(export_bytes=p.stat().st_size,export_sha256=sha(p));assert r['export_bytes']<256*1024**2
    raw,layout=read_raw(p,V);assert raw.shape[1]==8 and abs(raw[-1,0]-.03)<1e-14 and max(np.diff(raw[:,0]))<=125e-9*(1+1e-7);r['binary_layout']=layout
    e=crossings(raw[:,0],raw[:,1],-2.,True);e=e[e>=.015];assert len(e)>=3;period=np.diff(e);spread=float(np.ptp(period)/np.mean(period));assert spread<=1e-5
    aa,bb=e[-2:];t=raw[:,0];knots=np.r_[aa,t[(t>aa)&(t<bb)],bb];phase=(knots-aa)/(bb-aa);phase[0]=0.;phase[-1]=1.;c=np.zeros((7,H+1),complex)
    for k,col in enumerate([3,4,5]):c[k]=coefficients(phase,np.interp(knots,t,raw[:,col]),H)
    target=dict(frequency_hz=float(1/np.mean(period)),coefficients_ri=np.stack([c.real,c.imag],axis=-1).tolist());first=max(0,int(np.searchsorted(t,aa))-2);last=raw[first:].copy()
    r.update(reduction=target,settled_crossings_s=e.tolist(),period_spread_relative=spread,window=encode_window(last,sink),window_pack=PACK.relative_to(ROOT).as_posix());assert decode_window(r['window'],PACK).tobytes()==last.astype('<f8').tobytes()
    r['bus_source_law_error_a']=float(np.max(np.abs((s.imposed_mixer_v-last[:,6])/33000.+last[:,7])));assert r['bus_source_law_error_a']<=2e-12;p.unlink();return r
def main():
    assert not list(AREA.iterdir()) and not PACK.exists() and shutil.disk_usage(ROOT).free>1024**3
    sources=Sources(['tools/check_vco_family_dense.py','docs/VCO_FAMILIA_RESERVA_DENSA.md','tools/vco_family_raw.py','tools/vco_family.py','tools/vco1_circuit_reference.py']);r=dict(passed=False,**sources.fields(),cases=[],pack=PACK.relative_to(ROOT).as_posix(),family_data_sha256=sha(ROOT/'tools/vco_family_data.rs'),private_used_sha256={n:sha(ROOT/n) for n in [EXE,MODEL]})
    try:
        with PACK.open('xb') as sink:
            for i in range(4):
                s=Scenario(keyboard_v=-3.1+i,imposed_mixer_v=0.,r8_fraction=R8,r11_active_ohm=R11,duration_s=.03,max_step_s=125e-9);r['cases'].append(run(s,sink));write(ROOT/'evidence/vco_family_dense01.json',r);print('DENSE_RESERVED',i,flush=True)
        r['passed']=True
    except Exception:
        r['failure']=traceback.format_exc();r['failed_process']=LAST
        try:
            with PACK.open('ab') as sink:run(s,sink)
            r['unchanged_replay']='unexpected pass'
        except Exception:r['unchanged_replay']=traceback.format_exc();r['replay_process']=LAST
    finally:
        for n in ['dense.raw','dense.cir']:
            p=AREA/n
            if p.exists():assert p.resolve().parent==AREA.resolve();p.unlink()
    sources.unchanged();r.update(pack_sha256=sha(PACK),pack_bytes=PACK.stat().st_size,temporary_area_empty=not list(AREA.iterdir()));write(ROOT/'evidence/vco_family_dense01.json',r);print('DENSE_COMPLETE',r['passed'],r.get('failure',''),flush=True)
    if not r['passed']:raise SystemExit(1)
if __name__=='__main__':main()
