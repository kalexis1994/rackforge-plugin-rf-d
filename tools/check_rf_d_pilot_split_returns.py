"""Bench the audio side of the C2/C5 interface before allowing feedback."""
import json
import os
import subprocess
from pathlib import Path

import numpy as np

from affine_evidence import Sources
from check_rf_d_pilot_returns import (
    AREA, COMPILER, LIB, ORACLE, PROBE, ROOT, SOURCES, compare, emit, generate, generate_law,
)
from check_recovery_cost import digest
import check_rf_d_pilot_contours as contours
from prepare_charge_reduced import Y
from prepare_dual_chain import sha, write
from prepare_rf_d_pilot_returns import R59, R60, SPLIT_LAWS, emit_data
from recovery_port_input_model import cases

OWN = "tools/check_rf_d_pilot_split_returns.py"
CONTOURS = "evidence/rf_d_pilot_contours08.json"
ANCHOR_SOURCE = "evidence/charge_control_native01.json"
TRIALS = ((96_000, False), (192_000, False), (96_000, True))
REFERENCE_RATES = (384_000, 768_000)
HOST_RATE = 48_000
HOST_FRAMES = 128
OPEN = (1.91, 1.33)
OPEN_RANGE = (.015, .01)
CLOSED = (-.28, 1.45)
CHANNELS = ("j7_v", "bus_v", "c27_v", "panel_a", "r59_a", "r60_a")


def packed(values):
    return np.asarray(values, "<f8").tobytes()


def drives(time):
    w = 2. * np.pi * time
    return np.column_stack((.055 * np.sin(211 * w) + .015 * np.sin(817 * w),
                            OPEN_RANGE[0] * .98 * np.sin(331 * w),
                            OPEN_RANGE[1] * .98 * np.sin(407 * w)))


