// Calibrated callback markers and a paced, ASIO-free RackEngine comparison.

#[link(name = "kernel32")]
unsafe extern "system" {
    fn GetThreadTimes(thread: *mut c_void, create: *mut [u32; 2], exit: *mut [u32; 2],
                      kernel: *mut [u32; 2], user: *mut [u32; 2]) -> i32;
    fn SetThreadAffinityMask(thread: *mut c_void, mask: usize) -> usize;
    fn GetLogicalProcessorInformation(entries: *mut CoreInfo, bytes: *mut u32) -> i32;
    fn GetActiveProcessorGroupCount() -> u16;
    fn GetCurrentProcess() -> *mut c_void;
    fn GetProcessAffinityMask(process: *mut c_void, process_mask: *mut usize, system_mask: *mut usize) -> i32;
    fn CreateWaitableTimerExW(attributes: *const c_void, name: *const u16, flags: u32, access: u32) -> *mut c_void;
    fn SetWaitableTimer(timer: *mut c_void, due: *const i64, period: i32, callback: *const c_void,
                        argument: *const c_void, resume: i32) -> i32;
    #[link_name = "WaitForSingleObject"]
    fn schedule_wait(object: *mut c_void, millis: u32) -> u32;
    #[link_name = "CloseHandle"]
    fn schedule_close(object: *mut c_void) -> i32;
}

#[repr(C)]
#[derive(Clone, Copy, Default)]
struct CoreInfo {
    mask: usize,
    relationship: u32,
    data: [u64; 2],
}

fn schedule_cores() -> HostResult<(usize, Vec<usize>)> {
    if unsafe { GetActiveProcessorGroupCount() } != 1 {
        return Err("The lab requires one Windows processor group".into());
    }
    let (mut allowed, mut system) = (0, 0);
    if unsafe { GetProcessAffinityMask(GetCurrentProcess(), &mut allowed, &mut system) } == 0 {
        return Err(io::Error::last_os_error().into());
    }
    let mut bytes = 0;
    unsafe { GetLogicalProcessorInformation(std::ptr::null_mut(), &mut bytes); }
    let entry = std::mem::size_of::<CoreInfo>();
    if bytes == 0 || bytes as usize % entry != 0 {
        return Err("Unrecognized Windows topology record".into());
    }
    let mut topology = vec![CoreInfo::default(); bytes as usize / entry];
    if unsafe { GetLogicalProcessorInformation(topology.as_mut_ptr(), &mut bytes) } == 0 {
        return Err(io::Error::last_os_error().into());
    }
    let mut cores: Vec<_> = topology[..bytes as usize / entry].iter()
        .filter(|record| record.relationship == 0)
        .map(|record| record.mask & allowed).filter(|mask| *mask != 0).collect();
    cores.sort_unstable();
    Ok((allowed, cores))
}

fn schedule_topology() -> HostResult<()> {
    let (allowed, cores) = schedule_cores()?;
    println!("SCHED_TOPOLOGY\t{allowed}\t{cores:?}");
    Ok(())
}

fn schedule_cpu(variable: &str) -> HostResult<Option<u32>> {
    match std::env::var(variable) {
        Ok(value) => {
            let cpu: u32 = value.parse()?;
            if cpu >= usize::BITS { return Err("CPU index exceeds the affinity mask".into()); }
            Ok(Some(cpu))
        }
        Err(std::env::VarError::NotPresent) => Ok(None),
        Err(error) => Err(error.into()),
    }
}

fn schedule_pin(cpu: u32) -> io::Result<()> {
    if unsafe { SetThreadAffinityMask(GetCurrentThread(), 1 << cpu) } == 0 {
        return Err(io::Error::last_os_error());
    }
    Ok(())
}

fn thread_cpu_ns() -> u64 {
    let (mut created, mut exited, mut kernel, mut user) = ([0; 2], [0; 2], [0; 2], [0; 2]);
    if unsafe { GetThreadTimes(GetCurrentThread(), &mut created, &mut exited, &mut kernel, &mut user) } == 0 {
        return u64::MAX;
    }
    let ticks = |time: [u32; 2]| (u64::from(time[1]) << 32) | u64::from(time[0]);
    (ticks(kernel) + ticks(user)) * 100
}

fn schedule_delta(before: u64, after: u64) -> u64 {
    if after == u64::MAX { return u64::MAX; }
    after.checked_sub(before).unwrap_or(u64::MAX)
}

struct ScheduleCapture {
    cpu: Option<u32>,
    markers: Box<[UnsafeCell<[u64; 4]>]>,
}

impl ScheduleCapture {
    fn new(blocks: usize) -> HostResult<Self> {
        Ok(Self { cpu: schedule_cpu("RF_D_SCHED_CPU")?,
                  markers: (0..blocks).map(|_| UnsafeCell::new([0; 4])).collect() })
    }
}

struct Pacer(*mut c_void);
impl Pacer {
    fn new() -> io::Result<Self> {
        // CREATE_WAITABLE_TIMER_HIGH_RESOLUTION, TIMER_MODIFY_STATE | SYNCHRONIZE.
        let handle = unsafe { CreateWaitableTimerExW(std::ptr::null(), std::ptr::null(), 2, 0x100002) };
        if handle.is_null() { Err(io::Error::last_os_error()) } else { Ok(Self(handle)) }
    }

