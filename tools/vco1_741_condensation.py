"""Exact Decimal100 Newton port condensation; no dynamic model reduction."""
import argparse, json, sys, time
from decimal import Decimal, localcontext
from pathlib import Path
import vco1_increment_circuit as circuit
from vco1_newton_reference import ROOT, sha
op = circuit.op
Z = Decimal(0)
ONE = Decimal(1)
GATE = Decimal('1e-60')


def require(ok, msg):
    if not ok:
        raise ValueError(msg)


def lu_many(matrix, rhs):
    """Row scaled pivots, single factorization; column RHS stored per row."""
    a = [row[:] for row in matrix]
    b = [row[:] for row in rhs]
    n, columns = len(a), len(b[0])
    scale = [max(map(abs, row)) for row in a]
    require(all(scale), 'zero row in condensed factor')
    for k in range(n):
        p = max(range(k, n), key=lambda i: abs(a[i][k]) / scale[i])
        a[k], a[p] = a[p], a[k]
        b[k], b[p] = b[p], b[k]
        scale[k], scale[p] = scale[p], scale[k]
        require(a[k][k] != 0, 'singular condensed factor')
        for i in range(k + 1, n):
            if not a[i][k]:
                continue
            f = a[i][k] / a[k][k]
            a[i][k] = Z
            for q in range(k + 1, n):
                a[i][q] -= f * a[k][q]
            for q in range(columns):
                b[i][q] -= f * b[k][q]
    x = [[Z] * columns for _ in range(n)]
    for i in range(n - 1, -1, -1):
        for q in range(columns):
            x[i][q] = (b[i][q] - sum(a[i][k] * x[k][q] for k in range(i + 1, n))) / a[i][i]
    return x


def matvec(a, x):
    return [sum(v * w for v, w in zip(row, x)) for row in a]


def maximum(values):
    return max(map(abs, values), default=Z)


def board_ground_gradient(x, dt, inv):
    """Explicit grounded incidences of the board, excluding both opamp cards."""
    result = [Z] * 134
    ix = lambda n: 134 if n == '0' else inv['nodes'].index(n)
    trims = ['RR8_HIGH','RR8_LOW','RR11_ACTIVE']
    vs = 0
    for original in inv['lines']:
        w = original[:]
        if w[0] in ('VR8_HIGH','VR8_LOW','VR11_ACTIVE'):
            w[0] = 'R' + w[0][1:]
        kind = w[0][0]
        if kind in 'RCVI':
            a,b = ix(w[1]),ix(w[2])
            sign = (ONE if a == 134 else Z) - (ONE if b == 134 else Z)
            if kind == 'V' or (kind == 'R' and w[0] in trims):
                row = 98 + vs if kind == 'V' else 131 + trims.index(w[0])
                vs += int(kind == 'V')
                result[row] += sign
            elif sign and (kind == 'R' or kind == 'C' and dt):
                value = op.D(float(w[3]))
                g = ONE/value if kind == 'R' else value/op.D(dt)
                if a != 134:result[a] += sign*g
                if b != 134:result[b] -= sign*g
        elif kind in 'QJ':
            nodes = [ix(n) for n in w[1:4]] + ([134] if kind == 'Q' else [])
            if 134 not in nodes:continue
            z = [Z if i == 134 else x[i] for i in nodes]
            out = circuit.bjt_reference(1 if w[4]=='LAB_NPN' else -1,z,z,dt or 125e-9) if kind=='Q' else circuit.jfet_reference(z,z,dt or 125e-9)
            size = len(nodes)
            start = 3*size+(size*size if dt else 0)
            for a,i in enumerate(nodes):
                if i != 134:continue
                for b,k in enumerate(nodes):
                    if k != 134:result[k] += out[start+a*size+b]
    return result


