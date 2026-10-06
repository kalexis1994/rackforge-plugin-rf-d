"""Focused 48 regressions, immutable diagnosis and prior audio identity."""
import json,re,subprocess,sys,time,wave
from pathlib import Path
import check_loudness_voice_release as previous
import vco1_circuit_reference as vco

ROOT=vco.ROOT
DOCS=previous.DOCS+('docs/JFET_RESET_REPRESENTACION_PROTOCOLO.md',
                   'docs/VCO_REGULARIZACION_PROTOCOLO.md','docs/RESET_VCO_AISLADO_RESULTADOS.md')
PATTERNS=previous.PATTERNS+('test_vco_reset_screens.py',)


def main():
    output=ROOT/'evidence/voice_reset_tests.json'
    if output.exists():raise ValueError('preserve prior regressions')
    inputs=set(DOCS)
    for pattern in PATTERNS:inputs.update(path.relative_to(ROOT).as_posix() for path in (ROOT/'tests').glob(pattern))
    for pattern in ('voice_jfet*','voice_vco_rshunt*','voice_reset*','validate_vco_reset_screens.py',
                    'check_vco_reset_release.py','check_loudness_voice_release.py','voice_port*',
                    'loudness_voice*','vco1_circuit_reference.py','voice_circuit_reference.py',
                    'loudness_board4_circuit.py','filter_vca_circuit_reference.py'):
        inputs.update(path.relative_to(ROOT).as_posix() for path in (ROOT/'tools').glob(pattern) if path.is_file())
    for pattern in ('voice_jfet_decomposed*','voice_vco_rshunt*','voice_reset*'):
        inputs.update(path.relative_to(ROOT).as_posix() for path in (ROOT/'evidence').glob(pattern) if path.is_file())
    audit=vco.read(ROOT/'evidence/voice_reset_representation_validation02.json')
    if not audit['passed'] or audit['new_solves'] or len(audit['records'])!=5 or len(audit['observation_receipts'])!=2 or audit['coupling_admitted'] or audit['regularizer_selected'] is not None:
        raise ValueError('audited rejected scope')
    if audit['auditor_sha256']!=vco.sha(ROOT/'tools/validate_vco_reset_screens.py'):raise ValueError('auditor version')
    inputs.update(audit['original_inputs_unchanged'])
    inputs.add('evidence/loudness_board4_listening.json')
    before={name:vco.sha(ROOT/name) for name in sorted(inputs)};runs=[];count=0
    for pattern in PATTERNS:
        command=[sys.executable,'-B','-m','unittest','discover','-s','tests','-p',pattern,'-v']
        start=time.perf_counter();r=subprocess.run(command,cwd=ROOT,capture_output=True,text=True)
        runs.append(dict(command=command,exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr,wall_s=time.perf_counter()-start))
        if r.returncode or re.search(r'\bskipped=',r.stderr):raise ValueError('required regression failed or skipped: '+pattern)
        found=re.search(r'Ran (\d+) tests?',r.stderr)
        if found is None:raise ValueError('test count missing')
        count+=int(found[1]);print(pattern,found[1],'passed',flush=True)
    if count!=48:raise ValueError('expected forty-eight focused regressions')
    targets=[]
    for name in DOCS:
        path=ROOT/name
        for link in re.findall(r'\]\(([^)]+)\)',path.read_text(encoding='utf-8')):
            if link.startswith(('http:','https:','#')):continue
            target=(path.parent/link.split('#')[0].strip('<>')).resolve()
            if not target.exists() and target!=output:raise ValueError('missing document target: '+name+' -> '+link)
            targets.append(target)
    listening=vco.read(ROOT/'evidence/loudness_board4_listening.json')['montage'];audio=ROOT/listening['path']
    if vco.sha(audio)!=listening['sha256']:raise ValueError('previous audible artifact changed')
    with wave.open(str(audio),'rb') as w:
        audio_params=dict(channels=w.getnchannels(),sample_width_bytes=w.getsampwidth(),sample_rate_hz=w.getframerate(),frames=w.getnframes())
    if audio_params!=dict(channels=1,sample_width_bytes=2,sample_rate_hz=48000,frames=64800):raise ValueError('previous audio format')
    after={name:vco.sha(ROOT/name) for name in sorted(inputs)}
    if before!=after:raise ValueError('sources changed during QA')
    report=dict(schema='rf-d/reset-release-tests/v1',passed=True,tests_count=count,runs=runs,
                git_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
                source_sha256=before,source_after_sha256=after,sources_unchanged=True,
                audited_representation_regularization_receipts=5,audited_observation_receipts=2,
                new_solves_during_qa=0,measured_solves_in_block=7,local_document_links=len(targets),
                previous_audio=dict(path=listening['path'],sha256=listening['sha256'],**audio_params),
                new_audio=False,coupling_admitted=False,physical_fidelity=False,real_time=False)
    output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    if not all(target.exists() for target in targets):raise ValueError('published receipt link missing')
    print(count,'regressions passed; observed state replay admitted, coupling remains rejected',flush=True)


if __name__=='__main__':main()
