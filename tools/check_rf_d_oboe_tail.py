"""Measure the stereo component of the Oboe recording after the last note."""
import json
import wave

import numpy as np

from check_rf_d_oboe_ab import DEMO, FRAMES, REFERENCE, REFERENCE_SHA256, frames_at
from check_rf_d_oboe_refit import AUDITION, RECEIPT as REFIT
from check_rf_d_playable_voice import ROOT, SAMPLE_RATE, sha

WINDOWS_MS = ((1410, 1490), (1515, 1540), (1605, 1630), (1665, 1690), (1695, 1720), (1725, 1760))
RECEIPT = ROOT / "evidence/rf_d_oboe_tail01.json"


def read_take(path, expected_sha, channels, start=0):
    assert sha(path) == expected_sha, path
    with wave.open(str(path), "rb") as stream:
        assert (stream.getnchannels(), stream.getsampwidth(), stream.getframerate()) == (channels, 2, SAMPLE_RATE)
        stream.setpos(start)
        samples = np.frombuffer(stream.readframes(FRAMES), dtype="<i2")
    assert samples.size == channels * FRAMES
    return samples.reshape(-1, channels).astype(np.float64) / 32768.


def power(samples):
    return float(np.mean(samples**2))


def db(ratio):
    return float(10. * np.log10(ratio))


def compare(reference, candidate):
    sustain_start, sustain_end = map(frames_at, WINDOWS_MS[0])
    reference_level = power(reference[sustain_start:sustain_end].mean(axis=1))
    candidate_level = power(candidate[sustain_start:sustain_end])
    rows = []
    for start, end in WINDOWS_MS:
        region = slice(frames_at(start), frames_at(end))
        left, right = reference[region].T
        mid = (left + right) / 2.
        side = (left - right) / 2.
        # A scalar difference in left/right gain projects onto the mono signal.
        residual = side - mid * (mid @ side) / (mid @ mid)
        freq = np.fft.rfftfreq(16384, 1. / SAMPLE_RATE)
        spectrum = abs(np.fft.rfft((residual - residual.mean()) * np.hanning(residual.size), 16384))**2
        audible = (freq >= 100) & (freq <= 6000)
        near_note_harmonics = abs(freq - np.rint(freq / 500.) * 500.) <= 55
        rows.append(dict(
            window_ms=[start, end], correlation=float(np.corrcoef(left, right)[0, 1]),
            residual_side_over_mid_db=db(power(residual) / power(mid)),
            residual_side_near_final_note_fraction=float(spectrum[audible & near_note_harmonics].sum()
                                                        / spectrum[audible].sum()),
            reference_mid_db_over_sustain=db(power(mid) / reference_level),
            rf_d_db_over_sustain=db(power(candidate[region]) / candidate_level),
        ))
    return rows


def main():
    refit = json.loads(REFIT.read_bytes())
    audition = refit["audition"]
    candidate_start, = (take["start_frame"] for take in audition["playlist"] if take["source"] == "RF-D adjusted")
    reference = read_take(REFERENCE, REFERENCE_SHA256, 2)
    candidate = read_take(AUDITION, audition["sha256"], 1, candidate_start)[:, 0]
    rows = compare(reference, candidate)
    report = dict(source=DEMO, reference_sha256=REFERENCE_SHA256, audition_sha256=audition["sha256"],
                  sample_rate_hz=SAMPLE_RATE, last_note_off_ms=1510,
                  near_harmonic_mask=dict(fundamental_hz=500, radius_hz=55, limits_hz=[100, 6000]),
                  measurements=rows)
    output = json.dumps(report, indent=2, allow_nan=False) + "\n"
    RECEIPT.write_text(output, encoding="utf8", newline="\n")
    print(output, end="")


if __name__ == "__main__":
    main()
