"""Measure the muted CA3046 loads and replay them through the shared C14."""
import argparse
from dataclasses import replace
import json
from pathlib import Path

import numpy as np

import check_vco1_loaded_reset_edge as edge
import vco1_circuit_reference as vco
import voice_circuit_reference as voice

RECEIPT = vco.ROOT / "evidence/vco_shared_neg401.json"
SCHEMATIC = vco.ROOT / "references-local/pdf/service_204d_synthfool.pdf"
SCHEMATIC_SHA = "0edd35f3f9ab1eba346693545f0dcbe374bdcf6f37f9b1a34ecbdeb8ae682b4a"
SIGNALS = (*edge.VECTORS, "v(neg4_ref)")
COMMON = {"0", "POS10_V", "NEG10_V", "NEG5_V", "KEYBOARD", "BEND", "TUNE", "MOD", "EXT",
          "LAB_PNP", "LAB_NPN", "LAB_E402", "LM741"}
SHARED_ELEMENTS = {"CC14", "RR166", "RR174"}
CONTROL_ELEMENTS = {"RR11_active", "RR37", "RR43"}
RANGE_OFFSET_2 = 1.13
IC6_OUT_V = {"La2": -4.94, "La3": -4.955}
CLAMP_V = -3.895
C14 = .12e-6
G = 1 / 6200 + 1 / 3900
HARMONICS = 24
SETTLE = .018


def prefix_core(source, index):
    """Reuse the shared topology of the cores, retaining independent state."""
    prefix = f"osc{index}_"
    lines = []
    for line in source:
        fields = line.split()
        name = fields[0]
        if name in SHARED_ELEMENTS or name in CONTROL_ELEMENTS:
            continue
        fields[0] = name[0] + prefix + name[1:]
        for column in range(1, len(fields) - 1):
            node = fields[column]
            if node not in COMMON:
                fields[column] = prefix + node
        # A zero volt probe joins both load branches of this core to C14.
        lines.append(" ".join(fields))
    lines += [f"Vref{index} NEG4_REF {prefix}NEG4_REF 0"]
    return lines


def extra_core(source, index, base_range_v, osc3_control_v):
    prefix = f"osc{index}_"
    # The 15 kΩ range branch has the same small-signal weight as the 51.1 kΩ keyboard branch.
    lines = prefix_core(source, index)
    if index == 2:
        # IC4 non-inverting input uses R94 and the R95/R87 tune divider.
        # A fixed pin 12A boundary gives −5 V before loading.
        lines += ["Vosc2_tune OSC2_TUNE_PIN 0 7.087912087912088",
                  f"Rosc2_95 OSC2_TUNE_PIN {prefix}IC1_PLUS 220000",
                  f"Rosc2_87 {prefix}IC1_PLUS NEG10_V 91000",
                  f"Rosc2_62 {prefix}IC1_SUM {prefix}R37_TOP {edge.R11:.17g}",
                  f"Rosc2_61 {prefix}R37_TOP NEG10_V 11800",
                  f"Rosc2_36_PANEL {prefix}SAW_OUTPUT_9B {prefix}SAW_TRI_TAP 47000",
                  f"Rosc2_37_PANEL {prefix}SAW_TRI_TAP {prefix}TRI_OUTPUT_21B 10000",
                  f"Vosc2_range {prefix}RANGE 0 {base_range_v + RANGE_OFFSET_2 * 15000. / 51100.:.17g}",
                  f"Rosc2_range {prefix}RANGE {prefix}IC1_SUM 15000"]
    else:
        # Condition on IC6 output, preserving the current at the CA3046
        # converter, the IC10 servo, and the internal Q37 inverter load.
        control_nodes = {f"{prefix}IC1_PLUS", f"{prefix}IC1_SUM"}
        lines = [line for line in lines if not control_nodes.intersection(line.split()[1:])]
        lines += [f"Vosc3_control {prefix}IC1_OUT 0 {osc3_control_v:.17g}",
                  f"Rosc3_164 POS10_V {prefix}Q37_SUPPLY 330",
                  f"Cosc3_10 {prefix}Q37_SUPPLY 0 2.2u",
                  f"Rosc3_165 {prefix}Q37_SUPPLY {prefix}Q37_COLLECTOR 2200",
                  f"Rosc3_171 {prefix}SAW_OUTPUT_9B {prefix}Q37_BASE 33000",
                  f"Rosc3_68k {prefix}Q37_COLLECTOR {prefix}Q37_BASE 68000",
                  f"Rosc3_182 {prefix}Q37_BASE NEG10_V 390000",
                  f"Qosc3_37 {prefix}Q37_COLLECTOR {prefix}Q37_BASE 0 LAB_NPN",
                  f"Rosc3_7k5 {prefix}Q37_COLLECTOR {prefix}REVERSE_7B 7500",
                  f"Rosc3_176 {prefix}REVERSE_7B NEG10_V 18000"]
    lines += [f"Vosc{index}_width {prefix}PULSE_WIDTH_22B 0 0",
              # Mixer OFF isolates the common bus. With the level cursor at
              # zero, the full 25 kΩ track still loads the selected saw.
              f"Rosc{index}_panel_saw {prefix}SAW_OUTPUT_9B 0 25000"]
    return lines


