"""Independent original 119-row circuit plus original VCO resistor star."""
import base64,json,sys,time,traceback
from decimal import localcontext
import numpy as np
from prepare_dual_chain import ROOT,sha,write
from check_hybrid_voice import packed,unpack,parse
from check_vco_phase import star
from dual_chain_reference import Original,N,matrix,charge
from audit_dual_chain_star import original_state,original_mass

class Reference(Original):
    def __init__(self):
        super().__init__();self.y=matrix(0)
        profile=json.loads((ROOT/'evidence/vco_phase_profile01.json').read_text(encoding='utf8'))
        self.frequency=profile['frequency_hz'];self.epoch=profile['epoch_s']
        self.table=np.array(json.loads((ROOT/'evidence/hybrid_voice_profile01.json').read_text(encoding='utf8'))['table'])
    def dc(self,x,key=0.,short=False,t=0.):
        f=super().dc(x,key,short,t)
        phase=((t-self.epoch)*self.frequency)%1
        driver=[float(np.interp(phase,self.table[:,0],self.table[:,k])) for k in [1,2]]
        currents,_=star(.5,[*driver,0.,x[116]])
        f[116]+=currents[3]
        return f

def audit(native):
    r=json.loads((ROOT/native).read_text(encoding='utf8'));assert r['passed'];n=Reference();reports=[]
    for profile in r['profiles']:
        _,roots,final=parse(unpack(profile['stdout']));maximum=correction=0.
        for index,x in enumerate(roots):
            t,h,key=x[:3];old,da,db,a,b=[x[3+i*236:3+(i+1)*236] for i in range(5)]
            js=[];ms=[];fs=[];qs=[]
            for i,s in enumerate([a,b]):
                hi,lo=original_state(s);clock=t+h*(1/3 if i==0 else 1)
                j=n.fd(hi,key,t=clock);fs.append(n.dc(hi,key,t=clock)+j@lo)
                qs.append(np.r_[charge(old,s,h),0.]);js.append(j);ms.append(original_mass(s,h))
            B=np.array([[1.5,.5],[-4.5,2.5]])
            residual=np.concatenate([fs[i]+sum(B[i,j]*qs[j] for j in range(2)) for i in range(2)])
            tangent=np.block([[B[i,j]*ms[j]+(js[i] if i==j else 0) for j in range(2)] for i in range(2)])
            d=np.linalg.solve(tangent,-residual);kcl=float(max(abs(residual)));corr=float(max(abs(d)))
            assert kcl<=2e-11 and corr<=2e-9,dict(root=index,time_s=t,h_s=h,kcl_a=kcl,correction_v=corr)
            maximum=max(maximum,kcl);correction=max(correction,corr)
        reports.append(dict(maximum_full_ticks=profile['maximum_full_ticks'],original_rows=238*len(roots),pairs=len(roots),max_residual_a=maximum,max_correction_v=correction))
    return dict(profiles=reports,original_rows=sum(p['original_rows'] for p in reports),independent_original_trajectory=False,retained_amount_cursor=True,original_vco_resistor_star=True)
def main():
    native=sys.argv[1];k=1
    while (ROOT/f'evidence/hybrid_voice_audit{k:02d}.json').exists():k+=1
    names=['tools/audit_hybrid_voice.py','tools/audit_dual_chain_star.py','tools/dual_chain_reference.py','tools/c5_trigger_reference.py','tools/check_hybrid_voice.py','tools/check_vco_phase.py','docs/HYBRID_VOZ_PROTOCOLO.md','evidence/voice_vco1_radau_listening01.json','evidence/vco_phase_profile01.json','evidence/hybrid_voice_profile01.json',native]
    r=dict(passed=False,native=native,source_sha256={n:sha(ROOT/n) for n in names},physical_fidelity=False,real_time=False);start=time.monotonic()
    try:
        with localcontext() as ctx:ctx.prec=100;r.update(audit(native))
        r['passed']=True
    except Exception:
        r.update(failure=traceback.format_exc(),failed_sources=packed(json.dumps({n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in names},sort_keys=True).encode()))
        try:
            with localcontext() as ctx:ctx.prec=100;audit(native)
            r['unchanged_replay']='unexpected pass'
        except Exception:r['unchanged_replay']=traceback.format_exc()
    r['wall_s']=time.monotonic()-start;assert all(sha(ROOT/n)==h for n,h in r['source_sha256'].items());write(ROOT/f'evidence/hybrid_voice_audit{k:02d}.json',r)
    print('HYBRID_ORIGINAL',r['passed'],r.get('profiles'),r.get('failure',''),flush=True)
    if not r['passed']:raise SystemExit(1)
if __name__=='__main__':main()
