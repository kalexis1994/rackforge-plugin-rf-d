"""Measure independent loaded-voice stage and Schur changes under identical reserves."""
import argparse
import os
import statistics
import struct
import subprocess
import traceback
from pathlib import Path

from affine_evidence import Sources
from audit_vco_family_voice_bus_reuse import OUT as PRIOR_QA, RUN as PRIOR_RUN
from check_hybrid_voice import packed, unpack
from check_recovery_cost import digest
from check_vco_family_voice_bus_cost import ADAPTIVE, COST, OWN as PROFILE, profile_metrics, profile_source, references
from check_vco_family_voice_bus_model import AREA, materialize, read_oracle
from check_vco_family_voice_bus_reuse import OWN as REUSE, add_event_audit, compare, reuse
from check_vco_phase import COMPILER, LIB
from prepare_dual_chain import ROOT, sha, write
from prepare_hybrid_stamp import once
from prepare_vco_family_voice_bus import TABLE
from validate_vco_family_voice_bus import COUPLED, KERNEL, MODEL, PANEL, PATHS, PREFIX, PROBE, histories, parse_branch, read
import vco_family_voice_bus_hot_paths as paths

OWN = "tools/check_vco_family_voice_bus_hot.py"
TRANSFORM = "tools/vco_family_voice_bus_hot_paths.py"
AUDIT = "tools/vco_family_voice_bus_hot_audit.rs"
DOC = "docs/VCO_FAMILIA_BUS_VOZ_ARMADO_PROTOCOLO.md"
REPORT = PREFIX + "_hot"
SOURCE_NAMES = (OWN, TRANSFORM, AUDIT, DOC, REUSE, PROFILE, ADAPTIVE, COST, KERNEL, PANEL, PROBE, *PATHS.values())
VARIANTS = ("control", "assembly", "linear", "combined")
ORDERS = (VARIANTS, tuple(reversed(VARIANTS)), ("assembly", "combined", "control", "linear"))


def text(name):
    return (ROOT / name).read_text(encoding="utf8")


def build_source(kernel, variant, profiled, experiment):
    selected = dict(PATHS)

    def emit(slot, content, original):
        path = AREA / f"hot-{slot}.rs"
        if original:
            # Generated siblings still include the original device modules.
            parent = (ROOT / original).parent
            for dependency in ("prepared_chain_charge.rs", "prepared_contour_residual.rs"):
                content = content.replace(f'#[path="{dependency}"]', f'#[path="{(parent / dependency).as_posix()}"]')
        path.write_text(content, encoding="utf8", newline="\n")
        return path.relative_to(ROOT).as_posix()

    coupled = reuse(text(COUPLED))
    assembly = variant in ("assembly", "combined")
    linear = variant in ("linear", "combined")
    if experiment == "thin" and assembly:
        coupled = paths.thin_voice(coupled, profiled)
    selected["COUPLED_PATH"] = emit("voice", profile_source(coupled) if profiled else coupled, None)
    if assembly:
        graph = PATHS["GRAPH_PATH"]
        if experiment == "thin":
            selected["GRAPH_PATH"] = emit("graph", paths.thin_graph(text(graph)), graph)
        else:
            selected["GRAPH_PATH"] = emit("graph", paths.graph(text(graph)), graph)
            slot = "INCIDENCE_PATH"
            selected[slot] = emit("incidence", paths.matrix(text(PATHS[slot])), None)
    if linear:
        factor = paths.contiguous_solver if experiment == "thin" else paths.solver
        selected["SOLVER_PATH"] = emit("solver", factor(text(PATHS["SOLVER_PATH"])), None)

    probe = add_event_audit(text(PROBE)).replace("FAMILY_KERNEL_PATH", kernel.as_posix())
    for slot, name in selected.items():
        probe = probe.replace(slot, (ROOT / name).as_posix())
    if profiled:
        probe = once(probe, '        Some("ports") => ports(),', '''        Some("ports") => ports(),
        Some("profile") if args.len() == 4 => cost::profile(&args[2], &args[3]),''')
        probe += f'\n#[path = "{(ROOT / ADAPTIVE).as_posix()}"] mod adaptive;\n'
        probe += f'#[path = "{(ROOT / COST).as_posix()}"] mod cost;\n'
    else:
        original = once(text(COUPLED), "use crate::{graph, solver};",
                        "use crate::{original_graph as graph, original_solver as solver};")
        modules = dict(original_graph=PATHS["GRAPH_PATH"], original_solver=PATHS["SOLVER_PATH"],
                       original_voice=emit("original-voice", original, None), hot_audit=AUDIT)
        for module, name in modules.items():
            probe += f'\n#[path = "{(ROOT / name).as_posix()}"] mod {module};'
        probe = once(probe, "    let original = dense::Parameters::new(parameters())",
                     "    hot_audit::compare(model, p, old, phase, controls, h, q)?;\n"
                     "    let original = dense::Parameters::new(parameters())")
    return ROOT / emit("probe", probe, None)


def reserve(raw, original, prior):
    lines = raw.splitlines()
    grid_bytes = b"\n".join(line for line in lines if not line.startswith(b"HOT_AUDIT,"))
    metrics = compare(grid_bytes, original)
    assert metrics["latch_events"] == prior["latch_events"]
    _, grid = parse_branch(b"\n".join(line for line in grid_bytes.splitlines() if not line.startswith(b"LATCH,")))
    assert all(struct.pack("<ddd", *a[:3]) == struct.pack("<ddd", *b[:3])
               for a, b in zip(grid, original[1]))
    audits = []
    for line in lines:
        if line.startswith(b"HOT_AUDIT,"):
            _, entries, solves, error = line.split(b",")
            audits.append(dict(entries=int(entries), solves=int(solves), backward=float(error)))
    assert len(audits) == 7 + len(prior["latch_events"])
    assert all(audit["entries"] > 0 and audit["solves"] == 3 and audit["backward"] <= 1e-11 for audit in audits)
    return dict(**metrics, local=audits)


