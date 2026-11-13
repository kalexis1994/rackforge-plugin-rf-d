"""Measure Model D keyboard CV feedthrough with its track-and-hold circuit."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
import json
from pathlib import Path

import numpy as np

import check_vco_dual_rail_ripple as dual
import check_vco_neg10_ripple as ripple
import check_vco_shared_neg4 as shared
import vco1_circuit_reference as vco

RECEIPT = vco.ROOT / "evidence/keyboard_cv_ripple01.json"
MANUALS = {
    "references-local/pdf/service_204d_full_fdiskc.pdf": "d1f96fa26d9e25dda9d1cb0bbe9a5e0b017f7e463ec5b268c380b58d44f5b6fe",
    "references-local/pdf/service_204d_synthfool.pdf": "0edd35f3f9ab1eba346693545f0dcbe374bdcf6f37f9b1a34ecbdeb8ae682b4a",
    "references-local/datasheets/siliconix_fet_1977.pdf": "7f989de7c303bc3280ec06f31246a321cc7ab1e8956333dcd7c1880416812d70",
}
PEAK = dual.PEAK_V
PICKOFFS = (4, 16, 28, 40)
WINDOWS = {"track": (.080, .180), "hold": (.270, .370)}
SIGNALS = ("v(pitch)", "v(mem)", "v(keyboard)", "v(gate13)", "v(src13)", "v(gate10)",
           "v(drain10)", "v(kpos)", "v(kneg)", "v(pitch_test)", "i(vcv_probe)", "v(key_top)")
MATRIX = (("quiet", 0., 0., 0.), ("positive", PEAK, 0., 0.), ("negative", 0., PEAK, 0.),
          ("pitch", 0., 0., PEAK), ("opposite", PEAK, -PEAK, 0.))
# Siliconix 3-26 gives 4–10 mA IDSS and up to 6 V cutoff for 2N4303.
# These two conditional NJF cards bracket the selected model, not all devices.
FETS = {"nominal": (-3.5, .007), "deep-cutoff": (-5.5, .004)}


def stimulus(name, node, dc, ac):
    return f"V{name} {node} 0 SIN({dc} {ac:.17g} {ripple.FREQUENCY_HZ:.17g})"


def keyboard(tap, profile, positive, negative, pitch, load_count=3):
    vto, idss = FETS[profile]
    beta = idss / (vto**2 * 1.15)
    lines = [
        stimulus("kpos", "KPOS", 10, positive),
        stimulus("kneg", "KNEG", -10, negative),
        stimulus("pitch_test", "PITCH_TEST", 0, pitch),
        "Vvirtual KLOAD 0 -5",
        "Rk1 KPOS Q9E 590", "Qk9 KEY_TOP REF_CURRENT Q9E LAB_PNP",
        "Rk20 KPOS Q11B 1k", "Rk22 Q11B 0 1k",
        "Qk11 KPOS Q11B REF_CURRENT LAB_NPN", "Rk25 REF_CURRENT 0 1k",
        "Ck3 REF_CURRENT 0 0.1u",
        f"Rkeys_high KEY_TOP KEY_TAP {(43 - tap)*10}",
        f"Rkeys_low KEY_TAP 0 {tap*10}",
        # Keep the ladder loaded by the held key and add the test in series.
        "Epitch_series TAP_SERIES KEY_TAP PITCH_TEST 0 1",
        "Vpitch_closed 0 PRESS_PITCH PWL(0 -1 .200 -1 .2002 0)",
        "Vtrig_closed 0 PRESS_TRIG PWL(0 -1 .198 -1 .1982 0)",
        "Spitch TAP_SERIES PITCH PRESS_PITCH 0 KEY_CONTACT_SWITCH",
        "Strig KPOS TRIG PRESS_TRIG 0 KEY_CONTACT_SWITCH",
        ".model KEY_CONTACT_SWITCH SW(RON=.05 ROFF=1e12 VT=.5 VH=-.4)",
        "Rk53 KPOS PITCH 4.7meg", "Ck9 PITCH 0 .33u",
        "Rk58 KPOS Q23C 6.2k", "Rk51 KPOS Q14C 560",
        "Qk23 Q23C PITCH DIFF_E LAB_NPN", "Qk14 Q14C Q14B DIFF_E LAB_NPN",
        "Rk52 DIFF_E KNEG 43k", "Rk30 CV Q14B 10k",
        "Qk24 Q24C Q23C KPOS LAB_PNP",
        "Rk59 KPOS Q24C 3.9k", "Rk54 Q24C KNEG 1.5k",
        # R61 includes the zero-ohm bypass across the external glide control.
        "Rk61 Q24C SRC13 330", "Jk13 MEM GATE13 SRC13 LAB_4303",
        "Ck6 MEM 0 1u", "Rk21 MEM GATE10 10k",
        "Rk31 SRC13 DIODE_A 22meg", "Rk64 DIODE_A GATE13 100k",
        "Dk5 DIODE_A DIODE_K LAB_KD", ".model LAB_KD D(IS=1e-12 N=1.5)",
        "Rk65 TRIG DIODE_K 5.1k", "Rk34 DIODE_K KNEG 100k", "Ck13 DIODE_K KNEG .01u",
        "Rk2 KPOS DRAIN10 330", "Jk10 DRAIN10 GATE10 CV LAB_4303",
        "Rk18 CV KNEG 3.9k", "Vcv_probe CV KEYBOARD 0",
        f".model LAB_4303 NJF(VTO={vto:.17g} BETA={beta:.17g} LAMBDA=.0075 "
        "CGS=3p CGD=5.477225575051661p PB=1 IS=3.5e-11 B=1 FC=.4)",
        *(f"Rload{i} KEYBOARD KLOAD 51100" for i in range(load_count)),
    ]
    return lines


def deck(scene, export, tap, profile, case, step):
    base, metadata = ripple.deck(scene, export, "rail", 0., 1e-5)
    model_lines = [line for line in base.splitlines() if line.startswith((".model LAB_NPN", ".model LAB_PNP"))]
    assert len(model_lines) == 2
    vectors = " ".join(SIGNALS)
    content = ["Model D keyboard hold and ripple with the VCO input loads", *model_lines,
               *keyboard(tap, profile, *case),
               ".options temp=25 method=gear maxord=2 reltol=1e-8 abstol=1e-14 vntol=1e-9 gmin=1e-13",
               f".save {vectors}", ".control", "set numdgt=17", "set wr_singlescale", "set wr_vecnames",
               f"tran {step:.17g} {scene.oscillator.duration_s:.17g} 0 {step:.17g}",
               f"wrdata {export.as_posix()} {vectors}", "quit", ".endc", ".end", ""]
    metadata["source_sha256"].update(MANUALS)
    source = Path(__file__)
    metadata["source_sha256"][source.relative_to(vco.ROOT).as_posix()] = vco.sha(source)
    return "\n".join(content), metadata


def fit(time, signal):
    return dual.phasor(ripple.harmonic(time, signal))


def analyze(raw, control):
    windows = {}
    for state, (start, stop) in WINDOWS.items():
        t = np.arange(start, stop, 5e-5)
        actual = np.column_stack([np.interp(t, raw[:, 0], col) for col in raw[:, 1:].T])
        baseline = np.column_stack([np.interp(t, control[:, 0], col) for col in control[:, 1:].T])
        harmonic = {key: dual.record(fit(t, col)) for key, col in zip(SIGNALS, (actual-baseline).T, strict=True)}
        assert abs(actual[:, 2].mean() - actual[:, 0].mean()) < .09 or state == "hold"
        vgs = np.maximum(actual[:, 3] - actual[:, 4], actual[:, 3] - actual[:, 1])
        windows[state] = dict(average=dict(zip(SIGNALS, actual.mean(axis=0).tolist(), strict=True)),
                              q13_max_vgs_v=float(vgs.max()), harmonic=harmonic)
    return windows


def sweep(tap, profile, step, cases):
    from voice_circuit_reference import Scenario

    scene = Scenario(oscillator=replace(vco.Scenario(), duration_s=.38, max_step_s=step))
    results = {}
    for name, *case in cases:
        label = f"key-cv-smooth-{tap}-{profile}-{name}-{round(step*1e6)}"
        raw, run = shared.circuit_run(scene, label, lambda s, p: deck(s, p, tap, profile, case, step), SIGNALS)
        if name == "quiet":
            control = raw
        windows = analyze(raw, control)
        assert windows["hold"]["q13_max_vgs_v"] < FETS[profile][0]
        assert abs(windows["hold"]["average"]["v(keyboard)"] - windows["track"]["average"]["v(keyboard)"]) < .02
        results[name] = dict(inputs_peak_v=case, windows=windows, run=run)
        shared.retire(label)
    print(tap, profile, step, {name: [row["windows"][st]["harmonic"]["v(keyboard)"]["peak"]*1e6
                                     for st in WINDOWS] for name, row in results.items()}, flush=True)
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-report", action="store_true")
    args = parser.parse_args()
    for path, digest in MANUALS.items():
        assert vco.sha(vco.ROOT/path) == digest, path
    with ThreadPoolExecutor(max_workers=4) as pool:
        trials = {f"{tap}-{profile}-{round(step*1e6)}": pool.submit(sweep, tap, profile, step, MATRIX)
                  for tap in PICKOFFS for profile, step in (("nominal", 40e-6), ("deep-cutoff", 40e-6),
                                                            ("nominal", 20e-6))}
        results = {label: trial.result() for label, trial in trials.items()}
    for tap in PICKOFFS:
        for name, *_ in MATRIX[1:]:
            for state in WINDOWS:
                estimates = [dual.phasor(results[f"{tap}-nominal-{step}"][name]["windows"][state]["harmonic"]["v(keyboard)"])
                             for step in (20, 40)]
                assert abs(estimates[0]-estimates[1]) < 2e-8 + .01*abs(estimates[0]), (tap, name, state, estimates)
    report = dict(schema="rf-d/keyboard-cv-ripple/v1", frequency_hz=ripple.FREQUENCY_HZ, windows_s=WINDOWS,
                  tap_counts_from_ground=PICKOFFS, jfet_profiles=FETS, model_sources=MANUALS, notes=results)
    if args.write_report:
        RECEIPT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
