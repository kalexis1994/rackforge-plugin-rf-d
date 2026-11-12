"""Measure the same RF-D voice at 2x and 4x oversampling."""
import argparse
import json

import numpy as np

from check_rf_d_oboe_ab import DEMO, FRAMES, PREROLL, REFERENCE_SHA256, VOICE_DELAY, read_reference, score, write_audition
from check_rf_d_oboe_articulation import RECEIPT as ARTICULATION
from check_rf_d_oboe_body import RECEIPT as BODY
from check_rf_d_oboe_spectrum import band_levels
from check_rf_d_playable_filter import rms
from check_rf_d_playable_voice import ROOT, SAMPLE_RATE, main as build_voice, sha, write

AUDITION = ROOT / "artifacts/rf-d-oboe-sobremuestreo-ab.wav"
RECEIPT = ROOT / "evidence/rf_d_oboe_oversampling01.json"
BANDS = ((150, 700), (700, 1200), (1200, 2200), (2200, 4000), (4000, 8000),
         (8000, 12000), (12000, 18000))


def sustained_probe(render, schema, settings, note, cutoff):
    # A4 and A6 at nominal tuning fall on exact FFT bins over the last 200 ms.
    assert note in (57, 81)
    hz = 440 * 2 ** ((note - 57) // 12)
    frames = SAMPLE_RATE
    controls = dict(settings, tune=0, cutoff=cutoff, contour_amount=0, loudness_sustain=100)
    events = [event for event in score(schema, controls=controls, keys=((20, 1100, note),))
              if event[1] != 0xb0]
    audio, _ = render(events, frames=frames)
    length = SAMPLE_RATE // 5
    signal = audio[-length:].astype(np.float64)
    spectrum = abs(np.fft.rfft(signal))**2
    frequency = np.fft.rfftfreq(length, 1. / SAMPLE_RATE)
    audible = (frequency >= 20) & (frequency <= 20_000)
    harmonics = frequency % hz == 0
    total = spectrum[audible].sum()
    off_harmonic = spectrum[audible & ~harmonics].sum()
    return dict(fundamental_hz=hz, cutoff=cutoff, rms=rms(signal),
                nonharmonic_energy_db=float(10. * np.log10(off_harmonic / total)))


def compare(reference, prior, duty):
    settings = prior["settings"]
    start = PREROLL + VOICE_DELAY
    variants = {}
    takes = {"Minimoog": reference}
    for factor in (2, 4):
        name = f"RF-D {factor}x"

        def inspect(render, schema, component):
            events = score(schema, controls=settings, keys=prior["gate_ms_and_midi_note"])
            audio, times = render(events, frames=start + FRAMES)
            repeated, _ = render(events, frames=start + FRAMES, block=480)
            assert np.array_equal(audio, repeated)
            candidate = audio[start:]
            assert 0.005 < np.max(abs(candidate)) < 0.8
            takes[name] = candidate
            variants[name] = dict(component_sha256=component, internal_rate_hz=SAMPLE_RATE * factor,
                                  block_128_median_ns=float(np.median(times[8:])),
                                  band_levels_db=band_levels(candidate, BANDS).tolist(),
                                  steady_probes=[sustained_probe(render, schema, settings, note, cutoff)
                                                 for note, cutoff in ((57, settings["cutoff"]), (81, 100))])

        build_voice(["--midi"], inspect_audio=inspect, wide_pulse_duty=duty, oversampling=factor)

    reference_bands = band_levels(reference, BANDS)
    for variant in variants.values():
        difference = np.asarray(variant["band_levels_db"]) - reference_bands
        variant["mean_reference_error_db_by_band"] = abs(difference).mean(axis=0).tolist()
    bands_2x = np.asarray(variants["RF-D 2x"]["band_levels_db"])
    bands_4x = np.asarray(variants["RF-D 4x"]["band_levels_db"])
    report = dict(
        source=DEMO, reference_sha256=REFERENCE_SHA256, articulation_sha256=sha(ARTICULATION),
        prior_component_sha256=prior["component_sha256"],
        sample_rate_hz=SAMPLE_RATE, settings=settings, wide_pulse_duty=duty,
        band_edges_hz=BANDS, reference_band_levels_db=reference_bands.tolist(), variants=variants,
        mean_2x_to_4x_change_db_by_band=abs(bands_4x - bands_2x).mean(axis=0).tolist(),
        bit_equal_block_frames=[128, 480],
    )
    return report, takes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audition", action="store_true", help="write one level-matched comparison WAV")
    parser.add_argument("--write-report", action="store_true", help="save measurements in evidence/")
    args = parser.parse_args()
    prior = json.loads(ARTICULATION.read_bytes())
    body = json.loads(BODY.read_bytes())
    assert prior["reference_sha256"] == body["reference_sha256"] == REFERENCE_SHA256
    assert prior["prior_settings_sha256"] == sha(BODY)
    report, takes = compare(read_reference(), prior, body["wide_pulse_duty"])
    if args.audition:
        order = ("Minimoog", "RF-D 4x", "Minimoog", "RF-D 2x")
        report["audition"] = write_audition(takes, order, AUDITION)
    if args.write_report:
        write(RECEIPT, report)
    print(json.dumps(report, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
