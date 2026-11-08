"""Validate anticipation on the charged voice, then compare variable clocks."""
import argparse
import os
import statistics
import subprocess
import traceback
from pathlib import Path

import numpy as np

from affine_evidence import Sources
from audit_vco_family_voice_bus_clock import OUT as PRIOR_QA
from check_hybrid_voice import packed, unpack
from check_recovery_cost import digest
from check_vco_family_voice_bus_clock import (
    PROBE as OLD_PROBE, REPORT as OLD_REPORT, SOURCES as OLD_SOURCES, TICKS,
    metrics as old_metrics, stable,
)
from check_vco_family_voice_bus_cost import references, switch_frames
from check_vco_family_voice_bus_hot import text
from check_vco_family_voice_bus_latch_lu import (
    CPU, GUARDS, REPORT as RELEASE, emit, generate, pin, verify_run,
)
from check_vco_family_voice_bus_model import AREA, materialize, read_oracle
from check_vco_phase import COMPILER, LIB
from prepare_dual_chain import ROOT, sha, write
from prepare_hybrid_stamp import once
from prepare_vco_family_voice_bus import TABLE
from validate_vco_family_voice_bus import J7, KERNEL, MODEL, PANEL, PREFIX, histories, parse_branch, read, refinement
import vco_family_voice_bus_approach_paths as paths

OWN = "tools/check_vco_family_voice_bus_approach.py"
DOC = "docs/VCO_FAMILIA_BUS_VOZ_APROXIMACION_PROTOCOLO.md"
TRANSFORM = "tools/vco_family_voice_bus_approach_paths.py"
REPORT = PREFIX + "_approach"
CONTROL = OLD_REPORT + "01.json"
LATCH = RELEASE + "_tests01.json"
SOURCES = (*OLD_SOURCES, OWN, DOC, TRANSFORM)
RECIPES = [(base, middle) for middle in (64, 128) for base in (8, 16, 32)]
PHASE = {"positive": 0., "negative": .37}
HELD_PHASE = .125
ORDERS = (("old", "new"), ("new", "old"))


def grid_lines(raw):
    return b"\n".join(line for line in raw.splitlines() if line.startswith((b"GRID,", b"END,")))


