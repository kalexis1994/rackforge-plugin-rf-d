"""Final publication checkpoint after a documented count correction, without retesting."""
import hashlib,json,subprocess
from pathlib import Path
from mixer_on_native_vectors import ROOT,sha
from validate_mixer_on_native import native_source_identity

def main():
    output=ROOT/'evidence/voice_mixer_on_native_tests02.json'
    if output.exists():raise ValueError('preserve final mixer publication')
    previousp=ROOT/'evidence/voice_mixer_on_native_tests01.json';previous=json.loads(previousp.read_text(encoding='utf-8'))
    correctionp=ROOT/'evidence/voice_mixer_on_documentation01.json';correction=json.loads(correctionp.read_text(encoding='utf-8'))
    name=correction['path'];old=correction['original_source_text']
    if not previous['passed'] or hashlib.sha256(old.encode()).hexdigest()!=correction['original_sha256'] or previous['source_sha256'][name]!=correction['original_sha256']:
        raise ValueError('preserved publication draft and documentation snapshot')
    expected=old.replace('sus otras\nquince fuentes','sus otras\ntrece fuentes').replace('voice_mixer_on_native_tests01.json','voice_mixer_on_native_tests02.json')
    if (ROOT/name).read_text(encoding='utf-8')!=expected or sha(ROOT/name)!=correction['corrected_sha256']:raise ValueError('only declared documentation repair')
    nativep=ROOT/'evidence/voice_mixer_on_native_validation01.json';native=json.loads(nativep.read_text(encoding='utf-8'))
    if not native['passed'] or len(native['unchanged_native_sources'])!=13 or sha(nativep)!=previous['native_audit_sha256']:raise ValueError('audited source count')
    for n,h in previous['source_sha256'].items():
        if n!=name and sha(ROOT/n)!=h:raise ValueError('non-documentary draft source changed '+n)
    staged=subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=ROOT).decode().split('\0')
    names=sorted(set(previous['source_sha256'])|{previousp.relative_to(ROOT).as_posix(),correctionp.relative_to(ROOT).as_posix()}|{n for n in staged if n and ROOT/n!=output})
    sources={n:sha(ROOT/n) for n in names}
    for n,h in sources.items():native_source_identity(n,h,subprocess.check_output(['git','show',':'+n],cwd=ROOT))
    for n,h in previous['private_input_sha256'].items():
        if sha(ROOT/n)!=h:raise ValueError('preserved private input changed')
    if sha(ROOT/previous['previous_audio']['path'])!=previous['previous_audio']['sha256'] or sha(ROOT/'references-local/ngspice46/runtime/Spice64/bin/ngspice_con.exe')!=previous['official_executable_sha256']:raise ValueError('historical audio or executable changed')
    report=dict(previous)
    report.update(schema='rf-d/mixer-on-native-publication/v1',source_sha256=sources,source_sha256_after={n:sha(ROOT/n) for n in names},
        publication_draft_sha256=sha(previousp),documentation_correction_sha256=sha(correctionp),
        tests_reexecuted_after_documentation_correction=False)
    if report['source_sha256']!=report['source_sha256_after']:raise ValueError('publication sources changed')
    output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('final mixer publication: 173 covered, 8 executed; source inputs:',len(names),flush=True)

if __name__=='__main__':main()
