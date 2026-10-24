"""Reuse complete direct/scaled controls; finish the fixed six-scene bank."""
import json,traceback
from prepare_dual_chain import ROOT,sha,write
from affine_evidence import Sources
from vco_family_receipts import read
from family_mixer_analysis import compare
import family_mixer_scaled_oracle as driver
PACK=ROOT/'evidence/family_mixer_completion_windows01.xz'
OUT='evidence/family_mixer_complete01.json'
def main():
    assert not list(driver.AREA.iterdir()) and not PACK.exists();a=read('evidence/family_mixer_oracle02.json');b=read('evidence/family_mixer_scaled_control01.json');assert not a['passed'] and len(a['cases'])==3 and b['passed']
    sources=Sources(['tools/complete_family_mixer_oracle.py','tools/family_mixer_scaled_oracle.py','tools/family_mixer_analysis.py','docs/FAMILIA_MIXER_COORDENADA.md']);driver.PACK=PACK
    references=['evidence/family_mixer_oracle02.json','evidence/family_mixer_scaled_control01.json'];cases=[dict(x,window_pack=a['pack']) for x in a['cases']];cases.append(dict(b['cases'][1]['result'],window_pack=b['pack']))
    r=dict(passed=False,**sources.fields(),reused_reference_sha256={n:sha(ROOT/n) for n in references},cases=cases,method=[],pack=PACK.relative_to(ROOT).as_posix(),private_used_sha256={n:sha(ROOT/n) for n in ['references-local/ngspice46/runtime/Spice64/bin/ngspice_con.exe','references-local/datasheets/ti_lm741_lm741.lib']});training=read('evidence/vco_family_oracle03.json')['training']
    def save():write(ROOT/OUT,r)
    save()
    try:
        with PACK.open('xb') as sink:
            for load in [0,1]:
                args=(-.6,load,'gear',125e-9);x=driver.run(*args,sink,training);x['window_pack']=PACK.relative_to(ROOT).as_posix();r['cases'].append(x);save();print('COMPLETED_HIGH',load,flush=True)
            for method,step in [('trap',125e-9),('gear',62.5e-9)]:
                args=(-1.6,1,method,step);x=driver.run(*args,sink,training);x['window_pack']=PACK.relative_to(ROOT).as_posix();x['comparison']=compare(x['measurements'],cases[3]['measurements']);r['method'].append(x);save();print('COMPLETED_METHOD',method,flush=True)
        r['passed']=True
    except Exception:
        r.update(failure=traceback.format_exc(),failed_process=driver.LAST);save()
        try:
            with PACK.open('ab') as sink:
                x=driver.run(*args,sink,training)
                if args[0]==-1.6:compare(x['measurements'],cases[3]['measurements'])
            r['unchanged_replay']='unexpected pass'
        except Exception:r.update(unchanged_replay=traceback.format_exc(),replay_process=driver.LAST)
    finally:
        for name in ['coupled.raw','coupled.cir']:
            p=driver.AREA/name
            if p.exists():assert p.resolve().parent==driver.AREA.resolve();p.unlink()
    sources.unchanged();r.update(pack_sha256=sha(PACK),pack_bytes=PACK.stat().st_size,temporary_area_empty=not list(driver.AREA.iterdir()));save();print('COUPLED_BANK',r['passed'],r.get('failure',''),flush=True)
    if not r['passed']:raise SystemExit(1)
if __name__=='__main__':main()
