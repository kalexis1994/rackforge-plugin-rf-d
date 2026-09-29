//! Offline timing probe. `cargo run --release -p rf-d-circuit --example bench_board3`.
//! Allocation and printing occur only outside the measured processing blocks.

use std::hint::black_box;
use std::time::Instant;

use rf_d_circuit::{initial_state, step, Parameters, SolverBudget};

const SAMPLE_RATE: usize = 48_000;
const BLOCK: usize = 64;

fn percentile(sorted: &[f64], fraction: f64) -> f64 {
    let index = ((sorted.len() - 1) as f64 * fraction).ceil() as usize;
    sorted[index]
}

fn run(name: &str, tip: Option<f64>, ring: Option<f64>, peak_v: f64) {
    // Same imposed 300 K device scenario as the frozen board-3 vectors.
    let p = Parameters {
        transistor_is_a: 1e-14,
        beta_forward: 160.0,
        beta_reverse: 5.0,
        temperature_k: 300.0,
        diode_is_a: 1.446_588_643_457_551_9e-9,
        diode_ideality: 1.5,
    };
    let mut state = initial_state(p).expect("DC operating point");
    let mut durations_us = Vec::with_capacity(SAMPLE_RATE / BLOCK);
    let mut iteration_total = 0usize;
    let mut iteration_max = 0usize;
    let mut residual_max = 0.0_f64;
    let mut errors = 0usize;
    let budget = SolverBudget::default();

    // One warm-up pass has the same stimulus and is excluded from timing.
    for measured in [false, true] {
        state = initial_state(p).expect("DC reset");
        for block in 0..(SAMPLE_RATE / BLOCK) {
            let begin = Instant::now();
            for offset in 0..BLOCK {
                let sample = block * BLOCK + offset;
                let sine =
                    (2.0 * std::f64::consts::PI * 100.0 * sample as f64 / SAMPLE_RATE as f64).sin();
                // Halfway through, reverse polarity at equal magnitude.
                let polarity = if sample < SAMPLE_RATE / 2 { 1.0 } else { -1.0 };
                let input = black_box(peak_v * polarity * sine);
                match step(
                    &mut state,
                    p,
                    input,
                    1.0 / SAMPLE_RATE as f64,
                    tip,
                    ring,
                    budget,
                ) {
                    Ok(d) => {
                        if measured {
                            iteration_total += d.iterations;
                            iteration_max = iteration_max.max(d.iterations);
                            residual_max = residual_max.max(d.max_kcl_residual_a);
                        }
                    }
                    Err(_) => {
                        errors += 1;
                    }
                }
            }
            if measured {
                durations_us.push(begin.elapsed().as_secs_f64() * 1e6);
            }
            black_box(state.node_v[11]);
        }
    }
    durations_us.sort_by(|a, b| a.total_cmp(b));
    let total_us: f64 = durations_us.iter().sum();
    println!(
        "{name}: blocks={} samples={} deadline_us={:.1} mean_us={:.1} p99_us={:.1} max_us={:.1} mean_newton={:.2} max_newton={} max_kcl_a={:.3e} failures={} final_j7_v={:.6}",
        durations_us.len(), SAMPLE_RATE, BLOCK as f64 * 1e6 / SAMPLE_RATE as f64,
        total_us / durations_us.len() as f64, percentile(&durations_us, 0.99),
        durations_us.last().unwrap(), iteration_total as f64 / SAMPLE_RATE as f64,
        iteration_max, residual_max, errors, state.node_v[11]
    );
    assert_eq!(errors, 0, "a timed or warm-up step failed");
}

fn main() {
    run("loaded_32_32_0p5v", Some(32.0), Some(32.0), 0.5);
    run("open_0p5v", None, None, 0.5);
    run("loaded_32_32_1v", Some(32.0), Some(32.0), 1.0);
}
