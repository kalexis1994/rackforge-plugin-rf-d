//! Offline nested panel/board-3 timing probe.
//! `cargo run --release -p rf-d-circuit --example bench_panel`.

use std::hint::black_box;
use std::time::Instant;

use rf_d_circuit::panel::{initial_panel_state, solve_panel_boundary, PanelBoundary};
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
    let mut state = initial_panel_state(p).expect("DC point");
    for measured in [false, true] {
        state = initial_panel_state(p).expect("DC reset");
        for block in 0..(SAMPLE_RATE / BLOCK) {
            let begin = Instant::now();
            for offset in 0..BLOCK {
                let sample = block * BLOCK + offset;
                let source = black_box(
                    0.5 * (2.0 * std::f64::consts::PI * 100.0 * sample as f64 / SAMPLE_RATE as f64)
                        .sin(),
                );
                match solve_panel_boundary(
                    &mut state,
                    p,
                    PanelBoundary {
                        c2_right_v: source,
                        r21_lower_ohm: 2000.0,
                        dt_s: 1.0 / SAMPLE_RATE as f64,
                        tip_load_ohm: Some(32.0),
                        ring_load_ohm: Some(32.0),
                    },
                    SolverBudget::default(),
                ) {
                    Ok(result) => {
                        if measured {
                            outer_total += result.diagnostics.outer_iterations;
                            outer_max = outer_max.max(result.diagnostics.outer_iterations);
                            max_kcl = max_kcl.max(result.diagnostics.max_panel_kcl_residual_a);
                        }
                    }
                    Err(_) => failures += 1,
                }
            }
            if measured {
                durations_us.push(begin.elapsed().as_secs_f64() * 1e6);
            }
            black_box(state.amp.node_v[11]);
        }
    }
    durations_us.sort_by(|a, b| a.total_cmp(b));
    let mean = durations_us.iter().sum::<f64>() / durations_us.len() as f64;
    println!(
        "panel_loaded_32_32_0p5v: blocks={} samples={} deadline_us={:.1} mean_us={mean:.1} p99_us={:.1} max_us={:.1} mean_outer_newton={:.2} max_outer_newton={} max_panel_kcl_a={max_kcl:.3e} failures={} final_j7_v={:.6}",
        durations_us.len(), SAMPLE_RATE, BLOCK as f64 * 1e6 / SAMPLE_RATE as f64,
        percentile(&durations_us, 0.99), durations_us.last().unwrap(),
        outer_total as f64 / SAMPLE_RATE as f64, outer_max, failures, state.amp.node_v[11]
    );
    assert_eq!(failures, 0, "timed or warm-up panel step failed");
}
