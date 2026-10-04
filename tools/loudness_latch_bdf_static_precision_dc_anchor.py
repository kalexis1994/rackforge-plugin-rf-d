"""Frozen DC existence enclosure and KEY event domain obstruction."""
from fractions import Fraction as F
from decimal import Decimal as D,localcontext
from pathlib import Path
import gzip,json
import numpy as np
import loudness_latch_dc_anchor as law
import loudness_latch_bdf_static_precision_coverage_bridge as prior
from loudness_latch_bdf_static_precision_integrator import CompensatedBdfNetwork
from loudness_latch_bdf_probes import unpack
from bjt_charge_ngspice_probes import model_parameters
from loudness_latch_directional_curvature import graph
from circuit66_decimal_static import evaluate
from loudness_latch_weighted_descriptor import dyadic_floor
from loudness_latch_increment_probes import hashes
from loudness_latch_bdf_doubling_survey import store
from loudness_lab_metadata import environment
ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/'evidence/loudness_latch_bdf_static_precision_dc_anchor.json.gz'
SUMMARY=ROOT/'evidence/loudness_latch_bdf_static_precision_dc_anchor_summary.json'
PROTOCOL=ROOT/'docs/BIESTABLE_DC_EVENTO_PROTOCOLO.md'
RADII=(F(1,10**9),F(1,10**8),F(1,10**7),F(1,10**6))
SCALE=F(1e-12)
PATHS=tuple(dict.fromkeys((*prior.PATHS,prior.OUTPUT,prior.SUMMARY,
    ROOT/'evidence/loudness_latch_bdf_static_precision_coverage_bridge_validation.json',
    ROOT/'evidence/loudness_latch_bdf_static_precision_coverage_inputs.json.gz',
    ROOT/'evidence/loudness_latch_bdf_static_precision_coverage_inputs_summary.json',
    ROOT/'evidence/loudness_latch_bdf_static_precision_coverage_inputs_validation.json',
    Path(__file__).resolve(),Path(law.__file__).resolve(),PROTOCOL)))
def read(p):return json.loads(gzip.decompress(p.read_bytes()))
def memory_enclosure(network,state,center,error):
    net=network.network;x=list(map(F,center));error=F(error);rows=[];weights=[F(1)]*21
    if len(x)!=94 or error<0:raise ValueError('complete DC center and nonnegative error required')
    for i,(a,b,fixed,cap,resistance) in enumerate(net.branches):
        value=x[a]-(x[b] if b is not None else F(fixed));r=error*(2 if b is not None else 1);scale=F(cap)
        q=(scale*(value-r),scale*(value+r));stored=scale*sum(map(F,state.capacitor_pairs_v[i]),F(0));e=max(abs(v-stored) for v in q)
        rows.append(dict(index=i,kind='linear',left=a,right=b,scale_c_per_v=str(scale),ideal_charge_interval_c=list(map(str,q)),stored_charge_c=str(stored),error_upper_c=str(e),coordinate_error_upper_v=str(e/scale)))
    p=net.latch.device.parameters
    for k,terminals in enumerate(net.latch.terminals):
        v=[x[i] if i is not None else F(fixed) for i,fixed in terminals];device=state.latch.devices[k]
        for offset,other,dep,transit,emission,stored in ((0,2,p.depletion_be,p.transit_forward_s,p.emission_be_v,device.be_c),(1,1,p.depletion_bc,p.transit_reverse_s,p.emission_bc_v,device.bc_c)):
            i=21+2*k+offset;value=F(p.polarity)*(v[0]-v[other]);r=error*sum(terminals[j][0] is not None for j in (0,other))
            qlo,_=law.iv.junction_bounds(dep,transit,p.saturation_a,emission,value-r);qhi,_=law.iv.junction_bounds(dep,transit,p.saturation_a,emission,value+r)
            _,cap=law.iv.junction_bounds(dep,transit,p.saturation_a,emission,value)
            if cap[0]<=0:raise ValueError('positive center capacitance required')
            w=dyadic_floor(SCALE/cap[1]);weights.append(w);q=(qlo[0],qhi[1]);stored=F(stored);e=max(abs(v-stored) for v in q)
            rows.append(dict(index=i,kind='junction',device_index=k,other_terminal_index=other,voltage_interval_v=[str(value-r),str(value+r)],
                center_capacitance_interval_f=list(map(str,cap)),scale_c_per_v=str(SCALE),ideal_charge_interval_c=list(map(str,q)),stored_charge_c=str(stored),error_upper_c=str(e),coordinate_error_upper_v=str(e/SCALE)))
    if len(rows)!=25 or len(weights)!=25:raise ValueError('complete 25-memory enclosure required')
    for row,w in zip(rows,weights):row['weight']=str(w);row['weighted_error_upper_v']=str(w*F(row['coordinate_error_upper_v']))
    return dict(rows=rows,weights=list(map(str,weights)),weighted_infinity_error_upper_v=str(max(F(v['weighted_error_upper_v']) for v in rows)),
        dc_charge_error_bound_proven=True,post_key_charge_error_bound_proven=False,weight_policy='linear=1; junction=dyadic_floor(S/Cupper(center)); new initial norm, requires later conversion')

