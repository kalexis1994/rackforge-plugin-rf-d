"""Same-clock full-state comparison against both already admitted 8-ms voices."""
import json,traceback,base64
from prepare_dual_chain import ROOT,sha,write
N=250
def grids(path):
    result={}
    for line in path.read_text(encoding='utf8').splitlines():
        if line.startswith('GRID,'):
            tag,ticks,*v=line.split(',');result[int(ticks)]=list(map(float,v))
    return result
def audit(native):
    r=json.loads((ROOT/native).read_text(encoding='utf8'));assert r['passed'];old=json.loads((ROOT/'evidence/dual_voice_tests01.json').read_text(encoding='utf8'));profiles=[]
    for p in r['profiles']:
        maximum=p['maximum_half_ticks'];base=ROOT/f'references-local/dual-voice02/profile-{maximum}.stdout';assert sha(base)==old['private_input_sha256'][base.relative_to(ROOT).as_posix()]
        expected=grids(base);actual=grids(ROOT/r['output_directory']/f'profile-{maximum}.stdout');node=0.;load=0.
        for tick,a in expected.items():
            b=actual[tick]
            for k in range(N):
                d=abs((a[k]-b[k])+(a[k+N]-b[k+N]));gate=2e-9 if 98<=k<133 else 20e-6+2e-6*abs(b[k]);node=max(node,d/gate)
            for a,b in zip(a[-2:],b[-2:]):load=max(load,abs(a-b)/(2e-9+2e-5*abs(b)))
        assert node<=1 and load<=1,(node,load)
        profiles.append(dict(maximum_half_ticks=maximum,common_clocks=len(expected),node_fraction=node,load_fraction=load,baseline_sha256=sha(base)))
    return profiles
def main():
    import sys
    native=sys.argv[1];out=ROOT/'evidence/voice_cost_prefix01.json';assert not out.exists();names=['tools/check_voice_cost_prefix.py',native];hashes={n:sha(ROOT/n) for n in names};r=dict(passed=False,source_sha256=hashes)
    try:r['profiles']=audit(native);r['passed']=True
    except Exception:
        r['failure']=traceback.format_exc();r['source_base64']=base64.b64encode(__import__('pathlib').Path(__file__).read_bytes()).decode()
        try:audit(native);r['unchanged_replay']='unexpected pass'
        except Exception:r['unchanged_replay']=traceback.format_exc()
    assert hashes=={n:sha(ROOT/n) for n in names};write(out,r);print('VOICE_COST_PREFIX',r['passed'],r.get('failure',''),r.get('profiles',[]),flush=True)
    if not r['passed']:raise SystemExit(1)
if __name__=='__main__':main()
