"""Two release checkpoints: ten native tests, then three lossless archive tests."""
import hashlib, json, re, subprocess, sys, time, wave
from pathlib import Path
import numpy as np
import voice_binary_runner as runner
import voice_native_raw as native
import voice_six_runner as six
import vco1_circuit_reference as vco
import validate_voice_native_control as control_audit
from validate_loudness_board4_bank import source_identity

ROOT=vco.ROOT
NATIVE='evidence/voice_native_tests01.json'
ARCHIVE='evidence/voice_archive_tests01.json'
SUMMARIES=('README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md')

def hashes(names):return {n:vco.sha(ROOT/n) for n in names}

def main():
    if any((ROOT/p).exists() for p in (NATIVE,ARCHIVE)):raise ValueError('preserve release checkpoints')
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    base='3c5b9c21a06957dfec7eb8cf12fcf1fc106105a5'
    if head!=base:raise ValueError('declared inherited base required')
    inherited_path='evidence/voice_six_tests01.json';inherited=vco.read(ROOT/inherited_path)
    if not inherited['passed'] or inherited['tests_count']!=140:raise ValueError('admitted inherited QA')
    unchanged=[]
    for name,digest in inherited['source_sha256'].items():
        source_identity(name,digest,subprocess.check_output(['git','show',base+':'+name],cwd=ROOT))
        if name not in SUMMARIES:
            if vco.sha(ROOT/name)!=digest:raise ValueError('inherited input changed: '+name)
            unchanged.append(name)
    staged=subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=ROOT).decode().split('\0')
    names=sorted(set(inherited['source_sha256'])|{inherited_path}|{n for n in staged if n and n not in (NATIVE,ARCHIVE)})
    before=hashes(names)
    for name,digest in before.items():
        source_identity(name,digest,subprocess.check_output(['git','show',':'+name],cwd=ROOT))
    # Preserve both observed failures, their exact source snapshots and full replay.
    failed=[]
    for index in (1,2):
        p=ROOT/f'evidence/voice_native_parser_rejection0{index}.json';r=vco.read(p)
        if r['exit_code']!=1 or r['tests_count']!=10 or r['error_count']!=2 or r['gates_changed']:raise ValueError('preserved rejection')
        for n,snapshot in r['sources'].items():
            if hashlib.sha256(snapshot['source_text'].encode()).hexdigest()!=snapshot['sha256']:raise ValueError('failure snapshot identity')
            if n!='tools/voice_native_raw.py' and vco.sha(ROOT/n)!=snapshot['sha256']:raise ValueError('unchanged tests and runner')
            if n=='tools/voice_native_raw.py':
                restored=(ROOT/n).read_text(encoding='utf-8').replace(
                    "np.fromfile(path,dtype='<f8',count=rows*columns,offset=offset).reshape(rows,columns)",
                    "np.memmap(path,dtype='<f8',mode='r',offset=offset,shape=(rows,columns))")
                if restored!=snapshot['source_text']:raise ValueError('reader ownership-only repair')
        if index==2:
            if r['source_sha256_after']!={n:s['sha256'] for n,s in r['sources'].items()} or 'FAILED (errors=2)' not in r['stderr']:raise ValueError('full unchanged-source replay')
        failed.append(dict(path=p.relative_to(ROOT).as_posix(),sha256=vco.sha(p),attempt=index,exit_code=1,error_count=2))
    auditp=ROOT/'evidence/voice_native_control_validation01.json';audit=vco.read(auditp)
    if not audit['passed'] or not audit['control_admitted'] or audit['control_sha256']!=vco.sha(ROOT/'evidence/voice_native_control01.json'):raise ValueError('native audit binding')
    for n,h in audit['analysis_source_sha256'].items():
        if vco.sha(ROOT/n)!=h:raise ValueError('native audit source changed')
    receipt,a=control_audit.run_identity('nominal500')
    control=vco.read(ROOT/'evidence/voice_native_control01.json')
    if six.canonical(receipt)!=six.canonical(control['run']):raise ValueError('control public/private receipt')
    old,oldpath=runner.source('nominal500')
    ascii_array=np.loadtxt(runner.CONTROL/'nominal500.txt',skiprows=1,ndmin=2)
    old_array=np.loadtxt(oldpath.with_suffix('.txt'),skiprows=1,ndmin=2)
    if native.bits(old_array,ascii_array)!=audit['same_ascii_trajectory'] or native.bits(ascii_array,a)!=audit['binary_bit_identity']:raise ValueError('whole-array bit replay')
    archivep=ROOT/'evidence/voice_archive_control01.json';archive=vco.read(archivep)
    archive_auditp=ROOT/'evidence/voice_archive_control_validation01.json';archive_audit=vco.read(archive_auditp)
    if not archive_audit['passed'] or archive_audit['control_sha256']!=vco.sha(archivep):raise ValueError('archive audit binding')
    for scope in (archive['input_sha256'],archive_audit['analysis_source_sha256']):
        for n,h in scope.items():
            if vco.sha(ROOT/n)!=h:raise ValueError('archive input changed')
    private=dict(inherited['private_input_sha256'])
    private.update({p.relative_to(ROOT).as_posix():vco.sha(p) for p in runner.CONTROL.iterdir() if p.is_file()})
    for codec,r in archive['trials'].items():
        if private[r['path']]!=r['archive_sha256']:raise ValueError('archive changed since audited')
    for n,h in inherited['private_input_sha256'].items():
        if vco.sha(ROOT/n)!=h:raise ValueError('inherited private source changed')
    private[receipt['executable_path']]=receipt['executable_sha256']
    official=ROOT/'references-local/ngspice46/runtime/Spice64/bin/ngspice_con.exe'
    if vco.sha(official)!=inherited['official_executable_sha256']:raise ValueError('official executable changed')
    audio=inherited['previous_audio'];audio_path=ROOT/audio['path']
    if vco.sha(audio_path)!=audio['sha256']:raise ValueError('historical audio changed')
    with wave.open(str(audio_path),'rb') as stream:
        if (stream.getnchannels(),stream.getsampwidth(),stream.getframerate(),stream.getnframes())!=(audio['channels'],audio['sample_width_bytes'],audio['sample_rate_hz'],audio['frames']):raise ValueError('audio metadata')
    links=set()
    for name in names:
        if not name.endswith('.md'):continue
        path=ROOT/name
        for link in re.findall(r'\]\(([^)]+)\)',path.read_text(encoding='utf-8')):
            if link.startswith(('https:','http:','#')):continue
            target=(path.parent/link.split('#')[0].strip('<>')).resolve()
            if not target.exists() and target not in (ROOT/NATIVE,ROOT/ARCHIVE):raise ValueError('missing local document link: '+str(target))
            links.add(str(target))
    def checkpoint(output,pattern,count,previous,previous_count):
        source_before=hashes(names);private_before=hashes(private)
        command=[sys.executable,'-B','-m','unittest','discover','-s','tests','-p',pattern,'-v']
        start=time.perf_counter();result=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',timeout=180)
        if result.returncode or not re.search(r'Ran '+str(count)+r' tests? in ',result.stderr) or not result.stderr.rstrip().endswith('OK'):raise ValueError('release regression rejected: '+result.stderr)
        after=hashes(names);private_after=hashes(private)
        if source_before!=after or private_before!=private_after:raise ValueError('release inputs changed')
        report=dict(schema='rf-d/native-storage-release/v1',passed=True,tests_count=previous_count+count,new_tests_count=count,
            inherited_tests_count=previous_count,inherited_qa=dict(path=previous,sha256=vco.sha(ROOT/previous),base_commit=base,executed_again=False),
            unchanged_inherited_inputs=unchanged,summary_updates=list(SUMMARIES),
            runs=[dict(command=command,exit_code=result.returncode,tests_count=count,stdout=result.stdout,stderr=result.stderr,wall_s=time.perf_counter()-start)],
            source_sha256=source_before,source_sha256_after=after,private_input_sha256=private_before,private_input_sha256_after=private_after,
            preserved_parser_rejections=failed,control_admitted=True,control_audit_sha256=vco.sha(auditp),
            archive_control_admitted=True,archive_audit_sha256=vco.sha(archive_auditp),serial_resources_admitted=archive_audit['serial_resources_admitted'],
            previous_audio=audio,official_executable_sha256=vco.sha(official),local_document_links=len(links),
            measured_spice_solves=1,new_spice_solves_during_qa=0,new_compiler_runs_during_qa=0,
            long_note_measured_with_six=False,physical_fidelity=False,real_time=False,new_audio=False)
        runner.write(ROOT/output,report)
        print(output,':',count,'executed +',previous_count,'inherited =',previous_count+count,flush=True)
    checkpoint(NATIVE,'test_voice_native_raw.py',10,inherited_path,140)
    names.append(NATIVE)
    checkpoint(ARCHIVE,'test_voice_lossless_archive.py',3,NATIVE,150)
    if not all(Path(p).exists() for p in links):raise ValueError('release document links incomplete')

if __name__=='__main__':main()
