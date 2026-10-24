import traceback,json
from prepare_dual_chain import ROOT,sha,write
from affine_evidence import Sources
from vco_family_receipts import read
from family_mixer_analysis import compare
import family_mixer_scaled_oracle as driver
def main():
    assert not list(driver.AREA.iterdir()) and not driver.PACK.exists();sources=Sources(['tools/check_family_mixer_scaled_control.py','tools/family_mixer_scaled_oracle.py','docs/FAMILIA_MIXER_COORDENADA.md']);r=dict(passed=False,**sources.fields(),cases=[],pack=driver.PACK.relative_to(ROOT).as_posix());training=read('evidence/vco_family_oracle03.json')['training'];old=read('evidence/family_mixer_oracle02.json')
    with driver.PACK.open('xb') as sink:
        for cv in [-2.6,-1.6]:
            x=dict(cv_v=cv,passed=False)
            try:
                x['result']=driver.run(cv,1,'gear',125e-9,sink,training)
                if cv==-2.6:x['comparison']=compare(x['result']['measurements'],old['cases'][1]['measurements'])
                x['passed']=True
            except Exception:
                x.update(failure=traceback.format_exc(),process=driver.LAST)
                try:
                    replay=driver.run(cv,1,'gear',125e-9,sink,training)
                    if cv==-2.6:compare(replay['measurements'],old['cases'][1]['measurements'])
                    x['unchanged_replay']='unexpected pass'
                except Exception:x.update(unchanged_replay=traceback.format_exc(),replay_process=driver.LAST)
            for name in ['coupled.raw','coupled.cir']:
                p=driver.AREA/name
                if p.exists():assert p.resolve().parent==driver.AREA.resolve();p.unlink()
            r['cases'].append(x);write(ROOT/'evidence/family_mixer_scaled_control01.json',r);print('SCALED_C27',cv,x['passed'],flush=True)
            if not x['passed']:break
    sources.unchanged();r.update(passed=all(x['passed'] for x in r['cases']) and len(r['cases'])==2,pack_sha256=sha(driver.PACK),pack_bytes=driver.PACK.stat().st_size,temporary_area_empty=not list(driver.AREA.iterdir()));write(ROOT/'evidence/family_mixer_scaled_control01.json',r)
    if not r['passed']:raise SystemExit(1)
if __name__=='__main__':main()
