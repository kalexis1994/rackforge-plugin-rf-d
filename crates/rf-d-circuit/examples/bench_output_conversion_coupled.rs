//! Timing probe for board-4 Q1/Q12/Q17→C2→HI/LO/J7.
//! `cargo run --release -p rf-d-circuit --example bench_output_conversion_coupled`.

use std::hint::black_box;
use std::time::Instant;

use rf_d_circuit::output::OutputBoundary;
use rf_d_circuit::output_conversion::{
    initial_coupled_state, solve_coupled_step, Boundary, CoupledBoundary, DiodeParameters,
    Parameters as ConversionParameters,
};
use rf_d_circuit::{Parameters as HeadphoneParameters, SolverBudget};

const SAMPLE_RATE: usize = 48_000;
const BLOCK: usize = 64;

fn percentile(sorted: &[f64], fraction: f64) -> f64 {
    sorted[((sorted.len() - 1) as f64 * fraction).ceil() as usize]
}

fn scenario(sample: usize, base: Boundary) -> CoupledBoundary {
    let mut controls = base;
    controls.q17_base_v += black_box(
        0.02 * (2.0 * std::f64::consts::PI * 100.0 * sample as f64 / SAMPLE_RATE as f64).sin(),
    );
    CoupledBoundary {
        conversion: controls,
        output: OutputBoundary {
            q17_collector_v: 0.0,
            r20_lower_ohm: 2500.0,
            hi_load_ohm: 10000.0,
            lo_load_ohm: 100000.0,
            sw18_on: true,
            r21_lower_ohm: 2000.0,
            tip_load_ohm: Some(32.0),
            ring_load_ohm: Some(32.0),
            dt_s: 1.0 / SAMPLE_RATE as f64,
        },
    }
}

fn main() {
    let headphone = HeadphoneParameters {
        transistor_is_a: 1e-14,
        beta_forward: 160.0,
        beta_reverse: 5.0,
        temperature_k: 298.15,
        diode_is_a: 1.293_303_751_274_349e-9,
        diode_ideality: 1.5,
    };
    let conversion = ConversionParameters {
        transistor_is_a: 1e-14,
        beta_forward: 100.0,
        beta_reverse: 5.0,
        temperature_k: 298.15,
        diode: Some(DiodeParameters {
            is_a: headphone.diode_is_a,
            ideality: headphone.diode_ideality,
        }),
    };
    let base = Boundary {
        q1_base_v: 8.3,
        q12_base_v: 7.75,
        q17_base_v: 7.75,
        plus_v: 10.0,
    };
    let mut durations_us = Vec::with_capacity(SAMPLE_RATE / BLOCK);
    let mut iterations_total = 0usize;
    let mut iterations_max = 0usize;
    let mut ports_total = 0usize;
    let mut ports_max = 0usize;
    let mut fallbacks = 0usize;
    let mut max_kcl = 0.0_f64;
    let mut failures = 0usize;
    let mut final_j7 = 0.0;
    let mut predictor_trace = Vec::with_capacity(SAMPLE_RATE);
    for measured in [false, true] {
        let mut state = initial_coupled_state(conversion, base, headphone).expect("DC point");
        for block in 0..(SAMPLE_RATE / BLOCK) {
            let begin = Instant::now();
            for offset in 0..BLOCK {
                let sample = block * BLOCK + offset;
                match solve_coupled_step(
                    &mut state,
                    conversion,
                    headphone,
                    scenario(sample, base),
                    SolverBudget::default(),
                ) {
                    Ok(result) => {
                        if measured {
                            iterations_total += result.iterations;
                            iterations_max = iterations_max.max(result.iterations);
                            ports_total += result.output_port_evaluations;
                            ports_max = ports_max.max(result.output_port_evaluations);
                            fallbacks += usize::from(result.predictor_fallback);
                            max_kcl = max_kcl.max(result.max_conversion_kcl_residual_a);
                            predictor_trace.push([
                                result.output.j7_v,
                                result.output.j4_hi_v,
                                result.output.j5_lo_v,
                            ]);
                        }
                    }
                    Err(_) => failures += 1,
                }
            }
            if measured {
                durations_us.push(begin.elapsed().as_secs_f64() * 1e6);
            }
            final_j7 = black_box(state.output.panel.amp.node_v[11]);
        }
    }
    durations_us.sort_by(|a, b| a.total_cmp(b));
    let mean = durations_us.iter().sum::<f64>() / durations_us.len() as f64;
    println!(
        "conversion_c2_loaded_32_32: blocks={} samples={} deadline_us={:.1} mean_us={mean:.1} p99_us={:.1} max_us={:.1} mean_newton={:.2} max_newton={} mean_ports={:.2} max_ports={} fallbacks={} max_kcl_a={max_kcl:.3e} failures={} final_j7_v={final_j7:.9}",
        durations_us.len(), SAMPLE_RATE, BLOCK as f64 * 1e6 / SAMPLE_RATE as f64,
        percentile(&durations_us, 0.99), durations_us.last().unwrap(),
        iterations_total as f64 / SAMPLE_RATE as f64, iterations_max,
        ports_total as f64 / SAMPLE_RATE as f64, ports_max, fallbacks, failures,
    );
    assert_eq!(failures, 0, "timed or warm-up joint step failed");
    assert_eq!(predictor_trace.len(), SAMPLE_RATE);

    // Resetting the history to the current nodes disables extrapolation while
    // preserving the same nonlinear equations and convergence tolerance.
    let mut baseline = initial_coupled_state(conversion, base, headphone).expect("DC point");
    let mut baseline_durations = Vec::with_capacity(SAMPLE_RATE / BLOCK);
    let mut max_difference = [0.0_f64; 3];
    let mut square_difference = [0.0_f64; 3];
    let mut baseline_ports = 0usize;
    for block in 0..(SAMPLE_RATE / BLOCK) {
        let begin = Instant::now();
        for offset in 0..BLOCK {
            let sample = block * BLOCK + offset;
            baseline.previous_conversion_node_v = baseline.conversion.node_v;
            let result = solve_coupled_step(
                &mut baseline,
                conversion,
                headphone,
                scenario(sample, base),
                SolverBudget::default(),
            )
            .expect("baseline step");
            baseline_ports += result.output_port_evaluations;
            let actual = [
                result.output.j7_v,
                result.output.j4_hi_v,
                result.output.j5_lo_v,
            ];
            for channel in 0..3 {
                let difference = actual[channel] - predictor_trace[sample][channel];
                max_difference[channel] = max_difference[channel].max(difference.abs());
                square_difference[channel] += difference * difference;
            }
        }
        baseline_durations.push(begin.elapsed().as_secs_f64() * 1e6);
        black_box(baseline.output.panel.amp.node_v[11]);
    }
    baseline_durations.sort_by(|a, b| a.total_cmp(b));
    println!(
        "same_binary_no_predictor: mean_us={:.1} p99_us={:.1} max_us={:.1} mean_ports={:.2} max_abs_diff_v={max_difference:?} rms_diff_v={:?}",
        baseline_durations.iter().sum::<f64>() / baseline_durations.len() as f64,
        percentile(&baseline_durations, 0.99),
        baseline_durations.last().unwrap(),
        baseline_ports as f64 / SAMPLE_RATE as f64,
        square_difference.map(|v| (v / SAMPLE_RATE as f64).sqrt()),
    );
    assert!(
        max_difference.iter().all(|v| *v < 1e-7),
        "predictor changed the long-run output trace"
    );
}
