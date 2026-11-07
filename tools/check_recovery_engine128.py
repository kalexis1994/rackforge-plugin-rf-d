"""Time the RackForge portable plugin path against the actual ASIO period."""

import os
import re
import subprocess
import sys
import traceback
from pathlib import Path

import numpy as np

from affine_evidence import Sources
from check_hybrid_voice import packed
from check_recovery_cost import digest, read
from check_recovery_host import AREA, HOST, HOST_COMPILER, REALTIME
from check_recovery_host128 import (
    ASIO_DRIVER, ASIO_PROBE, PREVIOUS_PROBE, PROBE, analyze_asio,
    asio_profile, read_override, restore_override,
)
from check_vco_phase import COMPILER, LIB
from prepare_dual_chain import ROOT, sha, write

QA = "evidence/recovery_host128_tests01.json"
GUEST = "tools/recovery_engine128_guest.rs"
ENGINE_PROBE = "tools/recovery_engine128_probe.rs"
DSP = "tools/recovery_host_dsp.rs"
HOST_CORE = "librackforge_core-3896b480a6ff0d55.rlib"
PACKAGE_ID = "org.rackforge.lab.rf-d-recovery"
PLAN = [("control", 32), ("control", 1200), ("native", 1200), ("instance", 1200),
        ("rack", 1200), ("rack", 4800)]


def replace_once(source, old, new):
    assert source.count(old) == 1, old
    return source.replace(old, new, 1)


def engine_fixture(raw):
    values = np.frombuffer(raw, "<f4").reshape(3, 2048, 2)
    assert np.isfinite(values).all()
    assert np.all(values[:, :48] == 0) and np.all(values[:, 48] != 0)
    assert np.array_equal(values[:, :, 0], values[:, :, 1])
    peak = float(np.max(abs(values[0])))
    error = float(np.max(abs(values[0].astype(np.float64) - values[1:])))
    assert peak > 0 and error <= 1e-10 + 1e-7 * peak
    assert values[1].tobytes() == values[2].tobytes()
    return dict(frames=2048, startup_padding=48, peak_v=peak, max_error_v=error,
                native_instance_bit_exact=values[0].tobytes() == values[1].tobytes(),
                rack_instance_bit_exact=True)


def analyze(raw, stderr, blocks, mode):
    metrics = analyze_asio(raw, stderr, "dsp", blocks)
    line, = [line for line in stderr.splitlines() if line.startswith("ENGINE128\t")]
    calls, allocated, first, alloc_blocks, faults, misses, host_blocks, host_max = map(
        int, line.split("\t")[1:],
    )
    assert calls == blocks and alloc_blocks <= calls and first <= allocated
    assert host_blocks == (blocks if mode in ("rack", "control") else 0)
    metrics.update(engine_route=mode, host_allocations=allocated, first_host_allocations=first,
                   allocating_blocks=alloc_blocks, slot_faults=faults, rack_deadline_misses=misses,
                   rack_telemetry_blocks=host_blocks, rack_max_ns=host_max)
    metrics["gate_passed"] = metrics["gate_passed"] and allocated == faults == misses == 0
    return metrics


def make_package(path):
    path.mkdir()
    (path / "metadata").mkdir()
    manifest = f"""schema_version = 1
id = "{PACKAGE_ID}"
name = "RF-D Recovery Lab"
vendor = "RackForge"
version = "0.1.0"
kind = "instrument"
state_version = 1
capabilities = ["audio_output", "presets"]

[audio]
output_buses = [{{ id = "main", name = "Output", channels = 2, layout = "stereo" }}]

[api]
major = 1
minor = 11

[component]
abi = "wasm-v1"
path = "component.wasm"
runtime_descriptor = "metadata/runtime.json"
parameter_schema = "metadata/parameters.json"
preset_catalog = "metadata/presets.json"
"""
    (path / "rackforge-plugin.toml").write_bytes(manifest.encode())
    write(path / "metadata/runtime.json", dict(schema_version=1, id=PACKAGE_ID, version="0.1.0", state_version=1))
    write(path / "metadata/parameters.json", dict(schema_version=1, pages=[], parameters=[]))
    write(path / "metadata/presets.json", dict(
        schema_version=1, banks=[dict(id="lab", name="Lab", order=0)],
        presets=[dict(id="default", name="Default", bank="lab", category="Lab", order=0, tags=[])],
    ))


