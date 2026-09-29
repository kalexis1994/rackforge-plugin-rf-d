//! Offline Q17c→C2→HI/LO/J7 timing probe.
//! `cargo run --release -p rf-d-circuit --example bench_output`.

use std::hint::black_box;
use std::time::Instant;

use rf_d_circuit::output::{initial_output_state, solve_output_boundary, OutputBoundary};
use rf_d_circuit::{Parameters, SolverBudget};

const SAMPLE_RATE: usize = 48_000;
const BLOCK: usize = 64;

fn percentile(sorted: &[f64], fraction: f64) -> f64 {
    sorted[((sorted.len() - 1) as f64 * fraction).ceil() as usize]
}

fn main() {
    let p = Parameters {
        transistor_is_a: 1e-14,
        beta_forward: 160.0,
        beta_reverse: 5.0,
        temperature_k: 300.0,
        diode_is_a: 1.446_588_643_457_551_9e-9,
        diode_ideality: 1.5,
    };
    let mut durations_us = Vec::with_capacity(SAMPLE_RATE / BLOCK);
    let mut outer_total = 0usize;
    let mut outer_max = 0usize;
    let mut max_kcl = 0.0_f64;
    let mut failures = 0usize;
    let mut state = initial_output_state(p, 5.0).expect("DC point");
    for measured in [false, true] {
        state = initial_output_state(p, 5.0).expect("DC reset");
        for block in 0..(SAMPLE_RATE / BLOCK) {
            let begin = Instant::now();
            for offset in 0..BLOCK {
                let sample = block * BLOCK + offset;
                let source = black_box(
                    5.0 + 0.5
                        * (2.0 * std::f64::consts::PI * 100.0 * sample as f64 / SAMPLE_RATE as f64)
                            .sin(),
                );
                match solve_output_boundary(
                    &mut state,
                    p,
                    OutputBoundary {
                        q17_collector_v: source,
                        r20_lower_ohm: 2500.0,
                        hi_load_ohm: 10000.0,
                        lo_load_ohm: 100000.0,
                        sw18_on: true,
                        r21_lower_ohm: 2000.0,
                        tip_load_ohm: Some(32.0),
                        ring_load_ohm: Some(32.0),
                        dt_s: 1.0 / SAMPLE_RATE as f64,
                    },
                    SolverBudget::default(),
                ) {
                    Ok(result) => {
                        if measured {
                            outer_total += result.outer_iterations;
                            outer_max = outer_max.max(result.outer_iterations);
                            max_kcl = max_kcl.max(result.max_c2_right_kcl_residual_a);
                        }
                    }
                    Err(_) => failures += 1,
                }
            }
            if measured {
                durations_us.push(begin.elapsed().as_secs_f64() * 1e6);
            }
            black_box(state.panel.amp.node_v[11]);
        }
    }
    durations_us.sort_by(|a, b| a.total_cmp(b));
    let mean = durations_us.iter().sum::<f64>() / durations_us.len() as f64;
    println!(
        "output_loaded_32_32_0p5v: blocks={} samples={} deadline_us={:.1} mean_us={mean:.1} p99_us={:.1} max_us={:.1} mean_outer_newton={:.2} max_outer_newton={} max_c2_kcl_a={max_kcl:.3e} failures={} final_j7_v={:.9}",
        durations_us.len(), SAMPLE_RATE, BLOCK as f64 * 1e6 / SAMPLE_RATE as f64,
        percentile(&durations_us, 0.99), durations_us.last().unwrap(),
        outer_total as f64 / SAMPLE_RATE as f64, outer_max, failures,
        state.panel.amp.node_v[11]
    );
    assert_eq!(failures, 0, "timed or warm-up output step failed");
}
