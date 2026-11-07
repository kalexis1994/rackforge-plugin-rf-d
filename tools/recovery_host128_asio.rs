// Uses the binding and import library from RackForge's existing ASIO build.
use asio_ffi as asio;
use std::sync::atomic::{AtomicBool, AtomicPtr};

struct AsioDriver;
impl AsioDriver {
    fn open(name: &str) -> HostResult<Self> {
        let mut name = std::ffi::CString::new(name)?.into_bytes_with_nul();
        if !unsafe { asio::load_asio_driver(name.as_mut_ptr().cast()) } {
            return Err("load_asio_driver rejected the driver".into());
        }
        let driver = Self;
        let mut info = asio::ASIODriverInfo {
            asioVersion: 2,
            driverVersion: 0,
            name: [0; 32],
            errorMessage: [0; 124],
            sysRef: std::ptr::null_mut(),
        };
        asio_ok("ASIOInit", unsafe { asio::ASIOInit(&mut info) })?;
        Ok(driver)
    }
}

impl Drop for AsioDriver {
    fn drop(&mut self) {
        unsafe {
            asio::ASIOExit();
            asio::remove_current_driver();
        }
    }
}

fn asio_ok(operation: &str, code: i32) -> HostResult<()> {
    if code == 0 {
        Ok(())
    } else {
        Err(format!("{operation} returned {code}").into())
    }
}

fn asio_sizes() -> HostResult<[i32; 4]> {
    let (mut minimum, mut maximum, mut preferred, mut granularity) = (0, 0, 0, 0);
    asio_ok("ASIOGetBufferSize", unsafe {
        asio::ASIOGetBufferSize(&mut minimum, &mut maximum, &mut preferred, &mut granularity)
    })?;
    Ok([minimum, maximum, preferred, granularity])
}

fn asio_query128(name: &str) -> HostResult<()> {
    let _driver = AsioDriver::open(name)?;
    let [minimum, maximum, preferred, granularity] = asio_sizes()?;
    let (mut inputs, mut outputs, mut rate) = (0, 0, 0.);
    asio_ok("ASIOGetChannels", unsafe { asio::ASIOGetChannels(&mut inputs, &mut outputs) })?;
    asio_ok("ASIOGetSampleRate", unsafe { asio::get_sample_rate(&mut rate) })?;
    let can48 = unsafe { asio::can_sample_rate(48000.) };
    println!("ASIO\t{name}\t{rate}\t{inputs}\t{outputs}\t{minimum}\t{maximum}\t{preferred}\t{granularity}\t{can48}");
    Ok(())
}

fn asio_rate() -> HostResult<f64> {
    let mut rate = 0.;
    asio_ok("ASIOGetSampleRate", unsafe { asio::get_sample_rate(&mut rate) })?;
    Ok(rate)
}

struct RateRestore(Option<f64>);
impl RateRestore {
    fn restore(&mut self) -> HostResult<f64> {
        let rate = self.0.ok_or("Missing original rate")?;
        asio_ok("Restore ASIO sample rate", unsafe { asio::set_sample_rate(rate) })?;
        let restored = asio_rate()?;
        if restored != rate {
            return Err("ASIO sample rate did not restore".into());
        }
        self.0 = None;
        Ok(restored)
    }
}
impl Drop for RateRestore {
    fn drop(&mut self) {
        if let Some(rate) = self.0 {
            unsafe { asio::set_sample_rate(rate); }
        }
    }
}

struct AsioSession {
    capture: Capture,
    sample_positions: Box<[UnsafeCell<[u64; 2]>]>,
    buffers: [asio::ASIOBufferInfo; 2],
    byte_counts: [usize; 2],
    dsp: UnsafeCell<Option<Dsp>>,
    posture: UnsafeCell<(u64, u64)>,
    origin: Instant,
    output_ready: bool,
}

static ASIO_SESSION: AtomicPtr<AsioSession> = AtomicPtr::new(std::ptr::null_mut());
static ASIO_BUSY: AtomicBool = AtomicBool::new(false);
static ASIO_NOTICES: AtomicUsize = AtomicUsize::new(0);
static ASIO_ERRORS: AtomicUsize = AtomicUsize::new(0);

struct CallbackGuard;
impl Drop for CallbackGuard {
    fn drop(&mut self) { ASIO_BUSY.store(false, Ordering::Release); }
}

unsafe extern "C" fn asio_rate_changed(_: asio::ASIOSampleRate) {
    ASIO_NOTICES.fetch_or(1, Ordering::Relaxed);
}

unsafe extern "C" fn asio_message128(selector: i32, value: i32, _: *mut c_void, _: *mut f64) -> i32 {
    match selector {
        1 => i32::from(matches!(value, 2 | 3 | 4 | 5 | 15)),
        2 => 2,
        3 | 4 | 5 | 15 => {
            ASIO_NOTICES.fetch_or(1 << selector, Ordering::Relaxed);
            1
        }
        _ => 0,
    }
}

