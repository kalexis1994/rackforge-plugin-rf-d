"""Compare latch endpoint reuse and active LU rows around the loaded release."""
import argparse
import ctypes
from ctypes import wintypes
import os
import statistics
import struct
import subprocess
import traceback
from pathlib import Path

from affine_evidence import Sources
from audit_vco_family_voice_bus_jacobian import OUT as PRIOR_QA
from check_hybrid_voice import packed, unpack
from check_recovery_cost import digest
from check_vco_family_voice_bus_cost import COST, profile_metrics, references
from check_vco_family_voice_bus_hot import ORDERS, VARIANTS, text
from check_vco_family_voice_bus_jacobian import (
    CIRCUIT, REPORT as JACOBIAN, SOURCES as JACOBIAN_SOURCES, generate as base, verify,
)
from check_vco_family_voice_bus_model import AREA, materialize, read_oracle
from check_vco_phase import COMPILER, LIB
from prepare_dual_chain import ROOT, sha, write
from prepare_hybrid_stamp import once
from prepare_vco_family_voice_bus import TABLE
from validate_vco_family_voice_bus import KERNEL, MODEL, PANEL, PREFIX, histories, read
import vco_family_voice_bus_latch_lu_paths as paths

OWN = "tools/check_vco_family_voice_bus_latch_lu.py"
TRANSFORM = "tools/vco_family_voice_bus_latch_lu_paths.py"
AUDIT = "tools/vco_family_voice_bus_latch_lu_audit.rs"
DOC = "docs/VCO_FAMILIA_BUS_VOZ_LATCH_LU_PROTOCOLO.md"
TIMING = "tools/vco_family_voice_bus_latch_lu_timing.rs"
CPU = 9
CONTOUR = CIRCUIT + "prepared_contour_residual.rs"
LATCH = CIRCUIT + "conditioned_voice_latch.rs"
JUNCTION = CIRCUIT + "junction_charge.rs"
REPORT = PREFIX + "_latch_lu"
CONTROL = JACOBIAN + "02.json"
SOURCES = (*JACOBIAN_SOURCES, OWN, TRANSFORM, AUDIT, DOC, TIMING, CONTOUR, LATCH, JUNCTION)
WINDOWS = dict(negative=("negative", 15, 20), before=("positive", 52, 57),
               positive=("positive", 76, 81), after=("positive", 96, 101))
GUARDS = b"LINEAR_GUARD,4,2\nJUNCTION_GUARD,162,6\nACTIVE_GUARD,4"


def emit(name, source):
    path = AREA / name
    path.write_text(source, encoding="utf8", newline="\n")
    return path


