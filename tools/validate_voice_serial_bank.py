"""Prospective serial-bank replay, including original private receipts after restore."""
import argparse,math
from pathlib import Path
import voice_serial_long as serial
import voice_serial_archive as storage
import voice_binary_runner as runner
import validate_voice_native_control as native_audit
import voice_full_note as note
import vco1_circuit_reference as vco

ROOT=vco.ROOT

def resource_identity(path):
    r=vco.read(path);control=vco.read(ROOT/'evidence/voice_archive_control01.json')
    audit=ROOT/'evidence/voice_archive_control_validation01.json'
    if r['archive_control_sha256']!=vco.sha(ROOT/'evidence/voice_archive_control01.json') or r['archive_audit_sha256']!=vco.sha(audit) or not vco.read(audit)['passed']:
        raise ValueError('resource storage lineage')
    if r['native_audit_sha256']!=vco.sha(ROOT/'evidence/voice_native_control_validation01.json'):
        raise ValueError('resource native lineage')
    if r['helper_sha256']!=serial.helpers() or r['scene_order']!=list(storage.SCENES) or r['max_workers']!=1 or r['wall_limit_s_per_process']!=7200 or r['new_spice_solves']!=0:
        raise ValueError('resource implementation/budgets')
    short=vco.read(ROOT/'evidence/voice_six_short_runs01.json');native=vco.read(ROOT/'evidence/voice_native_control_validation01.json')
    for codec in ('gzip9','xz6-crc64'):
        pre=r['trials'][codec];density=control['trials'][codec]['archive_bytes']/control['original_bytes']
        retained=0;largest=0
        for name in storage.SCENES:
            sr=short['records']['joint-'+name];e=pre['estimates'][name]
            rows=math.ceil(sr['rows']*8.75);size=rows*19*8+native['native_layout']['header_bytes']
            receipt=runner.six.WORK/('joint-'+name+'.json')
            if e['short_rows']!=sr['rows'] or e['short_receipt_sha256']!=vco.sha(receipt) or e['estimated_long_rows']!=rows or e['columns']!=19 or e['bytes_per_scalar']!=8 or e['duration_ratio']!=8.75 or e['estimated_long_export_bytes']!=size or e['observed_header_bytes']!=native['native_layout']['header_bytes']:
                raise ValueError('resource scene identity')
            packed=math.ceil(size*density)
            if e['estimated_archive_bytes']!=packed:raise ValueError('resource density arithmetic')
            retained+=packed;largest=max(largest,size)
        required=retained+largest+2*1024**3
        if pre['density']!=density or pre['estimated_retained_archive_bytes']!=retained or pre['largest_intermediate_bytes']!=largest or pre['margin_bytes']!=2*1024**3 or pre['required_free_bytes']!=required or pre['available_free_bytes']!=r['available_free_bytes'] or pre['passed']!=(r['available_free_bytes']>=required) or not pre['estimates_are_not_bounds']:
            raise ValueError('recorded resource arithmetic')
    selected=next((c for c in ('gzip9','xz6-crc64') if r['trials'][c]['passed']),None)
    if r['selected_codec']!=selected or r['passed']!=(selected is not None):raise ValueError('codec selection')
    return r

