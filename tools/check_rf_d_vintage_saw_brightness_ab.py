"""Audition a small high-frequency lift on the clean trapezoidal render."""
import argparse
import json

import numpy as np

from check_rf_d_ladder_trapezoidal_ab import AUDITION as LADDER_AUDIO, RECEIPT as LADDER_REPORT
from check_rf_d_oboe_ab import write_audition
from check_rf_d_playable_voice import ROOT, SAMPLE_RATE, sha, write
from check_rf_d_vintage_saw_ab import FRAMES, NOTES, REFERENCE_SHA256, read_reference
from check_rf_d_vintage_saw_air import ANALYSIS, BANDS_HZ, RECEIPT as AIR_REPORT, band_power, read_renders

AUDITION = ROOT / "artifacts/rf-d-sierra-brillo-limpio-ab.wav"
RECEIPT = ROOT / "evidence/rf_d_vintage_saw_brightness_ab01.json"
# The sustained La2 shows roughly 0.7–0.9 dB of periodic deficit from 4 to 12 kHz.
LIFT_HZ = (2_500., 4_000., 10_000., 17_000.)
LIFT_DB = (0., 0.8, 0.8, 0.)


def lift_highs(audio, *, knots_hz=LIFT_HZ, gains_db=LIFT_DB):
    pad = FRAMES // 2
    padded = np.pad(audio, pad, mode="reflect")
    frequencies = np.fft.rfftfreq(padded.size, 1. / SAMPLE_RATE)
    gain_db = np.zeros_like(frequencies)
    for lo, hi, low_db, high_db in zip(knots_hz[:-1], knots_hz[1:], gains_db[:-1], gains_db[1:], strict=True):
        band = (frequencies >= lo) & (frequencies < hi)
        position = (frequencies[band] - lo) / (hi - lo)
        gain_db[band] = low_db + (high_db - low_db) * (0.5 - 0.5 * np.cos(np.pi * position))
    gain = 10. ** (gain_db / 20.)
    result = np.fft.irfft(np.fft.rfft(padded) * gain, n=padded.size)[pad:pad + FRAMES]
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-report", action="store_true")
    args = parser.parse_args()
    renders = read_renders()
    takes = {}
    measurements = {}
    for (note, _), original in zip(NOTES, read_reference(), strict=True):
        clean = renders[f"RF-D trapezoidal {note}"]
        brighter = lift_highs(clean)
        before, before_total = band_power(clean)
        after, after_total = band_power(brighter)
        delta = 10. * np.log10((after / after_total) / (before / before_total))
        assert 0.6 < delta[2] < 0.85
        assert abs(10. * np.log10(after_total / before_total)) < 0.02
        measurements[note] = delta.tolist()
        takes[f"Minimoog {note}"] = original[ANALYSIS]
        takes[f"RF-D limpio {note}"] = clean[ANALYSIS]
        takes[f"RF-D con realce {note}"] = brighter[ANALYSIS]

    order = tuple(takes)
    report = dict(
        reference_sha256=REFERENCE_SHA256, ladder_receipt_sha256=sha(LADDER_REPORT),
        ladder_audition_sha256=sha(LADDER_AUDIO), air_receipt_sha256=sha(AIR_REPORT),
        sample_rate_hz=SAMPLE_RATE, lift_hz=LIFT_HZ, lift_db=LIFT_DB, bands_hz=BANDS_HZ,
        band_delta_db_over_total=measurements, audition_gain_order=order,
        audition=write_audition(takes, order * 2, AUDITION),
    )
    if args.write_report:
        write(RECEIPT, report)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
