"""Continuous DAE residual on archived numerical states, without new solves."""
from decimal import Decimal as D,localcontext
from fractions import Fraction as F
import gzip,json
from pathlib import Path
import loudness_latch_bdf_static_precision_charge_proxy as proxy
import loudness_latch_bdf_charge_defect as law
import loudness_latch_directional_curvature as curvature
from circuit66_decimal_static import lift,evaluate as static_values
from loudness_latch_bdf_static_precision_integrator import CompensatedBdfNetwork
from loudness_latch_bdf_probes import unpack
from bjt_charge_ngspice_probes import model_parameters
from loudness_latch_bdf_doubling_survey import store
from loudness_latch_increment_probes import hashes
from loudness_lab_metadata import environment

ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/'evidence/loudness_latch_bdf_static_precision_continuous_charge.json.gz'
SUMMARY=ROOT/'evidence/loudness_latch_bdf_static_precision_continuous_charge_summary.json'
PROTOCOL=ROOT/'docs/BIESTABLE_CARGA_CONTINUA_PROTOCOLO.md'
PATHS=tuple(dict.fromkeys((*proxy.PATHS,Path(__file__).resolve(),PROTOCOL,proxy.OUTPUT,
    ROOT/'evidence/loudness_latch_bdf_static_precision_charge_proxy_validation.json')))


def nodes(state):
    return [lift(a)+lift(b) for a,b in zip(state.joint.node_v,state.node_low_v)]


def derivative(weights,vectors):
    # Subtract the destination: exact rational weights sum to zero.
    if sum(weights,F(0))!=0:raise ValueError('derivative must annihilate charge origin')
    return [sum((law.decimal_fraction(w)*(v[j]-vectors[0][j]) for w,v in
                 zip(weights[1:],vectors[1:])),D(0)) for j in range(len(vectors[0]))]


def incidence(network,rates):
    if len(rates)!=25:raise ValueError('25 charge rates required')
    nodal=[D(0)]*94;boundary=D(0)
    def stamp(left,right,current):
        nonlocal boundary
        if left is None:boundary+=current
        else:nodal[left]+=current
        if right is None:boundary-=current
        else:nodal[right]-=current
    for (left,right,_,_,_),current in zip(network.network.branches,rates[:21]):stamp(left,right,current)
    s=network.network.latch.device.parameters.polarity
    for i,terminals in enumerate(network.network.latch.terminals):
        b,c,e=[j for j,_ in terminals]
        stamp(b,e,s*rates[21+2*i]);stamp(b,c,s*rates[22+2*i])
    return nodal,boundary


def branch_equations(network,x,charge,rates):
    return [x[a]-(lift(fixed) if b is None else x[b])-q/lift(cap)-lift(resistance)*rate
            for (a,b,fixed,cap,resistance),q,rate in zip(network.network.branches,charge,rates)]


