"""Publish a completed serial campaign without changing its frozen producer."""
import argparse, base64, hashlib, json, re, subprocess, sys, time
from pathlib import Path
import voice_serial_long as serial
import voice_serial_archive as storage
import voice_full_note as note
from mixer_on_native_vectors import ROOT, sha
from validate_mixer_on_native import native_source_identity

QA = ROOT / 'evidence/voice_documentation_tests01.json'
SNAPSHOT = ROOT / 'evidence/voice_serial_documentation_snapshot01.json'
AUDIT = ROOT / 'evidence/voice_serial_audit_run01.json'
VALIDATION = ROOT / 'evidence/voice_serial_validation01.json'
OUTPUT = ROOT / 'evidence/voice_serial_release01.json'
DOCS = ('README.md', 'docs/PLAN.md', 'docs/MATRIZ_DE_FIDELIDAD.md')


def read(path):
    return json.loads(path.read_text(encoding='utf8'))


def write(path, value):
    with path.open('x', encoding='utf8', newline='\n') as f:
        f.write(json.dumps(value, indent=2) + '\n')


def final_bank():
    p = ROOT / 'evidence/voice_serial_runs01.json'
    b = read(p)
    if 'helper_sha256_after' not in b or b['decision'] == 'serial measurements pending':
        raise ValueError('completed producer required')
    if b['helper_sha256'] != serial.helpers() or b['helper_sha256_after'] != serial.helpers():
        raise ValueError('frozen campaign helpers changed')
    return p, b


def audit():
    p, b = final_bank()
    if AUDIT.exists() or VALIDATION.exists():
        raise ValueError('preserve the original audit attempt')
    validator = ROOT / 'tools/validate_voice_serial_bank.py'
    pins = {p.relative_to(ROOT).as_posix(): sha(p),
            validator.relative_to(ROOT).as_posix(): sha(validator),
            Path(__file__).relative_to(ROOT).as_posix(): sha(Path(__file__))}
    command = [sys.executable, '-B', str(validator)]
    start = time.perf_counter()
    process = subprocess.run(command, cwd=ROOT, capture_output=True, text=True,
                             encoding='utf8', timeout=3600)
    result = dict(schema='rf-d/serial-frozen-audit-run/v1', command=command,
                  exit_code=process.returncode, stdout=process.stdout, stderr=process.stderr,
                  wall_s=time.perf_counter()-start, source_sha256=pins,
                  source_sha256_after={n: sha(ROOT/n) for n in pins},
                  new_spice_solves=0, new_compiler_runs=0, new_audio=False)
    result['passed'] = (process.returncode == 0 and VALIDATION.exists()
                        and read(VALIDATION)['passed'] and result['source_sha256_after'] == pins)
    if VALIDATION.exists():
        result['validation_sha256'] = sha(VALIDATION)
    if not result['passed']:
        # Preserve source and the unchanged replay before any repair is attempted.
        result['failed_validator_source'] = validator.read_text(encoding='utf8')
        replay = subprocess.run(command, cwd=ROOT, capture_output=True, text=True,
                                encoding='utf8', timeout=3600)
        result['unchanged_replay'] = dict(exit_code=replay.returncode,
                                          stdout=replay.stdout, stderr=replay.stderr,
                                          validator_sha256=sha(validator), bank_sha256=sha(p))
    write(AUDIT, result)
    print(process.stdout + process.stderr, flush=True)
    print('frozen audit receipt:', result['passed'], flush=True)


