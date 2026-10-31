"""Exact algebraic elimination of a local linearized charge DAE; no fitting."""
import json,re,traceback
import numpy as np
from prepare_dual_chain import ROOT,sha,write
from affine_evidence import Sources
from check_hybrid_voice import unpack
GAMMA=1-1/np.sqrt(2);Y=1/39250

def capacitors():
    body=(ROOT/'crates/rf-d-circuit/src/chain_charge.rs').read_text(encoding='utf8').split('pub const CAPACITORS:')[1].split('];')[0]
    result=[]
    for a,b,c in re.findall(r'\((\d+),(\w+),([\d.e-]+)\)',body):result.append((int(a),{'GROUND':68,'BUS':66}.get(b,int(b) if b.isdigit() else 68),float(c)))
    assert len(result)==17;return result+[(67,7,10e-6)]

def exports():
    r=json.loads((ROOT/'evidence/charge_reduced_oracle02.json').read_text(encoding='utf8'));assert r['passed'];cases=[{} for _ in range(2)]
    for line in unpack(r['export']['stdout']).decode().splitlines():
        z=line.split(',');v=np.array(list(map(float,z[2:])));cases[int(z[1])][z[0]]=v if z[0]=='DC' else v.reshape(68,68)
    return cases

def derive(case):
    caps=capacitors();a=np.zeros((18,68));c=np.array([v for i,j,v in caps])
    for k,(i,j,_)in enumerate(caps):
        a[k,i]=1.
        if j<68:a[k,j]-=1.
    pivots=[]
    for k in range(68):
        if np.linalg.matrix_rank(a[:,pivots+[k]])>len(pivots):pivots.append(k)
    assert len(pivots)==18;alg=[k for k in range(68) if k not in pivots];l=np.vstack([a,np.eye(68)[alg]]);t=np.linalg.inv(l);identity=float(np.max(abs(l@t-np.eye(68))));assert identity<=1e-12
    g=case['G'].copy();g[66,66]+=Y;m=case['M'];b=np.zeros(68);b[66]=.5*Y
    mass_error=float(np.max(abs(m-a.T@np.diag(c)@a)));assert mass_error<=1e-20,mass_error
    gt=t.T@g@t;mt=t.T@m@t;bt=t.T@b
    assert np.max(abs(mt-np.diag(np.r_[c,np.zeros(50)])))<=1e-20
    r=-np.linalg.solve(gt[18:,18:],gt[18:,:18]);s=np.linalg.solve(gt[18:,18:],bt[18:]);xq=t[:,:18]+t[:,18:]@r;xu=t[:,18:]@s
    k=gt[:18,:18]+gt[:18,18:]@r;forcing=bt[:18]-gt[:18,18:]@s
    cq=np.diag(c);assert np.max(abs(a@xq-np.eye(18)))<=1e-12 and np.max(abs(a@xu))<=1e-12
    h=1/384000;aa=-k/c[:,None];bb=forcing/c;stage=np.linalg.solve(np.eye(18)-GAMMA*h*aa,np.eye(18));su=GAMMA*h*stage@bb
    f=stage@(np.eye(18)+h*(1-GAMMA)*aa@stage);v=stage@(h*(1-GAMMA)*(aa@su+bb));w=stage@(GAMMA*h*bb);u0=(1-GAMMA)*v;u1=GAMMA*v+w
    freq=[]
    for hz in np.geomspace(10,24000,33):
        omega=2j*np.pi*hz;direct=np.linalg.solve(g+omega*m,b);q=np.linalg.solve(k+omega*cq,forcing);reduced=xq@q+xu;error=abs(direct-reduced);limit=1e-12+1e-8*abs(direct);assert np.all(error<=limit),(hz,float(max(error/limit)));di=Y*(direct[66]-.5);ri=Y*(reduced[66]-.5);assert abs(di-ri)<=1e-15+1e-8*abs(di);freq.append(dict(hz=float(hz),max_voltage_error_v_per_v=float(max(error)),max_scaled_error=float(max(error/limit)),panel_error_a_per_v=float(abs(di-ri))))
    # Independent direct68 BE stages, physical history, including algebraic input feedthrough.
    comparisons=[]
    for i in range(8):
        q=np.sin(np.arange(18)+i)*1e-6;old=xq@q+xu*1e-5;before=1e-5;after=-.7e-5;us=(1-GAMMA)*before+GAMMA*after
        d1=np.linalg.solve(m/(GAMMA*h)+g,m@old/(GAMMA*h)+b*us);history=old+(1-GAMMA)/GAMMA*(d1-old);d2=np.linalg.solve(m/(GAMMA*h)+g,m@history/(GAMMA*h)+b*after)
        newq=f@q+u0*before+u1*after;endpoint=xq@newq+xu*after;error=float(max(abs(endpoint-d2)));assert error<=1e-11,error
        firstq=stage@q+su*us;first=xq@firstq+xu*us;rate=(1-GAMMA)*(-g@first+b*us)+GAMMA*(-g@endpoint+b*after);balance=float(max(abs(m@(endpoint-old)-h*rate)));assert balance<=1e-20,balance
        alg_kcl=float(max(abs(t[:,18:].T@(g@endpoint-b*after))));assert alg_kcl<=1e-12,alg_kcl;comparisons.append(dict(node_error_v=error,charge_balance_c=balance,algebraic_kcl_a=alg_kcl))
    return dict(dc=(case['DC'][:68]+case['DC'][68:]).tolist(),c=c.tolist(),incidence=a.tolist(),coordinate_inverse=t.tolist(),xq=xq.tolist(),xu=xu.tolist(),k=k.tolist(),forcing=forcing.tolist(),f=f.tolist(),u0=u0.tolist(),u1=u1.tolist(),stage=stage.tolist(),stage_u=su.tolist(),mass_error_f=mass_error,coordinate_identity_error=identity,frequency_checks=freq,discrete_checks=comparisons,poles_real_max_per_s=float(max(np.linalg.eigvals(aa).real)))

def main():
    sources=Sources(['tools/prepare_charge_reduced.py']);r=dict(passed=False,**sources.fields(),oracle_sha256=sha(ROOT/'evidence/charge_reduced_oracle02.json'))
    try:
        r['models']=[derive(x) for x in exports()];r['passed']=True
        out='//! Generated local linear charge DAE, CHARGE_REDUCED_PROTOCOLO. No modes truncated.\n'
        for key,ty in [('f','[[f64;18];18]'),('u0','[f64;18]'),('u1','[f64;18]'),('xq','[[f64;18];68]'),('xu','[f64;68]')]:
            def rust(v):return '['+','.join(map(rust,v))+']' if isinstance(v,list) else format(v,'.17e')
            out+=f'pub const {key.upper()}:[{ty};2]='+rust([m[key] for m in r['models']])+';\n'
        path=ROOT/'tools/charge_reduced_data.rs';assert not path.exists();path.write_bytes(out.encode());r['generated_sha256']={path.relative_to(ROOT).as_posix():sha(path)}
    except Exception:
        r['failure']=traceback.format_exc()
        try:[derive(x) for x in exports()];r['unchanged_replay']='unexpected pass'
        except Exception:r['unchanged_replay']=traceback.format_exc()
    sources.unchanged();k=1
    while(ROOT/f'evidence/charge_reduced_derivation{k:02d}.json').exists():k+=1
    write(ROOT/f'evidence/charge_reduced_derivation{k:02d}.json',r);print('CHARGE_DERIVE',r['passed'],r.get('failure',''))
    if not r['passed']:raise SystemExit(1)
if __name__=='__main__':main()
