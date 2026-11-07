// Read system counters on the supervisor, then publish affinity choices to the callback.
use std::sync::atomic::AtomicU32;

#[link(name = "kernel32")]
unsafe extern "system" {
    fn QueryIdleProcessorCycleTime(bytes: *mut u32, counters: *mut u64) -> i32;
    fn OpenThread(access: u32, inherit: i32, tid: u32) -> *mut c_void;
    fn GetSystemTimes(idle: *mut [u32; 2], kernel: *mut [u32; 2], user: *mut [u32; 2]) -> i32;
}

const SMT_SAMPLE: Duration = Duration::from_millis(4);
const SMT_WINDOW: usize = 4;
const SMT_COOLDOWN: usize = 24;
const SMT_LOAD_BLOCK: usize = 128;

fn smt_endpoints(driver: &str) -> HostResult<()> {
    let _com = Com::init()?;
    let _driver = AsioDriver::open(driver)?;
    let (left, left_bytes) = asio_channel128(0)?;
    let (right, right_bytes) = asio_channel128(1)?;
    println!("ASIO_CHANNELS\t{left}\t{right}\t{left_bytes}\t{right_bytes}");
    Ok(())
}

fn smt_idle() -> io::Result<[u64; 64]> {
    let mut values = [0; 64];
    let mut bytes = std::mem::size_of_val(&values) as u32;
    if unsafe { QueryIdleProcessorCycleTime(&mut bytes, values.as_mut_ptr()) } == 0 {
        return Err(io::Error::last_os_error());
    }
    Ok(values)
}

fn smt_delta(before: &[u64; 64], after: &[u64; 64], cpu: u32) -> u64 {
    after[cpu as usize].saturating_sub(before[cpu as usize])
}

fn smt_system_times() -> io::Result<[u64; 2]> {
    let (mut idle, mut kernel, mut user) = ([0; 2], [0; 2], [0; 2]);
    if unsafe { GetSystemTimes(&mut idle, &mut kernel, &mut user) } == 0 {
        return Err(io::Error::last_os_error());
    }
    let ticks = |value: [u32; 2]| (u64::from(value[1]) << 32) | u64::from(value[0]);
    Ok([ticks(idle), ticks(kernel) + ticks(user)])
}

fn smt_ratio(numerator: u64, denominator: u64) -> u64 {
    if denominator == 0 { 0 } else { (u128::from(numerator) * 10000 / u128::from(denominator)) as u64 }
}

struct SmtQualification {
    cpu: u32,
    windows: Vec<Vec<u64>>,
    total_windows: usize,
}

fn smt_qualify(pacer: &Pacer, pairs: &[(u32, u32)], system_floor: u64,
               fixed: Option<u32>) -> HostResult<SmtQualification> {
    let minimum_core = if fixed.is_some() { 9500 } else { 9000 };
    let mut previous_idle = smt_idle()?;
    let mut previous_system = smt_system_times()?;
    let mut windows: Vec<Vec<u64>> = Vec::with_capacity(4);
    let mut best_system = 0;
    let deadline = Instant::now() + Duration::from_secs(40);
    let mut total_windows = 0;
    while Instant::now() < deadline {
        pacer.wait(Duration::from_millis(250))?;
        total_windows += 1;
        let idle = smt_idle()?;
        let system = smt_system_times()?;
        let system_ratio = smt_ratio(system[0] - previous_system[0], system[1] - previous_system[1]);
        best_system = best_system.max(system_ratio);
        let max_idle = pairs.iter().flat_map(|&(cpu, sibling)| [cpu, sibling])
            .map(|cpu| smt_delta(&previous_idle, &idle, cpu)).max().unwrap_or(0);
        let scores = pairs.iter().map(|&(cpu, sibling)| {
            let minimum = smt_delta(&previous_idle, &idle, cpu).min(smt_delta(&previous_idle, &idle, sibling));
            smt_ratio(minimum, max_idle)
        });
        let window: Vec<_> = std::iter::once(system_ratio).chain(scores).collect();
        previous_idle = idle;
        previous_system = system;
        if system_ratio < system_floor {
            windows.clear();
            continue;
        }
        if windows.len() == 4 { windows.remove(0); }
        windows.push(window);
        if windows.len() < 4 { continue; }
        let best = pairs.iter().enumerate().filter(|(_, pair)| fixed.is_none_or(|cpu| cpu == pair.0 || cpu == pair.1))
            .map(|(i, &(cpu, _))| {
                let minimum = windows.iter().map(|row| row[i + 1]).min().unwrap_or(0);
                (minimum, std::cmp::Reverse(cpu))
            }).max();
        if let Some((score, std::cmp::Reverse(cpu))) = best {
            if (minimum_core..=10000).contains(&score) {
                return Ok(SmtQualification { cpu: fixed.unwrap_or(cpu), windows, total_windows });
            }
        }
    }
    eprintln!("SMT_QUALIFY_REJECT\t{total_windows}\t{best_system}");
    Err("The preflight did not identify a quiet SMT core within 40 seconds".into())
}

