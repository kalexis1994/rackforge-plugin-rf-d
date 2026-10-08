"""Conditional nonlinear roots with exact ports, and SDIRK base-Q2 identity."""
import argparse,json,sys,time
from decimal import Decimal,localcontext
from pathlib import Path
import vco1_741_condensation as kernel
import vco1_sdirk_reference as sdirk
circuit=kernel.circuit
op=kernel.op
ROOT=kernel.ROOT
sha=kernel.sha
Z=Decimal(0)
C=[.5,500.,1e-11,0.,0.,*([-2.1]*6)]


def direction(x,old,dt,inv):
    f,j,g=circuit.reference_decimal(x,old,dt,C)
    maps=inv['opamp_maps']
    removed={k for m in maps for k in m[5:]}
    kept=[k for k in range(134) if k not in removed]
    at={k:i for i,k in enumerate(kept)}
    matrix=[[j[i][k] for k in kept] for i in kept]
    residual=[f[i] for i in kept]
    ports=[]
    for m in maps:
        local=lambda values:[Z if k==134 else values[k] for k in m]
        p=kernel.port(local(x),local(old),dt)
        ports.append(p)
        for a,k in enumerate(m[:5]):
            if k==134:continue
            residual[at[k]]+=p['effective'][a]-p['f'][a]
            for b,n in enumerate(m[:5]):
                if n!=134:matrix[at[k]][at[n]]+=p['y'][a][b]-p['j'][a][b]
    outer=kernel.lu_many(matrix,[[-v] for v in residual])
    d=[Z]*134
    for k,v in zip(kept,outer):d[k]=v[0]
    for m,p in zip(maps,ports):
        dp=[Z if k==134 else d[k] for k in m[:5]]
        for a,k in enumerate(m[5:]):d[k]=p['offset'][a]+sum(v*w for v,w in zip(p['gradient'][a],dp))
    return f,d,g


def solve(old,dt,inv,iterations=64):
    x=list(old);history=list(old)
    for iteration in range(iterations):
        kernel.require(circuit.valid(x,C),'condensed nonlinear domain')
        r,d,g=direction(x,history,dt,inv)
        norm=max(abs(v)/op.D(2e-14 if k<98 else 2e-12) for k,v in enumerate(r))
        corr=max(abs(v)/op.D(2e-10 if k<98 else 2e-13) for k,v in enumerate(d))
        if norm<=1 and corr<=1:return x,iteration+1,r,g,norm,corr
        for power in range(24):
            alpha=Decimal(2)**(-power)
            trial=[v+alpha*w for v,w in zip(x,d)]
            if not circuit.valid(trial,C):continue
            rr,_,_=circuit.reference_decimal(trial,history,dt,C)
            new=max(abs(v)/op.D(2e-14 if k<98 else 2e-12) for k,v in enumerate(rr))
            if new<norm or new<=1:x=trial;break
        else:raise ValueError('condensed nonlinear line search')
    raise ValueError('condensed nonlinear iteration limit')


