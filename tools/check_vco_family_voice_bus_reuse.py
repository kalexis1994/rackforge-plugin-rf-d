"""Evaluate fixed-step solver reuse and hardware FMA on the two loaded reserves."""
import os
import subprocess
import traceback
from pathlib import Path

from affine_evidence import Sources
from check_hybrid_voice import packed, unpack
from check_recovery_cost import digest
from check_vco_family_voice_bus_model import AREA, materialize, read_oracle
from check_vco_phase import COMPILER, LIB
from check_vco_family_voice_bus_cost import ADAPTIVE, BASE_QA, COST, DOC, OWN as PROFILE, references, switch_frames
from prepare_dual_chain import ROOT, sha, write
from prepare_hybrid_stamp import once
from prepare_vco_family_voice_bus import TABLE
from validate_vco_family_voice_bus import COUPLED, KERNEL, MODEL, PANEL, PATHS, PREFIX, PROBE, histories, parse_branch, read

OWN = "tools/check_vco_family_voice_bus_reuse.py"
TRIAL = PREFIX + "_cost01.json"
MEASUREMENT = PREFIX + "_reuse"
SOURCE_NAMES = (OWN, PROFILE, ADAPTIVE, COST, DOC, KERNEL, PANEL, PROBE, *PATHS.values())


def reuse(source):
    return once(source, """                    maximum(&r) <= 1e-12 && maximum(&direction(work, &check, r)?) < size""", """
                    let norm = maximum(&r);
                    if norm <= 1e-12 {
                        let trial_size = maximum(&direction(work, &check, r)?);
                        // The next iteration would evaluate this identical point again.
                        if trial_size < size && trial_size <= 2e-9 && iterations < budget {
                            return Ok(Accepted {
                                stages: check, delta: trial, residual_a: norm,
                                correction_v: trial_size, iterations: iterations + 1,
                            });
                        }
                        trial_size < size
                    } else {
                        false
                    }""")


def add_event_audit(source):
    source = once(source, "fn branch(path:", """fn collector_order(s: State) -> [bool; 2] {
    [value(s, 26) >= value(s, 28), value(s, 40) >= value(s, 42)]
}

fn branch(path:""")
    source = once(source, "                if sub == 0 && completed == 0 && [0, 15, 16, 48, 95, 96, 127].contains(&frame) {", """
                let before = collector_order(state);
                let after = collector_order(q.stages.chain[1].now);
                let switching = before != after;
                if switching {
                    for pair in 0..2 {
                        if before[pair] != after[pair] {
                            println!("LATCH,{pair},{tick},{},{},{}", tick + width, subdivisions, u8::from(after[pair]));
                        }
                    }
                }
                if switching || (sub == 0 && completed == 0 && [0, 15, 16, 48, 95, 96, 127].contains(&frame)) {""")
    return source


def source_for(kernel, candidate):
    path = AREA / "reuse-probe.rs"
    source = add_event_audit((ROOT / PROBE).read_text(encoding="utf8")).replace("FAMILY_KERNEL_PATH", kernel.as_posix())
    parts = dict(PATHS)
    if candidate:
        path_voice = AREA / "reuse-voice.rs"
        path_voice.write_text(reuse((ROOT / COUPLED).read_text(encoding="utf8")), encoding="utf8", newline="\n")
        parts["COUPLED_PATH"] = path_voice.relative_to(ROOT).as_posix()
    for slot, module in parts.items():
        source = source.replace(slot, (ROOT / module).as_posix())
    path.write_text(source, encoding="utf8", newline="\n")
    return path


