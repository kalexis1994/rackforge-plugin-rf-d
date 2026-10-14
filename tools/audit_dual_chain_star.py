"""All 119 original rows with the retained Amount cursor, both Radau stages."""
import base64,json,time,traceback
import numpy as np
from prepare_dual_chain import ROOT,sha,write
from dual_chain_reference import Original,N,expanded,charge,mass
from c5_trigger_reference import LATCH,junction,D
from decimal import localcontext
def original_state(s):
    hi=expanded(s[:N]);lo=expanded(s[N:])
    # The star is linear and homogeneous: expand low separately.
    return np.array(hi),np.array(lo)
def original_mass(s,h):
    m=np.zeros((119,119));m[:N,:N]=mass(h)
    with localcontext() as ctx:
        ctx.prec=65
        epsilon=D(1e-6)
        for b,c in LATCH:
            be=D(s[b])+D(s[N+b]);bc=be-D(s[c])-D(s[N+c])
            gbe=float((junction(be+epsilon,True)-junction(be-epsilon,True))/(2*epsilon))/h
            gbc=float((junction(bc+epsilon,False)-junction(bc-epsilon,False))/(2*epsilon))/h
            m[b,b]+=gbe+gbc;m[b,c]-=gbc;m[c,b]-=gbc;m[c,c]+=gbc
    return m
def audit(native):
    r=json.loads((ROOT/native).read_text(encoding='utf8'));assert r['passed'];n=Original();profiles=[]
    for profile in r['profiles']:
        rows=0;maximum=0.;correction=0.;roots=0
        for line in (ROOT/r['output_directory']/f"profile-{profile['maximum_us']}.stdout").read_text(encoding='utf8').splitlines():
            name,*tokens=line.split(',')
            if name not in ['DC','ROOT']:continue
            x=list(map(float,tokens))
            if name=='DC':
                s=x[:2*N];hi,lo=original_state(s);j=n.fd(hi);f=n.dc(hi)+j@lo;d=np.linalg.solve(j,-f)
                assert max(abs(f))<=2e-11 and max(abs(d))<=2e-9,('full original DC',max(abs(f)),max(abs(d)))
                rows+=119;continue
            t,h,key=x[:3];states=[x[3+i*2*N:3+(i+1)*2*N] for i in range(5)];old,da,db,a,b=states
            js=[];ms=[];fs=[];qs=[]
            for i,s in enumerate([a,b]):
                hi,lo=original_state(s);clock=t+h*(1/3 if i==0 else 1)
                j=n.fd(hi,key,t=clock);f=n.dc(hi,key,t=clock)+j@lo
                q=np.array([*charge(old,s,h),0.]);m=original_mass(s,h)
                js.append(j);ms.append(m);fs.append(f);qs.append(q)
            B=np.array([[1.5,.5],[-4.5,2.5]])
            residual=np.concatenate([fs[i]+sum(B[i,j]*qs[j] for j in range(2)) for i in range(2)])
            tangent=np.block([[B[i,j]*ms[j]+(js[i] if i==j else 0) for j in range(2)] for i in range(2)])
            d=np.linalg.solve(tangent,-residual);kcl=float(max(abs(residual)));corr=float(max(abs(d)))
            assert kcl<=2e-11 and corr<=2e-9,('full original Radau',t,h,kcl,corr)
            rows+=238;roots+=1;maximum=max(maximum,kcl);correction=max(correction,corr)
        profiles.append(dict(maximum_us=profile['maximum_us'],original_rows=rows,roots=roots,max_kcl_a=maximum,max_correction_v=correction))
    return dict(profiles=profiles,original_rows=sum(p['original_rows'] for p in profiles),retained_amount_cursor=True)
def main():
    import sys
    native=sys.argv[1];out=ROOT/'evidence/dual_chain_star01.json';assert not out.exists()
    names=['tools/audit_dual_chain_star.py','tools/dual_chain_reference.py','tools/c5_trigger_reference.py',native];hashes={n:sha(ROOT/n) for n in names}
    start=time.monotonic();r=dict(schema='rf-d/dual-chain/original-star-v1',passed=False,source_sha256=hashes)
    try:r.update(audit(native));assert time.monotonic()-start<=300;r['passed']=True
    except Exception:
        r['failure']=traceback.format_exc();r['source_base64']=base64.b64encode(__import__('pathlib').Path(__file__).read_bytes()).decode()
        try:audit(native);r['unchanged_replay']='unexpected pass'
        except Exception:r['unchanged_replay']=traceback.format_exc()
    r['wall_s']=time.monotonic()-start;assert hashes=={n:sha(ROOT/n) for n in names};write(out,r)
    print('JOINT_STAR',r['passed'],r.get('failure',''),r.get('profiles',[]),flush=True)
    if not r['passed']:raise SystemExit(1)
if __name__=='__main__':main()
