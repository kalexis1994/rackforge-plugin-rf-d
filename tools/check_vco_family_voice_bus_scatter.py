"""Audit and time the single-traversal assembly of both loaded Radau rows."""
import argparse
import os
import statistics
import struct
import subprocess
import traceback
from pathlib import Path

from affine_evidence import Sources
from audit_vco_family_voice_bus_latch_lu import OUT as PRIOR_QA
from check_hybrid_voice import packed
from check_recovery_cost import digest
from check_vco_family_voice_bus_cost import profile_metrics, references
from check_vco_family_voice_bus_hot import text
from check_vco_family_voice_bus_latch_lu import (
    CPU, GUARDS as PREVIOUS_GUARDS, REPORT as RELEASE, SOURCES as RELEASE_SOURCES, WINDOWS,
    emit, generate as base, pin, verify_run,
)
from check_vco_family_voice_bus_model import AREA, materialize, read_oracle
from check_vco_phase import COMPILER, LIB
from prepare_dual_chain import ROOT, sha, write
from prepare_hybrid_stamp import once
from prepare_vco_family_voice_bus import TABLE
from validate_vco_family_voice_bus import KERNEL, MODEL, PANEL, PATHS, PREFIX, histories, read
import vco_family_voice_bus_scatter_paths as paths

OWN = "tools/check_vco_family_voice_bus_scatter.py"
TRANSFORM = "tools/vco_family_voice_bus_scatter_paths.py"
AUDIT = "tools/vco_family_voice_bus_scatter_audit.rs"
BITS = "tools/vco_family_voice_bus_scatter_bits.rs"
DOC = "docs/VCO_FAMILIA_BUS_VOZ_ENSAMBLADO_PROTOCOLO.md"
REPORT = PREFIX + "_scatter"
CONTROL = RELEASE + "02.json"
SOURCES = (*RELEASE_SOURCES, OWN, TRANSFORM, AUDIT, BITS, DOC)
VARIANTS = ("control", "candidate")
ORDERS = (VARIANTS, tuple(reversed(VARIANTS)), VARIANTS)
GUARDS = PREVIOUS_GUARDS + b"\nSCATTER_GUARD,3,2,1"
SECTIONS = ("full_stage", "residual_stage", "linear_solve", "assembly", "factor")


def generate(kernel, variant, profile, layout):
    probe = base(kernel, "combined", profile, True)
    solver = "hot-solver.rs"
    source = (AREA / solver).read_text(encoding="utf8")
    if variant == "candidate" and layout == "fused":
        source = paths.fused(source)
    emit(solver, paths.profile_solver(source) if profile else source)
    probe_text = probe.read_text(encoding="utf8")
    if layout == "bits":
        original = PATHS["INCIDENCE_PATH"]
        incidence = emit("bit-incidence.rs", paths.bit_rows(text(original)))
        probe_text = once(probe_text, (ROOT / original).as_posix(), incidence.as_posix())
        if variant == "candidate":
            graph = "hot-graph.rs"
            emit(graph, paths.bit_graph((AREA / graph).read_text(encoding="utf8")))
        if not profile:
            probe_text = once(probe_text, "release_audit::active(); Ok(())",
                              "release_audit::active(); bit_audit::guard(); Ok(())")
            probe_text += f'\n#[path = "{(ROOT / BITS).as_posix()}"] mod bit_audit;\n'
    emit(probe.name, probe_text)
    if profile:
        profile_name = "release-profile.rs"
        emit(profile_name, paths.profile_cost((AREA / profile_name).read_text(encoding="utf8")))
        return probe
    source = once(probe.read_text(encoding="utf8"), "    jacobian_audit::contact(old, controls, h, q)?;",
                  "    jacobian_audit::contact(old, controls, h, q)?;\n    scatter_audit::accepted(q);")
    source = once(source, "release_audit::active();", "release_audit::active(); scatter_audit::guards();")
    source += f'\n#[path = "{(ROOT / AUDIT).as_posix()}"] mod scatter_audit;\n'
    return emit(probe.name, source)


def reserve(raw, reference, prior):
    lines = raw.splitlines()
    audits = [line for line in lines if line.startswith(b"MATRIX,")]
    core = b"\n".join(line for line in lines if not line.startswith(b"MATRIX,"))
    metrics = verify_run(core, reference, prior, True)
    assert audits == [b"MATRIX,55696"] * len(metrics["local"])
    return dict(**metrics, matrix_entries=55696 * len(audits))


