"""Add the physical R59 drive and cutoff pin 16 to the pilot FOH model."""
import math

import numpy as np

from recovery_port_input_model import VT, build, cases

OWN = "tools/prepare_rf_d_pilot_returns.py"
R59 = 68_000.
R60 = 680.
R16 = 47_000.  # Resistance from board pin 16 in cutoff::reduce_panel.
BASE_NODES = (61, 66, 6, 32, 5, 65)
# Q18 and the first VCA's signal pair, in circuit66 coordinates.
FIRST_VCA = ((32, 28, 29), (25, 30, 27), (26, 31, 27))
LAWS = 12 + 2 * len(FIRST_VCA)


def foh(a, b, h):
    """Augmented exponential with each drive independently scaled."""
    n, m = b.shape
    scale = 1. / np.maximum(1., np.max(abs(h * b), axis=0))
    z = np.zeros((n + 2 * m, n + 2 * m))
    z[:n, :n] = h * a
    z[:n, n:n + m] = h * b * scale
    z[n:n + m, n + m:] = np.eye(m)
    squares = max(0, math.ceil(math.log2(np.linalg.norm(z, np.inf) / .125)))
    z /= 2 ** squares
    term = np.eye(len(z))
    exp = term.copy()
    for k in range(1, 25):
        term = term @ z / k
        exp += term
    for _ in range(squares):
        exp = exp @ exp
    new = exp[:n, n + m:] / scale
    return exp[:n, :n], exp[:n, n:n + m] / scale - new, new


def model(h):
    raw = build(cases()[1], h)
    a, g, c, d, e = (raw[key] for key in ("a", "g", "c", "d", "e"))
    n, charges = len(g), len(a)
    sense = np.zeros((2 * len(FIRST_VCA), n))
    inject = np.zeros((n, len(sense)))
    for k, (base, collector, emitter) in enumerate(FIRST_VCA):
        j = 2 * k
        sense[j:j + 2, base] = 1. / VT
        sense[j, emitter] = -1. / VT
        sense[j + 1, collector] = -1. / VT
        inject[[base, collector, emitter], j:j + 2] = [[.01, .2], [1., -1.2], [-1.01, 1.]]
    iexp = np.r_[raw["iexp"], 1e-14 * np.exp(sense @ raw["dc"])]
    d = np.column_stack((d, inject))
    e = np.vstack((e, sense))
    inputs = np.column_stack((raw["b"], np.eye(n)[:, 32] / R59, np.eye(n)[:, 62] / R16))
    lhs = np.block([[g, a.T * c], [a, np.zeros((charges, charges))]])
    forcing = np.column_stack((inputs, -d))
    rhs = np.block([[np.zeros((n, charges)), forcing],
                    [np.eye(charges), np.zeros((charges, forcing.shape[1]))]])
    projection = np.linalg.solve(lhs, rhs)
    xq, xu, xn = np.split(projection[:n], [charges, charges + 3], axis=1)
    aa, b = projection[n:, :charges], projection[n:, charges:]
    f, w0, w1 = foh(aa, b, h)
    f2, _, _ = foh(aa, b, h / 2.)
    projection_error = float(np.max(abs(lhs @ projection - rhs)))
    semigroup_error = float(np.max(abs(f2 @ f2 - f)))
    charge_error = float(np.max(abs(a @ projection[:n] - rhs[n:])))
    assert projection_error < 1e-8 and charge_error < 1e-11 and semigroup_error < 1e-10
    xd = -(xn + xq @ w1[:, 3:])
    data = dict(iexp=iexp, f=f, u0=w0[:, :3], u1=w1[:, :3], n0=w0[:, 3:], n1=w1[:, 3:],
                p=e @ xd, zh=e @ xq, zu=e @ xu,
                dc=raw["dc"][list(BASE_NODES)], xq=xq[list(BASE_NODES)],
                xu=xu[list(BASE_NODES)], xd=xd[list(BASE_NODES)])
    checks = dict(projection_error=projection_error, charge_error=charge_error,
                  semigroup_error=semigroup_error)
    return data, checks


def emit_data(path, h):
    data, checks = model(h)

    def rust(value):
        return "[" + ",".join(map(rust, value)) + "]" if isinstance(value, list) else f"{value:.17e}"

    source = ""
    for name, values in data.items():
        ty = "f64"
        for dimension in values.shape[::-1]:
            ty = f"[{ty}; {dimension}]"
        source += f"pub const {name.upper()}: {ty} = {rust(values.tolist())};\n"
    path.write_text(source, encoding="utf8", newline="\n")
    return checks
