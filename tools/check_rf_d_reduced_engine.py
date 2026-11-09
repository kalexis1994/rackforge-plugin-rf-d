"""Build and contrast the Rust audio block engine and its collector-driven clock."""
import argparse
import os
import subprocess
import traceback
from pathlib import Path

import numpy as np

from affine_evidence import Sources
from check_hybrid_voice import packed
from check_recovery_cost import digest
from check_rf_d_reduced_contour_ports import (
    CLOCK, LOCAL_PORTS, NODES, OUTPUT, SOURCES as PORT_SOURCES, Interior, build, compare_audio,
    endpoint_errors, endpoint_passed, history, matrix, stage_ids, unpack_stamp,
)
from check_vco_family_voice_bus_cost import references
from check_vco_family_voice_bus_hot import text
from check_vco_family_voice_bus_latch_lu import emit, pin
from check_vco_family_voice_bus_model import AREA, materialize, read_oracle
from check_vco_phase import COMPILER, LIB
from prepare_dual_chain import ROOT, sha, write
from prepare_hybrid_stamp import once
from prepare_vco_family_voice_bus import TABLE
from rf_d_reduced_contour_live import Junctions
from validate_vco_family_voice_bus import BUS, KERNEL, MODEL, N, PANEL, read

OWN = "tools/check_rf_d_reduced_engine.py"
DOC = "docs/VOZ_REDUCIDA_MOTOR_PROTOCOLO.md"
CONTOUR = "tools/rf_d_reduced_engine_contour.rs"
MODULES = dict(reduced_engine="tools/rf_d_reduced_engine.rs", reduced_audio="tools/rf_d_reduced_engine_audio.rs",
               reduced_lu="tools/rf_d_reduced_engine_lu.rs", reduced_probe="tools/rf_d_reduced_engine_probe.rs")
PRIOR = "evidence/rf_d_reduced_contour_ports11.json"
SOURCES = (*PORT_SOURCES, OWN, DOC, CONTOUR, *MODULES.values())
TICKS = 4096
BANKS = 8
DEADLINE_NS = 128 * 1_000_000_000 / (2 * 48_000)


def source(kernel):
    probe = build(kernel)
    graph = AREA / "hot-graph.rs"
    emit(graph.name, graph.read_text(encoding="utf8") + "\n" + text(CONTOUR))
    code = once(probe.read_text(encoding="utf8"), '        Some("ports") => ports(),', '''
        Some("ports") => ports(),
        Some("reduced-engine") if args.len() == 6 =>
            reduced_probe::run(&args[2], &args[3], args[4].parse()?, args[5].parse()?),''')
    for module, path in MODULES.items():
        code += f'\n#[path = "{(ROOT / path).as_posix()}"] mod {module};\n'
    return emit(probe.name, code)


def maps(stamp, panel, state, bank_count=BANKS):
    nodes, ports = NODES[1], LOCAL_PORTS[1]
    n = len(nodes)
    local_bus = int(np.flatnonzero(nodes == BUS)[0])
    bus_stages = stage_ids(np.array([local_bus]), n)
    terminals = np.r_[stage_ids(ports, n), bus_stages]
    anchor = state[:, nodes].sum(axis=0)
    f, g, m = (part.copy() for part in stamp)
    f[local_bus] -= panel[0]
    g[local_bus, local_bus] -= panel[1]
    for power in range(bank_count):
        h = (1 << power) / (48_000 * TICKS)
        audio = Interior(matrix((f, g, m), h, None), terminals)
        rhs = np.column_stack((history(m, h), -np.tile(f, 2)))
        part, i_history = audio.response(rhs)
        x_history = audio.reconstruct(part, np.zeros((len(terminals), n + 1)))
        x_port = audio.reconstruct(np.zeros((len(audio.inner), len(terminals))), np.eye(len(terminals)))
        model = Junctions(OUTPUT, audio, anchor)
        assert model.base.shape == (108,)
        for array in (model.base, model.model["iexp"], model.sense @ x_history, model.source_map,
                      model.p, i_history, audio.schur, model.return_map,
                      x_history[n:], x_port[n:], model.node_map[n:]):
            assert np.isfinite(array).all()
            yield np.asarray(array, dtype="<f8").tobytes()