def validate():
    bankp=ROOT/'evidence/voice_serial_runs01.json';bank=vco.read(bankp)
    preflight=ROOT/bank['preflight_path'];resource=resource_identity(preflight)
    if not resource['passed'] or bank['preflight_sha256']!=vco.sha(preflight) or bank['selected_codec']!=resource['selected_codec']:
        raise ValueError('admitted initial serial resource gate')
    qap=ROOT/serial.QA;qa=vco.read(qap)
    if bank['release_qa_sha256']!=vco.sha(qap) or not qa['passed'] or not qa['serial_implementation_verified']:raise ValueError('serial release dependency')
    if bank['helper_sha256']!=serial.helpers() or bank['helper_sha256_after']!=serial.helpers():raise ValueError('measured serial helper scope')
    if runner.six.canonical(bank['gates'])!=runner.six.canonical(note.GATES) or runner.six.canonical(bank['window_spans_s'])!=runner.six.canonical(note.WINDOWS) or bank['scene_order']!=list(storage.SCENES) or bank['max_workers']!=1:
        raise ValueError('frozen temporal gates')
    if bank['unreceipted_attempts']:raise ValueError('unreceipted attempt requires explicit recovery audit')
    if bank['storage_errors']:raise ValueError('storage failure requires explicit recovery audit')
    ordered=list(bank['records'])
    if ordered!=list(storage.SCENES[:len(ordered)]):raise ValueError('strict serial prefix')
    codec=bank['selected_codec'];estimates=resource['trials'][codec]['estimates'];density=resource['trials'][codec]['density']
    for index,phase in enumerate(bank['phase_resources']):
        replay=serial.phase_budget(estimates,density,storage.SCENES[index:],phase['available_free_bytes'])
        if phase['before_scene']!=storage.SCENES[index] or any(phase[k]!=v for k,v in replay.items()):raise ValueError('per-phase resource replay')
        if not phase['passed'] and index<len(ordered):raise ValueError('solver ran after rejected phase resources')
    if bank['measured_spice_solves']!=sum(int(r['process_started']) for r in bank['records'].values()):raise ValueError('receipted process count')
    events=[];archives={}
    for name,r in bank['records'].items():
        if 'raw_sha256' not in r:
            private,_=native_audit.run_identity(name,True)
        else:
            m,_,_,manifest=storage.archive_identity(serial.WORK,name)
            if m!=bank['archives'][name] or vco.sha(manifest)!=bank['archive_manifest_sha256'][name]:raise ValueError('public/private archive binding')
            private,_=serial.observe(name,events);archives[name]=m
        if runner.six.canonical(private)!=runner.six.canonical(r):raise ValueError('original public/private run receipt')
    replay=dict(records=bank['records'],archives=archives,measurements={},comparisons={},electrical_errors={},storage_errors={},resource_errors=bank['resource_errors'])
    required=max((r['original_bytes'] for r in archives.values()),default=0)+serial.MARGIN
    observation=bank['observation_resources']
    if observation['required_free_bytes']!=required:raise ValueError('restoration budget')
    if observation['available_free_bytes']>=required:
        serial.evaluate(replay,lambda name:serial.observe(name,events))
    else:replay['long_note_admitted_locally']=False
    for key in ('measurements','comparisons','long_note_admitted_locally'):
        if runner.six.canonical(replay[key])!=runner.six.canonical(bank[key]):raise ValueError('bank observation replay: '+key)
    if any(not e['passed'] or not e['temporary_retired'] for e in bank['restorations']):raise ValueError('stored restoration failure')
    for e in bank['restorations']:
        m=archives[e['scene']]
        if e['restored_sha256']!=m['original_sha256'] or e['restored_bytes']!=m['original_bytes'] or e['archive_sha256']!=m['archive_sha256'] or e['manifest_sha256']!=bank['archive_manifest_sha256'][e['scene']]:raise ValueError('stored restoration lineage')
    return dict(schema='rf-d/serial-long-audit/v1',passed=True,bank_sha256=vco.sha(bankp),
        analysis_source_sha256={Path(__file__).relative_to(ROOT).as_posix():vco.sha(Path(__file__))},
        restored_original_receipts=len(bank['records']),long_note_admitted_locally=bank['long_note_admitted_locally'],
        new_spice_solves=0,new_compiler_runs=0,new_audio=False)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--preflight',type=int);args=parser.parse_args()
    if args.preflight is not None:
        if not 1<=args.preflight<=99:raise ValueError('preflight number 1..99')
        path=ROOT/f'evidence/voice_serial_preflight{args.preflight:02d}.json';resource_identity(path)
        print('serial resource replay passed:',vco.read(path)['passed'],flush=True)
    else:
        path=ROOT/'evidence/voice_serial_validation01.json'
        if path.exists():raise ValueError('preserve serial audit')
        runner.write(path,validate());print('serial bank audit passed',flush=True)

if __name__=='__main__':main()