struct SmtCompletion(HANDLE);

impl SmtCompletion {
    fn new() -> windows::core::Result<Self> {
        unsafe { CreateEventW(None, false, false, PCWSTR::null()) }.map(Self)
    }

    fn wait(&self) -> HostResult<()> {
        match unsafe { WaitForSingleObject(self.0, 25000) } {
            WAIT_OBJECT_0 => Ok(()),
            windows::Win32::Foundation::WAIT_TIMEOUT => Err("Timed out waiting for the last ASIO callback".into()),
            _ => Err(io::Error::last_os_error().into()),
        }
    }

    fn signal(&self) {
        if unsafe { windows::Win32::System::Threading::SetEvent(self.0) }.is_err() {
            ASIO_ERRORS.fetch_add(1, Ordering::Relaxed);
        }
    }
}

impl Drop for SmtCompletion {
    fn drop(&mut self) { let _ = unsafe { CloseHandle(self.0) }; }
}

struct SmtCapture {
    completion: Option<SmtCompletion>,
    requested: AtomicU32,
    applied: UnsafeCell<Option<u32>>,
    rows: Box<[UnsafeCell<[u64; 2]>]>,
    background: bool,
}

impl SmtCapture {
    // Only the ASIO callback changes applied and writes one row per block.
    fn apply(&self, index: usize) -> io::Result<()> {
        let cpu = self.requested.load(Ordering::Acquire);
        let applied = unsafe { &mut *self.applied.get() };
        let mut ns_pin = 0;
        if applied.is_none() || (!self.background && *applied != Some(cpu)) {
            let started = Instant::now();
            schedule_pin(cpu)?;
            ns_pin = ns(started.elapsed()).max(1);
        }
        *applied = Some(cpu);
        unsafe { *self.rows[index].get() = [u64::from(cpu), ns_pin]; }
        Ok(())
    }
}

struct SmtPlanner {
    adaptive: bool,
    observe: bool,
    background: bool,
    supervisor: Option<u32>,
    pairs: Vec<(u32, u32)>,
    startup: Vec<(u32, u64, u64)>,
    initial: u32,
    selected: u32,
    stress: Option<u32>,
    load: Option<ScheduleLoad>,
    load_at: Option<usize>,
    pacer: Pacer,
    history: [[u64; 64]; SMT_WINDOW],
    sample: usize,
    low: usize,
    last_move: usize,
    informative: usize,
    events: Vec<[u64; 6]>,
    background_events: Vec<[u64; 4]>,
    callback: Option<SmtThread>,
    qualification: Option<SmtQualification>,
}

struct SmtThread(*mut c_void);
impl Drop for SmtThread {
    fn drop(&mut self) { unsafe { schedule_close(self.0); } }
}

