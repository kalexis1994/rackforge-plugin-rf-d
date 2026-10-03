"""Structured inverse and forcing reconstruction on 64 frozen temporal cells."""
from fractions import Fraction as F
import gzip,json
from pathlib import Path
import loudness_latch_cell_propagation as law
import loudness_latch_bdf_static_precision_weighted_descriptor as prior
import loudness_latch_bdf_static_precision_constitutive_enclosure as rectangular
import loudness_latch_bdf_static_precision_correlated_enclosure as correlated
from loudness_latch_increment_probes import hashes
from loudness_latch_bdf_doubling_survey import store
from loudness_lab_metadata import environment
ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/'evidence/loudness_latch_bdf_static_precision_cell_propagation.json.gz'
SUMMARY=ROOT/'evidence/loudness_latch_bdf_static_precision_cell_propagation_summary.json'
PROTOCOL=ROOT/'docs/BIESTABLE_PROPAGACION_CELDAS_PROTOCOLO.md'
PATHS=tuple(dict.fromkeys((*prior.PATHS,prior.OUTPUT,prior.SUMMARY,rectangular.OUTPUT,correlated.OUTPUT,
    ROOT/'evidence/loudness_latch_bdf_static_precision_weighted_descriptor_validation.json',
    Path(__file__).resolve(),Path(law.__file__).resolve(),PROTOCOL)))


def rows(path):
    data=json.loads(gzip.decompress(path.read_bytes()))
    return {(w['name'],l['subdivisions'],r['index']):r for w in data['windows'] for l in w['levels'] for r in l['rows']}


def generate():
    before=hashes(PATHS);env=environment();source=json.loads(gzip.decompress(prior.OUTPUT.read_bytes()))
    boxes=rows(rectangular.OUTPUT);rates=rows(correlated.OUTPUT)
    dense=prior.dense
    refs={(w['name'],l['reference']['subdivisions']):l['reference'] for w in json.loads(gzip.decompress(dense.previous.proxy.REFERENCE.read_bytes()))['windows'] for l in w['levels']}
    network=dense.CompensatedBdfNetwork(200,dense.model_parameters(1,'finite_transit'));cases=[]
    for case_index,old in enumerate(source['cases']):
        key=(old['window'],old['subdivisions'],old['index']);prepared=dense.prepare(network,refs[key[:2]],key[2])
        if not prepared['support_sha256']==old['support_sha256']==boxes[key]['support_sha256']==rates[key]['support_sha256']:
            raise ValueError('frozen support identities differ')
        forcing=law.residual_cells(boxes[key]['result'],rates[key]['result'],prepared['equations'],prepared['h'])
        parent_q=max(F(c['contraction_upper']) for c in old['ideal_temporal_cover']);cells=[]
        for cover,f in zip(old['ideal_temporal_cover'],forcing):
            inverse,certificate=law.structured_inverse(old['inverse_binary'],old['inverse_certificate']['column_scales'],cover,parent_q)
            cells.append(dict(inverse_certificate=certificate,forcing_inputs=f,metrics=law.metrics(inverse,94,old['weights'],f)))
        budgets=law.propagate(cells)
        sums={k:[str(sum((F(c['forcing_inputs'][k][j]) for c in cells),F(0))) for j in range(len(cells[0]['forcing_inputs'][k]))]
              for k in ('nodal_l1_c','constraint_l1_v_s')}
        parent=old['forcing_inputs']
        nonincreasing=all(F(v)<=F(p) for k,values in sums.items() for v,p in zip(values,parent[k]))
        if not nonincreasing:raise ValueError('recombined forcing exceeds parent budget')
        baseline=old['weighted_temporal_budget']
        row=dict(source_case_index=case_index,window=old['window'],subdivisions=old['subdivisions'],index=old['index'],
            duration_s=old['duration_s'],support_sha256=old['support_sha256'],weights=old['weights'],cells=cells,
            recombined_l1=sums,recombined_l1_nonincreasing=True,propagation=budgets,prior_weighted_temporal_budget=baseline,
            peak_node_budget_nonincreasing=F(budgets['peak_zero_anchor_node_upper_v'])<=F(baseline['zero_anchor_forced_node_upper_v']),
            binary_backward_gate_still_rejected=not old['backward_gate_passed'])
        cases.append(row)
        print(json.dumps(dict(window=old['window'],subdivisions=old['subdivisions'],cells=len(cells),
            peak_node_budget_nonincreasing=row['peak_node_budget_nonincreasing'])),flush=True)
    if hashes(PATHS)!=before:raise ValueError('cell propagation inputs changed')
    return dict(schema='rf-d/bdf-static-cell-propagation/v1',environment=env,source_sha256=before,cases=cases,
        neumann_order=1,cells_per_interval=8,weights_changed=False,new_exact_linear_systems=0,new_nonlinear_circuit_solves=0,
        ideal_time_varying_tangent_bound=True,nonlinear_remainder_bound=False,initial_error_known=False,actual_dae_error_bound=False,
        full_path_coverage=False,temporal_error_bound_admitted=False,physical_trajectory_bound=False,audio_admitted=False,deadline_admitted=False,
        numerical_gates_changed=False,prior_reports_modified=False,
        limitation='contiguous cells within eight noncontiguous selected intervals; tangent forcing only, unknown anchor and nonlinear remainder')


def save(report):
    storage=store(report,OUTPUT)
    summary={k:v for k,v in report.items() if k!='cases'}|dict(storage=storage,cases=[
        {k:c[k] for k in ('window','subdivisions','index','weights','recombined_l1_nonincreasing','peak_node_budget_nonincreasing','propagation')}|
        dict(cell_log_norms=[v['metrics']['logarithmic_norm_upper_per_s'] for v in c['cells']],
             strictly_narrower_entries=sum(v['inverse_certificate']['strictly_narrower_entries'] for v in c['cells'])) for c in report['cases']])
    SUMMARY.write_text(json.dumps(summary,indent=2,allow_nan=False)+chr(10),encoding='utf-8',newline=chr(10));return summary


if __name__=='__main__':save(generate())