def evaluate_point(network,g,reference,index,precision=80):
    with localcontext() as ctx:
        ctx.prec=precision;fi=reference['samples'][index]['fine_step_index']
        steps=[reference['steps'][j] for j in range(fi,fi-4,-1)]
        states=[unpack(network,s['history']).current for s in steps]
        times=tuple(F(s['history']['time_s']) for s in steps)
        w4=law.lagrange_weights(times);w3=law.lagrange_weights(times[:3])
        coeff=steps[0]['diagnostics']['coefficients'];h=F(steps[0]['diagnostics']['actual_dt_s'])
        a0=F(coeff['a0']);a2=F(coeff['a2']);wb=(a0/h,-(a0+a2)/h,a2/h)
        qs=[proxy.charges(network,s) for s in states];xs=[nodes(s) for s in states]
        q4=derivative(w4,qs);q3=derivative(w3,qs[:3]);qb=derivative(wb,qs[:3])
        xd=derivative(w4,xs);x=xs[0]
        static,_=static_values(g,x,precision,jacobian=False)
        rounded,_=static_values(g,list(states[0].joint.node_v),precision,jacobian=False)
        dynamic4,boundary4=incidence(network,q4);dynamic3,boundary3=incidence(network,q3)
        dynamicb,boundaryb=incidence(network,qb)
        rate_delta=[a-b for a,b in zip(q4,qb)];delta,bd=incidence(network,rate_delta)
        cont=[a+b for a,b in zip(static,dynamic4)];discrete=[a+b for a,b in zip(static,dynamicb)]
        rounded_discrete=[a+b for a,b in zip(rounded,dynamicb)]
        eq4=branch_equations(network,x,qs[0],q4);eqb=branch_equations(network,x,qs[0],qb)
        series_delta=[-lift(r)*dq for (_,_,_,_,r),dq in zip(network.network.branches,rate_delta)]
        chain=[];q_offset=[];knees=[];p=network.network.latch.device.parameters
        for i,terminals in enumerate(network.network.latch.terminals):
            vv=[[xx[j] if j is not None else lift(fixed) for j,fixed in terminals] for xx in xs]
            uv=[xd[j] if j is not None else D(0) for j,_ in terminals]
            for j,(other,dep,transit,scale) in enumerate(((2,p.depletion_be,p.transit_forward_s,p.emission_be_v),
                                                        (1,p.depletion_bc,p.transit_reverse_s,p.emission_bc_v))):
                voltage=p.polarity*(vv[0][0]-vv[0][other]);velocity=p.polarity*(uv[0]-uv[other])
                q,c,_=curvature.junction_values(dep,transit,p.saturation_a,scale,voltage)
                chain.append(c*velocity);q_offset.append(qs[0][21+2*i+j]-q)
                knee=lift(dep.forward_fraction*dep.potential_v)
                sides=[p.polarity*(v[0]-v[other])<knee for v in vv]
                knees.append(any(sides) and not all(sides))
        chain_rates=q4[:21]+chain;chain_dynamic,_=incidence(network,chain_rates)
        vectors=dict(charge_cubic_rate_a=q4,charge_quadratic_rate_a=q3,fine_binary_rate_a=qb,
            cubic_minus_binary_a=rate_delta,nonlinear_chain_rate_a=chain,
            nonlinear_chain_mismatch_a=[a-b for a,b in zip(q4[21:],chain)],
            nonlinear_constitutive_offset_c=q_offset,node_cubic_velocity_v_per_s=xd,
            static_kcl_a=static,static_pair_minus_rounded_a=[a-b for a,b in zip(static,rounded)],
            continuous_kcl_a=cont,fine_binary_kcl_a=discrete,fine_binary_rounded_kcl_a=rounded_discrete,
            continuous_quadratic_kcl_a=[a+b for a,b in zip(static,dynamic3)],
            continuous_chain_kcl_a=[a+b for a,b in zip(static,chain_dynamic)],
            kcl_derivative_delta_a=delta,continuous_branch_equation_v=eq4,fine_binary_branch_equation_v=eqb,
            branch_derivative_delta_v=series_delta,dynamic_boundary_a=[boundary4,boundary3,boundaryb,bd],
            dynamic_conservation_error_a=[sum(v,D(0))+b for v,b in
                ((dynamic4,boundary4),(dynamic3,boundary3),(dynamicb,boundaryb),(delta,bd))])
        algebra=dict(kcl=curvature.metrics(cont,[r+d for r,d in zip(discrete,delta)]),
            branch=curvature.metrics(eq4,[r+d for r,d in zip(eqb,series_delta)]),
            rounded=curvature.metrics(discrete,[r+d for r,d in zip(rounded_discrete,vectors['static_pair_minus_rounded_a'])]))
        return dict(vectors=vectors,algebra=algebra,knee_crossings=knees,times=times,
            weights=dict(cubic=w4,quadratic=w3,binary=wb),fine_coefficients=coeff,fine_dt_s=steps[0]['diagnostics']['actual_dt_s'],
            fine_publication=steps[0]['publication'])


