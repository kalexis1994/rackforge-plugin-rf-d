"""Release prepared serial infrastructure; no new SPICE and no repeated inherited tests."""
import json,re,subprocess
from pathlib import Path
import voice_serial_long as serial
import voice_serial_archive as storage
import voice_binary_runner as runner
import voice_serial_storage_control as control
import validate_voice_serial_bank as audit
import vco1_circuit_reference as vco
from validate_loudness_board4_bank import source_identity

ROOT=vco.ROOT
OUTPUT=ROOT/'evidence/voice_serial_tests01.json'
SUMMARIES=('README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md')

def hashes(names):return {n:vco.sha(ROOT/n) for n in names}

def main():
    if OUTPUT.exists():raise ValueError('preserve serial release QA')
    base='aaf434d8ab9ed00fd6936dbfda899ada33c01f6b'
    if subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()!=base:raise ValueError('declared release base')
    inherited_path='evidence/voice_archive_tests01.json';previous=vco.read(ROOT/inherited_path)
    if not previous['passed'] or previous['tests_count']!=153:raise ValueError('admitted inherited storage QA')
    unchanged=[]
    for n,h in previous['source_sha256'].items():
        source_identity(n,h,subprocess.check_output(['git','show',base+':'+n],cwd=ROOT))
        if n not in SUMMARIES:
            if vco.sha(ROOT/n)!=h:raise ValueError('inherited input changed: '+n)
            unchanged.append(n)
    staged=subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=ROOT).decode().split('\0')
    names=sorted(set(previous['source_sha256'])|{inherited_path}|{n for n in staged if n and ROOT/n!=OUTPUT})
    before=hashes(names)
    for n,h in before.items():source_identity(n,h,subprocess.check_output(['git','show',':'+n],cwd=ROOT))
    regressionp=ROOT/'evidence/voice_serial_regression01.json';reg=vco.read(regressionp)
    if not reg['passed'] or reg['exit_code']!=0 or reg['tests_count']!=12 or 'Ran 12 tests in ' not in reg['stderr'] or not reg['stderr'].rstrip().endswith('OK'):
        raise ValueError('twelve captured regressions required')
    if reg['source_sha256']!=reg['source_sha256_after']:raise ValueError('regression source stability')
    for n,h in reg['source_sha256'].items():
        if vco.sha(ROOT/n)!=h:raise ValueError('executed regression source changed')
    controlp=ROOT/'evidence/voice_serial_storage_control01.json';cp=vco.read(controlp)
    storagep=ROOT/'evidence/voice_serial_storage_validation01.json';sp=vco.read(storagep)
    if not cp['passed'] or not sp['passed'] or sp['control_sha256']!=vco.sha(controlp) or cp['errors']:
        raise ValueError('audited real-copy storage control')
    if cp['input_sha256']!=control.sources() or cp['input_sha256_after']!=control.sources():raise ValueError('control source scope')
    for n,h in sp['analysis_source_sha256'].items():
        if vco.sha(ROOT/n)!=h:raise ValueError('control auditor changed')
    preflightp=ROOT/'evidence/voice_serial_preflight01.json';pre=audit.resource_identity(preflightp)
    resourcep=ROOT/'evidence/voice_serial_preflight_validation01.json';resource=vco.read(resourcep)
    if not resource['passed'] or resource['exit_code']!=0 or resource['preflight_sha256']!=vco.sha(preflightp) or resource['recorded_resources_passed']!=pre['passed'] or resource['source_sha256']!=resource['source_sha256_after']:
        raise ValueError('resource audit binding')
    for n,h in resource['source_sha256'].items():
        if vco.sha(ROOT/n)!=h:raise ValueError('resource auditor changed')
    private=dict(previous['private_input_sha256'])
    for codec in ('gzip9','xz6-crc64'):
        case=control.WORK/codec;manifest,raw,target,mp=storage.archive_identity(case,'nominal500')
        if raw.exists() or cp['cases'][codec]['archive']!=manifest or cp['cases'][codec]['manifest_sha256']!=vco.sha(mp):raise ValueError('new copy archive identity')
        for p in (target,mp,case/'nominal500.json'):private[p.relative_to(ROOT).as_posix()]=vco.sha(p)
        if not cp['cases'][codec]['bit_identity']['passed'] or cp['cases'][codec]['bit_identity']['bit_mismatches']!=0 or not cp['cases'][codec]['restoration']['temporary_retired']:
            raise ValueError('real-copy exactness and retirement')
    for n,h in private.items():
        if vco.sha(ROOT/n)!=h:raise ValueError('private input changed')
    for n,h in cp['original_input_sha256'].items():
        if vco.sha(ROOT/n)!=h:raise ValueError('historical control changed')
    if cp['original_input_sha256']!=cp['original_input_sha256_after']:raise ValueError('historical stability')
    if runner.LONG.exists() or (ROOT/'evidence/voice_serial_runs01.json').exists():raise ValueError('this release declares no long bank')
    links=set()
    for n in names:
        if not n.endswith('.md'):continue
        path=ROOT/n
        for link in re.findall(r'\]\(([^)]+)\)',path.read_text(encoding='utf-8')):
            if link.startswith(('https:','http:','#')):continue
            p=(path.parent/link.split('#')[0].strip('<>')).resolve()
            if not p.exists() and p!=OUTPUT:raise ValueError('missing document target '+str(p))
            links.add(str(p))
    after=hashes(names);private_after=hashes(private)
    if before!=after or private!=private_after:raise ValueError('release input mutation')
    runner.write(OUTPUT,dict(schema='rf-d/serial-storage-release/v1',passed=True,tests_count=165,
        new_tests_count=12,inherited_tests_count=153,
        inherited_qa=dict(path=inherited_path,sha256=vco.sha(ROOT/inherited_path),base_commit=base,executed_again=False),
        unchanged_inherited_inputs=unchanged,summary_updates=list(SUMMARIES),
        regression_receipt_sha256=vco.sha(regressionp),runs=[{k:reg[k] for k in ('command','exit_code','tests_count','stdout','stderr','wall_s')}],
        source_sha256=before,source_sha256_after=after,private_input_sha256=private,private_input_sha256_after=private_after,
        serial_implementation_verified=True,real_copy_storage_control_admitted=True,
        storage_control_sha256=vco.sha(controlp),storage_control_audit_sha256=vco.sha(storagep),
        serial_resource_preflight_sha256=vco.sha(preflightp),serial_resource_audit_sha256=vco.sha(resourcep),
        serial_resources_admitted=pre['passed'],previous_audio=previous['previous_audio'],
        official_executable_sha256=previous['official_executable_sha256'],local_document_links=len(links),
        new_spice_solves=0,new_compiler_runs=0,long_note_measured_with_six=False,
        physical_fidelity=False,real_time=False,new_audio=False))
    print('serial QA: 12 executed + 153 inherited = 165; sources:',len(names),flush=True)

if __name__=='__main__':main()
