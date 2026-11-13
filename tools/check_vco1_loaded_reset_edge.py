"""Measure the CA3046 reset with the actual board 4 input loading the mixer."""
import argparse
from dataclasses import replace
import json
from pathlib import Path

import numpy as np

import vco1_circuit_reference as vco
import voice_circuit_reference as voice
from vco_cv_load_analysis import R8, R11

ROOT = vco.ROOT
LAB = ROOT / "tmp/lab-current"
EXE = ROOT / "references-local/ngspice46/runtime/Spice64/bin/ngspice_con.exe"
VINTAGE = ROOT / "evidence/rf_d_vintage_saw_reset_residual01.json"
RECEIPT = ROOT / "evidence/vco1_loaded_reset_edge01.json"
VECTORS = ("v(ramp_c1)", "v(schmitt_q6_collector)", "@qq10[ic]", "v(saw_output_9b)",
           "v(r6_wiper)", "v(mix_bus_board4_pin4)", "v(f4_base_q29)", "v(f4_main_output)")
KEYBOARD = {"La2": -4.1161, "La3": -3.10332}
OFFSET_V = 0.001
FFT_POINTS = 16_384


def deck(scenario, export, offset_v):
    text, metadata = voice.netlist(scenario, export, linear_solver="klu")
    original = " ".join(voice.VECTORS)
    assert text.count(original) == 2 and not any(line.startswith("Vmixer ") for line in text.splitlines())
    text = text.replace(original, " ".join(VECTORS))
    if offset_v:
        q5 = "Qq5 SCHMITT_Q5_COLLECTOR SCHMITT_SENSE 0 LAB_PNP"
        assert text.count(q5) == 1
        text = text.replace(q5, "Qq5 SCHMITT_Q5_COLLECTOR Q5_BASE_TEST 0 LAB_PNP\n"
                            f"Vtest_q5 Q5_BASE_TEST SCHMITT_SENSE {offset_v:.17g}", 1)
    metadata["q5_base_series_offset_v"] = offset_v
    metadata["source_sha256"][Path(__file__).relative_to(ROOT).as_posix()] = vco.sha(Path(__file__))
    return text, metadata


def single_crossing(t, signal, level, rising=True):
    result = vco.crossings(t, signal, level, rising)
    if len(result) != 1:
        raise ValueError(f"Expected one crossing of {level}, got {len(result)}")
    return float(result[0])


def shift_band_power(t, signal, start, stop, shift_s, band):
    """Band power of the difference for one fixed time shift of a solved cycle."""
    period = stop - start
    wave = np.interp(start + np.arange(FFT_POINTS) * period / FFT_POINTS, t, signal)
    spectrum = np.fft.rfft(wave - wave.mean())
    # Use a one-sided spectrum with Parseval weights for relative power.
    power = abs(spectrum)**2
    power[1:-1] *= 2.
    frequencies = np.fft.rfftfreq(FFT_POINTS, period / FFT_POINTS)
    mask = (frequencies >= band[0]) & (frequencies < band[1])
    difference = 4. * np.sin(np.pi * frequencies[mask] * shift_s)**2
    return dict(periodic_band_db=float(10. * np.log10(power[mask].sum() / power.sum())),
                shifted_minus_nominal_band_db=float(10. * np.log10(difference @ power[mask] / power.sum())))


def edge_metrics(raw, settled_after_s, vintage_shift_s, band):
    t = raw[:, 0]
    ramp, q6, q10, saw, wiper, bus, q29, main = raw[:, 1:].T
    resets = vco.crossings(t, ramp, -2., True)
    resets = resets[(resets > settled_after_s) & (resets + 200e-6 < t[-1])]
    if len(resets) < 3:
        raise ValueError("Three settled resets required")
    periods = np.diff(resets)
    rows = []
    for reset in resets:
        window = (t > reset - 2e-6) & (t < reset + 1.5e-6)
        local = t[window]
        pre_v, post_v = np.interp(reset + np.array([-1., 1.]) * 1e-6, t, saw)
        levels = pre_v + (post_v - pre_v) * np.array([.1, .5, .9])
        crossings = [vco.crossings(local, saw[window], level, True) for level in levels]
        low, middle, high = [float(times[0]) for times in crossings]
        assert low < middle < high
        slope, intercept = np.polyfit(t[(t > reset - 250e-6) & (t < reset - 100e-6)] - reset,
                                     ramp[(t > reset - 250e-6) & (t < reset - 100e-6)], 1)
        preceding = (t > reset - 1e-3) & (t < reset - 2e-6)
        anchor = single_crossing(t[preceding], ramp[preceding], -3.8, False)
        drive = single_crossing(local, q10[window], -0.001, False)
        sense = single_crossing(local[local < reset], q6[window][local < reset], -1., False)
        current = (wiper - bus) / 33000.
        rows.append(dict(
            c1_reset_s=reset, c1_ramp_slope_v_per_s=float(slope),
            c1_ramp_extrapolated_at_q10_v=float(intercept + slope * (drive - reset)),
            q6_to_q10_s=drive - sense, q10_to_9b_midpoint_s=middle - drive,
            q10_peak_collector_a=float(np.min(q10[window])),
            saw_9b_edge_swing_v=float(post_v - pre_v), saw_9b_rise_10_90_s=high - low,
            saw_9b_rising_crossing_counts=[len(times) for times in crossings],
            saw_9b_overshoot_v=float(saw[window].max() - post_v),
            saw_9b_from_c1_minus_3p8_v_s=middle - anchor,
            saw_9b_minus_c1_midpoint_s=middle - reset,
            bus_step_v=float(np.diff(np.interp(reset + np.array([-1., 1.]) * 1e-6, t, bus))[0]),
            r45_current_pre_post_a=np.interp(reset + np.array([-1., 1.]) * 1e-6, t, current).tolist(),
            c27_voltage_pre_post_v=np.interp(reset + np.array([-1., 1.]) * 1e-6, t, bus - q29).tolist(),
        ))
    return dict(
        frequency_hz=float(1. / periods.mean()), period_span_s=float(np.ptp(periods)), resets=rows,
        vintage_sized_fixed_shift={name: shift_band_power(t, signal, resets[-2], resets[-1], vintage_shift_s, band)
                                   for name, signal in (("9B", saw), ("board4_main", main))},
    )