def profile_summary(profiles):
    result = {}
    for variant in VARIANTS:
        result[variant] = {}
        for label in ("negative", "positive"):
            runs = [item["runs"][variant][label]["metrics"] for item in profiles]
            sections = ("full_stage", "residual_stage", "linear_solve")
            for section in sections:
                assert len({item[section]["calls"] for item in runs}) == 1
            result[variant][label] = dict(
                wall_ns=statistics.median(item["wall_ns"] for item in runs),
                **{section: statistics.median(item[section]["ns"] for item in runs) for section in sections},
            )
    return result


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--experiment", choices=("permutation", "thin"), default="permutation")
    experiment = cli.parse_args().experiment
    assert not list(AREA.iterdir())
    seq = 1
    while (ROOT / f"{REPORT}{seq:02}.json").exists():
        seq += 1
    destination = ROOT / f"{REPORT}{seq:02}.json"
    sources = Sources(SOURCE_NAMES)
    report = dict(passed=False, experiment=experiment, **sources.fields(), compiler_sha256=sha(Path(COMPILER)), library_sha256=sha(LIB),
                  prior_sha256=sha(ROOT / PRIOR_QA), control_sha256=sha(ROOT / PRIOR_RUN), builds={}, reserves={}, profiles=[])
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

    def build(variant, profiled):
        name = variant + ("-profile" if profiled else "")
        exe = AREA / f"{name}.exe"
        item = run([COMPILER, "--edition=2021", "-C", "opt-level=3", "-C", "target-feature=+fma",
                    "-C", "link-arg=-Wl,--stack,33554432", "-A", "dead_code",
                    *(["--cfg", "cost_profile"] if profiled else []), build_source(kernel, variant, profiled, experiment),
                    "--extern", f"rf_d_circuit={LIB}", "-o", exe])
        report["builds"][name] = item
        assert process.returncode == 0, process.stderr.decode(errors="replace")
        return exe

    try:
        report["fma_check"] = run(["pwsh", "-NoProfile", "-Command", "[System.Runtime.Intrinsics.X86.Fma]::IsSupported"])
        assert process.returncode == 0 and process.stdout.strip() == b"True"
        reference, report["reference_inputs"] = references()
        history, report["private_inputs"] = histories()
        prior = read(PRIOR_QA)
        assert prior["passed"] and prior["fixed_reserves_identical"]
        table, _, _, _, _, _ = materialize(read_oracle())
        report["table_sha256"] = digest(table)
        assert report["table_sha256"] == read(MODEL)["table_sha256"]
        table_path = AREA / TABLE
        table_path.write_bytes(table)
        kernel = AREA / "family-kernel.rs"
        kernel.write_text(text(KERNEL).replace("H128_VOICE_TABLE_PATH", table_path.as_posix()).replace(
            "VCO_PANEL_PORT_PATH", (ROOT / PANEL).as_posix()), encoding="utf8", newline="\n")
        state = AREA / "hot-history.bin"
        binaries = {variant: build(variant, False) for variant in (("combined", "control") if experiment == "thin" else ("control", "combined"))}
        for variant, exe in binaries.items():
            report["reserves"][variant] = {}
            for label, original in reference.items():
                state.write_bytes(history[label])
                item = run([exe, "branch", state, label, original[0]["subdivisions"]])
                report["reserves"][variant][label] = item
                assert process.returncode == 0, process.stderr.decode(errors="replace")
                item["metrics"] = reserve(process.stdout, original, prior["loaded_branches"][label]["reuse_fma"])
                print("VOICE_HOT_RESERVE", variant, label, item["metrics"]["duration_s"], flush=True)
        control = report["reserves"]["control"]
        combined = report["reserves"]["combined"]
        report["ratios"] = {}
        for label in reference:
            a, b = control[label]["metrics"], combined[label]["metrics"]
            assert {k: v for k, v in a.items() if k != "duration_s"} == {k: v for k, v in b.items() if k != "duration_s"}
            report["ratios"][label] = b["duration_s"] / a["duration_s"]

        binaries = {variant: build(variant, True) for variant in VARIANTS}
        for order in ORDERS:
            batch = dict(order=order, runs={})
            report["profiles"].append(batch)
            for variant in order:
                batch["runs"][variant] = {}
                for label, (_, grid) in reference.items():
                    start, end = (15, 20) if label == "negative" else (76, 81)
                    state.write_bytes(grid[start][3].tobytes() + struct.pack("<d", grid[start][0]))
                    item = run([binaries[variant], "profile", state, label])
                    batch["runs"][variant][label] = item
                    assert process.returncode == 0, process.stderr.decode(errors="replace")
                    item["metrics"] = profile_metrics(process.stdout, grid[end], end)
        report["median_profile_ns"] = profile_summary(report["profiles"])
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
        write(destination, report)
        for path in AREA.iterdir():
            assert path.is_file() and path.resolve().parent == AREA.resolve()
            path.unlink()
        sources.unchanged()
        report["temporary_area_empty"] = not list(AREA.iterdir())
        write(destination, report)
    print("VOICE_HOT", report["passed"], report.get("ratios"), report.get("median_profile_ns"), report.get("failure"), flush=True)
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
