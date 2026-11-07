//! Windows lab callback using the same CPAL backend and thread policy as RackForge.
#[path = "../../rackforge/crates/rackforge-core/src/realtime.rs"]
mod realtime;

use cpal::traits::{DeviceTrait, HostTrait, StreamTrait};
use std::{
    cell::UnsafeCell,
    ffi::c_void,
    io::{self, Write},
    sync::{Arc, atomic::{AtomicUsize, Ordering}},
    time::{Duration, Instant},
};

#[link(name = "kernel32")]
unsafe extern "system" {
    fn LoadLibraryW(path: *const u16) -> *mut c_void;
    fn GetProcAddress(module: *mut c_void, name: *const u8) -> *const c_void;
    fn GetCurrentThread() -> *mut c_void;
    fn GetCurrentThreadId() -> u32;
    fn GetCurrentProcessorNumber() -> u32;
    fn QueryThreadCycleTime(thread: *mut c_void, cycles: *mut u64) -> i32;
}

type New = extern "C" fn() -> *mut c_void;
type Render = unsafe extern "C" fn(*mut c_void, usize, *mut f64, *mut f64) -> i32;
type Free = unsafe extern "C" fn(*mut c_void);

#[derive(Clone, Copy)]
struct Api {
    new: New,
    render: Render,
    free: Free,
}

impl Api {
    fn load() -> io::Result<Self> {
        use std::os::windows::ffi::OsStrExt;
        let path = std::env::current_exe()?.with_file_name("recovery-host-dsp.dll");
        let wide: Vec<u16> = path.as_os_str().encode_wide().chain([0]).collect();
        // The lab keeps this module loaded for the duration of the process.
        let module = unsafe { LoadLibraryW(wide.as_ptr()) };
        if module.is_null() {
            return Err(io::Error::last_os_error());
        }
        let address = |name: &[u8]| {
            let p = unsafe { GetProcAddress(module, name.as_ptr()) };
            if p.is_null() { Err(io::Error::last_os_error()) } else { Ok(p) }
        };
        // The GNU DLL exposes these signatures through the Windows x64 C ABI.
        unsafe {
            Ok(Self {
                new: std::mem::transmute::<*const c_void, New>(address(b"rf_new\0")?),
                render: std::mem::transmute::<*const c_void, Render>(address(b"rf_render\0")?),
                free: std::mem::transmute::<*const c_void, Free>(address(b"rf_free\0")?),
            })
        }
    }
}

struct Dsp {
    api: Api,
    handle: std::ptr::NonNull<c_void>,
    raw: [f64; 1024],
    filtered: [f64; 128],
}

impl Dsp {
    fn new(api: Api) -> Self {
        let handle = std::ptr::NonNull::new((api.new)()).expect("DSP allocation");
        Self { api, handle, raw: [0.; 1024], filtered: [0.; 128] }
    }

    fn render(&mut self, frames: usize) -> i32 {
        unsafe {
            (self.api.render)(self.handle.as_ptr(), frames, self.raw.as_mut_ptr(), self.filtered.as_mut_ptr())
        }
    }
}

impl Drop for Dsp {
    fn drop(&mut self) {
        unsafe { (self.api.free)(self.handle.as_ptr()) }
    }
}

// One closure owns the handle and transfers it to CPAL's serial callback.
// The DLL allocates and frees the same handle with its own allocator.
unsafe impl Send for Dsp {}

fn cycles() -> u64 {
    let mut count = 0;
    if unsafe { QueryThreadCycleTime(GetCurrentThread(), &mut count) } == 0 {
        return 0;
    }
    count
}

fn ns(duration: Duration) -> u64 {
    duration.as_nanos() as u64
}

type Row = [u64; 13];

struct Capture {
    rows: Box<[UnsafeCell<Row>]>,
    completed: AtomicUsize,
    errors: AtomicUsize,
}

// CPAL's FnMut closure is the sole writer. The main thread reads only after
// acquiring the final count. Each row is written once and stays immutable.
unsafe impl Sync for Capture {}

impl Capture {
    fn new(blocks: usize) -> Self {
        Self {
            rows: (0..blocks).map(|_| UnsafeCell::new([0; 13])).collect(),
            completed: AtomicUsize::new(0),
            errors: AtomicUsize::new(0),
        }
    }