def assess(raw, target, expected, size, bank_count=BANKS):
    grid, switches, blocks, profile = [], [], [], []
    for line in raw.decode().splitlines():
        tag, *fields = line.split(",")
        if tag == "GRID":
            frame, angle, r59, r60, *words = fields
            assert int(frame) == len(grid)
            state = np.asarray([int(word, 16) for word in words], "<u8").view("<f8").reshape(2, N)
            assert np.isfinite(state).all()
            grid.append((float(angle), float(r59), float(r60), state))
        elif tag == "SWITCH":
            switches.append(list(map(int, fields)))
        elif tag == "PROFILE":
            values = list(map(int, fields))
            assert len(values) in (10, 11, 12, 13) and values[0] in (0, 1, 2)
            profile.append(values)
        elif tag == "CLOCK":
            solves, comparisons, error_retries, event_retries, *extra = map(int, fields)
            reused, siblings, seed_retries = (extra + [0] * 3)[:3]
            assert blocks and "clock" not in blocks[-1]
            assert len(extra) <= 3 and solves >= sum(blocks[-1]["widths"])
            assert 0 <= siblings <= reused <= comparisons <= solves
            blocks[-1]["clock"] = dict(solves=solves, comparisons=comparisons,
                                      error_retries=error_retries, event_retries=event_retries, reused_halves=reused, reused_siblings=siblings, half_seed_retries=seed_retries)
        else:
            assert tag == "BLOCK"
            frames, ns, allocs, guard, retries, iterations = map(int, fields[:6])
            residual, correction = map(float, fields[6:8])
            widths = list(map(int, fields[8:]))
            assert frames == size and len(widths) == bank_count
            assert sum(n * (1 << k) for k, n in enumerate(widths)) == frames * TICKS
            assert 0 < ns and allocs == 0 and 0. <= residual <= 1e-12 and 0. <= correction <= 2e-9
            blocks.append(dict(frames=frames, elapsed_ns=ns, allocations=allocs, guard_retries=guard,
                               solver_retries=retries, iterations=iterations, widths=widths,
                               max_residual_a=residual, max_correction_v=correction))
    assert len(grid) == 129 and len(blocks) == 128 // size
    endpoints = []
    for i, (a, b) in enumerate(zip(grid, target[1], strict=True)):
        nodes = a[3].sum(axis=0)
        result = endpoint_errors(i, nodes, b)
        result["phase_error_cycles"] = abs((a[0] - b[0] + .5) % 1. - .5)
        assert max(abs(a[1] - b[1]), abs(a[2] - b[2])) <= 2e-9 + 2e-5 * max(abs(b[1]), abs(b[2]))
        endpoints.append(result)
    sound = compare_audio(endpoints, target)
    windows = []
    if profile:
        assert len(profile) == 3 * len(blocks)
        field_count, = {len(row) for row in profile}
        for region, label in enumerate(("before", "crossing", "after")):
            rows = np.asarray([row[1:] for row in profile if row[0] == region], dtype=np.int64)
            steps, fine, wall, nc, na, nd, tc, ta, td, *extra = map(int, rows.sum(axis=0))
            tangents = extra[0] if field_count >= 11 else None
            reused_audio = extra[1] if field_count >= 12 else None
            tangent_ns = extra[2] if field_count == 13 else None
            evaluations = na + (reused_audio or 0)
            assert 0 <= fine <= steps and tc + ta + td <= wall and nc >= evaluations
            assert 0 <= (reused_audio or 0) <= na
            assert 0 <= (tangent_ns or 0) <= ta
            assert 0 <= (tangents or 0) <= evaluations and nd <= evaluations + (tangents or 0)
            windows.append(dict(region=label, steps=steps, fine_steps=fine, wall_ns=wall,
                                calls=dict(contour=nc, audio=na, direction=nd, audio_tangents=tangents,
                                           reused_audio=reused_audio),
                                ns=dict(contour=tc, audio=ta, direction=td, audio_tangents=tangent_ns)))
        assert sum(row["steps"] for row in windows) == sum(sum(b["widths"]) for b in blocks)
    passed = (switches == expected and all(endpoint_passed(row) for row in endpoints)
              and max(row["phase_error_cycles"] for row in endpoints) <= 1e-7 and sound["passed"])
    return dict(passed=passed, switches=switches, expected_switches=expected, audio=sound, blocks=blocks, profile=windows,
                accepted_steps=sum(sum(b["widths"]) for b in blocks),
                maximum={k: max(row[k] for row in endpoints) for k in (
                    "nodal_gate_fraction", "max_nodal_error_v", "contour_return_gate_fraction",
                    "r59_error_a", "r60_error_a", "j7_error_v", "phase_error_cycles",
                )},
                native_deadline_passed=all(b["elapsed_ns"] <= DEADLINE_NS for b in blocks))