def provenance(metadata):
    metadata["source_sha256"].update({
        SCHEMATIC.relative_to(vco.ROOT).as_posix(): SCHEMATIC_SHA,
        Path(__file__).relative_to(vco.ROOT).as_posix(): vco.sha(Path(__file__)),
    })


def isolate(scene, export, index, osc3_control_v):
    text, metadata = edge.deck(scene, export, 0.)
    lines = text.splitlines()
    core = text[text.index("CC1 "):text.index("RR34_PANEL ")].splitlines()
    extras = extra_core([line for line in core if line[0] != "V"], index,
                        scene.oscillator.other_control_v, osc3_control_v)
    osc = scene.oscillator
    ramp = f"v(osc{index}_ramp_c1)"
    current = f"i(vref{index})"
    provenance(metadata)
    lines = [f"RF-D isolated OSC{index} load on -4 V", *lines[1:5],
             *(line for line in lines if line.startswith(("VKEYBOARD ", "VTUNE ", "VBEND ",
                                                         "VMOD ", "VEXT ", ".model LAB_"))),
             f"Vclamp NEG4_REF 0 {CLAMP_V:.17g}", *extras,
             next(line for line in lines if line.startswith(".options ")),
             f".ic v(osc{index}_RAMP_C1)=0", f".save {ramp} {current}",
             ".control", "set numdgt=17", "set wr_singlescale", "set wr_vecnames",
             f"tran {osc.max_step_s:.17g} {osc.duration_s:.17g} 0 {osc.max_step_s:.17g}",
             f"wrdata {export.as_posix()} {ramp} {current}", "quit", ".endc", ".end", ""]
    return "\n".join(lines), metadata


def circuit_run(scene, name, builder, signals):
    raw, info = voice.run(scene, name, edge.LAB, edge.EXE, timeout=120,
                          netlist_factory=builder, vectors=signals)
    assert info["trajectory_complete"] and info["source_sha256"] == info["source_sha256_after"]
    receipt = {key: info[key] for key in ("raw_export_sha256", "deck_sha256", "rows", "scenario", "source_sha256")}
    return raw, receipt


def retire(name):
    for suffix in ("cir", "log", "json", "txt", "txt.gz"):
        (edge.LAB / f"{name}.{suffix}").unlink()


def current_cycle(raw, cycle_index=-1):
    t, ramp, current = raw.T
    resets = vco.crossings(t, ramp, -2., True)
    assert len(resets) >= 3
    start, end = resets[cycle_index - 1], resets[cycle_index]
    duration = end - start
    selected = (t > start) & (t < end)
    clocks = np.r_[start, t[selected], end]
    values = np.interp(clocks, t, current)
    relative = clocks - start
    increments = np.diff(clocks) * (values[:-1] + values[1:]) / 2.
    charge = np.r_[0., np.cumsum(increments)]
    dc = charge[-1] / duration
    # For the ideal divider, the oscillating rail voltage is a high-pass
    # transform of integrated excess charge divided by C14. Its peak-to-peak
    # value cannot exceed twice the excursion of that integral divided by C14.
    charge_span = np.ptp(charge - dc * relative)
    angular = 2 * np.pi * np.arange(1, HARMONICS + 1) / duration
    # Integrate on solver timestamps so sub-microsecond pulses keep their area.
    coeff = np.array([np.trapezoid(values * np.exp(-1j * omega * relative), relative) / duration
                      for omega in angular])
    rail_coeff = coeff / (G + 1j * angular * C14)
    metrics = dict(
        frequency_hz=float(1 / duration), load_mean_a=float(dc), load_span_a=float(np.ptp(values)),
        cycle_start_s=float(start), cycle_end_s=float(end), excess_charge_span_c=float(charge_span),
        one_way_rail_span_bound_v=float(2 * charge_span / C14),
        first_harmonics_rail_rms_v=float(np.sqrt(2) * np.linalg.norm(rail_coeff)),
    )
    return metrics, (float(dc), angular, coeff)


def replay(scene, export, loads, dynamic):
    text, metadata = edge.deck(scene, export, 0.)
    provenance(metadata)
    dc = sum(load[0] for load in loads)
    marker = "Iexternal NEG4_REF 0 0"
    assert text.count(marker) == 1
    source = f"Iexternal NEG4_REF 0 {dc:.17g}"
    if dynamic:
        duration = scene.oscillator.duration_s
        clocks = np.linspace(0., duration, round(duration / 4e-6) + 1)
        current = sum(2 * (np.exp(1j * clocks[:, None] * omega) @ coeff).real
                      for _, omega, coeff in loads)
        source += "\nIcycle NEG4_REF 0 PWL(\n"
        source += "\n".join(f"+ {t:.17g} {a:.17g}" for t, a in zip(clocks, current, strict=True))
        source += "\n+ )"
    text = text.replace(marker, source)
    return text.replace(" ".join(edge.VECTORS), " ".join(SIGNALS)), metadata


