"""Prepare reversible control archives and a prospective serial resource budget."""
import math, platform, shutil, sys, time, zlib
from pathlib import Path
import voice_lossless_archive as archive
import voice_binary_long_probe as probe
import voice_binary_runner as runner
import vco1_circuit_reference as vco

ROOT = vco.ROOT
PROTOCOL = 'docs/VOZ_NOTA_LARGA_ARCHIVO_PROTOCOLO.md'
OUTPUT = ROOT/'evidence/voice_archive_control01.json'

def main():
    if OUTPUT.exists(): raise ValueError('preserve archive control')
    source = runner.CONTROL/'nominal500.raw'
    controlp = ROOT/'evidence/voice_native_control01.json'
    auditp = ROOT/'evidence/voice_native_control_validation01.json'
    native = vco.read(auditp)
    estimates = probe.estimate()  # Replays native source/audit prerequisites.
    control = vco.read(controlp)
    if vco.sha(source) != control['run']['raw_sha256']:
        raise ValueError('admitted control raw required')
    inputs = [Path(__file__), Path(archive.__file__), Path(probe.__file__),
              ROOT/PROTOCOL, controlp, auditp]
    before = {p.relative_to(ROOT).as_posix():vco.sha(p) for p in inputs}
    report = dict(schema='rf-d/lossless-archive-control/v1', passed=False,
        native_control_sha256=vco.sha(controlp), native_audit_sha256=vco.sha(auditp),
        input_sha256=before, original_path=source.relative_to(ROOT).as_posix(),
        original_sha256=vco.sha(source), original_bytes=source.stat().st_size,
        original_ascii_sha256=vco.sha(runner.CONTROL/'nominal500.txt'),
        versions=dict(python=sys.version, platform=platform.platform(),
                      zlib_build=zlib.ZLIB_VERSION, zlib_runtime=zlib.ZLIB_RUNTIME_VERSION,
                      xz_codec='Python stdlib lzma FORMAT_XZ preset6 CHECK_CRC64'),
        trials={}, errors={}, selected_codec=None, estimates_are_not_bounds=True,
        max_workers=1, new_spice_solves=0, original_retained=True,
        long_note_admitted_locally=False, new_audio=False, physical_fidelity=False)
    runner.write(OUTPUT, report)
    for codec, suffix in zip(archive.CODECS, ('.gz','.xz')):
        target = source.with_name('nominal500.control.raw'+suffix)
        try:
            trial = archive.encode(source, target, codec)
            if trial['original_sha256'] != report['original_sha256'] or trial['original_bytes'] != report['original_bytes']:
                raise ValueError('control changed while archiving')
            trial['path'] = target.relative_to(ROOT).as_posix()
            density = trial['archive_bytes']/trial['original_bytes']
            cases = {n:dict(e, estimated_archive_bytes=math.ceil(e['estimated_long_export_bytes']*density))
                     for n,e in estimates['estimates'].items()}
            retained = sum(e['estimated_archive_bytes'] for e in cases.values())
            largest = max(e['estimated_long_export_bytes'] for e in cases.values())
            free = shutil.disk_usage(ROOT).free; margin = 2*1024**3
            trial['serial_preflight'] = dict(estimates=cases, density=density,
                estimated_retained_archive_bytes=retained, largest_intermediate_bytes=largest,
                margin_bytes=margin, required_free_bytes=retained+largest+margin,
                available_free_bytes=free, passed=free>=retained+largest+margin,
                estimates_are_not_bounds=True)
            report['trials'][codec] = trial
            print(codec, 'archive bytes:',trial['archive_bytes'], 'serial resources:',trial['serial_preflight']['passed'], flush=True)
        except Exception as exc:
            report['errors'][codec] = type(exc).__name__+': '+str(exc)
            if target.exists(): report.setdefault('failed_artifacts',{})[codec] = dict(path=target.relative_to(ROOT).as_posix(),sha256=vco.sha(target),bytes=target.stat().st_size)
        runner.write(OUTPUT, report)
    report['input_sha256_after'] = {p.relative_to(ROOT).as_posix():vco.sha(p) for p in inputs}
    report['source_retained_identity'] = dict(sha256=vco.sha(source), bytes=source.stat().st_size,
        ascii_sha256=vco.sha(runner.CONTROL/'nominal500.txt'))
    stable = before==report['input_sha256_after'] and report['source_retained_identity']==dict(
        sha256=report['original_sha256'],bytes=report['original_bytes'],ascii_sha256=report['original_ascii_sha256'])
    report['passed'] = stable and not report['errors'] and len(report['trials'])==2
    if report['passed']:
        for codec in archive.CODECS:
            if report['trials'][codec]['serial_preflight']['passed']:
                report['selected_codec']=codec; break
    report['serial_resources_admitted'] = report['passed'] and report['selected_codec'] is not None
    report['available_free_bytes_final'] = shutil.disk_usage(ROOT).free
    if report['selected_codec'] and report['available_free_bytes_final'] < report['trials'][report['selected_codec']]['serial_preflight']['required_free_bytes']:
        report['serial_resources_admitted']=False
    runner.write(OUTPUT, report)
    print('archive control:',report['passed'],'serial resources:',report['serial_resources_admitted'],flush=True)

if __name__=='__main__': main()
