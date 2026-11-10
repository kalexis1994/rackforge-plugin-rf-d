"""Contrast loaded pilot timer states and locate the audio-domain boundary."""
import argparse
import os
import subprocess
import traceback
from pathlib import Path

import numpy as np

from affine_evidence import Sources
from check_hybrid_voice import packed
from check_recovery_cost import digest
from check_rf_d_pilot_trigger import (
    ALL_SOURCES, AREA, CLOCK, COMPILER, KERNEL, LIB, MODEL, PANEL, ROOT, TABLE, WINDOWS,
    build, emit, materialize, once, read, read_oracle, references, sha, text, write,
)
from validate_vco_family_voice_bus import J7, N

OWN = "tools/check_rf_d_pilot_contours.py"
CANDIDATE = "tools/rf_d_pilot_contours.rs"
PROBE = "tools/rf_d_pilot_contours_probe.rs"
PORTS = "tools/rf_d_pilot_contour_ports.rs"
CORE = (6, 7, 8, 9, 10, 11, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 53)
TIMERS = (5, 38)
LOAD_NODES = (13, 14, 15, *range(29, 38), *range(39, 51), 52)
LOAD_CURRENTS = ("sustain_diode", "reset_diode", "c5_attack", "c5_decay", "c5_q22")
R59_RANGE = (1.985, 2.015)
R59_LIMIT_A = 2e-9
MARGIN_NS = 128e9 / (2 * 48_000)
MODES = (
    ("fine", ()),
    ("c5_loads_at_192khz", (30, 32, 44, 47)),
    ("all_at_192khz", (2, 4, 14, 30, 32, 34, 41, 44, 47, 48, 52, 54, 55)),
)
SENSITIVITY = tuple((f"x{node}_at_192khz", (node,)) for node in (14, 41, 48, 52))
LOADED_MODES = (
    ("fine", ()),
    ("tail_at_96khz", (55,)),
    ("all_at_96khz", (2, 4, 54, 55)),
)


def component(kernel):
    probe = build(kernel)
    code = once(probe.read_text(encoding="utf8"), '        Some("ports") => ports(),', '''
        Some("ports") => ports(),
        Some("contour-capture") if args.len() == 6 =>
            contour_probe::capture(&args[2], args[3].parse()?, args[4].parse()?, args[5].parse()?),
        Some("contour-replay") if (5..=6).contains(&args.len()) =>
            contour_probe::replay(&args[2], args[3].parse()?, args[4].parse()?, args.get(5).map_or(Ok(128), |s| s.parse())?),''')
    for name, path in (("pilot_contours", CANDIDATE), ("contour_probe", PROBE), ("contour_ports", PORTS)):
        code += f'\n#[path = "{(ROOT / path).as_posix()}"] mod {name};\n'
    return emit(probe.name, code)


def domain(raw):
    nodes = np.frombuffer(raw, "<f8").reshape(-1, N)
    assert np.isfinite(nodes).all()
    r59 = (nodes[:, 3] - nodes[:, 54]) / 68_000.
    r60 = (nodes[:, 55] - nodes[:, 37]) / 680.
    # At the oracle VCA-base voltage, this is the smallest R59 current error
    # any source voltage in the accepted pilot's domain can achieve.
    error = abs(np.clip(nodes[:, 3], *R59_RANGE) - nodes[:, 3]) / 68_000.
    return dict(r59_source_v=[float(min(nodes[:, 3])), float(max(nodes[:, 3]))],
                r59_a=[float(min(r59)), float(max(r59))], r60_a=[float(min(r60)), float(max(r60))],
                j7_v=[float(min(nodes[:, J7])), float(max(nodes[:, J7]))],
                out_of_range_points=int(np.count_nonzero(error)), observed_points=len(error),
                max_r59_clamp_error_a=float(max(error)), r59_gate_a=R59_LIMIT_A,
                r59_domain_passed=bool(max(error) <= R59_LIMIT_A))


