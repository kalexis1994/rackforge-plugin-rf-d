"""Interior reconstructed DAE residuals and exact polynomial constraints."""
from decimal import Decimal as D,localcontext
from fractions import Fraction as F
import gzip,hashlib,json
from pathlib import Path
import loudness_latch_dense_charge as poly
import loudness_latch_bdf_static_precision_continuous_charge as previous
import loudness_latch_bdf_charge_defect as law
import loudness_latch_directional_curvature as curvature
from circuit66_decimal_static import lift,evaluate as static_values
from loudness_latch_bdf_static_precision_integrator import CompensatedBdfNetwork
from loudness_latch_bdf_probes import unpack
from bjt_charge_ngspice_probes import model_parameters
from loudness_latch_bdf_doubling_survey import store,canonical
from loudness_latch_increment_probes import hashes
from loudness_lab_metadata import environment

ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/'evidence/loudness_latch_bdf_static_precision_dense_charge.json.gz'
SUMMARY=ROOT/'evidence/loudness_latch_bdf_static_precision_dense_charge_summary.json'
PROTOCOL=ROOT/'docs/BIESTABLE_CARGA_INTERIOR_PROTOCOLO.md'
PATHS=tuple(dict.fromkeys((*previous.PATHS,Path(__file__).resolve(),Path(poly.__file__).resolve(),PROTOCOL,
    previous.OUTPUT,ROOT/'evidence/loudness_latch_bdf_static_precision_continuous_charge_validation.json')))
FRACTIONS=(F(1,4),F(1,2),F(3,4))
DEPTH=40


def prepare(network,reference,index):
    fi=reference['samples'][index]['fine_step_index'];steps=[reference['steps'][j] for j in range(fi,fi-4,-1)]
    states=[unpack(network,s['history']).current for s in steps];times=tuple(F(s['history']['time_s']) for s in steps)
    h=times[0]-times[1];u=tuple((t-times[1])/h for t in times);basis=poly.cardinal_basis(u)
    x=poly.interpolate(basis,[[F(a)+F(b) for a,b in zip(s.joint.node_v,s.node_low_v)] for s in states])
    q=poly.interpolate(basis,[[F(cap)*(F(a)+F(b)) for (_,_,_,cap,_),(a,b) in
        zip(network.network.branches,s.capacitor_pairs_v)]+[F(v) for d in s.latch.devices for v in (d.be_c,d.bc_c)] for s in states])
    equations=[]
    for (a,b,fixed,cap,resistance),charge in zip(network.network.branches,q):
        terminal=poly.add(x[a],poly.scale(x[b],-1)) if b is not None else poly.add(x[a],(-F(fixed),))
        equations.append(poly.add(poly.add(terminal,poly.scale(charge,-1/F(cap))),
                                  poly.scale(poly.differentiate(charge),-F(resistance)/h)))
    p=network.network.latch.device.parameters;knee=[];junctions=[]
    for terminals in network.network.latch.terminals:
        vv=[x[j] if j is not None else (F(fixed),) for j,fixed in terminals]
        for other,dep,transit,scale in ((2,p.depletion_be,p.transit_forward_s,p.emission_be_v),
                                      (1,p.depletion_bc,p.transit_reverse_s,p.emission_bc_v)):
            v=poly.scale(poly.add(vv[0],poly.scale(vv[other],-1)),p.polarity)
            knee.append(poly.add(v,(-F(dep.forward_fraction*dep.potential_v),)))
            junctions.append((v,dep,transit,scale))
    return dict(x=x,q=q,equations=tuple(equations),knees=tuple(knee),junctions=tuple(junctions),
        times=times,h=h,u=u,support_sha256=[hashlib.sha256(canonical(s['history'])).hexdigest() for s in steps])


