"""Original 251-row VCO/dual-contour network at selected full joint candidates."""
import base64,json,time,traceback
from decimal import Decimal,localcontext
import numpy as np
from prepare_dual_chain import ROOT,sha,write
from dual_chain_reference import Original,matrix,expanded,charge
from audit_dual_chain_star import original_mass
from vco1_increment_circuit import reference_decimal
N=250;B=np.array([[1.5,.5],[-4.5,2.5]])
CONFIG=[.5,500.,1e-11,0.,0.,*([-2.1]*6)]
def vi(k):return None if k==108 else k if k<108 else k-1
def di(k):return 12 if k==116 else 133+k if k<116 else 249 if k==117 else 250
def state(x):return [Decimal.from_float(v)+Decimal.from_float(w) for v,w in zip(x[:N],x[N:])]
def assemble(n,old,current,key,h=None):
    absolute=state(current);previous=state(old)
    v=[Decimal(0) if vi(k) is None else absolute[vi(k)] for k in range(134)];ov=[Decimal(0) if vi(k) is None else previous[vi(k)] for k in range(134)]
    vf,vj,_=reference_decimal(v,ov,None,CONFIG)
    if h:ve,vej,_=reference_decimal(v,ov,h,CONFIG)
    high=expanded([current[di(k)] for k in range(118)]);low=expanded([current[N+di(k)] for k in range(118)])
    cj=n.fd(high,key);cf=n.dc(high,key)+cj@np.array(low)
    f=np.zeros(251);q=np.zeros(251);j=np.zeros((251,251));m=np.zeros((251,251))
    for a in range(134):
        i=vi(a)
        if i is None:continue
        f[i]+=float(vf[a]);q[i]+=float(ve[a]-vf[a]) if h else 0.
        for b in range(134):
            k=vi(b)
            if k is not None:j[i,k]+=float(vj[a][b]);m[i,k]+=float(vej[a][b]-vj[a][b]) if h else 0.
    now_dual=[current[di(k)] for k in range(118)]+[current[N+di(k)] for k in range(118)]
    old_dual=[old[di(k)] for k in range(118)]+[old[N+di(k)] for k in range(118)]
    cm=original_mass(now_dual,h) if h else np.zeros((119,119));cq=[*charge(old_dual,now_dual,h),0.] if h else [0.]*119
    for a in range(119):
        i=di(a);f[i]+=cf[a];q[i]+=cq[a]
        for b in range(119):j[i,di(b)]+=cj[a,b];m[i,di(b)]+=cm[a,b]
    return f,q,j,m
def gate(residual,jac,dc=False):
    tau=np.array([2e-10 if 98<=i%251<133 or (dc and i==43) else 2e-11 for i in range(len(residual))])
    ratio=float(max(abs(residual)/tau));d=np.linalg.solve(jac,-residual)
    correction=float(max(abs(d)/np.array([1e-9 if 98<=i%251<133 else 1e-6 for i in range(len(d))])))
    assert ratio<=1 and correction<=1,(ratio,correction)
    return dict(residual_fraction=ratio,correction_fraction=correction,max_nodal_kcl_a=float(max(abs(v) for i,v in enumerate(residual) if not 98<=i%251<133 and not(dc and i==43))))