def metrics(raw, original, prior, recipe):
    lines = raw.splitlines()
    measured, grid = parse_branch(grid_lines(raw))
    control, = [line for line in lines if line.startswith(b"CLOCK,")]
    guard, newton, audits, *widths = map(int, control.split(b",")[1:])
    approach, = [line for line in lines if line.startswith(b"APPROACH,")]
    middle, retries, ticks = map(int, approach.split(b",")[1:])
    assert [measured["subdivisions"], middle] == list(recipe)
    assert len(widths) == 13 and sum((1 << i) * count for i, count in enumerate(widths)) == 128 * TICKS
    assert not any(widths[(TICKS // recipe[0]).bit_length():]) and newton == measured["rejected_substeps"]
    assert 0 <= ticks <= 128 * TICKS and (ticks > 0 or retries == 0)
    events = [list(map(int, line.split(b",")[1:])) for line in lines if line.startswith(b"SWITCH,")]
    expected = [[pair, first * 512 // count, end * 512 // count, sign]
                for pair, first, end, count, sign in prior["latch_events"]]
    assert audits == 10 + len(events)
    assert all(0 <= first < end <= 128 * TICKS and end - first <= 8 for _, first, end, _ in events)
    held = [line for line in lines if line.startswith(b"HOLD,")]
    recovery = {}
    if held:
        line, = held
        steps, held_ticks = map(int, line.split(b",")[1:])
        assert 0 <= held_ticks <= min(ticks, len(events) * TICKS) and 0 <= steps <= sum(widths)
        assert bool(steps) == bool(held_ticks)
        recovery = dict(held_steps=steps, held_ticks=held_ticks)
    same_switches = events == expected and switch_frames(grid) == switch_frames(original[1])
    gates = refinement(grid, original[1])
    a = np.array([row[3].sum(axis=0)[J7] for row in grid])
    b = np.array([row[3].sum(axis=0)[J7] for row in original[1]])
    peak = float(max(abs(b)))
    assert peak > 0.
    error = a - b
    audio = dict(rms=float(np.linalg.norm(error) / np.linalg.norm(b)),
                 peak=float(max(abs(error)) / peak), mean_v=float(abs(np.mean(error))))
    passed = (same_switches and gates["passed"] and gates["phase_error_cycles"] <= 1e-7
              and audio["rms"] <= .001 and audio["peak"] <= .003 and audio["mean_v"] <= 1e-6)
    thread, = [line for line in lines if line.startswith(b"THREAD_CPU_NS,")]
    elapsed = int(thread.split(b",")[1]) / 1e9
    assert elapsed > 0.
    return dict(**measured, **recovery, passed=passed, refinement=gates, audio=audio, same_switches=same_switches,
                switch_brackets=events, expected_brackets=expected, guard_retries=guard, audited_steps=audits,
                thread_cpu_s=elapsed, accepted_steps=sum(widths), widths=widths,
                intermediate_cap=middle, approach_retries=retries, approach_ticks=ticks)


def held_reference(raw):
    original = parse_branch(grid_lines(raw))
    assert original[0]["subdivisions"] == 512 and original[1][0][0] == HELD_PHASE
    brackets = [list(map(int, line.split(b",")[1:])) for line in raw.splitlines() if line.startswith(b"LATCH,")]
    assert len(brackets) == 1
    prior = {"latch_events": brackets}
    return original, prior, verify_run(raw, original, prior, True)


def paired_stats(pairs):
    variants = ("old", "new")
    output = {}
    for v in variants:
        output[v] = {key: statistics.median(pair["runs"][v]["metrics"][key] for pair in pairs)
                     for key in ("duration_s", "thread_cpu_s", "accepted_steps")}
    output["speedup"] = output["old"]["duration_s"] / output["new"]["duration_s"]
    output["cpu_speedup"] = output["old"]["thread_cpu_s"] / output["new"]["thread_cpu_s"]
    return output


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--hold", action="store_true")
    hold = cli.parse_args().hold
    assert not list(AREA.iterdir())
    sequence = 1
    while (ROOT / f"{REPORT}{sequence:02}.json").exists():
        sequence += 1
    output = ROOT / f"{REPORT}{sequence:02}.json"
    sources = Sources(SOURCES)
    report = dict(passed=False, hold=hold, **sources.fields(), compiler_sha256=sha(Path(COMPILER)),
                  library_sha256=sha(LIB), prior_sha256=sha(ROOT / PRIOR_QA), control_sha256=sha(ROOT / CONTROL),
                  latch_sha256=sha(ROOT / LATCH), trials={}, chosen={}, held={}, paired={})
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

    def replay(item):
        original = process
        item["replay"] = run(command)
        assert process.returncode == original.returncode and process.stderr == original.stderr
        assert stable(process.stdout) == stable(original.stdout)

    try:
        report["fma_check"] = run(["pwsh", "-NoProfile", "-Command", "[System.Runtime.Intrinsics.X86.Fma]::IsSupported"])
        assert process.returncode == 0 and process.stdout.strip() == b"True"
        reference, report["reference_inputs"] = references()
        history, report["private_inputs"] = histories()
        prior, release, old = read(PRIOR_QA), read(LATCH), read(CONTROL)
        assert prior["passed"] and release["passed"] and old["passed"]
        table, _, _, _, _, _ = materialize(read_oracle())
        report["table_sha256"] = digest(table)
        assert report["table_sha256"] == read(MODEL)["table_sha256"]
        table_path = AREA / TABLE
        table_path.write_bytes(table)
        kernel = emit("family-kernel.rs", text(KERNEL).replace("H128_VOICE_TABLE_PATH", table_path.as_posix())
                      .replace("VCO_PANEL_PORT_PATH", (ROOT / PANEL).as_posix()))
        report["affinity"] = pin()
        probe = generate(kernel, "combined", False, True)
        controller = paths.controller(text(OLD_PROBE))
        module = emit("approach.rs", paths.hold_after_switch(controller) if hold else controller)
        source = paths.fixed_phase(probe.read_text(encoding="utf8"))
        source = once(source, '        Some("ports") => ports(),', '''        Some("ports") => ports(),
        Some("clock") if args.len() == 5 => clock::run(&args[2], &args[3], args[4].parse()?),
        Some("approach") if args.len() == 7 => approach::run(
            &args[2], &args[3], args[4].parse()?, args[5].parse()?, args[6].parse()?),''')
        source += f'\n#[path = "{(ROOT / OLD_PROBE).as_posix()}"] mod clock;\n#[path = "{module.as_posix()}"] mod approach;\n'
        emit(probe.name, source)
        exe = AREA / "approach.exe"
        report["build"] = run([COMPILER, "--edition=2021", "-C", "opt-level=3", "-C", "target-feature=+fma",
                               "-C", "link-arg=-Wl,--stack,33554432", "-A", "dead_code",
                               probe, "--extern", f"rf_d_circuit={LIB}", "-o", exe])
        assert process.returncode == 0, process.stderr.decode(errors="replace")
        report["affinity_check"] = run([exe, "affinity"])
        assert process.returncode == 0 and process.stdout.strip() == f"AFFINITY,{1 << CPU},{CPU}".encode()
        report["guards"] = run([exe, "linear-guard"])
        assert process.returncode == 0 and b"\n".join(process.stdout.splitlines()) == GUARDS
        state = AREA / "approach-history.bin"
        for label in ("positive", "negative"):
            state.write_bytes(history[label])
            frozen = release["loaded_branches"][label]["combined"]
            cases = report["trials"][label] = []
            for recipe in RECIPES:
                item = run([exe, "approach", state, label, *recipe, PHASE[label]])
                cases.append(dict(recipe=recipe, run=item))
                if process.returncode == 0:
                    item["metrics"] = metrics(process.stdout, reference[label], frozen, recipe)
                    m = item["metrics"]
                    print("APPROACH_TRIAL", label, recipe, m["passed"], m["refinement"], m["switch_brackets"], m["accepted_steps"], flush=True)
                    if m["passed"]:
                        report["chosen"][label] = recipe
                        break
                else:
                    print("APPROACH_REJECT", label, recipe, process.stderr.decode(errors="replace"), flush=True)
                replay(item)
        if "positive" in report["chosen"]:
            state.write_bytes(history["positive"])
            fixed = report["held"]["fixed"] = run([exe, "branch-phase", state, "positive", 512, HELD_PHASE])
            assert process.returncode == 0, process.stderr.decode(errors="replace")
            target, latch, fixed["metrics"] = held_reference(process.stdout)
            recipe = report["chosen"]["positive"]
            candidate = report["held"]["candidate"] = run([exe, "approach", state, "positive", *recipe, HELD_PHASE])
            if process.returncode == 0:
                candidate["metrics"] = metrics(process.stdout, target, latch, recipe)
            if not candidate.get("metrics", {}).get("passed"):
                replay(candidate)
            print("APPROACH_HELD", candidate.get("metrics", {}).get("passed", False), flush=True)
        if len(report["chosen"]) == 2 and report["held"]["candidate"].get("metrics", {}).get("passed"):
            for label in ("positive", "negative"):
                state.write_bytes(history[label])
                frozen = release["loaded_branches"][label]["combined"]
                previous = old["confirmation"][label]["trial"]["stdout"]
                selected = report["trials"][label][-1]["run"]["stdout"]
                recipe = report["chosen"][label]
                pairs = report["paired"][label] = []
                for order in ORDERS:
                    pair = dict(order=order, runs={})
                    pairs.append(pair)
                    for variant in order:
                        args = (["clock", state, label, prior["chosen"][label]] if variant == "old"
                                else ["approach", state, label, *recipe, PHASE[label]])
                        item = pair["runs"][variant] = run([exe, *args])
                        assert process.returncode == 0, process.stderr.decode(errors="replace")
                        raw = process.stdout
                        if variant == "old":
                            item["metrics"] = old_metrics(raw, reference[label], frozen)
                            assert stable(raw) == stable(unpack(previous))
                        else:
                            item["metrics"] = metrics(raw, reference[label], frozen, recipe)
                            assert stable(raw) == stable(unpack(selected))
                        assert item["metrics"]["passed"]
                    print("APPROACH_PAIR", label, order, {v: r["metrics"]["duration_s"] for v, r in pair["runs"].items()}, flush=True)
            report["comparison"] = {label: paired_stats(pairs) for label, pairs in report["paired"].items()}
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
    print("APPROACH_COST", report["passed"], report["chosen"], report.get("comparison"), report.get("failure"), flush=True)
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
