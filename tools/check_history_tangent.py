"""Independent old-charge mass, absolute-stage Jacobian and fixed-step response."""
import argparse,json,struct,sys,time,traceback
from decimal import Decimal,localcontext
from pathlib import Path
import numpy as np
from prepare_vco1_portable import ROOT,sha,write
from check_joint_reference import D,N,B,CONFIG,vi,ci
from vco1_increment_circuit import reference_decimal
from chain_charge_reference import problem,CAPS
from check_joint_cycles import bank
from joint_cycles_analysis import require
COLS=[43,5,12,139,199,194,157,117,98]

def mass(x,h):
    v=[Decimal(0) if vi(k) is None else x[vi(k)] for k in range(134)]
    _,dc,_=reference_decimal(v,v,None,CONFIG);_,transient,_=reference_decimal(v,v,h,CONFIG)
    m=np.zeros((N,N))
    for a in range(134):
        i=vi(a)
        if i is None:continue
        for b in range(134):
            j=vi(b)
            if j is not None:m[i,j]+=float(transient[a][b]-dc[a][b])
    for a,b,c in [*CAPS,(67,7,10e-6)]:
        b=b if isinstance(b,int) else 66 if b=='BUS' else None
        g=float(D(c)/D(h))
        for r,sign in [(a,1),(b,-1)]:
            if r is not None:
                m[ci(r),ci(a)]+=sign*g
                if b is not None:m[ci(r),ci(b)]-=sign*g
    return m

def stage_jacobian(case):
    _,h,old,_,_,sa,sb=case;oldv=[Decimal(0) if vi(k) is None else old[vi(k)] for k in range(134)]
    _,gradient,_=problem(200.,0,[0.,.2,-.3,.1,.4]);gs=[];ms=[]
    for s in [sa,sb]:
        v=[Decimal(0) if vi(k) is None else s[vi(k)] for k in range(134)]
        _,dc,_=reference_decimal(v,oldv,None,CONFIG);g=np.zeros((N,N))
        for a in range(134):
            i=vi(a)
            if i is None:continue
            for b in range(134):
                j=vi(b)
                if j is not None:g[i,j]+=float(dc[a][b])
        cg=gradient(np.array([float(s[ci(k)]) for k in range(68)]))
        for a in range(68):
            for b in range(68):g[ci(a),ci(b)]+=cg[a,b]
        gs.append(g);ms.append(mass(s,h))
    return np.block([[float(B[i][j])*ms[j]+(gs[i] if i==j else 0) for j in range(2)] for i in range(2)])

def ratio(a,b,absolute,relative):
    require(np.isfinite(a).all() and np.isfinite(b).all(),'finite comparison')
    error=np.abs(a-b)/(absolute+relative*np.abs(b));k=np.unravel_index(np.argmax(error),error.shape)
    return dict(max_ratio=float(error[k]),worst_index=list(map(int,k)),native=float(a[k]),reference=float(b[k]))

