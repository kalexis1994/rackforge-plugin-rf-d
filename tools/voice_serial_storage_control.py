"""Exercise retirement/restoration on new copies; leave the measured control intact."""
import shutil
from pathlib import Path
import numpy as np
import voice_serial_long as serial
import voice_serial_archive as storage
import voice_binary_runner as runner
import voice_native_raw as native
import vco1_circuit_reference as vco

ROOT=vco.ROOT
WORK=ROOT/'references-local/voice-circuit/serial-storage-control01'

def sources():
    return dict(serial.helpers(),**{p.relative_to(ROOT).as_posix():vco.sha(p) for p in (Path(__file__),Path(native.__file__))})

def main():
    output=ROOT/'evidence/voice_serial_storage_control01.json'
    if output.exists() or WORK.exists():raise ValueError('preserve serial storage control')
    control=ROOT/'evidence/voice_native_control01.json';audit=ROOT/'evidence/voice_native_control_validation01.json'
    r=vco.read(control);a=vco.read(audit)
    if not a['passed'] or not a['control_admitted'] or a['control_sha256']!=vco.sha(control):raise ValueError('admitted original native control')
    original=runner.CONTROL/'nominal500.raw';receipt=runner.CONTROL/'nominal500.json'
    if vco.sha(original)!=r['run']['raw_sha256'] or runner.six.canonical(vco.read(receipt))!=runner.six.canonical(r['run']):raise ValueError('original raw/receipt identity')
    pins={p.relative_to(ROOT).as_posix():vco.sha(p) for p in (original,receipt,runner.CONTROL/'nominal500.txt',control,audit)}
    before=sources();size=original.stat().st_size;free=shutil.disk_usage(ROOT).free
    # Conservative bound for two retained archives plus one intermediate/control copy.
    required=3*size+2*1024**2+serial.MARGIN
    report=dict(schema='rf-d/serial-storage-control/v1',passed=False,input_sha256=before,
        original_input_sha256=pins,available_free_bytes=free,required_free_bytes=required,
        resource_passed=free>=required,cases={},errors={},new_spice_solves=0,new_compiler_runs=0,
        historical_files_retained=True,long_note_measured=False,new_audio=False)
    runner.write(output,report)
    if not report['resource_passed']:print('serial storage control resource rejected',flush=True);return
    original_array,_=native.read(original,r['run']['vectors']);WORK.mkdir()
    for codec in ('gzip9','xz6-crc64'):
        case=WORK/codec;case.mkdir();raw=case/'nominal500.raw';copied_receipt=case/'nominal500.json'
        try:
            shutil.copyfile(original,raw);shutil.copyfile(receipt,copied_receipt)
            manifest=storage.archive_run(case,'nominal500',r['run'],codec)
            manifestp=case/'nominal500.archive.json'
            with storage.restored(case,'nominal500') as (restored,event):
                values,layout=native.read(restored,r['run']['vectors']);bits=native.bits(original_array,values)
                if not bits['passed']:raise ValueError('original control bit identity')
            if raw.exists() or not event['passed'] or not event['temporary_retired']:raise ValueError('control temporary retirement')
            report['cases'][codec]=dict(archive=manifest,manifest_path=manifestp.relative_to(ROOT).as_posix(),
                manifest_sha256=vco.sha(manifestp),bit_identity=bits,restoration=event,native_layout=layout)
        except Exception as exc:report['errors'][codec]=type(exc).__name__+': '+str(exc)
        runner.write(output,report)
    report['input_sha256_after']=sources()
    report['original_input_sha256_after']={n:vco.sha(ROOT/n) for n in pins}
    report['passed']=(len(report['cases'])==2 and not report['errors'] and before==report['input_sha256_after'] and pins==report['original_input_sha256_after'])
    runner.write(output,report);print('serial storage control:',report['passed'],flush=True)

if __name__=='__main__':main()
