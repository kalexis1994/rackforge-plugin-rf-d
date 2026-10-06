"""Refinement QA preserves prior inputs/audio; no new SPICE solves in release."""
import json,re,subprocess,sys,time,wave
from pathlib import Path
import vco1_circuit_reference as vco
from validate_loudness_board4_bank import source_identity
from check_voice_741_row_release import PATTERNS

ROOT=vco.ROOT
BASE='457b979b0e7d9862599a69bfbee2e898127ab5d0'
DOCS=('README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md',
    'docs/NEWTON_REFINAMIENTO_LINEAL_PROTOCOLO.md','docs/NEWTON_REFINAMIENTO_IMPLEMENTACION.md',
    'docs/NEWTON_REFINAMIENTO_RESULTADOS.md','docs/VOZ_REFINAMIENTO_UNION_PROTOCOLO.md')

def main():
    output=ROOT/'evidence/voice_refine_tests01.json'
    if output.exists():raise ValueError('preserve QA')
    audit=vco.read(ROOT/'evidence/voice_refine_validation01.json')
    if not audit['passed'] or not audit['candidate_admitted_locally'] or not audit['active_control']['passed'] or audit['new_solves_during_validation'] or audit['measured_solves']!=5 or audit['coupling_admitted']:raise ValueError('local refinement audit scope')
    for name,digest in audit['analysis_source_sha256'].items():
        if vco.sha(ROOT/name)!=digest:raise ValueError('analysis helper changed')
    old=vco.read(ROOT/'evidence/voice_matrix_tests01.json');originals=set(old['source_sha256'])-{'README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md'}
    for name in sorted(originals):
        if vco.sha(ROOT/name)!=old['source_sha256'][name]:raise ValueError('historical input changed: '+name)
        source_identity(name,vco.sha(ROOT/name),subprocess.check_output(['git','show',BASE+':'+name],cwd=ROOT))
    inputs=originals|set(DOCS)|{'evidence/voice_matrix_tests01.json','evidence/voice_refine_validation01.json',
        'evidence/voice_refine_runs01.json','evidence/voice_refine_arithmetic02.json','evidence/voice_refine_arithmetic_rejection01.json','tests/test_voice_refine.py'}
    inputs.update(p.relative_to(ROOT).as_posix() for p in (ROOT/'tools').glob('*voice_refine*') if p.is_file())
    before={n:vco.sha(ROOT/n) for n in sorted(inputs)};runs=[];count=0
    for pattern in ('test_voice_refine.py','test_voice_matrix.py')+PATTERNS:
        cmd=[sys.executable,'-B','-m','unittest','discover','-s','tests','-p',pattern,'-v'];start=time.perf_counter()
        r=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True)
        runs.append(dict(command=cmd,exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr,wall_s=time.perf_counter()-start))
        if r.returncode or re.search(r'\bskipped=',r.stderr):raise ValueError('regression failed/skipped: '+pattern)
        match=re.search(r'Ran (\d+) tests?',r.stderr)
        if not match:raise ValueError('test count missing')
        count+=int(match[1]);print(pattern,match[1],'passed',flush=True)
    targets=[]
    for name in DOCS:
        path=ROOT/name
        for link in re.findall(r'\]\(([^)]+)\)',path.read_text(encoding='utf-8')):
            if link.startswith(('http:','https:','#')):continue
            target=(path.parent/link.split('#')[0].strip('<>')).resolve()
            if not target.exists() and target!=output:raise ValueError('missing document target')
            targets.append(target)
    audio=old['previous_audio'];official=ROOT/'references-local/ngspice46/runtime/Spice64/bin/ngspice_con.exe'
    if vco.sha(ROOT/audio['path'])!=audio['sha256'] or vco.sha(official)!=old['official_executable_sha256']:raise ValueError('prior audio/official changed')
    with wave.open(str(ROOT/audio['path']),'rb') as w:
        if (w.getnchannels(),w.getsampwidth(),w.getframerate(),w.getnframes())!=(1,2,48000,64800):raise ValueError('prior audio format')
    after={n:vco.sha(ROOT/n) for n in sorted(inputs)}
    if before!=after:raise ValueError('QA input changed')
    report=dict(schema='rf-d/linear-refine-release/v1',passed=True,tests_count=count,runs=runs,source_sha256=before,source_sha256_after=after,
        original_inputs_unchanged=sorted(originals),base_commit=BASE,previous_audio=audio,official_executable_sha256=vco.sha(official),
        compiled_arithmetic_cases=280,compiled_arithmetic_cases_inherited=True,new_compiler_runs_during_qa=0,
        new_spice_solves_during_qa=0,local_document_links=len(targets),candidate_admitted_locally=True,
        coupling_admitted=False,explains_official_failure=False,physical_fidelity=False,real_time=False,new_audio=False)
    output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    if not all(p.exists() for p in targets):raise ValueError('QA self-link missing')
    print(count,'regressions; minimal VCO refined locally; physical inputs and audio unchanged',flush=True)

if __name__=='__main__':main()
