"""A posteriori charge derivative proxy; no new solve or estimator promotion."""
from decimal import Decimal as D,localcontext
from fractions import Fraction as F
import gzip,json
from pathlib import Path
import loudness_latch_bdf_charge_defect as law
from circuit66_decimal_static import lift
from bjt_charge_ngspice_probes import model_parameters
from loudness_latch_bdf_static_precision_integrator import CompensatedBdfNetwork
from loudness_latch_bdf_static_precision_forced_clock import OUTPUT as REFERENCE,SOURCE as BASE
from loudness_latch_bdf_static_precision_charge_defect import PATHS as OLD_PATHS,OUTPUT as WITNESSES
from loudness_latch_bdf_probes import unpack
from loudness_latch_bdf_doubling_survey import store
from loudness_latch_directional_curvature import metrics
from loudness_latch_increment_probes import hashes
from loudness_lab_metadata import environment

ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/'evidence/loudness_latch_bdf_static_precision_charge_proxy.json.gz'
SUMMARY=ROOT/'evidence/loudness_latch_bdf_static_precision_charge_proxy_summary.json'
PROTOCOL=ROOT/'docs/BIESTABLE_DEFECTO_MUESTREADO_PROTOCOLO.md'
PATHS=tuple(dict.fromkeys((*OLD_PATHS,Path(__file__).resolve(),PROTOCOL,REFERENCE,BASE,WITNESSES,
                         ROOT/'evidence/loudness_latch_bdf_static_precision_charge_defect_validation.json')))


def charges(network,state):
    return [lift(cap)*(lift(a)+lift(b)) for (_,_,_,cap,_),(a,b) in
            zip(network.network.branches,state.capacitor_pairs_v)]+[
            lift(q) for device in state.latch.devices for q in (device.be_c,device.bc_c)]


def weighted(weights,vectors):
    return [sum((law.decimal_fraction(w)*v[k] for w,v in zip(weights,vectors)),D(0)) for k in range(25)]


def operators(base,reference,index):
    ctimes=tuple(F(reference['samples'][j]['history']['time_s']) for j in (index,index-1,index-2))
    fi=reference['samples'][index]['fine_step_index']
    ftimes=tuple(F(reference['steps'][j]['history']['time_s']) for j in range(fi,fi-4,-1))
    step=base['reference'][index];h=F(step['diagnostics']['actual_dt_s']);k=F(base['reference'][index-1]['diagnostics']['actual_dt_s'])
    c=step['diagnostics']['coefficients'];a0=F(c['a0']);a2=F(c['a2'])
    return dict(clock=law.lagrange_weights(ctimes),command=law.weights(h,k),
                binary=(a0/h,-(a0+a2)/h,a2/h),fine_cubic=law.lagrange_weights(ftimes),
                fine_quadratic=law.lagrange_weights(ftimes[:3])),ctimes,ftimes,h,k,c


def evaluate_point(network,base,reference,index,precision=80):
    with localcontext() as ctx:
        ctx.prec=precision;ops,ctimes,ftimes,h,k,c=operators(base,reference,index)
        coarse=[charges(network,unpack(network,reference['samples'][j]['history']).current) for j in (index,index-1,index-2)]
        fi=reference['samples'][index]['fine_step_index']
        fine=[charges(network,unpack(network,reference['steps'][j]['history']).current) for j in range(fi,fi-4,-1)]
        coarse_values={name:weighted(ops[name],coarse) for name in ('clock','command','binary')}
        dc=weighted(ops['fine_cubic'],fine);dq=weighted(ops['fine_quadratic'],fine[:3])
        vectors=dict(clock_defect_proxy_a=[a-b for a,b in zip(coarse_values['clock'],dc)],
            command_clock_term_a=[a-b for a,b in zip(coarse_values['command'],coarse_values['clock'])],
            coefficient_term_a=[a-b for a,b in zip(coarse_values['binary'],coarse_values['command'])],
            binary_defect_proxy_a=[a-b for a,b in zip(coarse_values['binary'],dc)],
            fine_derivative_spread_a=[a-b for a,b in zip(dc,dq)])
        tau=vectors['binary_defect_proxy_a'];nodal=[D(0)]*94;pub=[D(0)]*25;boundary=D(0)
        dt=law.decimal_fraction(1/ops['binary'][0]);betas=[]
        def stamp(left,right,current):
            nonlocal boundary
            if left is not None:nodal[left]+=current
            else:boundary+=current
            if right is not None:nodal[right]-=current
            else:boundary-=current
        for j,(left,right,_,cap,resistance) in enumerate(network.network.branches):
            beta,current,offset=law.series_terms(tau[j],dt,lift(cap),lift(resistance))
            stamp(left,right,current);pub[j]=offset;betas.append(beta)
        p=network.network.latch.device.parameters
        for i,terminals in enumerate(network.network.latch.terminals):
            base_node,collector,emitter=[j for j,_ in terminals]
            stamp(base_node,emitter,p.polarity*tau[21+2*i]);stamp(base_node,collector,p.polarity*tau[22+2*i])
        vectors.update(nodal_residual_proxy_a=nodal,publication_proxy_v=pub,fixed_boundary_sum_a=[boundary],
                       conservation_error_a=[sum(nodal,D(0))+boundary])
        reconstructed=[a+b+d for a,b,d in zip(vectors['clock_defect_proxy_a'],vectors['command_clock_term_a'],vectors['coefficient_term_a'])]
        return dict(vectors=vectors,decomposition=metrics(tau,reconstructed),
            clock_times_s=ctimes,fine_times_s=ftimes,operators=ops,
            clock_ratio=(ctimes[0]-ctimes[1])/(ctimes[1]-ctimes[2]),command_ratio=h/k,
            ideal_effective_dt_s=1/ops['binary'][0],kernel_effective_dt_s=c['effective_dt_s'],
            effective_dt_difference_s=dt-lift(c['effective_dt_s']),beta=betas)