def port(x, previous, dt):
    history = op.memory(previous)
    f, j, candidate, ground = op.reference_decimal(x, dt, history)
    # Derivative of exactly linear history incidence. No new physical constants.
    hist = []
    for k in range(5):
        h = history[:]
        h[k] += ONE
        ff, _, _, _ = op.reference_decimal(x, dt, h)
        hist.append([v - w for v, w in zip(ff, f)])
    hrows = [[hist[k][i] for k in range(5)] for i in range(37)]
    interior = [row[5:] for row in j[5:]]
    rhs = [j[i][:5] + hrows[i] + [f[i]] for i in range(5, 37)]
    response = lu_many(interior, rhs)
    offset = [-row[10] for row in response]
    gradient = [[-v for v in row[:5]] for row in response]
    memory_gradient = [[-v for v in row[5:10]] for row in response]
    eff = [f[i] + sum(j[i][k + 5] * offset[k] for k in range(32)) for i in range(5)]
    y = [[j[i][q] + sum(j[i][k + 5] * gradient[k][q] for k in range(32)) for q in range(5)] for i in range(5)]
    b = [[hrows[i][q] + sum(j[i][k + 5] * memory_gradient[k][q] for k in range(32)) for q in range(5)] for i in range(5)]
    # Only two collector gmin returns in the original card go to global ground.
    gg = [Z] * 37
    for node in (5, 6):
        gg[op.NODES.index(node)] = -op.D(1e-12)
    ground_eff = ground + sum(gg[k + 5] * offset[k] for k in range(32))
    ground_y = [sum(gg[k + 5] * gradient[k][q] for k in range(32)) for q in range(5)]
    ground_b = [sum(gg[k + 5] * memory_gradient[k][q] for k in range(32)) for q in range(5)]
    return dict(f=f, j=j, candidate=candidate, history=history, ground=ground,
                offset=offset, gradient=gradient, memory_gradient=memory_gradient,
                effective=eff, y=y, b=b, hrows=hrows, ground_effective=ground_eff,
                ground_y=ground_y, ground_b=ground_b)


def check_port(x, previous, dt, p):
    # Absolute-pivot full 37-row equations with five imposed port rows.
    j = [row[:] for row in p['j']]
    for i in range(5):
        j[i] = [ONE if k == i else Z for k in range(37)]
    offsets = op.dense([row[:] for row in j], [Z] * 5 + [-v for v in p['f'][5:]])
    error = maximum(a - b for a, b in zip(offsets[5:], p['offset']))
    for q in range(10):
        rhs = [ONE if i == q else Z for i in range(5)] + [Z] * 32 if q < 5 else [Z] * 5 + [-row[q - 5] for row in p['hrows'][5:]]
        independent = op.dense([row[:] for row in j], rhs)
        inside = p['gradient'] if q < 5 else p['memory_gradient']
        error = max(error, maximum(independent[k + 5] - inside[k][q % 5] for k in range(32)))
        currents = matvec(p['j'][:5], independent)
        if q >= 5:
            currents = [v + p['hrows'][i][q - 5] for i, v in enumerate(currents)]
        expected = p['y'] if q < 5 else p['b']
        error = max(error, maximum(currents[i] - expected[i][q % 5] for i in range(5)))
    charge_balance = abs(sum(p['effective']) + p['ground_effective'])
    derivative_balance = maximum([sum(row[q] for row in p['y']) + p['ground_y'][q] for q in range(5)] + [sum(row[q] for row in p['b']) + p['ground_b'][q] for q in range(5)])
    # Linear common-mode identity, constants read from primary card, not fitted.
    card = {w[0]: w for w in op.card()}
    gain = op.D(card['G4'][7])
    resistance = op.D(card['R13'][4])
    inductance = op.D(card['L2'][4])
    eos = op.D(card['EOS'][6])
    u = (x[0] + x[1] - x[2] - x[3]) / 2
    il = -gain * u
    factor = gain * resistance + (gain * inductance / op.D(dt) if dt else Z)
    base = x[0] + eos + resistance * gain * u
    if dt:
        base -= inductance * (il - p['history'][3]) / op.D(dt)
    base_local = op.NODES.index(7)
    common_error = abs(x[base_local] + p['offset'][base_local - 5] - base)
    expected = [ONE + factor / 2, factor / 2, -factor / 2, -factor / 2, Z]
    common_error = max(common_error, maximum(a - b for a, b in zip(p['gradient'][base_local - 5], expected)))
    expected_h = [Z, Z, Z, inductance / op.D(dt) if dt else Z, Z]
    common_error = max(common_error, maximum(a - b for a, b in zip(p['memory_gradient'][base_local - 5], expected_h)))
    require(max(error, charge_balance, derivative_balance, common_error) <= GATE, 'port or common-mode identity')
    return dict(full37_comparison_max=str(error),current_balance_max_a=str(charge_balance),
                derivative_balance_max=str(derivative_balance),common_mode_identity_max=str(common_error),
                l2_g4_time_s=str(gain * inductance),base_input_factor=str(factor),
                base_history_l2_v_per_a=str(expected_h[3]),five_terminal_currents_affine_a=list(map(str,p['effective'])),
                admittance_s=[[str(v) for v in row] for row in p['y']],memory_derivative=[[str(v) for v in row] for row in p['b']],
                ground_effective_a=str(p['ground_effective']),ground_voltage_gradient=list(map(str,p['ground_y'])),
                ground_memory_gradient=list(map(str,p['ground_b'])))


