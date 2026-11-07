// Appended to the frozen Windows/ASIO measurement harness.
use rackforge_core::{
    LoadedPlugin, PluginInstance, PluginPackage,
    parallel_render::{MAX_RENDER_SLOTS, RenderPool, RenderTelemetry},
    rack_voice::{RackEngine, RackSlotRuntimeSpec, RackSlotStateLoad},
};
use std::{alloc::{GlobalAlloc, Layout, System}, cell::Cell, collections::BTreeMap, path::Path};

thread_local! { static HOST_ALLOCS: Cell<u64> = const { Cell::new(0) }; }

struct ThreadAllocator;
unsafe impl GlobalAlloc for ThreadAllocator {
    unsafe fn alloc(&self, layout: Layout) -> *mut u8 {
        let _ = HOST_ALLOCS.try_with(|n| n.set(n.get() + 1));
        #[cfg(engine_alloc_trace)]
        trace_engine_allocation(layout.size());
        unsafe { System.alloc(layout) }
    }
    unsafe fn dealloc(&self, p: *mut u8, layout: Layout) {
        unsafe { System.dealloc(p, layout) }
    }
    unsafe fn realloc(&self, p: *mut u8, layout: Layout, size: usize) -> *mut u8 {
        let _ = HOST_ALLOCS.try_with(|n| n.set(n.get() + 1));
        #[cfg(engine_alloc_trace)]
        trace_engine_allocation(size);
        unsafe { System.realloc(p, layout, size) }
    }
}
#[global_allocator]
static HOST_ALLOCATOR: ThreadAllocator = ThreadAllocator;

#[cfg(engine_alloc_trace)]
thread_local! {
    static TRACE_ARMED: Cell<bool> = const { Cell::new(false) };
    static ALLOC_TRACE: std::cell::RefCell<Option<(usize, std::backtrace::Backtrace)>> =
        const { std::cell::RefCell::new(None) };
}

#[cfg(engine_alloc_trace)]
fn trace_engine_allocation(size: usize) {
    if TRACE_ARMED.try_with(|armed| armed.replace(false)).unwrap_or(false) {
        let backtrace = std::backtrace::Backtrace::force_capture();
        ALLOC_TRACE.with(|slot| *slot.borrow_mut() = Some((size, backtrace)));
    }
}

#[cfg(engine_alloc_trace)]
fn engine_allocation_trace(package: &Path, cache: &Path) -> HostResult<()> {
    let mut work = EngineWork::load("instance", package, cache)?;
    work.silence = true;
    for _ in 0..4 {
        assert!(work.render(128) >= 0);
    }
    let rendered = match &mut work.route {
        EngineRoute::Instance(instance) => {
            TRACE_ARMED.with(|armed| armed.set(true));
            instance.process_interleaved(&[], &mut work.output, 128, 0, 2, &[], &[])
        }
        _ => unreachable!(),
    };
    TRACE_ARMED.with(|armed| armed.set(false));
    rendered?;
    let (size, backtrace) = ALLOC_TRACE.with(|slot| slot.take()).ok_or("No allocation captured")?;
    eprintln!("ENGINE_ALLOC {size}\n{backtrace}");
    Ok(())
}

trait LabRender {
    fn render(&mut self, frames: usize) -> i32;
}

impl LabRender for Dsp {
    fn render(&mut self, frames: usize) -> i32 { Dsp::render(self, frames) }
}