def check(native):
    require(native['passed'],'passed native campaign');inputs=json.loads((ROOT/'evidence/voice_history_tangent_inputs01.json').read_text());cases=[]
    for name,digest in inputs['selected_sha256'].items():require(sha(ROOT/name)==digest,'selected input');cases.extend(c[0] for c in bank(ROOT/name))
    require(len(cases)==48,'48 selected steps');binary=next(o['path'] for o in native['outputs'] if o['path'].endswith('/history.bin'));raw=(ROOT/binary).read_bytes();require(raw[:8]==b'RFJHIST2' and struct.unpack_from('<I',raw,8)[0]==48,'history codec');offset=12;records=[]
    def u32():
        nonlocal offset
        v=struct.unpack_from('<I',raw,offset)[0];offset+=4;return v
    def floats(n):
        nonlocal offset
        require(offset+8*n<=len(raw),'complete record');v=np.frombuffer(raw,dtype='<f8',count=n,offset=offset);offset+=8*n;require(np.isfinite(v).all(),'finite record');return v
    output_gate=np.tile(np.array([1e-11 if 98<=k<133 else 1e-8 for k in range(N)]),2)
    for id,case in enumerate(cases):
        require(u32()==id and floats(1)[0]==case[1],'step identity');native_m=floats(40000).reshape(N,N);fds=[floats(80000).reshape(N,2*N).T for _ in range(2)];leak=float(floats(1)[0]);require(leak<=1e-18,'absolute candidate leakage')
        oracle_m=mass(case[2],case[1]);expected=np.vstack([-2*oracle_m,2*oracle_m]);actual=np.vstack([-2*native_m,2*native_m]);analytic=ratio(actual,expected,2e-12,2e-9);require(analytic['max_ratio']<=1,'old mass/history independent gate')
        fd_checks=[ratio(fd,expected,2e-9,1e-6) for fd in fds];require(all(r['max_ratio']<=1 for r in fd_checks),'all history FD columns')
        refinement=ratio(fds[0],fds[1],2e-9,1e-6);tangents=[];observed=[];epsilons=[]
        for col in COLS:
            require(u32()==col,'response column order');epsilon=float(floats(1)[0]);tangent=floats(400);base=1e-10 if 98<=col<133 else 1e-5;target=np.tile(np.array([1e-8 if 98<=k<133 else 1e-5 for k in range(N)]),2);expected_epsilon=base/max(1.,float(np.max(base*np.abs(tangent)/target)));require(epsilon>0 and abs(epsilon-expected_epsilon)<=1e-15*expected_epsilon,'declared scaled response epsilon');epsilons.append(epsilon);tangents.append(tangent);observed.append([floats(400) for _ in range(2)])
        tangents=np.array(tangents).T;independent=np.linalg.solve(stage_jacobian(case),-expected[:,COLS]);responses=[]
        for n,col in enumerate(COLS):
            epsilon=epsilons[n];ind=ratio(epsilon*tangents[:,n],epsilon*independent[:,n],output_gate,1e-4);require(ind['max_ratio']<=1,'independent stage response')
            solved=[]
            for scale,fd in zip([1.,.5],observed[n]):
                r=ratio(scale*epsilon*fd,scale*epsilon*tangents[:,n],output_gate,1e-4);require(r['max_ratio']<=1,'perturbed nonlinear step response');solved.append(r)
            if col==98:require(np.count_nonzero(actual[:,col])==np.count_nonzero(tangents[:,n])==0,'algebraic negative control')
            responses.append(dict(column=col,independent=ind,nonlinear_fd=solved,epsilon=epsilon))
        records.append(dict(case=id,h_s=case[1],absolute_candidate_leak_per_epsilon=leak,history=analytic,history_fd=fd_checks,observed_fd_refinement=refinement,responses=responses));print('HISTORY_REFERENCE_CASE',id,flush=True)
    require(offset==len(raw),'no trailing codec bytes')
    return dict(records=records,input_sha256={binary:sha(ROOT/binary),**inputs['selected_sha256']},history_columns=9600,history_entries=3840000,history_fd_entries=7680000,response_directions=432,response_stage_coordinates=172800,perturbed_native_step_solves=1728,baseline_bit_reproductions=48,negative_controls=48,independent_roots=0,fixed_step_response_admitted=True,adaptive_derivative_admitted=False,period_map_admitted=False,new_audio=False,physical_fidelity=False,real_time=False)

def main():
    a=argparse.ArgumentParser();a.add_argument('--native',type=int,required=True);a.add_argument('--attempt',type=int,required=True);args=a.parse_args();name=f'evidence/voice_history_tangent_native{args.native:02d}.json';native=json.loads((ROOT/name).read_text());out=f'evidence/voice_history_tangent_reference{args.attempt:02d}.json';require(not (ROOT/out).exists(),'exclusive reference')
    names={name,'evidence/voice_history_tangent_inputs01.json','docs/VOZ_TANGENTE_HISTORIA_PROTOCOLO.md','docs/VOZ_TANGENTE_HISTORIA_FINA_PROTOCOLO.md','tools/check_history_tangent.py'}
    for module in list(sys.modules.values()):
        f=getattr(module,'__file__',None)
        if f:
            p=Path(f).resolve()
            if p.is_relative_to(ROOT/'tools') and p.suffix=='.py':names.add(p.relative_to(ROOT).as_posix())
    names.add('docs/VOZ_TANGENTE_HISTORIA_ESCALADA_PROTOCOLO.md');before={n:sha(ROOT/n) for n in sorted(names)};r=dict(schema='rf-d/history-tangent-reference/v1',passed=False,source_sha256=before);started=time.perf_counter()
    try:
        with localcontext() as ctx:ctx.prec=100;r.update(check(native))
        r['passed']=True
    except Exception:
        r['failure']=traceback.format_exc();r['failed_source_text']=(ROOT/'tools/check_history_tangent.py').read_text()
        try:
            with localcontext() as ctx:ctx.prec=100;check(native)
            r['replay']='unexpected pass'
        except Exception:r['replay']=traceback.format_exc()
    r['source_sha256_after']={n:sha(ROOT/n) for n in sorted(names)};require(before==r['source_sha256_after'],'unchanged reference sources');r['wall_s']=time.perf_counter()-started;write(out,r);print('HISTORY_REFERENCE',r['passed'],r.get('failure',''),flush=True)
if __name__=='__main__':main()
