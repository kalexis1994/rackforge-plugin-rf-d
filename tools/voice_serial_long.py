"""One fresh-DC long scene at a time, with verified reversible private storage."""
import argparse, math, shutil
from pathlib import Path
import voice_binary_runner as runner
import voice_binary_long_probe as binary
import voice_serial_archive as storage
import voice_lossless_archive as archive
import voice_full_note as note
import validate_voice_native_control as native_audit
import vco1_circuit_reference as vco

ROOT=vco.ROOT
PROTOCOL='docs/VOZ_NOTA_LARGA_ARCHIVO_PROTOCOLO.md'
IMPLEMENTATION='docs/VOZ_SERIAL_IMPLEMENTACION.md'
QA='evidence/voice_serial_tests01.json'
WORK=runner.LONG
MARGIN=2*1024**3

def helpers():
    paths=[Path(__file__),Path(storage.__file__),Path(archive.__file__),Path(native_audit.__file__),
           Path(note.__file__),Path(binary.__file__),ROOT/'tools/validate_voice_serial_bank.py',
           ROOT/PROTOCOL,ROOT/IMPLEMENTATION]
    return {p.relative_to(ROOT).as_posix():vco.sha(p) for p in paths}

def prerequisites():
    source=ROOT/'evidence/voice_archive_control01.json';proof=ROOT/'evidence/voice_archive_control_validation01.json'
    control=vco.read(source);audit=vco.read(proof)
    if not control['passed'] or not audit['passed'] or audit['control_sha256']!=vco.sha(source):
        raise ValueError('audited lossless storage control required')
    for scope in (control['input_sha256'],audit['analysis_source_sha256']):
        for n,h in scope.items():
            if vco.sha(ROOT/n)!=h:raise ValueError('control source changed')
    for codec in archive.CODECS:
        r=control['trials'][codec];p=ROOT/r['path']
        if not r['passed'] or vco.sha(p)!=r['archive_sha256'] or p.stat().st_size!=r['archive_bytes']:
            raise ValueError('admitted archive changed')
    return control,binary.estimate()['estimates']

def budget(estimates,density,free):
    cases={n:dict(e,estimated_archive_bytes=math.ceil(e['estimated_long_export_bytes']*density)) for n,e in estimates.items()}
    retained=sum(e['estimated_archive_bytes'] for e in cases.values())
    largest=max(e['estimated_long_export_bytes'] for e in cases.values())
    required=retained+largest+MARGIN
    return dict(estimates=cases,density=density,estimated_retained_archive_bytes=retained,
        largest_intermediate_bytes=largest,margin_bytes=MARGIN,required_free_bytes=required,
        available_free_bytes=free,passed=free>=required,estimates_are_not_bounds=True)

def estimate():
    control,estimates=prerequisites();free=shutil.disk_usage(ROOT).free
    trials={c:budget(estimates,control['trials'][c]['archive_bytes']/control['original_bytes'],free) for c in archive.CODECS}
    selected=next((c for c in archive.CODECS if trials[c]['passed']),None)
    return dict(schema='rf-d/serial-long-preflight/v1',passed=selected is not None,selected_codec=selected,
        trials=trials,available_free_bytes=free,scene_order=list(storage.SCENES),max_workers=1,
        wall_limit_s_per_process=7200,helper_sha256=helpers(),new_spice_solves=0,
        archive_control_sha256=vco.sha(ROOT/'evidence/voice_archive_control01.json'),
        archive_audit_sha256=vco.sha(ROOT/'evidence/voice_archive_control_validation01.json'),
        native_audit_sha256=vco.sha(ROOT/'evidence/voice_native_control_validation01.json'))

def preflight(number):
    if not 1<=number<=99:raise ValueError('explicit preflight number 1..99 required')
    path=ROOT/f'evidence/voice_serial_preflight{number:02d}.json'
    if path.exists():raise ValueError('preserve preflight; use a new explicit number')
    r=estimate();runner.write(path,r)
    print('serial preflight:',r['passed'],'selected:',r['selected_codec'],'available:',r['available_free_bytes'],flush=True)
    return path,r

def phase_budget(estimates,density,pending,free):
    # Completed archives already consume disk; do not count them again as future writes.
    retained=sum(math.ceil(estimates[n]['estimated_long_export_bytes']*density) for n in pending)
    largest=max((estimates[n]['estimated_long_export_bytes'] for n in pending),default=0)
    required=retained+largest+MARGIN
    return dict(pending=list(pending),estimated_future_archives_bytes=retained,
        largest_intermediate_bytes=largest,margin_bytes=MARGIN,required_free_bytes=required,
        available_free_bytes=free,passed=free>=required,estimates_are_not_bounds=True)

def observe(name,events):
    with storage.restored(WORK,name) as (path,event):
        receipt,array=native_audit.run_identity(name,True)
    events.append(event)
    return receipt,array

