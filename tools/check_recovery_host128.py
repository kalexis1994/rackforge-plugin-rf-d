"""Measure the effective Windows audio period using the frozen RF-D DSP."""

import os
import re
import subprocess
import sys
import traceback
import winreg
from pathlib import Path

import numpy as np

from affine_evidence import Sources
from check_hybrid_voice import packed
from check_recovery_cost import digest, read
from check_recovery_host import AREA, COLUMNS, HOST, HOST_COMPILER, REALTIME, fixtures, summarize
from check_vco_phase import COMPILER, LIB
from prepare_dual_chain import ROOT, sha, write

QA = "evidence/recovery_host_tests01.json"
PROBE = "tools/recovery_host128_probe.rs"
ASIO_PROBE = "tools/recovery_host128_asio.rs"
PREVIOUS_PROBE = "tools/recovery_host_probe.rs"
BASE = "3ef1c674762d81d9da6b5c9705e855c0bf6f8797"
ASIO_DRIVER = "ASIO4ALL v2"
ASIO_PLAN = [("control", 32), ("control", 1200), ("dsp", 1200), ("dsp", 4800)]
OVERRIDE = "DefaultBufferSize"


def asio_profile(exe):
    # ASIO4ALL's published application hash uses GetModuleFileNameA bytes.
    value = 0
    for byte in str(exe.resolve()).encode("mbcs"):
        low = value & 255
        shift = (low - byte) & 31
        value = (value & 0xFFFFFF00) | (low ^ byte)
        value = ((value >> shift) | (value << ((32 - shift) & 31))) & 0xFFFFFFFF
    return rf"Software\ASIO4ALL v2 by Wuschel\{value:08X}"


def read_override(profile):
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, profile) as key:
            return winreg.QueryValueEx(key, OVERRIDE)
    except FileNotFoundError:
        return None


def restore_override(profile, original):
    current = read_override(profile)
    if current == original:
        return
    assert current == (128, winreg.REG_DWORD), current
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, profile, 0, winreg.KEY_SET_VALUE) as key:
        if original is None:
            winreg.DeleteValue(key, OVERRIDE)
        else:
            value, kind = original
            winreg.SetValueEx(key, OVERRIDE, 0, kind, value)
    assert read_override(profile) == original


def analyze_asio(raw, stderr, mode, blocks):
    rows = np.frombuffer(raw, "<u8").reshape(blocks, len(COLUMNS) + 2)
    metrics = summarize(rows[:, :len(COLUMNS)].tobytes(), mode, blocks)
    positions = rows[:, -2]
    buffers = rows[:, -1]
    valid = bool(np.all(positions != np.iinfo(np.uint64).max))
    position_steps = {str(int(step)): int(n) for step, n in zip(
        *np.unique(np.diff(positions.astype(np.int64)), return_counts=True),
    )}
    bank, = [line for line in stderr.splitlines() if line.startswith("ASIO_BANK\t")]
    _, name, original, effective, restored, frames, count, notices, errors = bank.split("\t")
    assert name == ASIO_DRIVER and int(count) == blocks
    assert float(effective) == 48000 and float(original) == float(restored)
    exact = (valid and position_steps == {"128": blocks - 1}
             and int(frames) == 128 and metrics["frames_by_size"] == {"128": blocks}
             and bool(np.all(buffers[1:] != buffers[:-1])))
    first_wall = int(rows[0, 1]) + int(rows[0, 10])
    metrics.update(position_steps=position_steps, positions_valid=valid, frames_128_confirmed=exact,
                   original_rate=float(original), effective_rate=float(effective), restored_rate=float(restored),
                   notices=int(notices), errors=int(errors), first_wall_with_setup_ns=first_wall)
    metrics["gate_passed"] = (
        exact and int(notices) == 0 and int(errors) == 0
        and metrics["margin_exceeded"] == metrics["gap_over_1_5_periods"] == 0
        and first_wall <= 128e9 / 48000 / 2
    )
    return metrics


