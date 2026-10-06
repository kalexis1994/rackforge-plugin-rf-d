"""Last complete context pair; exact-float 80/120 roots; no new SPICE run."""
import json
from pathlib import Path
from decimal import Decimal
import voice_full_note_matrix_trace as matrix
import voice_full_note_matrix_probe as probe
import voice_refine_trace as refine
import vco1_circuit_reference as vco

ROOT=vco.ROOT;PROTOCOL='docs/VOZ_NOTA_LARGA_RAICES_PROTOCOLO.md'

def selection(snapshots):
    keys=('time_s','h_s','order','mode');pairs=[]
    for i in range(len(snapshots)-1):
        a,b=snapshots[i:i+2]
        if a['iteration']==100 and b['iteration']==101 and all(a[k]==b[k] for k in keys):pairs.append((i,i+1))
    if not pairs:raise ValueError('last complete 100/101 context pair unavailable')
    return pairs[-1]

def main():
    output=ROOT/'evidence/voice_full_note_matrix_roots01.json'
    if output.exists():raise ValueError('preserve root analysis')
    audit_path=ROOT/'evidence/voice_full_note_matrix_validation01.json';audit=vco.read(audit_path)
    if not audit['passed'] or not audit['observer_admitted_locally'] or audit['precise_roots_computed']:raise ValueError('exact captured-source audit required')
    helpers=[Path(__file__),Path(matrix.__file__),ROOT/'tools/voice_matrix_trace.py',Path(refine.__file__)]
    before={p.relative_to(ROOT).as_posix():vco.sha(p) for p in helpers}
    log_path=probe.WORK/'trap-on.log';log=log_path.read_text(encoding='utf-8')
    bank=vco.read(ROOT/'evidence/voice_full_note_matrix_runs01.json')
    if vco.sha(log_path)!=bank['records']['trap-on']['log_sha256']:raise ValueError('captured log identity')
    report=dict(schema='rf-d/full-note-matrix-roots/v1',passed=False,analyses=[],refinements=[],
        audit_sha256=vco.sha(audit_path),log_sha256=vco.sha(log_path),protocol_sha256=vco.sha(ROOT/PROTOCOL),
        helper_sha256=before,new_spice_solves=0,new_nonlinear_solves=0,new_native_corrections=0,
        cause_identified=False,long_note_admitted=False,new_audio=False)
    try:
        snapshots=matrix.parse(log);details=refine.parse(log);indices=selection(snapshots)
        report.update(selected_indices=indices,captured_systems=len(snapshots),capture_limit_reached=audit['observation']['capture_limit_reached'])
        for i in indices:
            s=snapshots[i];analysis=matrix.analyze(s);comparison=refine.compare(s,details[i],analysis)
            report['analyses'].append(analysis);report['refinements'].append(comparison)
        report['linear_system_factorizations']=4
        report['compiled_refinement_gate_passed']=all(c['passed'] for c in report['refinements'])
        report['original_voltage_error_max_v']=str(max(abs(Decimal(r['original_error'])) for c in report['refinements'] for r in c['rows'] if r['unknown_unit']=='V'))
        report['published_voltage_error_max_v']=str(max(Decimal(c['max_voltage_error']) for c in report['refinements']))
        report['passed']=True
    except Exception as e:report['analysis_error']=str(e)
    finally:
        report['helper_sha256_after']={p.relative_to(ROOT).as_posix():vco.sha(p) for p in helpers}
        if before!=report['helper_sha256_after']:report['passed']=False;report['source_error']='analysis helper changed'
        output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('captured-root analysis:',report['passed'],'refinement gate:',report.get('compiled_refinement_gate_passed'),flush=True)

if __name__=='__main__':main()
