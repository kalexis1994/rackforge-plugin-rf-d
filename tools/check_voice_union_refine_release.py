"""Monolithic release QA: replayed admission, focused regressions, fixed inputs."""
import json,re,subprocess,sys,time,wave
from pathlib import Path
import vco1_circuit_reference as vco
from validate_loudness_board4_bank import source_identity
from check_voice_741_row_release import PATTERNS

ROOT=vco.ROOT;BASE='232abddbd4ae0aadb5ede277aa688427b4fb57de'
DOCS=('README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md',
      'docs/VOZ_REFINAMIENTO_UNION_RESULTADOS.md','docs/VOZ_REFINAMIENTO_SIGUIENTE_PROTOCOLO.md')

def main():
    output=ROOT/'evidence/voice_union_refine_tests01.json'
    if output.exists():raise ValueError('preserve release QA')
    audit=vco.read(ROOT/'evidence/voice_union_refine_validation01.json')
    bank=vco.read(ROOT/'evidence/voice_union_refine_runs01.json')
    if not audit['passed'] or audit['new_solves_during_validation'] or audit['bank_sha256']!=vco.sha(ROOT/'evidence/voice_union_refine_runs01.json'):raise ValueError('audit identity')
    if audit['joint_admitted_locally']!=bank['joint_admitted_locally'] or audit['measured_solves']!=bank['measured_solves']:raise ValueError('measured scope')
    if any(audit[k] for k in ('old_port_iteration_admitted','physical_fidelity','real_time','new_audio')):raise ValueError('audit overclaim')
    for name,digest in audit['analysis_source_sha256'].items():
        if vco.sha(ROOT/name)!=digest:raise ValueError('audited helper changed: '+name)
    old=vco.read(ROOT/'evidence/voice_refine_tests02.json')
    originals=set(old['source_sha256'])-{'README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md'}
    for name in sorted(originals):
        if vco.sha(ROOT/name)!=old['source_sha256'][name]:raise ValueError('historical input changed: '+name)
        source_identity(name,vco.sha(ROOT/name),subprocess.check_output(['git','show',BASE+':'+name],cwd=ROOT))
    patterns=('test_voice_union_refine.py','test_voice_refine.py','test_voice_matrix.py')+PATTERNS+(
        'test_filter_vca_circuit*.py','test_loudness_board4*.py','test_voice_port_relaxation.py','test_loudness_voice_circuit.py')
    inputs=originals|set(DOCS)|{'evidence/voice_refine_tests02.json','evidence/voice_union_refine_runs01.json',
        'evidence/voice_union_refine_validation01.json',Path(__file__).relative_to(ROOT).as_posix()}
    inputs.update(p.relative_to(ROOT).as_posix() for pattern in patterns for p in (ROOT/'tests').glob(pattern))
    inputs.update(p.relative_to(ROOT).as_posix() for p in (ROOT/'tools').glob('*voice_union_refine*') if p.is_file())
    inputs.update(bank['wrapper_sha256']);inputs.update(audit['analysis_source_sha256'])
    private_inputs=set()
    for r in bank['records'].values():
        for name in r['current_source_sha256']:
            (private_inputs if name.startswith('references-local/') else inputs).add(name)
    for pattern in ('loudness_board4*','filter_vca_circuit*','voice_port*'):
        inputs.update(p.relative_to(ROOT).as_posix() for p in (ROOT/'tools').glob(pattern) if p.is_file())
    before={n:vco.sha(ROOT/n) for n in sorted(inputs)}
    private_before={n:vco.sha(ROOT/n) for n in sorted(private_inputs)};runs=[];count=0
    for pattern in patterns:
        command=[sys.executable,'-B','-m','unittest','discover','-s','tests','-p',pattern,'-v'];start=time.perf_counter()
        r=subprocess.run(command,cwd=ROOT,capture_output=True,text=True)
        runs.append(dict(command=command,exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr,wall_s=time.perf_counter()-start))
        if r.returncode or re.search(r'\bskipped=',r.stderr):raise ValueError('regression failed/skipped: '+pattern)
        match=re.search(r'Ran (\d+) tests?',r.stderr)
        if not match:raise ValueError('missing test count')
        count+=int(match[1]);print(pattern,match[1],'passed',flush=True)
    targets=[]
    for name in DOCS:
        path=ROOT/name
        for link in re.findall(r'\]\(([^)]+)\)',path.read_text(encoding='utf-8')):
            if link.startswith(('https:','http:','#')):continue
            target=(path.parent/link.split('#')[0].strip('<>')).resolve()
            if not target.exists() and target!=output:raise ValueError('missing link: '+name+' -> '+link)
            targets.append(target)
    audio=old['previous_audio'];official=ROOT/'references-local/ngspice46/runtime/Spice64/bin/ngspice_con.exe'
    if vco.sha(ROOT/audio['path'])!=audio['sha256'] or vco.sha(official)!=old['official_executable_sha256']:raise ValueError('prior audio/official identity')
    with wave.open(str(ROOT/audio['path']),'rb') as w:
        if (w.getnchannels(),w.getsampwidth(),w.getframerate(),w.getnframes())!=(1,2,48000,64800):raise ValueError('prior audio format')
    after={n:vco.sha(ROOT/n) for n in sorted(inputs)}
    private_after={n:vco.sha(ROOT/n) for n in sorted(private_inputs)}
    if before!=after or private_before!=private_after:raise ValueError('QA source changed')
    report=dict(schema='rf-d/union-refine-release/v1',passed=True,tests_count=count,runs=runs,
        source_sha256=before,source_sha256_after=after,private_input_sha256=private_before,private_input_sha256_after=private_after,
        base_commit=BASE,original_inputs_unchanged=sorted(originals),
        previous_audio=audio,official_executable_sha256=vco.sha(official),local_document_links=len(targets),
        measured_solves=bank['measured_solves'],new_spice_solves_during_qa=0,new_compiler_runs_during_qa=0,
        joint_admitted_locally=audit['joint_admitted_locally'],decision=audit['decision'],
        old_port_iteration_admitted=False,physical_fidelity=False,real_time=False,new_audio=False)
    output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    if not all(p.exists() for p in targets):raise ValueError('self-link missing')
    print(count,'regressions; monolithic admission:',audit['joint_admitted_locally'],flush=True)

if __name__=='__main__':main()
