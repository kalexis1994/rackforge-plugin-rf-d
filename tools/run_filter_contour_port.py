"""Bounded native/original graph bank, preserving failures and unchanged replay."""
import base64
import hashlib
import json
import os
import shutil
import subprocess
import time
from pathlib import Path
from filter_contour_port_reference import audit

ROOT = Path(__file__).resolve().parents[1]
LIB = ROOT/'references-local/voice-assembly-public01/librf_d_circuit.rlib'
COMPILER = 'C:/Users/kalex/.rustup/toolchains/stable-x86_64-pc-windows-gnu/bin/rustc.exe'
OWN = ['crates/rf-d-circuit/src/filter_contour_port.rs',
       'tools/filter_contour_port_bank.rs', 'tools/filter_contour_port_reference.py',
       'tools/run_filter_contour_port.py', 'docs/CONTORNO_FILTRO_PUERTO_PROTOCOLO.md',
       'evidence/filter_contour_port_graph01.json', 'evidence/filter_contour_port_review01.json']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False)+'\n', encoding='utf8', newline='\n')


def main():
    assert sha(LIB) == '9dbada9779f30c4972b057befe092524d091d3444ea777206b618d701236385d'
    assert shutil.disk_usage(ROOT).free >= 1024**3
    attempt = 1
    while (ROOT/f'evidence/filter_contour_port_native{attempt:02d}.json').exists():
        attempt += 1
    out = ROOT/f'references-local/filter-contour-port{attempt:02d}'
    out.mkdir()
    sources = {n: sha(ROOT/n) for n in OWN}
    snapshots = {n: base64.b64encode((ROOT/n).read_bytes()).decode() for n in OWN}
    receipt = dict(schema='rf-d/filter-contour-port/native-v1', attempt=attempt,
        source_sha256=sources, library_path=LIB.relative_to(ROOT).as_posix(),
        library_sha256=sha(LIB), compiler=COMPILER, passed=False,
        output_directory=out.relative_to(ROOT).as_posix(), scenario='local-1mV', large_step_admitted=False)
    env = dict(os.environ, PATH='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+os.environ['PATH'])
    exe = out/'bank.exe'
    command = [COMPILER, '--edition=2021', '-C', 'opt-level=2', '-C', 'strip=symbols',
        '-A', 'dead_code', str(ROOT/'tools/filter_contour_port_bank.rs'),
        '--extern', 'rf_d_circuit='+str(LIB), '-o', str(exe)]
    started = time.monotonic()

    def run(command, label, timeout):
        result = subprocess.run(command, cwd=ROOT, env=env, timeout=timeout, capture_output=True)
        (out/(label+'.stdout')).write_bytes(result.stdout)
        (out/(label+'.stderr')).write_bytes(result.stderr)
        receipt[label] = dict(command=command, exit_code=result.returncode,
                             stdout_sha256=hashlib.sha256(result.stdout).hexdigest(),
                             stderr_sha256=hashlib.sha256(result.stderr).hexdigest())
        return result

    phase = 'compile'
    try:
        compiled = run(command, 'compile', 120)
        if compiled.returncode:
            raise RuntimeError('native compilation failed')
        phase = 'run'
        result = run([str(exe), '--local'], 'run', 300)
        if result.returncode:
            raise RuntimeError('native bank rejected')
        phase = 'reference'
        receipt['reference'] = audit(out/'run.stdout')
        receipt['passed'] = True
    except Exception as error:
        receipt['failed_phase'] = phase
        receipt['error'] = repr(error)
        write(out/'failed_sources.json', snapshots)
        assert sources == {n: sha(ROOT/n) for n in OWN}
        if phase == 'reference':
            try:
                audit(out/'run.stdout')
            except Exception as replay:
                receipt['unchanged_replay'] = dict(error=repr(replay), same_error=repr(error)==repr(replay))
            else:
                raise AssertionError('failed oracle did not reproduce')
        else:
            replay = run(command if phase == 'compile' else [str(exe), '--local'], 'replay', 300)
            receipt['unchanged_replay'] = dict(exit_code=replay.returncode,
                same_exit_code=replay.returncode == receipt[phase]['exit_code'],
                stdout_identical=sha(out/'replay.stdout') == sha(out/(phase+'.stdout')))
    receipt['elapsed_s'] = time.monotonic()-started
    receipt['source_unchanged'] = sources == {n: sha(ROOT/n) for n in OWN}
    receipt['library_unchanged'] = sha(LIB) == receipt['library_sha256']
    receipt['private_sha256'] = {p.relative_to(ROOT).as_posix(): sha(p) for p in out.iterdir() if p.is_file()}
    receipt['private_bytes'] = sum(p.stat().st_size for p in out.iterdir() if p.is_file())
    assert receipt['source_unchanged'] and receipt['library_unchanged']
    assert receipt['private_bytes'] <= 32*1024**2
    write(ROOT/f'evidence/filter_contour_port_native{attempt:02d}.json', receipt)
    print(json.dumps({k: v for k, v in receipt.items() if k not in ('source_sha256', 'private_sha256')}, indent=2))
    if not receipt['passed']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