def asio_banks(exe, env, report):
    report["asio_banks"] = []
    for mode, blocks in ASIO_PLAN:
        bank = dict(mode=mode, blocks=blocks, runs=[])
        report["asio_banks"].append(bank)
        args = [str(exe), "asio-bench", ASIO_DRIVER, str(blocks), mode]
        for _ in range(2):
            try:
                output = subprocess.run(args, cwd=ROOT, env=env, capture_output=True, timeout=45)
                raw, stderr, status = output.stdout, output.stderr.decode(errors="replace"), output.returncode
            except subprocess.TimeoutExpired as error:
                raw, stderr, status = error.stdout or b"", (error.stderr or b"").decode(errors="replace"), None
            item = dict(exit_code=status, rows=packed(raw), sha256=digest(raw), stream=stderr)
            if status == 0:
                try:
                    item["metrics"] = analyze_asio(raw, stderr, mode, blocks)
                except Exception:
                    item["analysis_failure"] = traceback.format_exc()
            bank["runs"].append(item)
            metrics = item.get("metrics", {})
            print("ASIO128_BANK", mode, blocks, len(bank["runs"]), status,
                  {key: metrics.get(key) for key in ("position_steps", "deadline_misses", "margin_exceeded",
                                                     "gap_over_1_5_periods", "notices")}, stderr.strip(), flush=True)
            if metrics.get("gate_passed"):
                break
        first = bank["runs"][0].get("metrics", {})
        if not first.get("frames_128_confirmed"):
            break
    report["asio_128_admitted"] = len(report["asio_banks"]) == len(ASIO_PLAN) and all(
        bank["runs"][0].get("metrics", {}).get("gate_passed", False) for bank in report["asio_banks"]
    )
    queried = subprocess.run([str(exe), "asio-query", ASIO_DRIVER], cwd=ROOT, env=env,
                             capture_output=True, timeout=10)
    report["asio_post_query"] = dict(exit_code=queried.returncode, stdout=queried.stdout.decode(errors="replace"),
                                    stderr=queried.stderr.decode(errors="replace"))