def coupled(x, dt, controls, inv):
    f, j, ground = circuit.reference_decimal(x, x, dt, controls)
    maps = inv['opamp_maps']
    eliminated = {k for m in maps for k in m[5:]}
    retained = [k for k in range(134) if k not in eliminated]
    lookup = {k: i for i, k in enumerate(retained)}
    require(len(retained) == 70 and len(eliminated) == 64, 'partition count')
    s = [[j[i][k] for k in retained] for i in retained]
    residual = [f[i] for i in retained]
    ports, details = [], []
    for m in maps:
        q = [Z if k == 134 else x[k] for k in m]
        p = port(q, q, dt)
        details.append(check_port(q, q, dt, p))
        ports.append(p)
        # Full global matrix already contains Jpp; add only its Schur correction.
        for a in range(5):
            if m[a] == 134:
                continue
            row = lookup[m[a]]
            residual[row] += p['effective'][a] - p['f'][a]
            for b in range(5):
                if m[b] != 134:
                    s[row][lookup[m[b]]] += p['y'][a][b] - p['j'][a][b]
        # Every eliminated row/column must belong to its own card and terminals.
        allowed = set(m)
        require(all(j[k][v] == 0 and j[v][k] == 0 for k in m[5:] for v in range(134) if v not in allowed), 'interior ownership')
        require(all(f[k] == p['f'][a] and j[k][v] == p['j'][a][b] for a,k in enumerate(m[5:],5) for b,v in enumerate(m) if v != 134), 'full card incidence')
    outer = [row[0] for row in lu_many(s,[[-v] for v in residual])]
    correction = [Z]*134
    for i,k in enumerate(retained):
        correction[k] = outer[i]
    for m,p in zip(maps,ports):
        dp = [Z if k==134 else correction[k] for k in m[:5]]
        for a,k in enumerate(m[5:]):
            correction[k] = p['offset'][a] + sum(v*w for v,w in zip(p['gradient'][a],dp))
    independent = op.dense([row[:] for row in j],[-v for v in f])
    errors = [a-b for a,b in zip(correction,independent)]
    rr = [v+w for v,w in zip(f,matvec(j,correction))]
    ground_delta = sum(v*w for v,w in zip(board_ground_gradient(x,dt,inv),correction))
    for m,p in zip(maps,ports):
        ground_delta += -op.D(1e-12)*(correction[m[op.NODES.index(5)]] + correction[m[op.NODES.index(6)]])
        # Imposed terminal tied to global ground has no equation in global x.
        for a,k in enumerate(m[:5]):
            if k == 134:
                ground_delta += sum(v*correction[n] for v,n in zip(p['j'][a],m) if n != 134)
    mass = abs(sum(rr[:98]) + ground + ground_delta)
    maxerr = maximum(errors)
    maxres = maximum(rr)
    require(max(maxerr,maxres,mass)<=GATE,f'loaded Newton or ground identity: correction={maxerr}; residual={maxres}; ground={mass}')
    return dict(dt_s=dt,ports=details,retained_indices=retained,eliminated_indices=sorted(eliminated),
                condensed_correction_decimal=list(map(str,correction)),full_correction_decimal=list(map(str,independent)),
                max_node_correction_difference_v=str(maximum(errors[:98])),max_branch_correction_difference_a=str(maximum(errors[98:])),
                max_reconstructed_residual=str(maxres),global_kcl_ground_a=str(mass),linear_identity_admitted=True,
                nonlinear_root_admitted=False,domain_of_reconstructed_candidate_checked=False)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--attempt',type=int,required=True)
    attempt=ap.parse_args().attempt
    out=ROOT/f'evidence/voice_vco1_741_condensation{attempt:02d}.json'
    require(not out.exists(),'preserve condensation attempt')
    parent='evidence/voice_vco1_reset_modes02.json'
    previous='evidence/voice_vco1_sdirk_tests01.json'
    qa=json.loads((ROOT/previous).read_text(encoding='utf8'))
    require(qa['passed'],'previous QA')
    names=set(qa['source_sha256'])|{parent,previous,'tools/vco1_741_condensation.py','docs/VCO1_741_CONDENSACION_PROTOCOLO.md','docs/VCO1_741_CONDENSACION_AUDITORIA.md','evidence/voice_vco1_741_condensation01.json','evidence/voice_vco1_741_condensation02.json'}
    before={n:sha(ROOT/n) for n in names}
    diagnostic='references-local/vco1-741-condensation-diagnostic01.json'
    private={n:sha(ROOT/n) for n in (op.MODEL,diagnostic)}
    report=dict(schema='rf-d/loaded-lm741-exact-newton-condensation/v1',passed=False,base_commit='ce2eda7f58bc61ff9cda2fe2aac5e5b6a6952200',
                source_sha256=before,private_input_sha256=private,decimal_precision=100,identity_absolute_gate=str(GATE),
                python_sha256=sha(Path(sys.executable)),python_version=sys.version,scenes=[],
                new_spice_processes=0,new_audio=False,production_kernel_changed=False,nonlinear_roots_admitted=False,
                dynamic_reduction_admitted=False,native_full_period_admitted=False,physical_fidelity=False,real_time=False)
    def save():out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n')
    save();start=time.perf_counter()
    controls=[.5,500.,1e-11,0.,0.,*([-2.1]*6)]
    inv=circuit.inventory(circuit.scenario(controls))
    descriptor=json.loads((ROOT/parent).read_text(encoding='utf8'))
    try:
        with localcontext() as ctx:
            ctx.prec=100
            for i,scene in enumerate(descriptor['scenes']):
                x=[Decimal.from_float(h)+Decimal.from_float(l) for h,l in zip(scene['previous_high'],scene['previous_low'])]
                entry=dict(scene=i,previous_high=scene['previous_high'],previous_low=scene['previous_low'],cases=[])
                report['scenes'].append(entry)
                for dt in (0.,125e-9,125e-9/4096,125e-9/16384):
                    entry['cases'].append(coupled(x,dt,controls,inv))
                    save();print('Condensation scene',i,'dt',dt,'identity passed',flush=True)
        report['passed']=True
    except Exception as exc:
        report['error']=repr(exc)
        report['failed_source_text']={n:(ROOT/n).read_text(encoding='utf8') for n in ('tools/vco1_741_condensation.py','docs/VCO1_741_CONDENSACION_PROTOCOLO.md')}
    report.update(source_sha256_after={n:sha(ROOT/n) for n in names},private_input_sha256_after={n:sha(ROOT/n) for n in private},wall_s=time.perf_counter()-start)
    report['passed']=report['passed'] and before==report['source_sha256_after'] and private==report['private_input_sha256_after']
    save();print('Loaded exact condensation',report['passed'],report.get('error',''),flush=True)


if __name__=='__main__':main()