def generate(kernel, variant, profile, confirm):
    probe = base(kernel, "combined", profile, "zero-cross")
    stamp = variant in ("assembly", "combined")
    latch = None
    if stamp or not profile:
        law = emit("verified-depletion.rs", paths.depletion(text(JUNCTION)))
        latch = emit("verified-latch.rs", paths.latch(text(LATCH), law.as_posix()))
    if stamp:
        contour = once(text(CONTOUR), '"conditioned_voice_latch.rs"', f'"{latch.as_posix()}"')
        for name in ("prepared_filter_residual.rs", "prepared_volume_residual.rs"):
            contour = once(contour, f'"{name}"', f'"{(ROOT / (CIRCUIT + name)).as_posix()}"')
        contour = emit("verified-contour.rs", contour)
        graph = "hot-graph.rs"
        emit(graph, once((AREA / graph).read_text(encoding="utf8"), (ROOT / CONTOUR).as_posix(), contour.as_posix()))
    if variant in ("linear", "combined"):
        solver = "hot-solver.rs"
        emit(solver, paths.active_rows((AREA / solver).read_text(encoding="utf8")))
    source = probe.read_text(encoding="utf8")
    if profile:
        profile_path = emit("release-profile.rs", paths.profile_windows(text(COST)))
        source = once(source, (ROOT / COST).as_posix(), profile_path.as_posix())
    else:
        guard = emit("release-audit.rs", text(AUDIT).replace("OLD_LATCH_PATH", (ROOT / LATCH).as_posix())
                     .replace("NEW_LATCH_PATH", latch.as_posix()))
        source = once(source, "jacobian_audit::linear(); Ok(())",
                      "jacobian_audit::linear(); release_audit::junction(); release_audit::active(); Ok(())")
        source += f'\n#[path = "{guard.as_posix()}"] mod release_audit;\n'
    if confirm:
        source += f'\n#[path = "{(ROOT / TIMING).as_posix()}"] mod release_timing;\n'
        source = once(source, '        Some("ports") => ports(),', """        Some("ports") => ports(),
        Some("affinity") => Ok(release_timing::affinity()?),""")
        if not profile:
            source = once(source, "    let mut retries = 0;",
                          "    let thread_start = release_timing::thread_ns()?;\n    let mut retries = 0;")
            source = once(source, "    let [current, charge, c27, tangent, panel] = worst_audit;",
                          '    println!("THREAD_CPU_NS,{}", release_timing::thread_ns()? - thread_start);\n'
                          "    let [current, charge, c27, tangent, panel] = worst_audit;")
    return emit(probe.name, source)


def summary(profiles):
    sections = ("full_stage", "residual_stage", "linear_solve")
    medians = {variant: {} for variant in VARIANTS}
    for window in WINDOWS:
        for section in sections:
            assert len({batch["runs"][v][window]["metrics"][section]["calls"]
                        for batch in profiles for v in VARIANTS}) == 1
        for variant in VARIANTS:
            runs = [batch["runs"][variant][window]["metrics"] for batch in profiles]
            medians[variant][window] = dict(
                wall_ns=statistics.median(run["wall_ns"] for run in runs),
                **{section: statistics.median(run[section]["ns"] for run in runs) for section in sections},
            )
    return medians


def pin():
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    mask_ref = ctypes.POINTER(ctypes.c_size_t)
    kernel.GetProcessAffinityMask.argtypes = (wintypes.HANDLE, mask_ref, mask_ref)
    kernel.GetProcessAffinityMask.restype = wintypes.BOOL
    kernel.SetProcessAffinityMask.argtypes = (wintypes.HANDLE, ctypes.c_size_t)
    kernel.SetProcessAffinityMask.restype = wintypes.BOOL
    process = kernel.GetCurrentProcess()
    allowed, system = ctypes.c_size_t(), ctypes.c_size_t()
    if not kernel.GetProcessAffinityMask(process, ctypes.byref(allowed), ctypes.byref(system)):
        raise ctypes.WinError(ctypes.get_last_error())
    mask = 1 << CPU
    assert allowed.value & mask
    if not kernel.SetProcessAffinityMask(process, mask):
        raise ctypes.WinError(ctypes.get_last_error())
    return dict(cpu=CPU, mask=mask, original_mask=allowed.value)


