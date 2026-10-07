"""Replay complete decompression, pinned inputs, and recorded resource arithmetic."""
import gzip, hashlib, lzma, math
from pathlib import Path
import voice_binary_runner as runner
import voice_binary_long_probe as probe
import vco1_circuit_reference as vco

ROOT=vco.ROOT

def main():
    controlp=ROOT/'evidence/voice_archive_control01.json'
    output=ROOT/'evidence/voice_archive_control_validation01.json'
    if output.exists():raise ValueError('preserve archive audit')
    report=vco.read(controlp);sources=report['input_sha256']
    if sources!=report['input_sha256_after']:raise ValueError('archive inputs changed during preparation')
    for name,digest in sources.items():
        if vco.sha(ROOT/name)!=digest:raise ValueError('archive input changed: '+name)
    nativep=ROOT/'evidence/voice_native_control_validation01.json';native=vco.read(nativep)
    if not native['passed'] or not native['control_admitted'] or report['native_audit_sha256']!=vco.sha(nativep):raise ValueError('native audit binding')
    raw=ROOT/report['original_path'];raw_size=raw.stat().st_size;raw_sha=vco.sha(raw)
    if raw_sha!=report['original_sha256'] or raw_size!=report['original_bytes']:raise ValueError('retained raw identity')
    if vco.sha(raw.with_suffix('.txt'))!=report['original_ascii_sha256']:raise ValueError('retained ASCII identity')
    decoded={};expected_estimates=probe.estimate()['estimates']
    for codec,opener,suffix in (('gzip9',gzip.open,'.gz'),('xz6-crc64',lzma.open,'.xz')):
        trial=report['trials'][codec];path=ROOT/trial['path']
        if path.resolve()!=raw.with_name('nominal500.control.raw'+suffix).resolve():raise ValueError('archive path')
        if vco.sha(path)!=trial['archive_sha256'] or path.stat().st_size!=trial['archive_bytes']:raise ValueError('archive byte identity')
        digest=hashlib.sha256();count=0
        with opener(path,'rb') as stream:
            while block:=stream.read(1024*1024):digest.update(block);count+=len(block)
        restored=dict(sha256=digest.hexdigest(),bytes=count)
        if restored!=dict(sha256=raw_sha,bytes=raw_size) or restored!=trial['restored']:raise ValueError('full decompression identity')
        if trial['original_sha256']!=raw_sha or trial['original_bytes']!=raw_size or not trial['passed'] or not trial['source_retained']:raise ValueError('trial decision')
        pre=trial['serial_preflight'];density=trial['archive_bytes']/raw_size
        cases={n:dict(e,estimated_archive_bytes=math.ceil(e['estimated_long_export_bytes']*density)) for n,e in expected_estimates.items()}
        total=sum(e['estimated_archive_bytes'] for e in cases.values());largest=max(e['estimated_long_export_bytes'] for e in cases.values())
        if pre['density']!=density or cases!=pre['estimates'] or pre['margin_bytes']!=2*1024**3:raise ValueError('budget inputs')
        required=total+largest+pre['margin_bytes']
        if pre['estimated_retained_archive_bytes']!=total or pre['largest_intermediate_bytes']!=largest or pre['required_free_bytes']!=required or pre['passed']!=(pre['available_free_bytes']>=required):raise ValueError('recorded resource arithmetic')
        decoded[codec]=dict(restored=restored,archive_sha256=vco.sha(path),required_free_bytes=required,
                            recorded_resources_passed=pre['passed'])
    selected=next((c for c in ('gzip9','xz6-crc64') if report['trials'][c]['serial_preflight']['passed']),None)
    passed=not report['errors'] and report['source_retained_identity']==dict(sha256=raw_sha,bytes=raw_size,ascii_sha256=report['original_ascii_sha256'])
    resources=passed and selected is not None
    if resources:resources=report['available_free_bytes_final']>=report['trials'][selected]['serial_preflight']['required_free_bytes']
    if report['passed']!=passed or not passed or report['selected_codec']!=selected or report['serial_resources_admitted']!=resources or report['new_spice_solves']!=0:raise ValueError('archive decisions')
    runner.write(output,dict(schema='rf-d/lossless-archive-audit/v1',passed=True,
        control_sha256=vco.sha(controlp),analysis_source_sha256={Path(__file__).relative_to(ROOT).as_posix():vco.sha(Path(__file__))},
        decoded=decoded,serial_resources_admitted=resources,selected_codec=selected,
        current_availability_is_not_historical_replay=True,original_retained=True,new_spice_solves=0,
        long_note_measured=False,new_audio=False))
    print('archive audit: passed; serial resources:',resources,flush=True)

if __name__=='__main__':main()
