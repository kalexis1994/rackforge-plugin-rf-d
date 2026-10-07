"""Independent full BUS/cursor trajectories and source-port roots at 500/250/125 ns."""
import json, time, traceback
from pathlib import Path
import numpy as np
from mixer_on_native_vectors import ROOT, sha, network
from mixer_chain_vectors import solve
from circuit66_dc_vectors import dc_evaluator, solve_dc
from circuit66_vca_release_probes import transient_evaluator
from circuit66_r21_vectors import charges
from cutoff_j7_vectors import setup
from validate_mixer_on_native import native_source_identity
import mixer_panel_bus_reference as panel
import subprocess

PROTOCOL = 'docs/MEZCLADOR_DIRECTO_PROTOCOLO.md'
PREFIX = 'evidence/voice_mixer_direct'
GATES = dict(node_v=1e-6, current_a=1e-9, kcl_a=1e-11, correction_v=1e-8,
             jacobian_absolute=1e-8, jacobian_relative=2e-5,
             admittance_absolute_s=1e-8, admittance_relative=1e-3,
             gradient_absolute=1e-6, gradient_relative=1e-3)
LIB = 'crates/rf-d-circuit/src/lib.rs'
EXPORT = b'\npub mod mixer_chain66_direct;\npub mod mixer_chain_port_direct;\n'
ATTRS = (b'/crates/rf-d-circuit/src/mixer_chain66_direct.rs text eol=lf\n'
         b'/crates/rf-d-circuit/src/mixer_chain_port_direct.rs text eol=lf\n'
         b'/crates/rf-d-circuit/tests/mixer_chain_direct.rs text eol=lf\n'
         b'/crates/rf-d-circuit/tests/mixer_chain_direct_no_alloc.rs text eol=lf\n'
         b'/crates/rf-d-circuit/tests/mixer_port_direct.rs text eol=lf\n'
         b'/crates/rf-d-circuit/tests/mixer_port_direct_no_alloc.rs text eol=lf\n'
         b'/evidence/voice_mixer_direct_vectors01.txt -text\n'
         b'/evidence/voice_mixer_direct_port_vectors01.txt -text\n')
BASE = '272221d0c719df76e033c4af74c7b87b1011051b'


def read(path):
    return json.loads(path.read_text(encoding='utf8'))


def inherited():
    path = ROOT/'evidence/voice_serial_release02.json'; q = read(path)
    if not q['passed'] or q['covered_test_count'] != 185:
        raise ValueError('previous admitted native scope required')
    for n, h in q['source_sha256'].items():
        if n in (LIB, '.gitattributes'):
            old = subprocess.check_output(['git', 'show', BASE+':'+n], cwd=ROOT)
            native_source_identity(n, h, old)
            if (ROOT/n).read_bytes() != old+(EXPORT if n == LIB else ATTRS):
                raise ValueError('only new direct exports and byte policies allowed: '+n)
        elif sha(ROOT/n) != h:
            raise ValueError('protected input changed: '+n)
    return q, path


def source_pins():
    q, path = inherited()
    names = set(q['source_sha256']) | {path.relative_to(ROOT).as_posix(), PROTOCOL,
        Path(__file__).relative_to(ROOT).as_posix(),
        'crates/rf-d-circuit/src/mixer_chain66_direct.rs',
        'crates/rf-d-circuit/src/mixer_chain_port_direct.rs'}
    return {n: sha(ROOT/n) for n in sorted(names)}


def full_step(values, history, g, sources, interval, seed):
    b = dict(bus_v=0., loudness_v=2., q21_base_v=2., r21_lower_ohm=2000., dt_s=interval)
    core = transient_evaluator(values, history, b); gc = 10e-6/interval
    def evaluate(x):
        rr, _ = core(list(x[:66])); rr[6] += gc*x[66]
        resistive = g @ np.array([*sources, *x[66:]])
        return [*rr, float(resistive[5])-gc*(x[6]-x[66]-history['capacitor_v'][5]),
                *resistive[6:].tolist()]
    x, kcl, correction = solve(seed, evaluate)
    current = g @ np.array([*sources, *x[66:]])
    caps = charges(x[:66], x[66]); series = 25500.
    i10 = gc/(1+gc*series)*(x[22]-x[7]-history['c10_v'])
    return dict(source_v=sources, node_v=x[:66], bus_v=x[66], capacitor_v=caps,
                c10_v=x[22]-x[7]-series*i10,
                current_a=[*current[:5].tolist(), gc*(x[6]-x[66]-history['capacitor_v'][5])],
                kcl_a=kcl, correction_v=correction), x


