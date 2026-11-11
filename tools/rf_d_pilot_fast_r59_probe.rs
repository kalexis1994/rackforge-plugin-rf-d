//! Native measurements of the joined follower and fast receiver.
use crate::{
    fast_r59::{self, Frame, State},
    plant,
};
use std::{
    alloc::{GlobalAlloc, Layout, System},
    hint::black_box,
    io::{Read, Write},
    sync::atomic::{AtomicUsize, Ordering::Relaxed},
    time::Instant,
};
struct Counter;
pub(crate) static ALLOCS: AtomicUsize = AtomicUsize::new(0);
unsafe impl GlobalAlloc for Counter {
    unsafe fn alloc(&self, layout: Layout) -> *mut u8 {
        ALLOCS.fetch_add(1, Relaxed);
        unsafe { System.alloc(layout) }
    }
    unsafe fn dealloc(&self, pointer: *mut u8, layout: Layout) {
        unsafe { System.dealloc(pointer, layout) }
    }
    unsafe fn realloc(&self, pointer: *mut u8, layout: Layout, size: usize) -> *mut u8 {
        ALLOCS.fetch_add(1, Relaxed);
        unsafe { System.realloc(pointer, layout, size) }
    }
}
#[global_allocator]
static COUNTER: Counter = Counter;
const STEPS: usize = 256;

fn render(
    mut state: State,
    input: &[[f64; 4]],
    offset: usize,
    fresh: bool,
    mut emit: impl FnMut(Frame),
    #[cfg(pilot_r59_profile)] profile: &mut fast_r59::Profile,
) -> Result<(State, [f64; 4]), fast_r59::Error> {
    let mut stats = [0_f64; 4];
    for (i, &drive) in input.iter().enumerate() {
        let (next, frame) = fast_r59::advance(
            state,
            drive,
            fresh || (offset + i) % STEPS == 0,
            #[cfg(pilot_r59_profile)]
            profile,
        )?;
        stats[0] = stats[0].max(frame.iterations as f64);
        stats[1] = stats[1].max(frame.mismatch_v);
        stats[2] = stats[2].max(frame.mismatch_a);
        stats[3] += frame.tangent_calls as f64;
        state = next;
        emit(frame);
    }
    Ok((state, stats))
}

#[cfg(pilot_r59_profile)]
pub(crate) fn write_profile(out: &mut impl Write, profile: &fast_r59::Profile) -> std::io::Result<()> {
    for (calls, total_ns) in profile.stages {
        writeln!(out, "{calls},{total_ns}")?;
    }
    writeln!(
        out,
        "{},{},{},{},{},{},{:e},{:e}",
        profile.successful_root_evaluations,
        profile.reused_root_evaluations,
        profile.follower_fallbacks,
        profile.prediction_fallbacks,
        profile.q15_reused_endpoints,
        profile.r59_projected_histories,
        profile.r59_projection_error,
        profile.r59_direct_residual
    )
}

