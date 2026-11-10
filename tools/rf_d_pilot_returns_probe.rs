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
    if matches!(mode.as_str(), "electrical" | "electrical-ports" | "electrical-bench")
        || (cfg!(all(pilot_split_returns, pilot_receiver_handoff))
            && matches!(mode.as_str(), "electrical-resume" | "electrical-resume-bench"))
        || (cfg!(all(pilot_split_returns, pilot_receiver_handoff, pilot_receiver_ports))
            && matches!(mode.as_str(), "electrical-resume-tangent" | "electrical-resume-tangent-fd"
                | "electrical-resume-tangent-bench" | "electrical-resume-tangent-once-bench"))
    {
        let mut raw = Vec::new();
        std::io::stdin().lock().read_to_end(&mut raw)?;
        let mut state = plant::State::dc(1).unwrap();
        #[cfg(all(pilot_split_returns, pilot_receiver_handoff))]
        if mode.starts_with("electrical-resume") {
            const HEADER: usize = 139 * 8;
            assert!(raw.len() >= HEADER);
            let read = |k| f64::from_le_bytes(raw[8 * k..8 * (k + 1)].try_into().unwrap());
            state = plant::State::from_nodal(
                &std::array::from_fn(|k| read(k)),
                &std::array::from_fn(|k| read(68 + k)),
                read(136),
                Drive { volume_delta_v: read(137), filter_delta_v: read(138) },
            ).map_err(|e| format!("handoff: {e:?}"))?;
            raw.drain(..HEADER);
            if !mode.ends_with("-bench") {
                for value in state.capacitor_charge_offsets_c() {
                    out.write_all(&value.to_le_bytes())?;
                }
            }
        }
        assert_eq!(raw.len() % 24, 0);
        if mode.ends_with("-bench") {
            let rate: usize = std::env::args().nth(2).ok_or("circuit rate")?.parse()?;
            assert!(matches!(rate, 96_000 | 192_000));
            assert_eq!(raw.len() / 24, rate * 128 / 48_000);
            let inputs: Vec<_> = raw.chunks_exact(24).map(|row| {
                let read = |k| f64::from_le_bytes(row[k..k + 8].try_into().unwrap());
                (read(0), Drive { volume_delta_v: read(8), filter_delta_v: read(16) })
            }).collect();
            const PASSES: usize = 64;
            let initial = state;
            let mut times = [0_u128; PASSES];
            let mut allocations = 0;
            for pass in 0..=PASSES {
                let before = ALLOCS.load(Relaxed);
                let begin = Instant::now();
                let mut state = initial;
                for (index, &(signal, drive)) in inputs.iter().enumerate() {
                    #[cfg(pilot_receiver_ports)]
                    if mode == "electrical-resume-tangent-bench"
                        || (mode == "electrical-resume-tangent-once-bench" && index == 0)
                    {
                        let trial = plant::trial_with_load_tangent(state, std::hint::black_box(signal), drive)
                            .map_err(|e| format!("tangent trial: {e:?}"))?;
                        state = trial.state;
                        std::hint::black_box(trial);
                        continue;
                    }
                    let ports = plant::step(&mut state, std::hint::black_box(signal), drive)
                        .map_err(|e| format!("{e:?}"))?;
                    std::hint::black_box(ports);
                }
                std::hint::black_box(state);
                let elapsed = begin.elapsed().as_nanos();
                if pass > 0 {
                    allocations += ALLOCS.load(Relaxed) - before;
                    times[pass - 1] = elapsed;
                }
            }
            times.sort_unstable();
            writeln!(out, "{PASSES},{},{},{},{allocations}",
                     times[PASSES / 2], times[PASSES * 99 / 100], times[PASSES - 1])?;
            return Ok(());
        }
        for row in raw.chunks_exact(24) {
            let read = |k| f64::from_le_bytes(row[k..k + 8].try_into().unwrap());
            #[cfg(pilot_receiver_ports)]
            if matches!(mode.as_str(), "electrical-resume-tangent" | "electrical-resume-tangent-fd") {
                let signal = read(0);
                let drive = Drive { volume_delta_v: read(8), filter_delta_v: read(16) };
                let old = state;
                let trial = plant::trial_with_load_tangent(old, signal, drive)
                    .map_err(|e| format!("tangent trial: {e:?}"))?;
                state = trial.state;
                let p = trial.ports;
                write(&mut out, [p.j7_v, p.bus_v, p.base_v - p.bus_v, p.panel_a, p.returns_a[0], p.returns_a[1]])?;
                for value in p.loads_v.into_iter().chain(trial.load_jacobian.into_iter().flatten()) {
                    out.write_all(&value.to_le_bytes())?;
                }
                if mode.ends_with("-fd") {
                    for epsilon in [1e-5, 5e-6] {
                        let mut difference = [[0.; 2]; 2];
                        for column in 0..2 {
                            let mut shifted = [drive; 2];
                            for (drive, sign) in shifted.iter_mut().zip([-1., 1.]) {
                                if column == 0 { drive.volume_delta_v += sign * epsilon; }
                                else { drive.filter_delta_v += sign * epsilon; }
                            }
                            let mut low = old;
                            let mut high = old;
                            let a = plant::step(&mut low, signal, shifted[0]).map_err(|e| format!("FD low: {e:?}"))?;
                            let b = plant::step(&mut high, signal, shifted[1]).map_err(|e| format!("FD high: {e:?}"))?;
                            for row in 0..2 {
                                difference[row][column] = (b.loads_v[row] - a.loads_v[row]) / (2. * epsilon);
                            }
                        }
                        for value in difference.into_iter().flatten() {
                            out.write_all(&value.to_le_bytes())?;
                        }
                    }
                }
                continue;
            }
            let p = plant::step(&mut state, read(0), Drive {
                volume_delta_v: read(8), filter_delta_v: read(16),
            }).map_err(|e| format!("{e:?}"))?;
            write(&mut out, [p.j7_v, p.bus_v, p.base_v - p.bus_v, p.panel_a, p.returns_a[0], p.returns_a[1]])?;
            if matches!(mode.as_str(), "electrical-ports" | "electrical-resume") {
                for value in p.loads_v {
                    out.write_all(&value.to_le_bytes())?;
                }
            }
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
