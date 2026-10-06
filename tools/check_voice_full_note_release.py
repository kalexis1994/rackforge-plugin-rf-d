"""Release QA: new regressions and explicitly inherited, unchanged old inputs."""
import json,re,subprocess,sys,time,wave
from pathlib import Path
import vco1_circuit_reference as vco
from validate_loudness_board4_bank import source_identity

ROOT=vco.ROOT;BASE='b11cc160671cd8fd28d883158e3e2a055efa241a'
SUMMARIES={'README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md'}
DOCS=SUMMARIES|{p.relative_to(ROOT).as_posix() for p in (ROOT/'docs').glob('VOZ_NOTA_LARGA*')}
PATTERNS=('test_voice_full_note.py','test_voice_full_note_prefix.py','test_voice_full_note_matrix.py','test_voice_full_note_shadow.py')

def same(path,digest):
    if vco.sha(ROOT/path)!=digest:raise ValueError('input identity: '+path)

def main():
    output=ROOT/'evidence/voice_full_note_tests01.json'
    if output.exists():raise ValueError('preserve release QA')
    oldpath='evidence/voice_union_refine_tests01.json';old=vco.read(ROOT/oldpath)
    if not old['passed'] or old['tests_count']!=111:raise ValueError('previous regressions')
    originals=set(old['source_sha256'])-SUMMARIES
    for n in sorted(originals):
        same(n,old['source_sha256'][n])
        source_identity(n,old['source_sha256'][n],subprocess.check_output(['git','show',BASE+':'+n],cwd=ROOT))
    bank=vco.read(ROOT/'evidence/voice_full_note_runs01.json')
    audit=vco.read(ROOT/'evidence/voice_full_note_validation01.json')
    matrix=vco.read(ROOT/'evidence/voice_full_note_matrix_validation01.json')
    roots=vco.read(ROOT/'evidence/voice_full_note_matrix_roots01.json')
    root_audit=vco.read(ROOT/'evidence/voice_full_note_matrix_roots_validation01.json')
    diagnostic=vco.read(ROOT/'evidence/voice_full_note_diagnostic01.json')
    shadow=vco.read(ROOT/'evidence/voice_full_note_shadow_validation01.json')
    shadow_analysis=vco.read(ROOT/'evidence/voice_full_note_shadow_analysis01.json')
    shadow_replay=vco.read(ROOT/'evidence/voice_full_note_shadow_analysis_validation01.json')
    for a in (audit,matrix,roots,root_audit,diagnostic,shadow,shadow_analysis,shadow_replay):
        if not a['passed']:raise ValueError('required audit failed')
        for flag in ('new_audio','physical_fidelity','real_time','cause_identified'):
            if a.get(flag,False):raise ValueError('scope overclaim: '+flag)
    same('evidence/voice_full_note_runs01.json',audit['bank_sha256'])
    same('evidence/voice_full_note_matrix_runs01.json',matrix['bank_sha256'])
    same('evidence/voice_full_note_matrix_roots01.json',root_audit['analysis_sha256'])
    same('evidence/voice_full_note_matrix_validation01.json',roots['audit_sha256'])
    same('evidence/voice_full_note_runs01.json',diagnostic['bank_sha256'])
    same('evidence/voice_full_note_validation01.json',diagnostic['audit_sha256'])
    same('evidence/voice_full_note_shadow_runs02.json',shadow['bank_sha256'])
    same('evidence/voice_full_note_shadow_analysis01.json',shadow_replay['analysis_sha256'])
    same('evidence/voice_full_note_shadow_validation01.json',shadow_analysis['shadow_audit_sha256'])
    same('evidence/voice_full_note_matrix_roots01.json',shadow_analysis['inherited_roots_sha256'])
    same('evidence/voice_full_note_matrix_roots_validation01.json',shadow_analysis['inherited_root_audit_sha256'])
    if shadow['measured_solves']!=2 or shadow_analysis['published_corrections']!=3 or shadow_analysis['active_six_variant_measured']:raise ValueError('scratch scope')
    if shadow_analysis['six_correction_gate_passed']!=shadow_replay['six_correction_gate_passed']:raise ValueError('scratch decision')
    if len(bank['records'])!=4 or audit['measured_solves']!=4 or matrix['measured_solves']!=2:raise ValueError('run scope')
    if bank['decision']=='measurements pending' or bank['long_note_admitted_locally']!=audit['long_note_admitted_locally']:raise ValueError('unfinished bank')
    if not matrix['observer_admitted_locally'] or roots['compiled_refinement_gate_passed']!=root_audit['compiled_refinement_gate_passed']:raise ValueError('matrix gate scope')
    inputs=originals|DOCS|{oldpath,Path(__file__).relative_to(ROOT).as_posix()}
    inputs.update(p.relative_to(ROOT).as_posix() for p in (ROOT/'tools').glob('*voice_full_note*') if p.is_file())
    inputs.update(p.relative_to(ROOT).as_posix() for p in (ROOT/'evidence').glob('voice_full_note*.json') if p!=output)
    inputs.update(p.relative_to(ROOT).as_posix() for pattern in PATTERNS for p in (ROOT/'tests').glob(pattern))
    for report,key in ((audit,'analysis_source_sha256'),(matrix,'analysis_source_sha256'),(root_audit,'source_sha256'),(diagnostic,'diagnostic_source_sha256'),(roots,'helper_sha256'),(shadow,'analysis_source_sha256'),(shadow_analysis,'helper_sha256'),(shadow_replay,'source_sha256')):
        for n,h in report[key].items():same(n,h);inputs.add(n)
    private_inputs=set(old['private_input_sha256'])
    for n,h in old['private_input_sha256'].items():same(n,h)
    failed=vco.read(ROOT/'evidence/voice_full_note_shadow_regression_attempt01.json')
    same(failed['preserved_source_path'],failed['failed_source_sha256'])
    import hashlib
    if hashlib.sha256(failed['failed_source_text'].encode()).hexdigest()!=failed['failed_source_sha256']:raise ValueError('failed fixture archive')
    private_inputs.add(failed['preserved_source_path'])
    for r in bank['records'].values():
        for n,h in r['current_source_sha256'].items():
            same(n,h);(private_inputs if n.startswith('references-local/') else inputs).add(n)
    before={n:vco.sha(ROOT/n) for n in sorted(inputs)}
    private_before={n:vco.sha(ROOT/n) for n in sorted(private_inputs)}
    runs=[];count=0
    for pattern in PATTERNS:
        command=[sys.executable,'-B','-m','unittest','discover','-s','tests','-p',pattern,'-v'];start=time.perf_counter()
        r=subprocess.run(command,cwd=ROOT,capture_output=True,text=True)
        runs.append(dict(command=command,exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr,wall_s=time.perf_counter()-start))
        if r.returncode or re.search(r'\bskipped=',r.stderr):raise ValueError('regression failed/skipped: '+pattern)
        match=re.search(r'Ran (\d+) tests?',r.stderr)
        if not match:raise ValueError('test count missing')
        count+=int(match[1]);print(pattern,match[1],'passed',flush=True)
    if count!=22:raise ValueError('new regression count')
    targets=[]
    for n in DOCS:
        p=ROOT/n
        content=p.read_text(encoding='utf-8')
        if 'FINAL_COVERAGE_TABLE' in content:raise ValueError('unfinished coverage table')
        for link in re.findall(r'\]\(([^)]+)\)',content):
            if link.startswith(('https:','http:','#')):continue
            target=(p.parent/link.split('#')[0].strip('<>')).resolve()
            if not target.exists() and target!=output:raise ValueError('missing document target: '+n+' -> '+link)
            targets.append(target)
    audio=old['previous_audio'];official=ROOT/'references-local/ngspice46/runtime/Spice64/bin/ngspice_con.exe'
    same(audio['path'],audio['sha256'])
    if vco.sha(official)!=old['official_executable_sha256']:raise ValueError('official executable identity')
    with wave.open(str(ROOT/audio['path']),'rb') as w:
        if (w.getnchannels(),w.getsampwidth(),w.getframerate(),w.getnframes())!=(1,2,48000,64800):raise ValueError('previous audio format')
    after={n:vco.sha(ROOT/n) for n in sorted(inputs)}
    private_after={n:vco.sha(ROOT/n) for n in sorted(private_inputs)}
    if before!=after or private_before!=private_after:raise ValueError('QA inputs changed')
    report=dict(schema='rf-d/full-note-release/v1',passed=True,tests_count=count+111,new_tests_count=count,inherited_tests_count=111,
        inherited_qa=dict(path=oldpath,sha256=vco.sha(ROOT/oldpath),base_commit=BASE,executed_again=False),runs=runs,
        original_inputs_unchanged=sorted(originals),historical_summary_exceptions=sorted(SUMMARIES),
        source_sha256=before,source_sha256_after=after,private_input_sha256=private_before,private_input_sha256_after=private_after,
        previous_audio=audio,official_executable_sha256=vco.sha(official),local_document_links=len(targets),
        measured_spice_solves=8,producer_linear_factorizations=4,new_spice_solves_during_qa=0,new_compiler_runs_during_qa=0,
        long_note_admitted_locally=audit['long_note_admitted_locally'],observer_admitted_locally=True,
        compiled_refinement_gate_passed=roots['compiled_refinement_gate_passed'],decision=bank['decision'],
        six_scratch_correction_gate_passed=shadow_analysis['six_correction_gate_passed'],active_six_variant_measured=False,
        physical_fidelity=False,real_time=False,cause_identified=False,new_audio=False)
    output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    if not all(p.exists() for p in targets):raise ValueError('self-link missing')
    print('22 executed + 111 inherited; long-note admission:',report['long_note_admitted_locally'],flush=True)

if __name__=='__main__':main()
