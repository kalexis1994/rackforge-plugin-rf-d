"""Compare event-resolving Radau step control with the frozen loaded-voice reserves."""
import os
import struct
import subprocess
import traceback
from pathlib import Path

import numpy as np

from affine_evidence import Sources
from check_hybrid_voice import packed, unpack
from check_recovery_cost import digest
from check_vco_family_voice_bus_model import AREA, materialize, read_oracle
from check_vco_phase import COMPILER, LIB
from prepare_dual_chain import ROOT, sha, write
from prepare_hybrid_stamp import once
from prepare_vco_family_voice_bus import TABLE
from validate_vco_family_voice_bus import COUPLED, J7, KERNEL, MODEL, PANEL, PATHS, PREFIX, PROBE, histories, parse_branch, read, refinement
from vco_family_voice_bus_receipts import read_receipt, receipt_bytes

OWN = "tools/check_vco_family_voice_bus_cost.py"
ADAPTIVE = "tools/vco_family_voice_bus_adaptive.rs"
COST = "tools/vco_family_voice_bus_cost_probe.rs"
DOC = "docs/VCO_FAMILIA_BUS_VOZ_COSTO_PROTOCOLO.md"
BASE_QA = PREFIX + "_tests01.json"
TICKS = 65_536


def references():
    names = [PREFIX + f"_coupled{i:02}.json" for i in (2, 4)]
    receipts = [read_receipt(name) for name in names]
    result = {}
    for label, report in zip(("negative", "positive"), receipts):
        trace, = [trace for trace in report["traces"] if trace["case"] == label]
        assert trace["refinement"]["passed"]
        metrics, grid = parse_branch(unpack(trace["runs"][-1]["stdout"]))
        result[label] = (metrics, grid)
    return result, {name: digest(receipt_bytes(name)) for name in names}


def profile_source(text):
    text = once(text, "pub fn stages<const FULL: bool>", "fn raw_stages<const FULL: bool>")
    text = once(text, "fn direction(work:", "fn raw_direction(work:")
    return text + """
pub fn stages<const FULL: bool>(
    family: &Family, p: Parameters, old: State, phase: f64, delta: [State; 2],
    controls: Controls, h: f64,
) -> Result<Stages, StepError> {
    crate::cost::measure(usize::from(!FULL), || raw_stages::<FULL>(family, p, old, phase, delta, controls, h))
}

fn direction(work: &mut solver::Workspace, stages: &Stages, r: [f64; M]) -> Result<[f64; M], StepError> {
    crate::cost::measure(2, || raw_direction(work, stages, r))
}
"""


def build_source(kernel, instrumented=False):
    path = AREA / "cost-probe.rs"
    text = (ROOT / PROBE).read_text(encoding="utf8").replace("FAMILY_KERNEL_PATH", kernel.as_posix())
    parts = dict(PATHS)
    if instrumented:
        profiled = AREA / "cost-profiled.rs"
        profiled.write_text(profile_source((ROOT / COUPLED).read_text(encoding="utf8")), encoding="utf8", newline="\n")
        parts["COUPLED_PATH"] = profiled.relative_to(ROOT).as_posix()
    for slot, module in parts.items():
        text = text.replace(slot, (ROOT / module).as_posix())
    text = once(text, '        Some("ports") => ports(),', '''        Some("ports") => ports(),
        #[cfg(cost_profile)]
        Some("profile") if args.len() == 4 => cost::profile(&args[2], &args[3]),
        Some("adaptive") if args.len() == 4 => cost::adaptive(&args[2], &args[3]),''')
    text += f'\n#[path = "{(ROOT / ADAPTIVE).as_posix()}"] mod adaptive;\n'
    text += f'#[path = "{(ROOT / COST).as_posix()}"] mod cost;\n'
    path.write_text(text, encoding="utf8", newline="\n")
    return path