def inspect_reserve(raw, info):
    nodes = np.frombuffer(raw, "<f8").reshape(1 + 2 * info["frames"] * 512, contours.N)
    assert np.isfinite(nodes).all()
    order = nodes[::2, 26] >= nodes[::2, 28]
    base = info["start_frame"] * 4096
    events = [[base + int(k) * 8, base + (int(k) + 1) * 8, int(order[k + 1])]
              for k in np.flatnonzero(order[1:] != order[:-1])]
    assert events == info["expected_events"]
    voltage = nodes[:, [3, 37]]
    assert np.array_equal([min(voltage[:, 0]), max(voltage[:, 0])],
                          info["return_domain"]["r59_source_v"])
    rows = np.arange(len(nodes))
    time = rows // 2 + (rows % 2) / 3.
    hold = {}
    for rate in (96_000, 192_000, 384_000):
        samples = slice(None, None, 2 * (HOST_RATE * 512 // rate))
        interpolated = np.column_stack([np.interp(time, time[samples], column[samples])
                                       for column in voltage.T])
        error = np.max(abs(interpolated - voltage), axis=0)
        hold[str(rate)] = dict(max_voltage_error_v=error.tolist(),
                               current_error_at_fixed_receivers_a=(error / [R59, R60]).tolist())
    return dict(events=events, reference_trace_sha256=digest(raw),
                ranges_v=np.stack((voltage.min(0), voltage.max(0)), axis=1).tolist(), hold=hold)


def capture_reserves(run, flags):
    prior = json.loads((ROOT / CONTOURS).read_text(encoding="utf8"))
    ref, _ = contours.references()
    table, *_ = contours.materialize(contours.read_oracle())
    assert digest(table) == contours.read(contours.MODEL)["table_sha256"]
    table_path = AREA / contours.TABLE
    table_path.write_bytes(table)
    kernel = emit("family-kernel.rs", contours.text(contours.KERNEL)
                  .replace("H128_VOICE_TABLE_PATH", table_path.as_posix())
                  .replace("VCO_PANEL_PORT_PATH", (ROOT / contours.PANEL).as_posix()))
    exe = AREA / "split-reserves.exe"
    build = run([*flags, "--cfg", "laboratory", contours.component(kernel),
                 "--extern", f"rf_d_circuit={LIB}", "-o", exe])
    assert build.returncode == 0, build.stderr.decode(errors="replace")
    windows = {}
    for label, branch, start, frames, key in contours.WINDOWS:
        phase, _, _, state = ref[branch][1][start]
        anchor = AREA / "split-reserve.anchor"
        anchor.write_bytes(packed(np.r_[state.ravel(), phase]))
        info = prior["windows"][label]
        assert sha(anchor) == info["anchor_sha256"]
        trace = run([exe, "contour-capture", anchor, start, frames, key])
        assert trace.returncode == 0, trace.stderr.decode(errors="replace")
        windows[label] = inspect_reserve(trace.stdout, info)
    return windows


def main():
    assert not list(AREA.iterdir())
    sequence = 1
    while (out := ROOT / f"evidence/rf_d_pilot_split_returns{sequence:02}.json").exists():
        sequence += 1
    sources = Sources(tuple(dict.fromkeys((*SOURCES, *contours.ALL_SOURCES, contours.OWN,
                                          contours.CANDIDATE, contours.PROBE, contours.PORTS,
                                          OWN, CONTOURS, ANCHOR_SOURCE))))
    report = dict(passed=False, rack_integrated=False, contour_feedback=False,
                  audible_base="0.3.2", channels=CHANNELS, r59_r60_bias_v=OPEN,
                  r59_r60_range_v=OPEN_RANGE, off_bias_v=CLOSED, **sources.fields(),
                  compiler_sha256=sha(Path(COMPILER)), library_sha256=sha(LIB), rates={})
    env = dict(os.environ, PATH="C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;" + os.environ["PATH"])
    flags = [COMPILER, "--edition=2021", "-C", "opt-level=3", "-C", "target-feature=+fma",
             "-A", "dead_code", "-C", "link-arg=-Wl,--stack,33554432"]

    def run(args, payload=None, repeat=False):
        def call():
            return subprocess.run(list(map(str, args)), cwd=ROOT, env=env, input=payload,
                                  capture_output=True, timeout=180)
        result = call()
        if repeat:
            again = call()
            assert (again.returncode, again.stdout, again.stderr) == (
                result.returncode, result.stdout, result.stderr)
        return result

    def floats(args, values):
        result = run(args, packed(values))
        assert result.returncode == 0, result.stderr.decode(errors="replace")
        data = np.frombuffer(result.stdout, "<f8")
        assert np.isfinite(data).all()
        return data

    try:
        oracle = AREA / "pilot-split-oracle.exe"
        result = run([*flags, ROOT / ORACLE, "--extern", f"rf_d_circuit={LIB}", "-o", oracle])
        assert result.returncode == 0, result.stderr.decode(errors="replace")
        baseline = cases()[1]
        dc = floats([oracle, "anchor"], np.r_[baseline["DC"], 0., OPEN])
        case = dict(baseline, DC=dc[:136], G=dc[136:-1].reshape(68, 68).copy())
        case["G"][66, 66] -= Y  # build() adds the same BUS conductance.
        assert 0. <= dc[-1] <= 1e-13
        report["anchor_residual"] = float(dc[-1])
        off = run([oracle, "anchor"], packed(np.r_[baseline["DC"], 0., CLOSED]), repeat=True)
        report["off_anchor"] = dict(exit_code=off.returncode,
                                    stderr=off.stderr.decode(errors="replace").strip(),
                                    bit_exact_replay=True)

        def reference(clock, stimulus):
            ticks = np.arange(clock * HOST_FRAMES // HOST_RATE)
            center = [0., *OPEN]
            inputs = np.column_stack((stimulus((ticks + 1. / 3.) / clock) + center,
                                      stimulus((ticks + 1.) / clock) + center))
            return floats([oracle, clock, "split"], np.r_[case["DC"], inputs.ravel()]).reshape(-1, 6)

        fine = {clock: reference(clock, drives) for clock in REFERENCE_RATES}
        for clock, ladder in TRIALS:
            code, _ = generate(rate=clock)
            if ladder:
                generate_law(SPLIT_LAWS)
            src = emit("split-probe.rs", code + f'#[path = "{(ROOT / PROBE).as_posix()}"] mod probe;\n'
                       "fn main() -> Result<(), Box<dyn std::error::Error>> { probe::main() }\n")
            bank = AREA / "pilot-return-maps.rs"
            checks = emit_data(bank, 1. / clock, split=case, center=OPEN, limits=OPEN_RANGE,
                               split_ladder=ladder)
            exe = AREA / "pilot-split-probe.exe"
            roots = [] if ladder else ["--cfg", "pilot_block_roots"]
            result = run([*flags, "--cfg", "pilot_returns", "--cfg", "pilot_split_returns",
                          *roots, src, "-o", exe])
            assert result.returncode == 0, result.stderr.decode(errors="replace")
            time = np.arange(clock * HOST_FRAMES // HOST_RATE + 1) / clock
            coarse = drives(time)

            def hold(t):
                return np.column_stack([np.interp(t, time, column) for column in coarse.T])

            candidate = run([exe, "electrical"], packed(coarse[1:]), repeat=True)
            assert candidate.returncode == 0, candidate.stderr.decode(errors="replace")
            trial = np.frombuffer(candidate.stdout, "<f8").reshape(-1, 6)
            sample = {rate: values[rate // clock - 1::rate // clock] for rate, values in fine.items()}
            low, high = (sample[rate] for rate in REFERENCE_RATES)
            stride = REFERENCE_RATES[-1] // clock
            held = reference(REFERENCE_RATES[-1], hold)[stride - 1::stride]
            tag = f"{clock}_{'ladder' if ladder else 'local'}"
            report["rates"][tag] = dict(
                map_checks=checks, maps_sha256=sha(bank), bit_exact_candidate_replay=True,
                refinement=compare(low, high), comparison=compare(trial, high),
                fo_hold_reference_vs_continuous=compare(held, high),
                candidate_vs_fo_hold_reference=compare(trial, held))
            print(tag, report["rates"][tag]["comparison"], flush=True)
        report["reserves"] = capture_reserves(run, flags)
        print("CONTOUR_RESERVES", report["reserves"], flush=True)
        admitted = report["rates"]["96000_ladder"]
        report["positive_receiver_passed"] = admitted["refinement"]["passed"] and admitted["comparison"]["passed"]
        report["passed"] = False  # Offline ports remain externally driven and the feedback gate is still open.
        sources.unchanged()
    finally:
        write(out, report)
        for path in AREA.iterdir():
            assert path.is_file() and path.resolve().parent == AREA.resolve()
            path.unlink()
    raise SystemExit(0 if report["positive_receiver_passed"] else 1)


if __name__ == "__main__":
    main()
