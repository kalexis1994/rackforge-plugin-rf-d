//! Exercise the audio block entry point and capture the electrical state at each sample.
use crate::{dump, reduced_engine::{Counters, Engine, Frame, BLOCK}, StepError};
use std::{
    alloc::{GlobalAlloc, Layout, System},
    error::Error,
    fs,
    sync::atomic::{AtomicBool, AtomicUsize, Ordering::Relaxed},
    time::Instant,
};

struct AllocationCount;
static COUNT: AtomicUsize = AtomicUsize::new(0);
static ACTIVE: AtomicBool = AtomicBool::new(false);

unsafe impl GlobalAlloc for AllocationCount {
    unsafe fn alloc(&self, layout: Layout) -> *mut u8 {
        if ACTIVE.load(Relaxed) {
            COUNT.fetch_add(1, Relaxed);
        }
        unsafe { System.alloc(layout) }
    }
    unsafe fn dealloc(&self, ptr: *mut u8, layout: Layout) {
        unsafe { System.dealloc(ptr, layout) };
    }
    unsafe fn realloc(&self, ptr: *mut u8, layout: Layout, bytes: usize) -> *mut u8 {
        if ACTIVE.load(Relaxed) {
            COUNT.fetch_add(1, Relaxed);
        }
        unsafe { System.realloc(ptr, layout, bytes) }
    }
}

#[global_allocator]
static ALLOCATOR: AllocationCount = AllocationCount;

fn frame(index: usize, frame: &Frame) {
    dump(index, frame.phase, frame.state);
    for s in frame.switches.iter().flatten() {
        println!("SWITCH,{},{},{},{}", s.pair, s.first_tick, s.last_tick, u8::from(s.positive));
    }
}

pub fn run(path: &str, branch: &str, cap: usize, size: usize) -> Result<(), Box<dyn Error>> {
    assert!(matches!(branch, "negative" | "positive") && matches!(size, 64 | 128));
    let mut engine = Engine::prepare(&fs::read(path)?, cap).map_err(|e| format!("{e:?}"))?;
    let keys: [f64; BLOCK] = std::array::from_fn(|i| {
        if branch == "negative" && (16..96).contains(&i) { 10. } else { 0. }
    });
    let mut output = [Frame::EMPTY; BLOCK];
    let before = engine.position();
    assert!(matches!(engine.render(&[f64::NAN], &mut output[..1]), Err(StepError::InvalidInput)));
    assert_eq!(before.state, engine.position().state);
    assert_eq!(output[0].state, Frame::EMPTY.state);
    frame(0, &before);
    for (block, (input, frames)) in keys.chunks(size).zip(output.chunks_mut(size)).enumerate() {
        COUNT.store(0, Relaxed);
        ACTIVE.store(true, Relaxed);
        let start = Instant::now();
        let stats = engine.render(input, frames);
        let elapsed = start.elapsed().as_nanos();
        ACTIVE.store(false, Relaxed);
        let count = COUNT.load(Relaxed);
        let stats = stats.map_err(|e| format!("{branch} cap={cap} block={block}: {e:?}"))?;
        let Counters { widths, guard_retries, solver_retries, iterations, max_residual_a, max_correction_v, .. } = stats;
        #[cfg(profile_reduced)]
        for (region, p) in stats.profile.into_iter().enumerate() {
            let [contour, audio, direction] = p.calls;
            let [contour_ns, audio_ns, direction_ns] = p.ns;
            println!("PROFILE,{region},{},{},{},{contour},{audio},{direction},{contour_ns},{audio_ns},{direction_ns},{}",
                     p.steps, p.fine_steps, p.wall_ns, p.audio_tangents);
        }
        println!("BLOCK,{size},{elapsed},{count},{guard_retries},{solver_retries},{iterations},{max_residual_a:.17e},{max_correction_v:.17e},{}",
                 widths.map(|n| n.to_string()).join(","));
        let clock = stats.clock;
        println!("CLOCK,{},{},{},{},{},{}", clock.solves, clock.comparisons,
                 clock.error_retries, clock.event_retries, clock.reused_halves, clock.reused_siblings);
        for (i, sample) in frames.iter().enumerate() {
            frame(block * size + i + 1, sample);
        }
    }
    Ok(())
}
