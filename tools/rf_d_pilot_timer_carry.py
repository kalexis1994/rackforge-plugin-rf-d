"""Advance C2/C5 from their own currents on the bounded C4 load path."""
import numpy as np

from rf_d_pilot_precursor import CLOCK, GUARD, carry_charge, load_surface

PERIOD = 1. / CLOCK
CAP = 10e-6
OHMS = np.array([[1_000., 10_000., 10_000.], [100., 1_000., 10_000.]])
G = 1. / OHMS[:, 1:]
TOTAL = G.sum(axis=1)
RATE = TOTAL / CAP
MOVE = -np.expm1(-RATE * PERIOD)
PORTS = (40, 11, 0, 47, 29)
POST_POINTS = 33


def post_trace(stages, cross_s, steps, extra_nodes=()):
    time = np.r_[0., (np.arange(len(stages) // 2)[:, None] + [1. / 3., 1.]).ravel()] / (steps * CLOCK)
    # Denser around the regenerative crossing, where decay changes fastest.
    clock = PERIOD * np.linspace(0., 1., POST_POINTS) ** 2
    assert cross_s + clock[-1] <= time[-1]
    return clock, np.array([np.interp(cross_s + clock, time, stages[:, i]) for i in (*PORTS, *extra_nodes)])


def post_family(traces):
    assert all(np.array_equal(clock, traces[0][0]) for clock, _ in traces)
    return traces[0][0], *load_surface(np.array([values for _, values in traces]))


def post_at(model, load, coupled):
    time, nominal, slope, curvature, mixed = model
    values = (nominal + np.einsum("i,ijk->jk", load, slope)
              + np.einsum("i,ijk->jk", load ** 2, curvature))
    if coupled:
        values += mixed * load.prod()
    return time, values


def cell_current(evaluate, latch, timer):
    return evaluate(np.asarray(latch).reshape(-1, 2), np.asarray(timer).reshape(-1, 2))


def affine_weights(duration):
    x = RATE * duration
    moved = -np.expm1(-x)
    # Stable series for the small timing steps of the two loaded capacitors.
    end = x * (.5 - x * (1. / 6. - x * (1. / 24. - x / 120.)))
    return moved, end / moved


def advance(timer, attack, passive, moved=MOVE):
    return timer + moved / TOTAL * (attack + ((passive - timer[:, None]) * G).sum(axis=1))


def loads(state):
    return state[[0, 9]], state[10:14].reshape(2, 2)


def continuous_step(evaluate, timer, left, right, duration, projected=None):
    """Close the endpoint attack currents with two fixed corrections."""
    latch, ports = left
    end_latch, end_ports = right
    before = cell_current(evaluate, latch, timer)[0]
    moved, w = affine_weights(duration)
    passive = ports + w[:, None] * (end_ports - ports) if projected is None else projected
    predicted = advance(timer, before, passive, moved)
    for _ in range(2):
        after = cell_current(evaluate, end_latch, predicted)[0]
        predicted = advance(timer, before + w * (after - before), passive, moved)
    return predicted


def project_passive(path_time, path_values, start, end, total_end, norm):
    """Contribution of affine port segments to the timer's exponential mean."""
    if end <= start:
        return np.zeros((2, 2))
    times = np.r_[start, path_time[(start < path_time) & (path_time < end)], end]
    values = np.array([np.interp(times, path_time, row) for row in path_values]).T.reshape(-1, 2, 2)
    duration = np.diff(times)[:, None]
    moved, weight = affine_weights(duration)
    factor = moved / norm * np.exp(-RATE * (total_end - times[1:, None]))
    return np.sum(factor[..., None] * (values[:-1] + weight[..., None] * np.diff(values, axis=0)), axis=0)


def event_passive(left, previous, post_time, post_values, cross, mode, path=None):
    """Project independent decay and follower voltages over the event interval."""
    if mode == "hold":
        return left
    end_pre = left + (left - previous) * (cross / PERIOD)
    front = np.column_stack((left.ravel(), end_pre.ravel()))
    if path is None:
        before = project_passive(np.array([0., cross]), front, 0., cross, PERIOD, MOVE)
    else:
        time, values, origin = path
        to_guard = time[-1] - origin
        before = project_passive(time - origin, values, 0., to_guard, PERIOD, MOVE)
        remainder = cross - to_guard
        if remainder > 0.:
            rate = (values[:, -1] - values[:, -2]) / (time[-1] - time[-2])
            to_cross = values[:, -1] + remainder * rate
            last = np.column_stack((values[:, -1], to_cross))
            before += project_passive(np.array([to_guard, cross]), last, to_guard, cross, PERIOD, MOVE)
    after = project_passive(post_time + cross, post_values[1:], cross, PERIOD, PERIOD, MOVE)
    return before + after


def run(evaluate, crossing, shape, post, initial, coupled=False, mode="projected", path_projection=False):
    carried = carry_charge(shape, initial, coupled, PORTS)
    if carried is None:
        return None
    states = carried["state"]
    if len(states) < 2:
        return None
    timer = initial[[5, 38]].copy()
    history = [timer.copy()]
    path_time, path_values = carried["load_times"], carried["load_path"][1:]
    for i, (left, right) in enumerate(zip(states[:-1], states[1:])):
        start, end = i * PERIOD, (i + 1) * PERIOD
        projected = project_passive(path_time, path_values, start, end, end, MOVE) if path_projection else None
        timer = continuous_step(evaluate, timer, loads(left), loads(right), PERIOD, projected)
        history.append(timer)

    last, previous = states[-1], states[-2]
    guard_loads = carried["guard_loads"]
    guard = np.asarray(carried["point"])
    guard_inputs = np.array([GUARD, guard_loads[0]]), guard_loads[1:].reshape(2, 2)
    guard_s = carried["time_s"]
    if guard_s > 0.:
        end = path_time[-1]
        moved, _ = affine_weights(guard_s)
        projected = project_passive(path_time, path_values, end - guard_s, end, end, moved) if path_projection else None
        guard[4] = continuous_step(evaluate, timer, loads(last), guard_inputs, guard_s, projected)[0]
    else:
        guard[4] = timer[0]
    event = crossing(guard, guard_s)
    if event is None:
        return None
    cross, tail = event[0], event[-1]
    pre = cell_current(evaluate, np.array([previous[[0, 9]], last[[0, 9]]]), np.array(history[-2:]))
    x = RATE[0] * PERIOD
    xt = RATE[0] * cross
    m0 = np.expm1(xt) * np.exp(-x) / MOVE[0]
    m1 = (xt * np.exp(xt) - np.expm1(xt)) * np.exp(-x) / (x * MOVE[0])
    attack = np.array([m0 * pre[1, 0] + m1 * (pre[1, 0] - pre[0, 0]) + tail, pre[1, 1]])
    time, ports = post_at(post, np.asarray(carried["load_weights"]), coupled)
    event_path = (path_time, path_values, carried["slot"] * PERIOD) if mode == "projected_path" else None
    passive = event_passive(loads(last)[1], loads(previous)[1], time, ports, cross, mode, event_path)
    history.append(advance(timer, attack, passive))
    return dict(slot=carried["slot"], crossing_s=float(cross), timer=np.asarray(history),
                states=states, attack=attack, passive=passive)
