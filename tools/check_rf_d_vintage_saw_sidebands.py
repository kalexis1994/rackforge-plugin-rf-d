"""Check continuous sidebands for phase and amplitude modulation in the saw take."""
import argparse
import json

import numpy as np

import check_rf_d_vintage_saw_reset_residual as edge

RECEIPT = edge.ROOT / "evidence/rf_d_vintage_saw_sidebands01.json"
BANDS_HZ = ((500, 3500), edge.PREDICTOR_BAND, edge.BAND)
FREQUENCIES_HZ = (50., 60., 100., 120.)


def cycle_derivative(cycle):
    # Spectral differentiation avoids the high-frequency gain error of a
    # centered difference. Analyze only the interior of the reflected trace.
    pad = edge.ANALYSIS.start
    extended = np.pad(cycle, pad, mode="reflect")
    frequencies = np.fft.rfftfreq(extended.size, 1. / edge.SAMPLE_RATE)
    derivative = np.fft.irfft(2j * np.pi * frequencies * np.fft.rfft(extended), n=extended.size)
    return derivative[pad:-pad]


def columns(cycle, frequency, band):
    t = np.arange(cycle.size) / edge.SAMPLE_RATE
    angle = 2. * np.pi * frequency * t
    oscillation = np.column_stack((np.sin(angle), np.cos(angle)))
    derivative = cycle_derivative(cycle)
    amplitude = cycle - cycle.mean()
    products = np.column_stack((oscillation * derivative[:, None], oscillation * amplitude[:, None]))
    # Apply the same output band to both measured and predicted sidebands.
    return np.column_stack([edge.bandpass(col, band)[edge.ANALYSIS] for col in products.T])


def score(predicted, observed):
    return float(1. - np.sum((observed - predicted)**2) / np.sum(observed**2))


def measures(audio, cycle, frequency):
    residual = audio - cycle
    arrays = [(columns(cycle, frequency, band), edge.bandpass(residual, band)[edge.ANALYSIS]) for band in BANDS_HZ]
    result = []
    for basis, target in arrays:
        coeff = np.linalg.lstsq(basis, target, rcond=None)[0]
        timing = complex(*coeff[:2])
        amp = complex(*coeff[2:])
        result.append(dict(timing_peak_us=abs(timing) * 1e6, timing_phase_deg=float(np.angle(timing, deg=True)),
                           amplitude_peak_ratio=abs(amp), amplitude_phase_deg=float(np.angle(amp, deg=True)),
                           timing_variance_fraction=score(basis[:, :2] @ coeff[:2], target),
                           amplitude_variance_fraction=score(basis[:, 2:] @ coeff[2:], target)))
    validation = {
        key: held_out([(basis[:, indexes], target) for basis, target in arrays])
        for key, indexes in (("timing", slice(0, 2)), ("amplitude", slice(2, 4)), ("joint", slice(0, 4)))
    }
    return dict(fits=result, held_out_variance_fraction=validation)


def held_out(arrays):
    # Train in the middle band on one temporal half and predict each band on
    # the disjoint half, retaining the same absolute time origin.
    samples = arrays[0][1].size
    power = np.zeros((len(arrays), 2))
    for train, test in ((slice(None, samples // 2), slice(samples // 2, None)),
                        (slice(samples // 2, None), slice(None, samples // 2))):
        basis, target = arrays[1]
        coeff = np.linalg.lstsq(basis[train], target[train], rcond=None)[0]
        for acc, (basis, target) in zip(power, arrays, strict=True):
            predicted = basis[test] @ coeff
            observed = target[test]
            acc += [np.sum((predicted - observed)**2), np.sum(observed**2)]
    return (1. - power[:, 0] / power[:, 1]).tolist()


def simultaneous_timing(audio, cycle):
    residual = audio - cycle
    frequencies = (100., 120.)
    arrays = []
    fits = []
    for band in BANDS_HZ:
        basis = np.column_stack([columns(cycle, hz, band)[:, :2] for hz in frequencies])
        target = edge.bandpass(residual, band)[edge.ANALYSIS]
        coeff = np.linalg.lstsq(basis, target, rcond=None)[0]
        fits.append((np.linalg.norm(coeff.reshape(2, 2), axis=1) * 1e6).tolist())
        arrays.append((basis, target))
    return dict(frequencies_hz=frequencies, timing_peak_us=fits, held_out_variance_fraction=held_out(arrays))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-report", action="store_true")
    args = parser.parse_args()
    notes = {}
    for (note, _), audio in zip(edge.NOTES, edge.read_reference(), strict=True):
        _, cycle, frequency = edge.track(audio)
        notes[note] = dict(
            fundamental_hz=frequency,
            trials={str(int(hz)): measures(audio, cycle, hz) for hz in FREQUENCIES_HZ},
            simultaneous_timing=simultaneous_timing(audio, cycle),
        )
    report = dict(schema="rf-d/vintage-saw-sidebands/v1", reference_sha256=edge.REFERENCE_SHA256,
                  source_mp3_sha256=edge.SOURCE_SHA256, sample_rate_hz=edge.SAMPLE_RATE,
                  analysis_frames=[edge.ANALYSIS.start, audio.size + edge.ANALYSIS.stop],
                  bands_hz=BANDS_HZ, training_band_index=1, notes=notes)
    print(json.dumps(report, indent=2))
    if args.write_report:
        RECEIPT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
