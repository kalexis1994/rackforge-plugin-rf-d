"""Independent increment Radau roots: old nodal Python DC + explicit linear Q.
Binary64 physical interfaces/NumPy algebra; no native roots or native Jacobian.
"""
import json,math,sys,time,traceback
import numpy as np
from decimal import Decimal,getcontext
from prepare_vco1_portable import ROOT,sha
from circuit66_dc_vectors import dc_evaluator
from circuit66_vca_release_probes import CAPS
from cutoff_j7_vectors import setup
from mixer_on_native_vectors import network
import mixer_panel_bus_reference as panel
N=68
B=np.array([[1.5,.5],[-4.5,2.5]])
def matrix(m):
    g,_=network([bool(m&(1<<i)) for i in range(5)],[.5]*4,panel._sources());g=np.array(g,dtype=float)
    return g[:6,:6]-g[:6,6:]@np.linalg.solve(g[6:,6:],g[6:,:6]) if len(g)>6 else g
def mass():
    c=np.zeros((N,N))
    for a,b,f in CAPS:
        b=b if isinstance(b,int) else 66 if b=='BUS' else None
        for row,s in [(a,1),(b,-1)]:
            if row is not None:
                c[row,a]+=s*f
                if b is not None:c[row,b]-=s*f
    for row,s in [(67,1),(7,-1)]:c[row,67]+=s*10e-6;c[row,7]-=s*10e-6
    return c
def problem(r61,mask,sources):
    values=setup(r61);fcore=dc_evaluator(values,dict(values[4],loudness_v=2.,q21_base_v=2.))
    y=matrix(mask)
    def dc(x):
        r=np.empty(N);r[:66]=fcore(x[:66].tolist())[0];r[:48]*=-1.;r[66]=(y@np.array([*sources,x[66]]))[5]
        i=(x[22]-x[67])/25500.;r[22]+=i;r[67]=-i
        return r
    def gradient(x):
        j=np.empty((N,N));epsilon=1e-6
        for k in range(N):
            a=x.copy();b=x.copy();a[k]+=epsilon;b[k]-=epsilon;j[:,k]=(dc(a)-dc(b))/(2*epsilon)
        return j
    return dc,gradient,y
def solve(dc,gradient,old,h):
    getcontext().prec=80
    D=lambda v:v if isinstance(v,Decimal) else Decimal.from_float(float(v))
    old=list(map(D,old));c=mass()/h;d=[[Decimal(0)]*N for _ in range(2)]
    def charge(delta):
        q=[Decimal(0)]*N
        for a,b,farad in [*CAPS,(67,7,10e-6)]:
            b=b if isinstance(b,int) else 66 if b=='BUS' else None
            voltage=delta[a]-(delta[b] if b is not None else 0)
            current=D(farad)/D(h)*voltage
            q[a]+=current
            if b is not None:q[b]-=current
        return q
    def system(delta):
        absolute=[[old[a]+delta[k][a] for a in range(N)] for k in range(2)]
        high=[np.array(list(map(float,x))) for x in absolute];g=[gradient(x) for x in high]
        low=[np.array([float(absolute[k][a]-D(high[k][a])) for a in range(N)]) for k in range(2)]
        f=[[D(v)+D(w) for v,w in zip(dc(high[k]),g[k]@low[k])] for k in range(2)]
        q=[charge(delta[k]) for k in range(2)]
        r=[f[i][a]+sum(D(B[i,j])*q[j][a] for j in range(2)) for i in range(2) for a in range(N)]
        jac=np.block([[B[i,j]*c+(g[i] if i==j else 0) for j in range(2)] for i in range(2)])
        return r,jac
    for iteration in range(64):
        r,j=system(d);direction=np.linalg.solve(j,np.fromiter((-float(v) for v in r),dtype=np.float64,count=2*N));norm=float(max(abs(v)/D(1e-13) for v in r));corr=float(np.max(np.abs(direction)/2e-9))
        if norm<=1 and corr<=1:
            absolute=[[old[a]+d[k][a] for a in range(N)] for k in range(2)]
            return dict(delta=[[float(v) for v in row] for row in d],stage=list(map(float,absolute[0])),endpoint=list(map(float,absolute[1])),
                stage_decimal=list(map(str,absolute[0])),endpoint_decimal=list(map(str,absolute[1])),residual_ratio=norm,correction_ratio=corr,iterations=iteration+1)
        for power in range(24):
            trial=[[d[k][a]+D(direction[k*N+a])*Decimal(2)**-power for a in range(N)] for k in range(2)]
            rr,_=system(trial);nextnorm=float(max(abs(v)/D(1e-13) for v in rr))
            if nextnorm<norm*(1-1e-4*2.**-power) or nextnorm<=1:d=trial;break
        else:raise ValueError(f'independent Radau line search: {norm=} {h=}')
    raise ValueError('independent Radau iterations')
