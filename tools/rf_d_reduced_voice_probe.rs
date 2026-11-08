#[path = "PLANT_PATH"]
mod plant;
#[path = "WAVE_PATH"]
mod wave;
#[path = "FIR_PATH"]
mod coefficients;
#[path = "VOICE_PATH"]
mod voice;
#[path = "TIMING_PATH"]
mod release_timing;

use std::{alloc::{GlobalAlloc, Layout, System}, io::{BufWriter, Write},
          sync::atomic::{AtomicUsize, Ordering::Relaxed}, time::Instant};
use voice::{Event, Frame, Message::*, Voice};

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

const LENGTH: usize = 48_128;
const SCENE: [Event; 8] = [
    Event { offset: 61, message: NoteOn(57) },
    Event { offset: 6179, message: NoteOn(45) },
    Event { offset: 12298, message: NoteOff(45) },
    Event { offset: 18537, message: NoteOff(57) },
    Event { offset: 23229, message: NoteOn(52) },
    Event { offset: 29383, message: NoteOn(60) },
    Event { offset: 35678, message: NoteOff(52) },
    Event { offset: 42321, message: AllNotesOff },
];

fn guards<const F: usize>() {
    let mut trial = Voice::<F>::new();
    let mut exact = trial.clone();
    let saved = Frame { j7_v: -0., bus_v: 1., c27_v: 2., panel_a: 3. };
    let mut failed = [saved; 16];
    for events in [
        [Event { offset: 0, message: NoteOn(57) }, Event { offset: 12, message: NoteOn(127) }],
        [Event { offset: 0, message: NoteOn(57) }, Event { offset: 16, message: AllNotesOff }],
        [Event { offset: 1, message: NoteOn(57) }, Event { offset: 0, message: AllNotesOff }],
    ] {
        assert!(trial.render(&events, &mut failed).is_err());
        assert!(failed.iter().all(|f| *f == saved && f.j7_v.is_sign_negative()));
        let mut a = [Frame::default(); 16];
        let mut b = a;
        let valid = [Event { offset: 3, message: NoteOn(57) }];
        trial.render(&valid, &mut a).unwrap();
        exact.render(&valid, &mut b).unwrap();
        assert_eq!(a, b);
    }
}

fn run<const F: usize>(size: usize) -> Result<(), Box<dyn std::error::Error>> {
    guards::<F>();
    let mut voice = Voice::<F>::new();
    let mut out = BufWriter::new(std::io::stdout().lock());
    let mut blocks = 0;
    let mut elapsed = 0_u128;
    let mut maximum = 0_u128;
    let mut over = 0;
    let mut allocations = 0;
    for start in (0..LENGTH).step_by(size) {
        let count = size.min(LENGTH - start);
        let mut events = [Event { offset: 0, message: AllNotesOff }; SCENE.len()];
        let mut n = 0;
        for event in SCENE {
            if (start..start + count).contains(&event.offset) {
                events[n] = Event { offset: event.offset - start, message: event.message };
                n += 1;
            }
        }
        let mut frames = [Frame::default(); voice::MAX_BLOCK];
        let before = ALLOCS.load(Relaxed);
        let t = Instant::now();
        let status = voice.render(&events[..n], &mut frames[..count]);
        let ns = t.elapsed().as_nanos();
        allocations += ALLOCS.load(Relaxed) - before;
        if let Err(error) = status {
            return Err(format!("render at {start}: {error:?}").into());
        }
        blocks += 1;
        elapsed += ns;
        maximum = maximum.max(ns);
        over += usize::from(3 * ns > 4_000_000);
        for f in &frames[..count] {
            for v in [f.j7_v, f.bus_v, f.c27_v, f.panel_a] {
                out.write_all(&v.to_le_bytes())?;
            }
        }
    }
    out.flush()?;
    eprintln!("PILOT,{F},{size},{blocks},{elapsed},{maximum},{over},{allocations}");
    Ok(())
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let argument = std::env::args().nth(1).ok_or("argument")?;
    if argument == "affinity" {
        return Ok(release_timing::affinity()?);
    }
    let size: usize = argument.parse()?;
    if !matches!(size, 64 | 128) {
        return Err("block size".into());
    }
    run::<FACTOR>(size)
}
