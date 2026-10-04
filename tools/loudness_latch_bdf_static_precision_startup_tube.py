"""Frozen first-interval affine reconstruction and three nonlinear tube trials."""
from pathlib import Path
from fractions import Fraction as F
from decimal import localcontext
import json
import numpy as np
import loudness_latch_bdf_static_precision_post_key_startup as prior
import loudness_latch_startup_tube as law
from loudness_latch_continuous_descriptor import descriptor
from loudness_latch_increment_probes import hashes
from loudness_latch_bdf_doubling_survey import store
from loudness_lab_metadata import environment
ROOT=prior.ROOT
OUTPUT=ROOT/'evidence/loudness_latch_bdf_static_precision_startup_tube.json.gz'
SUMMARY=ROOT/'evidence/loudness_latch_bdf_static_precision_startup_tube_summary.json'
PROTOCOL=ROOT/'docs/BIESTABLE_PRIMER_TUBO_PROTOCOLO.md'
RADII=(F(1,10**7),F(1,10**6),F(1,10**5))
CELLS=8
RATE_WEIGHT=F(1,2**30)
PATHS=tuple(dict.fromkeys((*prior.PATHS,prior.OUTPUT,prior.SUMMARY,
    ROOT/'evidence/loudness_latch_bdf_static_precision_post_key_startup_validation.json',
    ROOT/'evidence/loudness_latch_bdf_static_precision_post_key_inputs.json.gz',
    ROOT/'evidence/loudness_latch_bdf_static_precision_post_key_inputs_summary.json',
    ROOT/'evidence/loudness_latch_bdf_static_precision_post_key_inputs_validation.json',
    Path(law.__file__).resolve(),Path(__file__).resolve(),PROTOCOL,
    ROOT/'tools/loudness_latch_dense_charge.py',ROOT/'tools/loudness_latch_weighted_descriptor.py',
    ROOT/'tools/loudness_latch_cell_propagation.py',ROOT/'tools/loudness_latch_constitutive_enclosure.py')))

def read(path):return prior.prior.prior.prior.read(path)
def generate():
    before=hashes(PATHS);env=environment();startup=read(prior.OUTPUT);dc=read(prior.prior.prior.prior.OUTPUT)
    constructor=prior.prior.prior.prior
    network=constructor.CompensatedBdfNetwork(200,constructor.model_parameters(1,'finite_transit'))
    projection=read(prior.prior.prior.OUTPUT);g=projection['graph']
    initial=law.origin.restore(network,startup['origin']);endpoint=prior.unpack(network,startup['rows'][0]['history'])
    prepared=law.prepare(network,initial,endpoint);weights=list(map(F,dc['memory_enclosure']['weights']))
    anchor=law.initial_memory(network,prepared,dc,weights);scales=[F(1)]*94+[RATE_WEIGHT]*25;power_gains=law.gains(network,g)
    compiled=[];base=[]
    for k in range(CELLS):
        left,right=F(k,CELLS),F(k+1,CELLS);mid=(left+right)/2;x=[law.poly.evaluate(v,mid) for v in prepared['x']]
        with localcontext() as ctx:
            ctx.prec=100;h,_=descriptor(network,g,[law.event.decimal(v) for v in x],100)
        inverse=np.linalg.inv(np.array(h,dtype=float)).tolist()
        if not np.isfinite(inverse).all():raise ValueError('finite candidate preconditioner required')
        constant,terms=law.weighted.compile_terms(network,g,prepared,inverse,scales);compiled.append((constant,terms))
        residual,forcing=law.forcing(network,g,prepared,left,right)
        base.append(dict(index=k,left=str(left),right=str(right),inverse_binary=inverse,
            descriptor_binary_sha256=law.event.dc.digest(np.array(h,dtype=float).tolist()),
            forcing_inputs=forcing,residual_bounds=residual))
    trials=[]
    for radius in RADII:
        rows=[]
        for k,(item,(constant,terms)) in enumerate(zip(base,compiled)):
            cover=law.inflated_cover(constant,terms,power_gains,F(item['left']),F(item['right']),radius)
            row=dict(index=k,cover=cover,inverse_certified=cover['strict_contraction'],forcing_inputs=item['forcing_inputs'])
            if row['inverse_certified']:
                inverse,certificate=law.cells.structured_inverse(item['inverse_binary'],scales,cover,F(cover['contraction_upper']))
                row.update(inverse_certificate=certificate,metrics=law.cells.metrics(inverse,94,weights,item['forcing_inputs']))
            rows.append(row)
            print(json.dumps(dict(radius_v=float(radius),cell=k,q=float(F(cover['contraction_upper'])),inverse_certified=row['inverse_certified'])),flush=True)
        result=law.close(rows,F(anchor['error_upper_v']),radius,F(startup['initial_bound']['node_error_upper_v']))
        trials.append(dict(radius_v=str(radius),cells=rows,result=result))
        print(json.dumps(dict(radius_v=float(radius),accepted=result['accepted'],reason=result['reason'],node_bound_v=float(F(result['peak_node_error_upper_v'])) if 'peak_node_error_upper_v' in result else None)),flush=True)
    selected=next((i for i,t in enumerate(trials) if t['result']['accepted']),None)
    queries=[dict(u=str(u),decimal80=law.query(network,g,prepared,u,80),decimal100=law.query(network,g,prepared,u,100)) for u in (F(0),F(1,4),F(1,2),F(3,4),F(1))]
    if hashes(PATHS)!=before:raise ValueError('startup tube inputs changed')
    # serialize rational polynomial/interval data without lossy floats
    def serialize(value):
        if isinstance(value,F):return str(value)
        if isinstance(value,dict):return {k:serialize(v) for k,v in value.items() if k!='junctions'}
        if isinstance(value,(tuple,list)):return [serialize(v) for v in value]
        return value
    return serialize(dict(schema='rf-d/bdf-static-startup-tube/v1',environment=env,source_sha256=before,
        prepared=prepared,initial_memory=anchor,weights=weights,descriptor_scales=scales,base_cells=base,
        trials=trials,primary_trial_index=selected,queries=queries,duration_s=prepared['h'],
        new_nonlinear_solves=0,new_preconditioners=CELLS,real_support_states=2,fabricated_history=False,
        constitutive_junction_path=True,original_integrator_modified=False,prior_reports_modified=False,numerical_gates_changed=False,
        first_interval_nonlinear_error_proven=selected is not None,
        continuous_actual_error_certified_duration_s=str(prepared['h']) if selected is not None else '0',
        full_path_coverage=False,global_1mv_gate_closed=False,physical_trajectory_bound=False,audio_admitted=False,deadline_admitted=False,
        limitation='first right-limit interval only; rejected radii retained; no global trajectory, hardware or native promotion'))

def save(report):
    if OUTPUT==SUMMARY or OUTPUT in PATHS or SUMMARY in PATHS:raise ValueError('output/input destination collision')
    storage=store(report,OUTPUT);summary={k:v for k,v in report.items() if k not in ('prepared','base_cells','queries','trials')}
    summary.update(storage=storage,trials=[dict(radius_v=t['radius_v'],result=t['result'],inverse_certified_cells=sum(c['inverse_certified'] for c in t['cells']),
        maximum_q=str(max(F(c['cover']['contraction_upper']) for c in t['cells']))) for t in report['trials']])
    SUMMARY.write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n');return summary
if __name__=='__main__':save(generate())
