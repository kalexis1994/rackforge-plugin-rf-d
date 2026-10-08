"""Independent nodal residual and correction at native coupled candidates.
Decimal100 VCO, inherited Python chain DC/FD Jacobian and Decimal linear Q.
Uses native candidate points intentionally; does not claim independent roots.
"""
import argparse,json,time,traceback
from decimal import Decimal,localcontext
import numpy as np
from prepare_vco1_portable import ROOT,sha
from vco1_increment_circuit import reference_decimal
from chain_charge_reference import problem,CAPS
N=200;B=[[Decimal('1.5'),Decimal('.5')],[Decimal('-4.5'),Decimal('2.5')]]
CONFIG=[.5,500.,1e-11,0.,0.,*([-2.1]*6)]
def vi(k):return None if k==108 else k if k<108 else k-1
def ci(k):return 12 if k==66 else 199 if k==67 else 133+k
def D(v):return Decimal.from_float(float(v))
def decode(line):
    x=list(map(float,line.split(',')[1:]));assert len(x)==400
    return [D(x[k])+D(x[N+k]) for k in range(N)]
def cases(receipt):
    lines=receipt['commands'][-1]['stdout'].splitlines();out=[]
    for i,line in enumerate(lines):
        if 'JOINT_ROOT,' in line:
            _,mask,h,res,corr=line[line.index('JOINT_ROOT,'):].split(',');assert all(s.startswith('JOINT_STATE,') for s in lines[i+1:i+6])
            out.append((int(mask),float(h),*[decode(s) for s in lines[i+1:i+6]]))
    assert len(out)==4;return out
def evaluate(case):
    mask,h,old,da,db,sa,sb=case
    sources=[0.,.2,-.3,.1,.4];dc,gradient,_=problem(200.,30 if mask else 0,sources)
    oldv=[Decimal(0) if vi(k) is None else old[vi(k)] for k in range(134)]
    f=[];q=[];g=[];mass=[]
    for delta,state in [(da,sa),(db,sb)]:
        assert max(abs(state[k]-(old[k]+delta[k])) for k in range(N))<Decimal('1e-28')
        v=[Decimal(0) if vi(k) is None else state[vi(k)] for k in range(134)]
        vf,vj,_=reference_decimal(v,oldv,None,CONFIG);ve,vej,_=reference_decimal(v,oldv,h,CONFIG)
        high=np.array([float(state[ci(k)]) for k in range(68)]);low=np.array([float(state[ci(k)]-D(high[k])) for k in range(68)])
        cj=gradient(high);cf=dc(high);cf=[D(cf[k])+sum(D(cj[k,l])*D(low[l]) for l in range(68)) for k in range(68)]
        cq=[Decimal(0)]*68;cm=np.zeros((68,68))
        for a,b,c in [*CAPS,(67,7,10e-6)]:
            b=b if isinstance(b,int) else 66 if b=='BUS' else None
            current=D(c)/D(h)*(delta[ci(a)]-(delta[ci(b)] if b is not None else 0))
            for r,sign in [(a,1),(b,-1)]:
                if r is not None:
                    cq[r]+=sign*current;cm[r,a]+=sign*c/h
                    if b is not None:cm[r,b]-=sign*c/h
        ff=[Decimal(0)]*N;qq=[Decimal(0)]*N;jj=np.zeros((N,N));mm=np.zeros((N,N))
        for a in range(134):
            i=vi(a)
            if i is None:continue
            ff[i]+=vf[a];qq[i]+=ve[a]-vf[a]
            for b in range(134):
                j=vi(b)
                if j is not None:jj[i,j]+=float(vj[a][b]);mm[i,j]+=float(vej[a][b]-vj[a][b])
        for a in range(68):
            i=ci(a);ff[i]+=cf[a];qq[i]+=cq[a]
            for b in range(68):jj[i,ci(b)]+=cj[a,b];mm[i,ci(b)]+=cm[a,b]
        f.append(ff);q.append(qq);g.append(jj);mass.append(mm)
    r=[f[i][a]+sum(B[i][j]*q[j][a] for j in range(2)) for i in range(2) for a in range(N)]
    jac=np.block([[float(B[i][j])*mass[j]+(g[i] if i==j else 0) for j in range(2)] for i in range(2)])
    direction=np.linalg.solve(jac,np.array([-float(v) for v in r]))
    ratio=max(float(abs(v)/D(2e-10 if 98<=k%N<133 else 2e-11)) for k,v in enumerate(r))
    correction=max(abs(v)/(1e-9 if 98<=k%N<133 else 1e-6) for k,v in enumerate(direction))
    assert ratio<=1 and correction<=1,(ratio,correction)
    return dict(other_ports_on=bool(mask),h_s=h,rows=400,residual_gate_ratio=ratio,correction_gate_ratio=correction,max_correction_v=max(abs(direction[k]) for k in range(400) if not 98<=k%N<133),max_correction_a=max(abs(direction[k]) for k in range(400) if 98<=k%N<133))
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--attempt',type=int,required=True);a=parser.parse_args()
    out=ROOT/f'evidence/voice_joint_reference{a.attempt:02d}.json';assert not out.exists()
    native='evidence/voice_joint_native02.json';receipt=json.loads((ROOT/native).read_text());assert receipt['passed']
    sources=[native,'tools/check_joint_reference.py','tools/vco1_increment_circuit.py','tools/vco1_increment_devices.py','tools/vco1_native_inventory.py','tools/lm741_port_reference.py','tools/chain_charge_reference.py','tools/circuit66_dc_vectors.py','tools/circuit66_vca_release_probes.py','tools/mixer_on_native_vectors.py','tools/cutoff_j7_vectors.py','docs/VOZ_BUS_CONJUNTO_PROTOCOLO.md']
    hashes={n:sha(ROOT/n) for n in sources};report=dict(schema='rf-d/joint-reference/v1',passed=False,source_sha256=hashes,cases=[],native_candidates_used=True,independent_root_solve=False,new_spice_processes=0)
    started=time.perf_counter()
    try:
        with localcontext() as ctx:
            ctx.prec=100
            for case in cases(receipt):report['cases'].append(evaluate(case))
        report['passed']=True
    except Exception:
        report['failure']=traceback.format_exc();report['failed_source_text']=(ROOT/'tools/check_joint_reference.py').read_text()
        try:
            with localcontext() as ctx:
                ctx.prec=100
                for case in cases(receipt):evaluate(case)
            report['replay']='unexpected pass'
        except Exception:report['replay']=traceback.format_exc()
    report['wall_s']=time.perf_counter()-started;report['source_sha256_after']={n:sha(ROOT/n) for n in sources};assert hashes==report['source_sha256_after']
    out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n');print('JOINT_REFERENCE',report['passed'],report.get('failure',''),report['cases'])
if __name__=='__main__':main()