def profile(raw, grid, end):
    lines = raw.splitlines()
    fields = lines[-1].split(b",")
    assert len(fields) == 11 and fields[0] == b"PROFILE"
    metrics = profile_metrics(b"\n".join([*lines[:-1], b",".join(fields[:7])]), grid[end], end)
    for index, section in enumerate(SECTIONS[3:]):
        ns, calls = map(int, fields[7 + 2 * index:9 + 2 * index])
        assert ns > 0 and calls == metrics["linear_solve"]["calls"]
        metrics[section] = dict(ns=ns, calls=calls)
    assert metrics["assembly"]["ns"] + metrics["factor"]["ns"] <= metrics["linear_solve"]["ns"]
    return metrics


def medians(profiles):
    values = {}
    for window in WINDOWS:
        for section in SECTIONS:
            assert len({batch["runs"][v][window]["metrics"][section]["calls"]
                        for batch in profiles for v in VARIANTS}) == 1
        values[window] = {}
        for variant in VARIANTS:
            runs = [batch["runs"][variant][window]["metrics"] for batch in profiles]
            values[window][variant] = {section: statistics.median(run[section]["ns"] for run in runs)
                                       for section in SECTIONS}
    return values


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--layout", choices=("fused", "bits"), default="fused")
    layout = cli.parse_args().layout
    expected_guards = GUARDS + b"\nBITROW_GUARD,4096,1,1" if layout == "bits" else GUARDS
    assert not list(AREA.iterdir())
    sequence = 1
    while (ROOT / f"{REPORT}{sequence:02}.json").exists():
        sequence += 1
    output = ROOT / f"{REPORT}{sequence:02}.json"
    sources = Sources(SOURCES)
    report = dict(passed=False, layout=layout, **sources.fields(), compiler_sha256=sha(Path(COMPILER)),
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

    def build(variant, instrumented):
        name = variant + ("-profile" if instrumented else "")
        exe = AREA / f"{name}.exe"
        report["builds"][name] = run([
            COMPILER, "--edition=2021", "-C", "opt-level=3", "-C", "target-feature=+fma",
            "-C", "link-arg=-Wl,--stack,33554432", "-A", "dead_code", "--cfg", "laboratory",
            *(["--cfg", "cost_profile"] if instrumented else []), generate(kernel, variant, instrumented, layout),
            "--extern", f"rf_d_circuit={LIB}", "-o", exe,
        ])
        assert process.returncode == 0, process.stderr.decode(errors="replace")
        report["affinities"][name] = run([exe, "affinity"])
        assert process.returncode == 0 and process.stdout.strip() == f"AFFINITY,{1 << CPU},{CPU}".encode()
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
        report["affinity"] = pin()
        state = AREA / "scatter-history.bin"
        order = reversed(VARIANTS) if layout == "bits" else VARIANTS
        binaries = {variant: build(variant, False) for variant in order}
        for variant, exe in binaries.items():
            report["guards"][variant] = run([exe, "linear-guard"])
            assert process.returncode == 0, process.stderr.decode(errors="replace")
            assert b"\n".join(process.stdout.splitlines()) == expected_guards
            report["reserves"][variant] = {}
            for label in ("positive", "negative"):
                original = reference[label]
                state.write_bytes(history[label])
                item = run([exe, "branch", state, label, original[0]["subdivisions"]])
                report["reserves"][variant][label] = item
                assert process.returncode == 0, process.stderr.decode(errors="replace")
                item["metrics"] = reserve(process.stdout, original, prior["loaded_branches"][label]["combined"])
                print("SCATTER_RESERVE", variant, label, item["metrics"]["duration_s"], flush=True)
        report["ratios"] = {}
        for label in reference:
            a = report["reserves"]["control"][label]["metrics"]
            b = report["reserves"]["candidate"][label]["metrics"]
            omit = {"duration_s", "thread_cpu_s"}
            assert {k: v for k, v in a.items() if k not in omit} == {k: v for k, v in b.items() if k not in omit}
            report["ratios"][label] = {key: b[key] / a[key] for key in sorted(omit)}
        print("SCATTER_RATIOS", report["ratios"], flush=True)
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
                    item["metrics"] = profile(process.stdout, grid, end)
        report["median_profile_ns"] = medians(report["profiles"])
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
    print("SCATTER_COST", report["passed"], report.get("median_profile_ns"), report.get("failure"), flush=True)
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
