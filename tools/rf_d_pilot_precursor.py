"""C4 charge clock leading to the collector predictor's rising guard."""
import numpy as np

GUARD = .35
CLOCK = 96_000
INTERVAL_S = 1. / CLOCK
R28_C4_S = 10_000. * 10e-9
POINTS = 65
NODES = [23, 25, 17, 27, 9, 5, 28, 38]
C2, C5 = 5, 7


def trace(stages):
    """Prepare a calibration trace with x26 as the independent variable."""
    c = stages[:, 26]
    end = int(np.flatnonzero(c >= GUARD)[0]) + 1
    rising = c[:end]
    monotone = np.r_[True, rising[1:] > np.maximum.accumulate(rising[:-1])]
    values = stages[:end, NODES][monotone].copy()
    values[:, 0] -= values[:, 1]  # C4 voltage, x23 - x25.
    return rising[monotone], values


def family(traces, points=POINTS):
    """One nominal path and independent positive/negative C2 and C5 perturbations."""
    low = max(columns[0] for columns, _ in traces)
    columns = np.geomspace(low, GUARD, points)
    table = np.array([[np.interp(columns, c, v) for v in values.T] for c, values in traces])
    nominal, c2_up, c2_down, c5_up, c5_down, diag_up, diag_down = table
    slope = np.array([(c2_up - c2_down) / 2., (c5_up - c5_down) / 2.])
    curvature = np.array([(c2_up + c2_down) / 2. - nominal,
                          (c5_up + c5_down) / 2. - nominal])
    mixed = nominal + curvature.sum(axis=0) - (diag_up + diag_down) / 2.
    return columns, nominal, slope, curvature, mixed


def advance(model, observed, order, quadratic_anchor=False):
    """From the left 96 kHz state, estimate the next C4 guard if it is in this interval."""
    c, nominal, slope, curvature, mixed = model
    start = observed[26]
    if not c[0] <= start < GUARD or not start < observed[28]:
        return None
    before = observed[NODES].copy()
    before[0] -= before[1]
    select = np.r_[start, c[c > start]]

    def at(values):
        result = np.array([np.interp(select, c, column) for column in values])
        if quadratic_anchor:
            first = max(0, min(int(np.searchsorted(c, start)) - 1, len(c) - 3))
            knots = c[first:first+3]
            weights = np.array([np.prod((start - np.delete(knots, i)) /
                                        (knots[i] - np.delete(knots, i))) for i in range(3)])
            result[:, 0] = values[:, first:first+3] @ weights
        return result

    values = at(nominal)
    weights = np.zeros(2)
    if order:
        linear = np.array([at(axis) for axis in slope])
        first = linear[:, [C2, C5], 0].T
        delta = before[[C2, C5]] - values[[C2, C5], 0]
        weights = np.linalg.solve(first, delta)
        if order >= 2:
            second = np.array([at(axis) for axis in curvature])
            cross = at(mixed) if order == 3 else np.zeros_like(values)
            quadratic = second[:, [C2, C5], 0].T
            coupling = cross[[C2, C5], 0]
            for _ in range(3):
                residual = first @ weights + quadratic @ (weights ** 2) + coupling * weights.prod() - delta
                tangent = first + 2. * quadratic * weights + coupling[:, None] * weights[::-1]
                weights -= np.linalg.solve(tangent, residual)
        if abs(weights).max() > 1.05:
            return None
        values += np.einsum("i,ijk->jk", weights, linear)
        if order >= 2:
            values += np.einsum("i,ijk->jk", weights ** 2, second) + cross * weights.prod()

    values += (before - values[:, 0])[:, None]
    charge_delta = -np.diff(values[0])
    gap = values[0] + values[1] - values[2]  # x23 - x17, R28 drop.
    if (charge_delta <= 0.).any() or (gap <= 0.).any() or values[6, -1] <= GUARD:
        return None
    relative = np.diff(gap) / gap[:-1]
    ratio = np.ones_like(relative)
    nonzero = relative != 0.
    ratio[nonzero] = np.log1p(relative[nonzero]) / relative[nonzero]
    time = float(R28_C4_S * np.sum(charge_delta / gap[:-1] * ratio))
    if not 0. < time < INTERVAL_S:
        return None
    guard = np.r_[GUARD, values[[1, 3, 4, C2, 6], -1]]
    return dict(time_s=time, point=guard.tolist(), load_weights=weights.tolist(), intervals=len(charge_delta))