pub fn main() -> Result<(), Box<dyn std::error::Error>> {
    let mode = std::env::args().nth(1).ok_or("cached or fresh")?;
    assert!(matches!(mode.as_str(), "cached" | "fresh"));
    let fresh = mode == "fresh";
    let second = std::env::args().nth(2).unwrap_or_else(|| "128".into());
    let mut raw = Vec::new();
    std::io::stdin().read_to_end(&mut raw)?;
    assert_eq!(raw.len() % 8, 0);
    let values: Vec<_> = raw
        .chunks_exact(8)
        .map(|b| f64::from_le_bytes(b.try_into().unwrap()))
        .collect();
    assert!(values.len() >= 141 && (values.len() - 141) % 4 == 0);
    let audio = plant::State::from_nodal(
        &values[..68].try_into()?,
        &values[68..136].try_into()?,
        0.,
        plant::Drive::default(),
    )
    .map_err(|e| format!("initial audio: {e:?}"))?;
    let seed: [f64; 5] = values[136..141].try_into()?;
    let initial = State {
        audio,
        volume: [seed[0], seed[1], seed[3], seed[2], seed[4]],
        vca_base: values[32] + values[100],
        gradient: None,
        #[cfg(pilot_r59_reuse_cr6)]
        cr6: None,
        #[cfg(pilot_r59_predict_base_drift)]
        base_drift_v: 0.,
        #[cfg(pilot_r59_junction_predictor)]
        junction_direction: None,
        #[cfg(pilot_r59_predict_follower)]
        follower: None,
    };
    let input: Vec<[f64; 4]> = values[141..]
        .chunks_exact(4)
        .map(|v| v.try_into().unwrap())
        .collect();
    assert_eq!(input.len(), 2 * STEPS);
    let mut out = std::io::BufWriter::new(std::io::stdout().lock());
    #[cfg(pilot_r59_profile)]
    let mut profile = fast_r59::Profile::default();
    #[cfg(pilot_r59_reset_port)]
    if second == "reset-port" {
        let mut state = initial;
        for (tick, &drive) in input.iter().enumerate() {
            let mut query = |drive| {
                fast_r59::advance(
                    state,
                    drive,
                    fresh || tick % STEPS == 0,
                    #[cfg(pilot_r59_profile)]
                    &mut profile,
                )
                .map_err(|e| format!("reset port at tick {tick}: {e:?}"))
            };
            let (next, frame) = query(drive)?;
            let port = frame.reset_port;
            for value in [port.current_a].into_iter().chain(port.derivative_a_per_v) {
                out.write_all(&value.to_le_bytes())?;
            }
            for step in [1e-5, 5e-6] {
                for column in [1, 2] {
                    let mut low = drive;
                    let mut high = drive;
                    low[column] -= step;
                    high[column] += step;
                    let low = query(low)?.1.reset_port.current_a;
                    let high = query(high)?.1.reset_port.current_a;
                    out.write_all(&((high - low) / (2. * step)).to_le_bytes())?;
                }
            }
            state = next;
        }
        return Ok(());
    }
    if second == "bench" {
        let (warm, _) = render(
            initial,
            &input[..STEPS],
            0,
            fresh,
            |_| {},
            #[cfg(pilot_r59_profile)]
            &mut profile,
        )
        .map_err(|e| format!("warmup: {e:?}"))?;
        #[cfg(pilot_r59_profile)]
        let mut profile = fast_r59::Profile::default();
        let mut times = [0_u128; 64];
        let mut allocations = 0;
        for time in &mut times {
            let before = ALLOCS.load(Relaxed);
            let begin = Instant::now();
            black_box(
                render(
                    black_box(warm),
                    &input[STEPS..],
                    STEPS,
                    fresh,
                    |frame| {
                        black_box(frame);
                    },
                    #[cfg(pilot_r59_profile)]
                    &mut profile,
                )
                .map_err(|e| format!("bench: {e:?}"))?,
            );
            *time = begin.elapsed().as_nanos();
            allocations += ALLOCS.load(Relaxed) - before;
        }
        times.sort_unstable();
        writeln!(
            out,
            "64,{},{},{},{allocations}",
            times[32], times[63], times[63]
        )?;
        #[cfg(pilot_r59_profile)]
        write_profile(&mut out, &profile)?;
    } else {
        let size = 2 * second.parse::<usize>()?;
        assert!(matches!(size, 128 | 256));
        let mut state = initial;
        let mut stats = [0_f64; 4];
        let mut samples = Vec::with_capacity(13 * input.len());
        for (i, chunk) in input.chunks(size).enumerate() {
            let (next, measured) = render(
                state,
                chunk,
                i * size,
                fresh,
                |frame| {
                    let p = frame.ports;
                    samples.extend([
                        p.j7_v,
                        p.bus_v,
                        p.base_v - p.bus_v,
                        p.panel_a,
                        p.returns_a[0],
                        p.returns_a[1],
                        p.loads_v[0],
                        p.loads_v[1],
                    ]);
                    samples.extend([
                        frame.volume[0],
                        frame.volume[1],
                        frame.volume[3],
                        frame.volume[2],
                        frame.volume[4],
                    ]);
                },
                #[cfg(pilot_r59_profile)]
                &mut profile,
            )
            .map_err(|e| format!("render chunk {i}: {e:?}"))?;
            state = next;
            for j in 0..3 {
                stats[j] = stats[j].max(measured[j]);
            }
            stats[3] += measured[3];
        }
        for value in stats.into_iter().chain(samples) {
            out.write_all(&value.to_le_bytes())?;
        }
        if std::env::args().nth(3).as_deref() == Some("--charges") {
            for charge in state.audio.capacitor_charge_offsets_c() {
                out.write_all(&charge.to_le_bytes())?;
            }
        }
    }
    Ok(())
}
