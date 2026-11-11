"""Confirm 128 effective frames for the bounded native pilot on NVIDIA ASIO."""
import subprocess
import winreg
from contextlib import contextmanager, nullcontext
from pathlib import Path

from check_hybrid_voice import packed
from check_recovery_engine128 import (
    ASIO_PROBE, ENGINE_PROBE, PREVIOUS_PROBE, PROBE, SCHEDULE_PROBE, SMT_PROBE,
    HOST_CORE, analyze, sources_for_build,
)
from check_recovery_engine128_schedule import topology
from check_recovery_engine128_smt import NVIDIA_ENDPOINT, admitted, analyze_smt, fixed_pair_primary
from check_recovery_engine128_endpoint import DEVICES, ENABLED, PARENT, active_hardware, snapshot
from check_recovery_host128 import ASIO_DRIVER, asio_profile, read_override, restore_override
from check_rf_d_pilot_returns import AREA, COMPILER, ROOT, emit
from check_rf_d_reduced_engine_rack import HOST, HOST_COMPILER, package
from prepare_dual_chain import sha

OWN = "tools/check_rf_d_pilot_returns_asio.py"
SOURCES = (OWN, ASIO_PROBE, ENGINE_PROBE, PREVIOUS_PROBE, PROBE, SCHEDULE_PROBE, SMT_PROBE,
           "tools/check_recovery_engine128.py", "tools/check_recovery_engine128_smt.py",
           "tools/check_recovery_host128.py", "tools/check_recovery_engine128_endpoint.py",
           "docs/RECOVERY_ENGINE128_NVIDIA_PROTOCOLO.md")


@contextmanager
def temporary_nvidia_profile(profile, report):
    before = snapshot(PARENT)
    key = profile.rsplit("\\", 1)[1]
    if key in before:
        yield
        return
    assert profile == PARENT + "\\C1EA3620", profile
    name, device, (interface,) = DEVICES[0]
    hardware = active_hardware().get(name, {})
    assert device in hardware.get("hashes", []) and hardware.get("endpoints"), hardware
    report["temporary_profile"] = dict(path=profile, hardware=hardware, restored=False)
    keys = (device, device + "\\" + interface, device + "\\" + interface + "\\00000000")
    try:
        with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, profile, 0, winreg.KEY_SET_VALUE) as entry:
            winreg.SetValueEx(entry, "Flags", 0, winreg.REG_DWORD, 0)
            winreg.SetValueEx(entry, "DefaultBufferSize", 0, winreg.REG_DWORD, 0)
        for suffix in keys:
            with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, profile + "\\" + suffix,
                                    0, winreg.KEY_SET_VALUE) as entry:
                winreg.SetValueEx(entry, "Flags", 0, winreg.REG_DWORD, ENABLED)
        yield
    finally:
        try:
            entries = snapshot(profile)
        except FileNotFoundError:
            entries = {}
        for suffix in sorted(entries, key=lambda item: (item.count("\\"), len(item)), reverse=True):
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, profile + ("\\" + suffix if suffix else ""))
        report["temporary_profile"]["restored"] = snapshot(PARENT) == before
        assert report["temporary_profile"]["restored"]


