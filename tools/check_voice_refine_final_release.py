"""Pin LF for measured C/header bytes while inheriting unchanged successful tests."""
import json,subprocess
from pathlib import Path
import vco1_circuit_reference as vco
from validate_loudness_board4_bank import source_identity

ROOT=vco.ROOT;BASE='35ac77e554f76080c8f875f8c6e2d17b294aaad6'

def main():
    output=ROOT/'evidence/voice_refine_tests02.json'
    if output.exists():raise ValueError('preserve final QA')
    path=ROOT/'evidence/voice_refine_tests01.json';old=vco.read(path)
    if not old['passed'] or old['tests_count']!=70 or old['source_sha256']!=old['source_sha256_after']:raise ValueError('successful QA identity')
    changed='docs/NEWTON_REFINAMIENTO_RESULTADOS.md'
    for name,digest in old['source_sha256'].items():
        blob=subprocess.check_output(['git','show',BASE+':'+name],cwd=ROOT);source_identity(name,digest,blob)
        if name!=changed and vco.sha(ROOT/name)!=digest:raise ValueError('tested source changed')
        if name==changed and (ROOT/name).read_bytes()!=blob.replace(b'voice_refine_tests01.json',b'voice_refine_tests02.json',1):raise ValueError('only final QA link may change')
    original=subprocess.check_output(['git','show',BASE+':.gitattributes'],cwd=ROOT)
    expected=original+b'\n# Measured arithmetic templates must materialize with their recorded bytes.\ntools/voice_refine*.c text eol=lf\ntools/voice_refine*.h text eol=lf\n'
    if (ROOT/'.gitattributes').read_bytes()!=expected:raise ValueError('only declared LF rules')
    native=[n for n in old['source_sha256'] if n.startswith('tools/voice_refine') and n.endswith(('.c','.h'))]
    attributes={}
    for name in native:
        attr=subprocess.check_output(['git','check-attr','text','eol','--',name],cwd=ROOT,text=True)
        if ': text: set' not in attr or ': eol: lf' not in attr:raise ValueError('native LF not pinned')
        attributes[name]=attr.splitlines()
    if vco.sha(ROOT/old['previous_audio']['path'])!=old['previous_audio']['sha256'] or vco.sha(ROOT/'references-local/ngspice46/runtime/Spice64/bin/ngspice_con.exe')!=old['official_executable_sha256']:raise ValueError('audio/official changed')
    inputs=set(old['source_sha256'])|{'.gitattributes',Path(__file__).relative_to(ROOT).as_posix(),'evidence/voice_refine_tests01.json'}
    before={n:vco.sha(ROOT/n) for n in sorted(inputs)}
    report=dict(schema='rf-d/linear-refine-final-release/v1',passed=True,tests_count=70,runs=old['runs'],
        source_sha256=before,source_sha256_after={n:vco.sha(ROOT/n) for n in sorted(inputs)},
        inherited_qa_sha256=vco.sha(path),inherited_base_commit=BASE,new_tests_during_final_qa=0,new_spice_solves_during_qa=0,
        native_materialization_attributes=attributes,changed_document=changed,
        previous_audio=old['previous_audio'],official_executable_sha256=old['official_executable_sha256'],
        candidate_admitted_locally=True,coupling_admitted=False,physical_fidelity=False,real_time=False,new_audio=False)
    output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('70 successful tests inherited; measured C/header checkout bytes pinned to LF',flush=True)

if __name__=='__main__':main()