unsafe extern "C" fn asio_switch128(buffer: i32, _: asio::ASIOBool) {
    if ASIO_BUSY.compare_exchange(false, true, Ordering::Acquire, Ordering::Relaxed).is_err() {
        ASIO_ERRORS.fetch_add(1, Ordering::Relaxed);
        return;
    }
    let _guard = CallbackGuard;
    // The main thread publishes the session after allocation and frees it
    // only after ASIOStop has quiesced the callback.
    let Some(session) = (unsafe { ASIO_SESSION.load(Ordering::Acquire).as_ref() }) else { return };
    if !(0..=1).contains(&buffer) {
        ASIO_ERRORS.fetch_add(1, Ordering::Relaxed);
        return;
    }
    let index = session.capture.completed.load(Ordering::Relaxed);
    let recording = index < session.capture.rows.len();
    let mut setup_ns = 0;
    if recording && index == 0 {
        let start = Instant::now();
        let status = realtime::engage(realtime::DEFAULT_AUDIO_PRIORITY);
        let policy = match status.scheduling {
            realtime::SchedulingState::Boosted { class: "pro-audio" } => 1,
            realtime::SchedulingState::Boosted { class: "time-critical" } => 2,
            _ => 3,
        };
        let throttle = if realtime::exempt_process_from_throttling()
            == realtime::ThrottlingState::Exempt { 1 } else { 2 };
        unsafe { *session.posture.get() = (policy, throttle); }
        setup_ns = ns(start.elapsed());
    }
    realtime::flush_subnormals();
    let start = Instant::now();
    let cpu_before = unsafe { GetCurrentProcessorNumber() };
    let before = cycles();
    for (channel, info) in session.buffers.iter().enumerate() {
        // Copy the packed pointer field before indexing it.
        let pair = info.buffers;
        unsafe { std::ptr::write_bytes(pair[buffer as usize].cast::<u8>(), 0, session.byte_counts[channel]); }
    }
    let mut position = asio::ASIOSamples { hi: 0, lo: 0 };
    let mut timestamp = asio::ASIOTimeStamp { hi: 0, lo: 0 };
    let position_status = unsafe { asio::ASIOGetSamplePosition(&mut position, &mut timestamp) };
    let row = if recording {
        let (policy, throttle) = unsafe { *session.posture.get() };
        let dsp = unsafe { &mut *session.dsp.get() };
        Some(measure(session.origin, HOST_FRAMES as usize, &mut [], dsp.as_mut(), setup_ns, policy, throttle))
    } else {
        None
    };
    if session.output_ready && unsafe { asio::ASIOOutputReady() } != 0 {
        ASIO_ERRORS.fetch_add(1, Ordering::Relaxed);
    }
    let after = cycles();
    let wall_ns = ns(start.elapsed());
    if let Some(mut row) = row {
        row[0] = ns(start.duration_since(session.origin));
        row[1] = wall_ns;
        row[2] = if before == 0 || after < before { u64::MAX } else { after - before };
        row[7] = cpu_before as u64;
        row[8] = unsafe { GetCurrentProcessorNumber() } as u64;
        let sample = if position_status == 0 { (u64::from(position.hi) << 32) | u64::from(position.lo) } else { u64::MAX };
        unsafe { *session.sample_positions[index].get() = [sample, buffer as u64]; }
        session.capture.publish(index, row);
    }
}

fn asio_channel128(channel: i32) -> HostResult<(String, usize)> {
    let mut info = asio::ASIOChannelInfo {
        channel, isInput: 0, isActive: 0, channelGroup: 0, type_: 0, name: [0; 32],
    };
    asio_ok("ASIOGetChannelInfo", unsafe { asio::ASIOGetChannelInfo(&mut info) })?;
    let bytes = info.name.into_iter().take_while(|c| *c != 0).map(|c| c as u8).collect::<Vec<_>>();
    // Integer and float LSB formats from the ASIO SDK sample type enum.
    let sample_bytes = match info.type_ {
        16 => 2,
        17 => 3,
        18 | 19 | 24..=27 => 4,
        20 => 8,
        _ => return Err(format!("Unsupported ASIO sample type {}", info.type_).into()),
    };
    Ok((String::from_utf8_lossy(&bytes).into_owned(), sample_bytes))
}

fn callbacks128() -> asio::ASIOCallbacks {
    asio::ASIOCallbacks {
        bufferSwitch: Some(asio_switch128),
        sampleRateDidChange: Some(asio_rate_changed),
        asioMessage: Some(asio_message128),
        bufferSwitchTimeInfo: None,
    }
}