    fn publish(&self, index: usize, row: Row) {
        unsafe { *self.rows[index].get() = row };
        self.completed.store(index + 1, Ordering::Release);
    }

    fn export(&self) -> io::Result<()> {
        let count = self.completed.load(Ordering::Acquire);
        let mut out = io::BufWriter::new(io::stdout().lock());
        for cell in &self.rows[..count] {
            for value in unsafe { *cell.get() } {
                out.write_all(&value.to_le_bytes())?;
            }
        }
        out.flush()
    }
}

fn measure(
    origin: Instant,
    frames: usize,
    data: &mut [f32],
    dsp: Option<&mut Dsp>,
    setup_ns: u64,
    policy: u64,
    throttle: u64,
) -> Row {
    let start = Instant::now();
    let cpu_before = unsafe { GetCurrentProcessorNumber() };
    let before = cycles();
    data.fill(0.);
    let mut produced = 0;
    let mut max128_ns = 0;
    let mut dsp_ns = 0;
    let mut dsp_error = 0;
    if let Some(dsp) = dsp {
        let mut left = frames;
        while left != 0 {
            let chunk = left.min(128);
            let begin = Instant::now();
            let result = dsp.render(chunk);
            let duration = ns(begin.elapsed());
            if result < 0 {
                dsp_error = (-result) as u64;
                break;
            }
            produced += result as u64;
            dsp_ns += duration;
            if chunk == 128 {
                max128_ns = max128_ns.max(duration);
            }
            left -= chunk;
        }
    }
    let after = cycles();
    let cpu_after = unsafe { GetCurrentProcessorNumber() };
    let wall_ns = ns(start.elapsed());
    let used_cycles = if before == 0 || after < before { u64::MAX } else { after - before };
    [
        ns(start.duration_since(origin)), wall_ns, used_cycles, frames as u64, produced,
        dsp_ns, max128_ns, cpu_before as u64, cpu_after as u64,
        unsafe { GetCurrentThreadId() } as u64, setup_ns, policy | (throttle << 8), dsp_error,
    ]
}

fn native(api: Api, blocks: usize) -> io::Result<()> {
    let capture = Capture::new(blocks);
    let mut dsp = Dsp::new(api);
    let origin = Instant::now();
    for block in 0..blocks {
        capture.publish(block, measure(origin, 128, &mut [], Some(&mut dsp), 0, 0, 0));
    }
    capture.export()
}

fn wasapi(
    api: Api,
    blocks: usize,
    process_dsp: bool,
    endpoint_name: Option<&str>,
) -> Result<(), Box<dyn std::error::Error>> {
    let host = cpal::host_from_id(cpal::HostId::Wasapi)?;
    let device = match endpoint_name {
        Some(name) => host.output_devices()?.find(|d| d.name().is_ok_and(|s| s == name)),
        None => host.default_output_device(),
    }.ok_or("No matching WASAPI output")?;
    let default = device.default_output_config()?;
    let preferred_channels = default.channels();
    let selected = device.supported_output_configs()?
        .filter(|c| c.sample_format() == cpal::SampleFormat::F32
            && c.min_sample_rate().0 <= 48000 && c.max_sample_rate().0 >= 48000)
        .min_by_key(|c| c.channels().abs_diff(preferred_channels))
        .ok_or("No f32 WASAPI configuration at 48 kHz")?;
    let mut config = selected.with_sample_rate(cpal::SampleRate(48000)).config();
    config.buffer_size = cpal::BufferSize::Fixed(128);
    let channels = config.channels as usize;
    let endpoint = device.name()?;
    eprintln!("OPEN\t{endpoint}\t{channels}\t48000\t128");
    let capture = Arc::new(Capture::new(blocks));
    let writer = capture.clone();
    let errors = capture.clone();
    let mut dsp = process_dsp.then(|| Dsp::new(api));
    let origin = Instant::now();
    let mut index = 0;
    let mut policy = 0;
    let mut throttle = 0;
    let stream = device.build_output_stream(
        &config,
        move |data: &mut [f32], _| {
            if index >= blocks {
                data.fill(0.);
                return;
            }
            let mut setup_ns = 0;
            if index == 0 {
                let start = Instant::now();
                let status = realtime::engage(realtime::DEFAULT_AUDIO_PRIORITY);
                policy = match status.scheduling {
                    realtime::SchedulingState::Boosted { class: "pro-audio" } => 1,
                    realtime::SchedulingState::Boosted { class: "time-critical" } => 2,
                    _ => 3,
                };
                throttle = if realtime::exempt_process_from_throttling()
                    == realtime::ThrottlingState::Exempt { 1 } else { 2 };
                setup_ns = ns(start.elapsed());
            }
            realtime::flush_subnormals();
            let frames = data.len() / channels;
            writer.publish(index, measure(origin, frames, data, dsp.as_mut(), setup_ns, policy, throttle));
            index += 1;
        },
        move |_| { errors.errors.fetch_add(1, Ordering::Relaxed); },
        None,
    )?;
    stream.play()?;
    let expires = Instant::now() + Duration::from_secs(115);
    while capture.completed.load(Ordering::Acquire) < blocks && Instant::now() < expires {
        std::thread::sleep(Duration::from_millis(10));
    }
    drop(stream);
    let complete = capture.completed.load(Ordering::Acquire);
    let errors = capture.errors.load(Ordering::Relaxed);
    eprintln!("WASAPI\t{endpoint}\t{channels}\t48000\t128\t{complete}\t{errors}");
    capture.export()?;
    if complete != blocks || errors != 0 {
        return Err("Incomplete or errored WASAPI stream".into());
    }
    Ok(())
}