def compare(raw, original):
    lines = raw.splitlines()
    measured, grid = parse_branch(b"\n".join(line for line in lines if not line.startswith(b"LATCH,")))
    ref, frozen = original
    assert len(grid) == len(frozen) == 129
    assert all(a[:3] == b[:3] and a[3].tobytes() == b[3].tobytes() for a, b in zip(grid, frozen))
    for key in ("subdivisions", "iterations", "residual_a", "correction_v", "bus_v", "final_j7_v",
                "rejected_substeps", "maximum_halvings"):
        assert measured[key] == ref[key], key
    events = [list(map(int, line.split(b",")[1:])) for line in lines if line.startswith(b"LATCH,")]
    switches = []
    for pair, start, end, count, direction in events:
        assert count == ref["subdivisions"] and 0 <= start < end <= 128 * count * 8
        switches.append((pair, (end + count * 8 - 1) // (count * 8), direction))
    assert switches == switch_frames(frozen)
    return dict(**measured, identical_grid=True, latch_events=events)


def main():
    assert not list(AREA.iterdir())
    seq = 1
    while (ROOT / f"{MEASUREMENT}{seq:02}.json").exists():
        seq += 1
    target = ROOT / f"{MEASUREMENT}{seq:02}.json"
    sources = Sources(SOURCE_NAMES)
    report = dict(passed=False, **sources.fields(), compiler_sha256=sha(Path(COMPILER)), library_sha256=sha(LIB),
                  prior_sha256=sha(ROOT / BASE_QA), adaptive_trial_sha256=sha(ROOT / TRIAL), builds={}, runs={})
    env = dict(os.environ, PATH="C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;" + os.environ["PATH"])
    command = []
    last = None

    def run(args):
        nonlocal command, last
        command = list(map(str, args))
        last = None
        last = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, timeout=180)
        return dict(command=command, exit_code=last.returncode, stdout=packed(last.stdout), stderr=packed(last.stderr))

    def compile_variant(variant, kernel):
        candidate = variant == "reuse_fma"
        exe = AREA / f"{variant}.exe"
        report["builds"][variant] = run([
            COMPILER, "--edition=2021", "-C", "opt-level=3", "-C", "link-arg=-Wl,--stack,33554432",
            "-A", "dead_code", *(["-C", "target-feature=+fma"] if candidate else []),
            source_for(kernel, candidate), "--extern", f"rf_d_circuit={LIB}", "-o", exe,
        ])
        assert last.returncode == 0, last.stderr.decode(errors="replace")
        return exe

    try:
        report["fma_check"] = run(["pwsh", "-NoProfile", "-Command", "[System.Runtime.Intrinsics.X86.Fma]::IsSupported"])
        assert last.returncode == 0 and last.stdout.strip() == b"True"
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
        state = AREA / "history.bin"
        for variant in ("reuse_fma", "fixed"):
            exe = compile_variant(variant, kernel)
            report["runs"][variant] = {}
            for label, original in reference.items():
                state.write_bytes(history[label])
                item = run([exe, "branch", state, label, original[0]["subdivisions"]])
                report["runs"][variant][label] = item
                assert last.returncode == 0, last.stderr.decode(errors="replace")
                item["metrics"] = compare(unpack(item["stdout"]), original)
                print("VOICE_FIXED", variant, label, item["metrics"], flush=True)
        report["speedup"] = {}
        for label in reference:
            fast = report["runs"]["reuse_fma"][label]["metrics"]
            control = report["runs"]["fixed"][label]["metrics"]
            assert fast["latch_events"] == control["latch_events"]
            report["speedup"][label] = control["duration_s"] / fast["duration_s"]
        report["passed"] = True
    except Exception:
        report["failure"] = traceback.format_exc()
        if last is not None:
            report["failed"] = dict(exit_code=last.returncode, stdout=packed(last.stdout), stderr=packed(last.stderr))
        if command:
            try:
                report["unchanged_replay"] = run(command)
            except subprocess.TimeoutExpired:
                report["unchanged_replay"] = dict(timeout=True)
    finally:
        write(target, report)
        for path in AREA.iterdir():
            assert path.is_file() and path.resolve().parent == AREA.resolve()
            path.unlink()
        sources.unchanged()
        report["temporary_area_empty"] = not list(AREA.iterdir())
        write(target, report)
    print("VOICE_REUSE", report["passed"], report.get("speedup", report.get("failure")), flush=True)
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
