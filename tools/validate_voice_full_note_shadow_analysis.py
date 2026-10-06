"""Replay the stored scratch analysis without SPICE or new factorization."""
import json
from pathlib import Path
import analyze_voice_full_note_shadow as producer
import voice_union_refine_runner as prior
import vco1_circuit_reference as vco

def main():
    root=vco.ROOT;output=root/'evidence/voice_full_note_shadow_analysis_validation01.json'
    if output.exists():raise ValueError('preserve shadow replay')
    path=root/'evidence/voice_full_note_shadow_analysis01.json';r=vco.read(path)
    if not r['passed'] or r['helper_sha256']!=r['helper_sha256_after']:raise ValueError('successful producer required')
    for n,h in r['helper_sha256'].items():
        if vco.sha(root/n)!=h:raise ValueError('producer input changed')
    replay=producer.evaluate()
    if any(prior.canonical(r[k])!=prior.canonical(v) for k,v in replay.items()):raise ValueError('scratch residual/update/root gate replay')
    report=dict(schema='rf-d/full-note-shadow-analysis-validation/v1',passed=True,analysis_sha256=vco.sha(path),
        six_correction_gate_passed=r['six_correction_gate_passed'],new_spice_solves=0,new_linear_factorizations=0,
        new_nonlinear_solves=0,active_six_variant_measured=False,published_corrections=3,
        source_sha256={p.relative_to(root).as_posix():vco.sha(p) for p in (Path(__file__),Path(producer.__file__))},
        long_note_admitted=False,cause_identified=False,new_audio=False)
    output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('shadow pair/root replay passed',flush=True)

if __name__=='__main__':main()
