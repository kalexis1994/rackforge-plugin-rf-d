"""Integrate Q25 collector time and attack charge along a sparse voltage path."""
import numpy as np

VT = 1.380649e-23 * 298.15 / 1.602176634e-19
RATE = 96_000
COLLECTOR = 26
NEIGHBORS = [25, 27, 9, 5]


def extract(stages, steps):
    """Locate the crossing and extract only the monotone collector segment."""
    assert len(stages) == 2 * steps + 1
    time = np.r_[0., (np.arange(steps)[:, None] + [1. / 3., 1.]).ravel()] / (steps * RATE)
    difference = stages[:, COLLECTOR] - stages[:, 28]
    changes = np.flatnonzero((difference[:-1] < 0.) & (difference[1:] >= 0.))
    assert len(changes) == 1
    i = changes[0]
    fraction = -difference[i] / (difference[i+1] - difference[i])
    at = stages[i] + fraction * (stages[i+1] - stages[i])
    cross_time = time[i] + fraction * (time[i+1] - time[i])
    cross = float(at[COLLECTOR])
    c = stages[:, COLLECTOR]
    low, high = min(.25, .5 * cross), 8.
    begin = np.flatnonzero(c >= low)[0] - 1
    end = np.flatnonzero(c >= high)[0] + 1
    assert begin >= 0 and low < cross < high and end <= len(c)
    cut = slice(begin, end)
    assert (np.diff(c[cut]) > 0.).all(), c[cut].tolist()
    values = stages[cut][:, NEIGHBORS]
    return dict(bounds=[low, cross, high], time=float(cross_time),
                crossing=at[NEIGHBORS], voltages=c[cut], states=values, times=time[cut])


def landmarks(path, points):
    edges = [np.linspace(a, b, points + 1) for a, b in zip(path["bounds"], path["bounds"][1:])]
    columns = np.r_[edges[0], edges[1][1:]]
    values = np.stack([np.interp(columns, path["voltages"], row) for row in path["states"].T], axis=1)
    values[points] = path["crossing"]
    return columns, values


def collector_density(collector, values, base_slope, evaluate):
    base, neighbor, emitter, timer = values.T
    ports = evaluate(collector, timer)
    vbc = base - collector
    forward = 1e-14 * np.expm1(base / VT)
    reverse = 1e-14 * np.expm1(vbc / VT)
    decay_base = (1e-14 * np.expm1((collector - emitter) / VT) / 100.
                  + 1e-14 * np.expm1((collector - 9.3) / VT) / 5.)
    dc = -ports[:, 3] + (collector - neighbor) / 33_000. + forward - 1.2 * reverse + decay_base
    # The collector's only stored charge is the Q25 BC terminal.
    knee = .4 * .7
    knee_cap = 5e-12 * (1. - .4)**(-.33)
    cap = np.where(vbc < knee, 5e-12 * (1. - vbc / .7)**(-.33),
                   knee_cap * (1. + .33 * (vbc - knee) / (.7 * .6)))
    cap += 3e-9 * 1e-14 * np.exp(vbc / VT) / VT
    return -cap * (1. - base_slope) / dc, ports[:, 2]


def attack_area(target, source, points, evaluate, rate_x, pre, post, pre_slope, post_slope,
                post_only=False):
    columns, values = landmarks(source, points)
    if source is not target:
        # Transfer the two voltage spans and anchor every neighboring node
        # at the new crossing state. The reserved path supplies no shape.
        bounds = target["bounds"]
        columns = np.r_[np.linspace(bounds[0], bounds[1], points + 1),
                        np.linspace(bounds[1], bounds[2], points + 1)[1:]]
        values += target["crossing"] - source["crossing"]
    before_count = points
    if post_only:
        columns = columns[points:]
        values = values[points:]
        before_count = 0
    panel = 8
    sub = (np.arange(panel) + .5) / panel
    increments = np.diff(columns)
    abscissa = (columns[:-1, None] + increments[:, None] * sub).ravel()
    states = (values[:-1, None, :] + np.diff(values, axis=0)[:, None, :] * sub[:, None]).reshape(-1, 4)
    base_slope = np.repeat(np.diff(values[:, 0]) / increments, panel)
    density, current = collector_density(abscissa, states, base_slope, evaluate)
    if not np.isfinite(density).all() or (density <= 0.).any():
        return dict(passed=False, reason="nonpositive collector time density",
                    min_density_s_per_v=float(density.min()))
    dt = density * np.repeat(increments / panel, panel)
    from_cross = np.r_[0., np.cumsum(dt)] - dt[:before_count * panel].sum()
    at = target["time"] + (from_cross[:-1] + .5 * dt)
    fraction = at * RATE
    if not ((0. <= fraction) & (fraction <= 1.)).all():
        return dict(passed=False, reason="predicted pulse outside current interval",
                    support_fraction=[float(fraction.min()), float(fraction.max())])
    baseline = np.where(at < target["time"], pre + pre_slope * fraction,
                        post + post_slope * (fraction - 1.))
    weight = rate_x / -np.expm1(-rate_x)
    area = np.sum((current - baseline) * np.exp(rate_x * (fraction - 1.)) * dt)
    want_times = np.interp(target["bounds"], target["voltages"], target["times"])
    return dict(correction_a=float(weight * RATE * area),
                pre_area_c=float(np.sum((current - baseline)[:before_count * panel] * dt[:before_count * panel])),
                evaluations=len(current), area_c=float(area), start_s=float(target["time"] + from_cross[0]),
                end_s=float(target["time"] + from_cross[-1]),
                reference_support_s=[float(want_times[0]), float(want_times[-1])])