def query(network,g,prepared,u,precision=80):
    with localcontext() as ctx:
        ctx.prec=precision;cv=law.decimal_fraction;h=prepared['h']
        x=[cv(poly.evaluate(p,u)) for p in prepared['x']];q=[cv(poly.evaluate(p,u)) for p in prepared['q']]
        rates=[cv(poly.evaluate(poly.differentiate(p),u)/h) for p in prepared['q']]
        static,_=static_values(g,x,precision,jacobian=False);dynamic,boundary=previous.incidence(network,rates)
        chain=[];offset=[];sides=[];p=network.network.latch.device.parameters
        for j,(v,dep,transit,scale) in enumerate(prepared['junctions']):
            voltage=cv(poly.evaluate(v,u));velocity=cv(poly.evaluate(poly.differentiate(v),u)/h)
            constitutive,c,_=curvature.junction_values(dep,transit,p.saturation_a,scale,voltage)
            chain.append(c*velocity);offset.append(q[21+j]-constitutive)
            sides.append(voltage<lift(dep.forward_fraction*dep.potential_v))
        chain_rates=rates[:21]+chain;dynamic_chain,boundary_chain=previous.incidence(network,chain_rates)
        delta,boundary_delta=previous.incidence(network,[D(0)]*21+[a-b for a,b in zip(rates[21:],chain)])
        kcl=[a+b for a,b in zip(static,dynamic)];kcl_chain=[a+b for a,b in zip(static,dynamic_chain)]
        equations=previous.branch_equations(network,x,q,rates)
        exact_equations=[cv(poly.evaluate(e,u)) for e in prepared['equations']]
        vectors=dict(continuous_kcl_a=kcl,continuous_chain_kcl_a=kcl_chain,
            charge_rate_a=rates,nonlinear_chain_rate_a=chain,nonlinear_constitutive_offset_c=offset,
            nonlinear_rate_mismatch_a=[a-b for a,b in zip(rates[21:],chain)],
            branch_equation_v=equations,kcl_chain_delta_a=delta,
            dynamic_boundary_a=[boundary,boundary_chain,boundary_delta],
            dynamic_conservation_error_a=[sum(v,D(0))+b for v,b in
                ((dynamic,boundary),(dynamic_chain,boundary_chain),(delta,boundary_delta))])
        return dict(vectors=vectors,knee_below=sides,algebra=dict(
            kcl_chain=curvature.metrics(kcl,[a+b for a,b in zip(kcl_chain,delta)]),
            exact_branch=curvature.metrics(exact_equations,equations)))


def serialize(value):
    if isinstance(value,F):return law.rational(value)
    if isinstance(value,dict):return {k:serialize(v) for k,v in value.items()}
    if isinstance(value,(list,tuple)):return [serialize(v) for v in value]
    return value


def certificate(prepared):
    branches=[]
    for equation in prepared['equations']:
        b=poly.bernstein(equation);maximum=max(map(abs,b))
        branches.append(dict(power=equation,bernstein=b,lower=min(b),upper=max(b),
            absolute_upper_v=maximum,whole_interpolant_below_10fv=maximum<F(1e-14)))
    knees=[]
    for v in prepared['knees']:
        intervals=[]
        for left,right in ((F(0),F(1)),(prepared['u'][-1],F(1))):
            b=poly.bernstein(v,left,right);isolated=poly.isolate_zero(v,left,right,DEPTH)
            intervals.append(dict(left=left,right=right,bernstein=b,lower=min(b),upper=max(b),
                strict_same_piece=min(b)>0 or max(b)<0,zero_cover=isolated))
        knees.append(dict(power=v,intervals=intervals))
    return dict(branches=branches,knees=knees)


