"""Test the -10 V ripple scale at 1.25 mV and isolate the R37 tuning path."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
import json
from pathlib import Path

import check_vco_neg10_ripple as ripple
import check_vco_shared_neg4 as shared
import vco1_circuit_reference as vco
import voice_circuit_reference as voice

RECEIPT = vco.ROOT / "evidence/vco_neg10_r37_01.json"
AMPLITUDE_V = .00125


def deck(scene, export, route):
    peak = 0. if route == "quiet" else AMPLITUDE_V
    text, metadata = ripple.deck(scene, export, "rail", peak, 1e-5)
    if route == "r37":
        supply = "Vneg10 NEG10_V NEG10_TEST -10"
        tuning = "RR37 R37_TOP NEG10_V 11800"
        assert text.count(supply) == text.count(tuning) == 1
        text = text.replace(supply, "Vneg10 NEG10_V 0 -10\nVneg10_r37 NEG10_R37 NEG10_TEST -10", 1)
        text = text.replace(tuning, tuning.replace("NEG10_V", "NEG10_R37"), 1)
    for source in (__file__, ripple.__file__):
        path = Path(source)
        metadata["source_sha256"][path.relative_to(vco.ROOT).as_posix()] = vco.sha(path)
    return text, metadata


def experiment(note, reference):
    settings = dict(reference["trials"]["quiet"]["run"]["scenario"])
    oscillator = vco.Scenario(**settings.pop("oscillator"))
    scene = voice.Scenario(oscillator=replace(oscillator, duration_s=.124), **settings)
    results = {}
    for route in ("quiet", "rail", "r37"):
        label = f"neg10-r37-{note.lower()}-{route}"
        raw, info = shared.circuit_run(scene, label, lambda s, p: deck(s, p, route), ripple.SIGNALS)
        _, middle, local = ripple.edges(raw)
        if route == "quiet":
            baseline, baseline_local = middle, local
            results["quiet_run"] = info
        else:
            fit = ripple.harmonic(baseline, middle - baseline)
            local_fit = ripple.harmonic(baseline, local - baseline_local)
            gain = reference["trials"]["rail-8mv-fine"]["edge_sensitivity_s_per_v"]
            results[route] = dict(edge_count=len(middle), edge_shift_s=fit, local_delay_s=local_fit,
                                  relative_to_full_rail_prediction=fit["peak"] / (gain * AMPLITUDE_V), run=info)
            print(note, route, fit, flush=True)
        shared.retire(label)
    assert abs(results["rail"]["relative_to_full_rail_prediction"] - 1.) < .05
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-report", action="store_true")
    args = parser.parse_args()
    source = vco.read(ripple.RECEIPT)
    with ThreadPoolExecutor(max_workers=2) as pool:
        trials = {note: pool.submit(experiment, note, ref) for note, ref in source["notes"].items()}
        results = {note: trial.result() for note, trial in trials.items()}
    report = dict(schema="rf-d/vco-neg10-r37/v1", input_peak_v=AMPLITUDE_V,
                  input_frequency_hz=ripple.FREQUENCY_HZ, ripple_sha256=vco.sha(ripple.RECEIPT),
                  notes=results)
    if args.write_report:
        RECEIPT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