def summarize(raw, note_ref, band):
    trace = edge.edge_metrics(raw[:, :9], SETTLE, note_ref["vintage_edge_timing_std_s"], band)
    selected = raw[:, 0] >= SETTLE
    t, rail = raw[selected][:, [0, 9]].T
    average = np.trapezoid(rail, t) / np.ptp(t)
    delay = [r["saw_9b_from_c1_minus_3p8_v_s"] for r in trace["resets"]]
    reset = np.asarray([r["c1_reset_s"] for r in trace["resets"]])
    return dict(frequency_hz=trace["frequency_hz"], rail_mean_v=float(average),
                rail_ac_rms_v=float(np.sqrt(np.trapezoid((rail - average)**2, t) / np.ptp(t))),
                rail_span_v=float(np.ptp(rail)), edge_delay_span_s=float(np.ptp(delay)),
                period_std_s=float(np.std(np.diff(reset))), settled_resets=len(reset))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--note", choices=tuple(IC6_OUT_V))
    parser.add_argument("--write-report", action="store_true")
    args = parser.parse_args()
    if args.note and args.write_report:
        parser.error("Use both notes to publish evidence")
    assert vco.sha(SCHEMATIC) == SCHEMATIC_SHA
    base = vco.read(edge.RECEIPT)
    report = dict(
        scope="Two muted oscillator currents at fixed NEG4_REF, then one-way replay into loaded OSC1.",
        nominal_source_sha256=vco.sha(edge.RECEIPT), executable_sha256=vco.EXPECTED_EXE_SHA,
        clamp_v=CLAMP_V, capacitor_f=C14, harmonics=HARMONICS, replay_step_s=4e-6,
        osc2_range_offset_octave_equivalent=RANGE_OFFSET_2, notes={},
    )
    for note, reference in base["notes"].items():
        if args.note and note != args.note:
            continue
        config = dict(reference["gear_250ns"]["run"]["scenario"])
        osc = vco.Scenario(**config.pop("oscillator"))
        scene = voice.Scenario(oscillator=replace(osc, duration_s=.018 if note == "La2" else .012), **config)
        loads = []
        branches = {}
        for index in (2, 3):
            comparisons = {}
            for grid, step in (("trap750", .75e-6), ("trap500", .5e-6)):
                label = f"neg4-load-{note.lower()}-{index}-{grid}"
                trial = replace(scene, oscillator=replace(scene.oscillator, method="trap", max_step_s=step))
                raw, info = circuit_run(trial, label, lambda s, p: isolate(s, p, index, IC6_OUT_V[note]),
                                        (f"v(osc{index}_ramp_c1)", f"i(vref{index})"))
                stats, load = current_cycle(raw)
                previous, _ = current_cycle(raw, -2)
                assert abs(stats["load_mean_a"] - previous["load_mean_a"]) < 2e-9
                comparisons[grid] = dict(**stats, run=info)
                retire(label)
                print(note, index, grid, json.dumps(stats), flush=True)
            coarse, fine = comparisons["trap750"], comparisons["trap500"]
            assert abs(coarse["frequency_hz"] / fine["frequency_hz"] - 1.) < .001
            assert abs(coarse["one_way_rail_span_bound_v"] / fine["one_way_rail_span_bound_v"] - 1.) < .02
            loads.append(load)
            branches[str(index)] = comparisons
        scene = replace(scene, oscillator=replace(scene.oscillator, duration_s=.052))
        cases = {}
        for kind, dynamic in (("dc", False), ("dynamic", True)):
            label = f"neg4-replay-{note.lower()}-{kind}"
            raw, info = circuit_run(scene, label, lambda s, p: replay(s, p, loads, dynamic), SIGNALS)
            cases[kind] = dict(**summarize(raw, reference, base["comparison_band_hz"]), run=info)
            retire(label)
        bound = sum(row["trap500"]["one_way_rail_span_bound_v"] for row in branches.values())
        assert cases["dynamic"]["rail_span_v"] < bound * 1.05
        result = dict(ic6_out_v=IC6_OUT_V[note], isolated_loads=branches, **cases,
                      rail_span_bound_v=bound, vintage_edge_std_s=reference["vintage_edge_timing_std_s"],
                      vintage_residual_db=reference["vintage_residual_db_over_signal"])
        report["notes"][note] = result
        print(note, json.dumps({k: v for k, v in result.items() if not isinstance(v, dict)}),
              {k: {a: b for a, b in v.items() if a != "run"} for k, v in cases.items()}, flush=True)
    if args.write_report:
        RECEIPT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