fn asio_bench128(name: &str, blocks: usize, dsp: bool) -> HostResult<()> {
    let _driver = AsioDriver::open(name)?;
    let original_rate = asio_rate()?;
    let mut restore = RateRestore(Some(original_rate));
    asio_ok("ASIOSetSampleRate", unsafe { asio::set_sample_rate(f64::from(HOST_RATE)) })?;
    if asio_rate()? != f64::from(HOST_RATE) {
        return Err("ASIO clock rejected 48 kHz".into());
    }
    let [min, max, preferred, step] = asio_sizes()?;
    if !(min..=max).contains(&(HOST_FRAMES as i32)) || step <= 0 || (HOST_FRAMES as i32 - min) % step != 0 {
        return Err(format!("ASIO range {min}/{max}/{preferred}/{step} excludes 128").into());
    }
    let (left, left_bytes) = asio_channel128(0)?;
    let (right, right_bytes) = asio_channel128(1)?;
    eprintln!("ASIO_CHANNELS\t{left}\t{right}\t{left_bytes}\t{right_bytes}");
    let mut callbacks = Box::new(callbacks128());
    let dsp = if dsp { Some(Dsp::new(Api::load()?)) } else { None };
    let mut session = Box::new(AsioSession {
        capture: Capture::new(blocks),
        sample_positions: (0..blocks).map(|_| UnsafeCell::new([0; 2])).collect(),
        buffers: std::array::from_fn(|i| asio::ASIOBufferInfo {
            isInput: 0, channelNum: i as i32, buffers: [std::ptr::null_mut(); 2],
        }),
        byte_counts: [left_bytes * HOST_FRAMES as usize, right_bytes * HOST_FRAMES as usize],
        dsp: UnsafeCell::new(dsp),
        posture: UnsafeCell::new((0, 0)),
        origin: Instant::now(),
        output_ready: false,
    });
    asio_ok("ASIOCreateBuffers", unsafe {
        asio::ASIOCreateBuffers(session.buffers.as_mut_ptr(), 2, HOST_FRAMES as i32, &mut *callbacks)
    })?;
    if session.buffers.iter().any(|info| {
        let pair = info.buffers;
        pair.iter().any(|ptr| ptr.is_null())
    }) {
        unsafe { asio::ASIODisposeBuffers(); }
        return Err("ASIOCreateBuffers returned a null channel buffer".into());
    }
    let verified_formats = (|| -> HostResult<bool> {
        Ok(asio_channel128(0)?.1 == left_bytes && asio_channel128(1)?.1 == right_bytes)
    })();
    if !matches!(verified_formats, Ok(true)) {
        unsafe { asio::ASIODisposeBuffers(); }
        return Err("ASIO channel format changed after opening buffers".into());
    }
    session.output_ready = unsafe { asio::ASIOOutputReady() } == 0;
    let raw = Box::into_raw(session);
    ASIO_SESSION.store(raw, Ordering::Release);
    let start_result = unsafe { asio::ASIOStart() };
    let expires = Instant::now() + Duration::from_secs(25);
    let session = unsafe { &*raw };
    if start_result == 0 {
        while session.capture.completed.load(Ordering::Acquire) < blocks && Instant::now() < expires {
            std::thread::sleep(Duration::from_millis(5));
        }
    }
    let stopped = if start_result == 0 { unsafe { asio::ASIOStop() } } else { 0 };
    if stopped != 0 || ASIO_BUSY.load(Ordering::Acquire) {
        // Retain callback memory on a broken driver teardown until process exit.
        std::mem::forget(restore);
        std::mem::forget(_driver);
        std::mem::forget(callbacks);
        return Err(format!("ASIOStop returned {stopped} or callback did not quiesce").into());
    }
    ASIO_SESSION.store(std::ptr::null_mut(), Ordering::Release);
    let session = unsafe { Box::from_raw(raw) };
    let active_rate = asio_rate();
    let notices = ASIO_NOTICES.load(Ordering::Relaxed);
    let disposed = unsafe { asio::ASIODisposeBuffers() };
    if disposed != 0 {
        std::mem::forget(callbacks);
    }
    let restored_rate = restore.restore()?;
    let active_rate = active_rate?;
    let count = session.capture.completed.load(Ordering::Acquire);
    let errors = ASIO_ERRORS.load(Ordering::Relaxed);
    eprintln!("ASIO_BANK\t{name}\t{original_rate}\t{active_rate}\t{restored_rate}\t{HOST_FRAMES}\t{count}\t{notices}\t{errors}");
    let mut out = io::BufWriter::new(io::stdout().lock());
    for index in 0..count {
        let row = unsafe { *session.capture.rows[index].get() };
        let extra = unsafe { *session.sample_positions[index].get() };
        for value in row.into_iter().chain(extra) {
            out.write_all(&value.to_le_bytes())?;
        }
    }
    out.flush()?;
    asio_ok("ASIOStart", start_result)?;
    asio_ok("ASIODisposeBuffers", disposed)?;
    if count != blocks || active_rate != f64::from(HOST_RATE) || errors != 0 {
        return Err("ASIO bank incomplete, changed rate or callback error".into());
    }
    Ok(())
}