def evaluate(bank,observer):
    scenes=note.scenes()
    for name,s in scenes.items():
        r=bank['records'].get(name)
        if not r:continue  # Resource-pending scenes have no electrical result.
        if not r['trajectory_complete']:
            bank['electrical_errors'].setdefault(name,'solver trajectory incomplete');continue
        if name not in bank['archives']:
            bank['storage_errors'].setdefault(name,'complete scene archive missing');continue
        try:
            _,array=observer(name)
            m=note.measurement(array,s);bank['measurements'][name]=m
            if max(m['timing_balance_max_c'],m['output_balance_max_c'])>note.GATES['charge_c']:
                bank['electrical_errors'][name]='charge gate rejected'
        except Exception as exc:bank['storage_errors'][name]='observation: '+str(exc)
    for left,right in note.short.PAIRS:
        key=left+'--'+right
        if left not in bank['measurements'] or right not in bank['measurements']:
            bank['comparisons'][key]=dict(measured=False,passed=False,reason='required complete archived scene missing');continue
        try:
            _,a=observer(left);_,b=observer(right)
            bank['comparisons'][key]=note.contrast(a,b,scenes[left],scenes[right])
        except Exception as exc:
            bank['storage_errors'][key]='contrast: '+str(exc)
            bank['comparisons'][key]=dict(measured=False,passed=False,reason='archive observation failed')
    bank['long_note_admitted_locally']=(len(bank['measurements'])==4 and len(bank['comparisons'])==3
        and not bank['electrical_errors'] and not bank['storage_errors'] and not bank['resource_errors']
        and all(c['measured'] and c['passed'] for c in bank['comparisons'].values()))

def run_bank(preflight_path,resource):
    output=ROOT/'evidence/voice_serial_runs01.json'
    if output.exists() or WORK.exists():raise ValueError('preserve serial campaign')
    qap=ROOT/QA;qa=vco.read(qap)
    if not qa['passed'] or not qa['serial_implementation_verified'] or qa['source_sha256'].get('tools/voice_serial_long.py')!=vco.sha(Path(__file__)):
        raise ValueError('serial release QA required')
    for n,h in helpers().items():
        if qa['source_sha256'].get(n)!=h:raise ValueError('serial release source changed')
    current=estimate()
    if not resource['passed'] or current['helper_sha256']!=resource['helper_sha256'] or not current['trials'][resource['selected_codec']]['passed']:
        raise ValueError('admitted recorded and current resources required')
    codec=resource['selected_codec'];estimates=resource['trials'][codec]['estimates'];density=resource['trials'][codec]['density']
    bank=dict(schema='rf-d/serial-long-bank/v1',preflight_path=preflight_path.relative_to(ROOT).as_posix(),
        preflight_sha256=vco.sha(preflight_path),release_qa_sha256=vco.sha(qap),selected_codec=codec,
        helper_sha256=helpers(),records={},archives={},archive_manifest_sha256={},measurements={},comparisons={},
        electrical_errors={},storage_errors={},resource_errors={},phase_resources=[],restorations=[],
        scene_order=list(storage.SCENES),max_workers=1,gates=note.GATES,window_spans_s=note.WINDOWS,
        decision='serial measurements pending',long_note_admitted_locally=False,new_audio=False,
        physical_fidelity=False,real_time=False,measured_spice_solves=0,unreceipted_attempts={})
    runner.write(output,bank)
    for index,name in enumerate(storage.SCENES):
        phase=phase_budget(estimates,density,storage.SCENES[index:],shutil.disk_usage(ROOT).free)
        phase['before_scene']=name;bank['phase_resources'].append(phase)
        if not phase['passed']:
            bank['resource_errors'][name]='current phase storage rejected; remaining scenes not measured';break
        try:
            r=runner.run(name,True);bank['records'][name]=r
            bank['measured_spice_solves']+=int(r['process_started'])
            runner.write(output,bank)
            if 'raw_sha256' in r:
                bank['archives'][name]=storage.archive_run(WORK,name,r,codec)
                bank['archive_manifest_sha256'][name]=vco.sha(WORK/(name+'.archive.json'))
            else:bank['electrical_errors'][name]='solver produced no native export'
        except Exception as exc:
            # A storage/launch exception retains every surviving new artifact.
            bank['storage_errors'][name]=type(exc).__name__+': '+str(exc)
            if name not in bank['records']:
                bank['unreceipted_attempts'][name]=dict(process_started_unknown=True,
                    surviving_artifacts={p.name:dict(sha256=vco.sha(p),bytes=p.stat().st_size)
                        for p in WORK.glob(name+'.*') if p.is_file()})
            runner.write(output,bank);break
        runner.write(output,bank)
    restore_required=max((r['original_bytes'] for r in bank['archives'].values()),default=0)+MARGIN
    bank['observation_resources']=dict(required_free_bytes=restore_required,available_free_bytes=shutil.disk_usage(ROOT).free)
    if bank['observation_resources']['available_free_bytes']>=restore_required:
        evaluate(bank,lambda name:observe(name,bank['restorations']))
    else:bank['resource_errors']['observation']='restoration storage rejected; comparisons not measured'
    bank['helper_sha256_after']=helpers()
    if bank['helper_sha256']!=bank['helper_sha256_after']:
        bank['storage_errors']['sources']='serial helpers changed';bank['long_note_admitted_locally']=False
    bank['decision']=('serial long note admitted locally' if bank['long_note_admitted_locally'] else
                      'serial bank incomplete due to resources/storage' if bank['resource_errors'] or bank['storage_errors'] else 'serial long note rejected')
    runner.write(output,bank)
    print('serial bank:',bank['decision'],flush=True)
    return bank

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--preflight',type=int,required=True)
    parser.add_argument('--run',action='store_true');args=parser.parse_args()
    path,resource=preflight(args.preflight)
    if args.run and resource['passed']:run_bank(path,resource)
    elif args.run:print('no SPICE: serial resource gate rejected',flush=True)

if __name__=='__main__':main()
