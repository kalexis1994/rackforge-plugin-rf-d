"""Release receipt: seven new regressions, unchanged inherited inputs, staged bytes."""
import json,re,subprocess,sys,time,wave
from pathlib import Path
import vco1_circuit_reference as vco
import voice_six_runner as runner
import validate_voice_six_build as compiled
from validate_loudness_board4_bank import source_identity

ROOT=vco.ROOT
BASE='f3b2ce13d58037759be1dce6ff04b24de635464d'
PRIOR='evidence/voice_full_note_tests01.json'
SUMMARY={'README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md'}

def git_bytes(ref,name):return subprocess.check_output(['git','show',ref+':'+name],cwd=ROOT)

def main():
    output=ROOT/'evidence/voice_six_tests01.json'
    if output.exists():raise ValueError('preserve release receipt')
    previous=vco.read(ROOT/PRIOR)
    if not previous['passed'] or previous['tests_count']!=133:raise ValueError('inherited regression scope')
    source_identity(PRIOR,vco.sha(ROOT/PRIOR),git_bytes(BASE,PRIOR))
    inherited=[]
    for name,digest in previous['source_sha256'].items():
        source_identity(name,digest,git_bytes(BASE,name))
        if name not in SUMMARY:
            if vco.sha(ROOT/name)!=digest:raise ValueError('inherited input changed: '+name)
            inherited.append(name)
    audit_path=ROOT/'evidence/voice_six_short_validation01.json';audit=vco.read(audit_path)
    if not audit['passed'] or audit['bank_sha256']!=vco.sha(ROOT/'evidence/voice_six_short_runs01.json'):raise ValueError('completed short audit required')
    for name,digest in audit['analysis_source_sha256'].items():
        if vco.sha(ROOT/name)!=digest:raise ValueError('audited helper changed')
    full=compiled.validate();stored=vco.read(ROOT/'evidence/voice_six_build_validation01.json')
    if runner.canonical(full)!=runner.canonical({k:v for k,v in stored.items() if k!='schema'}):raise ValueError('compiled tree changed after short bank')
    preflight_path=ROOT/'evidence/voice_six_long_preflight01.json'
    long_resources=None
    if preflight_path.exists():
        import voice_six_long_preflight
        long_resources=vco.read(preflight_path);replay=voice_six_long_preflight.estimate()
        if any(long_resources[k]!=replay[k] for k in replay if k not in ('available_free_bytes','passed')) or long_resources['passed']!=(long_resources['available_free_bytes']>=long_resources['required_free_bytes']):raise ValueError('long resource replay')
    private=previous['private_input_sha256']
    for name,digest in private.items():
        if vco.sha(ROOT/name)!=digest:raise ValueError('private inherited input changed')
    audio=previous['previous_audio'];audio_path=ROOT/audio['path']
    if vco.sha(audio_path)!=audio['sha256']:raise ValueError('previous audio changed')
    with wave.open(str(audio_path),'rb') as wav:
        actual=(wav.getnchannels(),wav.getsampwidth(),wav.getframerate(),wav.getnframes())
    if actual!=tuple(audio[k] for k in ('channels','sample_width_bytes','sample_rate_hz','frames')):raise ValueError('previous audio shape changed')
    official=ROOT/'references-local/ngspice46/runtime/Spice64/bin/ngspice_con.exe'
    if vco.sha(official)!=previous['official_executable_sha256']:raise ValueError('official executable changed')
    names=set(previous['source_sha256'])
    names.add(PRIOR)
    names.update(subprocess.check_output(['git','diff','--cached','--name-only','--diff-filter=ACM'],cwd=ROOT,text=True).splitlines())
    names.discard(output.relative_to(ROOT).as_posix())
    names={n for n in names if (ROOT/n).is_file()}
    before={n:vco.sha(ROOT/n) for n in sorted(names)}
    for name,digest in before.items():source_identity(name,digest,git_bytes('',name))
    command=[sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_voice_six.py','-v']
    start=time.perf_counter();run=subprocess.run(command,cwd=ROOT,capture_output=True,text=True)
    elapsed=time.perf_counter()-start
    if run.returncode or not re.search(r'Ran 7 tests\b',run.stderr):raise ValueError('seven regressions required: '+run.stderr)
    after={n:vco.sha(ROOT/n) for n in before}
    if before!=after:raise ValueError('release sources changed during QA')
    links=0
    for name in before:
        if not name.endswith('.md'):continue
        for link in re.findall(r'\]\(([^)]+)\)',(ROOT/name).read_text(encoding='utf-8')):
            if link.startswith(('http:','https:','#','app:')):continue
            target=((ROOT/name).parent/link.split('#')[0].strip('<>')).resolve()
            if target!=output.resolve() and not target.exists():raise ValueError('missing local document target: '+name+' -> '+link)
            links+=1
    report=dict(schema='rf-d/active-six-short-release/v1',passed=True,tests_count=140,new_tests_count=7,inherited_tests_count=133,
        inherited_qa=dict(path=PRIOR,sha256=vco.sha(ROOT/PRIOR),base_commit=BASE,executed_again=False),
        unchanged_inherited_inputs=inherited,summary_updates=sorted(SUMMARY),
        runs=[dict(command=command,exit_code=run.returncode,stdout=run.stdout,stderr=run.stderr,wall_s=elapsed)],
        source_sha256=before,source_sha256_after=after,private_input_sha256=private,
        private_input_sha256_after={n:vco.sha(ROOT/n) for n in private},previous_audio=audio,
        official_executable_sha256=vco.sha(official),local_document_links=links,
        measured_spice_solves=audit['new_spice_solves'],inherited_reference_solves=1,new_spice_solves_during_qa=0,new_compiler_runs_during_qa=0,
        short_audit_sha256=vco.sha(audit_path),build_audit_sha256=vco.sha(ROOT/'evidence/voice_six_build_validation01.json'),
        active_six_variant_measured=any(r['process_started'] and r['refinement_enabled'] and r['refinement_activation_confirmed'] for r in audit['records'].values()),joint_admitted_locally=audit['joint_admitted_locally'],decision=audit['decision'],
        long_resource_preflight=long_resources,
        long_note_measured_with_six=False,physical_fidelity=False,real_time=False,cause_identified=False,new_audio=False)
    output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('six release: 7 executed + 133 inherited = 140 covered;',len(before),'staged input hashes;',audit['decision'])

if __name__=='__main__':main()
