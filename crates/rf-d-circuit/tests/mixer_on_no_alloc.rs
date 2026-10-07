use rf_d_circuit::mixer_on::OnMixer;
use std::alloc::{GlobalAlloc, Layout, System};
use std::sync::atomic::{AtomicUsize, Ordering};

struct Count;
static ALLOCATIONS: AtomicUsize = AtomicUsize::new(0);
unsafe impl GlobalAlloc for Count {
    unsafe fn alloc(&self, l: Layout) -> *mut u8 {
        ALLOCATIONS.fetch_add(1, Ordering::Relaxed);
        unsafe { System.alloc(l) }
    }
    unsafe fn alloc_zeroed(&self, l: Layout) -> *mut u8 {
        ALLOCATIONS.fetch_add(1, Ordering::Relaxed);
        unsafe { System.alloc_zeroed(l) }
    }
    unsafe fn realloc(&self, p: *mut u8, l: Layout, n: usize) -> *mut u8 {
        ALLOCATIONS.fetch_add(1, Ordering::Relaxed);
        unsafe { System.realloc(p, l, n) }
    }
    unsafe fn dealloc(&self, p: *mut u8, l: Layout) {
        unsafe { System.dealloc(p, l) }
    }
}
#[global_allocator]
static ALLOCATOR: Count = Count;

#[test]
fn constructor_stamp_and_ten_thousand_evaluations_use_no_heap() {
    let before = ALLOCATIONS.load(Ordering::Relaxed);
    let mut checksum = 0.0;
    for i in 0..10000 {
        let alpha = (i % 101) as f64 / 100.0;
        let m = OnMixer::new([true; 5], [alpha, 1.0 - alpha, 0.0, 1.0]).unwrap();
        let p = m.evaluate([1.0, -2.0, 3.0, -4.0, 5.0, -0.2]).unwrap();
        let solved = m
            .solve_imposed_current([1.0, -2.0, 3.0, -4.0, 5.0], 1e-6)
            .unwrap();
        checksum += std::hint::black_box(p.current_a[0] + solved.bus_v + m.admittance_s()[5][5]);
    }
    let after = ALLOCATIONS.load(Ordering::Relaxed);
    assert_eq!(after - before, 0);
    assert!(checksum.is_finite());
    println!(
        "MIXER_ALLOCATION,evaluations=10000,allocations={}",
        after - before
    );
}
