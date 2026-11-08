"""Check a collector-driven Radau clock against the frozen loaded voice."""
import os
import subprocess
import traceback
from pathlib import Path

import numpy as np

from affine_evidence import Sources
from audit_vco_family_voice_bus_latch_lu import OUT as PRIOR_QA
from check_hybrid_voice import packed
from check_recovery_cost import digest
from check_vco_family_voice_bus_cost import references, switch_frames
from check_vco_family_voice_bus_hot import text
from check_vco_family_voice_bus_latch_lu import (
    CPU, GUARDS, REPORT as RELEASE, SOURCES as RELEASE_SOURCES, emit, generate, pin, verify_run,
)
from check_vco_family_voice_bus_model import AREA, materialize, read_oracle
from check_vco_phase import COMPILER, LIB
from prepare_dual_chain import ROOT, sha, write
from prepare_hybrid_stamp import once
from prepare_vco_family_voice_bus import TABLE
from validate_vco_family_voice_bus import J7, KERNEL, MODEL, PANEL, PREFIX, histories, parse_branch, read, refinement

OWN = "tools/check_vco_family_voice_bus_clock.py"
PROBE = "tools/vco_family_voice_bus_clock_probe.rs"
DOC = "docs/VCO_FAMILIA_BUS_VOZ_RELOJ_PROTOCOLO.md"
REPORT = PREFIX + "_clock"
CONTROL = RELEASE + "02.json"
SOURCES = (*RELEASE_SOURCES, OWN, PROBE, DOC)
CAPS = (32, 64, 128, 256)
TICKS = 4096


