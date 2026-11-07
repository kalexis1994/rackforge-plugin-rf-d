"""Check the exact scalar and SIMD recovery kernels on the frozen electrical inputs."""

import argparse
import os
import shutil
import subprocess
import traceback
from pathlib import Path

import numpy as np

from affine_evidence import Sources
from check_hybrid_voice import packed, unpack
from check_recovery_cost import check_laws, decode, digest, read, store
from check_recovery_cost_exp import compare, endpoints, physical
from check_recovery_engine128 import (
    AREA, BROADCAST_KERNEL, COLUMNS_KERNEL, COMPILER, EXP_KERNEL, SPLIT_FIR, column_kernel, replace_once, retire_lab,
)
from prepare_dual_chain import ROOT, sha, write

REF = "evidence/recovery_cost_exp_native01.json"
PHYSICAL = "evidence/charge_control_native01.json"
SOURCE = "tools/recovery_cost_probe.rs"
DATA = "tools/recovery_cost_exp_data.rs"
PROTOCOL = "docs/RECOVERY_ENGINE128_BROADCAST_PROTOCOLO.md"
RUNNER = "tools/check_recovery_engine128_reserve.py"
MODES = ("vectors", "stress", "stages", "laws")
VARIANTS = ("scalar", "pairs", "broadcast")
WASI = """const fs = require('node:fs');
const { WASI } = require('node:wasi');
const args = process.argv.slice(1);
const wasi = new WASI({version: 'preview1', args, returnOnExit: true});
const moduleBytes = fs.readFileSync(args[0]);
const instance = new WebAssembly.Instance(new WebAssembly.Module(moduleBytes), wasi.getImportObject());
process.exitCode = wasi.start(instance);
"""


def probe_source(kernel, table_paths):
    probe = (ROOT / SOURCE).read_text(encoding="utf8")
    probe = replace_once(probe, '"recovery_cost_exp_kernel.rs"', f'"{kernel.as_posix()}"')
    stream = (ROOT / "crates/rf-d-circuit/src/j7_stream_output.rs").as_posix()
    probe = probe.replace('"../crates/rf-d-circuit/src/j7_stream_output.rs"', f'"{stream}"')
    start, end = probe.index("fn input("), probe.index("fn same(")
    nominal, stress = (path.as_posix() for path in table_paths)
    probe = probe[:start] + f"""fn input(k: usize, stress: bool) -> f64 {{
    let table = if stress {{ include_bytes!("{stress}") }} else {{ include_bytes!("{nominal}") }};
    let offset = k * 8;
    f64::from_le_bytes(table[offset..offset + 8].try_into().unwrap())
}}
""" + probe[end:]
    probe = replace_once(probe, "let ports = core::step(&mut s, u).unwrap(); let x = core::nodes(s);",
                          "let (ports, z, iterations, residual) = core::inspect(&mut s, u, 12).unwrap();\n"
                          "            let x = core::nodes(s);")
    probe = replace_once(probe, ".chain(s.q).chain(x) { out.write_all",
                          ".chain(s.q).chain(x).chain(s.history).chain(s.defects).chain(z)\n"
                          "                .chain([iterations as f64, residual]) { out.write_all")
    return probe.encode()


def fir_source(kernel):
    source = (ROOT / SOURCE).read_text(encoding="utf8")
    source = replace_once(source, '"recovery_cost_exp_kernel.rs"', f'"{kernel.as_posix()}"')
    source = replace_once(source, '"recovery_cost_split_fir.rs"', f'"{(ROOT / SPLIT_FIR).as_posix()}"')
    stream = (ROOT / "crates/rf-d-circuit/src/j7_stream_output.rs").as_posix()
    return source.replace('"../crates/rf-d-circuit/src/j7_stream_output.rs"', f'"{stream}"').encode()