fn smt_prepare(blocks: usize) -> HostResult<(Option<SmtPlanner>, Option<SmtCapture>)> {
    let mode = match std::env::var("RF_D_SMT_MODE") {
        Ok(mode) => mode,
        Err(std::env::VarError::NotPresent) => return Ok((None, None)),
        Err(error) => return Err(error.into()),
    };
    let adaptive = match mode.as_str() {
        "adaptive" | "background" => true,
        "hold" | "qualified" | "quiet-hold" | "quiet-event" => false,
        _ => return Err("Unknown SMT placement policy".into()),
    };
    let (_, cores) = schedule_cores()?;
    let supervisor = if std::env::var("RF_D_SMT_SUPERVISOR").as_deref() == Ok("1") {
        let cpu = cores[0].trailing_zeros();
        schedule_pin(cpu)?;
        Some(cpu)
    } else {
        None
    };
    let background = mode == "background";
    let pairs: Vec<_> = cores.iter().skip(1).filter(|mask| mask.count_ones() == 2).map(|mask| {
        let cpu = mask.trailing_zeros();
        (cpu, (mask & !(1 << cpu)).trailing_zeros())
    }).collect();
    if pairs.len() < 2 { return Err("Need two eligible SMT cores".into()); }
    let fixed = schedule_cpu("RF_D_SMT_FIXED_CPU")?;
    if fixed.is_some_and(|cpu| mode != "quiet-event" || !pairs.iter().any(|&(a, b)| a == cpu || b == cpu)) {
        return Err("The fixed CPU must belong to an eligible SMT pair in quiet-event mode".into());
    }
    let pacer = Pacer::new()?;
    let qualification = match mode.as_str() {
        "qualified" => Some(smt_qualify(&pacer, &pairs, 7000, None)?),
        "quiet-hold" => Some(smt_qualify(&pacer, &pairs, 8500, None)?),
        "quiet-event" => {
            if let Some(cpu) = fixed { eprintln!("SMT_FIXED_CPU\t{cpu}"); }
            let system_floor = match std::env::var("RF_D_SMT_FIXED_IDLE").as_deref() {
                Ok("8500") if fixed.is_some() => {
                    eprintln!("SMT_FIXED_IDLE\t8500");
                    8500
                }
                Err(std::env::VarError::NotPresent) => if fixed.is_some() { 9000 } else { 8500 },
                _ => return Err("Unknown SMT fixed idle requirement".into()),
            };
            Some(smt_qualify(&pacer, &pairs, system_floor, fixed)?)
        }
        _ => None,
    };
    let before = smt_idle()?;
    pacer.wait(Duration::from_millis(64))?;
    let after = smt_idle()?;
    let startup: Vec<_> = pairs.iter().map(|&(cpu, sibling)| {
        (cpu, smt_delta(&before, &after, cpu), smt_delta(&before, &after, sibling))
    }).collect();
    let Some(&(preferred, idle, sibling_idle)) = startup.iter().max_by_key(
        |&&(cpu, a, b)| (a.min(b), std::cmp::Reverse(cpu))
    ) else { return Err("No placement candidate".into()); };
    if idle.min(sibling_idle) == 0 {
        return Err("Idle counters did not identify an available SMT core".into());
    }
    let seed = schedule_cpu("RF_D_SMT_SEED")?;
    let initial = seed.unwrap_or_else(|| qualification.as_ref().map_or(preferred, |pass| pass.cpu));
    let sibling = pairs.iter().find_map(|&(a, b)| {
        if a == initial { Some(b) } else if fixed == Some(b) { Some(a) } else { None }
    }).ok_or("Unknown placement seed")?;
    let capture = SmtCapture {
        completion: (mode == "quiet-event").then(SmtCompletion::new).transpose()?,
        requested: AtomicU32::new(initial),
        applied: UnsafeCell::new(None),
        rows: (0..blocks).map(|_| UnsafeCell::new([0; 2])).collect(),
        background,
    };
    let planner = SmtPlanner {
        adaptive, observe: !matches!(mode.as_str(), "quiet-hold" | "quiet-event"), background, supervisor, pairs, startup, initial,
        selected: initial, stress: seed.map(|_| sibling),
        load: None, load_at: None, pacer, history: [after; SMT_WINDOW], sample: 0, low: 0, last_move: 0,
        informative: 0, events: Vec::with_capacity(blocks / SMT_COOLDOWN + 1),
        background_events: Vec::with_capacity(blocks / SMT_COOLDOWN + 1), callback: None, qualification,
    };
    Ok((Some(planner), Some(capture)))
}

