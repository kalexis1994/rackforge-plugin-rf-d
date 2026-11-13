"""Fit a shared high-frequency lift to the periodic part of the vintage saw."""
import argparse
import itertools
import json

import numpy as np

from check_rf_d_oboe_ab import write_audition
from check_rf_d_playable_voice import ROOT, SAMPLE_RATE, sha, write
from check_rf_d_vintage_saw_ab import NOTES, REFERENCE_SHA256, read_reference
from check_rf_d_vintage_saw_air import (
    ANALYSIS, BANDS_HZ, PRIOR_AUDIO, RECEIPT as AIR_REPORT, band_power, periodic_component, read_renders,
)
from check_rf_d_vintage_saw_brightness_ab import LIFT_DB, LIFT_HZ, lift_highs

AUDITION = ROOT / "artifacts/rf-d-sierra-refit-ab.wav"
RECEIPT = ROOT / "evidence/rf_d_vintage_saw_brightness_refit01.json"
AMOUNTS_DB = np.arange(16) / 10.
TAPER_ENDS_HZ = (12_000., 14_000., 17_000., 20_000.)


def levels(periodic):
    bands, total = band_power(periodic)
    return 10. * np.log10(bands / total)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-report", action="store_true")
    args = parser.parse_args()
    reference = read_reference()
    renders = read_renders()
    notes = [name for name, _ in NOTES]
    clean = [renders[f"RF-D trapezoidal {name}"] for name in notes]
    reference_levels = [levels(periodic_component(audio)[0]) for audio in reference]
    periodic = [periodic_component(audio)[0] for audio in clean]
    air = json.loads(AIR_REPORT.read_bytes())
    assert air["reference_sha256"] == REFERENCE_SHA256
    assert air["previous_audition_sha256"] == sha(PRIOR_AUDIO)

    grid = []
    for amount, end in itertools.product(AMOUNTS_DB, TAPER_ENDS_HZ):
        knots = (*LIFT_HZ[:3], end)
        gains = (0., float(amount), float(amount), 0.)
        candidate = levels(lift_highs(periodic[0], knots_hz=knots, gains_db=gains))
        error = float(np.sqrt(np.mean((candidate - reference_levels[0]) ** 2)))
        grid.append(dict(knots_hz=knots, gains_db=gains, fit_error_rms_db=error))
    best = min(grid, key=lambda trial: trial["fit_error_rms_db"])
    settings = dict(knots_hz=best["knots_hz"], gains_db=best["gains_db"])
    assert 0. < best["gains_db"][1] < AMOUNTS_DB[-1]

    takes = {}
    results = {}
    for name, vintage, audio, cycle, target in zip(notes, reference, clean, periodic, reference_levels, strict=True):
        before = levels(cycle)
        earlier = levels(lift_highs(cycle, knots_hz=LIFT_HZ, gains_db=LIFT_DB))
        fitted = levels(lift_highs(cycle, **settings))
        assert np.linalg.norm(fitted - target) < np.linalg.norm(before - target)
        results[name] = dict(
            reference_db=target.tolist(), clean_db=before.tolist(), manual_db=earlier.tolist(),
            fitted_db=fitted.tolist(),
            error_rms_db={label: float(np.sqrt(np.mean((band - target) ** 2)))
                          for label, band in (("clean", before), ("manual", earlier), ("refit", fitted))},
        )
        takes[f"Minimoog {name}"] = vintage[ANALYSIS]
        takes[f"RF-D limpio {name}"] = audio[ANALYSIS]
        takes[f"RF-D con refit {name}"] = lift_highs(audio, **settings)[ANALYSIS]

    order = tuple(takes)
    report = dict(
        reference_sha256=REFERENCE_SHA256, previous_audition_sha256=sha(PRIOR_AUDIO),
        air_receipt_sha256=sha(AIR_REPORT), fit_note=notes[0], reserved_note=notes[1],
        sample_rate_hz=SAMPLE_RATE, bands_hz=BANDS_HZ, settings=settings, trials=grid,
        results=results, audition_gain_order=order, audition=write_audition(takes, order * 2, AUDITION),
    )
    if args.write_report:
        write(RECEIPT, report)
    print(json.dumps(dict(settings=settings, results=results, audition=report["audition"]), indent=2))


if __name__ == "__main__":
    main()
