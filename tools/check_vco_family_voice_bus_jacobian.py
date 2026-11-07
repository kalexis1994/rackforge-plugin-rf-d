"""Compare the direct stage stamp and bounded substitutions against the current bank."""
import argparse
import os
import struct
import subprocess
import traceback
from pathlib import Path

from affine_evidence import Sources
from audit_vco_family_voice_bus_hot import OUT as PRIOR_QA
from check_hybrid_voice import packed, unpack
from check_recovery_cost import digest
from check_vco_family_voice_bus_cost import profile_metrics, references
from check_vco_family_voice_bus_hot import (
    ORDERS, REPORT as HOT_REPORT, SOURCE_NAMES as HOT_SOURCES, VARIANTS, build_source,
    profile_summary, reserve, text,
)
from check_vco_family_voice_bus_model import AREA, materialize, read_oracle
from check_vco_phase import COMPILER, LIB
from prepare_dual_chain import ROOT, sha, write
from prepare_hybrid_stamp import once
from prepare_vco_family_voice_bus import TABLE
from validate_vco_family_voice_bus import KERNEL, MODEL, PANEL, PREFIX, histories, read
import vco_family_voice_bus_jacobian_paths as paths

OWN = "tools/check_vco_family_voice_bus_jacobian.py"
TRANSFORM = "tools/vco_family_voice_bus_jacobian_paths.py"
AUDIT = "tools/vco_family_voice_bus_jacobian_audit.rs"
DOC = "docs/VCO_FAMILIA_BUS_VOZ_JACOBIANO_PROTOCOLO.md"
CIRCUIT = "crates/rf-d-circuit/src/"
CHAIN = CIRCUIT + "prepared_chain_charge.rs"
AUDIO = CIRCUIT + "prepared_audio_stamp.rs"
REPORT = PREFIX + "_jacobian"
CONTROL = HOT_REPORT + "02.json"
SOURCES = (*HOT_SOURCES, OWN, TRANSFORM, AUDIT, DOC, CHAIN, AUDIO)


def generate(kernel, variant, profile, linear):
    probe = build_source(kernel, "combined", profile, "thin")
    if variant in ("assembly", "combined"):
        audio = AREA / "direct-audio.rs"
        audio.write_text(paths.audio(text(AUDIO)), encoding="utf8", newline="\n")
        chain = AREA / "direct-chain.rs"
        chain.write_text(once(paths.chain(text(CHAIN)), 'path="prepared_audio_stamp.rs"',
                              f'path="{audio.as_posix()}"'), encoding="utf8", newline="\n")
        graph = AREA / "hot-graph.rs"
        graph.write_text(once(graph.read_text(encoding="utf8"), (ROOT / CHAIN).as_posix(), chain.as_posix()),
                         encoding="utf8", newline="\n")
    if variant in ("linear", "combined"):
        solver = AREA / "hot-solver.rs"
        transform = paths.triangular if linear == "bounded" else paths.zero_cross
        solver.write_text(transform(solver.read_text(encoding="utf8")), encoding="utf8", newline="\n")
    if not profile:
        source = probe.read_text(encoding="utf8")
        source = once(source, "    hot_audit::compare(model, p, old, phase, controls, h, q)?;",
                      "    hot_audit::compare(model, p, old, phase, controls, h, q)?;\n"
                      "    jacobian_audit::contact(old, controls, h, q)?;")
        source = once(source, '        Some("ports") => ports(),', '''        Some("ports") => ports(),
        Some("linear-guard") => { jacobian_audit::linear(); Ok(()) },''')
        source += f'\n#[path = "{(ROOT / AUDIT).as_posix()}"] mod jacobian_audit;\n'
        probe.write_text(source, encoding="utf8", newline="\n")
    return probe


def verify(raw, original, prior):
    lines = raw.splitlines()
    contacts = [line for line in lines if line.startswith(b"CONTACT,")]
    rest = b"\n".join(line for line in lines if not line.startswith(b"CONTACT,"))
    metrics = reserve(rest, original, prior)
    assert contacts == [b"CONTACT,6"] * len(metrics["local"])
    return dict(**metrics, contact_stages=6 * len(contacts))


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--linear", choices=("bounded", "zero-cross"), default="bounded")
    linear = cli.parse_args().linear
    assert not list(AREA.iterdir())
    sequence = 1
    while (ROOT / f"{REPORT}{sequence:02}.json").exists():
        sequence += 1
    output = ROOT / f"{REPORT}{sequence:02}.json"
    sources = Sources(SOURCES)
    report = dict(passed=False, linear=linear, **sources.fields(), compiler_sha256=sha(Path(COMPILER)),
                  library_sha256=sha(LIB), prior_sha256=sha(ROOT / PRIOR_QA), control_sha256=sha(ROOT / CONTROL),
                  builds={}, guards={}, reserves={}, profiles=[])
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
            *(["--cfg", "cost_profile"] if profile else []), generate(kernel, variant, profile, linear),
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
        kernel = AREA / "family-kernel.rs"
        kernel.write_text(text(KERNEL).replace("H128_VOICE_TABLE_PATH", table_path.as_posix()).replace(
            "VCO_PANEL_PORT_PATH", (ROOT / PANEL).as_posix()), encoding="utf8", newline="\n")
        state = AREA / "jacobian-history.bin"
        binaries = {variant: build(variant, False) for variant in (("control", "combined") if linear == "zero-cross" else ("combined", "control"))}
        for variant, exe in binaries.items():
            report["guards"][variant] = run([exe, "linear-guard"])
            assert process.returncode == 0, process.stderr.decode(errors="replace")
            assert process.stdout.strip() == b"LINEAR_GUARD,4,2"
            report["reserves"][variant] = {}
            for label, original in reference.items():
                state.write_bytes(history[label])
                item = run([exe, "branch", state, label, original[0]["subdivisions"]])
                report["reserves"][variant][label] = item
                assert process.returncode == 0, process.stderr.decode(errors="replace")
                item["metrics"] = verify(process.stdout, original, prior["loaded_branches"][label]["combined"])
                print("JACOBIAN_RESERVE", variant, label, item["metrics"]["duration_s"], flush=True)
        report["ratios"] = {}
        for label in reference:
            a = report["reserves"]["control"][label]["metrics"]
            b = report["reserves"]["combined"][label]["metrics"]
            assert {k: v for k, v in a.items() if k != "duration_s"} == {k: v for k, v in b.items() if k != "duration_s"}
            report["ratios"][label] = b["duration_s"] / a["duration_s"]
        print("JACOBIAN_RATIOS", report["ratios"], flush=True)
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
        write(output, report)
        for path in AREA.iterdir():
            assert path.is_file() and path.resolve().parent == AREA.resolve()
            path.unlink()
        sources.unchanged()
        report["temporary_area_empty"] = not list(AREA.iterdir())
        write(output, report)
    print("JACOBIAN_COST", report["passed"], report.get("median_profile_ns"), report.get("failure"), flush=True)
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