def audit(native):
    r=json.loads((ROOT/native).read_text(encoding='utf8'));assert r['passed'];n=Original();n.y=matrix(0)
    profiles=[];clocks=[];directions=[]
    for p in r['profiles']:
        maximum=p['maximum_half_ticks'];path=ROOT/r['output_directory']/f'profile-{maximum}.stdout';checks=[];dc=[];trace={};final=None;first_jac=None
        for line in path.read_text(encoding='utf8').splitlines():
            tag,*tokens=line.split(',');x=list(map(float,tokens))
            if tag=='DC':
                current=x[4:];f,_,j,_=assemble(n,current,current,0.);forcing=-f[43];f[43]=float(state(current)[43]);j[43,:]=0.;j[43,43]=1.
                check=gate(f,j,True);assert abs(forcing-x[1])<=2e-11;check['forcing_a']=forcing;dc.append(check)
            elif tag=='ROOT':
                h,key=x[:2];old,da,db,a,b=[x[2+i*2*N:2+(i+1)*2*N] for i in range(5)]
                fa,qa,ja,ma=assemble(n,old,a,key,h);fb,qb,jb,mb=assemble(n,old,b,key,h)
                residual=np.concatenate([fa+B[0,0]*qa+B[0,1]*qb,fb+B[1,0]*qa+B[1,1]*qb])
                jac=np.block([[ja+B[0,0]*ma,B[0,1]*mb],[B[1,0]*ma,jb+B[1,1]*mb]])
                check=gate(residual,jac);check.update(h_s=h,key_v=key,bus_balance_a=x[-1]);assert abs(x[-1])<=2e-11;checks.append(check)
                if first_jac is None:
                    # Retain the original Amount cursor for each stage, then Schur
                    # eliminate exactly those two rows for the native comparison.
                    keep=[i for i in range(502) if i not in [250,501]];ports=[250,501]
                    first_jac=jac[np.ix_(keep,keep)]-jac[np.ix_(keep,ports)]@np.linalg.solve(jac[np.ix_(ports,ports)],jac[np.ix_(ports,keep)])
            elif tag=='GRID':trace[int(tokens[0])]=x[1:1+2*N],x[-2:]
            elif tag=='FINAL':final=dict(ticks=int(tokens[0]),accepted_steps=int(tokens[1]),selected_pairs=int(tokens[2]),atomic_rejections=int(tokens[3]),wall_s=x[4],max_bus_kcl_a=x[5])
        assert final and final['ticks']==24000*524288 and len(trace)==192 and len(checks)==final['selected_pairs'] and len(dc)==1
        raw=np.frombuffer((ROOT/r['output_directory']/f'linear-{maximum}.bin').read_bytes(),dtype='<f8');assert len(raw)==M*M+2*M
        j=raw[:M*M].reshape(M,M);rhs=raw[M*M:M*M+M];d=raw[-M:];expected=np.linalg.solve(j,rhs)
        delta=float(max(abs(d-expected)/np.array([2e-12 if 98<=k%N<133 else 2e-9 for k in range(M)])))
        backward=float(max(abs(j@d-rhs)/(abs(rhs)+abs(j)@abs(d)+abs(j)@np.array([2e-12 if 98<=k%N<133 else 2e-9 for k in range(M)]))))
        stamp=float(np.max(abs(j-first_jac)/(2e-9+2e-5*abs(first_jac))))
        assert delta<=1 and backward<=1e-11 and stamp<=1,(delta,backward,stamp);directions.append(dict(maximum_half_ticks=maximum,dense_difference_fraction=delta,backward_fraction=backward,original_tangent_fraction=stamp,compared_entries=500*500))
        profiles.append(dict(maximum_half_ticks=maximum,dc=dc,stage_checks=checks,original_rows=251+502*len(checks),**final));clocks.append(trace)
    refinements=[]
    for tick in clocks[0]:
        a,ia=clocks[0][tick];b,ib=clocks[1][tick];a=np.array([float(v) for v in state(a)]);b=np.array([float(v) for v in state(b)])
        gates=20e-6+2e-6*abs(b);gates[98:133]=2e-9;node=float(max(abs(a-b)/gates));load=float(max(abs(np.array(ia)-np.array(ib))/(2e-9+2e-5*abs(np.array(ib)))))
        assert node<=1 and load<=1,(tick,node,load);refinements.append((node,load))
    return dict(profiles=profiles,original_rows=sum(p['original_rows'] for p in profiles),common_clocks=192,max_node_fraction=max(x[0] for x in refinements),max_load_fraction=max(x[1] for x in refinements),linear_directions=directions)
M=500
def main():
    import sys
    native=sys.argv[1];out=ROOT/'evidence/voice_sparse_reference01.json';assert not out.exists()
    names=['tools/audit_voice_sparse.py','tools/dual_chain_reference.py','tools/audit_dual_chain_star.py','tools/vco1_increment_circuit.py','tools/vco1_increment_devices.py',native];hashes={n:sha(ROOT/n) for n in names};start=time.monotonic();r=dict(schema='rf-d/dual-voice/reference-v1',passed=False,source_sha256=hashes,native_candidates_used=True,independent_root_solve=False)
    try:
        with localcontext() as ctx:ctx.prec=100;r.update(audit(native))
        assert time.monotonic()-start<=300;r['passed']=True
    except Exception:
        r['failure']=traceback.format_exc();r['source_base64']=base64.b64encode(__import__('pathlib').Path(__file__).read_bytes()).decode()
        try:
            with localcontext() as ctx:ctx.prec=100;audit(native)
            r['unchanged_replay']='unexpected pass'
        except Exception:r['unchanged_replay']=traceback.format_exc()
    r['wall_s']=time.monotonic()-start;assert hashes=={n:sha(ROOT/n) for n in names};write(out,r);print('DUAL_VOICE_REFERENCE',r['passed'],r.get('failure',''),r.get('original_rows'),flush=True)
    if not r['passed']:raise SystemExit(1)
if __name__=='__main__':main()
