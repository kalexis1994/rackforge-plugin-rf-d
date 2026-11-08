"""Validate the loaded Q20/Q12/C7 trigger and the volume latch as one system."""
import os
import subprocess
import traceback
from pathlib import Path

import numpy as np

from affine_evidence import Sources
from check_hybrid_voice import packed
from check_recovery_cost import digest
from check_rf_d_pilot_latch import (
    AREA, CLOCK, COMPILER, KERNEL, LIB, MODEL, PANEL, ROOT, SOURCES, TABLE, WINDOWS,
    emit, materialize, once, read, read_oracle, references, sha, source, text, write,
)

CORE = (6, 7, 8, 9, 10, 11, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 53)
PORTS = (4, 5, 14, 41, 48, 52)
CANDIDATE = "tools/rf_d_pilot_trigger.rs"
PROBE = "tools/rf_d_pilot_trigger_probe.rs"
DOC = "docs/VOZ_PILOTO_GATILLO_PROTOCOLO.md"
ALL_SOURCES = (*SOURCES, CANDIDATE, PROBE, DOC, "tools/check_rf_d_pilot_trigger.py")
MODES = ((1, 1), (128, 1), (128, 8), (128, 128))


def build(kernel):
    probe = source(kernel)
    code = once(probe.read_text(encoding="utf-8"), '        Some("ports") => ports(),', '''
        Some("ports") => ports(),
        Some("trigger-capture") if args.len() == 6 =>
            trigger_probe::capture(&args[2], args[3].parse()?, args[4].parse()?, args[5].parse()?),
        Some("trigger-replay") if args.len() == 7 =>
            trigger_probe::replay(&args[2], args[3].parse()?, args[4].parse()?, args[5].parse()?, args[6].parse()?),''')
    for name, path in (("pilot_trigger", CANDIDATE), ("trigger_probe", PROBE)):
        code += f'\n#[path = "{(ROOT / path).as_posix()}"] mod {name};\n'
    return emit(probe.name, code)


def capture_events(raw, start, frames):
    data = np.frombuffer(raw, "<f8")
    header = len(CORE) + len(PORTS)
    rows = data[header:].reshape(frames * 512, 2, header + 2 * len(CORE))
    a, b = CORE.index(26), CORE.index(28)
    order = np.r_[data[a] >= data[b], rows[:, 1, a] >= rows[:, 1, b]]
    base = start * 4096
    return [[base + int(k) * 8, base + (int(k) + 1) * 8, int(order[k + 1])]
            for k in np.flatnonzero(order[1:] != order[:-1])]


def assess(raw, start, frames, expected):
    lines = raw.decode().splitlines()
    tag, steps, current, charge, time = lines[0].split(",")
    assert tag == "CORE" and int(steps) == frames * 512
    errors, events = {}, []
    for line in lines[1:]:
        tag, *values = line.split(",")
        if tag == "NODE":
            k, v = values
            errors[int(k)] = float(v)
        else:
            assert tag == "SWITCH"
            lo, hi, sign = map(int, values)
            events.append([lo + start * 4096, hi + start * 4096, sign])
    assert tuple(errors) == CORE and all(np.isfinite(list(errors.values())))
    a, q, v = float(current), float(charge), max(errors.values())
    return dict(passed=events == expected and a <= 2e-13 and q <= 2e-20 and v <= 20e-6,
                events=events, expected_events=expected, stamp_error_a=a, charge_error_c=q,
                maximum_v=v, worst_node=max(errors, key=errors.get), maximum_by_node_v=errors,
                elapsed_ns=int(time))


def stable(raw):
    return [line.rsplit(b",", 1)[0] if line.startswith(b"CORE,") else line
            for line in raw.splitlines()]


