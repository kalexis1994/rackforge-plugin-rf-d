"""Focused equivalent-row gates with preserved physical inputs and prior audio."""
import json,re,subprocess,sys,time,wave
from pathlib import Path
import vco1_circuit_reference as vco
from validate_loudness_board4_bank import source_identity

ROOT=vco.ROOT
BASE='dbb7c8a899969cd595cc1bfab8904cf3724cc37c'
PATTERNS=('test_voice_741_row.py','test_voice_741_control_gates.py','test_voice_kcl_reduction.py','test_voice_kcl_alias.py','test_voice_kcl_trace.py','test_voice_inductor_trace.py','test_voice_newton_observation.py','test_vco_reset_screens.py','test_voice_circuit*.py')
DOCS=('README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md',
      'docs/741_FILA_REDUCIDA_PROTOCOLO.md','docs/741_FILA_REDUCIDA_RESULTADOS.md','docs/NEWTON_MATRIZ_COMPLETA_PROTOCOLO.md')


def main():
    output=ROOT/'evidence/voice_741_row_tests01.json'
    if output.exists():raise ValueError('preserve prior release test')
    audit=vco.read(ROOT/'evidence/voice_741_row_validation01.json')
    if not audit['passed'] or audit['coupling_admitted'] or audit['new_solves_during_validation'] or audit['measured_solves']!=3 or audit['candidate_admitted_locally'] or audit['decision']!='active positive control gate':
        raise ValueError('observation audit scope')
    for name,digest in audit['analysis_source_sha256'].items():
        if vco.sha(ROOT/name)!=digest:raise ValueError('analysis source changed: '+name)
    official=ROOT/'references-local/ngspice46/runtime/Spice64/bin/ngspice_con.exe'
    if vco.sha(official)!=vco.EXPECTED_EXE_SHA:raise ValueError('official executable changed')
    originals=set(vco.read(ROOT/'evidence/voice_kcl_tests02.json')['source_sha256'])-{'README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md'}
    originals.add('evidence/voice_port_behavioral01.json.gz')
    # The historical audit also includes documentation; only active summaries are updated.
    for name in sorted(originals):
        source_identity(name,vco.sha(ROOT/name),subprocess.check_output(['git','show',BASE+':'+name],cwd=ROOT))
    inputs=set(DOCS)|originals|{'evidence/voice_741_row_validation01.json','evidence/voice_newton_build_rejections01.json',
                             'evidence/voice_newton_build_rejections02.json','evidence/voice_newton_preflight_rejection01.json'}
    inputs.update(p.relative_to(ROOT).as_posix() for p in (ROOT/'tools').glob('*voice_741*.py'))
    inputs.add('evidence/voice_741_row_runs01.json')
    inputs.update(p.relative_to(ROOT).as_posix() for p in (ROOT/'tools').glob('voice_741*.py'))
    inputs.update(p.relative_to(ROOT).as_posix() for pattern in PATTERNS for p in (ROOT/'tests').glob(pattern))
    before={name:vco.sha(ROOT/name) for name in sorted(inputs)};runs=[];count=0
    for pattern in PATTERNS:
        cmd=[sys.executable,'-B','-m','unittest','discover','-s','tests','-p',pattern,'-v'];start=time.perf_counter()
        r=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True)
        runs.append(dict(command=cmd,exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr,wall_s=time.perf_counter()-start))
        if r.returncode or re.search(r'\bskipped=',r.stderr):raise ValueError('required regression failed or skipped: '+pattern)
        match=re.search(r'Ran (\d+) tests?',r.stderr)
        if not match:raise ValueError('missing test count')
        count+=int(match[1]);print(pattern,match[1],'passed',flush=True)
    targets=[]
    for name in DOCS:
        path=ROOT/name
        for link in re.findall(r'\]\(([^)]+)\)',path.read_text(encoding='utf-8')):
            if link.startswith(('http:','https:','#')):continue
            target=(path.parent/link.split('#')[0].strip('<>')).resolve()
            if not target.exists() and target!=output:raise ValueError('document target missing: '+str(target))
            targets.append(target)
    listening=vco.read(ROOT/'evidence/loudness_board4_listening.json')['montage'];audio=ROOT/listening['path']
    if vco.sha(audio)!=listening['sha256']:raise ValueError('previous audio changed')
    with wave.open(str(audio),'rb') as w:
        params=dict(channels=w.getnchannels(),sample_width_bytes=w.getsampwidth(),sample_rate_hz=w.getframerate(),frames=w.getnframes())
    if params!=dict(channels=1,sample_width_bytes=2,sample_rate_hz=48000,frames=64800):raise ValueError('previous audio format')
    after={name:vco.sha(ROOT/name) for name in sorted(inputs)}
    if before!=after:raise ValueError('release inputs changed')
    report=dict(schema='rf-d/741-equivalent-row-release/v1',passed=True,tests_count=count,runs=runs,
                source_sha256=before,source_sha256_after=after,original_inputs_unchanged=sorted(originals),
                base_commit=BASE,git_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
                previous_audio=dict(path=listening['path'],sha256=listening['sha256'],**params),
                official_executable_sha256=vco.sha(official),
                local_document_links=len(targets),new_solves_during_qa=0,new_audio=False,
                numerical_reformulation_measured=True,candidate_admitted_locally=False,
                full_nonlinear_kcl_residual_observed=False,
                coupling_admitted=False,physical_fidelity=False,real_time=False)
    output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    if not all(p.exists() for p in targets):raise ValueError('release self-link missing')
    print(count,'focused regressions; circuit and prior audio unchanged',flush=True)


if __name__=='__main__':main()
