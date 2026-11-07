"""Match deterministic solver work to previously measured ASIO callback ordinals."""

import os
import shutil
import subprocess
import traceback
from pathlib import Path

import numpy as np

from affine_evidence import Sources
from check_hybrid_voice import packed, unpack
from check_recovery_cost import digest, read
from check_recovery_engine128 import (
    AREA, BROADCAST_KERNEL, COLUMNS_KERNEL, COMPILER, DSP, EXP_KERNEL, SPLIT_FIR,
    column_kernel, retire_lab, sources_for_build,
)
from check_recovery_host import COLUMNS
from prepare_dual_chain import ROOT, sha, write

REF = "evidence/recovery_engine128_native09.json"
PREFIX = "evidence/recovery_engine128_work"
WORK = "tools/recovery_engine128_work.rs"
PROTOCOL = "docs/RECOVERY_ENGINE128_HOT_PROTOCOLO.md"
SCRIPT = """const fs = require('node:fs');
const bytes = fs.readFileSync(process.argv[1]);
const {exports: wasm} = new WebAssembly.Instance(new WebAssembly.Module(bytes));
const handle = wasm.rf_profile_new();
const output = Buffer.alloc(4800 * 4);
for (let block = 0; block < 4800; block++) {
    output.writeUInt32LE(wasm.rf_profile_block(handle), block * 4);
}
wasm.rf_free(handle);
process.stdout.write(output);
"""


def analyze(raw, reference):
    rows = np.frombuffer(raw, "<u4")
    assert len(rows) == 4800
    evaluations = rows & 0x3fff
    worst = (rows >> 14) & 0xf
    large = rows >> 18
    assert np.all((evaluations >= 1024) & (evaluations <= 12288))
    assert np.all((worst >= 1) & (worst <= 12)) and np.all(large <= 1024)
    result = dict(min_evaluations=int(min(evaluations)), max_evaluations=int(max(evaluations)),
                  max_iterations=int(max(worst)), steps_with_large_converged_z=int(sum(large)), runs=[])
    for run in reference["banks"][-1]["runs"]:
        assert run["metrics"]["frames_128_confirmed"]
        timed = np.frombuffer(unpack(run["rows"]), "<u8").reshape(4800, len(COLUMNS) + 2)
        wall = timed[:, COLUMNS.index("wall_ns")]
        cycles = timed[:, COLUMNS.index("cycles")]
        exceeded = wall > 128e9 / 48000 / 2
        assert exceeded.any() and (~exceeded).any()
        result["runs"].append(dict(
            over_margin=int(sum(exceeded)), max_evaluations_over_margin=int(max(evaluations[exceeded])),
            median_evaluations_over_margin=float(np.median(evaluations[exceeded])),
            median_evaluations_within_margin=float(np.median(evaluations[~exceeded])),
            evaluations_at_peak=int(evaluations[np.argmax(wall)]),
            correlation_cycles=float(np.corrcoef(evaluations, cycles)[0, 1]),
        ))
    return result


def run(report, destination):
    keep = set(AREA.iterdir())
    assert all(path.name in ("host-target", "host-target-msvc.jsonl") for path in keep)
    kernel, probe, wasm, lib = (AREA / name for name in
                               ("work-kernel.rs", "work-probe.rs", "work-probe.wasm", "librf_d_circuit_work.rlib"))
    node = Path(shutil.which("node"))
    ref = read(REF)
    assert sha(Path(COMPILER)) == next(value for name, value in ref["dependencies"].items()
                                      if Path(name) == Path(COMPILER))
    rust = [COMPILER, "--edition=2021", "--target", "wasm32-unknown-unknown",
            "-C", "opt-level=3", "-C", "target-feature=+simd128", "-A", "dead_code"]
    report.update(reference_sha256=sha(ROOT / REF), node_sha256=sha(node), build=[])
    command, execution = [], None

    def execute(args):
        nonlocal command, execution
        command, execution = list(map(str, args)), None
        execution = subprocess.run(command, cwd=ROOT, capture_output=True, timeout=90, env=os.environ)
        assert execution.returncode == 0, execution.stderr.decode(errors="replace")
        return execution.stdout

    try:
        kernel.write_bytes(column_kernel(True))
        assert sha(kernel) == ref["artifact_sha256"]["engine_kernel_columns.rs"]
        guest, _ = sources_for_build(kernel, True)
        before_guest, _, _ = guest.decode().partition("\n// Appended to the frozen DSP adapter")
        assert len(before_guest) < len(guest)
        source = before_guest + "\n" + (ROOT / WORK).read_text(encoding="utf8")
        probe.write_bytes(source.encode())
        for args in (
            [*rust, "--crate-type", "rlib", "--crate-name", "rf_d_circuit",
             ROOT / "crates/rf-d-circuit/src/lib.rs", "-o", lib],
            [*rust, "--crate-type", "cdylib", "-C", "link-arg=-zstack-size=8388608",
             "-C", "panic=abort", probe, "--extern", f"rf_d_circuit={lib}", "-o", wasm],
        ):
            execute(args)
            report["build"].append(command)
        raw = execute([node, "-e", SCRIPT, wasm])
        report.update(passed=True, kernel_sha256=sha(kernel), probe_sha256=sha(probe),
                      wasm_sha256=sha(wasm), raw=packed(raw), metrics=analyze(raw, ref))
    except Exception:
        report["failure"] = traceback.format_exc()
        if command:
            report["failed_command"] = command
            if execution is not None:
                report["failed_output"] = dict(exit_code=execution.returncode,
                    stdout_sha256=digest(execution.stdout), stderr=packed(execution.stderr))
            replay = subprocess.run(command, cwd=ROOT, capture_output=True, timeout=90)
            report["unchanged_replay"] = dict(exit_code=replay.returncode,
                stdout_sha256=digest(replay.stdout), stderr=packed(replay.stderr))
    finally:
        write(destination, report)
        retire_lab(keep)
        report["measurement_area_retired"] = set(AREA.iterdir()) == keep
        write(destination, report)


if __name__ == "__main__":
    number = 1
    while (ROOT / f"{PREFIX}{number:02d}.json").exists():
        number += 1
    sources = Sources([WORK, DSP, EXP_KERNEL, COLUMNS_KERNEL, BROADCAST_KERNEL, SPLIT_FIR, PROTOCOL,
                       "tools/check_recovery_engine128_work.py", "tools/check_recovery_engine128.py",
                       "tools/recovery_cost_exp_data.rs", "tools/recovery_engine128_guest.rs"])
    report = dict(passed=False, **sources.fields())
    run(report, ROOT / f"{PREFIX}{number:02d}.json")
    sources.unchanged()
    print("ENGINE128_WORK", report.get("metrics"), report.get("failure", ""), flush=True)
    raise SystemExit(0 if report["passed"] else 1)