def decomposition(floor,inv,half):
    m=inv['opamp_maps'][1]
    il=m[35];base=m[op.NODES.index(7)]
    card={w[0]:w for w in op.card()}
    l=op.D(card['L2'][4]);r=op.D(card['R13'][4]);offset=op.D(card['EOS'][6])
    previous=[Decimal.from_float(h)+Decimal.from_float(lo) for h,lo in zip(floor['previous_high'],floor['previous_low'])]
    rows=[];parts={};old=previous
    for name,h in [('full',2*half),('mid',half),('end',half)]:
        if name=='mid':old=previous
        roots=floor['steps'][name]
        stage=list(map(Decimal,roots['stage']['independent_decimal']))
        endpoint=list(map(Decimal,roots['endpoint']['independent_decimal']))
        dt=op.D(sdirk.GAMMA*h)
        # Constant A is binary64-pinned exactly as in the stage oracle.
        a=op.D(sdirk.WEIGHT)
        stage_static=stage[m[0]]+offset-r*stage[il]
        stage_dynamic=-l*(stage[il]-old[il])/dt
        static=endpoint[m[0]]+offset-r*endpoint[il]
        dynamic=-l*(endpoint[il]-old[il])/dt+a*l*(stage[il]-old[il])/dt
        error=max(abs(stage[base]-stage_static-stage_dynamic),abs(endpoint[base]-static-dynamic))
        kernel.require(error<=op.D(1e-11),'SDIRK common-mode stage identity')
        rows.append(dict(step=name,dt_s=h,effective_dt_s=float(dt),identity_error_v=str(error),
                         stage_static_v=str(stage_static),stage_dynamic_v=str(stage_dynamic),
                         endpoint_static_v=str(static),endpoint_dynamic_v=str(dynamic),endpoint_base_v=str(endpoint[base])))
        parts[name]=(static,dynamic,endpoint[base])
        if name=='mid':old=endpoint
    static=parts['full'][0]-parts['end'][0]
    dynamic=parts['full'][1]-parts['end'][1]
    actual=parts['full'][2]-parts['end'][2]
    kernel.require(abs(actual-static-dynamic)<=op.D(1e-11),'full/end decomposition sum')
    return dict(rows=rows,static_difference_v=str(static),dynamic_difference_v=str(dynamic),
                base_difference_v=str(actual),dynamic_fraction_signed=str(dynamic/actual),
                identity_error_v=str(abs(actual-static-dynamic)))


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--attempt',type=int,required=True);attempt=ap.parse_args().attempt
    out=ROOT/f'evidence/voice_vco1_741_roots{attempt:02d}.json';kernel.require(not out.exists(),'preserve root attempt')
    qa=json.loads((ROOT/'evidence/voice_vco1_sdirk_tests01.json').read_text(encoding='utf8'))
    names=set(qa['source_sha256'])|{'evidence/voice_vco1_sdirk_tests01.json','evidence/voice_vco1_741_condensation03.json',
            'tools/vco1_741_condensation.py','tools/vco1_741_roots.py','docs/VCO1_741_RAICES_PROTOCOLO.md','docs/VCO1_741_CONDENSACION_PROTOCOLO.md',
            'docs/VCO1_741_RAICES_AUDITORIA.md','evidence/voice_vco1_741_roots01.json','evidence/voice_vco1_741_roots02.json'}
    before={n:sha(ROOT/n) for n in names};private={op.MODEL:sha(ROOT/op.MODEL)}
    report=dict(schema='rf-d/loaded-lm741-exact-condensed-nonlinear-roots/v1',passed=False,source_sha256=before,
                private_input_sha256=private,python_version=sys.version,python_sha256=sha(Path(sys.executable)),cases=[],decompositions=[],
                new_spice_processes=0,new_audio=False,production_kernel_changed=False,native_full_period_admitted=False,
                native_frequency_refinement_admitted=False,dynamic_reduction_admitted=False,physical_fidelity=False,real_time=False)
    def save():out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n')
    save();start=time.perf_counter();inv=circuit.inventory(circuit.scenario(C))
    try:
        with localcontext() as ctx:
            ctx.prec=100
            descriptor=json.loads((ROOT/'evidence/voice_vco1_reset_modes02.json').read_text(encoding='utf8'))
            for scene,s in enumerate(descriptor['scenes']):
                old=[Decimal.from_float(h)+Decimal.from_float(l) for h,l in zip(s['previous_high'],s['previous_low'])]
                for dt in (125e-9/16384,125e-9/8192,125e-9/4096):
                    snapshot=list(old)
                    x,it,r,g,norm,corr=solve(old,dt,inv)
                    full,full_it,rr,gg=circuit.solve(old,dt,C)
                    error=[a-b for a,b in zip(x,full)]
                    kernel.require(kernel.maximum(error[:98])<=op.D(2e-7) and kernel.maximum(error[98:])<=op.D(2e-10),'condensed root comparison')
                    kernel.require(abs(sum(r[:98])+g)<=op.D(1e-11),'condensed root global KCL')
                    repeated=solve(old,dt,inv)
                    kernel.require(json.dumps(list(map(str,repeated[0])))==json.dumps(list(map(str,x))) and old==snapshot,'root purity and replay')
                    try:solve(old,dt,inv,iterations=1)
                    except ValueError as exc:rejected=str(exc)=='condensed nonlinear iteration limit'
                    else:rejected=False
                    kernel.require(rejected and old==snapshot,'budget rejection atomicity')
                    report['cases'].append(dict(scene=scene,dt_s=dt,iterations=it,full_iterations=full_it,
                           condensed_decimal=list(map(str,x)),full_decimal=list(map(str,full)),
                           residual_ratio=str(norm),correction_ratio=str(corr),max_node_difference_v=str(kernel.maximum(error[:98])),
                           max_branch_difference_a=str(kernel.maximum(error[98:])),ground_balance_a=str(abs(sum(r[:98])+g)),
                           repetition_identical=True,history_unchanged=True,budget_rejected=True,passed=True))
                    save();print('Condensed root scene',scene,'dt',dt,'passed',flush=True)
            for name,ticks in (('evidence/voice_vco1_sdirk_floor01.json',8),('evidence/voice_vco1_sdirk_floor4_01.json',4)):
                floor=json.loads((ROOT/name).read_text(encoding='utf8'))
                result=decomposition(floor,inv,ticks*125e-9/65536);result['source_receipt']=name
                report['decompositions'].append(result);save()
                print('Common-mode decomposition',name,result['dynamic_fraction_signed'],flush=True)
        report['passed']=True
    except Exception as exc:
        report['error']=repr(exc)
        report['failed_source_text']={n:(ROOT/n).read_text(encoding='utf8') for n in ('tools/vco1_741_roots.py','docs/VCO1_741_RAICES_PROTOCOLO.md')}
    report.update(source_sha256_after={n:sha(ROOT/n) for n in names},private_input_sha256_after={n:sha(ROOT/n) for n in private},wall_s=time.perf_counter()-start)
    report['passed']=report['passed'] and before==report['source_sha256_after'] and private==report['private_input_sha256_after'];save()
    print('Loaded condensed roots',report['passed'],report.get('error',''),flush=True)


if __name__=='__main__':main()
