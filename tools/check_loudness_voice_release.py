"""Focused regressions and artifact identities for the coupling block."""
import json,re,subprocess,sys,time,wave
from pathlib import Path
import vco1_circuit_reference as vco

ROOT=vco.ROOT
PATTERNS=('test_voice_circuit*.py','test_filter_vca_circuit*.py','test_loudness_board4*.py',
          'test_voice_port_relaxation.py','test_loudness_voice_circuit.py')
DOCS=('README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md',
      'docs/CONTORNO_VCO_UNION_PROTOCOLO.md','docs/CONTORNO_VCO_UNION_RESULTADOS.md',
      'docs/PUERTO_VCO_CONTORNO_PROTOCOLO.md','docs/PUERTO_VCO_EXPRESION_PROTOCOLO.md')


def main():
    output=ROOT/'evidence/loudness_voice_tests.json'
    if output.exists():raise ValueError('preserve prior test receipt')
    inputs=set(DOCS)
    for pattern in PATTERNS:inputs.update(p.relative_to(ROOT).as_posix() for p in (ROOT/'tests').glob(pattern))
    for pattern in ('loudness_voice*','voice_port*','validate_loudness_voice.py','check_loudness_voice_release.py',
                    'loudness_board4*','validate_loudness_board4_bank.py','voice_circuit*','filter_vca_circuit*'):
        inputs.update(p.relative_to(ROOT).as_posix() for p in (ROOT/'tools').glob(pattern) if p.is_file())
    for pattern in ('loudness_voice*','voice_port*','loudness_board4_listening.json'):
        inputs.update(p.relative_to(ROOT).as_posix() for p in (ROOT/'evidence').glob(pattern) if p.is_file())
    audit=vco.read(ROOT/'evidence/loudness_voice_validation02.json')
    if not audit['passed'] or audit['coupling_admitted'] or audit['new_solves'] or len(audit['records'])!=17 or len(audit['replayed_port_pairs'])!=4:
        raise ValueError('audited rejected scope')
    inputs.update(audit['unchanged_electrical_inputs'])
    if audit['auditor_sha256']!=vco.sha(ROOT/'tools/validate_loudness_voice.py'):raise ValueError('auditor version')
    before={n:vco.sha(ROOT/n) for n in sorted(inputs)};runs=[];count=0
    for pattern in PATTERNS:
        command=[sys.executable,'-B','-m','unittest','discover','-s','tests','-p',pattern,'-v']
        start=time.perf_counter();r=subprocess.run(command,cwd=ROOT,capture_output=True,text=True)
        runs.append(dict(command=command,exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr,wall_s=time.perf_counter()-start))
        if r.returncode:raise ValueError('regression failed: '+pattern)
        match=re.search(r'Ran (\d+) tests?',r.stderr)
        if match is None:raise ValueError('missing test count')
        count+=int(match[1]);print(pattern,match[1],'passed',flush=True)
    if count!=40:raise ValueError('expected forty focused regressions')
    links=0
    for name in DOCS:
        path=ROOT/name
        for destination in re.findall(r'\]\(([^)]+)\)',path.read_text(encoding='utf-8')):
            if destination.startswith(('https:','http:','#')):continue
            target=destination.split('#')[0].strip('<>')
            if not (path.parent/target).exists():raise ValueError('missing document link: '+name+' -> '+target)
            links+=1
    listening=vco.read(ROOT/'evidence/loudness_board4_listening.json');montage=listening['montage']
    audio=ROOT/montage['path']
    if vco.sha(audio)!=montage['sha256']:raise ValueError('previous listening artifact altered')
    with wave.open(str(audio),'rb') as w:
        params=dict(sample_rate_hz=w.getframerate(),channels=w.getnchannels(),sample_width=w.getsampwidth(),frames=w.getnframes())
    if params!=dict(sample_rate_hz=48000,channels=1,sample_width=2,frames=64800):raise ValueError('previous audio format')
    after={n:vco.sha(ROOT/n) for n in sorted(inputs)}
    if before!=after:raise ValueError('inputs changed during regressions')
    report=dict(schema='rf-d/loudness-voice-tests/v1',passed=True,tests_count=count,runs=runs,
        git_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        source_sha256=before,source_after_sha256=after,sources_unchanged=True,new_solves=0,
        audited_receipts=17,replayed_port_pairs=4,local_document_links=links,
        previous_audio=dict(path=montage['path'],sha256=montage['sha256'],**params),
        new_audio=False,coupling_admitted=False,physical_fidelity=False,real_time=False)
    output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(count,'regressions passed; coupling remains rejected',flush=True)


if __name__=='__main__':main()