def generate():
    before=hashes(PATHS);env=environment();source=json.loads(gzip.decompress(previous.proxy.REFERENCE.read_bytes()))['windows']
    old=json.loads(gzip.decompress(previous.OUTPUT.read_bytes()))['windows']
    network=CompensatedBdfNetwork(200,model_parameters(1,'finite_transit'));g=curvature.graph(network,10.);windows=[]
    for w,ow in zip(source,old):
        if w['name']!=ow['name']:raise ValueError('window order changed')
        levels=[]
        for level,ol in zip(w['levels'],ow['levels']):
            ref=level['reference'];rows=[]
            if not ref['complete'] or len(ref['samples'])!=64:raise ValueError('archived support absent')
            for index in range(2,64):
                prepared=prepare(network,ref,index);cert=certificate(prepared);queries=[]
                for u in FRACTIONS:
                    try:
                        a=query(network,g,prepared,u,80);b=query(network,g,prepared,u,100)
                        queries.append(dict(u=serialize(u),time_s=serialize(prepared['times'][1]+u*prepared['h']),
                            vectors={k:list(map(str,v)) for k,v in a['vectors'].items()},knee_below=a['knee_below'],algebra=a['algebra'],
                            precision={k:curvature.metrics(v,b['vectors'][k]) for k,v in a['vectors'].items()},
                            observed_kcl_below_10pa=max(map(abs,a['vectors']['continuous_kcl_a']))<lift(1e-11),
                            observed_branches_below_10fv=max(map(abs,a['vectors']['branch_equation_v']))<lift(1e-14),failure=None))
                    except (ValueError,OverflowError) as exc:
                        queries.append(dict(u=serialize(u),time_s=serialize(prepared['times'][1]+u*prepared['h']),failure=str(exc)))
                end=query(network,g,prepared,F(1),100);prior=ol['rows'][index-2]
                endpoint={new:curvature.metrics(list(map(D,prior['vectors'][oldname])),end['vectors'][new]) for new,oldname in (
                    ('continuous_kcl_a','continuous_kcl_a'),('continuous_chain_kcl_a','continuous_chain_kcl_a'),
                    ('charge_rate_a','charge_cubic_rate_a'),('branch_equation_v','continuous_branch_equation_v'),
                    ('nonlinear_constitutive_offset_c','nonlinear_constitutive_offset_c'))}
                rows.append(dict(index=index,interval_s=serialize(prepared['times'][1::-1]),support_times_s=serialize(prepared['times']),
                    normalized_support=serialize(prepared['u']),support_sha256=prepared['support_sha256'],
                    certificate=serialize(cert),queries=queries,endpoint_replay=endpoint))
            levels.append(dict(subdivisions=ref['subdivisions'],rows=rows,skipped_indices=[0,1]))
        windows.append(dict(name=w['name'],levels=levels));print(json.dumps(dict(window=w['name'],interior_queries=372)),flush=True)
    if hashes(PATHS)!=before:raise ValueError('dense reconstruction inputs changed')
    return dict(schema='rf-d/bdf-static-dense-charge/v1',environment=env,source_sha256=before,windows=windows,
        fractions=serialize(FRACTIONS),root_cover_depth=DEPTH,new_nonlinear_solves=0,
        diagnostic_only=True,exact_polynomial_constraints=True,whole_interpolant_knee_cover=True,
        prior_reports_modified=False,integrator_changed=False,physical_trajectory_bound=False,
        exact_temporal_defect_known=False,independent_error_estimator=False,temporal_error_bound_admitted=False,
        physical_switching_admitted=False,audio_admitted=False,deadline_admitted=False,
        limitation='bounds and zero covers belong to exact rational numerical interpolants, not the physical trajectory; point KCL has no whole-interval bound')


def save(report):
    storage=store(report,OUTPUT);windows=[]
    for w in report['windows']:
        levels=[]
        for level in w['levels']:
            rows=level['rows'];qs=[q for r in rows for q in r['queries']];valid=[q for q in qs if q['failure'] is None]
            levels.append(dict(subdivisions=level['subdivisions'],intervals=len(rows),queries=len(qs),failed_queries=len(qs)-len(valid),
                precision_passes=sum(all(v['passed'] for v in q['precision'].values()) for q in valid),
                algebra_passes=sum(all(v['passed'] for v in q['algebra'].values()) for q in valid),
                endpoint_passes=sum(all(v['passed'] for v in r['endpoint_replay'].values()) for r in rows),
                observed_kcl_passes=sum(q['observed_kcl_below_10pa'] for q in valid),
                observed_branch_passes=sum(q['observed_branches_below_10fv'] for q in valid),
                whole_interpolant_branch_passes=sum(all(b['whole_interpolant_below_10fv'] for b in r['certificate']['branches']) for r in rows),
                maximum_absolute_values={k:max(abs(float(v)) for q in valid for v in q['vectors'][k]) for k in valid[0]['vectors']} if valid else {},
                maximum_branch_bernstein_bound_v=max(float(F(b['absolute_upper_v']['numerator'],b['absolute_upper_v']['denominator']))
                    for r in rows for b in r['certificate']['branches']),
                knee_intervals=[dict(domain=domain,strict_same_piece=sum(k['intervals'][domain]['strict_same_piece'] for r in rows for k in r['certificate']['knees']),
                    opposite_sign_brackets=sum(sum(b['opposite_endpoint_signs'] for b in k['intervals'][domain]['zero_cover']['brackets']) for r in rows for k in r['certificate']['knees']),
                    unresolved_brackets=sum(sum(not b['opposite_endpoint_signs'] for b in k['intervals'][domain]['zero_cover']['brackets']) for r in rows for k in r['certificate']['knees']),
                    exact_root_points=sum(len(k['intervals'][domain]['zero_cover']['exact_points']) for r in rows for k in r['certificate']['knees'])) for domain in (0,1)]))
        windows.append(dict(name=w['name'],levels=levels))
    summary={k:v for k,v in report.items() if k!='windows'}|dict(storage=storage,windows=windows)
    SUMMARY.write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n');return summary


if __name__=='__main__':save(generate())
