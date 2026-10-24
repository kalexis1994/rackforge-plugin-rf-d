"""Predeclared numerical variants at the exact failed coupled scene."""
import traceback,json
from prepare_dual_chain import ROOT,sha,write
from affine_evidence import Sources
from vco_family_receipts import read
import check_family_mixer_oracle as driver
PACK=ROOT/'evidence/family_mixer_diagnostic_windows01.xz'
def main():
    assert not list(driver.AREA.iterdir()) and not PACK.exists();sources=Sources(['tools/diagnose_family_mixer_methods.py','tools/check_family_mixer_oracle.py','tools/family_mixer_analysis.py','docs/FAMILIA_MIXER_REFINAMIENTO.md']);r=dict(passed=False,**sources.fields(),cases=[],pack=PACK.relative_to(ROOT).as_posix());driver.PACK=PACK;training=read('evidence/vco_family_oracle03.json')['training']
    with PACK.open('xb') as sink:
        for method,step in [('gear',62.5e-9),('trap',125e-9)]:
            x=dict(method=method,step_s=step,passed=False)
            try:x['result']=driver.run(-1.6,1,method,step,sink,training);x['passed']=True
            except Exception:
                x.update(failure=traceback.format_exc(),process=driver.LAST)
                try:driver.run(-1.6,1,method,step,sink,training);x['unchanged_replay']='unexpected pass'
                except Exception:x.update(unchanged_replay=traceback.format_exc(),replay_process=driver.LAST)
            for name in ['coupled.raw','coupled.cir']:
                p=driver.AREA/name
                if p.exists():assert p.resolve().parent==driver.AREA.resolve();p.unlink()
            r['cases'].append(x);write(ROOT/'evidence/family_mixer_methods01.json',r);print('COUPLED_DIAGNOSTIC',method,step,x['passed'],flush=True)
    sources.unchanged();r.update(passed=True,pack_sha256=sha(PACK),pack_bytes=PACK.stat().st_size,temporary_area_empty=not list(driver.AREA.iterdir()));write(ROOT/'evidence/family_mixer_methods01.json',r)
if __name__=='__main__':main()
