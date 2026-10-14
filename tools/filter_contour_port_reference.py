"""Original Q22/Q21 + explicit R17 cursor + Q26/Q28, finite-difference Newton.

Does not import the native reduced stamp, tangent or solver. Currents are
positive leaving a circuit node into an element, including all eight ports.
"""
import csv
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VT = 1.380649e-23 * 298.15 / 1.602176634e-19


def original(x, b, amount, cutoff, c11=0., history=None):
    n = 10 if 0 < amount < 1 else 9
    v = list(x) + list(b)
    r = [0.] * (n + 8)

    def branch(a, c, resistance):
        i = (v[a] - v[c]) / resistance
        r[a] += i
        r[c] -= i

    for a, c, resistance in [(0, n, 10000.), (2, n+3, 560.),
            (3, 4, 5600.), (4, n+4, 16900.),
            (5, n+5, 200000.+5000.*cutoff*(1.-cutoff)),
            (5, n+7, 2050.), (5, n+7, 100000.), (5, n+7, 33000.),
            (6, n+6, 68900.), (7, n+4, 330.), (8, n+2, 680.)]:
        branch(a, c, resistance)
    if amount == 0:
        cursor = n+7
        branch(3, cursor, 50000.)
    elif amount == 1:
        cursor = 3
        branch(cursor, n+7, 50000.)
    else:
        cursor = 9
        branch(3, cursor, 50000.*(1.-amount))
        branch(cursor, n+7, 50000.*amount)
    branch(cursor, 5, 47000.)
    for base, collector, emitter, sign in [(0, 1, 3, 1.),
            (1, 3, 2, -1.), (5, 7, 6, -1.), (6, 8, n+7, 1.)]:
        forward_v = sign*(v[base]-v[emitter])/VT
        reverse_v = sign*(v[base]-v[collector])/VT
        if max(forward_v, reverse_v) > 45:
            raise ValueError('BJT exponential domain')
        forward = 1e-14*math.expm1(forward_v)
        reverse = 1e-14*math.expm1(reverse_v)
        ib = sign*(forward/100. + reverse/5.)
        ic = sign*((forward-reverse)-reverse/5.)
        r[base] += ib
        r[collector] += ic
        r[emitter] -= ib+ic
    z = (v[4]-b[1])/(1.5*VT)
    if z > 45:
        raise ValueError('CR3 exponential domain')
    diode = 1e-8*math.expm1(z)
    r[4] += diode
    r[n+1] -= diode
    if history is not None:
        old, dt = history
        for k, (a, c, cap) in enumerate([(1, 2, c11), (5, n+7, 100e-12)]):
            current = cap*(v[a]-v[c]-old[k])/dt
            r[a] += current
            r[c] -= current
    return r[:n], r[n:]


def cursor_voltage(x, b, amount):
    """Solve the original three-resistor cursor row, not the native G formula."""
    upper = 1./(50000.*(1.-amount))
    lower = 1./(50000.*amount)
    load = 1./47000.
    return (upper*x[3]+lower*b[7]+load*x[5])/(upper+lower+load)


def reduced_values(x, b, amount, cutoff, c11=0., history=None):
    original_x = list(x)
    if 0 < amount < 1:
        original_x.append(cursor_voltage(x, b, amount))
    rows, ports = original(original_x, b, amount, cutoff, c11, history)
    return rows[:9]+ports


def gaussian(matrix, rhs):
    n = len(rhs)
    rows = [list(matrix[i])+[rhs[i]] for i in range(n)]
    for k in range(n):
        pivot = max(range(k, n), key=lambda i: abs(rows[i][k]))
        if rows[pivot][k] == 0:
            raise ValueError('singular original graph')
        rows[k], rows[pivot] = rows[pivot], rows[k]
        for i in range(k+1, n):
            factor = rows[i][k]/rows[k][k]
            for j in range(k+1, n+1):
                rows[i][j] -= factor*rows[k][j]
    result = [0.]*n
    for i in range(n-1, -1, -1):
        result[i] = (rows[i][n]-sum(rows[i][j]*result[j]
                                  for j in range(i+1, n)))/rows[i][i]
    return result


def derivative(function, values, step=1e-6):
    cols = []
    for j in range(len(values)):
        lo, hi = list(values), list(values)
        lo[j] -= step
        hi[j] += step
        cols.append([(a-b)/(2*step) for a, b in zip(function(hi), function(lo))])
    return [list(row) for row in zip(*cols)]


