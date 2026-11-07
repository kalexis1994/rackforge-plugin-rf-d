"""Prepare H128 interpolation and a compact saw/phase derivative table from training only."""

import math
import re

import numpy as np

from prepare_dual_chain import ROOT
from vco_family import CV, COLS, coefficients, complex_coeff, decode_window, lagrange

LEGACY = "tools/family_mixer_data128.rs"
BUSES = np.array([-1., -.125, .125, 1.])
H = 128
PHASE_SAMPLES = 4096
TABLE = "h128-voice-bus.bin"


def window_coefficients(item):
    raw = decode_window(item["window"], ROOT / item["window_pack"])
    start, end = item["measurements"]["reset_crossings_s"][-2:]
    times = raw[:, 0]
    knots = np.r_[start, times[(times > start) & (times < end)], end]
    phase = (knots - start) / (end - start)
    phase[0], phase[-1] = 0., 1.
    result = np.array([coefficients(phase, np.interp(knots, times, raw[:, i]), H) for i in COLS])
    assert np.array_equal(result[:, :65], complex_coeff(item["reduction"]))
    return result


def training_image(training):
    text = (ROOT / LEGACY).read_text(encoding="utf8")
    pat = r"[-+]?\d+\.\d+(?:e[-+]?\d+)?"
    logs, waves = (part.split("=", 1)[1] for part in text.split("pub const ")[1:])
    old_logs = np.array(re.findall(pat, logs), dtype="f8").reshape(4, 2)
    old_waves = np.array(re.findall(pat, waves), dtype="f8").reshape(4, 2, 7, H + 1, 2)
    assert len(training) == 8
    frequency = np.empty((4, 4))
    frequency[:, 1:3] = old_logs
    model = np.empty((4, 4, 7, H + 1), dtype="complex128")
    model[:, 1:3] = old_waves[..., 0] + 1j * old_waves[..., 1]
    for index, item in enumerate(training):
        row, side = divmod(index, 2)
        col = 3 * side
        assert item["scenario"]["keyboard_v"] == CV[row]
        assert item["scenario"]["imposed_mixer_v"] == BUSES[col]
        model[row, col] = window_coefficients(item)
        frequency[row, col] = math.log2(item["reduction"]["frequency_hz"])
    return frequency, model


def prediction(frequency, model, cv, bus):
    assert CV[0] <= cv <= CV[-1] and BUSES[0] <= bus <= BUSES[-1]
    interval = int(np.searchsorted(BUSES[1:-1], bus, side="right"))
    delta = BUSES[interval + 1] - BUSES[interval]
    alpha = (bus - BUSES[interval]) / delta
    weights, _ = lagrange(cv)
    blend = np.array([1. - alpha, alpha])
    logs = weights @ frequency[:, interval:interval + 2]
    z = np.einsum("i,ijck->jck", weights, model[:, interval:interval + 2])
    hz = 2. ** float(logs @ blend)
    return dict(frequency_hz=hz, frequency_dbus=hz * math.log(2.) * float(logs[1] - logs[0]) / delta,
                c=np.einsum("j,jck->ck", blend, z), dbus=(z[1] - z[0]) / delta)


def hermite_image(logs, model):
    saw = model[:, :, 0]
    harmonics = np.arange(H + 1)
    spectrum = saw.copy()
    spectrum[..., 1:] *= 2.
    derivative = spectrum * (2j * np.pi * harmonics)
    values = np.fft.ifft(spectrum, n=PHASE_SAMPLES).real * PHASE_SAMPLES
    slopes = np.fft.ifft(derivative, n=PHASE_SAMPLES).real
    table = np.stack([values, slopes], axis=-1)
    bound = float(np.max(np.sum(abs(spectrum) * (2 * np.pi * harmonics)**4, axis=-1))
                  / (384 * PHASE_SAMPLES**4))
    return np.asarray(logs, "<f8").tobytes() + np.asarray(table, "<f8").tobytes(), bound