def summarize(data, reference):
    results = {}
    for mode in ("vectors", "stress"):
        full = np.frombuffer(data[mode], "<f8").reshape(3, 1537, 137)
        assert np.isfinite(full).all() and float(np.max(full[..., -1])) <= 2e-13
        assert np.all((full[..., -2] >= 1) & (full[..., -2] <= 12))
        raw = full[..., :93].tobytes()
        results[mode] = dict(
            saved=store(raw, REF, mode), full_state_sha256=digest(data[mode]),
            max_residual=float(np.max(full[..., -1])), max_iterations=int(np.max(full[..., -2])),
            native_bit_exact=raw == decode(reference, mode), python_comparison=compare(raw),
        )
    results["stages"] = dict(raw=packed(data["stages"]), comparisons=endpoints(data["stages"]))
    results["laws"] = dict(raw=packed(data["laws"]), comparisons=check_laws(data["laws"]))
    nominal = np.frombuffer(data["vectors"], "<f8").reshape(3, 1537, 137)
    results["physical"] = physical(nominal[..., :93].tobytes())
    assert all(case["admitted"] for case in results["physical"])
    return results


def run(report, destination, fir_only=False):
    keep = set(AREA.iterdir())
    paths = {name: AREA / f"reserve-{name}" for name in
             ("probe.rs", "kernel.rs", "circuit.rlib", "probe.wasm", "vectors.bin", "stress.bin")}
    paths["circuit.rlib"] = AREA / "librf_d_circuit_reserve.rlib"
    assert not keep.intersection(paths.values())
    assert all(path.name == "host-target" or path.name == "host-target-msvc.jsonl" for path in keep)
    reference = read(REF)
    assert reference["physical_admitted"] and sha(Path(COMPILER)) == reference["compiler_sha256"]
    node = Path(shutil.which("node"))
    report.update(node=dict(path=str(node), sha256=sha(node),
                            version=subprocess.check_output([node, "--version"], text=True).strip()),
                  compiler_sha256=sha(Path(COMPILER)), reference_sha256=sha(ROOT / REF),
                  physical_sha256=sha(ROOT / PHYSICAL), variants={})
    rust = [COMPILER, "--edition=2021", "--target", "wasm32-wasip1",
            "-C", "opt-level=3", "-C", "target-feature=+simd128", "-A", "dead_code", "-A", "unused_imports"]
    env = dict(os.environ, OPENBLAS_NUM_THREADS="1")
    command, stdin, execution = [], None, None

    def execute(args, input_bytes=None):
        nonlocal command, stdin, execution
        command, stdin, execution = list(map(str, args)), input_bytes, None
        execution = subprocess.run(command, cwd=ROOT, env=env, input=stdin, capture_output=True, timeout=95)
        assert execution.returncode == 0, execution.stderr.decode(errors="replace")
        return execution.stdout

    try:
        execute([*rust, "--crate-type", "rlib", "--crate-name", "rf_d_circuit",
                 ROOT / "crates/rf-d-circuit/src/lib.rs", "-o", paths["circuit.rlib"]])
        report["library_sha256"] = sha(paths["circuit.rlib"])
        if fir_only:
            kernel, probe, wasm = (paths[name] for name in ("kernel.rs", "probe.rs", "probe.wasm"))
            kernel.write_bytes(column_kernel(True))
            probe.write_bytes(fir_source(kernel))
            execute([*rust, "--cfg", "expfoh", "--cfg", "splitfir", "-C", "link-arg=-zstack-size=8388608",
                     probe, "--extern", f"rf_d_circuit={paths['circuit.rlib']}", "-o", wasm])
            build = command
            raw = execute([node, "--no-warnings", "-e", WASI, wasm, "fircheck"])
            tag, frames, scenes, chunks = raw.decode().strip().split(",")
            assert tag == "FIR_EXACT" and int(frames) > 9000 and (int(scenes), int(chunks)) == (4, 48)
            report.update(passed=True, kernel_sha256=sha(kernel), probe_sha256=sha(probe),
                          wasm_sha256=sha(wasm), compile=build, fir_check=packed(raw))
            print("FIR128_WASI", raw.decode().strip(), flush=True)
            return
        for mode in ("vectors", "stress"):
            table = np.frombuffer(decode(reference, mode), "<f8").reshape(3, 1537, 93)[..., 2]
            assert np.array_equal(table[0].view("<u8"), table[1].view("<u8"))
            assert np.array_equal(table[0].view("<u8"), table[2].view("<u8"))
            paths[mode + ".bin"].write_bytes(table[0].tobytes())
        report["input_sha256"] = {mode: sha(paths[mode + ".bin"]) for mode in ("vectors", "stress")}
        scalar = {}
        for variant in VARIANTS:
            if variant == "scalar":
                kernel = ROOT / EXP_KERNEL
            else:
                kernel = paths["kernel.rs"]
                kernel.write_bytes(column_kernel(variant == "broadcast"))
            probe = paths["probe.rs"]
            probe.write_bytes(probe_source(kernel, (paths["vectors.bin"], paths["stress.bin"])))
            wasm = paths["probe.wasm"]
            execute([*rust, "--cfg", "expfoh", "-C", "link-arg=-zstack-size=8388608",
                     probe, "--extern", f"rf_d_circuit={paths['circuit.rlib']}", "-o", wasm])
            item = dict(compile=command, kernel_sha256=sha(kernel), probe_sha256=sha(probe),
                        wasm_sha256=sha(wasm), modes={})
            report["variants"][variant] = item
            for mode in MODES:
                raw = execute([node, "--no-warnings", "-e", WASI, wasm, mode],
                              unpack(reference["laws"]["input"]) if mode == "laws" else None)
                item["modes"][mode] = dict(sha256=digest(raw), bytes=len(raw))
                if variant == "scalar":
                    scalar[mode] = raw
                else:
                    if raw != scalar[mode]:
                        got, expected = np.frombuffer(raw, "<u8"), np.frombuffer(scalar[mode], "<u8")
                        if len(got) == len(expected):
                            i = int(np.flatnonzero(got != expected)[0])
                            item["first_difference"] = dict(mode=mode, word=i, actual=int(got[i]),
                                                            expected=int(expected[i]))
                    assert raw == scalar[mode], (variant, mode)
            print("RESERVE_BITWISE", variant, item["modes"], flush=True)
        report["results"] = summarize(scalar, reference)
        report["passed"] = True
    except Exception:
        report["failure"] = traceback.format_exc()
        if command:
            report["failed_command"] = command
            if execution is not None:
                report["failed_output"] = dict(exit_code=execution.returncode,
                    stdout_sha256=digest(execution.stdout), stderr=packed(execution.stderr))
            try:
                replay = subprocess.run(command, cwd=ROOT, env=env, input=stdin, capture_output=True, timeout=95)
                report["unchanged_replay"] = dict(exit_code=replay.returncode,
                    stdout_sha256=digest(replay.stdout), stderr=packed(replay.stderr))
            except subprocess.TimeoutExpired:
                report["unchanged_replay"] = dict(timeout_s=95)
    finally:
        write(destination, report)
        retire_lab(keep)
        report["measurement_area_retired"] = set(AREA.iterdir()) == keep
        write(destination, report)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fir", action="store_true", help="recheck the contiguous FIR in WASI")
    args = parser.parse_args()
    sources = Sources([RUNNER, SOURCE, EXP_KERNEL, DATA, COLUMNS_KERNEL, BROADCAST_KERNEL, PROTOCOL,
                       "tools/check_recovery_engine128.py", "tools/check_recovery_cost_exp.py",
                       "tools/check_recovery_cost.py", "tools/recovery_cost_exp_model.py",
                       "crates/rf-d-circuit/src/j7_stream_output.rs", *([SPLIT_FIR] if args.fir else [])])
    kind = "broadcast_fir" if args.fir else "reserve"
    n = 1
    while (ROOT / f"evidence/recovery_engine128_{kind}{n:02d}.json").exists():
        n += 1
    report = dict(passed=False, **sources.fields())
    run(report, ROOT / f"evidence/recovery_engine128_{kind}{n:02d}.json", fir_only=args.fir)
    sources.unchanged()
    print("RESERVE_FINAL", report["passed"], report.get("failure", ""), flush=True)
    raise SystemExit(0 if report["passed"] else 1)