def metrics(raw, original, prior):
    lines = raw.splitlines()
    core = b"\n".join(line for line in lines if line.startswith((b"GRID,", b"END,")))
    measured, grid = parse_branch(core)
    assert measured["subdivisions"] in CAPS
    counter, = [line for line in lines if line.startswith(b"CLOCK,")]
    guard, newton, audits, *widths = map(int, counter.split(b",")[1:])
    assert len(widths) == 13 and sum((1 << k) * count for k, count in enumerate(widths)) == 128 * TICKS
    assert not any(widths[(TICKS // measured["subdivisions"]).bit_length():])
    assert newton == measured["rejected_substeps"]
    events = [list(map(int, line.split(b",")[1:])) for line in lines if line.startswith(b"SWITCH,")]
    assert audits == 10 + len(events)
    assert all(0 <= first < end <= 128 * TICKS and end - first <= 8 for _, first, end, _ in events)
    expected = [[pair, first * 512 // count, end * 512 // count, sign]
                for pair, first, end, count, sign in prior["latch_events"]]
    same_switches = events == expected and switch_frames(grid) == switch_frames(original[1])
    gates = refinement(grid, original[1])
    base = np.array([item[3].sum(axis=0)[J7] for item in original[1]])
    test = np.array([item[3].sum(axis=0)[J7] for item in grid])
    delta = test - base
    audio = dict(rms=float(np.linalg.norm(delta) / np.linalg.norm(base)),
                 peak=float(max(abs(delta)) / max(abs(base))), mean_v=float(abs(np.mean(delta))))
    assert max(abs(base)) > 0.
    accepted = (gates["passed"] and gates["phase_error_cycles"] <= 1e-7 and same_switches
                and audio["rms"] <= .001 and audio["peak"] <= .003 and audio["mean_v"] <= 1e-6)
    thread, = [line for line in lines if line.startswith(b"THREAD_CPU_NS,")]
    cpu = int(thread.split(b",")[1]) / 1e9
    assert cpu > 0.
    return dict(**measured, passed=accepted, refinement=gates, audio=audio, switch_brackets=events,
                expected_brackets=expected, same_switches=same_switches, guard_retries=guard, thread_cpu_s=cpu,
                accepted_steps=sum(widths), widths=widths, audited_steps=audits)


def stable(raw):
    lines = []
    for line in raw.splitlines():
        if line.startswith(b"THREAD_CPU_NS,"):
            continue
        if line.startswith(b"END,"):
            fields = line.split(b",")
            fields[3] = b"elapsed"
            line = b",".join(fields)
        lines.append(line)
    return lines


def main():
    assert not list(AREA.iterdir())
    sequence = 1
    while (ROOT / f"{REPORT}{sequence:02}.json").exists():
        sequence += 1
    output = ROOT / f"{REPORT}{sequence:02}.json"
    sources = Sources(SOURCES)
    report = dict(passed=False, **sources.fields(), compiler_sha256=sha(Path(COMPILER)),
                  library_sha256=sha(LIB), prior_sha256=sha(ROOT / PRIOR_QA), control_sha256=sha(ROOT / CONTROL),
                  trials={}, confirmation={}, chosen={})
    env = dict(os.environ, PATH="C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;" + os.environ["PATH"])
    command = []
    process = None

    def run(args):
        nonlocal command, process
        command = list(map(str, args))
        process = None
        process = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, timeout=180)
        return dict(command=command, exit_code=process.returncode,
                    stdout=packed(process.stdout), stderr=packed(process.stderr))

    try:
        report["fma_check"] = run(["pwsh", "-NoProfile", "-Command", "[System.Runtime.Intrinsics.X86.Fma]::IsSupported"])
        assert process.returncode == 0 and process.stdout.strip() == b"True"
        reference, report["reference_inputs"] = references()
        history, report["private_inputs"] = histories()
        prior = read(PRIOR_QA)
        assert prior["passed"]
        table, _, _, _, _, _ = materialize(read_oracle())
        report["table_sha256"] = digest(table)
        assert report["table_sha256"] == read(MODEL)["table_sha256"]
        table_path = AREA / TABLE
        table_path.write_bytes(table)
        kernel = emit("family-kernel.rs", text(KERNEL).replace("H128_VOICE_TABLE_PATH", table_path.as_posix())
                      .replace("VCO_PANEL_PORT_PATH", (ROOT / PANEL).as_posix()))
        report["affinity"] = pin()
        probe = generate(kernel, "combined", False, True)
        source = once(probe.read_text(encoding="utf8"), '        Some("ports") => ports(),', '''        Some("ports") => ports(),
        Some("clock") if args.len() == 5 => clock::run(&args[2], &args[3], args[4].parse()?),''')
        source += f'\n#[path = "{(ROOT / PROBE).as_posix()}"] mod clock;\n'
        emit(probe.name, source)
        exe = AREA / "clock.exe"
        report["build"] = run([COMPILER, "--edition=2021", "-C", "opt-level=3", "-C", "target-feature=+fma",
                               "-C", "link-arg=-Wl,--stack,33554432", "-A", "dead_code",
                               probe, "--extern", f"rf_d_circuit={LIB}", "-o", exe])
        assert process.returncode == 0, process.stderr.decode(errors="replace")
        report["affinity_check"] = run([exe, "affinity"])
        assert process.returncode == 0 and process.stdout.strip() == f"AFFINITY,{1 << CPU},{CPU}".encode()
        report["guards"] = run([exe, "linear-guard"])
        assert process.returncode == 0 and b"\n".join(process.stdout.splitlines()) == GUARDS
        state = AREA / "clock-history.bin"
        for label in ("positive", "negative"):
            original = reference[label]
            frozen = prior["loaded_branches"][label]["combined"]
            state.write_bytes(history[label])
            report["trials"][label] = {}
            for cap in CAPS:
                item = run([exe, "clock", state, label, cap])
                report["trials"][label][str(cap)] = item
                raw = process.stdout
                if process.returncode == 0:
                    item["metrics"] = metrics(raw, original, frozen)
                    print("CLOCK_TRIAL", label, cap, item["metrics"], flush=True)
                    if item["metrics"]["passed"]:
                        report["chosen"][label] = cap
                        break
                else:
                    print("CLOCK_REJECT", label, cap, process.stderr.decode(errors="replace"), flush=True)
                status, stderr = process.returncode, process.stderr
                item["replay"] = run(command)
                assert process.returncode == status and process.stderr == stderr and stable(process.stdout) == stable(raw)
        for label, cap in report["chosen"].items():
            original = reference[label]
            frozen = prior["loaded_branches"][label]["combined"]
            state.write_bytes(history[label])
            fixed = run([exe, "branch", state, label, original[0]["subdivisions"]])
            assert process.returncode == 0, process.stderr.decode(errors="replace")
            fixed["metrics"] = verify_run(process.stdout, original, frozen, True)
            trial = run([exe, "clock", state, label, cap])
            assert process.returncode == 0, process.stderr.decode(errors="replace")
            trial["metrics"] = metrics(process.stdout, original, frozen)
            assert trial["metrics"]["passed"]
            before = report["trials"][label][str(cap)]
            assert {k: v for k, v in before["metrics"].items() if k not in ("duration_s", "thread_cpu_s")} == {
                k: v for k, v in trial["metrics"].items() if k not in ("duration_s", "thread_cpu_s")}
            report["confirmation"][label] = dict(fixed=fixed, trial=trial,
                                                 speedup=fixed["metrics"]["duration_s"] / trial["metrics"]["duration_s"])
            print("CLOCK_CONFIRM", label, fixed["metrics"]["duration_s"], trial["metrics"]["duration_s"], flush=True)
        report["passed"] = True
    except Exception:
        report["failure"] = traceback.format_exc()
        if process is not None:
            report["failed"] = dict(exit_code=process.returncode, stdout=packed(process.stdout), stderr=packed(process.stderr))
        if command:
            try:
                report["unchanged_replay"] = run(command)
            except subprocess.TimeoutExpired:
                report["unchanged_replay"] = dict(timeout=True)
    finally:
        write(output, report)
        for path in AREA.iterdir():
            assert path.is_file() and path.resolve().parent == AREA.resolve()
            path.unlink()
        sources.unchanged()
        report["temporary_area_empty"] = not list(AREA.iterdir())
        write(output, report)
    print("CLOCK_COST", report["passed"], report["chosen"], report.get("failure"), flush=True)
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