impl SmtPlanner {
    fn tick(&mut self, completed: usize, capture: &SmtCapture, progress: &Capture, origin: Instant) -> HostResult<()> {
        if !self.observe {
            self.pacer.wait(Duration::from_millis(5))?;
            return Ok(());
        }
        if completed >= SMT_LOAD_BLOCK && self.load_at.is_none() && self.stress.is_some() {
            self.load = Some(ScheduleLoad::start(self.stress)?);
            self.load_at = Some(completed);
        }
        self.pacer.wait(SMT_SAMPLE)?;
        let now = smt_idle()?;
        let before = std::mem::replace(&mut self.history[self.sample % SMT_WINDOW], now);
        self.sample += 1;
        if self.sample < SMT_WINDOW { return Ok(()); }
        let current_sibling = self.pairs.iter().find(|(cpu, _)| *cpu == self.selected).unwrap().1;
        let current = smt_delta(&before, &now, current_sibling);
        let best_sibling = self.pairs.iter().map(|&(_, sibling)| smt_delta(&before, &now, sibling)).max().unwrap();
        if best_sibling > 0 { self.informative += 1; }
        if !self.adaptive || (self.stress.is_some() && self.load_at.is_none()) { return Ok(()); }
        if best_sibling == 0 || u128::from(current) * 4 >= u128::from(best_sibling) * 3 {
            self.low = 0;
            return Ok(());
        }
        self.low += 1;
        if self.low < 2 || completed < self.last_move + SMT_COOLDOWN { return Ok(()); }
        let candidates = self.pairs.iter().filter(|&&(cpu, sibling)| {
            cpu != self.selected && u128::from(smt_delta(&before, &now, sibling)) * 4 >= u128::from(best_sibling) * 3
        });
        if let Some(&(cpu, sibling)) = candidates.max_by_key(|&&(cpu, sibling)| {
            (smt_delta(&before, &now, cpu).min(smt_delta(&before, &now, sibling)), std::cmp::Reverse(cpu))
        }) {
            let completed = if self.background {
                let Some(event) = self.move_between_callbacks(cpu, progress, origin)? else { return Ok(()); };
                self.background_events.push(event);
                event[0] as usize
            } else {
                completed
            };
            let target_idle = smt_delta(&before, &now, sibling);
            self.events.push([completed as u64, self.selected as u64, cpu as u64, current, target_idle, best_sibling]);
            self.selected = cpu;
            self.last_move = completed;
            self.low = 0;
            capture.requested.store(cpu, Ordering::Release);
        }
        Ok(())
    }

    fn move_between_callbacks(&mut self, cpu: u32, progress: &Capture, origin: Instant)
        -> HostResult<Option<[u64; 4]>>
    {
        let completed = progress.completed.load(Ordering::Acquire);
        if completed == 0 || completed >= progress.rows.len() || ASIO_BUSY.load(Ordering::Acquire) {
            return Ok(None);
        }
        let row = unsafe { *progress.rows[completed - 1].get() };
        if self.callback.is_none() {
            // THREAD_SET_INFORMATION | THREAD_QUERY_INFORMATION, scoped to this process.
            let handle = unsafe { OpenThread(0x60, 0, row[9] as u32) };
            if handle.is_null() { return Err(io::Error::last_os_error().into()); }
            self.callback = Some(SmtThread(handle));
        }
        let now = ns(origin.elapsed());
        let end = row[0] + row[1];
        let next = row[0] + 128 * 1_000_000_000 / 48000;
        if now < end || now - end > 500_000 || next.saturating_sub(now) < 900_000
            || ASIO_BUSY.load(Ordering::Acquire) || progress.completed.load(Ordering::Acquire) != completed
        {
            return Ok(None);
        }
        let start = Instant::now();
        let handle = self.callback.as_ref().unwrap().0;
        if unsafe { SetThreadAffinityMask(handle, 1 << cpu) } == 0 {
            return Err(io::Error::last_os_error().into());
        }
        Ok(Some([completed as u64, now - end, next - now, ns(start.elapsed()).max(1)]))
    }

    fn report(&mut self) {
        let load_batches = self.load.as_mut().map_or(0, ScheduleLoad::finish);
        eprintln!("SMT_BANK\t{}\t{}\t{}\t{}\t{}\t{}\t{:?}", u8::from(self.adaptive),
            self.initial, self.load_at.unwrap_or(0), load_batches, self.sample, self.informative, self.startup);
        if let Some(cpu) = self.supervisor { eprintln!("SMT_OBSERVER\t{cpu}"); }
        if let Some(pass) = &self.qualification {
            eprintln!("SMT_QUALIFIED\t{}\t{:?}", pass.total_windows, pass.windows);
        }
        for event in &self.events { eprintln!("SMT_EVENT\t{event:?}"); }
        for event in &self.background_events { eprintln!("SMT_BACKGROUND\t{event:?}"); }
    }
}
