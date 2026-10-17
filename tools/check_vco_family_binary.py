"""Same-plot short control of ASCII versus strict native binary64 export."""
import json,subprocess,traceback
from dataclasses import replace
import numpy as np
from prepare_dual_chain import ROOT,sha,write
from affine_evidence import Sources
from check_hybrid_voice import packed
from vco1_circuit_reference import Scenario,netlist,VECTORS
from lm741_reference import EXE
from vco_cv_load_analysis import R8,R11
from vco_family_raw import read,bits
EXTRA=['v(ic1_sum)','i(vmixer)','i(vbend)','i(vtune)','i(vkeyboard)','i(vmod)','i(vext)','i(vosc1_range)']
AREA=ROOT/'tmp/lab-current'
def run():
    assert not list(AREA.iterdir());sources=Sources(['tools/check_vco_family_binary.py','tools/vco_family_raw.py','tools/voice_native_raw.py','docs/VCO_FAMILIA_EXPORT_BINARIO.md'])
    r=dict(passed=False,**sources.fields());paths=[AREA/n for n in ['binary.cir','binary.txt','binary.raw']]
    try:
        deck,ascii_p,raw_p=paths;s=Scenario(keyboard_v=-.1,imposed_mixer_v=-.125,r8_fraction=R8,r11_active_ohm=R11,duration_s=4e-6,max_step_s=125e-9);text,_=netlist(s,ascii_p);v=VECTORS+EXTRA
        text=text.replace('.save '+' '.join(VECTORS),'.save '+' '.join(v),1).replace(f"wrdata {ascii_p.as_posix()} {' '.join(VECTORS)}",f"wrdata {ascii_p.as_posix()} {' '.join(v)}\nset filetype=binary\nwrite {raw_p.as_posix()} {' '.join(v)}",1);deck.write_text(text,encoding='utf8',newline='\n')
        p=subprocess.run([str(ROOT/EXE),'-n','-b',str(deck)],cwd=(ROOT/EXE).parent,capture_output=True,timeout=180);r.update(deck=packed(text.encode()),stdout=packed(p.stdout),stderr=packed(p.stderr),exit_code=p.returncode);assert p.returncode==0 and ascii_p.exists() and raw_p.exists()
        a=np.loadtxt(ascii_p,skiprows=1);b,layout=read(raw_p,v);r.update(layout=layout,comparison=bits(a,b),ascii_sha256=sha(ascii_p),binary_sha256=sha(raw_p),ascii_bytes=ascii_p.stat().st_size,binary_bytes=raw_p.stat().st_size);assert r['comparison']['passed'];r['passed']=True
    finally:
        for path in paths:
            if path.exists():assert path.resolve().parent==AREA.resolve();path.unlink()
    sources.unchanged();r['temporary_area_empty']=not list(AREA.iterdir());return r
if __name__=='__main__':
    try:r=run()
    except Exception:
        r=dict(passed=False,**Sources(['tools/check_vco_family_binary.py','tools/vco_family_raw.py']).fields(),failure=traceback.format_exc())
        try:run();r['unchanged_replay']='unexpected pass'
        except Exception:r['unchanged_replay']=traceback.format_exc()
        write(ROOT/'evidence/vco_family_binary_failure01.json',r);raise
    write(ROOT/'evidence/vco_family_binary_control01.json',r);print('FAMILY_BINARY',r['comparison'],r['binary_bytes'])