def campaign(path, source, rack, env, cpu, component_flags=None):
    env = env.copy()
    report = rack["physical"] = dict(passed=False, physical_measured=False, cpu=cpu, builds={}, runs=[])
    for key in tuple(env):
        if key.startswith(("RF_D_SMT_", "RF_D_SCHED_")):
            del env[key]
    env["RACKFORGE_AUDIO_WORKERS"] = "0"

    def run(args, task_env=env, timeout=90):
        command = list(map(str, args))
        process = subprocess.run(command, cwd=ROOT, env=task_env, capture_output=True, timeout=timeout)
        result = dict(command=command, exit_code=process.returncode,
                      stdout=packed(process.stdout), stderr=packed(process.stderr))
        return process, result

    paths = dict(pilot=path, control=AREA / "reduced-asio-control")
    assert sha(path / "rf-d-loaded.dll") == rack["component_sha256"]
    package(paths["control"])
    begin = source.index("    let Some(engine) = &mut voice.engine else")
    end = source.index("\n    STATUS_OK\n}", begin)
    source = source[:begin] + """    if voice.engine.is_none() {
        return STATUS_INVALID_STATE;
    }
    unsafe { slice::from_raw_parts_mut(block.output_interleaved, frames * 2) }.fill(0.);""" + source[end:]
    if component_flags is None:
        component_flags = [
            COMPILER, "--edition=2021", "-C", "opt-level=3", "-C", "target-feature=+fma",
            "-C", "panic=abort", "-A", "dead_code", "--cfg", "pilot_returns",
            *(["--cfg", "pilot_wide_returns"] if rack["wide"] else []),
        ]
    proc, report["builds"]["control"] = run([
        *component_flags, "--crate-type", "cdylib",
        emit("pilot-silent.rs", source), "-o", paths["control"] / "rf-d-loaded.dll",
    ])
    assert proc.returncode == 0, proc.stderr.decode(errors="replace")
    _, host_source = sources_for_build(schedule=True, smt=True, smt_lean=True)
    probe = AREA / "pilot-physical.rs"
    probe.write_bytes(host_source)
    deps = HOST / "target/release/deps"
    core = deps / HOST_CORE
    assert sha(core) == rack["core_sha256"]
    cpal = deps / "libcpal-7dab8e06a9b0e32f.rlib"
    windows = deps / "libwindows-30e5b7032d286333.rlib"
    asio = HOST / "target/release/build/asio-sys-bb9248db199c7ec7/out"
    report["dependencies"] = {item.name: sha(item) for item in (cpal, windows, asio / "asio.lib")}
    registry = Path(COMPILER).parents[4] / ".cargo/registry/src"
    native = list(dict.fromkeys(path.parent for path in (
        *sorted((HOST / "target/release/build").glob("*/out/*.lib")),
        *sorted(registry.glob("*/windows_x86_64_msvc-*/lib/*.lib")),
    )))
    exe = AREA / "recovery-host128.exe"
    proc, report["builds"]["rack"] = run([
        HOST_COMPILER, "--edition=2021", "-C", "opt-level=2", "-A", "dead_code", "-A", "unused_imports",
        "--cfg", "asio128", "-L", f"dependency={deps}", *[arg for d in native for arg in ("-L", f"native={d}")],
        "-L", f"native={asio}", "-l", "static=asio", probe, "--extern", f"cpal={cpal}",
        "--extern", f"windows={windows}", "--extern", f"rackforge_core={core}", "-o", exe,
    ])
    assert proc.returncode == 0, proc.stderr.decode(errors="replace")
    query = [exe, "asio-query", ASIO_DRIVER]
    profile = asio_profile(exe)
    if rack.get("continuous", {}).get("passed"):
        scope = temporary_nvidia_profile(profile, report)
    else:
        scope = nullcontext()
    with scope:
        original = read_override(profile)
        proc, report["before"] = run(query)
        assert proc.returncode == 0
        try:
            proc, report["endpoint"] = run([exe, "smt-endpoints", ASIO_DRIVER], timeout=10)
            assert proc.returncode == 0 and proc.stdout.decode().strip() == NVIDIA_ENDPOINT
            proc, report["topology_probe"] = run([exe, "schedule-topology"])
            assert proc.returncode == 0
            top = topology(proc.stdout.decode())
            fixed_pair_primary(top, cpu)
            rows = AREA / "pilot-asio-rows.bin"
            for label, blocks in (("control", 1200), ("pilot", 4800), ("pilot", 4800)):
                rows.unlink(missing_ok=True)
                controls = dict(env, RF_D_ENGINE_ROUTE="control" if label == "control" else "rack",
                                RF_D_ENGINE_PACKAGE=str(paths[label]),
                                RF_D_ENGINE_CACHE=str(AREA / "pilot-cache"), RF_D_ENGINE_ROWS=str(rows),
                                RF_D_SMT_MODE="quiet-event", RF_D_SMT_SUPERVISOR="1",
                                RF_D_SMT_FIXED_CPU=str(cpu), RF_D_SMT_FIXED_IDLE="8500")
                proc, item = run([exe, "asio-bench", ASIO_DRIVER, blocks, "dsp"], controls)
                item.update(label=label, blocks=blocks, rows=packed(rows.read_bytes() if rows.exists() else b""))
                report["runs"].append(item)
                if proc.returncode == 0:
                    result = analyze_smt(rows.read_bytes(), proc.stderr.decode(), blocks, "quiet-event",
                                         None, top, analyze, silent=label == "control",
                                         endpoint=NVIDIA_ENDPOINT, event_cpu=cpu, event_idle=8500)
                    item["metrics"] = result
                    report["physical_measured"] |= result["frames_128_confirmed"]
                    print("PILOT_ASIO", label, result["wall_ns"], result["margin_exceeded"],
                          result["gate_passed"], flush=True)
                else:
                    print("PILOT_ASIO", label, proc.returncode, proc.stderr.decode(errors="replace"), flush=True)
            report["passed"] = admitted(report["runs"][0], report["runs"][1:])
        finally:
            restore_override(profile, original)
            proc, report["restored"] = run(query)
            assert proc.returncode == 0 and report["restored"]["stdout"] == report["before"]["stdout"]
    rack["physical_measured"] = report["physical_measured"]
