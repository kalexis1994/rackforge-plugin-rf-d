use std::alloc::{GlobalAlloc, Layout, System};
use std::sync::atomic::{AtomicUsize, Ordering};

use rf_d_circuit::{initial_state, step, Parameters, SolverBudget};

struct CountingAllocator;
static ALLOCATIONS: AtomicUsize = AtomicUsize::new(0);

// The test binary has one test, so the counter isolates this processing loop.
unsafe impl GlobalAlloc for CountingAllocator {
    unsafe fn alloc(&self, layout: Layout) -> *mut u8 {
        ALLOCATIONS.fetch_add(1, Ordering::Relaxed);
        unsafe { System.alloc(layout) }
    }

    unsafe fn alloc_zeroed(&self, layout: Layout) -> *mut u8 {
        ALLOCATIONS.fetch_add(1, Ordering::Relaxed);
        unsafe { System.alloc_zeroed(layout) }
    }

    unsafe fn realloc(&self, ptr: *mut u8, layout: Layout, new_size: usize) -> *mut u8 {
        ALLOCATIONS.fetch_add(1, Ordering::Relaxed);
        unsafe { System.realloc(ptr, layout, new_size) }
    }

    unsafe fn dealloc(&self, ptr: *mut u8, layout: Layout) {
        unsafe { System.dealloc(ptr, layout) }
    }
}

#[global_allocator]
static ALLOCATOR: CountingAllocator = CountingAllocator;

#[test]
fn dc_initialization_and_audio_steps_do_not_allocate() {
    let p = Parameters {
        transistor_is_a: 1e-14,
        beta_forward: 160.0,
        beta_reverse: 5.0,
        temperature_k: 300.0,
        diode_is_a: 1.446_588_643_457_551_9e-9,
        diode_ideality: 1.5,
    };
    let before = ALLOCATIONS.load(Ordering::Relaxed);
    let mut state = initial_state(p).expect("DC initialization");
    for i in 0..1000 {
        let input = if i % 200 < 100 { 0.5 } else { -0.5 };
        step(
            &mut state,
            p,
            input,
            1.0 / 48000.0,
            Some(32.0),
            Some(32.0),
            SolverBudget::default(),
        )
        .expect("bounded board-3 step");
    }
    let after = ALLOCATIONS.load(Ordering::Relaxed);
    assert_eq!(after - before, 0, "processing allocated heap memory");
}
