"""Admit the limited DC/local port; retain the rejected original large step."""
import base64
import csv
import hashlib
import json
import shutil
import subprocess
import traceback
from pathlib import Path
from run_filter_contour_port import ROOT, sha, write
from filter_contour_port_reference import audit as reference_audit
from validate_joint_charge_seed import local_links

OUT = 'evidence/filter_contour_port_tests01.json'
ATTR = (b'\n/crates/rf-d-circuit/src/filter_contour_port.rs text eol=lf\n'
        b'/tools/filter_contour_port_bank.rs text eol=lf\n'
        b'/evidence/filter_contour_port*.json text eol=lf\n')


def read(name):
    return json.loads((ROOT/name).read_text(encoding='utf8'))


def audit():
    before = read('evidence/filter_contour_port_before01.json')
    old = read(before['previous_qa'])
    assert old['passed'] and sha(ROOT/before['previous_qa']) == before['previous_qa_sha256']
    assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip() == before['base_commit']
    saved = {n: base64.b64decode(v) for n, v in before['mutable_original_b64'].items()}
    for n, h in old['source_sha256'].items():
        assert hashlib.sha256(saved[n] if n in saved else (ROOT/n).read_bytes()).hexdigest() == h, n
    for n in ['README.md', 'docs/PLAN.md', 'docs/MATRIZ_DE_FIDELIDAD.md']:
        assert (ROOT/n).read_bytes().startswith(saved[n]), n
    assert (ROOT/'.gitattributes').read_bytes() == saved['.gitattributes']+ATTR
    private = dict(old['private_input_sha256'])
    for n, h in private.items():
        assert sha(ROOT/n) == h, n
    review = read('evidence/filter_contour_port_review01.json')
    assert review['visual_review'] and not list((ROOT/'references-local/filter-contour-review01').glob('*.pdf'))
    for source in review['sources'].values():
        assert sha(ROOT/source['path']) == source['sha256']
        private[source['path']] = source['sha256']
    for n, h in review['private_sha256'].items():
        assert sha(ROOT/n) == h, n
        private[n] = h
    graph = read('evidence/filter_contour_port_graph01.json')
    assert len(graph['nodes']) == 9 and len(graph['ports']) == 8
    assert graph['r74_count'] == 1 and graph['old_imposed_v16_removed']
    assert graph['potentiometer']['endpoint_contacts_exact'] and graph['reference_original_cursor']
    receipts = [read(f'evidence/filter_contour_port_native{k:02d}.json') for k in range(1, 6)]
    assert not receipts[0]['passed'] and receipts[0]['failed_phase'] == 'compile'
    assert receipts[0]['compile']['stderr_sha256'] == receipts[0]['replay']['stderr_sha256']
    assert receipts[0]['unchanged_replay']['same_exit_code'] and receipts[0]['unchanged_replay']['stdout_identical']
    assert not receipts[1]['passed'] and receipts[1]['failed_phase'] == 'reference'
    assert receipts[1]['unchanged_replay']['same_error']
    assert all(r['passed'] and r['scenario'] == 'local-1mV' and not r['large_step_admitted'] for r in receipts[2:])
    for r in receipts:
        assert r['source_unchanged'] and r['library_unchanged'] and r['elapsed_s'] <= 300
        assert sha(ROOT/r['library_path']) == r['library_sha256'] == before['protected_library_sha256']
        for n, h in r['private_sha256'].items():
            assert sha(ROOT/n) == h, n
            private[n] = h
        if not r['passed']:
            snapshots = read(r['output_directory']+'/failed_sources.json')
            for n, b64 in snapshots.items():
                assert hashlib.sha256(base64.b64decode(b64)).hexdigest() == r['source_sha256'][n], n
    final = receipts[-1]
    for n, h in final['source_sha256'].items():
        assert sha(ROOT/n) == h, n
    metrics = reference_audit(ROOT/final['output_directory']/'run.stdout')
    assert metrics == final['reference']
    assert metrics['atomic_rejections'] == 24 and metrics['fd_stamp_entries'] == 45084
    assert metrics['fd_port_entries'] == 9984 and metrics['original_dc_rows']+metrics['original_dynamic_rows'] == 1520
    # A functional gate from the documented DC bank, independent of Newton norms.
    dc = {}
    traces = {}
    for row in csv.reader((ROOT/final['output_directory']/'run.stdout').read_text().splitlines()):
        if row[0] == 'DC':
            v = list(map(float, row[1:]))
            a, timing, reset, cutoff = v[:4]
            if reset == .01 and cutoff == .5 and timing in [.85, 3., 6.]:
                dc[(a, timing)] = dict(out_v=v[7], base_q26_v=v[9], tail_a=v[15])
        if row[0] == 'STEP':
            v = list(map(float, row[1:]))
            c11, dt, k, timing = v[:4]
            clock = int(k)*round(dt*1e9)
            assert timing == (.85 if clock <= 32000 or clock > 96000 else .851)
            traces.setdefault((c11, dt), set()).add(clock)
    for timing in [.85, 3., 6.]:
        assert abs(dc[(0., timing)]['tail_a']-dc[(0., .85)]['tail_a']) <= 1e-15
        assert dc[(0., timing)]['tail_a'] < dc[(.5, timing)]['tail_a'] < dc[(1., timing)]['tail_a']
        assert dc[(0., timing)]['out_v'] > dc[(1., timing)]['out_v']
    for a in [.5, 1.]:
        assert dc[(a, .85)]['tail_a'] < dc[(a, 3.)]['tail_a'] < dc[(a, 6.)]['tail_a']
    clocks = sum(len(traces[(cap, 8e-6)] & traces[(cap, 4e-6)]) for cap in [0., 47e-12])
    assert clocks == 32
    compiler = read('evidence/voice_assembly_public01.json')['compiler']
    assert sha(Path(compiler['path'])) == compiler['sha256']
    size = sum((ROOT/n).stat().st_size for n in set(private)-set(old['private_input_sha256']))
    assert size <= 32*1024**2 and shutil.disk_usage(ROOT).free >= 1024**3
    staged = subprocess.check_output(['git', 'diff', '--cached', '--name-only'], cwd=ROOT, text=True).splitlines()
    assert OUT in staged
    names = set(old['source_sha256']) | {before['previous_qa']} | (set(staged)-{OUT})
    sources = {n: sha(ROOT/n) for n in sorted(names)}
    for n in set(staged)-{OUT}:
        blob = subprocess.check_output(['git', 'show', ':'+n], cwd=ROOT)
        assert hashlib.sha256(blob).hexdigest() == sources[n], n
    r = dict(schema='rf-d/filter-contour-port/admission-v1', passed=True,
        base_commit=before['base_commit'], previous_qa_sha256=before['previous_qa_sha256'],
        source_sha256=sources, source_sha256_after=sources, private_input_sha256=private,
        protected_public_sources=len(old['source_sha256']), protected_private_inputs=len(old['private_input_sha256']),
        new_private_bytes=size, original_circuit_sources_unchanged=True,
        dc_port_admitted=True, local_dynamic_port_admitted=True, original_full_stress_admitted=False,
        large_step_admitted=False, complete_filter_contour=False, integrated_voice=False,
        new_continuous_history_duration_s=0, new_audio=False,
        native_receipt='evidence/filter_contour_port_native05.json', reference=metrics,
        original_dc_rows=560, original_dynamic_rows=960, new_independent_nonlinear_rows=1520,
        shared_clock_states=clocks, native_state_coordinates=9, port_coordinates=8,
        provisional_checks=96, replayed_local_steps=96, atomic_rollbacks=24,
        functional_dc={str(k): v for k, v in dc.items()}, compiler=compiler,
        new_library_compile=False, new_cargo_cache=False,
        inherited_test_count=255, inherited_tests_reexecuted=False,
        inherited_python_test_definitions=2, new_unit_test_definitions=0,
        physical_fidelity=False, real_time=False, heap_measured=False, deadline_measured=False,
        rejected_attempts=['evidence/filter_contour_port_native01.json', 'evidence/filter_contour_port_native02.json'],
        local_markdown_links=local_links([n for n in staged if n.endswith('.md')]))
    inherited = ['previous_audio', 'native_listening', 'native_chain_listening',
        'official_executable_sha256', 'conditioned_transient_listening', 'sustained_listening',
        'sustained_diagnostic', 'release_listening', 'release_reference', 'release_review',
        'decay_listening', 'decay_reference', 'extended_reference', 'extended_listening',
        'public_block_library_sha256', 'public_assembly_library_sha256', 'public_assembly_library_path',
        'public_assembly_family_admitted', 'tail_reference', 'tail_listening', 'retrigger_reference',
        'retrigger_listening', 'cutoff_reference', 'cutoff_listening', 'cutoff_ab_reference', 'cutoff_ab_listening']
    for key in inherited:
        r[key] = old[key]
    return r


def main():
    try:
        result = audit()
    except Exception:
        first = traceback.format_exc()
        try:
            audit()
        except Exception:
            replay = traceback.format_exc()
        else:
            replay = 'unexpected pass'
        attempt = 1
        while (ROOT/f'evidence/filter_contour_port_qa_failure{attempt:02d}.json').exists():
            attempt += 1
        write(ROOT/f'evidence/filter_contour_port_qa_failure{attempt:02d}.json',
            dict(passed=False, failure=first, replay=replay,
                 source_base64=base64.b64encode(Path(__file__).read_bytes()).decode()))
        raise
    write(ROOT/OUT, result)
    print('FILTER_CONTOUR_PORT_QA', result['passed'], len(result['source_sha256']),
          len(result['private_input_sha256']), result['new_private_bytes'])


if __name__ == '__main__':
    main()
