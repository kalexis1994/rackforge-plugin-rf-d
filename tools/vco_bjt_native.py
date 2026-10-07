"""Build production-root four-terminal BJT tests, preserving all attempts."""
import argparse, json, os, shutil, subprocess, time
from pathlib import Path
from vco_bjt_vectors import ROOT, sha


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--attempt', type=int, required=True)
    number = parser.parse_args().attempt
    if not 1 <= number <= 99:
        raise ValueError('attempt 1..99')
    out = ROOT/f'evidence/voice_vco_bjt_native{number:02d}.json'
    work = ROOT/f'references-local/vco-bjt-native{number:02d}'
    if out.exists() or work.exists():
        raise ValueError('preserve direct native attempt')
    vectorp = ROOT/'evidence/voice_vco_bjt_vectors01.json'
    vectors = json.loads(vectorp.read_text(encoding='utf8'))
    if not vectors['passed'] or vectors['source_sha256'] != vectors['source_sha256_after']:
        raise ValueError('bound oracle required')
    for n, h in vectors['source_sha256'].items():
        if sha(ROOT/n) != h:
            raise ValueError('measured oracle changed: '+n)
    targets = ('vco_bjt', 'vco_bjt_no_alloc')
    names = set(vectors['source_sha256']) | {vectorp.relative_to(ROOT).as_posix(),
        'evidence/voice_vco_bjt_vectors01.txt', 'evidence/voice_vco_bjt_neighbors01.txt',
        'evidence/voice_vco_bjt_spice02.json', 'evidence/voice_vco_bjt_spice02.txt',
        'tools/vco_bjt_spice.py', 'tools/vco_bjt_spice02.py', 'evidence/voice_vco_bjt_spice01.json',
        Path(__file__).relative_to(ROOT).as_posix()} | {f'crates/rf-d-circuit/tests/{n}.rs' for n in targets}
    before = {n: sha(ROOT/n) for n in sorted(names)}
    spice = json.loads((ROOT/'evidence/voice_vco_bjt_spice02.json').read_text(encoding='utf8'))
    if not spice['passed'] or spice['source_sha256'] != spice['source_sha256_after']:
        raise ValueError('complete independent SPICE admission')
    for n, h in spice['source_sha256'].items():
        if sha(ROOT/n) != h:
            raise ValueError('measured SPICE input changed '+n)
    for n, h in vectors['private_input_sha256'].items():
        if sha(ROOT/n) != h:
            raise ValueError('primary device source changed '+n)
    old = json.loads((ROOT/'evidence/voice_mixer_chain_port_native01.json').read_text(encoding='utf8'))
    compiler = old['compiler']; rustc = Path(compiler['path'])
    if sha(rustc) != compiler['sha256']:
        raise ValueError('pinned compiler required')
    free = shutil.disk_usage(ROOT).free; estimate = 64*1024**2; margin = 2*1024**3
    report = dict(schema='rf-d/vco-bjt-production/v1', passed=False, source_sha256=before,
        compiler=compiler, available_free_bytes=free, estimated_build_bytes=estimate, margin_bytes=margin,
        resource_passed=free >= estimate+margin, estimates_are_not_bounds=True, commands=[],
        unchanged_replays=[], outputs=[], new_spice_solves=0, new_audio=False,
        private_input_sha256=vectors['private_input_sha256'])
    def write():
        out.write_text(json.dumps(report, indent=2)+'\n', encoding='utf8', newline='\n')
    write()
    if not report['resource_passed']:
        print('direct build storage gate rejected', flush=True); return
    work.mkdir(); library = work/'librf_d_circuit.rlib'
    env = os.environ.copy(); env['PATH'] = 'C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+env['PATH']
    commands = [('compile', [str(rustc), '--edition=2021', '--crate-type', 'lib', '--crate-name',
                            'rf_d_circuit', 'crates/rf-d-circuit/src/lib.rs', '-o', str(library)])]
    for name in targets:
        executable = work/(name+'.exe')
        commands.extend([('compile', [str(rustc), '--edition=2021', '--test', '--crate-name', name,
            f'crates/rf-d-circuit/tests/{name}.rs', '--extern', 'rf_d_circuit='+str(library), '-o', str(executable)]),
            ('test', [str(executable), '--nocapture', '--test-threads=1'])])
    start = time.perf_counter()
    try:
        for kind, command in commands:
            p = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, text=True, encoding='utf8', timeout=900)
            entry = dict(kind=kind, command=command, exit_code=p.returncode, stdout=p.stdout, stderr=p.stderr)
            report['commands'].append(entry); write()
            if kind == 'test' or p.returncode:
                print(p.stdout+p.stderr, flush=True)
            if p.returncode:
                report['failed_source_text'] = {n: (ROOT/n).read_text(encoding='utf8')
                    for n in before if n.endswith(('.rs', '.py', '.md'))}
                replay = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, text=True,
                                        encoding='utf8', timeout=900)
                report['unchanged_replays'].append(dict(command=command, exit_code=replay.returncode,
                    stdout=replay.stdout, stderr=replay.stderr,
                    source_sha256={n: sha(ROOT/n) for n in before}))
                raise RuntimeError('direct production '+kind+' rejected')
        report['passed'] = True
    except (OSError, RuntimeError, subprocess.TimeoutExpired) as exc:
        report['error'] = str(exc)
    report.update(wall_s=time.perf_counter()-start, source_sha256_after={n: sha(ROOT/n) for n in before},
                  compiler_sha256_after=sha(rustc),
                  private_input_sha256_after={n: sha(ROOT/n) for n in vectors['private_input_sha256']})
    report['outputs'] = [dict(path=p.relative_to(ROOT).as_posix(), sha256=sha(p), bytes=p.stat().st_size)
                         for p in work.glob('*') if p.is_file()]
    report['passed'] = report['passed'] and before == report['source_sha256_after'] and compiler['sha256'] == report['compiler_sha256_after']
    write(); print('direct production attempt:', report['passed'], flush=True)


if __name__ == '__main__':
    main()