def main():
    assert not list(AREA.iterdir())
    seq = 1
    while (out := ROOT / f"evidence/rf_d_pilot_trigger{seq:02}.json").exists():
        seq += 1
    sources = Sources(ALL_SOURCES)
    report = dict(passed=False, rack_integrated=False, **sources.fields(), core=CORE, ports=PORTS,
                  compiler_sha256=sha(Path(COMPILER)), library_sha256=sha(LIB), clock_sha256=sha(ROOT / CLOCK),
                  windows={})
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
        exe = AREA / "pilot-trigger.exe"
        proc, report["build"] = run([COMPILER, "--edition=2021", "-C", "opt-level=3", "-C", "target-feature=+fma",
                                     "-C", "link-arg=-Wl,--stack,33554432", "--cfg", "laboratory", "-A", "dead_code",
                                     build(kernel), "--extern", f"rf_d_circuit={LIB}", "-o", exe])
        if proc.returncode:
            replay, report["build_replay"] = run(report["build"]["command"])
            assert replay.returncode == proc.returncode and replay.stderr == proc.stderr
            raise RuntimeError(proc.stderr.decode(errors="replace"))
        anchor, trace = AREA / "trigger-anchor.bin", AREA / "trigger-reference.bin"
        for label, branch, start, frames, key in WINDOWS:
            phase, _, _, state = ref[branch][1][start]
            np.asarray(np.r_[state.ravel(), phase], "<f8").tofile(anchor)
            known = [[lo, hi, sign] for pair, lo, hi, sign in archived if pair == 0] if branch == "positive" else []
            item = report["windows"][label] = dict(start_frame=start, frames=frames, key_v=key,
                                                    anchor_sha256=sha(anchor), modes={})
            proc, item["reference"] = run([exe, "trigger-capture", anchor, start, frames, key])
            assert proc.returncode == 0, proc.stderr.decode(errors="replace")
            assert capture_events(proc.stdout, start, frames) == known
            trace.write_bytes(proc.stdout)
            def trial_for(port_stride, step_stride, fine_ports, keep_replay):
                command = [exe, "trigger-replay", trace, key, port_stride, step_stride, fine_ports]
                proc, trial = run(command, store=True)
                trial["metrics"] = (assess(proc.stdout, start, frames, known) if proc.returncode == 0
                                    else dict(passed=False))
                if keep_replay and not trial["metrics"]["passed"]:
                    replay, trial["unchanged_replay"] = run(command, store=True)
                    assert replay.returncode == proc.returncode and replay.stderr == proc.stderr
                    assert stable(replay.stdout) == stable(proc.stdout)
                return trial, proc.stderr.decode(errors="replace").strip()

            for port_stride, step_stride in MODES:
                mode = f"{port_stride}-{step_stride}"
                trial, stderr = trial_for(port_stride, step_stride, 0, True)
                item["modes"][mode] = trial
                m = trial["metrics"]
                print("PILOT_TRIGGER", label, mode, trial["exit_code"], m.get("passed"), m.get("events"),
                      m.get("maximum_v"), m.get("worst_node"), m.get("stamp_error_a"), m.get("charge_error_c"),
                      m.get("elapsed_ns"), stderr, flush=True)
            if branch == "positive":
                item["port_bandwidth"] = []
                for mask in range(1, (1 << len(PORTS)) - 1):
                    fine = [node for i, node in enumerate(PORTS) if mask & (1 << i)]
                    trial, _ = trial_for(128, 1, mask, False)
                    item["port_bandwidth"].append(dict(fine_ports=fine, **trial))
                passing = [row["fine_ports"] for row in item["port_bandwidth"] if row["metrics"]["passed"]]
                item["minimum_fine_ports"] = [nodes for nodes in passing if len(nodes) == min(map(len, passing))]
                if not passing and item["modes"]["1-1"]["metrics"]["passed"]:
                    item["minimum_fine_ports"] = [list(PORTS)]
                print("PILOT_TRIGGER_PORTS", item["minimum_fine_ports"], flush=True)
        report["admitted_modes"] = [f"{p}-{s}" for p, s in MODES if all(
            item["modes"][f"{p}-{s}"]["metrics"]["passed"] for item in report["windows"].values())]
        report["passed"] = "1-1" in report["admitted_modes"]
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