def release():
    bankp, bank = final_bank()
    q = read(QA); snapshot = read(SNAPSHOT); a = read(AUDIT); v = read(VALIDATION)
    if not q['passed'] or snapshot['previous_qa_sha256'] != sha(QA):
        raise ValueError('inherited release lineage')
    if not a['passed'] or a['validation_sha256'] != sha(VALIDATION) or not v['passed'] or v['bank_sha256'] != sha(bankp):
        raise ValueError('frozen bank audit lineage')
    for n, h in a['source_sha256'].items():
        if sha(ROOT/n) != h or a['source_sha256_after'].get(n) != h:
            raise ValueError('audited campaign changed: ' + n)
    if set(snapshot['previous_bytes_base64']) != set(DOCS):
        raise ValueError('exact three-document snapshot required')
    for n, encoded in snapshot['previous_bytes_base64'].items():
        old = base64.b64decode(encoded, validate=True)
        if hashlib.sha256(old).hexdigest() != q['source_sha256'][n]:
            raise ValueError('historical documentation bytes: ' + n)
    for n, h in q['source_sha256'].items():
        if n not in DOCS and sha(ROOT/n) != h:
            raise ValueError('protected numerical input changed: ' + n)

    # The frozen auditor replays every measurement and comparison. Explicitly
    # close its separate electrical-error and final-decision fields here.
    expected = {}
    observation_allowed = (bank['observation_resources']['available_free_bytes']
                           >= bank['observation_resources']['required_free_bytes'])
    for name, r in bank['records'].items():
        if 'raw_sha256' not in r:
            expected[name] = 'solver produced no native export'
        if observation_allowed:
            if not r['trajectory_complete']:
                expected.setdefault(name, 'solver trajectory incomplete')
            elif name in bank['measurements']:
                m = bank['measurements'][name]
                if max(m['timing_balance_max_c'], m['output_balance_max_c']) > note.GATES['charge_c']:
                    expected[name] = 'charge gate rejected'
    if expected != bank['electrical_errors']:
        raise ValueError('electrical rejection classification')
    decision = ('serial long note admitted locally' if bank['long_note_admitted_locally'] else
                'serial bank incomplete due to resources/storage' if bank['resource_errors'] or bank['storage_errors'] else
                'serial long note rejected')
    if decision != bank['decision'] or bank['new_audio'] or bank['physical_fidelity'] or bank['real_time']:
        raise ValueError('final decision and claim scope')
    if v['long_note_admitted_locally'] != bank['long_note_admitted_locally']:
        raise ValueError('auditor admission mismatch')

    private = dict(q['private_input_sha256'])
    for name in bank['archives']:
        m, raw, target, manifest = storage.archive_identity(serial.WORK, name)
        if raw.exists() or m != bank['archives'][name] or sha(manifest) != bank['archive_manifest_sha256'][name]:
            raise ValueError('retired native archive identity')
        r = bank['records'][name]
        receipt = serial.WORK / (name + '.json')
        if serial.runner.six.canonical(read(receipt)) != serial.runner.six.canonical(r):
            raise ValueError('original private run receipt')
        for suffix in ('.cir', '.log', '.json', '.archive.json', storage.SUFFIX[m['codec']]):
            path = serial.WORK / (name + suffix)
            private[path.relative_to(ROOT).as_posix()] = sha(path)
    for n, h in private.items():
        if sha(ROOT/n) != h:
            raise ValueError('private dependency changed: ' + n)
    audio = q['previous_audio']
    if sha(ROOT/audio['path']) != audio['sha256'] or sha(ROOT/'references-local/ngspice46/runtime/Spice64/bin/ngspice_con.exe') != q['official_executable_sha256']:
        raise ValueError('historical listening/official executable changed')
    staged = subprocess.check_output(['git', 'diff', '--cached', '--name-only', '-z'], cwd=ROOT).decode().split('\0')
    publication = {p.relative_to(ROOT).as_posix() for p in
                   (QA, SNAPSHOT, AUDIT, VALIDATION, Path(__file__))}
    publication |= set(a['source_sha256']) | {'docs/VOZ_SERIAL_RESULTADOS.md',
                                             'docs/VCO1_NATIVO_PROTOCOLO.md'}
    names = sorted(set(q['source_sha256']) | publication |
                   {n for n in staged if n and ROOT/n != OUTPUT})
    sources = {n: sha(ROOT/n) for n in names}
    for n, h in sources.items():
        native_source_identity(n, h, subprocess.check_output(['git', 'show', ':'+n], cwd=ROOT))
    local = []
    for n in (*DOCS, 'docs/VOZ_SERIAL_RESULTADOS.md'):
        path = ROOT/n
        for link in re.findall(r'\]\(([^)]+)\)', path.read_text(encoding='utf8')):
            if link.startswith(('https:', 'http:', '#')):
                continue
            target = (path.parent/link.split('#')[0].strip('<>')).resolve()
            if not target.exists() and target != OUTPUT.resolve():
                raise ValueError('missing local publication target: ' + link)
            local.append(target.relative_to(ROOT).as_posix())
    after = {n: sha(ROOT/n) for n in names}
    if sources != after or any(sha(ROOT/n) != h for n, h in private.items()):
        raise ValueError('publication inputs changed')
    write(OUTPUT, dict(schema='rf-d/serial-long-release/v1', passed=True,
        source_sha256=sources, source_sha256_after=after, previous_qa_sha256=sha(QA),
        documentation_snapshot_sha256=sha(SNAPSHOT), frozen_audit_sha256=sha(AUDIT),
        serial_validation_sha256=sha(VALIDATION), bank_sha256=sha(bankp),
        checked_local_targets=sorted(set(local)), private_input_sha256=private,
        previous_audio=audio, official_executable_sha256=q['official_executable_sha256'],
        covered_test_count=q['covered_test_count'], native_test_count=0,
        inherited_test_count=q['covered_test_count'], inherited_tests_reexecuted=False,
        serial_bank_audited=True, campaign_spice_solves=bank['measured_spice_solves'],
        new_spice_solves_by_release=0, new_compiler_runs=0, new_audio=False,
        decision=decision, electrical_errors=expected,
        long_note_admitted_locally=bank['long_note_admitted_locally'],
        algorithms_changed=False, numerical_gates_changed=False,
        physical_fidelity=False, real_time=False))
    print('serial release QA:', q['covered_test_count'], 'inherited tests;',
          bank['measured_spice_solves'], 'campaign solves;', decision, flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--audit', action='store_true')
    parser.add_argument('--release', action='store_true')
    args = parser.parse_args()
    if args.audit == args.release:
        parser.error('choose exactly one of --audit or --release')
    audit() if args.audit else release()
