"""Check how much of the vintage saw residual follows common phase variation."""
import argparse
import json

import numpy as np

from check_rf_d_playable_voice import ROOT, SAMPLE_RATE, sha, write
from check_rf_d_vintage_saw_ab import NOTES, REFERENCE_SHA256, read_reference
from check_rf_d_vintage_saw_air import (
    ANALYSIS, BANDS_HZ, PRIOR_AUDIO, RECEIPT as AIR_REPORT, band_power, fit_cycle, read_renders, saw_phase,
)

RECEIPT = ROOT / "evidence/rf_d_vintage_saw_phase01.json"
GROUPS = ((2, 4, 6), (3, 5, 7))
SMOOTHING_HZ = 35.
HALF_WINDOW_FRAMES = 2_400


def phase_corrections(audio, phase):
    time = np.arange(-HALF_WINDOW_FRAMES, HALF_WINDOW_FRAMES + 1) / SAMPLE_RATE
    kernel = np.sinc(2. * SMOOTHING_HZ * time) * np.hanning(time.size)
    kernel /= kernel.sum()
    deviations = {}
    for harmonic in sorted(n for group in GROUPS for n in group):
        baseband = audio * np.exp(-1j * harmonic * phase)
        padded = np.pad(baseband, HALF_WINDOW_FRAMES, mode="reflect")
        envelope = np.convolve(padded, kernel, mode="valid")
        center = envelope[ANALYSIS].mean()
        deviations[harmonic] = np.angle(envelope / center) / harmonic
    return [np.median([deviations[n] for n in group], axis=0) for group in GROUPS]


def measure(audio):
    phase, fundamental = saw_phase(audio)
    periodic = fit_cycle(audio, phase, fundamental)
    initial, _ = band_power(audio - periodic)
    _, power = band_power(audio)
    corrections = phase_corrections(audio, phase)
    combined = np.mean(corrections, axis=0)
    results = []
    for correction in (*corrections, combined):
        fitted = fit_cycle(audio, phase + correction, fundamental)
        residual, _ = band_power(audio - fitted)
        results.append(dict(
            correction_rms_rad=float(np.std(correction[ANALYSIS])),
            residual_delta_db=(10. * np.log10(residual / initial)).tolist(),
            residual_db_over_signal=(10. * np.log10(residual / power)).tolist(),
        ))
    return dict(
        fundamental_hz=fundamental,
        initial_residual_db_over_signal=(10. * np.log10(initial / power)).tolist(),
        group_phase_correlation=float(np.corrcoef([part[ANALYSIS] for part in corrections])[0, 1]),
        phase_estimates=results,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-report", action="store_true")
    args = parser.parse_args()
    reference = read_reference()
    renders = read_renders()
    results = {name: dict(minimoog=measure(audio), rf_d=measure(renders[f"RF-D trapezoidal {name}"]))
               for (name, _), audio in zip(NOTES, reference, strict=True)}
    report = dict(
        reference_sha256=REFERENCE_SHA256, previous_audition_sha256=sha(PRIOR_AUDIO),
        air_receipt_sha256=sha(AIR_REPORT), sample_rate_hz=SAMPLE_RATE, bands_hz=BANDS_HZ,
        phase_groups=GROUPS, smoothing_hz=SMOOTHING_HZ, smoothing_half_window_frames=HALF_WINDOW_FRAMES,
        phase_estimate_order=["even harmonics", "odd harmonics", "mean of group estimates"],
        results=results,
    )
    if args.write_report:
        write(RECEIPT, report)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
