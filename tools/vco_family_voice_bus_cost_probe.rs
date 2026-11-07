use crate::{audit, dump, family::Family, graph, parameters, solver, voice};
use crate::{adaptive as integrator, State, Controls, Parameters, BUS, J7, N};
use std::{error::Error, fs, time::{Duration, Instant}};

#[cfg(cost_profile)]
mod instrumentation {
    use std::sync::atomic::{AtomicU64, Ordering::Relaxed};
    use std::time::Instant;

    static TIME: [AtomicU64; 3] = [const { AtomicU64::new(0) }; 3];
    static CALLS: [AtomicU64; 3] = [const { AtomicU64::new(0) }; 3];

    pub fn measure<T>(slot: usize, operation: impl FnOnce() -> T) -> T {
        let start = Instant::now();
        let value = operation();
        TIME[slot].fetch_add(start.elapsed().as_nanos() as u64, Relaxed);
        CALLS[slot].fetch_add(1, Relaxed);
        value
    }

    pub fn report() {
        print!("PROFILE");
        for (time, calls) in TIME.iter().zip(CALLS.iter()) {
            print!(",{},{}", time.load(Relaxed), calls.load(Relaxed));
        }
        println!();
    }
}

#[cfg(cost_profile)]
pub use instrumentation::measure;

fn inputs(path: &str) -> Result<(State, f64), Box<dyn Error>> {
    let raw = fs::read(path)?;
    assert_eq!(raw.len(), (2 * N + 1) * 8);
    let value = |i: usize| f64::from_le_bytes(raw[i * 8..(i + 1) * 8].try_into().unwrap());
    Ok((State {
        high: std::array::from_fn(value), low: std::array::from_fn(|i| value(i + N)), optional: false,
    }, value(2 * N)))
}

fn value(state: State, index: usize) -> f64 {
    state.high[index] + state.low[index]
}

fn controls(label: &str, frame: usize) -> Controls {
    assert!(matches!(label, "negative" | "positive"));
    let key = if label == "negative" && (16..96).contains(&frame) { 10. } else { 0. };
    Controls { key, optional: false, short: false }
}

#[cfg(cost_profile)]
pub fn profile(path: &str, label: &str) -> Result<(), Box<dyn Error>> {
    let (mut state, mut phase) = inputs(path)?;
    let (first, last, count) = if label == "negative" { (15, 20, 64) } else { (76, 81, 512) };
    let h = 1. / (48_000 * count) as f64;
    let family = Family::prepare(-1.6).unwrap();
    let mut work = solver::Workspace::new();
    let mut p = Parameters::new(parameters()).map_err(|e| format!("{e:?}"))?;
    let start = Instant::now();
    for frame in first..last {
        let c = controls(label, frame);
        for sub in 0..count {
            let tick = (frame * count + sub) * 8;
            p.time = tick as f64 * (h / 8.);
            let step = voice::radau(&mut work, &family, p, state, phase, c, h, 80)
                .map_err(|e| format!("profile {label} {frame} {sub}: {e:?}"))?;
            state = step.stages.chain[1].now;
            phase = step.stages.phase[1];
        }
    }
    println!("PROFILE_WALL,{}", start.elapsed().as_nanos());
    dump(last, phase, state);
    instrumentation::report();
    Ok(())
}

fn collectors(s: State) -> [f64; 2] {
    [value(s, 26) - value(s, 28), value(s, 40) - value(s, 42)]
}

pub fn adaptive(path: &str, label: &str) -> Result<(), Box<dyn Error>> {
    let (mut state, mut phase) = inputs(path)?;
    let family = Family::prepare(-1.6).unwrap();
    let mut work = solver::Workspace::new();
    let mut p = Parameters::new(parameters()).map_err(|e| format!("{e:?}"))?;
    let clock = 1. / (48_000 * integrator::TICKS) as f64;
    let mut elapsed = Duration::ZERO;
    let mut min_span = usize::MAX;
    let mut max_span = 0;
    let mut max_error = 0_f64;
    let mut accepted = 0;
    let mut rejected = 0;
    let mut proposal = integrator::MAX_STEP;
    let (mut max_residual, mut max_correction) = (0_f64, 0_f64);
    let mut bus = [value(state, BUS); 2];
    let mut iterations = 0;
    let mut worst_audit = [0_f64; 5];
    let mut n_audits = 0;
    let mut switches = Vec::with_capacity(4);
    dump(0, phase, state);
    for frame in 0..128 {
        let c = controls(label, frame);
        let mut completed = 0;
        while completed < integrator::TICKS {
            let tick = frame * integrator::TICKS + completed;
            let remaining = integrator::TICKS - completed;
            let width = proposal.min(1_usize << remaining.ilog2());
            let start = Instant::now();
            let q = integrator::advance(&mut work, &family, p, state, phase, c, tick, width, &mut rejected);
            elapsed += start.elapsed();
            let q = q.map_err(|e| format!("adaptive {label} {frame} {completed} span={width}: {e:?}"))?;
            min_span = min_span.min(q.ticks);
            max_span = max_span.max(q.ticks);
            max_error = max_error.max(q.error);
            accepted += 1;
            let half_ticks = q.ticks / 2;
            for (index, half) in q.half.iter().enumerate() {
                let step_tick = tick + index * half_ticks;
                let next = half.stages.chain[1].now;
                let mut crossed = false;
                for (pair, (before, after)) in collectors(state).into_iter().zip(collectors(next)).enumerate() {
                    if before.is_sign_positive() != after.is_sign_positive() {
                        switches.push((pair, step_tick, step_tick + half_ticks, after.is_sign_positive()));
                        crossed = true;
                    }
                }
                if crossed || (index == 0 && completed == 0 && [0, 16, 48, 77, 78, 96, 127].contains(&frame)) {
                    p.time = step_tick as f64 * clock;
                    for (maximum, measured) in worst_audit.iter_mut().zip(
                        audit(&family, p, state, phase, c, half_ticks as f64 * clock, half)?)
                    {
                        *maximum = maximum.max(measured);
                    }
                    n_audits += 1;
                }
                for s in &half.stages.chain {
                    bus[0] = bus[0].min(value(s.now, BUS));
                    bus[1] = bus[1].max(value(s.now, BUS));
                }
                state = next;
                phase = half.stages.phase[1];
                iterations += half.iterations;
                max_residual = max_residual.max(half.residual_a);
                max_correction = max_correction.max(half.correction_v);
            }
            completed += q.ticks;
            proposal = if q.error < 0.0625 { (q.ticks * 2).min(integrator::MAX_STEP) } else { q.ticks };
        }
        dump(frame + 1, phase, state);
    }
    let [current, charge, c27, tangent, panel] = worst_audit;
    println!("END,0,{iterations},{:.17e},{max_residual:.17e},{max_correction:.17e},\
        {:.17e},{:.17e},{:.17e},{current:.17e},{charge:.17e},{c27:.17e},{tangent:.17e},{panel:.17e},{rejected},0",
        elapsed.as_secs_f64(), bus[0], bus[1], value(state, J7));
    println!("ADAPT,{accepted},{rejected},{min_span},{max_span},{max_error:.17e},{n_audits}");
    for (pair, first, last, direction) in switches {
        println!("SWITCH,{pair},{first},{last},{}", u8::from(direction));
    }
    Ok(())
}
