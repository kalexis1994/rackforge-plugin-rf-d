"""Original 119-row equations at reconstructed condensed Radau endpoints."""
import base64,json,sys,time,traceback
from decimal import localcontext
import numpy as np
from prepare_dual_chain import ROOT,sha,write
from check_hybrid_voice import packed,unpack,parse
from audit_hybrid_voice import Reference
from audit_dual_chain_star import original_state,original_mass
from dual_chain_reference import charge
from affine_evidence import Sources

def audit(native):
    r=json.loads((ROOT/native).read_text(encoding='utf8'));assert r.get('numerical_integration_verified') and (r['passed'] or r.get('failed_phase')=='cost');n=Reference();reports=[]
    for p in r['profiles']:
        if p['mode']!='incidence':continue
        _,roots,_=parse(unpack(p['stdout']));maximum=correction=0.
        for index,x in enumerate(roots):
            t,h,key=x[:3];old,da,db,a,b=[x[3+i*236:3+(i+1)*236] for i in range(5)]
            js=[];ms=[];fs=[];qs=[]
            for i,s in enumerate([a,b]):
                hi,lo=original_state(s);clock=t+h*(1/3 if i==0 else 1);j=n.fd(hi,key,t=clock)
                fs.append(n.dc(hi,key,t=clock)+j@lo);qs.append(np.r_[charge(old,s,h),0.]);js.append(j);ms.append(original_mass(s,h))
            B=np.array([[1.5,.5],[-4.5,2.5]])
            residual=np.concatenate([fs[i]+sum(B[i,j]*qs[j] for j in range(2)) for i in range(2)])
            tangent=np.block([[B[i,j]*ms[j]+(js[i] if i==j else 0) for j in range(2)] for i in range(2)])
            d=np.linalg.solve(tangent,-residual);kcl=float(max(abs(residual)));corr=float(max(abs(d)))
            assert kcl<=2e-11 and corr<=2e-9,dict(root=index,time_s=t,h_s=h,kcl_a=kcl,correction_v=corr)
            maximum=max(maximum,kcl);correction=max(correction,corr)
        reports.append(dict(maximum_full_ticks=p['maximum_full_ticks'],original_rows=238*len(roots),pairs=len(roots),max_residual_a=maximum,max_correction_v=correction))
    assert len(reports)==2
    return dict(profiles=reports,original_rows=sum(p['original_rows'] for p in reports),independent_original_trajectory=False,retained_amount_cursor=True,original_vco_resistor_star=True)
def main():
    native=sys.argv[1];k=1
    while (ROOT/f'evidence/incidence_voice_audit{k:02d}.json').exists():k+=1
    names=['tools/audit_incidence_voice.py','tools/audit_hybrid_voice.py','tools/audit_dual_chain_star.py','tools/dual_chain_reference.py','tools/c5_trigger_reference.py','tools/check_hybrid_voice.py','docs/INCIDENCE_VOICE_PROTOCOLO.md']
    sources=Sources(names+['tools/affine_evidence.py']);r=dict(passed=False,native=native,native_sha256=sha(ROOT/native),**sources.fields(),physical_fidelity=False,real_time=False);start=time.monotonic()
    try:
        with localcontext() as ctx:ctx.prec=100;r.update(audit(native))
        r['passed']=True
    except Exception:
        r.update(failure=traceback.format_exc())
        try:
            with localcontext() as ctx:ctx.prec=100;audit(native)
            r['unchanged_replay']='unexpected pass'
        except Exception:r['unchanged_replay']=traceback.format_exc()
    r['wall_s']=time.monotonic()-start;sources.unchanged();write(ROOT/f'evidence/incidence_voice_audit{k:02d}.json',r)
    print('INCIDENCE_ORIGINAL',r['passed'],r.get('profiles'),r.get('failure',''),flush=True)
    if not r['passed']:raise SystemExit(1)
if __name__=='__main__':main()