def run(report, use_asio=False, bench_asio=False, restore_asio=False):
    assert not list(AREA.iterdir())
    prior = read(QA)
    assert prior["passed"] and sha(Path(COMPILER)) == prior["compiler"]["sha256"]
    assert sha(LIB) == prior["private_input_sha256"][LIB.relative_to(ROOT).as_posix()]
    host_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=HOST, text=True).strip()
    host_bytes = subprocess.check_output(["git", "show", f"{host_commit}:{REALTIME}"], cwd=HOST)
    assert (HOST / REALTIME).read_bytes() in (host_bytes, host_bytes.replace(b"\n", b"\r\n"))
    deps = HOST / "target/release/deps"
    windows = deps / "libwindows-30e5b7032d286333.rlib"
    cpal, = deps.glob("libcpal-*.rlib")
    registry = Path(COMPILER).parents[4] / ".cargo/registry/src"
    windows_import, = registry.glob("*/windows_x86_64_msvc-0.52.6/lib/windows.0.52.0.lib")
    dependency_names = [
        "libdasp_sample-2afcd869b85b3c7a.rlib", "libwindows_core-b43b419d6265e5f1.rlib",
        "libwindows_result-fd18a7c25a2f3fff.rlib", "libwindows_targets-6f7ce55fc1841be5.rlib",
    ]
    report.update(host_commit=host_commit, host_source_sha256=sha(HOST / REALTIME),
                  previous_qa_sha256=sha(ROOT / QA))
    inputs = [Path(COMPILER), LIB, HOST_COMPILER, cpal, windows, windows_import,
              *(deps / name for name in dependency_names)]
    asio_dir = HOST / "target/release/build/asio-sys-bb9248db199c7ec7/out"
    asio_binding = asio_dir / "asio_bindings.rs"
    if use_asio:
        inputs.extend([asio_binding, asio_dir / "asio.lib"])
    report["input_sha256"] = {str(path): sha(path) for path in inputs}
    dll = AREA / "recovery-host-dsp.dll"
    exe = AREA / "recovery-host128.exe"
    combined = AREA / "recovery_host128_combined.rs"
    env = dict(os.environ, PATH="C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;" + os.environ["PATH"])
    command = []
    result = None

    def execute(args, timeout=90):
        nonlocal command, result
        command = list(map(str, args))
        result = None
        result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, timeout=timeout)
        assert result.returncode == 0, result.stderr.decode(errors="replace")
        return result

    try:
        frozen = (ROOT / PREVIOUS_PROBE).read_text(encoding="utf8")
        assert frozen.count('fn main()') == 1
        assert frozen.count('../../rackforge/' + REALTIME) == 1
        source = frozen.replace('fn main()', 'fn previous_main()', 1).replace(
            '../../rackforge/' + REALTIME, (HOST / REALTIME).as_posix(), 1,
        ) + "\n" + (ROOT / PROBE).read_text(encoding="utf8")
        if use_asio:
            source += (f'\n#[path = "{asio_binding.as_posix()}"]\nmod asio_ffi;\n'
                       + (ROOT / ASIO_PROBE).read_text(encoding="utf8"))
        combined.write_bytes(source.encode())
        report["combined_sha256"] = sha(combined)
        flags = ["--edition=2021", "-C", "opt-level=2", "-A", "dead_code", "-A", "unused_imports"]
        asio_flags = ["--cfg", "asio128", "-L", f"native={asio_dir}", "-l", "static=asio"] if use_asio else []
        report["build"] = []
        for cmd in [
            [COMPILER, *flags, "--crate-type", "cdylib", "-C", "strip=symbols",
             ROOT / "tools/recovery_host_dsp.rs", "--extern", f"rf_d_circuit={LIB}", "-o", dll],
            [HOST_COMPILER, *flags, "-L", f"dependency={deps}", "-L", f"native={windows_import.parent}",
             *asio_flags,
             combined, "--extern", f"cpal={cpal}", "--extern", f"windows={windows}", "-o", exe],
        ]:
            output = execute(cmd)
            report["build"].append(dict(command=command, stderr=packed(output.stderr)))
        report["binary_sha256"] = {p.name: sha(p) for p in (dll, exe)}
        raw = execute([exe, "fixtures"]).stdout
        report["fixtures"] = dict(rows=packed(raw), sha256=digest(raw), metrics=fixtures(raw))
        if restore_asio:
            initial = read("evidence/recovery_host128_native05.json")["asio_queries"][ASIO_DRIVER][0]
            assert initial["exit_code"] == 0
            expected = initial["stdout"].strip().split("\t")
            original_rate, original_preferred = expected[2], expected[7]
            before = execute([exe, "asio-query", ASIO_DRIVER]).stdout.decode().strip()
            assert before.split("\t")[2] == original_rate and before.split("\t")[7] == "128"
            profile = asio_profile(exe)
            assert profile.endswith("\\C1EA3620")
            original_override = read_override(profile)
            assert original_override == (128, winreg.REG_DWORD)
            restore_override(profile, (0, winreg.REG_DWORD))
            after = execute([exe, "asio-query", ASIO_DRIVER]).stdout.decode().strip()
            assert after.split("\t")[2] == original_rate and after.split("\t")[7] == original_preferred
            report["asio_preference_restoration"] = dict(
                before=before, verified=after, lab_application_profile=profile.split("\\")[-1],
                override_name=OVERRIDE, previous_value=original_override[0], restored_value=0,
            )
            print("HOST128_ASIO_RESTORED", report["asio_preference_restoration"], flush=True)
        elif bench_asio:
            profile = asio_profile(exe)
            original = read_override(profile)
            assert original is None or original[1] == winreg.REG_DWORD
            before = execute([exe, "asio-query", ASIO_DRIVER]).stdout.decode().strip()
            try:
                asio_banks(exe, env, report)
            finally:
                changed = read_override(profile)
                restore_override(profile, original)
                after = execute([exe, "asio-query", ASIO_DRIVER]).stdout.decode().strip()
                report["asio_preference_restoration"] = dict(
                    before=before, verified=after, lab_application_profile=profile.split("\\")[-1],
                    override_name=OVERRIDE, original_value=None if original is None else original[0],
                    observed_value=None if changed is None else changed[0],
                )
                assert before.split("\t")[2:] == after.split("\t")[2:]
        elif use_asio:
            for driver in ("FL Studio ASIO", "ASIO4ALL v2", "Focusrite USB ASIO", "Focusrite Thunderbolt ASIO"):
                attempts = []
                for _ in range(2):
                    args = [str(exe), "asio-query", driver]
                    try:
                        output = subprocess.run(args, cwd=ROOT, env=env, capture_output=True, timeout=10)
                        item = dict(exit_code=output.returncode, stdout=output.stdout.decode(errors="replace"),
                                    stderr=output.stderr.decode(errors="replace"))
                    except subprocess.TimeoutExpired as error:
                        item = dict(exit_code=None, timeout_s=10, stdout=(error.stdout or b"").decode(errors="replace"),
                                    stderr=(error.stderr or b"").decode(errors="replace"))
                    attempts.append(item)
                report.setdefault("asio_queries", {})[driver] = attempts
                print("HOST128_ASIO", driver, attempts[0], flush=True)
        else:
            for attempt in range(2):
                output = execute([exe, "discover"])
                rows = output.stdout.decode().splitlines()
                report.setdefault("discovery", []).append(rows)
                print("HOST128_DISCOVERY", attempt, "\n".join(rows), flush=True)
        report.update(passed=True, physical_128_admitted=False, whole_voice_rt=False)
    except Exception:
        report["failure"] = traceback.format_exc()
        if result is not None:
            report["failed_output"] = dict(exit_code=result.returncode, stdout=packed(result.stdout),
                                           stderr=packed(result.stderr), command=command)
        if command:
            replay = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, timeout=90)
            report["unchanged_failure_replay"] = dict(
                exit_code=replay.returncode, stdout=packed(replay.stdout), stderr=packed(replay.stderr),
            )
    finally:
        allowed = {p.name for p in (dll, exe, combined)} | {
            "recovery-host128.pdb", "librecovery-host-dsp.dll.a",
        }
        for artifact in AREA.iterdir():
            obj = re.fullmatch(r"recovery-host128\.[\w.-]+\.rcgu\.o", artifact.name)
            assert (artifact.name in allowed or obj) and artifact.resolve().parent == AREA.resolve(), artifact
            artifact.unlink()
    report["temporary_area_empty"] = not list(AREA.iterdir())


if __name__ == "__main__":
    restore_asio = sys.argv[1:] == ["--restore-asio"]
    bench_asio = sys.argv[1:] == ["--asio-bench"]
    use_asio = restore_asio or bench_asio or sys.argv[1:] == ["--asio"]
    sources = Sources([
        "tools/check_recovery_host128.py", PROBE, PREVIOUS_PROBE, "tools/recovery_host_dsp.rs",
        "tools/recovery_cost_exp_kernel.rs", "tools/recovery_cost_exp_data.rs",
        "crates/rf-d-circuit/src/j7_stream_output.rs", "docs/RECOVERY_HOST128_PROTOCOLO.md",
        *([ASIO_PROBE, "docs/RECOVERY_HOST128_ASIO.md"] if use_asio else []),
    ])
    report = dict(passed=False, **sources.fields())
    run(report, use_asio, bench_asio, restore_asio)
    sources.unchanged()
    number = 1
    while (ROOT / f"evidence/recovery_host128_native{number:02d}.json").exists():
        number += 1
    write(ROOT / f"evidence/recovery_host128_native{number:02d}.json", report)
    print("HOST128_FINAL", report["passed"], report.get("failure", ""), flush=True)
    if not report["passed"]:
        raise SystemExit(1)
