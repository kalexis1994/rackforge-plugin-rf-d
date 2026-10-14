"""Original-network DC/FD/charge checks at full coupled Radau candidates."""
import base64,json,time,traceback
import numpy as np
from prepare_dual_chain import ROOT,sha,write
from dual_chain_reference import Original,N,expanded,charge,ci
def physical(s):return np.array(s[:N])+np.array(s[N:])
def audit(native):
    r=json.loads((ROOT/native).read_text(encoding='utf8'));assert r['passed']
    oracle=Original();result=[];clocks=[];all_fd=0;all_rows=0
    for profile in r['profiles']:
        directory=ROOT/r['output_directory'];lines=(directory/f"profile-{profile['maximum_us']}.stdout").read_text(encoding='utf8').splitlines()
        report=dict(maximum_us=profile['maximum_us'],max_kcl_a=0.,max_correction_v=0.,max_fd_fraction=0.,dc_difference_v=0.,original_rows=0,fd_entries=0)
        trace={};last_root=None;stage=0
        for line in lines:
            name,*tokens=line.split(',');x=list(map(float,tokens))
            if name=='DC':
                state=x[:2*N];native_j=np.array(x[3*N:]).reshape(N,N)
                point=physical(state);expected=oracle.reduced_fd(point)
                fraction=float(np.max(abs(native_j-expected)/(2e-9+2e-5*abs(expected))))
                assert fraction<=1,f'DC FD {fraction}'
                original=json.loads((directory/'original_inputs.json').read_text(encoding='utf8'))['original_dc']
                report['dc_difference_v']=float(max(abs(point-np.array(original[:N]))))
                assert report['dc_difference_v']<=20e-6,report
                residual=oracle.reduced(point);direction=np.linalg.solve(expected,-residual)
                assert max(abs(residual))<=2e-11 and max(abs(direction))<=2e-9,('original DC',max(abs(residual)),max(abs(direction)))
                report['max_fd_fraction']=fraction;report['fd_entries']+=N*N
            elif name=='ROOT':
                t,h,key=x[:3];offset=3
                states=[x[offset+i*2*N:offset+(i+1)*2*N] for i in range(5)]
                old,da,db,a,b=states
                f=[];q=[];js=[];ms=[]
                for index,s in enumerate([a,b]):
                    point=physical(s);clock=t+h*(1/3 if index==0 else 1)
                    j=oracle.reduced_fd(point,key,t=clock)
                    # Residual using compensated high/low rather than rounding the state.
                    ff=oracle.reduced(np.array(s[:N]),key,t=clock)+j@np.array(s[N:])
                    f.append(ff);q.append(charge(old,s,h));js.append(j)
                    mass=np.empty((N,N));epsilon=1e-6
                    for k in range(N):
                        up=list(s);down=list(s);up[k]+=epsilon;down[k]-=epsilon
                        mass[:,k]=(charge(old,up,h)-charge(old,down,h))/(2*epsilon)
                    ms.append(mass)
                B=np.array([[1.5,.5],[-4.5,2.5]])
                residual=np.concatenate([f[i]+sum(B[i,j]*q[j] for j in range(2)) for i in range(2)])
                jac=np.block([[B[i,j]*ms[j]+(js[i] if i==j else 0) for j in range(2)] for i in range(2)])
                direction=np.linalg.solve(jac,-residual)
                kcl=float(max(abs(residual)));correction=float(max(abs(direction)))
                assert kcl<=2e-11 and correction<=2e-9,('Radau original',t,h,kcl,correction)
                report['max_kcl_a']=max(report['max_kcl_a'],kcl);report['max_correction_v']=max(report['max_correction_v'],correction)
                report['original_rows']+=2*(N+1);last_root=(js,ms);stage=0
            elif name=='STAMP':
                j=np.array(x[:N*N]).reshape(N,N);mass=np.array(x[N*N:]).reshape(N,N)
                expected_j,expected_m=last_root[0][stage],last_root[1][stage]
                for got,expected in [(j,expected_j),(mass,expected_m)]:
                    fraction=float(np.max(abs(got-expected)/(2e-9+2e-5*abs(expected))))
                    assert fraction<=1,('FD',stage,fraction)
                    report['max_fd_fraction']=max(report['max_fd_fraction'],fraction)
                report['fd_entries']+=2*N*N;stage+=1
            elif name=='GRID':
                ticks=int(tokens[0]);assert ticks%1073741824==0
                trace[ticks]=x[1:1+2*N],x[1+2*N:]
            elif name=='FINAL':
                steps,replays,roots,invalid=map(int,tokens[:4]);report.update(accepted_steps=steps,local_replays=replays,roots=roots,atomic_rejections=invalid,wall_s=x[4])
        assert len(trace)==144 and max(trace)==36000*1073741824
        assert report['original_rows']==report['roots']*2*(N+1)
        result.append(report);clocks.append(trace);all_fd+=report['fd_entries'];all_rows+=report['original_rows']
    fractions=[]
    for tick in clocks[0]:
        a,ia=clocks[0][tick];b,ib=clocks[1][tick]
        a=physical(a);b=physical(b)
        node=float(max(abs(a-b)/(20e-6+2e-6*abs(b))))
        load=float(max(abs(np.array(ia)-np.array(ib))/(2e-9+2e-5*abs(np.array(ib)))))
        assert node<=1 and load<=1,('clock refinement',tick,node,load)
        fractions.append((node,load))
    return dict(profiles=result,original_rows=all_rows,fd_entries=all_fd,common_clocks=144,max_node_refinement_fraction=max(p[0] for p in fractions),max_load_refinement_fraction=max(p[1] for p in fractions))
def main():
    import sys
    native=sys.argv[1];out=ROOT/'evidence/dual_chain_reference01.json';assert not out.exists()
    names=['tools/audit_dual_chain.py','tools/dual_chain_reference.py',native];hashes={n:sha(ROOT/n) for n in names}
    start=time.monotonic();r=dict(schema='rf-d/dual-chain/reference-v1',passed=False,native_receipt=native,native_receipt_sha256=sha(ROOT/native),source_sha256=hashes,native_candidates_used=True,independent_dc_root=True,independent_transient_root=False)
    try:r.update(audit(native));assert time.monotonic()-start<=300;r['passed']=True
    except Exception:
        r['failure']=traceback.format_exc();r['source_base64']=base64.b64encode(Path(__file__).read_bytes()).decode()
        try:audit(native);r['unchanged_replay']='unexpected pass'
        except Exception:r['unchanged_replay']=traceback.format_exc()
    r['wall_s']=time.monotonic()-start;r['source_sha256_after']={n:sha(ROOT/n) for n in names};assert hashes==r['source_sha256_after']
    write(out,r);print('JOINT_REFERENCE',r['passed'],r.get('failure',''),r.get('profiles',[]),flush=True)
    if not r['passed']:raise SystemExit(1)
if __name__=='__main__':main()
