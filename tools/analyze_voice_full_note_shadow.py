"""Six scratch corrections versus the existing audited roots, no new LU."""
import json
from pathlib import Path
from decimal import Decimal
import voice_full_note_shadow_trace as trace
import voice_full_note_shadow_probe_retry as probe
import voice_full_note_matrix_trace as matrix
import analyze_voice_full_note_matrix as selected
import voice_union_refine_runner as prior
import vco1_circuit_reference as vco

ROOT=vco.ROOT

def evaluate():
    rootp=ROOT/'evidence/voice_full_note_matrix_roots01.json';roots=vco.read(rootp)
    rp=ROOT/'evidence/voice_full_note_matrix_roots_validation01.json';ra=vco.read(rp)
    ap=ROOT/'evidence/voice_full_note_shadow_validation01.json';audit=vco.read(ap)
    bankp=ROOT/'evidence/voice_full_note_shadow_runs02.json';bank=vco.read(bankp)
    if not ra['passed'] or ra['analysis_sha256']!=vco.sha(rootp) or not audit['passed'] or audit['bank_sha256']!=vco.sha(bankp):raise ValueError('audited shadow/root identities')
    for source in (roots['helper_sha256'],ra['source_sha256'],audit['analysis_source_sha256']):
        for n,h in source.items():
            if vco.sha(ROOT/n)!=h:raise ValueError('audited input changed: '+n)
    logp=probe.WORK/'trap-on.log'
    if vco.sha(logp)!=bank['records']['trap-on']['log_sha256']:raise ValueError('shadow log identity')
    text=logp.read_text(encoding='utf-8');snapshots=matrix.parse(text);details=trace.parse(text)
    indices=selected.selection(snapshots)
    if prior.canonical(indices)!=prior.canonical(roots['selected_indices']) or len(details)!=len(snapshots):raise ValueError('last complete pair')
    comparisons=[]
    for i,a in zip(indices,roots['analyses']):
        s=snapshots[i]
        if any(a[k]!=s[k] for k in ('time_s','h_s','iteration','order','mode','n','nz','diag_gmin')):raise ValueError('same precise root context')
        comparisons.append(trace.compare_six(s,details[i],a))
    return dict(selected_indices=indices,comparisons=comparisons,six_correction_gate_passed=all(c['passed'] for c in comparisons),
        scratch_voltage_error_max_v=str(max(Decimal(c['max_voltage_error']) for c in comparisons)),
        published_three_voltage_error_max_v=roots['published_voltage_error_max_v'],
        inherited_roots_sha256=vco.sha(rootp),inherited_root_audit_sha256=vco.sha(rp),
        shadow_audit_sha256=vco.sha(ap),shadow_bank_sha256=vco.sha(bankp),log_sha256=vco.sha(logp))

def main():
    output=ROOT/'evidence/voice_full_note_shadow_analysis01.json'
    if output.exists():raise ValueError('preserve shadow analysis')
    helpers=(Path(__file__),Path(trace.__file__),Path(matrix.__file__),Path(selected.__file__))
    before={p.relative_to(ROOT).as_posix():vco.sha(p) for p in helpers}
    report=dict(schema='rf-d/full-note-shadow-analysis/v1',passed=False,helper_sha256=before,
        new_linear_factorizations=0,inherited_root_factorizations=4,new_spice_solves=0,new_nonlinear_solves=0,
        observed_additional_native_corrections=12,published_corrections=3,active_six_variant_measured=False,
        long_note_admitted=False,cause_identified=False,physical_fidelity=False,real_time=False,new_audio=False)
    try:report.update(evaluate());report['passed']=True
    except Exception as e:report['analysis_error']=str(e)
    report['helper_sha256_after']={p.relative_to(ROOT).as_posix():vco.sha(p) for p in helpers}
    if before!=report['helper_sha256_after']:report['passed']=False;report['source_error']='analysis inputs changed'
    output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('shadow analysis:',report['passed'],'six-correction gate:',report.get('six_correction_gate_passed'),flush=True)

if __name__=='__main__':main()
