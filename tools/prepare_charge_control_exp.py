"""Exact local linear FOH transition; immutable constitutive matrices."""
import json,traceback
import numpy as np
from prepare_dual_chain import ROOT,sha,write
from affine_evidence import Sources

def transition(m,h):
    c=np.array(m['c']);a=-np.array(m['k'])/c[:,None];b=np.array(m['forcing'])/c;values,v=np.linalg.eig(a);inv=np.linalg.inv(v);r=h*values;phi1=np.empty_like(r);phi2=np.empty_like(r);small=abs(r)<1e-3
    phi1[~small]=np.expm1(r[~small])/r[~small];phi2[~small]=(np.expm1(r[~small])-r[~small])/r[~small]**2
    phi1[small]=sum(r[small]**k/float(__import__('math').factorial(k+1)) for k in range(9));phi2[small]=sum(r[small]**k/float(__import__('math').factorial(k+2)) for k in range(9))
    f=(v*np.exp(r))@inv;g0=h*(v*(phi1-phi2))@inv@b;g1=h*(v*phi2)@inv@b;imag=float(max(np.max(abs(np.imag(x))) for x in[f,g0,g1]));assert imag<=1e-10;f=f.real;g0=g0.real;g1=g1.real
    half=((v*np.exp(r/2))@inv).real;semigroup=float(np.max(abs(half@half-f)));assert semigroup<=1e-10
    eig_res=float(np.linalg.norm(a@v-v*values)/max(np.linalg.norm(a)*np.linalg.norm(v),1e-30));assert eig_res<=1e-10
    checks=[]
    for left,right in[(a@(g0+g1),(f-np.eye(18))@b),(a@g1,(g0+g1)/h-b)]:
        ratio=float(max(abs(left-right)/(1e-10+1e-8*abs(right))));assert ratio<=1,ratio;checks.append(ratio)
    return dict(f=f.tolist(),u0=g0.tolist(),u1=g1.tolist(),imaginary_max=imag,eigenvector_condition=float(np.linalg.cond(v)),eigen_residual=eig_res,semigroup_error=semigroup,identity_max_scaled_error=max(checks))

def simulate(models,time,u,index,dynamic=True):
    h=time[1]-time[0];maps=[transition(m,h) for m in models];caps=[np.array(m['incidence'])@np.array(m['dc']) for m in models];q=np.zeros(18);last=index;nodes=np.empty((len(time),68));nodes[0]=models[index]['dc'];switches=[]
    f=[np.array(m['f']) for m in maps];u0=[np.array(m['u0']) for m in maps];u1=[np.array(m['u1']) for m in maps];xq=[np.array(m['xq']) for m in models];xu=[np.array(m['xu']) for m in models];dc=[np.array(m['dc']) for m in models]
    for k in range(1,len(time)):
        mid=(time[k-1]+time[k])/2;idx=(1 if mid<.001 or mid>=.003 else 2 if mid<.002 else 0) if dynamic else index
        if idx!=last:q=q+caps[last]-caps[idx];last=idx
        q=f[idx]@q+u0[idx]*u[k-1]+u1[idx]*u[k];nodes[k]=dc[idx]+xq[idx]@q+xu[idx]*u[k]
    return nodes,switches

def main():
    sources=Sources(['tools/prepare_charge_control_exp.py','docs/CHARGE_CONTROL_EXPONENCIAL.md']);native=json.loads((ROOT/'evidence/charge_control_native01.json').read_text(encoding='utf8'));assert native['passed'];models=native['models'];r=dict(passed=False,**sources.fields(),native_sha256=sha(ROOT/'evidence/charge_control_native01.json'))
    try:
        r['transitions']=[transition(m,1/384000) for m in models];old=(ROOT/'tools/charge_control_data.rs').read_text(encoding='utf8');rows=old.splitlines();new=[rows[0]+' Exact exponential FOH variant.']
        def rust(v):return '['+','.join(map(rust,v))+']' if isinstance(v,list) else format(v,'.17e')
        for line in rows[1:]:
            key=next((k for k in ['f','u0','u1'] if line.startswith('pub const '+k.upper()+':')),None)
            if key:line=line.split('=',1)[0]+'='+rust([m[key] for m in r['transitions']])+';'
            new.append(line)
        p=ROOT/'tools/charge_control_exp_data.rs';assert not p.exists();p.write_bytes(('\n'.join(new)+'\n').encode('utf8'));r['generated_sha256']={p.relative_to(ROOT).as_posix():sha(p)};r['passed']=True
    except Exception:
        r['failure']=traceback.format_exc()
        try:[transition(m,1/384000) for m in models];r['unchanged_replay']='unexpected pass'
        except Exception:r['unchanged_replay']=traceback.format_exc()
    sources.unchanged();write(ROOT/'evidence/charge_control_exponential01.json',r);print('CONTROL_EXP',r['passed'],r.get('failure',''))
    if not r['passed']:raise SystemExit(1)
if __name__=='__main__':main()