def verify_run(raw, original, prior, confirm):
    if not confirm:
        return verify(raw, original, prior)
    lines = raw.splitlines()
    time, = [line for line in lines if line.startswith(b"THREAD_CPU_NS,")]
    elapsed = int(time.split(b",")[1]) / 1e9
    assert elapsed > 0.
    core = b"\n".join(line for line in lines if not line.startswith(b"THREAD_CPU_NS,"))
    return dict(**verify(core, original, prior), thread_cpu_s=elapsed)


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--confirm", action="store_true")
    confirm = cli.parse_args().confirm
    assert not list(AREA.iterdir())
    sequence = 1
    while (ROOT / f"{REPORT}{sequence:02}.json").exists():
        sequence += 1
    output = ROOT / f"{REPORT}{sequence:02}.json"
    sources = Sources(SOURCES)
    report = dict(passed=False, confirm=confirm, **sources.fields(), compiler_sha256=sha(Path(COMPILER)),
                  library_sha256=sha(LIB), prior_sha256=sha(ROOT / PRIOR_QA), control_sha256=sha(ROOT / CONTROL),
                  windows=WINDOWS, builds={}, guards={}, affinities={}, reserves={}, profiles=[])
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

    def build(variant, profile):
        name = variant + ("-profile" if profile else "")
        exe = AREA / f"{name}.exe"
        report["builds"][name] = run([
            COMPILER, "--edition=2021", "-C", "opt-level=3", "-C", "target-feature=+fma",
            "-C", "link-arg=-Wl,--stack,33554432", "-A", "dead_code",
            *(["--cfg", "cost_profile"] if profile else []), generate(kernel, variant, profile, confirm),
            "--extern", f"rf_d_circuit={LIB}", "-o", exe,
        ])
        assert process.returncode == 0, process.stderr.decode(errors="replace")
        return exe

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
        state = AREA / "release-history.bin"
        if confirm:
            report["affinity"] = pin()
        variants = ("control", "combined", "linear") if confirm else ("combined", "control")
        binaries = {variant: build(variant, False) for variant in variants}
        for variant, exe in binaries.items():
            if confirm:
                report["affinities"][variant] = run([exe, "affinity"])
                assert process.returncode == 0 and process.stdout.strip() == f"AFFINITY,{1 << CPU},{CPU}".encode()
            report["guards"][variant] = run([exe, "linear-guard"])
            assert process.returncode == 0, process.stderr.decode(errors="replace")
            assert b"\n".join(process.stdout.splitlines()) == GUARDS
            report["reserves"][variant] = {}
            for label in ("positive", "negative"):
                original = reference[label]
                state.write_bytes(history[label])
                item = run([exe, "branch", state, label, original[0]["subdivisions"]])
                report["reserves"][variant][label] = item
                assert process.returncode == 0, process.stderr.decode(errors="replace")
                item["metrics"] = verify_run(process.stdout, original, prior["loaded_branches"][label]["combined"], confirm)
                print("RELEASE_RESERVE", variant, label, item["metrics"]["duration_s"], flush=True)
        report["ratios"] = {}
        report["isolated_linear_ratios"] = {}
        report["thread_ratios"] = {}
        for label in reference:
            a = report["reserves"]["control"][label]["metrics"]
            for variant in variants:
                b = report["reserves"][variant][label]["metrics"]
                omit = {"duration_s", "thread_cpu_s"}
                assert {k: v for k, v in a.items() if k not in omit} == {k: v for k, v in b.items() if k not in omit}
                if variant == "combined":
                    report["ratios"][label] = b["duration_s"] / a["duration_s"]
                    if confirm:
                        report["thread_ratios"][label] = b["thread_cpu_s"] / a["thread_cpu_s"]
                if variant == "linear":
                    report["isolated_linear_ratios"][label] = b["duration_s"] / a["duration_s"]
        print("RELEASE_RATIOS", report["ratios"], flush=True)
        binaries = {variant: build(variant, True) for variant in VARIANTS}
        for order in ORDERS:
            batch = dict(order=order, runs={})
            report["profiles"].append(batch)
            for variant in order:
                batch["runs"][variant] = {}
                for window, (label, start, end) in WINDOWS.items():
                    _, grid = reference[label]
                    state.write_bytes(grid[start][3].tobytes() + struct.pack("<d", grid[start][0]))
                    item = run([binaries[variant], "profile", state, window])
                    batch["runs"][variant][window] = item
                    assert process.returncode == 0, process.stderr.decode(errors="replace")
                    item["metrics"] = profile_metrics(process.stdout, grid[end], end)
        report["median_profile_ns"] = summary(report["profiles"])
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
    print("RELEASE_COST", report["passed"], report.get("median_profile_ns"), report.get("failure"), flush=True)
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