fn fixtures(api: Api) -> io::Result<()> {
    let mut out = io::BufWriter::new(io::stdout().lock());
    for chunks in [[128, 128, 128, 128, 0, 0], [17, 96, 128, 127, 120, 24]] {
        let mut dsp = Dsp::new(api);
        let mut raw = [0.; 4096];
        let mut filtered = [0.; 512];
        let mut consumed = 0;
        let mut produced = 0;
        for chunk in chunks.into_iter().filter(|n| *n != 0) {
            let n = dsp.render(chunk);
            assert!(n >= 0);
            raw[consumed..consumed + chunk * 8].copy_from_slice(&dsp.raw[..chunk * 8]);
            filtered[produced..produced + n as usize].copy_from_slice(&dsp.filtered[..n as usize]);
            consumed += chunk * 8;
            produced += n as usize;
        }
        assert_eq!((consumed, produced), (4096, 464));
        for v in raw.into_iter().chain(filtered.into_iter().take(produced)) {
            out.write_all(&v.to_le_bytes())?;
        }
    }
    out.flush()
}

fn calibrate() {
    for mode in ["counter", "wait", "busy"] {
        for _ in 0..12 {
            let start = Instant::now();
            let before = cycles();
            match mode {
                "wait" => std::thread::sleep(Duration::from_millis(4)),
                "busy" => {
                    while start.elapsed() < Duration::from_millis(4) {
                        std::hint::spin_loop();
                    }
                }
                _ => {}
            }
            let after = cycles();
            println!("{mode},{},{}", ns(start.elapsed()), after.saturating_sub(before));
        }
    }
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let mut args = std::env::args().skip(1);
    let mode = args.next().ok_or("Expected bank name")?;
    if mode == "calibrate" {
        calibrate();
        return Ok(());
    }
    if mode == "devices" {
        let host = cpal::host_from_id(cpal::HostId::Wasapi)?;
        if let Some(device) = host.default_output_device() {
            println!("DEFAULT\t{}", device.name()?);
        }
        for device in host.output_devices()? {
            println!("OUTPUT\t{}", device.name()?);
        }
        return Ok(());
    }
    let api = Api::load()?;
    if mode == "fixtures" {
        return Ok(fixtures(api)?);
    }
    let blocks = args.next().ok_or("Expected block count")?.parse()?;
    let endpoint = args.next();
    match mode.as_str() {
        "native" => Ok(native(api, blocks)?),
        "control" => wasapi(api, blocks, false, endpoint.as_deref()),
        "dsp" => wasapi(api, blocks, true, endpoint.as_deref()),
        _ => Err("Unknown bank".into()),
    }
}
