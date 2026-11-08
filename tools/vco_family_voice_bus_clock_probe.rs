use crate::{audit, dump, family::Family, parameters, release_timing, solver, voice, StepError};
use voice::{Controls, Parameters, State, BUS, J7, N};
use std::{error::Error, fs, time::{Duration, Instant}};

const TICKS: usize = 4096;
const FINE: usize = TICKS / 512;
const CLOCK: f64 = 1. / (48_000 * TICKS) as f64;
const VT: f64 = 1.380649e-23 * 298.15 / 1.602176634e-19;
const LIMIT: f64 = VT / 32.;
const COLLECTORS: [usize; 4] = [26, 28, 40, 42];

fn value(state: &State, index: usize) -> f64 {
    state.high[index] + state.low[index]
}

fn collectors(state: &State) -> [f64; 4] {
    COLLECTORS.map(|k| value(state, k))
}

fn order(v: [f64; 4]) -> [bool; 2] {
    [v[0] >= v[1], v[2] >= v[3]]
}

fn move_from(old: [f64; 4], now: [f64; 4]) -> f64 {
    old.into_iter().zip(now).fold(0_f64, |m, (a, b)| m.max((a - b).abs()))
}

pub fn run(path: &str, label: &str, cap: usize) -> Result<(), Box<dyn Error>> {
    if !matches!(label, "negative" | "positive") || !matches!(cap, 32 | 64 | 128 | 256) {
        return Err("clock domain".into());
    }
    let raw = fs::read(path)?;
    assert_eq!(raw.len(), 2 * N * 8);
    let number = |k: usize| f64::from_le_bytes(raw[8 * k..8 * k + 8].try_into().unwrap());
    let mut state = State {
        high: std::array::from_fn(number), low: std::array::from_fn(|k| number(N + k)), optional: false,
    };
    let mut phase = if label == "negative" { 0.37 } else { 0. };
    let family = Family::prepare(-1.6).unwrap();
    let mut work = solver::Workspace::new();
    let mut p = Parameters::new(parameters()).map_err(|e| format!("{e:?}"))?;
    let ceiling = TICKS / cap;
    let mut proposal = ceiling;
    let mut elapsed = Duration::ZERO;
    let mut widths = [0usize; 13];
    let (mut guard_retries, mut newton_retries, mut deepest) = (0, 0, 0);
    let (mut iterations, mut audits) = (0, 0);
    let (mut max_residual, mut max_correction) = (0_f64, 0_f64);
    let mut worst_audit = [0_f64; 5];
    let mut bus = [value(&state, BUS); 2];
    let thread = release_timing::thread_ns()?;
    dump(0, phase, state);
    for frame in 0..128 {
        let controls = Controls {
            key: if label == "negative" && (16..96).contains(&frame) { 10. } else { 0. },
            optional: false, short: false,
        };
        let mut within = 0;
        while within < TICKS {
            let tick = frame * TICKS + within;
            let before = collectors(&state);
            let initial_order = order(before);
            let mut width = proposal;
            while tick % width != 0 || width > TICKS - within {
                width /= 2;
            }
            let (q, motion, end) = loop {
                p.time = tick as f64 * CLOCK;
                let timer = Instant::now();
                let trial = voice::radau(&mut work, &family, p, state, phase, controls, width as f64 * CLOCK, 80);
                elapsed += timer.elapsed();
                match trial {
                    Ok(q) => {
                        let intermediate = collectors(&q.stages.chain[0].now);
                        let end = collectors(&q.stages.chain[1].now);
                        let motion = move_from(before, intermediate).max(move_from(before, end));
                        if width > FINE && (motion > LIMIT || order(intermediate) != initial_order || order(end) != initial_order) {
                            guard_retries += 1;
                            width /= 2;
                            continue;
                        }
                        break (q, motion, end);
                    }
                    Err(StepError::NoDecrease | StepError::IterationBudget) if width > 1 => {
                        newton_retries += 1;
                        width /= 2;
                        deepest = deepest.max(ceiling.ilog2() - width.ilog2());
                    }
                    Err(error) => return Err(format!("clock {label} cap={cap} tick={tick} span={width}: {error:?}").into()),
                }
            };
            let final_order = order(end);
            let crossing = initial_order != final_order;
            if crossing {
                for pair in 0..2 {
                    if initial_order[pair] != final_order[pair] {
                        println!("SWITCH,{pair},{tick},{},{}", tick + width, u8::from(final_order[pair]));
                    }
                }
            }
            if crossing || (within == 0 && [0, 15, 16, 48, 76, 77, 78, 95, 96, 127].contains(&frame)) {
                for (maximum, measured) in worst_audit.iter_mut().zip(
                    audit(&family, p, state, phase, controls, width as f64 * CLOCK, &q)?)
                {
                    *maximum = maximum.max(measured);
                }
                audits += 1;
            }
            for stage in &q.stages.chain {
                bus[0] = bus[0].min(value(&stage.now, BUS));
                bus[1] = bus[1].max(value(&stage.now, BUS));
            }
            state = q.stages.chain[1].now;
            phase = q.stages.phase[1];
            iterations += q.iterations;
            max_residual = max_residual.max(q.residual_a);
            max_correction = max_correction.max(q.correction_v);
            widths[width.ilog2() as usize] += 1;
            within += width;
            proposal = if motion < LIMIT / 4. { (2 * width).min(ceiling) } else { width };
        }
        dump(frame + 1, phase, state);
    }
    println!("THREAD_CPU_NS,{}", release_timing::thread_ns()? - thread);
    print!("CLOCK,{guard_retries},{newton_retries},{audits}");
    for n in widths {
        print!(",{n}");
    }
    println!();
    let [current, charge, c27, tangent, panel] = worst_audit;
    println!("END,{cap},{iterations},{:.17e},{max_residual:.17e},{max_correction:.17e},\
        {:.17e},{:.17e},{:.17e},{current:.17e},{charge:.17e},{c27:.17e},{tangent:.17e},{panel:.17e},{newton_retries},{deepest}",
        elapsed.as_secs_f64(), bus[0], bus[1], value(&state, J7));
    Ok(())
}