def root(b, amount, cutoff, c11=0., history=None, seed=None):
    if seed is None:
        out = b[0]-.58
        fb = min((out/5600.+b[4]/16900.)/(1./5600.+1./16900.), b[1]+.28)
        x = [b[0]-.025, b[3]-.58, b[3]-.04, out, fb,
             .015, .50, -9.999, b[2]-.04]
        if 0 < amount < 1:
            x.append(amount*out)
    else:
        x = list(seed)
    evaluate = lambda y: original(y, b, amount, cutoff, c11, history)[0]
    for iteration in range(100):
        residual = evaluate(x)
        j = derivative(evaluate, x)
        dx = gaussian(j, [-v for v in residual])
        norm, correction = max(map(abs, residual)), max(map(abs, dx))
        if norm <= 1e-12 and correction <= 1e-8:
            return x, original(x, b, amount, cutoff, c11, history)[1], norm
        for power in range(28):
            candidate = [v+d*2.**(-power) for v, d in zip(x, dx)]
            try:
                if max(map(abs, evaluate(candidate))) < norm:
                    x = candidate
                    break
            except ValueError:
                continue
        else:
            raise ValueError('original graph Newton no decrease')
    raise ValueError('original graph iteration budget')


def tangents(x, b, a, cutoff, c11=0., history=None):
    # Re-solve the original graph for every boundary perturbation.
    def response(bb):
        return root(bb, a, cutoff, c11, history, seed=x)[1]
    return derivative(response, b, step=1e-5)


def boundary(timing, reset, cutoff=.5):
    return [timing, reset, 1.4, 9.3, -10., -10.+20.*cutoff, 1., 0.]


def maximum_difference(a, b):
    return max(abs(v-w) for v, w in zip(a, b))


def flat(matrix):
    return [v for row in matrix for v in row]