def generate():
    before=hashes(PATHS);env=environment();source=json.loads(gzip.decompress(proxy.REFERENCE.read_bytes()))['windows']
    network=CompensatedBdfNetwork(200,model_parameters(1,'finite_transit'));g=curvature.graph(network,10.);windows=[]
    for w in source:
        levels=[]
        for level in w['levels']:
            ref=level['reference'];rows=[]
            if not ref['complete'] or len(ref['samples'])!=64:raise ValueError('archived coverage missing')
            for index in range(2,64):
                a=evaluate_point(network,g,ref,index,80);b=evaluate_point(network,g,ref,index,100)
                rows.append(dict(index=index,time_s=ref['samples'][index]['history']['time_s'],
                    vectors={k:list(map(str,v)) for k,v in a['vectors'].items()},
                    precision={k:curvature.metrics(v,b['vectors'][k]) for k,v in a['vectors'].items()},algebra=a['algebra'],
                    knee_crossings=a['knee_crossings'],fine_times_s=[law.rational(t) for t in a['times']],
                    weights={k:[law.rational(t) for t in v] for k,v in a['weights'].items()},
                    fine_coefficients=a['fine_coefficients'],fine_dt_s=a['fine_dt_s'],fine_publication=a['fine_publication'],
                    observed_continuous_kcl_below_10pa=max(abs(v) for v in a['vectors']['continuous_kcl_a'])<lift(1e-11),
                    observed_lifted_fine_kcl_below_10pa=max(abs(v) for v in a['vectors']['fine_binary_kcl_a'])<lift(1e-11),
                    observed_continuous_branches_below_10fv=max(abs(v) for v in a['vectors']['continuous_branch_equation_v'])<lift(1e-14)))
            levels.append(dict(subdivisions=ref['subdivisions'],rows=rows,skipped_indices=[0,1]))
        with localcontext() as ctx:
            ctx.prec=80
            differences=[dict(index=a['index'],time_s=a['time_s'],continuous_kcl_4_minus_2_a=[str(D(v)-D(u)) for u,v in
                zip(a['vectors']['continuous_kcl_a'],b['vectors']['continuous_kcl_a'])])
                for a,b in zip(levels[0]['rows'],levels[1]['rows'])]
        windows.append(dict(name=w['name'],levels=levels,differences=differences))
        print(json.dumps(dict(window=w['name'],points=124)),flush=True)
    if hashes(PATHS)!=before:raise ValueError('continuous-charge inputs changed')
    return dict(schema='rf-d/bdf-static-continuous-charge/v1',environment=env,source_sha256=before,windows=windows,
        absolute_gate=1e-30,relative_gate=1e-8,new_nonlinear_solves=0,diagnostic_only=True,
        node_preparation='high+low inside Decimal80/100; rounded static comparison separate',
        branch_rates='stored authoritative Q; continuous incidence without beta filtering',
        prior_reports_modified=False,integrator_changed=False,exact_temporal_defect_known=False,
        independent_error_estimator=False,temporal_error_bound_admitted=False,physical_switching_admitted=False,
        audio_admitted=False,deadline_admitted=False,
        limitation='point residuals on numerical interpolants, not a solved continuous trajectory or a whole-interval/global bound')


def save(report):
    storage=store(report,OUTPUT);windows=[]
    for w in report['windows']:
        levels=[]
        for level in w['levels']:
            rows=level['rows'];names=rows[0]['vectors']
            levels.append(dict(subdivisions=level['subdivisions'],points=len(rows),
                precision_passes=sum(all(v['passed'] for v in r['precision'].values()) for r in rows),
                algebra_passes=sum(all(v['passed'] for v in r['algebra'].values()) for r in rows),
                maximum_precision_scaled_error=max(v['maximum_scaled_error'] for r in rows for v in r['precision'].values()),
                knee_crossing_coordinates=sum(sum(r['knee_crossings']) for r in rows),
                observation_passes={key:sum(r[key] for r in rows) for key in (
                    'observed_continuous_kcl_below_10pa','observed_lifted_fine_kcl_below_10pa','observed_continuous_branches_below_10fv')},
                maximum_absolute_values={k:max(abs(float(v)) for r in rows for v in r['vectors'][k]) for k in names}))
        windows.append(dict(name=w['name'],levels=levels,maximum_continuous_kcl_4_minus_2_a=max(
            abs(float(v)) for r in w['differences'] for v in r['continuous_kcl_4_minus_2_a'])))
    summary={k:v for k,v in report.items() if k!='windows'}|dict(storage=storage,windows=windows)
    SUMMARY.write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')
    return summary


if __name__=='__main__':save(generate())
