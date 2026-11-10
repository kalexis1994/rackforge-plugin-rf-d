"""C7-clocked C2/C5 carry for the two negative KEY edges."""
import numpy as np

from rf_d_pilot_timer_carry import MOVE, PERIOD, continuous_step, project_passive

NODES = (20, 26, 40, 28, 42, 11, 0, 47, 29)
POINTS = 65
PERTURBATION_V = .01
CAP_C7 = 100e-9
R55 = 47_000.
R60_TRIGGER = 100_000.
DIODE_SCALE = 1.5 * (1.380649e-23 * 298.15 / 1.602176634e-19)
DIODE_IS_A = 1e-8


def trace(stages):
    c7 = stages[:, 21]
    sign = float(np.sign(c7[-1] - c7[0]))
    delta = sign * (c7 - c7[0])
    assert (np.diff(delta) > 0.).all()
    assert (stages[:, 26] > stages[:, 28]).all() and (stages[:, 40] > stages[:, 42]).all()
    # The first row retains the old KEY-side algebraic state.
    return sign, delta[1:], stages[1:, NODES]


def family(traces):
    direction = traces[0][0]
    assert all(sign == direction for sign, _, _ in traces)
    progress = np.linspace(0., min(x[-1] for _, x, _ in traces), POINTS)
    samples = np.array([[np.interp(progress, x, row) for row in values.T] for _, x, values in traces])
    nominal, c2_up, c2_down, c5_up, c5_down = samples
    slope = np.array([(c2_up - c2_down) * .5, (c5_up - c5_down) * .5])
    curve = np.array([(c2_up + c2_down) * .5 - nominal, (c5_up + c5_down) * .5 - nominal])
    return direction, progress, nominal, slope, curve


def key_side(capacitor, key):
    """Eliminate x22 with the original diode and 100 kΩ current."""
    ratio = R60_TRIGGER * DIODE_IS_A / DIODE_SCALE
    source = (key - capacitor) / DIODE_SCALE
    exponent = source + ratio
    conducting = source > 0.
    exponent[conducting] = np.log1p(source[conducting] / ratio)
    for _ in range(8):
        error = exponent + ratio * np.expm1(exponent) - source
        exponent -= error / (1. + ratio * np.exp(exponent))
    residual = exponent + ratio * np.expm1(exponent) - source
    assert abs(residual).max() <= 2e-12
    return key - DIODE_SCALE * exponent


def run(evaluate, model, initial, nominal_seed, key, frames):
    direction, progress, center, linear, quadratic = model
    if not initial[26] > initial[28] or not initial[40] > initial[42]:
        return None
    timers = initial[[5, 38]].copy()
    offset = (timers - nominal_seed[[5, 38]]) / PERTURBATION_V
    if abs(offset).max() > 1.:
        return None
    values = center + np.einsum("i,ijk->jk", offset, linear) + np.einsum("i,ijk->jk", offset ** 2, quadratic)
    c7 = initial[21] + direction * progress
    x22 = key_side(c7, key)
    speed = direction / CAP_C7 * ((values[0] - c7) / R55 + (x22 - c7) / R60_TRIGGER)
    if (speed <= 0.).any():
        return None
    relative = np.diff(speed) / speed[:-1]
    ratio = np.ones_like(relative)
    changed = relative != 0.
    ratio[changed] = np.log1p(relative[changed]) / relative[changed]
    durations = np.diff(progress) / speed[:-1] * ratio
    times = np.r_[0., np.cumsum(durations)]
    clock = np.arange(2 * frames + 1) * PERIOD
    if clock[-1] >= times[-1]:
        return None
    i = np.searchsorted(times, clock, side="right") - 1
    u = (clock - times[i]) / durations[i]
    frac = u.copy()
    nonconstant = changed[i]
    frac[nonconstant] = np.expm1(np.log1p(relative[i][nonconstant]) * u[nonconstant]) / relative[i][nonconstant]
    nodes = values[:, i] + frac * (values[:, i+1] - values[:, i])
    memory = c7[i] + frac * (c7[i+1] - c7[i])
    outputs = [timers.copy()]
    for k in range(len(clock) - 1):
        left = nodes[1:3, k], nodes[5:, k].reshape(2, 2)
        right = nodes[1:3, k+1], nodes[5:, k+1].reshape(2, 2)
        passive = project_passive(times, values[5:], clock[k], clock[k+1], clock[k+1], MOVE)
        timers = continuous_step(evaluate, timers, left, right, PERIOD, passive)
        outputs.append(timers)
    timers = np.array(outputs)
    return timers, nodes.T, memory