def audit(csv_path):
    metrics = dict(dc_cases=0, dynamic_steps=0, original_dc_rows=0,
        original_dynamic_rows=0, fd_stamp_entries=0, fd_port_entries=0,
        max_root_error_v=0., max_port_error_a=0., max_stamp_gate_fraction=0.,
        max_tangent_gate_fraction=0., max_original_residual_a=0.,
        max_total_return_error_a=0., max_charge_error_c=0.,
        max_native_residual_a=0., max_native_correction_v=0.,
        max_refinement_node_v=0., max_refinement_port_a=0.)
    rows = list(csv.reader(Path(csv_path).read_text(encoding='utf8').splitlines()))
    traces, histories, charge_sum = {}, {}, {}
    for row in rows:
        if row[0] == 'PASSED':
            assert row[1:] in (['60', '96', '20'], ['60', '96', '24'])
            metrics['atomic_rejections'] = int(row[3])
            continue
        data = list(map(float, row[1:]))
        if row[0] == 'DC':
            assert len(data) == 383
            a, timing, reset, cutoff = data[:4]
            b = boundary(timing, reset, cutoff)
            x, ports, norm = root(b, a, cutoff)
            metrics['dc_cases'] += 1
            metrics['original_dc_rows'] += len(x)
            native_x, native_i, native_t = data[4:13], data[13:21], data[21:85]
            e = maximum_difference(native_x, x[:9])
            i = maximum_difference(native_i, ports)
            assert e <= 1e-6 and i <= 1e-9, ('DC root/current', a, timing, reset, cutoff, e, i)
            metrics['max_root_error_v'] = max(metrics['max_root_error_v'], e)
            metrics['max_port_error_a'] = max(metrics['max_port_error_a'], i)
            metrics['max_original_residual_a'] = max(metrics['max_original_residual_a'], norm)
            native_res = data[85:94]
            assert max(map(abs, native_res)) <= 1e-11
            values = reduced_values(native_x, b, a, cutoff)
            assert maximum_difference(values, native_res+native_i) <= 2e-11
            j = derivative(lambda v: reduced_values(v[:9], v[9:], a, cutoff), native_x+b)
            expected = (flat([r[:9] for r in j[:9]]) + flat([r[9:] for r in j[:9]])
                        + flat([r[:9] for r in j[9:]]) + flat([r[9:] for r in j[9:]]))
            assert len(expected) == 289
            for v, ref in zip(data[94:], expected):
                fraction = abs(v-ref)/(2e-9+2e-5*abs(ref))
                assert fraction <= 1, ('stamp', a, timing, reset, cutoff, fraction)
                metrics['max_stamp_gate_fraction'] = max(metrics['max_stamp_gate_fraction'], fraction)
            metrics['fd_stamp_entries'] += len(expected)
            for v, ref in zip(native_t, flat(tangents(x, b, a, cutoff))):
                fraction = abs(v-ref)/(2e-9+2e-5*abs(ref))
                assert fraction <= 1, ('tangent', a, timing, reset, cutoff, fraction)
                metrics['max_tangent_gate_fraction'] = max(metrics['max_tangent_gate_fraction'], fraction)
            metrics['fd_port_entries'] += 64
            total = abs(sum(native_res)+sum(native_i))
            assert total <= 2e-11
            metrics['max_total_return_error_a'] = max(metrics['max_total_return_error_a'], total)
        elif row[0] == 'START':
            c11, dt = data[:2]
            x, _, _ = root(boundary(.85, .01), .5, .5, c11)
            assert maximum_difference(x[:9], data[2:11]) <= 1e-6
            histories[(c11, dt)] = (x, [x[1]-x[2], x[5]])
            charge_sum[(c11, dt)] = [0., 0.]
            traces[(c11, dt)] = {}
        elif row[0] == 'STEP':
            assert len(data) in (89, 378)
            c11, dt, k, timing = data[:4]
            key = (c11, dt)
            prior_x, old = histories[key]
            b = boundary(timing, .01)
            x, ports, norm = root(b, .5, .5, c11, (old, dt), prior_x)
            new = [x[1]-x[2], x[5]]
            e = maximum_difference(x[:9], data[4:13])
            i = maximum_difference(ports, data[13:21])
            assert e <= 1e-6 and i <= 1e-9, ('trajectory root', key, k, e, i)
            metrics['max_root_error_v'] = max(metrics['max_root_error_v'], e)
            metrics['max_port_error_a'] = max(metrics['max_port_error_a'], i)
            metrics['max_original_residual_a'] = max(metrics['max_original_residual_a'], norm)
            for v, ref in zip(data[21:85], flat(tangents(x, b, .5, .5, c11, (old, dt)))):
                fraction = abs(v-ref)/(2e-9+2e-5*abs(ref))
                assert fraction <= 1, ('dynamic tangent', key, k, fraction)
                metrics['max_tangent_gate_fraction'] = max(metrics['max_tangent_gate_fraction'], fraction)
            metrics['fd_port_entries'] += 64
            if len(data) == 378:
                native_x = data[4:13]
                j_fd = derivative(lambda v: reduced_values(v[:9], v[9:], .5, .5,
                                      c11, (old, dt)), native_x+b)
                expected = (flat([r[:9] for r in j_fd[:9]]) + flat([r[9:] for r in j_fd[:9]])
                            + flat([r[:9] for r in j_fd[9:]]) + flat([r[9:] for r in j_fd[9:]]))
                for v, ref in zip(data[89:], expected):
                    fraction = abs(v-ref)/(2e-9+2e-5*abs(ref))
                    assert fraction <= 1, ('dynamic stamp', key, k, fraction)
                    metrics['max_stamp_gate_fraction'] = max(metrics['max_stamp_gate_fraction'], fraction)
                metrics['fd_stamp_entries'] += len(expected)
            for j, cap in enumerate([c11, 100e-12]):
                charge = cap*(new[j]-old[j])
                error = abs(charge-data[85+j])
                assert error <= 2e-11*dt, ('charge', key, k, error)
                metrics['max_charge_error_c'] = max(metrics['max_charge_error_c'], error)
                charge_sum[key][j] += charge
            original_r, _ = original(x, b, .5, .5, c11, (old, dt))
            total = abs(sum(original_r)+sum(ports))
            assert total <= 2e-11
            metrics['max_total_return_error_a'] = max(metrics['max_total_return_error_a'], total)
            assert data[87] <= 1e-11 and data[88] <= 1e-8
            metrics['max_native_residual_a'] = max(metrics['max_native_residual_a'], data[87])
            metrics['max_native_correction_v'] = max(metrics['max_native_correction_v'], data[88])
            histories[key] = (x, new)
            traces[key][int(k)*round(dt*1e9)] = (data[4:13], data[13:21])
            metrics['dynamic_steps'] += 1
            metrics['original_dynamic_rows'] += len(x)
        elif row[0] == 'LEDGER':
            key = tuple(data[:2])
            assert maximum_difference(charge_sum[key], data[2:]) <= 2e-15
        else:
            raise ValueError('unexpected native row '+row[0])
    assert metrics['dc_cases'] == 60 and metrics['dynamic_steps'] == 96
    for c11 in [0., 47e-12]:
        for clock, (x, i) in traces[(c11, 8e-6)].items():
            fine_x, fine_i = traces[(c11, 4e-6)][clock]
            dx, di = maximum_difference(x, fine_x), maximum_difference(i, fine_i)
            metrics['max_refinement_node_v'] = max(metrics['max_refinement_node_v'], dx)
            metrics['max_refinement_port_a'] = max(metrics['max_refinement_port_a'], di)
    assert metrics['max_refinement_node_v'] <= 2e-6, metrics
    assert metrics['max_refinement_port_a'] <= 2e-9, metrics
    metrics['passed'] = True
    return metrics


if __name__ == '__main__':
    import sys
    print(json.dumps(audit(sys.argv[1]), indent=2))
