"""Audition the trapezoidal ladder against the current RF-D and the vintage saw."""
import argparse
import json

import numpy as np

from check_rf_d_oboe_ab import write_audition
from check_rf_d_playable_voice import ROOT, main as build_voice, sha, write
from check_rf_d_vintage_saw_ab import NOTES, RECEIPT as BASELINE, compare, read_reference

AUDITION = ROOT / "artifacts/rf-d-sierra-filtro-ab.wav"
RECEIPT = ROOT / "evidence/rf_d_ladder_trapezoidal_ab01.json"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-report", action="store_true")
    args = parser.parse_args()
    reference = read_reference()
    previous = json.loads(BASELINE.read_bytes())
    takes = {}
    modes = {}

    def inspect_mode(label, trapezoidal):
        timings = []

        def inspect(render, schema, component):
            def timed_render(events, *, frames, block):
                audio, samples = render(events, frames=frames, block=block)
                if block == 128:
                    # Use only full callbacks from the sustained portion of each note.
                    timings.extend(samples[80:frames // block])
                return audio, samples

            clips, measured = compare(reference, timed_render, schema)
            for note, _ in NOTES:
                takes[f"Minimoog {note}"] = clips[f"Minimoog {note}"]
                takes[f"{label} {note}"] = clips[f"RF-D {note}"]
            modes[label] = dict(
                component_sha256=component, notes=measured, bit_equal_block_frames=[128, 480],
                wasm_128_frames_us=dict(zip(("median", "p95", "max"),
                                            (np.percentile(timings, [50, 95, 100]) / 1000.).tolist())),
            )

        build_voice(["--midi"], inspect_audio=inspect, oversampling=4, trapezoidal_ladder=trapezoidal)

    inspect_mode("RF-D actual", False)
    baseline = modes["RF-D actual"]
    assert baseline["component_sha256"] == previous["oversampling"]["4x"]["component_sha256"]
    assert json.dumps(baseline["notes"]) == json.dumps(previous["oversampling"]["4x"]["notes"])
    inspect_mode("RF-D trapezoidal", True)
    candidate = modes["RF-D trapezoidal"]
    assert baseline["component_sha256"] != candidate["component_sha256"]
    deltas = {}
    for old, new in zip(baseline["notes"], candidate["notes"], strict=True):
        bands_old = old["rf_d_minus_minimoog_band_db"]
        bands_new = new["rf_d_minus_minimoog_band_db"]
        deltas[old["note"]] = {band: bands_new[band] - value for band, value in bands_old.items()}
        assert abs(deltas[old["note"]]["H2-H7"]) < 0.6
        assert deltas[old["note"]]["H17-H24"] > 0.

    order = tuple(f"{source} {note}" for note, _ in NOTES
                  for source in ("Minimoog", "RF-D actual", "RF-D trapezoidal"))
    report = dict(
        source=previous["source"], reference_sha256=previous["reference_sha256"],
        baseline_sha256=sha(BASELINE), oversampling=4, modes=modes,
        trapezoidal_minus_current_band_db=deltas,
        audition_gain_order=list(takes),
        audition=write_audition(takes, order * 2, AUDITION),
    )
    if args.write_report:
        write(RECEIPT, report)
    print(json.dumps({
        "difference_db": deltas,
        "timings_us": {label: mode["wasm_128_frames_us"] for label, mode in modes.items()},
        "audition": report["audition"],
    }, indent=2))


if __name__ == "__main__":
    main()