def profile_metrics(raw, target, frame):
    lines = raw.decode().splitlines()
    wall, grid, counters = lines
    assert wall.startswith("PROFILE_WALL,") and counters.startswith("PROFILE,")
    fields = grid.split(",")
    assert fields[:2] == ["GRID", str(frame)]
    phase, r59, r60 = map(float, fields[2:5])
    assert (phase, r59, r60) == target[:3]
    assert [int(x, 16) for x in fields[5:]] == target[3].view("<u8").ravel().tolist()
    times = list(map(int, counters.split(",")[1:]))
    metrics = {name: dict(ns=times[k * 2], calls=times[k * 2 + 1])
               for k, name in enumerate(("full_stage", "residual_stage", "linear_solve"))}
    wall_ns = int(wall.split(",")[1])
    assert 0 < sum(v["ns"] for v in metrics.values()) <= wall_ns
    return dict(metrics, wall_ns=wall_ns, same_end_state=True)


def switch_frames(grid):
    nodes = np.array([item[3].sum(axis=0) for item in grid])
    states = nodes[:, [26, 40]] >= nodes[:, [28, 42]]
    return [(int(pair), int(frame + 1), int(states[frame + 1, pair]))
            for frame, pair in zip(*np.where(states[:-1] != states[1:]))]