enum EngineRoute {
    Native(Dsp),
    Instance(PluginInstance<'static>),
    Rack { rack: RackEngine<'static>, pool: RenderPool },
}

struct EngineWork {
    route: EngineRoute,
    output: [f32; 256],
    startup: usize,
    calls: usize,
    allocations: u64,
    first_allocations: u64,
    allocated_blocks: usize,
    silence: bool,
}

impl EngineWork {
    fn load(mode: &str, package_path: &Path, cache: &Path) -> HostResult<Self> {
        let route = if mode == "native" {
            EngineRoute::Native(Dsp::new(Api::load()?))
        } else {
            let package = PluginPackage::open(package_path)?;
            let loaded = unsafe { LoadedPlugin::load(&package, None, &BTreeMap::new(), Some(cache))? };
            // The plugin owns the module for this short-lived lab process.
            let plugin: &'static LoadedPlugin = Box::leak(Box::new(loaded));
            if mode == "instance" {
                let mut instance = plugin.create_instance()?;
                instance.activate(48000., 128, 0, 2)?;
                assert!(instance.is_portable());
                assert_eq!(instance.latency_frames()?, 48);
                EngineRoute::Instance(instance)
            } else {
                assert!(matches!(mode, "rack" | "control"));
                let id = plugin.manifest().id.clone();
                let spec = RackSlotRuntimeSpec {
                    slot_id: "rf-d-lab".into(), plugin_id: id.clone(), state: RackSlotStateLoad::Default,
                    midi_stages: vec![], audio_sources: vec![], sends_to_main: true,
                    level_per_mille: 1000, pan_per_mille: 0,
                };
                let rack = RackEngine::build(&BTreeMap::from([(id, plugin)]), &[spec], 48000, 128, 2)?;
                let pool = RenderPool::automatic(RenderTelemetry::new(MAX_RENDER_SLOTS));
                EngineRoute::Rack { rack, pool }
            }
        };
        Ok(Self {
            route, output: [0.; 256], startup: 48, calls: 0, allocations: 0,
            first_allocations: 0, allocated_blocks: 0, silence: mode == "control",
        })
    }

    fn from_env() -> HostResult<Self> {
        let mode = std::env::var("RF_D_ENGINE_ROUTE")?;
        let package = std::env::var_os("RF_D_ENGINE_PACKAGE").ok_or("Missing package")?;
        let cache = std::env::var_os("RF_D_ENGINE_CACHE").ok_or("Missing cache directory")?;
        Self::load(&mode, Path::new(&package), Path::new(&cache))
    }

    fn report(&self) {
        let (mut faults, mut misses, mut host_blocks, mut host_max) = (0, 0, 0, 0);
        if let EngineRoute::Rack { pool, .. } = &self.route {
            let snapshot = pool.telemetry().snapshot_and_reset();
            faults = snapshot.slot_faults.iter().sum();
            misses = snapshot.deadline_misses;
            host_blocks = snapshot.block.count;
            host_max = snapshot.block.max_ns;
        }
        eprintln!("ENGINE128\t{}\t{}\t{}\t{}\t{faults}\t{misses}\t{host_blocks}\t{host_max}",
            self.calls, self.allocations, self.first_allocations, self.allocated_blocks);
    }
}

impl LabRender for EngineWork {
    fn render(&mut self, frames: usize) -> i32 {
        if !(1..=128).contains(&frames) {
            return -5;
        }
        let output = &mut self.output[..frames * 2];
        let padding = self.startup.min(frames);
        let before = HOST_ALLOCS.with(Cell::get);
        let ok = match &mut self.route {
            EngineRoute::Native(dsp) => {
                let result = dsp.render(frames);
                if result >= 0 {
                    output[..padding * 2].fill(0.);
                    for (frame, value) in output[padding * 2..].chunks_exact_mut(2)
                        .zip(&dsp.filtered[..result as usize])
                    {
                        frame.fill(*value as f32);
                    }
                }
                result == (frames - padding) as i32
            }
            EngineRoute::Instance(instance) => instance.process_interleaved(
                &[], output, frames as u32, 0, 2, &[], &[],
            ).is_ok(),
            EngineRoute::Rack { rack, pool } => {
                let telemetry = pool.telemetry().clone();
                rack.render(pool, &telemetry, frames as u32, frames as u64 * 1_000_000_000 / 48000,
                            None, output).is_ok()
            }
        };
        let allocated = HOST_ALLOCS.with(Cell::get) - before;
        self.allocations += allocated;
        self.allocated_blocks += usize::from(allocated != 0);
        if self.calls == 0 {
            self.first_allocations = allocated;
        }
        self.calls += 1;
        self.startup -= padding;
        if !ok || output.iter().any(|x| !x.is_finite())
            || (!self.silence && frames > padding && output.iter().all(|x| *x == 0.))
            || (self.silence && output.iter().any(|x| *x != 0.))
        {
            return -6;
        }
        std::hint::black_box(output);
        (frames - padding) as i32
    }
}

fn engine_rows() -> io::Result<io::BufWriter<std::fs::File>> {
    let path = std::env::var_os("RF_D_ENGINE_ROWS")
        .ok_or_else(|| io::Error::new(io::ErrorKind::NotFound, "Missing lab rows path"))?;
    Ok(io::BufWriter::new(std::fs::File::create(path)?))
}

fn engine_fixtures(package: &Path, cache: &Path) -> HostResult<()> {
    let mut out = engine_rows()?;
    for mode in ["native", "instance", "rack"] {
        let mut work = EngineWork::load(mode, package, cache)?;
        for _ in 0..16 {
            if work.render(128) < 0 {
                return Err(format!("Fixture render failed for {mode}").into());
            }
            for sample in work.output {
                out.write_all(&sample.to_le_bytes())?;
            }
        }
        work.report();
    }
    out.flush()?;
    Ok(())
}