    fn wait(&self, duration: Duration) -> io::Result<()> {
        if duration.is_zero() { return Ok(()); }
        let due = -(duration.as_nanos().div_ceil(100) as i64);
        let set = unsafe { SetWaitableTimer(self.0, &due, 0, std::ptr::null(), std::ptr::null(), 0) };
        if set == 0 || unsafe { schedule_wait(self.0, 1000) } != 0 {
            return Err(io::Error::last_os_error());
        }
        Ok(())
    }
}
impl Drop for Pacer {
    fn drop(&mut self) { unsafe { schedule_close(self.0); } }
}

fn schedule_calibration() -> HostResult<()> {
    let pacer = Pacer::new()?;
    let mut out = engine_rows()?;
    for busy in [true, false] {
        for _ in 0..128 {
            let before_cpu = thread_cpu_ns();
            let before_cycles = cycles();
            let start = Instant::now();
            if busy {
                while start.elapsed() < Duration::from_micros(900) { std::hint::spin_loop(); }
            } else {
                pacer.wait(Duration::from_micros(900))?;
            }
            let wall = ns(start.elapsed());
            let used = schedule_delta(before_cycles, cycles());
            let cpu = schedule_delta(before_cpu, thread_cpu_ns());
            for value in [wall, used, cpu] {
                out.write_all(&value.to_le_bytes())?;
            }
        }
    }
    out.flush()?;
    Ok(())
}

struct ScheduleLoad {
    stop: Arc<AtomicBool>,
    thread: Option<std::thread::JoinHandle<u64>>,
}
impl ScheduleLoad {
    fn start(cpu: Option<u32>) -> HostResult<Self> {
        let stop = Arc::new(AtomicBool::new(false));
        let mut load = Self { stop, thread: None };
        if let Some(cpu) = cpu {
            let stop = load.stop.clone();
            let (ready, receive) = std::sync::mpsc::sync_channel(0);
            load.thread = Some(std::thread::spawn(move || {
                let pinned = schedule_pin(cpu);
                let ok = pinned.is_ok();
                if ready.send(pinned).is_err() || !ok { return 0; }
                let (mut batches, mut value) = (0, 3_u64);
                while !stop.load(Ordering::Relaxed) {
                    for _ in 0..1024 {
                        value = std::hint::black_box(value.wrapping_mul(1664525).wrapping_add(1013904223));
                    }
                    batches += 1;
                }
                batches
            }));
            receive.recv()??;
        }
        Ok(load)
    }

    fn finish(&mut self) -> u64 {
        self.stop.store(true, Ordering::Relaxed);
        self.thread.take().map_or(0, |thread| thread.join().unwrap())
    }
}
impl Drop for ScheduleLoad {
    fn drop(&mut self) { self.finish(); }
}

fn schedule_offline(blocks: usize) -> HostResult<()> {
    let mut dsp = EngineWork::from_env()?;
    let capture = Capture::new(blocks);
    let mut markers = vec![[0; 4]; blocks];
    let pacer = Pacer::new()?;
    let cpu = schedule_cpu("RF_D_SCHED_CPU")?;
    let helper = schedule_cpu("RF_D_SCHED_LOAD")?;
    let mut load = ScheduleLoad::start(helper)?;
    let start = Instant::now();
    let status = realtime::engage(realtime::DEFAULT_AUDIO_PRIORITY);
    let policy = match status.scheduling {
        realtime::SchedulingState::Boosted { class: "pro-audio" } => 1,
        realtime::SchedulingState::Boosted { class: "time-critical" } => 2,
        _ => 3,
    };
    let throttle = if realtime::exempt_process_from_throttling()
        == realtime::ThrottlingState::Exempt { 1 } else { 2 };
    if let Some(cpu) = cpu { schedule_pin(cpu)?; }
    let setup = ns(start.elapsed());
    let origin = Instant::now();
    for (block, marker) in markers.iter_mut().enumerate() {
        let target = Duration::from_nanos(block as u64 * 128 * 1_000_000_000 / 48000);
        pacer.wait(target.saturating_sub(origin.elapsed()))?;
        let cpu_before = thread_cpu_ns();
        let cycles_before = cycles();
        let render = Instant::now();
        let row = measure(origin, 128, &mut [], Some(&mut dsp), if block == 0 { setup } else { 0 },
                          policy, throttle);
        let wall = ns(render.elapsed());
        let used = schedule_delta(cycles_before, cycles());
        let cpu_ns = schedule_delta(cpu_before, thread_cpu_ns());
        *marker = [wall, used, cpu_ns, cpu_ns];
        capture.publish(block, row);
    }
    let batches = load.finish();
    eprintln!("SCHED_OFFLINE\t{blocks}\t{}\t{}\t{batches}",
              cpu.map_or(-1, |v| v as i32), helper.map_or(-1, |v| v as i32));
    let mut out = engine_rows()?;
    for (index, marker) in markers.into_iter().enumerate() {
        let row = unsafe { *capture.rows[index].get() };
        for value in row.into_iter().chain([0, 0]).chain(marker) {
            out.write_all(&value.to_le_bytes())?;
        }
    }
    out.flush()?;
    dsp.report();
    Ok(())
}