def sources_for_build():
    guest = (ROOT / DSP).read_text(encoding="utf8")
    for original, absolute in [
        ("recovery_cost_exp_kernel.rs", ROOT / "tools/recovery_cost_exp_kernel.rs"),
        ("../crates/rf-d-circuit/src/j7_stream_output.rs", ROOT / "crates/rf-d-circuit/src/j7_stream_output.rs"),
    ]:
        guest = replace_once(guest, f'"{original}"', f'"{absolute.as_posix()}"')
    guest += "\n" + (ROOT / GUEST).read_text(encoding="utf8")

    probe = (ROOT / PREVIOUS_PROBE).read_text(encoding="utf8")
    probe = replace_once(probe, "fn main()", "fn legacy_main()")
    probe = replace_once(probe, "../../rackforge/" + REALTIME, (HOST / REALTIME).as_posix())
    probe = replace_once(probe, "fn measure(", "fn measure<R: LabRender>(")
    probe = replace_once(probe, "dsp: Option<&mut Dsp>", "dsp: Option<&mut R>")

    asio = (ROOT / ASIO_PROBE).read_text(encoding="utf8")
    asio = replace_once(asio, "UnsafeCell<Option<Dsp>>", "UnsafeCell<Option<EngineWork>>")
    asio = replace_once(asio, "Some(Dsp::new(Api::load()?))", "Some(EngineWork::from_env()?)")
    asio = replace_once(asio, "io::BufWriter::new(io::stdout().lock())", "engine_rows()?")
    asio = replace_once(asio, "    out.flush()?;", """    out.flush()?;
    if let Some(work) = unsafe { &*session.dsp.get() } {
        work.report();
    }""")
    entry = (ROOT / PROBE).read_text(encoding="utf8")
    entry = replace_once(entry, "    let _com = Com::init()?;", """    if args.first().is_some_and(|s| s == "engine-fixtures") {
        return engine_fixtures(Path::new(&args[1]), Path::new(&args[2]));
    }
    #[cfg(engine_alloc_trace)]
    if args.first().is_some_and(|s| s == "engine-allocation") {
        return engine_allocation_trace(Path::new(&args[1]), Path::new(&args[2]));
    }
    let _com = Com::init()?;""")
    asio_dir = HOST / "target/release/build/asio-sys-bb9248db199c7ec7/out"
    probe += "\n" + entry + f'\n#[path = "{(asio_dir / "asio_bindings.rs").as_posix()}"]\nmod asio_ffi;\n'
    probe += asio + "\n" + (ROOT / ENGINE_PROBE).read_text(encoding="utf8")
    return guest.encode(), probe.encode()


def retire_lab():
    # The caller starts with an empty lab and owns every generated artifact.
    assert AREA.resolve() == (ROOT / "tmp/lab-current").resolve()
    entries = sorted(AREA.rglob("*"), key=lambda path: len(path.parts), reverse=True)
    for path in entries:
        assert not path.is_symlink() and path.resolve().is_relative_to(AREA.resolve()), path
        if path.is_dir():
            path.rmdir()
        else:
            path.unlink()


