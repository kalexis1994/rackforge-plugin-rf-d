"""Replay real-copy retirement and restoration, with historical originals pinned."""
from pathlib import Path
import voice_serial_storage_control as control
import voice_serial_archive as storage
import voice_binary_runner as runner
import voice_native_raw as native
import vco1_circuit_reference as vco

ROOT=vco.ROOT

def main():
    reportp=ROOT/'evidence/voice_serial_storage_control01.json'
    output=ROOT/'evidence/voice_serial_storage_validation01.json'
    if output.exists():raise ValueError('preserve serial storage audit')
    report=vco.read(reportp)
    if not report['passed'] or not report['resource_passed'] or report['errors']:raise ValueError('completed control required')
    if report['input_sha256']!=control.sources() or report['input_sha256_after']!=control.sources():raise ValueError('measured storage control source scope')
    if report['original_input_sha256']!=report['original_input_sha256_after']:raise ValueError('originals changed during control')
    for n,h in report['original_input_sha256'].items():
        if vco.sha(ROOT/n)!=h:raise ValueError('historical original changed')
    original=runner.CONTROL/'nominal500.raw';receipt=runner.CONTROL/'nominal500.json';r=vco.read(receipt)
    if report['required_free_bytes']!=3*original.stat().st_size+2*1024**2+2*1024**3 or report['available_free_bytes']<report['required_free_bytes']:
        raise ValueError('control resource arithmetic')
    a,layout=native.read(original,r['vectors']);replayed={}
    for codec in ('gzip9','xz6-crc64'):
        case=control.WORK/codec;proof=report['cases'][codec]
        manifestp=case/'nominal500.archive.json'
        manifest,raw,_,_=storage.archive_identity(case,'nominal500')
        if raw.exists() or proof['archive']!=manifest or proof['manifest_path']!=manifestp.relative_to(ROOT).as_posix() or proof['manifest_sha256']!=vco.sha(manifestp):raise ValueError('new copy manifest binding')
        if manifest['receipt_sha256']!=vco.sha(receipt):raise ValueError('copied exact original receipt')
        with storage.restored(case,'nominal500') as (restored,event):
            b,native_layout=native.read(restored,r['vectors']);bits=native.bits(a,b)
            if not bits['passed'] or bits!=proof['bit_identity'] or native_layout!=layout or native_layout!=proof['native_layout']:
                raise ValueError('all native control bits and layout')
        if event!=proof['restoration'] or not event['passed'] or raw.exists():raise ValueError('restoration retirement replay')
        replayed[codec]=dict(bit_identity=bits,manifest_sha256=vco.sha(manifestp),original_sha256=manifest['original_sha256'],temporary_retired=event['temporary_retired'])
    for n,h in report['original_input_sha256'].items():
        if vco.sha(ROOT/n)!=h:raise ValueError('historical original changed during audit')
    runner.write(output,dict(schema='rf-d/serial-storage-control-audit/v1',passed=True,
        control_sha256=vco.sha(reportp),analysis_source_sha256={Path(__file__).relative_to(ROOT).as_posix():vco.sha(Path(__file__))},
        replayed=replayed,originals_retained=True,new_spice_solves=0,new_compiler_runs=0,
        long_note_measured=False,new_audio=False))
    print('serial real-copy storage audit: passed',flush=True)

if __name__=='__main__':main()
