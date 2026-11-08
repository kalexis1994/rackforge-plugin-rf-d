use crate::{plant::{self, Drive}, scene::{Scene, LENGTH}, voice::{Event, Frame, Message, Voice, MAX_BLOCK}};
use std::{alloc::{GlobalAlloc, Layout, System}, io::{BufWriter, Read, Write},
          sync::atomic::{AtomicUsize, Ordering::Relaxed}, time::Instant};

struct Counter;
static ALLOCS: AtomicUsize = AtomicUsize::new(0);
unsafe impl GlobalAlloc for Counter {
    unsafe fn alloc(&self, layout: Layout) -> *mut u8 {
        ALLOCS.fetch_add(1, Relaxed);
        unsafe { System.alloc(layout) }
    }
    unsafe fn dealloc(&self, ptr: *mut u8, layout: Layout) {
        unsafe { System.dealloc(ptr, layout) }
    }
    unsafe fn realloc(&self, ptr: *mut u8, layout: Layout, size: usize) -> *mut u8 {
        ALLOCS.fetch_add(1, Relaxed);
        unsafe { System.realloc(ptr, layout, size) }
    }
}
#[global_allocator]
static COUNTER: Counter = Counter;

fn write(out: &mut impl Write, items: [f64; 6]) -> std::io::Result<()> {
    for v in items {
        out.write_all(&v.to_le_bytes())?;
    }
    Ok(())
}

fn guard() -> Result<(), Box<dyn std::error::Error>> {
    let mut candidate = Voice::<4>::new();
    let mut control = candidate.clone();
    let note = [Event { offset: 0, message: Message::NoteOn(57) }];
    let saved = Frame { j7_v: -0., returns_a: [3., 4.], ..Frame::default() };
    let mut actual = [saved; 2];
    let valid = [Drive::default(); 2];
    let invalid = [valid[0], Drive { volume_delta_v: f64::NAN, filter_delta_v: 0. }];
    assert!(candidate.render_with_returns(&note, &mut actual, &invalid).is_err());
    assert!(actual.iter().all(|sample| *sample == saved && sample.j7_v.is_sign_negative()));
    let mut expected = actual;
    candidate.render_with_returns(&note, &mut actual, &valid).map_err(|e| format!("{e:?}"))?;
    control.render_with_returns(&note, &mut expected, &valid).map_err(|e| format!("{e:?}"))?;
    assert_eq!(actual, expected);
    Ok(())
}

pub fn main() -> Result<(), Box<dyn std::error::Error>> {
    let mode = std::env::args().nth(1).ok_or("argument")?;
    let mut out = BufWriter::new(std::io::stdout().lock());
    if mode == "electrical" {
        let mut raw = Vec::new();
        std::io::stdin().lock().read_to_end(&mut raw)?;
        let mut state = plant::State::dc(1).unwrap();
        assert_eq!(raw.len() % 24, 0);
        for row in raw.chunks_exact(24) {
            let read = |k| f64::from_le_bytes(row[k..k + 8].try_into().unwrap());
            let p = plant::step(&mut state, read(0), Drive {
                volume_delta_v: read(8), filter_delta_v: read(16),
            }).map_err(|e| format!("{e:?}"))?;
            write(&mut out, [p.j7_v, p.bus_v, p.base_v - p.bus_v, p.panel_a, p.returns_a[0], p.returns_a[1]])?;
        }
    } else {
        guard()?;
        let size: usize = std::env::args().nth(2).ok_or("size")?.parse()?;
        assert!(matches!(mode.as_str(), "zero" | "driven") && matches!(size, 64 | 128));
        let mut scene = Scene::new(mode == "driven");
        let mut maximum = 0_u128;
        let mut timings = Vec::with_capacity(LENGTH / size);
        let mut allocations = 0;
        for _ in (0..LENGTH).step_by(size) {
            let mut frames = [Frame::default(); MAX_BLOCK];
            let before = ALLOCS.load(Relaxed);
            let now = Instant::now();
            scene.render(&mut frames[..size]).map_err(|e| format!("{e:?}"))?;
            let elapsed = now.elapsed().as_nanos();
            allocations += ALLOCS.load(Relaxed) - before;
            timings.push(elapsed);
            maximum = maximum.max(elapsed);
            for f in &frames[..size] {
                write(&mut out, [f.j7_v, f.bus_v, f.c27_v, f.panel_a, f.returns_a[0], f.returns_a[1]])?;
            }
        }
        eprintln!("PILOT_PORTS,{size},{maximum},{allocations},{}", timings.iter().filter(|&&t| 3 * t > 4_000_000).count());
    }
    out.flush()?;
    Ok(())
}