def generate():
    before=hashes(PATHS);env=environment();base=json.loads(gzip.decompress(BASE.read_bytes()))['windows']
    source=json.loads(gzip.decompress(REFERENCE.read_bytes()))['windows']
    network=CompensatedBdfNetwork(200,model_parameters(1,'finite_transit'));windows=[]
    for w,b in zip(source,base):
        if w['name']!=b['name']:raise ValueError('window order changed')
        levels=[]
        for level in w['levels']:
            ref=level['reference']
            if not ref['complete'] or len(ref['samples'])!=64:raise ValueError('declared reference coverage absent')
            rows=[]
            for index in range(2,64):
                a=evaluate_point(network,b,ref,index,80);high=evaluate_point(network,b,ref,index,100)
                rows.append(dict(index=index,time_s=ref['samples'][index]['history']['time_s'],
                    clock_times_s=[law.rational(t) for t in a['clock_times_s']],fine_times_s=[law.rational(t) for t in a['fine_times_s']],
                    operators={name:[law.rational(v) for v in weights] for name,weights in a['operators'].items()},
                    vectors={name:[str(v) for v in vector] for name,vector in a['vectors'].items()},
                    precision={name:metrics(vector,high['vectors'][name]) for name,vector in a['vectors'].items()},
                    decomposition=a['decomposition'],clock_ratio=law.rational(a['clock_ratio']),
                    clock_ratio_exceeds_solver_domain=a['clock_ratio']>2,command_ratio=law.rational(a['command_ratio']),
                    ideal_effective_dt_s=law.rational(a['ideal_effective_dt_s']),kernel_effective_dt_s=a['kernel_effective_dt_s'],
                    effective_dt_difference_s=str(a['effective_dt_difference_s']),beta=[str(v) for v in a['beta']],
                    conservation_gate_passed=abs(a['vectors']['conservation_error_a'][0])<lift(1e-30)))
            levels.append(dict(subdivisions=ref['subdivisions'],rows=rows,skipped_indices=[0,1],
                skip_reason='two preceding coarse samples from own fine continuation required'))
        differences=[]
        with localcontext() as ctx:
            ctx.prec=80
            for a,brow in zip(levels[0]['rows'],levels[1]['rows']):
                differences.append(dict(index=a['index'],time_s=a['time_s'],
                    binary_proxy_4_minus_2_a=[str(D(v)-D(u)) for u,v in zip(a['vectors']['binary_defect_proxy_a'],brow['vectors']['binary_defect_proxy_a'])]))
        windows.append(dict(name=w['name'],levels=levels,proxy_4_minus_2=differences))
        print(json.dumps(dict(window=w['name'],points=124,precision_passes=sum(all(v['passed'] for v in r['precision'].values())
            for l in levels for r in l['rows']))),flush=True)
    if hashes(PATHS)!=before:raise ValueError('charge-proxy sources changed')
    return dict(schema='rf-d/bdf-static-charge-proxy/v1',environment=env,source_sha256=before,windows=windows,
        indices=[2,63],absolute_gate=1e-30,relative_gate=1e-8,new_nonlinear_solves=0,
        diagnostic_only=True,derivative_is_interpolated=True,charges_are_authoritative_stored_values=True,
        coefficients_are_lifted_binary64=True,prior_reports_modified=False,integrator_changed=False,
        exact_temporal_defect_known=False,independent_error_estimator=False,temporal_error_bound_admitted=False,
        physical_switching_admitted=False,audio_admitted=False,deadline_admitted=False,
        limitation='charge differentiation proxy on numerical refined states; unknown interpolation and trajectory error, no smooth-derivative bound at switching or independent estimator')


def save(report):
    storage=store(report,OUTPUT);windows=[]
    for w in report['windows']:
        levels=[]
        for level in w['levels']:
            rows=level['rows'];names=rows[0]['vectors']
            levels.append(dict(subdivisions=level['subdivisions'],points=len(rows),
                precision_passes=sum(all(v['passed'] for v in r['precision'].values()) for r in rows),
                decomposition_passes=sum(r['decomposition']['passed'] for r in rows),
                conservation_passes=sum(r['conservation_gate_passed'] for r in rows),
                clock_ratios_exceeding_solver_domain=sum(r['clock_ratio_exceeds_solver_domain'] for r in rows),
                maximum_precision_scaled_error=max(v['maximum_scaled_error'] for r in rows for v in r['precision'].values()),
                maximum_absolute_values={name:max(abs(float(v)) for r in rows for v in r['vectors'][name]) for name in names},
                maximum_effective_interval_difference_s=max(abs(float(r['effective_dt_difference_s'])) for r in rows)))
        windows.append(dict(name=w['name'],levels=levels,maximum_proxy_4_minus_2_a=max(
            abs(float(v)) for r in w['proxy_4_minus_2'] for v in r['binary_proxy_4_minus_2_a'])))
    summary={k:v for k,v in report.items() if k!='windows'}|dict(storage=storage,windows=windows)
    SUMMARY.write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')
    return summary


if __name__=='__main__':save(generate())
