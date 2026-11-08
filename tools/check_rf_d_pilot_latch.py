"""Isolate the charge-driven latch and test the contour boundary bandwidth."""
import os
import subprocess
import traceback
from pathlib import Path

import numpy as np

from affine_evidence import Sources
from check_hybrid_voice import packed
from check_recovery_cost import digest
from check_rf_d_reduced_contour_ports import CLOCK, SOURCES as CONTOUR_SOURCES, build
from check_vco_family_voice_bus_cost import references
from check_vco_family_voice_bus_hot import text
from check_vco_family_voice_bus_latch_lu import emit
from check_vco_family_voice_bus_model import AREA, materialize, read_oracle
from check_vco_phase import COMPILER, LIB
from prepare_dual_chain import ROOT, sha, write
from prepare_hybrid_stamp import once
from prepare_vco_family_voice_bus import TABLE
from validate_vco_family_voice_bus import KERNEL, MODEL, PANEL, read

OWN = "tools/check_rf_d_pilot_latch.py"
CORE = "tools/rf_d_pilot_latch.rs"
PROBE = "tools/rf_d_pilot_latch_probe.rs"
LU = "tools/rf_d_reduced_engine_lu.rs"
CHARGE = "crates/rf-d-circuit/src/conditioned_voice_latch.rs"
DOC = "docs/VOZ_PILOTO_BIESTABLE_PROTOCOLO.md"
SOURCES = (*CONTOUR_SOURCES, OWN, CORE, PROBE, LU, CHARGE, DOC,
           "crates/rf-d-circuit/src/junction_charge.rs")
WINDOWS = (("positive_crossing", "positive", 76, 5, 0.),
           ("negative_key_on", "negative", 16, 2, 10.),
           ("negative_key_off", "negative", 96, 2, 0.))


def source(kernel):
    probe = build(kernel)
    code = once(probe.read_text(encoding="utf8"), '        Some("ports") => ports(),', '''
        Some("ports") => ports(),
        Some("latch-capture") if args.len() == 6 =>
            latch_probe::capture(&args[2], args[3].parse()?, args[4].parse()?, args[5].parse()?),
        Some("latch-replay") if args.len() == 4 => latch_probe::replay(&args[2], &args[3]),''')
    for name, path in (("latch_core", CORE), ("latch_probe", PROBE), ("latch_charge", CHARGE), ("reduced_lu", LU)):
        code += f'\n#[path = "{(ROOT / path).as_posix()}"] mod {name};\n'
    return emit(probe.name, code)


def capture_events(raw, count):
    values = np.frombuffer(raw, "<f8")
    initial = values[:5]
    points = values[11:].reshape(count * 512, 2, 21)[:, 1, :5]
    order = np.r_[initial[2] >= initial[4], points[:, 2] >= points[:, 4]]
    return [[int(k)*8, int(k+1)*8, int(order[k+1])] for k in np.flatnonzero(order[1:] != order[:-1])]


def assess(raw, start, count, expected):
    lines = raw.decode().splitlines()
    tag, mode, steps, current, charge, volts, collector, time = lines[0].split(",")
    assert tag == "CORE" and int(steps) == count * 512
    events = []
    for line in lines[1:]:
        kind, a, b, sign = line.split(",")
        assert kind == "SWITCH"
        events.append([int(a) + 4096 * start, int(b) + 4096 * start, int(sign)])
    a, q, v, g = map(float, (current, charge, volts, collector))
    return dict(mode=mode, passed=events == expected and a <= 2e-13 and q <= 2e-20 and v <= 20e-6,
                events=events, expected_events=expected, stamp_error_a=a, charge_error_c=q,
                maximum_v=v, maximum_collector_diff_v=g, elapsed_ns=int(time))