def electrical(raw):
    return [line for line in raw.splitlines() if line.startswith((b"GRID,", b"SWITCH,"))]


def clock_build(wide=False, adaptive=False, sample=False, curvature=False):
    bank_count = 13 if sample else 11 if wide or adaptive else BANKS
    flags = [flag for active, name in (
        (wide or adaptive, "wide_contour_clock"), (adaptive, "adaptive_contour_clock"),
        (sample, "sample_contour_clock"), (curvature, "wide_clock_curvature"),
    ) if active for flag in ("--cfg", name)]
    return bank_count, flags


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wide-clock", action="store_true", help="exercise the 1,024-tick ceiling in the native bank")
    parser.add_argument("--curvature", action="store_true", help="refine wide steps from contour stage curvature")
    parser.add_argument("--profile", action="store_true", help="measure native solve phases by window")
    parser.add_argument("--adaptive-clock", action="store_true", help="compare wide steps with two halves")
    parser.add_argument("--sample-clock", action="store_true", help="allow steps of one full sample in adaptive mode")
    options = parser.parse_args()
    if options.sample_clock and not options.adaptive_clock:
        parser.error("--sample-clock requires --adaptive-clock")
    if options.adaptive_clock and options.curvature:
        parser.error("--adaptive-clock and --curvature choose different clock guards")
    if options.curvature and not options.wide_clock:
        parser.error("--curvature requires --wide-clock")
    bank_count, clock_flags = clock_build(options.wide_clock, options.adaptive_clock,
                                          options.sample_clock, options.curvature)
    assert not list(AREA.iterdir())
    sequence = 1
    while (output := ROOT / f"evidence/rf_d_reduced_engine{sequence:02}.json").exists():
        sequence += 1
    sources = Sources(SOURCES)
    report = dict(passed=False, rackforge_measured=False, native_deadline_ns=DEADLINE_NS,
                  profiled=options.profile, clock_banks=bank_count, curvature_guard=options.curvature, adaptive_clock=options.adaptive_clock, **sources.fields(), compiler_sha256=sha(Path(COMPILER)), library_sha256=sha(LIB),
                  control_sha256=sha(ROOT / PRIOR), clock_sha256=sha(ROOT / CLOCK), trials={})
    env = dict(os.environ, PATH="C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;" + os.environ["PATH"])

    def run(args, binary=False):
        cmd = list(map(str, args))
        proc = subprocess.run(cmd, cwd=ROOT, env=env, capture_output=True, timeout=180)
        receipt = dict(command=cmd, exit_code=proc.returncode, stderr=packed(proc.stderr),
                       stdout=dict(sha256=digest(proc.stdout), bytes=len(proc.stdout)) if binary else packed(proc.stdout))
        return proc, receipt

    try:
        ref, report["reference_inputs"] = references()
        clock, previous = read(CLOCK), read(PRIOR)
        assert clock["passed"] and previous["continuous_128_passed"]
        plan = (("negative", 32), ("positive", 64))
        report["caps"] = {name: TICKS >> (bank_count - 1) if bank_count > BANKS else cap
                          for name, cap in plan}
        keys = [ref[name][1][0] for name, _ in plan]
        path = AREA / "reduced-anchors.bin"
        np.asarray([np.r_[key[3].ravel(), key[0], 0.] for key in keys], "<f8").tofile(path)
        report["anchor_sha256"] = sha(path)
        table, *_ = materialize(read_oracle())
        report["table_sha256"] = digest(table)
        assert report["table_sha256"] == read(MODEL)["table_sha256"]
        table_path = AREA / TABLE
        table_path.write_bytes(table)
        kernel = emit("family-kernel.rs", text(KERNEL).replace("H128_VOICE_TABLE_PATH", table_path.as_posix())
                      .replace("VCO_PANEL_PORT_PATH", (ROOT / PANEL).as_posix()))
        report["affinity"] = pin()
        exe = AREA / "reduced-engine.exe"
        proc, report["build"] = run([COMPILER, "--edition=2021", "-C", "opt-level=3", "-C", "target-feature=+fma",
                                     "-C", "link-arg=-Wl,--stack,33554432", "--cfg", "laboratory", "-A", "dead_code",
                                     *(["--cfg", "profile_reduced"] if options.profile else []),
                                     *clock_flags,
                                     source(kernel), "--extern", f"rf_d_circuit={LIB}", "-o", exe])
        assert proc.returncode == 0, proc.stderr.decode(errors="replace")
        proc, report["stamps"] = run([exe, "contour-stamps", path], binary=True)
        assert proc.returncode == 0, proc.stderr.decode(errors="replace")
        matrices = np.frombuffer(proc.stdout, dtype="<f8").reshape(len(plan), -1)
        for (name, cap), key, row in zip(plan, keys, matrices):
            blocks, _, phase, errors = unpack_stamp(row)
            bank = AREA / f"audio-{name}.bin"
            with bank.open("wb") as out:
                out.write(np.asarray(np.r_[key[3].ravel(), key[0]], "<f8").tobytes())
                for chunk in maps(blocks[1], phase, key[3], bank_count):
                    out.write(chunk)
            entry = dict(bank_sha256=sha(bank), bank_bytes=bank.stat().st_size, stamp_errors=errors, runs={})
            report["trials"][name] = entry
            expected = clock["trials"][name][str(cap)]["expected_brackets"]
            full = None
            for size in (128, 64):
                command = [exe, "reduced-engine", bank, name, report["caps"][name], size]
                proc, item = run(command)
                entry["runs"][str(size)] = item
                if proc.returncode == 0:
                    item["metrics"] = assess(proc.stdout, ref[name], expected, size, bank_count)
                    print("REDUCED_ENGINE", name, size, item["metrics"], flush=True)
                if proc.returncode != 0 or not item["metrics"]["passed"]:
                    replay, item["replay"] = run(command)
                    assert replay.returncode == proc.returncode and replay.stderr == proc.stderr
                    assert electrical(replay.stdout) == electrical(proc.stdout)
                    break
                if full is None:
                    full = electrical(proc.stdout)
                else:
                    entry["block_partition_bit_exact"] = electrical(proc.stdout) == full
                    assert entry["block_partition_bit_exact"]
        report["passed"] = all(item.get("block_partition_bit_exact", False) for item in report["trials"].values())
        report["native_deadline_passed"] = report["passed"] and all(
            item["runs"]["128"]["metrics"]["native_deadline_passed"] for item in report["trials"].values())
        sources.unchanged()
    except Exception:
        report["failure"] = traceback.format_exc()
        raise
    finally:
        write(output, report)
        for path in AREA.iterdir():
            assert path.is_file() and path.resolve().parent == AREA.resolve()
            path.unlink()
    print("REDUCED_ENGINE_GATE", report["passed"], report["native_deadline_passed"], flush=True)
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
