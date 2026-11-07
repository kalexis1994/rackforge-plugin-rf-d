"""Time the RackForge portable plugin path against the actual ASIO period."""

import argparse
import json
import os
import subprocess
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
EXP_KERNEL = "tools/recovery_cost_exp_kernel.rs"
COLUMNS_KERNEL = "tools/recovery_engine128_columns.rs"
BROADCAST_KERNEL = "tools/recovery_engine128_broadcast.rs"
SPLIT_FIR = "tools/recovery_cost_split_fir.rs"
HOT_KERNEL = "tools/recovery_engine128_hot.rs"
MODEL_KERNEL = "tools/recovery_engine128_model.rs"
ELIMINATE_KERNEL = "tools/recovery_engine128_eliminate.rs"
REGISTER_KERNEL = "tools/recovery_engine128_registers.rs"
SCHEDULE_PROBE = "tools/recovery_engine128_schedule.rs"
SCHEDULE_DRIVER = "tools/check_recovery_engine128_schedule.py"
SMT_PROBE = "tools/recovery_engine128_smt.rs"
SMT_DRIVER = "tools/check_recovery_engine128_smt.py"
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


def column_kernel(broadcast=False, hot=False, specialize=False, column_solve=False, registers=False):
    assert not hot or broadcast
    assert not specialize or hot
    assert not column_solve or specialize
    assert not registers or specialize
    source = (ROOT / EXP_KERNEL).read_text(encoding="utf8")
    data = (ROOT / "tools/recovery_cost_exp_data.rs").as_posix()
    columns = (ROOT / COLUMNS_KERNEL).as_posix()
    source = replace_once(source, '#[path="recovery_cost_exp_data.rs"]mod data;',
                          f'#[path="{data}"]mod data;\n#[path="{columns}"]mod columns;')
    source = replace_once(source, """        for j in 0..18 {base[k]+=data::F[i][k][j]*s.q[j];}
        for j in 0..12 {base[k]+=data::N0[i][k][j]*s.defects[j];}
    }""", """    }
    columns::accumulate::<18, 18, false>(&mut base, &columns::F[i], &s.q);
    columns::accumulate::<18, 12, false>(&mut base, &columns::N0[i], &s.defects);""")
    source = replace_once(source, """    let mut zp=[0.;12];
    for k in 0..12 {
        zp[k]=data::ZU[i][k]*u;
        for j in 0..18 {zp[k]+=data::ZH[i][k][j]*base[j];}
    }""", """    let mut zp=data::ZU[i].map(|coefficient| coefficient*u);
    columns::accumulate::<12, 18, false>(&mut zp, &columns::ZH[i], &base);""")
    source = replace_once(source, "    for k in 0..12 {for j in 0..12 {z[k]-=data::P[i][k][j]*s.defects[j];}}",
                          "    columns::accumulate::<12, 12, true>(&mut z, &columns::P[i], &s.defects);")
    source = replace_once(source, """        let mut r=[0.;12];let mut maximum=0_f64;
        for k in 0..12 {r[k]=z[k]-zp[k];for j in 0..12 {r[k]+=data::P[i][k][j]*n[j];}maximum=maximum.max(r[k].abs());}""",
                          """        let mut r=std::array::from_fn(|k| z[k]-zp[k]);
        columns::accumulate::<12, 12, false>(&mut r, &columns::P[i], &n);
        let maximum=r.iter().fold(0_f64, |maximum, value| maximum.max(value.abs()));""")
    source = replace_once(source,
                          "            for k in 0..18 {for j in 0..12 {q[k]+=data::N1[i][k][j]*n[j];}if !q[k].is_finite(){return Err(Error::Domain)}}",
                          """            columns::accumulate::<18, 12, false>(&mut q, &columns::N1[i], &n);
            if q.iter().any(|value| !value.is_finite()) {return Err(Error::Domain)}""")
    if broadcast:
        module = (ROOT / BROADCAST_KERNEL).as_posix()
        source = replace_once(source, "mod columns;", f'mod columns;\n#[path="{module}"]mod broadcast;')
        for rows, cols, subtract in [(18, 18, "false"), (18, 12, "false"), (12, 18, "false"),
                                     (12, 12, "true"), (12, 12, "false")]:
            source = source.replace(f"columns::accumulate::<{rows}, {cols}, {subtract}>",
                                    f"broadcast::accumulate::<{rows}, {cols}, {rows // 2}, {subtract}>")
        assert "columns::accumulate" not in source and source.count("broadcast::accumulate") == 6
    if hot:
        module = (ROOT / HOT_KERNEL).as_posix()
        start = source.index("pub fn law(")
        end = source.index("// The physical state is q.")
        source = (source[:start] + f'#[path="{module}"]mod hot;\npub use hot::law;\nuse hot::solve;\n\n'
                  + source[end:])
        source = replace_once(source,
                              "let bus=node(&candidate,66);let input_base=node(&candidate,6);let j7=node(&candidate,61);",
                              "let [bus, input_base, j7, _]=hot::ports(i,u,&base,&n);")
    if specialize:
        module = (ROOT / MODEL_KERNEL).as_posix()
        source = replace_once(source, "use hot::solve;", f'use hot::solve;\n#[path="{module}"]mod model;')
        start = source.index("pub fn step_with_budget(")
        end = source.index("    if i>=3", start)
        source = source[:start] + """pub fn step_with_budget(s: &mut State, u: f64, budget: usize) -> Result<Ports, Error> {
    if s.index == 1 {
        project::<1, _>(s, u, budget, |ports, _, _, _| ports)
    } else {
        project::<3, _>(s, u, budget, |ports, _, _, _| ports)
    }
}

pub fn inspect(s: &mut State, u: f64, budget: usize) -> Result<(Ports, [f64; 12], usize, f64), Error> {
    project::<3, _>(s, u, budget, |ports, z, iteration, residual| (ports, z, iteration, residual))
}

fn project<const MODEL: usize, T>(
    s: &mut State,
    u: f64,
    budget: usize,
    output: impl FnOnce(Ports, [f64; 12], usize, f64) -> T,
) -> Result<T, Error> {
    let i = if MODEL < 3 { MODEL } else { s.index };
""" + source[end:]
        source = replace_once(source, "s.q.iter().any(|v|!v.is_finite())", "!model::finite(&s.q)")
        source = replace_once(source, "q.iter().any(|value| !value.is_finite())", "!model::finite(&q)")
        source = replace_once(source, "return Ok((Ports{", "return Ok(output(Ports{")
        source = replace_once(source,
            "        for k in 0..6 {let mut odd=r[2*k+1];for j in 0..6 {odd-=data::P[i][2*k+1][2*j]*slope[2*j]*even[j];}z[2*k]-=even[k];z[2*k+1]-=odd;}",
            "        model::update(i, &mut z, &r, &slope, &even);")
    if column_solve:
        module = (ROOT / ELIMINATE_KERNEL).as_posix()
        source = replace_once(source, "use hot::solve;", f'#[path="{module}"]mod eliminate;')
        start = source.index("        let a=std::array::from_fn(")
        end = source.index("        model::update", start)
        source = source[:start] + "        let even=eliminate::solve(i, &slope, &r)?;\n" + source[end:]
    if registers:
        source = replace_once(source, (ROOT / BROADCAST_KERNEL).as_posix(), (ROOT / REGISTER_KERNEL).as_posix())
    return source.encode()


