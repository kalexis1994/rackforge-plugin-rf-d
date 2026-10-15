"""Original 119-row DC and Radau equations at own startup and KEY boundaries."""
import json,time,traceback,struct
from decimal import localcontext
import numpy as np
from prepare_dual_chain import ROOT,sha,write
from affine_evidence import Sources
from run_chain_startup import OWN as BASE,parse
from check_hybrid_voice import unpack
from audit_hybrid_voice import Reference
from audit_dual_chain_star import original_state,original_mass
from dual_chain_reference import charge
OWN=BASE+['tools/audit_chain_startup.py','tools/audit_hybrid_voice.py','tools/audit_dual_chain_star.py','tools/dual_chain_reference.py','tools/check_vco_phase.py','evidence/hybrid_voice_profile01.json','evidence/vco_phase_profile01.json']
def bits(v):return struct.pack('<'+str(len(v))+'d',*v)
def audit(native):
    r=json.loads((ROOT/native).read_text(encoding='utf8'));assert r['passed'];n=Reference();profiles=[];initials=[];seams=[]
    for pi,p in enumerate(r['profiles']):
        data=parse(unpack(p['stdout']));maximum=correction=0.
        if pi==0:
            for d in data['dc']:
                hi,lo=original_state(d['state']);j=n.fd(hi,0.,t=0.);f=n.dc(hi,0.,t=0.)+j@lo;dx=np.linalg.solve(j,-f);kcl=float(max(abs(f)));corr=float(max(abs(dx)));assert kcl<=20e-12 and corr<=2e-9
                initials.append(dict(mode=d['mode'],rows=119,residual_a=kcl,correction_v=corr))
        assert bits(data['roots'][0][3:239])==bits(data['dc'][0]['state'])
        for event in data['events']:
            t=event[0]*(125e-9/65536);following=[x for x in data['roots'] if x[0]==t];assert len(following)==2 and all(x[2]==event[1] and bits(x[3:239])==bits(event[2:]) for x in following)
            seams.append(dict(maximum_full_ticks=p['maximum_full_ticks'],time_s=t,key_v=event[1],state_bits_preserved=True))
        for index,x in enumerate(data['roots']):
            t,h,key=x[:3];old,da,db,a,b=[x[3+i*236:3+(i+1)*236] for i in range(5)];js=[];ms=[];fs=[];qs=[]
            for i,s in enumerate([a,b]):
                hi,lo=original_state(s);clock=t+h*(1/3 if i==0 else 1);j=n.fd(hi,key,t=clock);fs.append(n.dc(hi,key,t=clock)+j@lo);qs.append(np.r_[charge(old,s,h),0.]);js.append(j);ms.append(original_mass(s,h))
            B=np.array([[1.5,.5],[-4.5,2.5]]);residual=np.concatenate([fs[i]+sum(B[i,j]*qs[j] for j in range(2)) for i in range(2)]);tangent=np.block([[B[i,j]*ms[j]+(js[i] if i==j else 0) for j in range(2)] for i in range(2)])
            dx=np.linalg.solve(tangent,-residual);kcl=float(max(abs(residual)));corr=float(max(abs(dx)));assert kcl<=20e-12 and corr<=2e-9,dict(root=index,t=t,h=h,kcl_a=kcl,correction_v=corr)
            maximum=max(maximum,kcl);correction=max(correction,corr)
        profiles.append(dict(maximum_full_ticks=p['maximum_full_ticks'],pairs=len(data['roots']),original_rows=238*len(data['roots']),max_residual_a=maximum,max_correction_v=correction))
    assert len(initials)==2 and len(profiles)==2 and len(seams)==4
    return dict(dc=initials,profiles=profiles,dc_rows=238,dynamic_rows=8568,original_rows=8806,initial_and_key_seams=seams,independent_original_trajectory=False)
def main():
    native='evidence/chain_startup_native02.json';sources=Sources(OWN);r=dict(passed=False,native=native,native_sha256=sha(ROOT/native),**sources.fields(),physical_fidelity=False,real_time=False);clock=time.monotonic()
    try:
        with localcontext() as ctx:ctx.prec=100;r.update(audit(native))
        r['passed']=True
    except Exception:
        r['failure']=traceback.format_exc()
        try:
            with localcontext() as ctx:ctx.prec=100;audit(native)
            r['unchanged_replay']='unexpected pass'
        except Exception:r['unchanged_replay']=traceback.format_exc()
    sources.unchanged();r['wall_s']=time.monotonic()-clock;k=1
    while (ROOT/f'evidence/chain_startup_audit{k:02d}.json').exists():k+=1
    write(ROOT/f'evidence/chain_startup_audit{k:02d}.json',r);print('CHAIN_STARTUP_ORIGINAL',r['passed'],r.get('profiles'),r.get('failure',''),flush=True)
    if not r['passed']:raise SystemExit(1)
if __name__=='__main__':main()
