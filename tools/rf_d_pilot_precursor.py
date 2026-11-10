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
    return columns, *load_surface(table)


def load_surface(table):
    nominal, c2_up, c2_down, c5_up, c5_down, diag_up, diag_down = table
    slope = np.array([(c2_up - c2_down) / 2., (c5_up - c5_down) / 2.])
    curvature = np.array([(c2_up + c2_down) / 2. - nominal,
                          (c5_up + c5_down) / 2. - nominal])
    mixed = nominal + curvature.sum(axis=0) - (diag_up + diag_down) / 2.
    return nominal, slope, curvature, mixed


def conditioned_path(model, observed, order, quadratic_anchor=False):
    """Anchor the electrical curve once at the supplied latch and timer voltages."""
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
    times = R28_C4_S * charge_delta / gap[:-1] * ratio
    return select, values, weights, gap, times


def advance(model, observed, order, quadratic_anchor=False):
    """Estimate the next C4 guard if it is inside the current 96 kHz interval."""
    path = conditioned_path(model, observed, order, quadratic_anchor)
    if path is None:
        return None
    _, values, weights, _, times = path
    time = float(np.sum(times))
    if not 0. < time < INTERVAL_S:
        return None
    guard = np.r_[GUARD, values[[1, 3, 4, C2, 6], -1]]
    return dict(time_s=time, point=guard.tolist(), load_weights=weights.tolist(), intervals=len(times))


def carry(model, observed, order=2):
    """Run C4 from a single initial state through every 96 kHz boundary."""
    path = conditioned_path(model, observed, order, quadratic_anchor=True)
    if path is None:
        return None
    return clock_path(*path)


def clock_path(collector, values, weights, gap, times):
    boundaries = np.r_[0., np.cumsum(times)]
    duration = float(boundaries[-1])
    if not 0. < duration < 64. * INTERVAL_S:
        return None
    clock = np.arange(int(duration * CLOCK) + 1) * INTERVAL_S
    index = np.minimum(np.searchsorted(boundaries, clock, side="right") - 1, len(times) - 1)
    elapsed_fraction = (clock - boundaries[index]) / times[index]
    relative = (gap[index+1] - gap[index]) / gap[index]
    fraction = elapsed_fraction.copy()
    varying = relative != 0.
    fraction[varying] = np.expm1(np.log1p(relative[varying]) * elapsed_fraction[varying]) / relative[varying]
    state = values[:, index] + fraction * (values[:, index+1] - values[:, index])
    voltage = collector[index] + fraction * (collector[index+1] - collector[index])
    guard = np.r_[GUARD, values[[1, 3, 4, C2, 6], -1]]
    return dict(time_s=duration - clock[-1], point=guard.tolist(), load_weights=weights.tolist(),
                slot=len(clock) - 1, state=np.column_stack((voltage, state.T)),
                end_c4_v=float(values[0, -1]))


def charge_trace(stages, extra_nodes=()):
    """Resolve the precursor against C4's monotonically decreasing plate voltage."""
    index = int(np.flatnonzero(stages[:, 26] >= GUARD)[0])
    a, b = stages[index-1:index+1]
    weight = (GUARD - a[26]) / (b[26] - a[26])
    end = a + weight * (b - a)
    nodes = [26, *NODES, *extra_nodes]
    values = np.vstack((stages[:index, nodes], end[nodes]))
    values[-1, 0] = GUARD
    values[:, 1] -= values[:, 2]
    charge = values[0, 1] - values[:, 1]
    assert (np.diff(charge) > 0.).all()
    return charge / charge[-1], values


def charge_family(traces, points=POINTS):
    progress = np.linspace(0., 1., points) if isinstance(points, int) else points
    table = np.array([[np.interp(progress, u, v) for v in values.T] for u, values in traces])
    return progress, *load_surface(table)


def carry_charge(model, observed, coupled, extra_nodes=()):
    """Condition the fixed curve in C4 charge instead of collector voltage."""
    if not 0. <= observed[26] < GUARD or not observed[26] < observed[28]:
        return None
    progress, nominal, slope, curvature, mixed = model
    before = observed[[26, *NODES, *extra_nodes]].copy()
    before[1] -= before[2]
    if not nominal[1, -1] < before[1] <= nominal[1, 0] + 1e-12:
        return None
    phase = np.interp(before[1], nominal[1, ::-1], progress[::-1])
    timers = [C2 + 1, C5 + 1]
    coupling = mixed if coupled else np.zeros_like(mixed)

    def at(table, u):
        return np.array([np.interp(u, progress, row) for row in table])

    for _ in range(4):
        a = np.array([at(axis[timers], phase) for axis in slope]).T
        b = np.array([at(axis[timers], phase) for axis in curvature]).T
        c = at(coupling[timers], phase)
        wanted = before[timers] - at(nominal[timers], phase)
        load = np.linalg.solve(a, wanted)
        for _ in range(3):
            error = a @ load + b @ (load ** 2) + c * load.prod() - wanted
            tangent = a + 2. * b * load + c[:, None] * load[::-1]
            load -= np.linalg.solve(tangent, error)
        if abs(load).max() > 1.05:
            return None
        fitted = (nominal + np.einsum("i,ijk->jk", load, slope)
                  + np.einsum("i,ijk->jk", load ** 2, curvature) + coupling * load.prod())
        if (np.diff(fitted[1]) >= 0.).any() or not fitted[1, -1] < before[1] <= fitted[1, 0] + 1e-12:
            return None
        phase = np.interp(before[1], fitted[1, ::-1], progress[::-1])

    after = np.searchsorted(progress, phase, side="right")
    state = np.column_stack((at(fitted, phase), fitted[:, after:]))
    state[1:] += (before[1:] - state[1:, 0])[:, None]
    state[0, 0] = before[0]
    gap = state[1] + state[2] - state[3]
    delta = -np.diff(state[1])
    if (gap <= 0.).any() or (delta <= 0.).any() or state[7, -1] <= GUARD:
        return None
    relative = np.diff(gap) / gap[:-1]
    ratio = np.ones_like(relative)
    nonzero = relative != 0.
    ratio[nonzero] = np.log1p(relative[nonzero]) / relative[nonzero]
    times = R28_C4_S * delta / gap[:-1] * ratio
    result = clock_path(state[0], state[1:], load, gap, times)
    if result is not None and extra_nodes:
        result["guard_loads"] = state[-len(extra_nodes):, -1]
        result["load_times"] = np.r_[0., np.cumsum(times)]
        result["load_path"] = state[-len(extra_nodes):]
    return result
