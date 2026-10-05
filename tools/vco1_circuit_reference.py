"""Complete conditional CA3046 VCO1 circuit oracle, SVC-9 pp. 5 and 19.

ngspice solves converter, ramp, amplifier, reset and output formers together.
No imposed saw, threshold, reset timer or pitch-to-current formula is used.
Device hypotheses and the private TI 741 macromodel are explicitly identified.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass, replace
import gzip
import hashlib
import json
import math
from pathlib import Path
import subprocess
import time

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
GRAPH = ROOT / "evidence/vco1_ramp_graph.json"
CONTROLS = ROOT / "evidence/vco1_ca3046_parts.json"
PANEL = ROOT / "evidence/vco1_panel_pulse_width.json"
DEVICES = ROOT / "evidence/vco1_laboratory_devices.json"
EXPECTED_EXE_SHA = "86c9ea5f645ca919e305639fa7bdb522355364c424d14e197f1ade617feb3453"
VECTORS = ["v(ramp_c1)", "v(schmitt_drive)", "v(saw_output_9b)",
           "v(tri_output_21b)", "v(rect_output_20b)", "v(neg4_ref)",
           "v(qb_collector)", "v(ic1_out)", "v(ic3_out)",
           "v(q10_base)", "v(fet_common_source)", "v(fet_c4_left)",
           "v(r6_wiper)", "v(pulse_width_22b)",
           "@qic2_qa[ic]", "@qq10[ic]"]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@dataclass(frozen=True)
class Scenario:
    # Board-line voltages, never MIDI notes or physical knob rotation.
    keyboard_v: float = -2.1
    other_control_v: float = -2.1
    r8_fraction: float = 0.5
    r11_active_ohm: float = 500.0
    c4_f: float = 10e-12
    upper_contact: int = 3
    lower_contact: int = 10
    level_fraction: float = 0.5
    imposed_mixer_v: float = 0.0
    external_neg4_load_a: float = 0.0
    duration_s: float = 0.015
    max_step_s: float = 0.5e-6
    method: str = "gear"
    order: int = 2

    def validate(self) -> None:
        if any(not math.isfinite(v) for v in asdict(self).values()
               if isinstance(v, (int, float))):
            raise ValueError("finite scenario required")
        if not 0 <= self.r8_fraction <= 1 or not 0 <= self.level_fraction <= 1:
            raise ValueError("electrical pot fractions must be in 0..1")
        if not 0 <= self.r11_active_ohm <= 1000:
            raise ValueError("R11 active resistance outside documented track")
        if self.c4_f not in (10e-12, 100e-12):
            raise ValueError("C4 must retain one of the two documentary profiles")
        if self.upper_contact not in range(1, 7) or self.lower_contact not in range(7, 13):
            raise ValueError("unsupported electrical selector contact")
        if self.duration_s <= 0 or not 0 < self.max_step_s <= self.duration_s:
            raise ValueError("positive duration and maximum step required")
        if self.method not in ("gear", "trap") or self.order not in (1, 2):
            raise ValueError("supported integration method/order required")


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def netlist(s: Scenario, export: Path) -> tuple[str, dict]:
    """Generate electrical branches from recorded terminals, including loads."""
    s.validate()
    if any(c.isspace() or c in '";$' for c in export.as_posix()):
        raise ValueError("SPICE export path cannot contain whitespace or control syntax")
    graph, controls, panel, devices = map(read, (GRAPH, CONTROLS, PANEL, DEVICES))
    opamp = ROOT / devices["opamp"]["path"]
    if sha(opamp) != devices["opamp"]["sha256"]:
        raise ValueError("private manufacturer macromodel digest mismatch")
    if graph["board"] != "SVC-204D_Fig_9-3_CA3046":
        raise ValueError("wrong board revision")
    parts = graph["parts"]
    if len({p["ref"] for p in parts}) != len(parts):
        raise ValueError("duplicate board designator")
    lines = ["RF-D conditional VCO1 CA3046 complete circuit",
             f'.include "{opamp.as_posix()}"',
             "Vneg10 NEG10_V 0 -10", "Vpos10 POS10_V 0 10", "Vneg5 NEG5_V 0 -5",
             f"Iexternal NEG4_REF 0 {s.external_neg4_load_a:.17g}"]
    manifest = []

    def node(name: str) -> str:
        return "0" if name == "GND" else name

    def branch(name: str, a: str, b: str, value: float, kind: str = "R") -> None:
        # Endpoint pot contacts use an exact voltage constraint, not epsilon R.
        lines.append(f"{kind if value else 'V'}{name} {node(a)} {node(b)} {value:.17g}")
        manifest.append(dict(ref=name, terminals=[a, b], value=value, kind=kind if value else "contact"))

    for p in parts:
        ref, t, kind = p["ref"], p["terminals"], p["kind"]
        if kind in ("resistor", "temperature_compensating_resistor", "capacitor"):
            value = s.c4_f if ref == "C4" else p["value"]
            branch(ref, t["a"], t["b"], value, "C" if kind == "capacitor" else "R")
        elif kind == "trim_potentiometer":
            total = p["value_end_to_end"]
            if ref == "R8":
                branch("R8_high", t["high"], t["wiper"], total * (1 - s.r8_fraction))
                branch("R8_low", t["wiper"], t["low"], total * s.r8_fraction)
            elif ref == "R11":
                branch("R11_active", t["high"], t["low"], s.r11_active_ohm)
            else:
                raise ValueError("unhandled trim")
        elif kind == "resistance_capacitance_network":
            for i, b in enumerate(p["branches"]):
                if b["kind"] == "resistor":
                    branch(f"{ref}_dc", t["a"], t["b"], b["resistance_ohm"])
                elif b["kind"] == "series_rc":
                    mid = f"{ref}_RC_MID"
                    branch(f"{ref}_series", t["a"], mid, b["resistance_ohm"])
                    branch(f"{ref}_cap", mid, t["b"], b["capacitance_farad"], "C")
                else:
                    raise ValueError("unhandled composite branch")
        elif kind == "741_opamp_schematic":
            pins = " ".join(node(t[k]) for k in devices["opamp"]["pin_order"])
            lines.append(f"X{ref} {pins} LM741")
            manifest.append(dict(ref=ref, terminals=t, model="TI-LM741-MODEL"))
        elif kind == "dual_FET_E402_schematic":
            for side in ("left", "right"):
                terminals = [t[side + "_drain"], t[side + "_gate"], t["common_source"]]
                lines.append(f"J{ref}_{side} {' '.join(map(node, terminals))} LAB_E402")
                manifest.append(dict(ref=ref + "_" + side, terminals=terminals, model="LAB_E402"))
        elif "NPN" in kind or "PNP" in kind:
            name = ref.lower().replace(".", "_")
            model = "LAB_PNP" if "PNP" in kind else "LAB_NPN"
            terminals = [t[k] for k in ("collector", "base", "emitter")]
            lines.append(f"Q{name} {' '.join(map(node, terminals))} {model}")
            manifest.append(dict(ref=ref, terminals=terminals, model=model))
        else:
            raise ValueError(f"unhandled graph element {ref}: {kind}")
    for p in controls["components"]:
        if p["role"] == "cv_input":
            control = p["source_node"]
            v = s.keyboard_v if control == "KEYBOARD" else s.other_control_v
            lines.append(f"V{control} {control} 0 {v:.17g}")
            branch(p["ref"], control, p["target_node"], p["schematic"])
    pp = {p["ref"]: p for p in panel["parts"]}
    for ref in ("R34_PANEL", "R33_PANEL", "R32_PANEL", "R30_PANEL", "R31_PANEL"):
        p = pp[ref]
        branch(ref, *p["terminals"], p["value_ohm"])
    selected = panel["links"]["sw6_upper_contacts"][str(s.upper_contact)]
    width = panel["sw6_lower_contacts"][str(s.lower_contact)]
    if width != "open":
        branch("SW6_width", "PULSE_WIDTH_22B", width, 0)
    total = pp["R6_PANEL"]["value_ohm"]
    branch("R6_panel_high", selected, "R6_WIPER", total * (1 - s.level_fraction))
    branch("R6_panel_low", "R6_WIPER", "GND", total * s.level_fraction)
    branch("R45_PANEL", "R6_WIPER", "MIX_BUS_BOARD4_PIN4", pp["R45_PANEL"]["value_ohm"])
    lines.append(f"Vmixer MIX_BUS_BOARD4_PIN4 0 {s.imposed_mixer_v:.17g}")
    for polarity in ("NPN", "PNP"):
        card = " ".join(f"{k}={v:.17g}" for k, v in devices["bjt"].items())
        lines.append(f".model LAB_{polarity} {polarity}({card})")
    card = " ".join(f"{k}={v:.17g}" for k, v in devices["jfet"].items())
    lines.append(f".model LAB_E402 NJF({card})")
    lines += [f".options temp={devices['temperature_c']} tnom=25 method={s.method} maxord={s.order} reltol=1e-7 abstol=1e-13 vntol=1e-8 gmin=1e-12",
              # Only startup capacitor voltage is imposed. Reset is all Q5/Q6/Q10.
              ".ic v(RAMP_C1)=0", ".save " + " ".join(VECTORS),
              ".control", "set numdgt=17", "set wr_singlescale", "set wr_vecnames",
              f"tran {s.max_step_s:.17g} {s.duration_s:.17g} 0 {s.max_step_s:.17g}",
              f"wrdata {export.as_posix()} {' '.join(VECTORS)}", "quit", ".endc", ".end", ""]
    return "\n".join(lines), dict(branches=manifest, scenario=asdict(s),
        source_sha256={p.relative_to(ROOT).as_posix(): sha(p) for p in (GRAPH, CONTROLS, PANEL, DEVICES, Path(__file__), opamp)})


def run(s: Scenario, label: str, work: Path, executable: Path, timeout: float = 60) -> tuple[np.ndarray, dict]:
    """Preserve exact deck, log and run receipt, also on incomplete/failed runs."""
    if not label or any(c not in "abcdefghijklmnopqrstuvwxyz0123456789_-" for c in label):
        raise ValueError("safe unique run label required")
    if sha(executable) != EXPECTED_EXE_SHA:
        raise ValueError("recorded ngspice46 binary required")
    work.mkdir(parents=True, exist_ok=True)
    deck, export, log, receipt = [work / f"{label}.{suffix}" for suffix in ("cir", "txt", "log", "json")]
    if any(p.exists() for p in (deck, export, log, receipt, export.with_suffix(".txt.gz"))):
        raise ValueError("run label already exists; preserve previous attempt")
    text, metadata = netlist(s, export)
    deck.write_text(text, encoding="utf-8", newline="\n")
    record = dict(schema="rf-d/vco1-spice-run/v1", label=label, **metadata,
        deck_sha256=sha(deck), executable_sha256=sha(executable),
        command=[str(executable), "-n", "-b", str(deck)],
        git_commit=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        git_status=subprocess.check_output(["git", "status", "--short"], cwd=ROOT, text=True),
        trajectory_complete=False, physical_fidelity=False)
    start = time.perf_counter()
    try:
        process = subprocess.run(record["command"], cwd=executable.parent,
            capture_output=True, text=True, timeout=timeout)
        output = process.stdout + process.stderr
        log.write_text(output, encoding="utf-8", newline="\n")
        record["exit_code"] = process.returncode
        if process.returncode or any(w in output.lower() for w in ("error", "aborted", "timestep too small")):
            raise ValueError("SPICE reported failure; see preserved run log")
        raw = np.loadtxt(export, skiprows=1, ndmin=2)
        if raw.shape[1] != len(VECTORS) + 1 or not np.isfinite(raw).all():
            raise ValueError("invalid exported trace")
        if raw[0, 0] != 0 or np.any(np.diff(raw[:, 0]) <= 0) or not math.isclose(raw[-1, 0], s.duration_s, rel_tol=0, abs_tol=1e-14):
            raise ValueError("incomplete/nonmonotone trajectory")
        if np.max(np.diff(raw[:, 0])) > s.max_step_s * (1 + 1e-7):
            raise ValueError("maximum timestep not respected")
        record.update(trajectory_complete=True, rows=len(raw), raw_export_sha256=sha(export),
                      max_actual_step_s=float(np.max(np.diff(raw[:, 0]))))
        with export.open("rb") as src, gzip.open(export.with_suffix(".txt.gz"), "wb", compresslevel=3) as dst:
            import shutil
            shutil.copyfileobj(src, dst)
        # Keep uncompressed data private as well: no deletion/replacement of evidence.
        return raw, record
    except Exception as error:
        record.update(error_type=type(error).__name__, error=str(error))
        if isinstance(error, subprocess.TimeoutExpired):
            log.write_bytes((error.stdout or b"") + (error.stderr or b""))
        if export.exists():
            record["partial_export_sha256"] = sha(export)
        raise
    finally:
        record["wall_s"] = time.perf_counter() - start
        if log.exists():
            record["log_sha256"] = sha(log)
        record["source_sha256_after"] = {p: sha(ROOT / p) for p in record["source_sha256"]}
        receipt.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8", newline="\n")


def crossings(t: np.ndarray, v: np.ndarray, level: float, rising: bool) -> np.ndarray:
    idx = np.flatnonzero((v[:-1] < level) & (v[1:] >= level) if rising else
                         (v[:-1] > level) & (v[1:] <= level))
    return t[idx] + (level - v[idx]) * (t[idx + 1] - t[idx]) / (v[idx + 1] - v[idx])


def measure(raw: np.ndarray, settle_s: float = 0.005) -> dict:
    t, ramp = raw[:, 0], raw[:, 1]
    edges = crossings(t, ramp, -2.0, True)
    edges = edges[edges >= settle_s]
    if len(edges) < 3:
        raise ValueError("fewer than two settled periods; sustained oscillation unverified")
    periods = np.diff(edges)
    mask = (t >= edges[-3]) & (t <= edges[-1])
    window = raw[mask]
    waves = {}
    for k, name in enumerate(VECTORS[:14], start=1):
        v = window[:, k]
        waves[name] = dict(min_v=float(v.min()), max_v=float(v.max()),
            mean_v=float(np.trapezoid(v, window[:, 0]) / np.ptp(window[:, 0])))
    # Phase coordinates describe the last actual cycle; no ideal waveform.
    phase = np.linspace(0, 1, 1025)
    cycle_t = edges[-2] + phase * (edges[-1] - edges[-2])
    cycle = np.column_stack([np.interp(cycle_t, t, raw[:, i]) for i in range(1, 6)])
    pulse = window[:, 5]
    # Duty of the negative-going rectangular state. Offset is measured, not removed.
    level = (float(pulse.min()) + float(pulse.max())) / 2
    pulse_down = crossings(t, raw[:, 5], level, False)
    pulse_up = crossings(t, raw[:, 5], level, True)
    active_s = 0.0
    for down in pulse_down:
        following = pulse_up[pulse_up > down]
        if len(following):
            active_s += max(0.0, min(following[0], edges[-1]) - max(down, edges[-3]))
    return dict(frequency_hz=float(1 / np.mean(periods)),
        period_spread_relative=float(np.ptp(periods) / np.mean(periods)),
        reset_crossings_s=edges.tolist(), windows_v=waves,
        phase_grid=phase.tolist(), cycle_v=cycle.tolist(),
        pulse_negative_duty=active_s / (edges[-1] - edges[-3]),
        qa_mean_a=float(np.trapezoid(window[:, 15], window[:, 0]) / np.ptp(window[:, 0])),
        reset_collector_mean_a=float(np.trapezoid(window[:, 16], window[:, 0]) / np.ptp(window[:, 0])))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--label", required=True)
    parser.add_argument("--keyboard-v", type=float, default=-2.1)
    parser.add_argument("--max-step-ns", type=float, default=500)
    parser.add_argument("--duration-ms", type=float, default=15)
    parser.add_argument("--c4-pf", type=int, choices=(10, 100), default=10)
    parser.add_argument("--method", choices=("gear", "trap"), default="gear")
    parser.add_argument("--order", choices=(1, 2), type=int, default=2)
    args = parser.parse_args()
    exe = ROOT / "references-local/ngspice46/runtime/Spice64/bin/ngspice_con.exe"
    s = replace(Scenario(), keyboard_v=args.keyboard_v, max_step_s=args.max_step_ns * 1e-9,
                duration_s=args.duration_ms * 1e-3, c4_f=args.c4_pf * 1e-12,
                method=args.method, order=args.order)
    raw, receipt = run(s, args.label, ROOT / "references-local/vco1-circuit", exe)
    summary = measure(raw)
    print(json.dumps({k: v for k, v in summary.items() if k not in ("cycle_v", "phase_grid")}, indent=2))


if __name__ == "__main__":
    main()