def event_audit(network,g,center,error):
    key='contour/KEYBOARD_TRIGGER';devices=[d for d in g['diodes'] if d['anode']==key]
    if len(devices)!=1 or devices[0]['ref']!='CR10-contour':raise ValueError('frozen CR10 KEY connection required')
    d=devices[0];node=d['cathode'];vt=F(d['ideality'])*F(d['vt']);x=F(center[node]);r=F(error);post=F(10)
    exponent=((post-x-r)/vt,(post-x+r)/vt);minimum_voltage=post-45*vt;minimum_jump=minimum_voltage-(x+r)
    ports=[i for i,(a,b,_,_,_) in enumerate(network.network.branches) if node in (a,b)]
    for k,terminals in enumerate(network.network.latch.terminals):
        for offset,other in ((0,2),(1,1)):
            if node in (terminals[0][0],terminals[other][0]):ports.append(21+2*k+offset)
    return dict(device=d,graph_key_before_v=str(F(g['fixed'][key])),key_after_v=str(post),node_row_index=node,
        pre_event_node_interval_v=[str(x-r),str(x+r)],post_key_exponent_with_frozen_nodes=list(map(str,exponent)),domain_upper='45',
        frozen_voltage_hypothesis_admissible=exponent[1]<=45,frozen_voltage_hypothesis_refuted=exponent[0]>45,
        minimum_post_event_node_v=str(minimum_voltage),minimum_upward_jump_for_domain_v=str(minimum_jump),
        modeled_memory_ports=ports,modeled_mass_row_zero=not ports,physical_parasitics_identified=False,
        post_event_state_solved=False,post_event_anchor_error_bound_proven=False,exponential_evaluated_outside_domain=False)

def generate():
    before=hashes(PATHS);env=environment();frozen=read(prior.FIXED);network=CompensatedBdfNetwork(200,model_parameters(1,'finite_transit'));history=unpack(network,frozen['initial']);state=history.current
    if history.time_s!=0 or history.key_v!=0 or history.previous is not None:raise ValueError('frozen initial DC KEY=0 required')
    center=[F(a)+F(b) for a,b in zip(state.joint.node_v,state.node_low_v)];g=graph(network,0.)
    with localcontext() as ctx:
        ctx.prec=100;decimal_center=[D(v.numerator)/D(v.denominator) for v in center];r,j=evaluate(g,decimal_center,100)
    inverse=np.linalg.inv(np.array(j,dtype=float)).tolist()
    if not np.isfinite(inverse).all():raise ValueError('finite offline static preconditioner required')
    compiled=law.compile_graph(g,center,inverse);certificates=[]
    for radius in RADII:
        cert=law.certify(compiled,radius);certificates.append(cert)
        print(json.dumps(dict(radius_v=float(radius),accepted=cert['accepted'],q=float(F(cert['contraction_upper'])),eta_v=float(F(cert['eta_upper_v'])))),flush=True)
    primary=next((i for i,c in enumerate(certificates) if c['accepted']),None);memory=event=None
    if primary is not None:
        error=F(certificates[primary]['posterior_error_upper_v']);memory=memory_enclosure(network,state,center,error);event=event_audit(network,g,center,error)
    if hashes(PATHS)!=before:raise ValueError('DC/event sources changed')
    return dict(schema='rf-d/bdf-static-dc-anchor/v1',environment=env,source_sha256=before,initial_history_sha256=law.digest(frozen['initial']),
        graph=g,center_node_v=list(map(str,center)),decimal100_residual_a=list(map(str,r)),decimal100_jacobian_sha256=law.digest([[str(v) for v in row] for row in j]),
        inverse_binary=inverse,compiled_policy=compiled['residual_policy'],certificates=certificates,primary_certificate_index=primary,
        memory_enclosure=memory,event_audit=event,dc_root_enclosure_proven=primary is not None,
        dc_memory_error_bound_proven=memory is not None,post_key_initial_error_known=False,initial_error_known=False,
        new_binary_preconditioners=1,new_dc_nonlinear_solves=0,binary_preconditioner_audio_admitted=False,
        prior_parameters_changed=False,prior_norms_changed=False,nonlinear_remainder_bound=False,actual_dae_error_bound=False,
        full_path_coverage=False,temporal_error_bound_admitted=False,physical_trajectory_bound=False,audio_admitted=False,deadline_admitted=False,
        numerical_gates_changed=False,prior_reports_modified=False,
        limitation='local ideal static DC enclosure only; KEY event is not initialized, charge consistency and temporal error remain separate')
def save(report):
    if OUTPUT==SUMMARY or OUTPUT in PATHS or SUMMARY in PATHS:raise ValueError('output/input destination collision')
    storage=store(report,OUTPUT);summary={k:v for k,v in report.items() if k not in ('inverse_binary','certificates','decimal100_residual_a','graph')}
    summary.update(storage=storage,certificates=[{k:v for k,v in c.items() if k not in ('defect_intervals','exponent_ranges','preconditioned_residual_intervals','row_image_radius_v')} for c in report['certificates']])
    SUMMARY.write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n');return summary
if __name__=='__main__':save(generate())
