"""Direct input/loaded-port production admission, independent replay and inherited scope."""
import base64, hashlib, json, re, subprocess
from pathlib import Path
import mixer_chain_direct_vectors as oracle
from mixer_on_native_vectors import ROOT, sha
from validate_mixer_on_native import native_source_identity

OUTPUT = ROOT/'evidence/voice_mixer_direct_tests01.json'
DOCS = ('README.md', 'docs/PLAN.md', 'docs/MATRIZ_DE_FIDELIDAD.md')


def read(p):
    return json.loads(p.read_text(encoding='utf8'))


def main():
    if OUTPUT.exists():
        raise ValueError('preserve direct publication QA')
    qp = ROOT/'evidence/voice_serial_release02.json'; q = read(qp)
    vp = ROOT/'evidence/voice_mixer_direct_vectors01.json'; v = read(vp)
    ap = ROOT/'evidence/voice_mixer_direct_native01.json'; a = read(ap)
    sp = ROOT/'evidence/voice_mixer_direct_documentation01.json'; snapshot = read(sp)
    if not all(r['passed'] for r in (q, v, a)) or q['covered_test_count'] != 185:
        raise ValueError('required direct and inherited admission')
    if snapshot['previous_qa_sha256'] != sha(qp) or set(snapshot['previous_bytes_base64']) != set(DOCS):
        raise ValueError('current-document snapshot lineage')
    for n, encoded in snapshot['previous_bytes_base64'].items():
        if hashlib.sha256(base64.b64decode(encoded, validate=True)).hexdigest() != q['source_sha256'][n]:
            raise ValueError('historical current-document bytes: '+n)
    for n, h in q['source_sha256'].items():
        if n in DOCS:
            continue
        if n in (oracle.LIB, '.gitattributes'):
            old = subprocess.check_output(['git', 'show', oracle.BASE+':'+n], cwd=ROOT)
            native_source_identity(n, h, old)
            if (ROOT/n).read_bytes() != old+(oracle.EXPORT if n == oracle.LIB else oracle.ATTRS):
                raise ValueError('only direct exports/byte policies added: '+n)
        elif sha(ROOT/n) != h:
            raise ValueError('inherited numerical input changed: '+n)
    for measured in (v, a):
        if measured['source_sha256'] != measured['source_sha256_after']:
            raise ValueError('measured direct sources changed')
        for n, h in measured['source_sha256'].items():
            if n not in DOCS and sha(ROOT/n) != h:
                raise ValueError('measured direct input changed: '+n)
            if n in DOCS and h != q['source_sha256'][n]:
                raise ValueError('measured document snapshot differs')
    if v['gates'] != oracle.GATES or (v['rows'], v['columns'], v['port_rows'], v['port_columns']) != (192, 187, 12, 528) or v['fd_source_delta_v'] != .001 or v['native_seeds_used']:
        raise ValueError('frozen oracle definitions')
    pins = {n: sha(ROOT/n) for n in v['source_sha256']}
    cases, text, ports, porttext = oracle.fixtures()
    canonical = lambda value: json.dumps(value, sort_keys=True, separators=(',', ':'))
    if canonical(cases) != canonical(v['cases']) or canonical(ports) != canonical(v['ports']):
        raise ValueError('full uneliminated oracle replay')
    tp = ROOT/'evidence/voice_mixer_direct_vectors01.txt'; pp = ROOT/'evidence/voice_mixer_direct_port_vectors01.txt'
    if text.encode() != tp.read_bytes() or porttext.encode() != pp.read_bytes() or sha(tp) != v['text_sha256'] or sha(pp) != v['port_text_sha256']:
        raise ValueError('exact oracle tables')
    if pins != {n: sha(ROOT/n) for n in pins}:
        raise ValueError('oracle replay inputs changed')
    compiler = a['compiler']
    if sha(Path(compiler['path'])) != compiler['sha256'] or a['compiler_sha256_after'] != compiler['sha256']:
        raise ValueError('compiler identity')
    if not a['resource_passed'] or a['available_free_bytes'] < a['estimated_build_bytes']+a['margin_bytes'] or a['estimated_build_bytes'] != 128*1024**2 or a['margin_bytes'] != 2*1024**3:
        raise ValueError('production resource gate')
    if a['unchanged_replays'] or any(c['exit_code'] for c in a['commands']) or [c['kind'] for c in a['commands']] != ['compile', 'compile', 'test', 'compile', 'test', 'compile', 'test', 'compile', 'test']:
        raise ValueError('captured successful production commands')
    tests = '\n'.join(c['stdout'] for c in a['commands'] if c['kind'] == 'test')
    if re.findall(r'test result: ok\. (\d+) passed; 0 failed; 0 ignored; 0 measured; 0 filtered out;', tests) != ['4', '1', '2', '1']:
        raise ValueError('eight production tests')
    for label, length in (('DIRECT_ALLOCATION', 'steps=32'), ('DIRECT_PORT_ALLOCATION', 'solves=16')):
        measured = re.findall(label+r',dt=([^,\s]+),'+length+r',allocations=(\d+)', tests)
        if len(measured) != 3 or {float(t) for t, _ in measured} != {.5e-6, .25e-6, .125e-6} or any(int(count) for _, count in measured):
            raise ValueError('isolated full-processing heap gate')
    patterns = {
        'trajectory': r'DIRECT_ORACLE,cases=12,steps=192,max_node_v=([^,\s]+),max_current_a=([^,\s]+)',
        'shared': r'DIRECT_SHARED,cases=4,steps=64,max_node_v=([^,\s]+),max_current_a=([^,\s]+)',
        'port': r'DIRECT_PORT,cases=12,max_admittance_delta_s=([^,\s]+),max_node_gradient_delta=([^,\s]+)'}
    maxima = {}
    for name, pattern in patterns.items():
        match = re.search(pattern, tests)
        if not match:
            raise ValueError('captured direct maxima: '+name)
        values = list(map(float, match.groups())); limits = [1e-8, 1e-6] if name == 'port' else [1e-6, 1e-9]
        if any(not 0 <= x < limit for x, limit in zip(values, limits)):
            raise ValueError('direct measured gates: '+name)
        maxima[name] = values
    private = dict(q['private_input_sha256'])
    if len(a['outputs']) != 5:
        raise ValueError('library plus four test binaries')
    for item in a['outputs']:
        path = ROOT/item['path']
        if not path.resolve().is_relative_to((ROOT/'references-local/mixer-chain-direct-native01').resolve()) or path.stat().st_size != item['bytes'] or sha(path) != item['sha256']:
            raise ValueError('preserved direct production binary')
        private[item['path']] = item['sha256']
    for n, h in private.items():
        if sha(ROOT/n) != h:
            raise ValueError('private dependency changed: '+n)
    if sha(ROOT/q['previous_audio']['path']) != q['previous_audio']['sha256'] or sha(ROOT/'references-local/ngspice46/runtime/Spice64/bin/ngspice_con.exe') != q['official_executable_sha256']:
        raise ValueError('historical audio/official executable')
    staged = subprocess.check_output(['git', 'diff', '--cached', '--name-only', '-z'], cwd=ROOT).decode().split('\0')
    names = sorted(set(q['source_sha256']) | {qp.relative_to(ROOT).as_posix()} |
                   {n for n in staged if n and ROOT/n != OUTPUT})
    sources = {n: sha(ROOT/n) for n in names}
    for n, h in sources.items():
        native_source_identity(n, h, subprocess.check_output(['git', 'show', ':'+n], cwd=ROOT))
    local = []
    for n in (*DOCS, 'docs/MEZCLADOR_DIRECTO_PROTOCOLO.md', 'docs/MEZCLADOR_DIRECTO_RESULTADOS.md'):
        path = ROOT/n
        for link in re.findall(r'\]\(([^)]+)\)', path.read_text(encoding='utf8')):
            if link.startswith(('https:', 'http:', '#')):
                continue
            target = (path.parent/link.split('#')[0]).resolve()
            if not target.exists() and target != OUTPUT.resolve():
                raise ValueError('direct publication link missing: '+link)
            local.append(target.relative_to(ROOT).as_posix())
    after = {n: sha(ROOT/n) for n in names}
    if after != sources:
        raise ValueError('direct publication changed')
    OUTPUT.write_text(json.dumps(dict(schema='rf-d/mixer-direct-release/v1', passed=True,
        base_commit=oracle.BASE, previous_qa_sha256=sha(qp), source_sha256=sources,
        source_sha256_after=after, private_input_sha256=private,
        documentation_snapshot_sha256=sha(sp), oracle_sha256=sha(vp), production_sha256=sha(ap),
        numerical_maxima=maxima, cases=12, temporal_steps=192, source_port_cases=12,
        shared_domain_steps=64, covered_test_count=193, inherited_test_count=185, native_test_count=8,
        inherited_tests_reexecuted=False, old_native_algorithms_unchanged=True,
        new_direct_adapter=True, dt_domain_s=[.125e-6, 1e-3], checked_local_targets=sorted(set(local)),
        previous_audio=q['previous_audio'], official_executable_sha256=q['official_executable_sha256'],
        long_note_admitted_locally=False, new_spice_solves=0, new_audio=False,
        physical_fidelity=False, real_time=False), indent=2)+'\n', encoding='utf8', newline='\n')
    print('direct release: 193 covered, 8 executed + 185 inherited;', len(sources), 'inputs', flush=True)


if __name__ == '__main__':
    main()