def generate():
    archived=json.loads((ROOT/'evidence/voice_mixer_direct_vectors01.json').read_text())
    cases=[]
    for r61 in [200,200000]:
        for mask in [1,31]:
            oldcase=next(c for c in archived['cases'] if c['r61_ohm']==r61 and c['mask']==mask and c['dt_s']==125e-9)
            row=oldcase['rows'][2];old=np.array([*row['node_v'],row['bus_v'],row['node_v'][7]+row['c10_v']])
            sources=row['source_v'];dc,gradient,y=problem(r61,mask,sources)
            for h in [125e-9,31.25e-9,8*(125e-9/65536)]:
                full=solve(dc,gradient,old,h);mid=solve(dc,gradient,old,h/2)
                middle=list(map(Decimal,mid['endpoint_decimal']));end=solve(dc,gradient,middle,h/2)
                error=float(max(abs(Decimal(a)-Decimal(b))/Decimal.from_float(2e-6) for a,b in zip(full['endpoint_decimal'],end['endpoint_decimal'])))
                cur=[(y@np.array([*sources,p['endpoint'][66]]))[:5].tolist() for p in [full,mid,end]]
                cases.append(dict(r61_ohm=r61,mask=mask,h_s=h,old=old.tolist(),source_v=sources,
                    full=full,mid=mid,end=end,current_a=cur,error_ratio=error))
                print('CHAIN_REFERENCE',r61,mask,h,'LTE',error,flush=True)
    return cases
def main():
    out=ROOT/'evidence/voice_chain_charge_reference06.json';data=ROOT/'evidence/voice_chain_charge_vectors06.txt'
    assert not out.exists() and not data.exists(),'preserve reference attempt'
    start=time.perf_counter();names=['docs/CADENA_CARGA_RADAU_PROTOCOLO.md','tools/chain_charge_reference.py','evidence/voice_mixer_direct_vectors01.json']
    for module in list(sys.modules.values()):
        f=getattr(module,'__file__',None)
        if f:
            p=__import__('pathlib').Path(f).resolve()
            if p.is_relative_to(ROOT/'tools') and p.suffix=='.py':names.append(p.relative_to(ROOT).as_posix())
    before={n:sha(ROOT/n) for n in set(names)}
    report=dict(schema='rf-d/chain-charge-reference/v1',passed=False,source_sha256=before,cases=[],native_seeds_used=False,
        physical_fidelity=False,real_time=False,new_spice_processes=0,new_audio=False,arithmetic='Decimal80 state/charge accumulation; binary64 physical/FD interfaces and NumPy directions',gates=dict(node_v=1e-6,current_a=1e-9,local_error_v=2e-6))
    try:
        report['cases']=generate();lines=[]
        for c in report['cases']:
            row=[c['r61_ohm'],c['mask'],c['h_s'],*c['source_v'],*c['old']]
            for name,cur in zip(['full','mid','end'],c['current_a']):
                row.extend(c[name]['stage']);row.extend(c[name]['endpoint']);row.extend(cur)
            row.append(c['error_ratio']);lines.append(' '.join(format(v,'.17e') for v in row))
        data.write_text('\n'.join(lines)+'\n',encoding='utf8',newline='\n');report['vectors_sha256']=sha(data)
        report['passed']=all(c['error_ratio']<=1. for c in report['cases'])
    except Exception:
        report['failure']=traceback.format_exc();report['failed_source_text']={n:(ROOT/n).read_text(encoding='utf8') for n in before if n.endswith('.py')}
        try:generate();report['replay']='completed'
        except Exception:report['replay']=traceback.format_exc()
    report['source_sha256_after']={n:sha(ROOT/n) for n in before};report['wall_s']=time.perf_counter()-start
    out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n')
    print('CHAIN_REFERENCE_PASSED',report['passed'],report.get('failure',''),flush=True)
if __name__=='__main__':main()
