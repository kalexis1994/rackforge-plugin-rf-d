"""Fixed directed block bank for the archived first nonlinear startup tube."""
from pathlib import Path
from fractions import Fraction as F
import json
import loudness_latch_bdf_static_precision_startup_tube as prior
import loudness_latch_startup_blocks as law
from loudness_latch_increment_probes import hashes
from loudness_latch_bdf_doubling_survey import store
from loudness_lab_metadata import environment
ROOT=prior.ROOT
OUTPUT=ROOT/'evidence/loudness_latch_bdf_static_precision_startup_blocks.json.gz'
SUMMARY=ROOT/'evidence/loudness_latch_bdf_static_precision_startup_blocks_summary.json'
PROTOCOL=ROOT/'docs/BIESTABLE_TUBO_BLOQUES_PROTOCOLO.md'
PATHS=tuple(dict.fromkeys((*prior.PATHS,prior.OUTPUT,prior.SUMMARY,
    ROOT/'evidence/loudness_latch_bdf_static_precision_startup_tube_validation.json',
    ROOT/'evidence/loudness_latch_bdf_static_precision_startup_tube_inputs.json.gz',
    ROOT/'evidence/loudness_latch_bdf_static_precision_startup_tube_inputs_summary.json',
    ROOT/'evidence/loudness_latch_bdf_static_precision_startup_tube_inputs_validation.json',
    Path(__file__).resolve(),Path(law.__file__).resolve(),PROTOCOL,
    *(ROOT/'tools'/name for name in ('loudness_latch_block_comparison.py','loudness_latch_junction_rms.py',
        'loudness_latch_junction_metric.py','loudness_latch_junction_directed.py','loudness_latch_junction_balanced.py',
        'loudness_latch_junction_modal.py','loudness_latch_spectral_junction.py')))))
read=prior.read

def generate():
    before=hashes(PATHS);env=environment();source=read(prior.OUTPUT);startup=read(prior.prior.OUTPUT)
    weights=list(map(F,source['weights']));scales=list(map(F,source['descriptor_scales']));trials=[]
    origin=F(startup['initial_bound']['node_error_upper_v'])
    for trial in source['trials']:
        inverses=[];certificates=[];generators=[]
        for base,row in zip(source['base_cells'],trial['cells']):
            if not row['inverse_certified']:raise ValueError('archived whole tube inverse required')
            inverse,cert=prior.law.cells.structured_inverse(base['inverse_binary'],scales,row['cover'],F(row['cover']['contraction_upper']))
            if cert!=row['inverse_certificate']:raise ValueError('archived inverse reconstruction differs')
            inverses.append(inverse);certificates.append(cert);generators.append(law.generator(inverse,weights))
        metric=law.quadratic.candidate(generators)
        prepared=law.directed.basis(metric) if metric['accepted'] else None
        balance=law.balanced.balance(prepared) if prepared else None
        modes=[]
        for mode in law.MODES:
            if mode=='quadratic_balanced' and not metric['accepted']:
                modes.append(dict(mode=mode,cells=[],initial_block_error_upper_v=None,result=dict(accepted=False,reason=metric['rejection'],actual_dae_error_bound=False)));continue
            initial=law.initial_vector(source['initial_memory'],mode,metric);rows=[]
            for k,(old,inverse,cert) in enumerate(zip(trial['cells'],inverses,certificates)):
                metrics,rate=law.cell_metrics(inverse,weights,old['forcing_inputs'],mode,metric,prepared,balance)
                rows.append(dict(index=k,inverse_certified=True,forcing_inputs=old['forcing_inputs'],metrics=metrics,rate_certificate=rate,
                    inverse_certificate=cert,inverse_intervals_sha256=law.quadratic.box.digest(prior.law.cells.packed_matrix(inverse))))
            result=law.close(rows,initial,F(trial['radius_v']),origin)
            modes.append(dict(mode=mode,initial_block_error_upper_v=initial,cells=rows,result=result))
            print(json.dumps(dict(radius_v=float(F(trial['radius_v'])),mode=mode,accepted=result['accepted'],node_bound_v=float(F(result['peak_node_error_upper_v'])) if 'peak_node_error_upper_v' in result else None,reason=result['reason'])),flush=True)
        trials.append(dict(radius_v=trial['radius_v'],metric=metric,congruence=prepared,balance=balance,modes=modes,prior_scalar_result=trial['result']))
    selected=next(([i,j] for i,t in enumerate(trials) for j,m in enumerate(t['modes']) if m['result']['accepted']),None)
    if hashes(PATHS)!=before:raise ValueError('startup block inputs changed')
    return dict(schema='rf-d/bdf-static-startup-blocks/v1',environment=env,source_sha256=before,
        weights=source['weights'],blocks=[list(v) for v in law.blocks.BLOCKS],block_names=list(law.blocks.NAMES),mode_order=list(law.MODES),
        initial_memory=source['initial_memory'],duration_s=source['duration_s'],trials=trials,primary_trial_mode=selected,
        new_nonlinear_solves=0,new_preconditioners=0,metric_systems_attempted=3,real_support_states=2,
        fixed_candidate_bank=True,metric_constant_whole_interval=True,original_integrator_modified=False,prior_reports_modified=False,numerical_gates_changed=False,
        first_interval_nonlinear_error_proven=selected is not None,continuous_actual_error_certified_duration_s=source['duration_s'] if selected else '0',
        full_path_coverage=False,global_1mv_gate_closed=False,physical_trajectory_bound=False,audio_admitted=False,deadline_admitted=False)

def save(report):
    if OUTPUT==SUMMARY or OUTPUT in PATHS or SUMMARY in PATHS:raise ValueError('output/input destination collision')
    storage=store(report,OUTPUT);summary={k:v for k,v in report.items() if k not in ('trials','initial_memory')}
    summary.update(storage=storage,trials=[dict(radius_v=t['radius_v'],metric_accepted=t['metric']['accepted'],metric_rejection=t['metric']['rejection'],
        modes=[dict(mode=m['mode'],result={k:v for k,v in m['result'].items() if k!='propagation'}) for m in t['modes']]) for t in report['trials']])
    SUMMARY.write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n');return summary
if __name__=='__main__':save(generate())