def run(report, destination, trace_allocation=False):
    assert not list(AREA.iterdir()) and not destination.exists()
    prior = read(QA)
    assert prior["passed"] and sha(Path(COMPILER)) == prior["compiler"]["sha256"]
    assert sha(LIB) == prior["private_input_sha256"][LIB.relative_to(ROOT).as_posix()]
    exe = AREA / "recovery-host128.exe"
    dll = AREA / "recovery-host-dsp.dll"
    guest = AREA / "engine_guest.rs"
    probe = AREA / "engine_probe.rs"
    circuit = AREA / "librf_d_circuit.rlib"
    sdk = AREA / "librackforge_plugin_sdk.rlib"
    dsp_package, silent_package = AREA / "package-dsp", AREA / "package-control"
    cache = AREA / "engine-cache"
    deps = HOST / "target/release/deps"
    asio_dir = HOST / "target/release/build/asio-sys-bb9248db199c7ec7/out"
    cpal, = deps.glob("libcpal-*.rlib")
    windows = deps / "libwindows-30e5b7032d286333.rlib"
    registry = Path(COMPILER).parents[4] / ".cargo/registry/src"
    windows_imports = sorted(registry.glob("*/windows_x86_64_msvc-*/lib/*.lib"))
    native_libs = sorted((HOST / "target/release/build").glob("*/out/*.lib"))
    native_dirs = sorted({p.parent for p in [*native_libs, *windows_imports]})
    host_sources = [
        REALTIME, "crates/rackforge-plugin-sdk/src/lib.rs", "crates/rackforge-core/src/hosted.rs",
        "crates/rackforge-core/src/rack_voice.rs", "crates/rackforge-core/src/parallel_render.rs",
        "crates/rackforge-plugin-runtime/src/native.rs", "apps/rackforge-desktop/src/desktop_audio.rs",
    ]
    host_head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=HOST, text=True).strip()
    for name in host_sources:
        frozen = subprocess.check_output(["git", "show", f"{host_head}:{name}"], cwd=HOST)
        assert (HOST / name).read_bytes() in (frozen, frozen.replace(b"\n", b"\r\n")), name
    report.update(
        previous_qa_sha256=sha(ROOT / QA), host_checkout=host_head,
        host_checkout_source_sha256={name: sha(HOST / name) for name in host_sources},
        dependencies={str(p): sha(p) for p in [
            Path(COMPILER), HOST_COMPILER, LIB, cpal, windows, deps / HOST_CORE,
            asio_dir / "asio.lib", asio_dir / "asio_bindings.rs",
            *deps.glob("librackforge_plugin_runtime-*.rlib"), *deps.glob("libwasmtime-*.rlib"),
            *native_libs, *windows_imports,
        ]},
    )
    rows_path = AREA / "engine-rows.bin"
    env = dict(os.environ, PATH="C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;" + os.environ["PATH"],
               RF_D_ENGINE_ROWS=str(rows_path))
    command, result = [], None

    def execute(args, timeout=95):
        nonlocal command, result
        command, result = list(map(str, args)), None
        result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, timeout=timeout)
        assert result.returncode == 0, result.stderr.decode(errors="replace")
        return result

    try:
        guest_bytes, probe_bytes = sources_for_build()
        guest.write_bytes(guest_bytes)
        probe.write_bytes(probe_bytes)
        make_package(dsp_package)
        make_package(silent_package)
        flags = ["-C", "opt-level=2", "-A", "dead_code", "-A", "unused_imports"]
        wasm = ["--target", "wasm32-unknown-unknown", "-C", "target-feature=+simd128"]
        wasm_link = ["--crate-type", "cdylib", "-C", "link-arg=-zstack-size=8388608", "-C", "panic=abort"]
        trace_flags = ["--cfg", "engine_alloc_trace", "-C", "debuginfo=1"] if trace_allocation else []
        report["build"] = []
        for args in [
            [COMPILER, "--edition=2021", *flags, "--crate-type", "cdylib", ROOT / DSP,
             "--extern", f"rf_d_circuit={LIB}", "-o", dll],
            [COMPILER, "--edition=2021", *flags, *wasm, "--crate-type", "rlib", "--crate-name", "rf_d_circuit",
             ROOT / "crates/rf-d-circuit/src/lib.rs", "-o", circuit],
            [COMPILER, "--edition=2024", *flags, *wasm, "--crate-type", "rlib", "--crate-name", "rackforge_plugin_sdk",
             HOST / "crates/rackforge-plugin-sdk/src/lib.rs", "-o", sdk],
            *[[COMPILER, "--edition=2021", *flags, *wasm, *wasm_link, guest,
               "--extern", f"rf_d_circuit={circuit}", "--extern", f"rackforge_plugin_sdk={sdk}",
               *(["--cfg", "engine_silence"] if path == silent_package else []), "-o", path / "component.wasm"]
              for path in [dsp_package, silent_package]],
            [HOST_COMPILER, "--edition=2021", *flags, "--cfg", "asio128", *trace_flags,
             "-L", f"dependency={deps}", *[arg for p in native_dirs for arg in ("-L", f"native={p}")],
             "-L", f"native={asio_dir}", "-l", "static=asio", probe,
             "--extern", f"cpal={cpal}", "--extern", f"windows={windows}",
             "--extern", f"rackforge_core={deps / HOST_CORE}", "-o", exe],
        ]:
            built = execute(args)
            report["build"].append(dict(command=command, stderr=packed(built.stderr)))
        report["artifact_sha256"] = {p.relative_to(AREA).as_posix(): sha(p) for p in [
            guest, probe, sdk, circuit, dll, exe, *dsp_package.rglob("*.*"), *silent_package.rglob("*.*"),
        ]}
        if trace_allocation:
            traced = execute([exe, "engine-allocation", silent_package, cache])
            stack = traced.stderr.decode(errors="replace")
            assert "ENGINE_ALLOC " in stack
            report.update(passed=True, allocation_trace=stack, log=traced.stdout.decode(errors="replace"),
                          scope="offline silent PluginInstance, 128 frames, after four warm calls")
            return
        fixture = execute([exe, "engine-fixtures", dsp_package, cache])
        fixture_raw = rows_path.read_bytes()
        report["fixtures"] = dict(rows=packed(fixture_raw), sha256=digest(fixture_raw),
                                  metrics=engine_fixture(fixture_raw), stream=fixture.stderr.decode(),
                                  log=fixture.stdout.decode(errors="replace"))
        print("ENGINE128_FIXTURE", report["fixtures"]["metrics"], flush=True)

        profile = asio_profile(exe)
        original = read_override(profile)
        initial = execute([exe, "asio-query", ASIO_DRIVER]).stdout.decode().strip()
        report["banks"] = []
        try:
            for mode, blocks in PLAN:
                bank = dict(mode=mode, blocks=blocks, runs=[])
                report["banks"].append(bank)
                bank_env = dict(env, RF_D_ENGINE_ROUTE=mode, RF_D_ENGINE_CACHE=str(cache),
                                RF_D_ENGINE_PACKAGE=str(silent_package if mode == "control" else dsp_package))
                args = [str(exe), "asio-bench", ASIO_DRIVER, str(blocks), "dsp"]
                for _ in range(2):
                    rows_path.unlink(missing_ok=True)
                    try:
                        measured = subprocess.run(args, cwd=ROOT, env=bank_env, capture_output=True, timeout=45)
                        log, stderr, status = measured.stdout, measured.stderr, measured.returncode
                    except subprocess.TimeoutExpired as error:
                        log, stderr, status = error.stdout or b"", error.stderr or b"", None
                    raw = rows_path.read_bytes() if rows_path.exists() else b""
                    stream = stderr.decode(errors="replace")
                    item = dict(exit_code=status, rows=packed(raw), sha256=digest(raw), stream=stream,
                                log=log.decode(errors="replace"))
                    if status == 0:
                        try:
                            item["metrics"] = analyze(raw, stream, blocks, mode)
                        except Exception:
                            item["analysis_failure"] = traceback.format_exc()
                    bank["runs"].append(item)
                    m = item.get("metrics", {})
                    print("ENGINE128_BANK", mode, blocks, len(bank["runs"]), status,
                          {k: m.get(k) for k in ["frames_128_confirmed", "deadline_misses", "margin_exceeded",
                                                  "wall_ns", "host_allocations", "slot_faults", "notices"]},
                          stream.strip() if not m else "", flush=True)
                    if m.get("gate_passed"):
                        break
        finally:
            changed = read_override(profile)
            restore_override(profile, original)
            final = execute([exe, "asio-query", ASIO_DRIVER]).stdout.decode().strip()
            report["asio_profile"] = dict(before=initial, verified=final, original=original, during=changed)
            assert initial == final and read_override(profile) == original
        report["cached_artifacts"] = {p.relative_to(cache).as_posix(): sha(p)
                                      for p in cache.rglob("*") if p.is_file()}
        report["rack_128_admitted"] = all(b["runs"][0].get("metrics", {}).get("gate_passed", False)
                                          for b in report["banks"])
        report.update(passed=True, whole_voice_rt=False)
    except Exception as error:
        report["failure"] = traceback.format_exc()
        if isinstance(error, subprocess.TimeoutExpired):
            report["timeout"] = dict(seconds=error.timeout, stdout=packed(error.stdout or b""),
                                     stderr=packed(error.stderr or b""))
        if result is not None:
            report["failed_output"] = dict(exit_code=result.returncode, stdout=packed(result.stdout),
                                           stderr=packed(result.stderr), command=command)
        if command:
            try:
                replay = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, timeout=95)
                report["unchanged_failure_replay"] = dict(exit_code=replay.returncode,
                                                           stdout=packed(replay.stdout), stderr=packed(replay.stderr))
            except subprocess.TimeoutExpired as replay:
                report["unchanged_failure_replay"] = dict(timeout_s=replay.timeout,
                    stdout=packed(replay.stdout or b""), stderr=packed(replay.stderr or b""))
    finally:
        write(destination, report)
        retire_lab()
        report["temporary_area_empty"] = not list(AREA.iterdir())
        write(destination, report)


if __name__ == "__main__":
    sources = Sources([
        "tools/check_recovery_engine128.py", DSP, GUEST, ENGINE_PROBE, ASIO_PROBE, PREVIOUS_PROBE, PROBE,
        "tools/recovery_cost_exp_kernel.rs", "tools/recovery_cost_exp_data.rs",
        "crates/rf-d-circuit/src/j7_stream_output.rs", "docs/RECOVERY_ENGINE128_PROTOCOLO.md",
    ])
    assert sys.argv[1:] in ([], ["--alloc-trace"])
    trace_allocation = sys.argv[1:] == ["--alloc-trace"]
    kind = "alloc" if trace_allocation else "native"
    number = 1
    while (ROOT / f"evidence/recovery_engine128_{kind}{number:02d}.json").exists():
        number += 1
    report = dict(passed=False, **sources.fields())
    run(report, ROOT / f"evidence/recovery_engine128_{kind}{number:02d}.json", trace_allocation)
    sources.unchanged()
    print("ENGINE128_FINAL", report["passed"], report.get("rack_128_admitted"), report.get("failure", ""), flush=True)
    if not report["passed"]:
        raise SystemExit(1)