def fixtures():
    cases = []; lines = []; ports = []; port_lines = []
    for r61 in (200, 200000):
        values = setup(r61)
        initial, _, _ = solve_dc(list(values[5]['node_v']), dc_evaluator(values, values[4]))
        for mask in (1, 31):
            alpha = [.5]*4
            g, _ = network([bool(mask & (1 << i)) for i in range(5)], alpha, panel._sources())
            g = np.array(g, dtype=float)
            for interval in (.5e-6, .25e-6, .125e-6):
                prior = initial+[0.]*(len(g)-5)
                history = dict(node_v=initial, capacitor_v=charges(initial, 0.), c10_v=initial[22]-initial[7])
                case = dict(r61_ohm=r61, mask=mask, alpha=alpha, dt_s=interval,
                            initial_node_v=initial, initial_history=history, rows=[])
                for step in range(16):
                    src = [(.08, -.05, .03, -.02, .04)[i]*(1 if step % 8 < 4 else -1) for i in range(5)]
                    row, x = full_step(values, history, g, src, interval, prior)
                    case['rows'].append(row)
                    flat = [r61, mask, *alpha, interval, *src, *history['node_v'],
                            *history['capacitor_v'], history['c10_v'], *x[:66], x[66],
                            *row['capacitor_v'], row['c10_v'], *row['current_a']]
                    lines.append(' '.join(format(float(v), '.17e') for v in flat))
                    if step == 3:
                        matrix = np.empty((5, 5)); gradient = np.empty((66, 5)); bus = []
                        for col in range(5):
                            plus = src.copy(); minus = src.copy(); plus[col] += .001; minus[col] -= .001
                            rp, xp = full_step(values, history, g, plus, interval, prior)
                            rm, xm = full_step(values, history, g, minus, interval, prior)
                            matrix[:, col] = (np.array(rp['current_a'][:5])-rm['current_a'][:5])/.002
                            gradient[:, col] = (np.array(xp[:66])-xm[:66])/.002
                            bus.append((xp[66]-xm[66])/.002)
                        ports.append(dict(r61_ohm=r61, mask=mask, alpha=alpha, dt_s=interval,
                            source_v=src, previous=history, node_v=x[:66], bus_v=x[66],
                            current_a=row['current_a'][:5], admittance_s=matrix.tolist(),
                            node_gradient_v_per_v=gradient.tolist(), bus_gradient_v_per_v=bus,
                            kcl_a=row['kcl_a'], correction_v=row['correction_v']))
                        flatp = [r61, mask, *alpha, interval, *src, *history['node_v'],
                            *history['capacitor_v'], history['c10_v'], *x[:66], x[66],
                            *row['current_a'][:5], *matrix.flatten(), *gradient.flatten(), *bus]
                        port_lines.append(' '.join(format(float(v), '.17e') for v in flatp))
                    prior = x
                    history = dict(node_v=x[:66], capacitor_v=row['capacitor_v'], c10_v=row['c10_v'])
                cases.append(case)
                print('direct full nodal oracle:', r61, mask, interval, '16 steps + 10 displaced roots', flush=True)
    return cases, '\n'.join(lines)+'\n', ports, '\n'.join(port_lines)+'\n'


def main():
    output = ROOT/(PREFIX+'_vectors01.json'); text = ROOT/(PREFIX+'_vectors01.txt')
    porttext = ROOT/(PREFIX+'_port_vectors01.txt'); rejection = ROOT/(PREFIX+'_oracle_rejection01.json')
    if any(p.exists() for p in (output, text, porttext, rejection)):
        raise ValueError('preserve direct oracle attempt')
    before = source_pins(); start = time.perf_counter()
    try:
        cases, data, ports, pdata = fixtures()
        after = {n: sha(ROOT/n) for n in before}
        if before != after:
            raise ValueError('oracle sources changed')
    except Exception:
        failure = traceback.format_exc()
        preserved = {n: (ROOT/n).read_text(encoding='utf8') for n in before if n.endswith(('.py', '.rs', '.md'))}
        try:
            fixtures(); replay = 'completed without repeating the exception'
        except Exception:
            replay = traceback.format_exc()
        rejection.write_text(json.dumps(dict(source_sha256=before, failed_source_text=preserved,
            failure=failure, unchanged_replay=replay, source_sha256_after={n: sha(ROOT/n) for n in before}), indent=2)+'\n',
            encoding='utf8', newline='\n')
        raise
    text.write_text(data, encoding='utf8', newline='\n'); porttext.write_text(pdata, encoding='utf8', newline='\n')
    output.write_text(json.dumps(dict(schema='rf-d/mixer-direct-oracle/v1', passed=True,
        source_sha256=before, source_sha256_after=after, cases=cases, ports=ports, gates=GATES,
        rows=192, columns=187, port_rows=12, port_columns=528, fd_source_delta_v=.001,
        text_sha256=sha(text), port_text_sha256=sha(porttext), wall_s=time.perf_counter()-start,
        native_seeds_used=False, new_spice_solves=0, new_audio=False, physical_fidelity=False, real_time=False), indent=2)+'\n',
        encoding='utf8', newline='\n')
    print('direct oracle: 12 scenes, 192 steps and 12 source ports', flush=True)


if __name__ == '__main__':
    main()