def parse_adaptive(raw, ref):
    lines = raw.splitlines()
    kept = b"\n".join(line for line in lines if line.startswith((b"GRID,", b"END,")))
    measured, grid = parse_branch(kept)
    line, = [line.decode() for line in lines if line.startswith(b"ADAPT,")]
    _, accepted, rejected, minimum, maximum, error, audits = line.split(",")
    assert int(accepted) > 0 and 2 <= int(minimum) <= int(maximum) <= 8192 and int(audits) >= 7
    assert 0. <= float(error) <= 1.
    assert measured["rejected_substeps"] == int(rejected)
    brackets = [tuple(map(int, line.split(b",")[1:])) for line in lines if line.startswith(b"SWITCH,")]
    assert all(0 <= start < end <= 128 * TICKS for _, start, end, _ in brackets)
    switches = [(pair, (end + TICKS - 1) // TICKS, direction) for pair, start, end, direction in brackets]
    expected = switch_frames(ref)
    nodes = np.array([item[3].sum(axis=0) for item in grid])
    reference = np.array([item[3].sum(axis=0) for item in ref])
    target = reference[:, J7]
    delta = nodes[:, J7] - target
    peak = float(max(abs(target)))
    assert peak > 0.
    audio = dict(rms_relative=float(np.linalg.norm(delta) / np.linalg.norm(target)),
                 peak_relative=float(max(abs(delta)) / peak), mean_v=float(abs(np.mean(delta))))
    gates = refinement(grid, ref)
    passed = (gates["passed"] and audio["rms_relative"] <= .001 and audio["peak_relative"] <= .003
              and audio["mean_v"] <= 1e-6 and switches == switch_frames(grid) == expected)
    return dict(**measured, accepted=int(accepted), minimum_ticks=int(minimum), maximum_ticks=int(maximum),
                local_error=float(error), audited_steps=int(audits), refinement=gates, audio=audio,
                switch_brackets=brackets, reference_switches=expected, passed=passed)


def main():
    assert not list(AREA.iterdir())
    seq = 1
    while (ROOT / f"{PREFIX}_cost{seq:02}.json").exists():
        seq += 1
    destination = ROOT / f"{PREFIX}_cost{seq:02}.json"
    sources = Sources([OWN, ADAPTIVE, COST, DOC, COUPLED, KERNEL, PANEL, PROBE, *PATHS.values()])
    report = dict(passed=False, **sources.fields(), compiler_sha256=sha(Path(COMPILER)), library_sha256=sha(LIB),
                  prior_sha256=sha(ROOT / BASE_QA), profiles={}, adaptive={}, fixed={})
    env = dict(os.environ, PATH="C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;" + os.environ["PATH"])
    command, process = [], None

    def run(args):
        nonlocal command, process
        command, process = list(map(str, args)), None
        process = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, timeout=150)
        return dict(command=command, exit_code=process.returncode, stdout=packed(process.stdout), stderr=packed(process.stderr))

    def build(exe, source, profile=False):
        return run([COMPILER, "--edition=2021", "-C", "opt-level=3", "-C", "link-arg=-Wl,--stack,33554432",
                    "-A", "dead_code", *(["--cfg", "cost_profile"] if profile else []), source,
                    "--extern", f"rf_d_circuit={LIB}", "-o", exe])

    try:
        reference, report["reference_inputs"] = references()
        history, report["private_inputs"] = histories()
        table, _, _, _, _, _ = materialize(read_oracle())
        assert digest(table) == read(MODEL)["table_sha256"]
        report["table_sha256"] = digest(table)
        table_path = AREA / TABLE
        table_path.write_bytes(table)
        kernel = AREA / "family-kernel.rs"
        kernel.write_text((ROOT / KERNEL).read_text(encoding="utf8").replace(
            "H128_VOICE_TABLE_PATH", table_path.as_posix()).replace("VCO_PANEL_PORT_PATH", (ROOT / PANEL).as_posix()),
            encoding="utf8", newline="\n")
        profile_exe = AREA / "profile.exe"
        report["profile_build"] = build(profile_exe, build_source(kernel, instrumented=True), profile=True)
        assert process.returncode == 0, process.stderr.decode(errors="replace")
        state = AREA / "history.bin"
        for label, (_, grid) in reference.items():
            start, stop = (15, 20) if label == "negative" else (76, 81)
            state.write_bytes(grid[start][3].tobytes() + struct.pack("<d", grid[start][0]))
            item = run([profile_exe, "profile", state, label])
            report["profiles"][label] = item
            assert process.returncode == 0, process.stderr.decode(errors="replace")
            item["metrics"] = profile_metrics(process.stdout, grid[stop], stop)
            print("VOICE_PROFILE", label, item["metrics"], flush=True)
        exe = AREA / "cost.exe"
        report["build"] = build(exe, build_source(kernel))
        assert process.returncode == 0, process.stderr.decode(errors="replace")
        for label, (_, grid) in reference.items():
            state.write_bytes(history[label] + struct.pack("<d", grid[0][0]))
            item = run([exe, "adaptive", state, label])
            report["adaptive"][label] = item
            if process.returncode == 0:
                item["metrics"] = parse_adaptive(process.stdout, grid)
            if not item.get("metrics", {}).get("passed"):
                item["unchanged_replay"] = run(command)
            print("VOICE_ADAPTIVE", label, item.get("metrics", process.stderr.decode(errors="replace")), flush=True)
        report["reserves_passed"] = all(item.get("metrics", {}).get("passed") for item in report["adaptive"].values())
        if report["reserves_passed"]:
            for label, (metrics, grid) in reference.items():
                state.write_bytes(history[label])
                item = run([exe, "branch", state, label, metrics["subdivisions"]])
                report["fixed"][label] = item
                assert process.returncode == 0, process.stderr.decode(errors="replace")
                item["metrics"], fresh = parse_branch(process.stdout)
                assert all(x[:3] == y[:3] and x[3].tobytes() == y[3].tobytes() for x, y in zip(grid, fresh))
                adaptive = report["adaptive"][label]["metrics"]["duration_s"]
                item["speedup"] = item["metrics"]["duration_s"] / adaptive
                print("VOICE_FIXED", label, item["metrics"]["duration_s"], item["speedup"], flush=True)
        report["passed"] = True
    except Exception:
        report["failure"] = traceback.format_exc()
        if command:
            if process is not None:
                report["failed"] = dict(exit_code=process.returncode, stdout=packed(process.stdout), stderr=packed(process.stderr))
            try:
                report["unchanged_replay"] = run(command)
            except subprocess.TimeoutExpired:
                report["unchanged_replay"] = dict(timeout=True)
    finally:
        write(destination, report)
        for path in AREA.iterdir():
            assert path.is_file() and path.resolve().parent == AREA.resolve()
            path.unlink()
        sources.unchanged()
        report["temporary_area_empty"] = not list(AREA.iterdir())
        write(destination, report)
    print("VOICE_COST", report["passed"], report.get("reserves_passed"), report.get("failure", ""), flush=True)
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
