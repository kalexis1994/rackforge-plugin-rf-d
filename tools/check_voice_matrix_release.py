"""Matrix regressions plus existing gates; no new SPICE solves in QA."""
import json,re,subprocess,sys,time,wave
from pathlib import Path
import vco1_circuit_reference as vco
from validate_loudness_board4_bank import source_identity
from check_voice_741_row_release import PATTERNS

ROOT=vco.ROOT
BASE='5377da45212c1420769a85ee30ecf4ee82035b85'
DOCS=('README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md',
      'docs/NEWTON_MATRIZ_COMPLETA_PROTOCOLO.md','docs/NEWTON_MATRIZ_COMPLETA_RESULTADOS.md',
      'docs/NEWTON_REFINAMIENTO_LINEAL_PROTOCOLO.md')

def main():
    output=ROOT/'evidence/voice_matrix_tests01.json'
    if output.exists():raise ValueError('preserve QA')
    audit=vco.read(ROOT/'evidence/voice_matrix_observation01.json')
    if not audit['passed'] or audit['coupling_admitted'] or audit['new_solves_during_validation'] or audit['measured_solves']!=4 or audit['missing_selected']:raise ValueError('matrix audit scope')
    for name,digest in audit['analysis_source_sha256'].items():
        if vco.sha(ROOT/name)!=digest:raise ValueError('analysis source changed')
    rounded=vco.read(ROOT/'evidence/voice_matrix_rounding01.json')
    if not rounded['passed'] or rounded['audit_sha256']!=vco.sha(ROOT/'evidence/voice_matrix_observation01.json') or rounded['new_spice_solves'] or rounded['source_sha256']!=rounded['source_sha256_after']:raise ValueError('rounding postprocessing')
    for name,digest in rounded['source_sha256'].items():
        if vco.sha(ROOT/name)!=digest:raise ValueError('rounding helper changed')
    old=vco.read(ROOT/'evidence/voice_741_row_tests02.json')
    originals=set(old['source_sha256'])-{'README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md'}
    for name in sorted(originals):
        if vco.sha(ROOT/name)!=old['source_sha256'][name]:raise ValueError('historical input changed: '+name)
        source_identity(name,vco.sha(ROOT/name),subprocess.check_output(['git','show',BASE+':'+name],cwd=ROOT))
    inputs=originals|set(DOCS)|{'evidence/voice_matrix_observation01.json','evidence/voice_matrix_runs01.json',
        'evidence/voice_matrix_preflight_rejection01.json','evidence/voice_741_row_tests02.json','evidence/voice_matrix_rounding01.json'}
    inputs.update(p.relative_to(ROOT).as_posix() for p in (ROOT/'tools').glob('*voice_matrix*.py'))
    inputs.add('tests/test_voice_matrix.py');before={n:vco.sha(ROOT/n) for n in sorted(inputs)}
    runs=[];count=0
    for pattern in ('test_voice_matrix.py',)+PATTERNS:
        cmd=[sys.executable,'-B','-m','unittest','discover','-s','tests','-p',pattern,'-v'];start=time.perf_counter()
        r=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True)
        runs.append(dict(command=cmd,exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr,wall_s=time.perf_counter()-start))
        if r.returncode or re.search(r'\bskipped=',r.stderr):raise ValueError('regression failed/skipped: '+pattern)
        match=re.search(r'Ran (\d+) tests?',r.stderr)
        if not match:raise ValueError('missing test count')
        count+=int(match[1]);print(pattern,match[1],'passed',flush=True)
    targets=[]
    for name in DOCS:
        p=ROOT/name
        for link in re.findall(r'\]\(([^)]+)\)',p.read_text(encoding='utf-8')):
            if link.startswith(('http:','https:','#')):continue
            target=(p.parent/link.split('#')[0].strip('<>')).resolve()
            if not target.exists() and target!=output:raise ValueError('document target missing')
            targets.append(target)
    audio=old['previous_audio'];official=ROOT/'references-local/ngspice46/runtime/Spice64/bin/ngspice_con.exe'
    if vco.sha(ROOT/audio['path'])!=audio['sha256'] or vco.sha(official)!=old['official_executable_sha256']:raise ValueError('previous audio/official changed')
    with wave.open(str(ROOT/audio['path']),'rb') as w:
        if (w.getnchannels(),w.getsampwidth(),w.getframerate(),w.getnframes())!=(1,2,48000,64800):raise ValueError('previous audio format')
    after={n:vco.sha(ROOT/n) for n in sorted(inputs)}
    if before!=after:raise ValueError('QA inputs changed')
    report=dict(schema='rf-d/newton-matrix-release/v1',passed=True,tests_count=count,runs=runs,source_sha256=before,source_sha256_after=after,
        original_inputs_unchanged=sorted(originals),base_commit=BASE,previous_audio=audio,official_executable_sha256=vco.sha(official),
        local_document_links=len(targets),new_solves_during_qa=0,linear_system_observed=True,
        full_nonlinear_kcl_residual_observed=False,coupling_admitted=False,physical_fidelity=False,real_time=False,new_audio=False)
    output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    if not all(p.exists() for p in targets):raise ValueError('QA self link missing')
    print(count,'regressions; original physical inputs and audio unchanged',flush=True)

if __name__=='__main__':main()