def median(metrics, name):
    return float(np.median([row[name] for row in metrics["resets"]]))


def run_case(note, scene, name, vintage_shift_s, band, offset=0.):
    label = f"{note.lower()}-loaded-edge-{name}"
    raw, run = voice.run(scene, label, LAB, EXE, timeout=120,
                         netlist_factory=lambda s, p: deck(s, p, offset), vectors=VECTORS)
    assert run["source_sha256"] == run["source_sha256_after"] and run["trajectory_complete"]
    result = edge_metrics(raw, 0.015, vintage_shift_s, band)
    result["run"] = {key: run[key] for key in ("deck_sha256", "log_sha256", "raw_export_sha256",
                                              "rows", "scenario", "q5_base_series_offset_v")}
    for suffix in ("cir", "log", "json", "txt", "txt.gz"):
        (LAB / f"{label}.{suffix}").unlink()
    return result, run["source_sha256"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-report", action="store_true")
    args = parser.parse_args()
    vintage = vco.read(VINTAGE)
    report = dict(
        schema="rf-d/vco1-loaded-reset-edge/v1", source_vintage_sha256=vco.sha(VINTAGE),
        executable_sha256=vco.EXPECTED_EXE_SHA, signals=VECTORS,
        scope="Nominal CA3046 documentary circuit, SW6 3/10, R6/R45 into the dynamic board 4 input.",
        measured_vintage_scope="MP3 output. Timing estimate is not an internal node measurement.",
        comparison_band_hz=vintage["analysis_band_hz"], cycle_fft_points=FFT_POINTS,
        notes={},
    )
    for note, keyboard in KEYBOARD.items():
        observed = vintage["notes"][note]
        timing_std_s = observed["source_edge_timing"]["predictor_shift_std_us"] * 1e-6
        band = vintage["analysis_band_hz"]
        oscillator = vco.Scenario(keyboard_v=keyboard, r8_fraction=R8, r11_active_ohm=R11,
                                  max_step_s=250e-9, duration_s=.045)
        scene = voice.Scenario(oscillator=oscillator, cutoff_fraction=1.)
        fine = replace(scene, oscillator=replace(oscillator, max_step_s=125e-9, method="trap"))
        original, _ = run_case(note, scene, "gear250", timing_std_s, band)
        refined, sources = run_case(note, fine, "trap125", timing_std_s, band)
        early, _ = run_case(note, scene, "offset-minus", timing_std_s, band, -OFFSET_V)
        late, _ = run_case(note, scene, "offset-plus", timing_std_s, band, OFFSET_V)
        report["source_sha256"] = sources
        delay = "saw_9b_from_c1_minus_3p8_v_s"
        rise = "saw_9b_rise_10_90_s"
        sensitivity = (median(late, delay) - median(early, delay)) / (2 * OFFSET_V)
        frequency_cents = 1200. * np.log2(original["frequency_hz"] / observed["fundamental_hz"])
        refine_delta_s = abs(median(original, delay) - median(refined, delay))
        nominal_spread_s = np.ptp([row[delay] for row in original["resets"]])
        result = dict(
            vintage_fundamental_hz=observed["fundamental_hz"], vintage_edge_timing_std_s=timing_std_s,
            vintage_residual_db_over_signal=observed["source"]["mean"]["residual_db_over_signal"],
            frequency_error_cents=float(frequency_cents), method_delay_difference_s=refine_delta_s,
            method_rise_difference_s=abs(median(original, rise) - median(refined, rise)),
            nominal_delay_span_s=float(nominal_spread_s),
            q5_offset_sensitivity_s_per_v=sensitivity,
            q5_offset_equivalent_std_v=timing_std_s / abs(sensitivity),
            gear_250ns=original, trap_125ns=refined, offset_minus=early, offset_plus=late,
        )
        report["notes"][note] = result
        assert abs(frequency_cents) < 1. and refine_delta_s < .1e-6, result
        print(note, json.dumps({key: value for key, value in result.items() if not isinstance(value, dict)}),
              flush=True)
    if args.write_report:
        RECEIPT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