def main():
    assert not list(AREA.iterdir())
    seq = 1
    while (out := ROOT / f"evidence/rf_d_pilot_latch{seq:02}.json").exists():
        seq += 1
    sources = Sources(SOURCES)
    report = dict(passed=False, pilot_boundary_passed=False, rack_integrated=False, **sources.fields(),
                  compiler_sha256=sha(Path(COMPILER)), library_sha256=sha(LIB), clock_sha256=sha(ROOT / CLOCK),
                  windows={})
    env = dict(os.environ, PATH="C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;" + os.environ["PATH"])

    def run(args, store=False):
        command = list(map(str, args))
        proc = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, timeout=180)
        rec = dict(command=command, exit_code=proc.returncode, stderr=packed(proc.stderr),
                   stdout=packed(proc.stdout) if store else dict(sha256=digest(proc.stdout), bytes=len(proc.stdout)))
        return proc, rec

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
        exe = AREA / "pilot-latch.exe"
        proc, report["build"] = run([COMPILER, "--edition=2021", "-C", "opt-level=3", "-C", "target-feature=+fma",
                                     "-C", "link-arg=-Wl,--stack,33554432", "--cfg", "laboratory", "-A", "dead_code",
                                     source(kernel), "--extern", f"rf_d_circuit={LIB}", "-o", exe])
        if proc.returncode:
            replay, report["build_replay"] = run(report["build"]["command"])
            assert replay.returncode == proc.returncode and replay.stderr == proc.stderr
            raise RuntimeError(proc.stderr.decode(errors="replace"))
        path = AREA / "latch-anchor.bin"
        trace = AREA / "latch-conditional.bin"
        for label, branch, start, count, key in WINDOWS:
            angle, _, _, state = ref[branch][1][start]
            np.asarray(np.r_[state.ravel(), angle], "<f8").tofile(path)
            item = report["windows"][label] = dict(start_frame=start, frames=count, key_v=key, anchor_sha256=sha(path), modes={})
            proc, item["reference"] = run([exe, "latch-capture", path, start, count, key])
            assert proc.returncode == 0, proc.stderr.decode(errors="replace")
            trace.write_bytes(proc.stdout)
            known = [[lo, hi, sign] for pair, lo, hi, sign in archived if pair == 0] if branch == "positive" else []
            observed = [[lo + start * 4096, hi + start * 4096, sign]
                        for lo, hi, sign in capture_events(proc.stdout, count)]
            assert observed == known, (observed, known)
            modes = ("fine", "pilot", "cr8-fine", "cr8-pilot") if branch == "positive" else ("fine", "pilot", "cr8-fine")
            for mode in modes:
                command = [exe, "latch-replay", trace, mode]
                proc, trial = run(command, store=True)
                item["modes"][mode] = trial
                trial["metrics"] = (assess(proc.stdout, start, count, known) if proc.returncode == 0
                                    else dict(passed=False))
                if not trial["metrics"]["passed"]:
                    replay, trial["unchanged_replay"] = run(command, store=True)
                    # The runtime counter is observational, so compare everything else.
                    stable = lambda data: [line.rsplit(b",", 1)[0] if line.startswith(b"CORE,") else line
                                           for line in data.splitlines()]
                    assert replay.returncode == proc.returncode and replay.stderr == proc.stderr
                    assert stable(replay.stdout) == stable(proc.stdout)
                print("PILOT_LATCH", label, mode, trial["metrics"], flush=True)
            if branch == "positive":
                sensitivity = item["boundary_bandwidth"] = []
                nodes = (17, 6, 9, 4, 24)
                for mask in range(1, 31):
                    proc, trial = run([exe, "latch-replay", trace, f"mixed-{mask}"], store=True)
                    measured = assess(proc.stdout, start, count, known) if proc.returncode == 0 else dict(passed=False)
                    sensitivity.append(dict(exact_nodes=[node for k, node in enumerate(nodes) if mask & (1 << k)],
                                            run=trial, metrics=measured))
                passing = [trial["exact_nodes"] for trial in sensitivity if trial["metrics"]["passed"]]
                item["smallest_fine_boundary"] = ([nodes for nodes in passing if len(nodes) == min(map(len, passing))]
                                                   if passing else [list(nodes)])
                print("PILOT_LATCH_BOUNDARY", item["smallest_fine_boundary"], flush=True)
        positive_modes = report["windows"]["positive_crossing"]["modes"]
        report["cr8_fine_passed"] = all(item["modes"]["cr8-fine"]["metrics"]["passed"]
                                        for item in report["windows"].values())
        report["cr8_pilot_passed"] = positive_modes["cr8-pilot"]["metrics"]["passed"]
        report["passed"] = report["cr8_fine_passed"] and all(
            item["modes"]["fine"]["metrics"]["passed"] for item in report["windows"].values()
        )
        report["pilot_boundary_passed"] = all(item["modes"]["pilot"]["metrics"]["passed"]
                                              for item in report["windows"].values())
        sources.unchanged()
    except Exception:
        report["failure"] = traceback.format_exc()
        raise
    finally:
        write(out, report)
        for path in AREA.iterdir():
            assert path.is_file() and path.resolve().parent == AREA.resolve()
            path.unlink()
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
