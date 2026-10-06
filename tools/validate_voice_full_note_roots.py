"""Replay stored precise-root residuals and native pairs; no refactorization."""
from decimal import Decimal,localcontext
import json
from pathlib import Path
import voice_full_note_matrix_trace as matrix
import voice_full_note_matrix_probe as probe
import voice_refine_trace as refine
import analyze_voice_full_note_matrix as producer
import vco1_circuit_reference as vco
import voice_union_refine_runner as prior
from voice_matrix_trace import residual

ROOT=vco.ROOT

def main():
    output=ROOT/'evidence/voice_full_note_matrix_roots_validation01.json'
    if output.exists():raise ValueError('preserve precise-root replay')
    path=ROOT/'evidence/voice_full_note_matrix_roots01.json';r=vco.read(path)
    if not r['passed'] or r['helper_sha256']!=r['helper_sha256_after']:raise ValueError('successful root producer required')
    for name,digest in r['helper_sha256'].items():
        if vco.sha(ROOT/name)!=digest:raise ValueError('root analysis helper changed')
    audit_path=ROOT/'evidence/voice_full_note_matrix_validation01.json'
    if vco.sha(audit_path)!=r['audit_sha256'] or vco.sha(ROOT/producer.PROTOCOL)!=r['protocol_sha256']:raise ValueError('root context binding')
    logp=probe.WORK/'trap-on.log'
    if vco.sha(logp)!=r['log_sha256']:raise ValueError('captured root inputs')
    log=logp.read_text(encoding='utf-8');snapshots=matrix.parse(log);details=refine.parse(log);indices=producer.selection(snapshots)
    if prior.canonical(indices)!=prior.canonical(r['selected_indices']) or len(r['analyses'])!=2 or len(r['refinements'])!=2 or r['linear_system_factorizations']!=4:raise ValueError('selected complete pair')
    contexts=[]
    for i,a,c in zip(indices,r['analyses'],r['refinements']):
        s=snapshots[i];n=s['n']
        if any(a[k]!=s[k] for k in ('time_s','h_s','iteration','order','mode','n','nz','diag_gmin')) or len(a['rows'])!=n:raise ValueError('precise-root matrix context')
        with localcontext() as ctx:
            ctx.prec=120;rows=a['rows'];x=[Decimal(row['precise']) for row in rows]
            dense=[[Decimal(0) for _ in range(n)] for _ in range(n)]
            for (j,k),value in s['entries'].items():dense[j][k]=matrix.exact(value)
            b=[matrix.exact(s['nodes'][j]['b']) for j in range(n)]
            residual_values=residual(dense,x,b)
            for j,row in enumerate(rows):
                if row['node']!=s['nodes'][j]['name'] or row['old']!=s['nodes'][j]['old'] or row['precise_residual']!=str(residual_values[j]):raise ValueError('stored 120-digit residual')
                scale=sum((abs(value*x[k]) for k,value in enumerate(dense[j])),abs(b[j]))
                if abs(residual_values[j])>Decimal('1e-95')*max(Decimal(1),scale) or abs(Decimal(row['agreement_80_120']))>Decimal('1e-55')*max(Decimal(1),abs(x[j])):raise ValueError('precise-root gates')
        replay=refine.compare(s,details[i],a)
        if prior.canonical(replay)!=prior.canonical(c):raise ValueError('compiled pairs/final publication replay')
        contexts.append({k:s[k] for k in ('time_s','h_s','iteration','n','nz')})
    passed=all(c['passed'] for c in r['refinements'])
    if passed!=r['compiled_refinement_gate_passed']:raise ValueError('linear refinement decision')
    report=dict(schema='rf-d/full-note-root-validation/v1',passed=True,analysis_sha256=vco.sha(path),contexts=contexts,
        stored_precise_roots=2,residual_digits=120,new_linear_factorizations=0,new_spice_solves=0,new_nonlinear_solves=0,
        inherited_producer_factorizations=4,agreement_80_120_inherited_from_producer=True,compiled_refinement_gate_passed=passed,
        source_sha256={p.relative_to(ROOT).as_posix():vco.sha(p) for p in (Path(__file__),Path(producer.__file__),Path(matrix.__file__),Path(refine.__file__))},
        cause_identified=False,long_note_admitted=False,new_audio=False)
    output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('precise-root residual/pair replay passed; new factorizations: 0',flush=True)

if __name__=='__main__':main()
