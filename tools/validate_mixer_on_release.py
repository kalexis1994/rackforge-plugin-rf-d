"""Publish an independent passive native block while inheriting frozen voice evidence."""
import json,re,subprocess
from pathlib import Path
import mixer_on_native_vectors as oracle
from validate_mixer_on_native import native_source_identity

ROOT=oracle.ROOT;OUTPUT=ROOT/'evidence/voice_mixer_on_native_tests01.json'
MUTABLE=('.gitattributes','README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md')

def hashes(names):return {n:oracle.sha(ROOT/n) for n in names}

def main():
    if OUTPUT.exists():raise ValueError('preserve mixer release QA')
    base='9042af90d55b84113eb69e2cb4e9f6982b8b8e9e'
    if subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()!=base:raise ValueError('release base')
    previousp=ROOT/'evidence/voice_serial_tests01.json';previous=json.loads(previousp.read_text(encoding='utf-8'))
    if not previous['passed'] or previous['tests_count']!=165:raise ValueError('inherited voice QA')
    unchanged=[]
    for n,h in previous['source_sha256'].items():
        native_source_identity(n,h,subprocess.check_output(['git','show',base+':'+n],cwd=ROOT))
        if n not in MUTABLE:
            if oracle.sha(ROOT/n)!=h:raise ValueError('inherited input changed '+n)
            unchanged.append(n)
    old=subprocess.check_output(['git','show',base+':.gitattributes'],cwd=ROOT)
    expected=(old+b'\n# Exact native mixer source bytes across Windows checkouts.\n'
        b'/crates/rf-d-circuit/src/lib.rs text eol=lf\n/crates/rf-d-circuit/src/mixer_on.rs text eol=lf\n'
        b'/crates/rf-d-circuit/tests/mixer_on.rs text eol=lf\n/crates/rf-d-circuit/tests/mixer_on_no_alloc.rs text eol=lf\n')
    if (ROOT/'.gitattributes').read_bytes()!=expected:raise ValueError('only declared Rust LF rules added')
    staged=subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=ROOT).decode().split('\0')
    names=sorted(set(previous['source_sha256'])|{'evidence/voice_serial_tests01.json'}|
        {n for n in staged if n and ROOT/n!=OUTPUT}|{p.relative_to(ROOT).as_posix() for p in (ROOT/'crates/rf-d-circuit/src').glob('*.rs')})
    before=hashes(names)
    for n,h in before.items():native_source_identity(n,h,subprocess.check_output(['git','show',':'+n],cwd=ROOT))
    auditp=ROOT/'evidence/voice_mixer_on_native_validation01.json';audit=json.loads(auditp.read_text(encoding='utf-8'))
    attemptp=ROOT/'evidence/voice_mixer_on_native_attempt01.json';attempt=json.loads(attemptp.read_text(encoding='utf-8'))
    if not audit['passed'] or not audit['admitted_static_on_ports'] or audit['native_attempt_sha256']!=oracle.sha(attemptp) or audit['native_test_count']!=8:
        raise ValueError('audited eight native tests')
    for scope in (attempt['source_sha256'],audit['analysis_source_sha256']):
        for n,h in scope.items():
            if oracle.sha(ROOT/n)!=h:raise ValueError('native measured source changed')
    failures=[]
    for index in (1,2):
        p=ROOT/f'evidence/voice_mixer_on_audit_rejection{index:02d}.json';r=json.loads(p.read_text(encoding='utf-8'))
        if r['exit_code']!=1 or r['numeric_gates_changed']:raise ValueError('preserved failed identity audit')
        if index==1:
            import hashlib
            if hashlib.sha256(r['source_text'].encode()).hexdigest()!=r['source_sha256']:raise ValueError('failed source snapshot')
        else:
            if r['source_sha256']!=r['source_sha256_after'] or 'ValueError: other native circuit source changed:' not in r['stderr']:raise ValueError('unchanged failure replay')
        failures.append(dict(path=p.relative_to(ROOT).as_posix(),sha256=oracle.sha(p)))
    private=dict(previous['private_input_sha256'],**audit['private_binary_sha256'])
    for n,h in private.items():
        if oracle.sha(ROOT/n)!=h:raise ValueError('private input changed')
    if oracle.sha(ROOT/previous['previous_audio']['path'])!=previous['previous_audio']['sha256'] or oracle.sha(ROOT/'references-local/ngspice46/runtime/Spice64/bin/ngspice_con.exe')!=previous['official_executable_sha256']:raise ValueError('historical audio/executable changed')
    links=set()
    for n in names:
        if not n.endswith('.md'):continue
        path=ROOT/n
        for link in re.findall(r'\]\(([^)]+)\)',path.read_text(encoding='utf-8')):
            if link.startswith(('https:','http:','#')):continue
            p=(path.parent/link.split('#')[0].strip('<>')).resolve()
            if not p.exists() and p!=OUTPUT:raise ValueError('missing document link '+str(p))
            links.add(str(p))
    after=hashes(names)
    if before!=after:raise ValueError('release input change')
    OUTPUT.write_text(json.dumps(dict(schema='rf-d/mixer-on-native-release/v1',passed=True,tests_count=173,
        new_tests_count=8,inherited_tests_count=165,inherited_qa=dict(path=previousp.relative_to(ROOT).as_posix(),sha256=oracle.sha(previousp),base_commit=base,executed_again=False),
        unchanged_inherited_inputs=unchanged,declared_input_updates=list(MUTABLE),source_sha256=before,source_sha256_after=after,
        private_input_sha256=private,private_input_sha256_after=hashes(private),preserved_identity_rejections=failures,
        native_audit_sha256=oracle.sha(auditp),native_case_count=279,zero_heap_evaluations=10000,
        runs=[{k:attempt[k] for k in ('command','exit_code','stdout','stderr','wall_s')}],
        admitted_static_on_ports=True,full_voice_integrated=False,previous_audio=previous['previous_audio'],official_executable_sha256=previous['official_executable_sha256'],
        local_document_links=len(links),new_spice_solves=0,new_compiler_runs_during_qa=0,new_audio=False,physical_fidelity=False,real_time=False),indent=2)+'\n',encoding='utf-8',newline='\n')
    print('mixer QA: 8 executed + 165 inherited = 173; sources:',len(names),flush=True)

if __name__=='__main__':main()