def sources_for_build(kernel=ROOT / EXP_KERNEL, split_fir=False, schedule=False, smt=False):
    assert not smt or schedule
    guest = (ROOT / DSP).read_text(encoding="utf8")
    for original, absolute in [
        ("recovery_cost_exp_kernel.rs", kernel),
        ("../crates/rf-d-circuit/src/j7_stream_output.rs",
         ROOT / (SPLIT_FIR if split_fir else "crates/rf-d-circuit/src/j7_stream_output.rs")),
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
    if schedule:
        entry = replace_once(entry, "    let _com = Com::init()?;", """    match args.first().map(String::as_str) {
        Some("schedule-topology") => return schedule_topology(),
        Some("schedule-calibration") => return schedule_calibration(),
        Some("schedule-offline") => return schedule_offline(args[1].parse()?),
        _ => {}
    }
    let _com = Com::init()?;""")
        asio = replace_once(asio, "    capture: Capture,", "    capture: Capture,\n    schedule: ScheduleCapture,")
        asio = replace_once(asio, "        capture: Capture::new(blocks),",
                            "        capture: Capture::new(blocks),\n        schedule: ScheduleCapture::new(blocks)?,")
        asio = replace_once(asio, "        unsafe { *session.posture.get() = (policy, throttle); }",
                            """        if session.schedule.cpu.is_some_and(|cpu| schedule_pin(cpu).is_err()) {
            ASIO_ERRORS.fetch_add(1, Ordering::Relaxed);
            return;
        }
        unsafe { *session.posture.get() = (policy, throttle); }""")
        asio = replace_once(asio, "    let before = cycles();",
                            "    let before = cycles();\n    let whole_cpu_before = thread_cpu_ns();")
        asio = replace_once(asio,
            "        Some(measure(session.origin, HOST_FRAMES as usize, &mut [], dsp.as_mut(), setup_ns, policy, throttle))",
            """        let render_cpu = thread_cpu_ns();
        let render_cycles = cycles();
        let render_start = Instant::now();
        let row = measure(session.origin, HOST_FRAMES as usize, &mut [], dsp.as_mut(), setup_ns, policy, throttle);
        let marker = [ns(render_start.elapsed()), schedule_delta(render_cycles, cycles()),
                      schedule_delta(render_cpu, thread_cpu_ns()), 0];
        unsafe { *session.schedule.markers[index].get() = marker; }
        Some(row)""")
        asio = replace_once(asio, "    let after = cycles();",
                            "    let whole_cpu = schedule_delta(whole_cpu_before, thread_cpu_ns());\n    let after = cycles();")
        asio = replace_once(asio, "        session.capture.publish(index, row);",
                            "        unsafe { (*session.schedule.markers[index].get())[3] = whole_cpu; }\n"
                            "        session.capture.publish(index, row);")
        asio = replace_once(asio, "row.into_iter().chain(extra)", """row.into_iter().chain(extra)
            .chain(unsafe { *session.schedule.markers[index].get() })""")
    if smt:
        entry = replace_once(entry, '        Some("schedule-topology") => return schedule_topology(),',
                             '        Some("schedule-topology") => return schedule_topology(),\n'
                             '        Some("smt-endpoints") => return smt_endpoints(&args[1]),')
        asio = replace_once(asio, "    schedule: ScheduleCapture,", "    schedule: ScheduleCapture,\n    smt: Option<SmtCapture>,")
        asio = replace_once(asio, "    let mut session = Box::new(AsioSession {",
                            "    let (mut planner, smt) = smt_prepare(blocks)?;\n    let mut session = Box::new(AsioSession {")
        asio = replace_once(asio, "        schedule: ScheduleCapture::new(blocks)?,",
                            "        schedule: ScheduleCapture::new(blocks)?,\n        smt,")
        asio = replace_once(asio, """    let cpu_before = unsafe { GetCurrentProcessorNumber() };
    let before = cycles();""", """    let before = cycles();
    if recording {
        if let Some(smt) = &session.smt {
            if smt.apply(index).is_err() {
                ASIO_ERRORS.fetch_add(1, Ordering::Relaxed);
                return;
            }
        }
    }
    let cpu_before = unsafe { GetCurrentProcessorNumber() };""")
        asio = replace_once(asio, """    if start_result == 0 {
        while session.capture.completed.load(Ordering::Acquire) < blocks && Instant::now() < expires {
            std::thread::sleep(Duration::from_millis(5));
        }
    }""", """    let mut smt_error = None;
    if start_result == 0 {
        loop {
            let completed = session.capture.completed.load(Ordering::Acquire);
            if completed >= blocks || Instant::now() >= expires || ASIO_ERRORS.load(Ordering::Relaxed) != 0 {
                break;
            }
            if let (Some(planner), Some(capture)) = (&mut planner, &session.smt) {
                if let Err(error) = planner.tick(completed, capture, &session.capture, session.origin) {
                    smt_error = Some(error);
                    break;
                }
            } else {
                std::thread::sleep(Duration::from_millis(5));
            }
        }
    }""")
        asio = replace_once(asio, "    let session = unsafe { Box::from_raw(raw) };",
                            "    let session = unsafe { Box::from_raw(raw) };\n"
                            "    if let Some(planner) = &mut planner { planner.report(); }")
        asio = replace_once(asio, "            .chain(unsafe { *session.schedule.markers[index].get() })",
                            """            .chain(unsafe { *session.schedule.markers[index].get() })
            .chain(session.smt.as_ref().map_or([u64::MAX, 0], |smt| unsafe { *smt.rows[index].get() }))""")
        asio = replace_once(asio, '    asio_ok("ASIOStart", start_result)?;',
                            '    if let Some(error) = smt_error { return Err(error); }\n'
                            '    asio_ok("ASIOStart", start_result)?;')
    asio_dir = HOST / "target/release/build/asio-sys-bb9248db199c7ec7/out"
    probe += "\n" + entry + f'\n#[path = "{(asio_dir / "asio_bindings.rs").as_posix()}"]\nmod asio_ffi;\n'
    probe += asio + "\n" + (ROOT / ENGINE_PROBE).read_text(encoding="utf8")
    if schedule:
        probe += "\n" + (ROOT / SCHEDULE_PROBE).read_text(encoding="utf8")
    if smt:
        probe += "\n" + (ROOT / SMT_PROBE).read_text(encoding="utf8")
    return guest.encode(), probe.encode()


def retire_lab(keep=()):
    # The caller owns the lab; an optional Cargo build stays for the next pass.
    assert AREA.resolve() == (ROOT / "tmp/lab-current").resolve()
    entries = sorted(AREA.rglob("*"), key=lambda path: len(path.parts), reverse=True)
    for path in entries:
        if AREA / path.relative_to(AREA).parts[0] in keep:
            continue
        assert not path.is_symlink() and path.resolve().is_relative_to(AREA.resolve()), path
        if path.is_dir():
            path.rmdir()
        else:
            path.unlink()


def cargo_artifacts(build_log):
    rows = [json.loads(line) for line in build_log.read_text(encoding="utf8").splitlines()]
    assert rows[-1] == {"reason": "build-finished", "success": True}
    artifacts = {}
    for crate in ("rackforge_core", "rackforge_plugin_runtime", "wasmtime"):
        paths = [Path(name) for row in rows if row["reason"] == "compiler-artifact"
                 and row["target"]["name"] == crate for name in row["filenames"] if name.endswith(".rlib")]
        path, = paths
        # Cargo reports the hard-linked top-level output for the requested library.
        if path.parent.name == "release":
            path, = (path.parent / "deps").glob(f"{path.stem}-*.rlib")
        assert path.is_file() and path.resolve().is_relative_to(AREA.resolve())
        artifacts[crate] = path
    return artifacts


def run(report, destination, trace_allocation=False, host=HOST, host_build=None, wasm_opt=2,
        column_simd=False, broadcast_simd=False, split_fir=False, hot_simd=False, specialize=False,
        column_solve=False, lto=False, registers=False, schedule=False, schedule_survey=False,
        schedule_confirm=None, smt=False, smt_background=False, smt_qualified=False):
    assert not broadcast_simd or column_simd
    assert not split_fir or broadcast_simd
    assert not hot_simd or split_fir
    assert not specialize or hot_simd
    assert not column_solve or specialize
    assert not lto or specialize
    assert not registers or specialize
    assert not schedule or (registers and lto and not column_solve and host_build)
    assert not schedule or wasm_opt == (2 if smt or schedule_confirm is not None else 3)
    assert not schedule_survey or schedule
    assert schedule_confirm is None or (schedule and not schedule_survey)
    assert not smt or (schedule and not schedule_survey and schedule_confirm is None and not trace_allocation)
    assert not smt_background or smt
    assert not smt_qualified or (smt and not smt_background)
    keep = set(AREA.iterdir()) if host_build else set()
    assert not destination.exists() and (host_build or not list(AREA.iterdir()))
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
    rows_path = AREA / "engine-rows.bin"
    kernel = AREA / "engine_kernel_columns.rs" if column_simd else ROOT / EXP_KERNEL
    assert not keep.intersection((exe, dll, guest, probe, circuit, sdk, dsp_package,
                                  silent_package, cache, rows_path, kernel))
    platform_deps = HOST / "target/release/deps"
    asio_dir = HOST / "target/release/build/asio-sys-bb9248db199c7ec7/out"
    cpal, = platform_deps.glob("libcpal-*.rlib")
    windows = platform_deps / "libwindows-30e5b7032d286333.rlib"
    if host_build:
        assert host_build.parent == AREA and host_build.is_file()
        rebuilt = cargo_artifacts(host_build)
        core = rebuilt["rackforge_core"]
        deps = core.parent
        runtime_dependencies = list(rebuilt.values())
        report["host_build"] = dict(log=host_build.name, sha256=sha(host_build),
                                    libraries={name: sha(path) for name, path in rebuilt.items()})
    else:
        deps = platform_deps
        core = deps / HOST_CORE
        runtime_dependencies = [core, *deps.glob("librackforge_plugin_runtime-*.rlib"),
                                *deps.glob("libwasmtime-*.rlib")]
    registry = Path(COMPILER).parents[4] / ".cargo/registry/src"
    windows_imports = sorted(registry.glob("*/windows_x86_64_msvc-*/lib/*.lib"))
    native_libs = sorted((deps.parent / "build").glob("*/out/*.lib"))
    platform_libs = sorted((HOST / "target/release/build").glob("*/out/*.lib"))
    native_dirs = list(dict.fromkeys(p.parent for p in [*native_libs, *platform_libs, *windows_imports]))
    host_sources = [
        REALTIME, "crates/rackforge-plugin-sdk/src/lib.rs", "crates/rackforge-core/src/hosted.rs",
        "crates/rackforge-core/src/rack_voice.rs", "crates/rackforge-core/src/parallel_render.rs",
        "crates/rackforge-plugin-runtime/src/native.rs", "apps/rackforge-desktop/src/desktop_audio.rs",
    ]
    host_head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=host, text=True).strip()
    for name in host_sources:
        frozen = subprocess.check_output(["git", "show", f"{host_head}:{name}"], cwd=host)
        assert (host / name).read_bytes() in (frozen, frozen.replace(b"\n", b"\r\n")), name
    assert (host / REALTIME).read_bytes() == (HOST / REALTIME).read_bytes()
    report.update(
        previous_qa_sha256=sha(ROOT / QA), host_checkout=host_head, wasm_opt_level=wasm_opt,
        column_simd=column_simd, broadcast_simd=broadcast_simd, split_fir=split_fir, hot_simd=hot_simd,
        specialize=specialize, column_solve=column_solve, wasm_lto=lto, registers=registers,
        host_checkout_source_sha256={name: sha(host / name) for name in host_sources},
        dependencies={str(p): sha(p) for p in [
            Path(COMPILER), HOST_COMPILER, LIB, cpal, windows, *runtime_dependencies,
            asio_dir / "asio.lib", asio_dir / "asio_bindings.rs", *native_libs, *platform_libs, *windows_imports,
        ]},
    )
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
        if column_simd:
            kernel.write_bytes(column_kernel(broadcast_simd, hot_simd, specialize, column_solve, registers))
        guest_bytes, probe_bytes = sources_for_build(kernel, split_fir, schedule, smt)
        guest.write_bytes(guest_bytes)
        probe.write_bytes(probe_bytes)
        make_package(dsp_package)
        make_package(silent_package)
        flags = ["-C", "opt-level=2", "-A", "dead_code", "-A", "unused_imports"]
        wasm = ["--target", "wasm32-unknown-unknown", "-C", "target-feature=+simd128",
                "-C", f"opt-level={wasm_opt}"]
        dependency_dirs = list(dict.fromkeys((deps, platform_deps)))
        wasm_link = ["--crate-type", "cdylib", "-C", "link-arg=-zstack-size=8388608", "-C", "panic=abort"]
        if lto:
            wasm_link += ["-C", "lto=fat", "-C", "codegen-units=1"]
        trace_flags = ["--cfg", "engine_alloc_trace", "-C", "debuginfo=1"] if trace_allocation else []
        report["build"] = []
        for args in [
            [COMPILER, "--edition=2021", *flags, "--crate-type", "cdylib", ROOT / DSP,
             "--extern", f"rf_d_circuit={LIB}", "-o", dll],
            [COMPILER, "--edition=2021", *flags, *wasm, "--crate-type", "rlib", "--crate-name", "rf_d_circuit",
             ROOT / "crates/rf-d-circuit/src/lib.rs", "-o", circuit],
            [COMPILER, "--edition=2024", *flags, *wasm, "--crate-type", "rlib", "--crate-name", "rackforge_plugin_sdk",
             host / "crates/rackforge-plugin-sdk/src/lib.rs", "-o", sdk],
            *[[COMPILER, "--edition=2021", *flags, *wasm, *wasm_link, guest,
               "--extern", f"rf_d_circuit={circuit}", "--extern", f"rackforge_plugin_sdk={sdk}",
               *(["--cfg", "engine_silence"] if path == silent_package else []), "-o", path / "component.wasm"]
              for path in [dsp_package, silent_package]],
            [HOST_COMPILER, "--edition=2021", *flags, "--cfg", "asio128", *trace_flags,
             *[arg for p in dependency_dirs for arg in ("-L", f"dependency={p}")],
             *[arg for p in native_dirs for arg in ("-L", f"native={p}")],
             "-L", f"native={asio_dir}", "-l", "static=asio", probe,
             "--extern", f"cpal={cpal}", "--extern", f"windows={windows}",
             "--extern", f"rackforge_core={core}", "-o", exe],
        ]:
            built = execute(args)
            report["build"].append(dict(command=command, stderr=packed(built.stderr)))
        report["artifact_sha256"] = {p.relative_to(AREA).as_posix(): sha(p) for p in [
            guest, probe, sdk, circuit, dll, exe, *dsp_package.rglob("*.*"), *silent_package.rglob("*.*"),
            *([kernel] if column_simd else []),
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
        if smt:
            from check_recovery_engine128_smt import campaign
            campaign(report, exe, env, dsp_package, silent_package, cache, rows_path, analyze, execute,
                     background=smt_background, qualified=smt_qualified)
            report.update(passed=True, whole_voice_rt=False, rack_128_admitted=False)
            return
        if schedule:
            from check_recovery_engine128_schedule import campaign
            campaign(report, exe, env, dsp_package, silent_package, cache, rows_path, analyze, execute,
                     survey=schedule_survey, confirm_cpu=schedule_confirm)
            report.update(passed=True, whole_voice_rt=False, rack_128_admitted=report.get("free_128_admitted", False))
            return

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
                    if m.get("gate_passed") and not (hot_simd and blocks == 4800):
                        break
        finally:
            changed = read_override(profile)
            restore_override(profile, original)
            final = execute([exe, "asio-query", ASIO_DRIVER]).stdout.decode().strip()
            report["asio_profile"] = dict(before=initial, verified=final, original=original, during=changed)
            assert initial == final and read_override(profile) == original
        report["cached_artifacts"] = {p.relative_to(cache).as_posix(): sha(p)
                                      for p in cache.rglob("*") if p.is_file()}
        report["rack_128_admitted"] = all(run.get("metrics", {}).get("gate_passed", False)
                                          for bank in report["banks"] for run in bank["runs"])
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
        retire_lab(keep)
        report["temporary_area_empty"] = not list(AREA.iterdir())
        report["measurement_area_retired"] = set(AREA.iterdir()) == keep
        write(destination, report)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--alloc-trace", action="store_true")
    parser.add_argument("--host-checkout", type=Path, default=HOST)
    parser.add_argument("--host-build", type=Path, help="successful Cargo JSON build log in tmp/lab-current")
    parser.add_argument("--wasm-opt", type=int, choices=(2, 3), default=2)
    parser.add_argument("--column-simd", action="store_true")
    parser.add_argument("--broadcast-simd", action="store_true", help="share each input splat across all row pairs")
    parser.add_argument("--split-fir", action="store_true", help="use contiguous ring spans for the same FIR")
    parser.add_argument("--hot-simd", action="store_true", help="vectorize independent laws, elimination and ports")
    parser.add_argument("--specialize-model", action="store_true", help="specialize the nominal audio step and SIMD odd correction")
    parser.add_argument("--column-solve", action="store_true", help="eliminate the even system in SIMD across rows")
    parser.add_argument("--wasm-lto", action="store_true", help="use a single Wasm codegen unit and fat LTO")
    parser.add_argument("--register-simd", action="store_true", help="use explicit accumulators in the matrix maps")
    parser.add_argument("--schedule-study", action="store_true", help="compare the frozen package with and without ASIO")
    parser.add_argument("--schedule-survey", action="store_true", help="select one CPU before independent long passes")
    parser.add_argument("--schedule-confirm", type=int, help="repeat the selected placement with Wasm O2")
    parser.add_argument("--smt-study", action="store_true", help="control and confirm idle-aware ASIO affinity")
    parser.add_argument("--smt-background", action="store_true", help="apply adaptive affinity between callbacks")
    parser.add_argument("--smt-qualified", action="store_true", help="confirm fixed placement after a quiet-host preflight")
    args = parser.parse_args()
    if args.broadcast_simd and not args.column_simd:
        parser.error("--broadcast-simd requires --column-simd")
    if args.split_fir and not args.broadcast_simd:
        parser.error("--split-fir requires --broadcast-simd")
    if args.hot_simd and not args.split_fir:
        parser.error("--hot-simd requires --split-fir")
    if args.specialize_model and not args.hot_simd:
        parser.error("--specialize-model requires --hot-simd")
    if args.column_solve and not args.specialize_model:
        parser.error("--column-solve requires --specialize-model")
    if args.wasm_lto and not args.specialize_model:
        parser.error("--wasm-lto requires --specialize-model")
    if args.register_simd and not args.specialize_model:
        parser.error("--register-simd requires --specialize-model")
    if args.schedule_survey and not args.schedule_study:
        parser.error("--schedule-survey requires --schedule-study")
    if args.schedule_confirm is not None and (not args.schedule_study or args.schedule_survey):
        parser.error("--schedule-confirm requires --schedule-study without --schedule-survey")
    if args.smt_study and (not args.schedule_study or args.schedule_survey or args.schedule_confirm is not None):
        parser.error("--smt-study requires --schedule-study without a survey or fixed confirmation")
    if args.smt_background and not args.smt_study:
        parser.error("--smt-background requires --smt-study")
    if args.smt_qualified and (not args.smt_study or args.smt_background):
        parser.error("--smt-qualified requires --smt-study without --smt-background")
    sources = Sources([
        "tools/check_recovery_engine128.py", DSP, GUEST, ENGINE_PROBE, ASIO_PROBE, PREVIOUS_PROBE, PROBE,
        EXP_KERNEL, "tools/recovery_cost_exp_data.rs",
        "crates/rf-d-circuit/src/j7_stream_output.rs", "docs/RECOVERY_ENGINE128_PROTOCOLO.md",
        "docs/RECOVERY_ENGINE128_FUEL_PROTOCOLO.md",
        "docs/RECOVERY_ENGINE128_BROADCAST_PROTOCOLO.md",
        "docs/RECOVERY_ENGINE128_HOT_PROTOCOLO.md",
        *([COLUMNS_KERNEL] if args.column_simd else []),
        *([BROADCAST_KERNEL] if args.broadcast_simd else []),
        *([SPLIT_FIR] if args.split_fir else []),
        *([HOT_KERNEL] if args.hot_simd else []),
        *([MODEL_KERNEL] if args.specialize_model else []),
        *([ELIMINATE_KERNEL] if args.column_solve else []),
        *([REGISTER_KERNEL] if args.register_simd else []),
        *([SCHEDULE_PROBE, SCHEDULE_DRIVER, "docs/RECOVERY_ENGINE128_SCHED_PROTOCOLO.md"]
          if args.schedule_study else []),
        *([SMT_PROBE, SMT_DRIVER, "docs/RECOVERY_ENGINE128_SMT_PROTOCOLO.md"] if args.smt_study else []),
    ])
    kind = "smt" if args.smt_study else "schedule" if args.schedule_study else "alloc" if args.alloc_trace else "native"
    number = 1
    while (ROOT / f"evidence/recovery_engine128_{kind}{number:02d}.json").exists():
        number += 1
    report = dict(passed=False, **sources.fields())
    run(report, ROOT / f"evidence/recovery_engine128_{kind}{number:02d}.json",
        trace_allocation=args.alloc_trace, host=args.host_checkout.resolve(),
        host_build=args.host_build.resolve() if args.host_build else None, wasm_opt=args.wasm_opt,
        column_simd=args.column_simd, broadcast_simd=args.broadcast_simd, split_fir=args.split_fir,
        hot_simd=args.hot_simd, specialize=args.specialize_model, column_solve=args.column_solve,
        lto=args.wasm_lto, registers=args.register_simd, schedule=args.schedule_study,
        schedule_survey=args.schedule_survey, schedule_confirm=args.schedule_confirm, smt=args.smt_study,
        smt_background=args.smt_background, smt_qualified=args.smt_qualified)
    sources.unchanged()
    print("ENGINE128_FINAL", report["passed"], report.get("rack_128_admitted"), report.get("failure", ""), flush=True)
    if not report["passed"]:
        raise SystemExit(1)
