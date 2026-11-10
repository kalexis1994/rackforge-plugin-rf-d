"""Generate the pilot FOH model with its physical contour drives."""
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
# Ladder junctions above the signal pair, which is already in build().
# Node 68 represents the fixed 10 V collector in the top two devices.
UPPER_LADDER = ((3, 9, 8), (2, 10, 9), (1, 11, 10), (0, 68, 11),
                (3, 13, 12), (2, 14, 13), (1, 15, 14), (0, 68, 15))
LAWS = 12 + 2 * len(FIRST_VCA)
SPLIT_LAWS = LAWS + 2 * len(UPPER_LADDER)
WIDE_LAWS = LAWS + 4


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


def model(h, wide=False, split=None, split_ladder=False, normalize_defects=False):
    assert split is None or not wide
    assert not (split_ladder or normalize_defects) or split is not None
    raw = build(cases()[1] if split is None else split, h)
    a, g, c, d, e = (raw[key] for key in ("a", "g", "c", "d", "e"))
    n, charges = len(g), len(a)
    devices = FIRST_VCA + UPPER_LADDER if split_ladder else FIRST_VCA
    sense = np.zeros((2 * len(devices), n))
    inject = np.zeros((n, len(sense)))
    fixed = np.zeros(len(sense))
    for k, (base, collector, emitter) in enumerate(devices):
        j = 2 * k
        sense[j:j + 2, base] = 1. / VT
        sense[j, emitter] = -1. / VT
        inject[[base, emitter], j:j + 2] = [[.01, .2], [-1.01, 1.]]
        if collector < n:
            sense[j + 1, collector] = -1. / VT
            inject[collector, j:j + 2] = [1., -1.2]
        else:
            fixed[j + 1] = -10. / VT
    iexp = np.r_[raw["iexp"], 1e-14 * np.exp(sense @ raw["dc"] + fixed)]
    d = np.column_stack((d, inject))
    e = np.vstack((e, sense))
    if wide:
        # PNP Q26 and NPN Q28, with the latter's emitter tied to ground.
        sense = np.zeros((4, n))
        inject = np.zeros((n, 4))
        for j, base, collector, emitter, sign in ((0, 62, 64, 63, -1.), (2, 63, 65, None, 1.)):
            sense[j:j + 2, base] = sign / VT
            sense[j + 1, collector] = -sign / VT
            if emitter is not None:
                sense[j, emitter] = -sign / VT
                inject[emitter, j:j + 2] = sign * np.array([-1.01, 1.])
            inject[[base, collector], j:j + 2] = sign * np.array([[.01, .2], [1., -1.2]])
        iexp = np.r_[iexp, 1e-14 * np.exp(sense @ raw["dc"])]
        d = np.column_stack((d, inject))
        e = np.vstack((e, sense))
    if split is None:
        inputs = np.column_stack((raw["b"], np.eye(n)[:, 32] / R59, np.eye(n)[:, 62] / R16))
        output = list(BASE_NODES)
    else:
        # The contour owns Q26/Q28 and the capacitor at x62. R60 remains
        # in the TAIL row, with its collector voltage supplied at the port.
        keep = np.r_[0:62, 66:68]
        drop = np.arange(62, 66)
        assert g[5, 65] == -1. / R60
        assert np.count_nonzero(g[np.ix_(keep, drop)]) == 1
        assert np.count_nonzero(a[:, drop]) == 1
        charge = np.flatnonzero(np.any(a[:, keep] != 0., axis=1))
        assert len(charge) == charges - 1
        inputs = np.column_stack((raw["b"], np.eye(n)[:, 32] / R59, np.eye(n)[:, 5] / R60))[keep]
        a, c = a[np.ix_(charge, keep)], c[charge]
        g, d, e = g[np.ix_(keep, keep)], d[keep], e[:, keep]
        n, charges = len(keep), len(charge)
        output = [int(np.flatnonzero(keep == node)[0]) for node in BASE_NODES[:-1]]
    if normalize_defects:
        # Project the current at each junction's own exponential bias.
        # The plant then solves the dimensionless exponential remainder,
        # without asking the off VCA to respond to a one-ampere defect.
        d = d * iexp
        iexp = np.ones_like(iexp)
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
    assert projection_error < 1e-8 and charge_error < 1e-11 and semigroup_error < 1e-10, (
        projection_error, charge_error, semigroup_error)
    xd = -(xn + xq @ w1[:, 3:])
    data = dict(iexp=iexp, f=f, u0=w0[:, :3], u1=w1[:, :3], n0=w0[:, 3:], n1=w1[:, 3:],
                p=e @ xd, zh=e @ xq, zu=e @ xu,
                dc=raw["dc"][list(BASE_NODES)], xq=xq[output], xu=xu[output], xd=xd[output])
    if split is not None:
        data["xq"] = np.pad(data["xq"], ((0, 1), (0, 0)))
        data["xu"] = np.vstack((data["xu"], [0., 0., 1.]))
        data["xd"] = np.pad(data["xd"], ((0, 1), (0, 0)))
    checks = dict(projection_error=projection_error, charge_error=charge_error,
                  semigroup_error=semigroup_error)
    return data, checks


def emit_data(path, h, wide=False, split=None, center=None, limits=None, split_ladder=False,
              normalize_defects=False):
    data, checks = model(h, wide, split, split_ladder, normalize_defects)
    if split is not None:
        assert center is not None and limits is not None
        data["split_center"] = np.array(center)
        data["split_range"] = np.array(limits)

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
