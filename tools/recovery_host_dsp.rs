//! C boundary for measuring the frozen GNU DSP inside the MSVC CPAL host.
pub use rf_d_circuit::{junction_charge, StepError};
#[path = "recovery_cost_exp_kernel.rs"]
mod kernel;
#[path = "../crates/rf-d-circuit/src/j7_stream_output.rs"]
mod stream;

use std::{
    alloc::{GlobalAlloc, Layout, System},
    ffi::c_void,
    sync::atomic::{AtomicUsize, Ordering},
};

struct Counter;
static ALLOCS: AtomicUsize = AtomicUsize::new(0);
unsafe impl GlobalAlloc for Counter {
    unsafe fn alloc(&self, layout: Layout) -> *mut u8 {
        ALLOCS.fetch_add(1, Ordering::Relaxed);
        unsafe { System.alloc(layout) }
    }
    unsafe fn dealloc(&self, ptr: *mut u8, layout: Layout) {
        unsafe { System.dealloc(ptr, layout) }
    }
    unsafe fn realloc(&self, ptr: *mut u8, layout: Layout, size: usize) -> *mut u8 {
        ALLOCS.fetch_add(1, Ordering::Relaxed);
        unsafe { System.realloc(ptr, layout, size) }
    }
}
#[global_allocator]
static ALLOCATOR: Counter = Counter;

struct Dsp {
    state: kernel::State,
    fir: stream::Decimator,
    input: Vec<f64>,
    position: usize,
}

#[no_mangle]
extern "C" fn rf_new() -> *mut c_void {
    let state = kernel::State::dc(1).unwrap();
    let fir = stream::Decimator::new(kernel::nodes(state)[61]).unwrap();
    let input = (0..384_000)
        .map(|sample| {
            let t = sample as f64 / 384000.;
            0.1 * ((std::f64::consts::TAU * 137. * t).sin()
                + 0.3 * (std::f64::consts::TAU * 1103. * t).sin())
        })
        .collect();
    Box::into_raw(Box::new(Dsp { state, fir, input, position: 0 })).cast()
}

// The handle belongs to one caller at a time. Both output slices are disjoint
// and have capacity for frames*8 and frames values, respectively.
#[no_mangle]
unsafe extern "C" fn rf_render(
    dsp: *mut c_void,
    frames: usize,
    raw: *mut f64,
    filtered: *mut f64,
) -> i32 {
    if !(1..=128).contains(&frames) {
        return -1;
    }
    let dsp = unsafe { &mut *dsp.cast::<Dsp>() };
    let raw = unsafe { std::slice::from_raw_parts_mut(raw, frames * 8) };
    let filtered = unsafe { std::slice::from_raw_parts_mut(filtered, frames) };
    let mut output = [stream::Frame::EMPTY; 128];
    let allocations = ALLOCS.load(Ordering::Relaxed);
    for sample in raw.iter_mut() {
        let Ok(ports) = kernel::step(&mut dsp.state, dsp.input[dsp.position]) else {
            return -2;
        };
        *sample = ports.j7_v;
        dsp.position += 1;
        if dsp.position == dsp.input.len() {
            dsp.position = 0;
        }
    }
    let Ok(written) = dsp.fir.push(raw, &mut output) else {
        return -3;
    };
    for (slot, frame) in filtered.iter_mut().zip(&output[..written]) {
        *slot = frame.voltage_v;
    }
    if ALLOCS.load(Ordering::Relaxed) != allocations {
        return -4;
    }
    written as i32
}

#[no_mangle]
unsafe extern "C" fn rf_free(dsp: *mut c_void) {
    drop(unsafe { Box::from_raw(dsp.cast::<Dsp>()) });
}