def assess(raw, start, frames, expected, loaded=False):
    lines = raw.decode().splitlines()
    tag, steps, window_ns, sample_ns = lines.pop(0).split(",")
    assert tag == "COST" and int(steps) == frames * 512
    error, events, returns, loads = {}, [], [], []
    direction_ratio = None
    for line in lines:
        tag, *fields = line.split(",")
        if tag == "NODE":
            node, volts = fields
            error[int(node)] = float(volts)
        elif tag == "RETURNS":
            returns = list(map(float, fields))
        elif tag == "DIRECTION":
            direction_ratio = float(fields[0])
        elif tag == "LOAD":
            loads = list(map(float, fields))
        else:
            assert tag == "SWITCH"
            lo, hi, order = map(int, fields)
            events.append([start * 4096 + lo, start * 4096 + hi, order])
    assert tuple(error) == CORE + (LOAD_NODES if loaded else ()) + TIMERS
    assert np.isfinite(list(error.values())).all()
    assert len(returns) == 2 and np.isfinite(returns).all()
    assert len(loads) == (len(LOAD_CURRENTS) if loaded else 0) and np.isfinite(loads).all()
    direction_ok = not loaded or (direction_ratio is not None and 0 <= direction_ratio <= 1)
    return dict(passed=direction_ok and events == expected and max(error.values()) <= 20e-6
                and max(returns + loads) <= R59_LIMIT_A,
                schur_direction_error_ratio=direction_ratio,
                max_load_error_a=dict(zip(LOAD_CURRENTS, loads)),
                max_current_error_a=returns,
                events=events, maximum_by_node_v=error, window_elapsed_ns=int(window_ns),
                max_compute_per_frame_ns=int(sample_ns), single_frame_over_block_budget=int(sample_ns) > MARGIN_NS)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--loaded-filter", action="store_true")
    loaded = parser.parse_args().loaded_filter
    assert AREA.is_dir() and not list(AREA.iterdir())
    seq = 1
    while (out := ROOT / f"evidence/rf_d_pilot_contours{seq:02}.json").exists():
        seq += 1
    sources = Sources((*ALL_SOURCES, OWN, CANDIDATE, PROBE, PORTS,
                       "tools/rf_d_pilot_return_plant.rs"))
    report = dict(passed=False, promoted=False, rack_integrated=False, loaded_filter=loaded, **sources.fields(),
                  compiler_sha256=sha(Path(COMPILER)), library_sha256=sha(LIB),
                  clock_sha256=sha(ROOT / CLOCK), margin_ns=MARGIN_NS, windows={})
    env = dict(os.environ, PATH="C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;" + os.environ["PATH"])

    def run(args, store=False):
        command = list(map(str, args))
        proc = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, timeout=180)
        return proc, dict(command=command, exit_code=proc.returncode, stderr=packed(proc.stderr),
                          stdout=packed(proc.stdout) if store else dict(sha256=digest(proc.stdout), bytes=len(proc.stdout)))

    try:
        ref, report["reference_inputs"] = references()
        archived = read(CLOCK)["trials"]["positive"]["64"]["expected_brackets"]
        table, *_ = materialize(read_oracle())
        report["table_sha256"] = digest(table)
        assert report["table_sha256"] == read(MODEL)["table_sha256"]
        table_path = AREA / TABLE
        table_path.write_bytes(table)
        kernel = emit("family-kernel.rs", text(KERNEL).replace("H128_VOICE_TABLE_PATH", table_path.as_posix())
                      .replace("VCO_PANEL_PORT_PATH", (ROOT / PANEL).as_posix()))
        exe = AREA / "pilot-contours.exe"
        profile = ["--cfg", "pilot_loaded_filter"] if loaded else []
        proc, report["build"] = run([COMPILER, "--edition=2021", "-C", "opt-level=3", "-C", "target-feature=+fma",
                                     "-C", "link-arg=-Wl,--stack,33554432", "--cfg", "laboratory", *profile, "-A", "dead_code",
                                     component(kernel), "--extern", f"rf_d_circuit={LIB}", "-o", exe])
        if proc.returncode:
            replay, report["build_replay"] = run(report["build"]["command"])
            assert replay.returncode == proc.returncode and replay.stderr == proc.stderr
            raise RuntimeError(proc.stderr.decode(errors="replace"))
        anchor, trace = AREA / "contour-anchor.bin", AREA / "contour-reference.bin"
        for label, branch, start, frames, key in WINDOWS:
            phase, _, _, state = ref[branch][1][start]
            np.asarray(np.r_[state.ravel(), phase], "<f8").tofile(anchor)
            expected = [[lo, hi, sign] for pair, lo, hi, sign in archived if pair == 0] if branch == "positive" else []
            item = report["windows"][label] = dict(start_frame=start, frames=frames, key_v=key,
                                                    anchor_sha256=sha(anchor), expected_events=expected, modes={})
            proc, item["reference"] = run([exe, "contour-capture", anchor, start, frames, key])
            assert proc.returncode == 0, proc.stderr.decode(errors="replace")
            raw = np.frombuffer(proc.stdout, "<f8").reshape(-1, N)
            assert len(raw) == 1 + frames * 1024
            endpoints = np.vstack((raw[0], raw[2::2]))
            order = endpoints[:, 26] >= endpoints[:, 28]
            assert [[start * 4096 + 8 * int(i), start * 4096 + 8 * (int(i) + 1), int(order[i+1])]
                    for i in np.flatnonzero(order[1:] != order[:-1])] == expected
            item["return_domain"] = domain(proc.stdout)
            trace.write_bytes(proc.stdout)
            modes = LOADED_MODES if loaded else ((*MODES, *SENSITIVITY) if expected else MODES)
            if loaded and expected:
                modes = (*modes, *((f"x{node}_at_96khz", (node,)) for node in (2, 4, 54)))
            for mode, coarse in modes:
                command = [exe, "contour-replay", trace, key, sum(1 << node for node in coarse), 256 if loaded else 128]
                proc, trial = run(command, store=True)
                item["modes"][mode] = trial
                trial["coarse_nodes"] = coarse
                metrics = trial["metrics"] = (assess(proc.stdout, start, frames, expected, loaded) if proc.returncode == 0
                                               else dict(passed=False))
                if not metrics["passed"]:
                    replay, trial["unchanged_replay"] = run(command, store=True)
                    assert replay.returncode == proc.returncode and replay.stderr == proc.stderr
                    assert replay.stdout.splitlines()[1:] == proc.stdout.splitlines()[1:]
                if proc.returncode == 0:
                    print(label, mode, metrics["passed"], metrics["events"],
                          max(metrics["maximum_by_node_v"].values()), metrics["max_current_error_a"],
                          metrics["max_load_error_a"], metrics["max_compute_per_frame_ns"], flush=True)
                else:
                    print(label, mode, proc.stderr.decode().strip(), flush=True)
        report["passed"] = all(w["modes"]["fine"]["metrics"]["passed"] for w in report["windows"].values())
        sources.unchanged()
    except Exception:
        report["failure"] = traceback.format_exc()
        raise
    finally:
        for path in AREA.iterdir():
            assert path.is_file() and path.resolve().parent == AREA.resolve()
            path.unlink()
        write(out, report)
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
