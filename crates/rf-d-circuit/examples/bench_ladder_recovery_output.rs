//! Conditional ladder to J7 deadline probe, with C10 open.
//! `cargo run --release -p rf-d-circuit --example bench_ladder_recovery_output`.

use std::hint::black_box;
use std::time::Instant;

use rf_d_circuit::ladder_recovery_output::{
    initial_state, step, step_with_emphasis, Boundary, Parameters,
};
use rf_d_circuit::output::OutputBoundary;
use rf_d_circuit::output_conversion::{DiodeParameters, Parameters as ConversionParameters};
use rf_d_circuit::output_conversion_c4::BoundaryC4;
use rf_d_circuit::recovery_vca_output::Boundary as RecoveryBoundary;
use rf_d_circuit::vca1_output::Boundary as FirstBoundary;
use rf_d_circuit::vca2_output::{Boundary as SecondBoundary, Parameters as TransistorParameters};
use rf_d_circuit::{Parameters as HeadphoneParameters, SolverBudget};

const SAMPLE_RATE: usize = 48_000;
const BLOCK: usize = 64;
const MEASURED_SAMPLES: usize = 8192;
const SEED: [f64; 16] = [
    7.8431017460109675,
    6.372499040594479,
    4.9019061730679665,
    3.43132324181033,
    1.9607503461842566,
    1.4561733893906676,
    1.9607344627142946,
    1.9607223099167141,
    2.9270178181494293,
    4.397856399069791,
    5.868704916259031,
    7.339563271338244,
    2.927029970947009,
    4.397868551867372,
    5.868717069056611,
    7.339575424135825,
];

fn percentile(sorted: &[f64], fraction: f64) -> f64 {
    sorted[((sorted.len() - 1) as f64 * fraction).ceil() as usize]
}

fn boundary(sample: usize) -> Boundary {
    let sine =
        black_box((2.0 * std::f64::consts::PI * 100.0 * sample as f64 / SAMPLE_RATE as f64).sin());
    Boundary {
        bus_v: 0.1 * sine,
        recovery: RecoveryBoundary {
            ladder_left_v: 0.0,
            ladder_right_v: 0.0,
            vca: FirstBoundary {
                recover_collector_v: 0.0,
                loudness_v: 2.0,
                first_balance_left_ohm: 12.5,
                second: SecondBoundary {
                    q14_base_v: 0.0,
                    q13_base_v: 0.0,
                    q21_base_v: 2.0,
                    first_balance_wiper_v: 0.0,
                    second_balance_left_ohm: 50.0,
                    minus_v: -10.0,
                    output: BoundaryC4 {
                        second_balance_wiper_v: 0.0,
                        q12_base_v: 0.0,
                        q17_base_v: 0.0,
                        plus_v: 10.0,
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
                    },
                },
            },
        },
    }
}

fn main() {
    let closed = std::env::args().any(|arg| arg == "--emphasis");
    let transistors = TransistorParameters {
        transistor_is_a: 1e-14,
        beta_forward: 100.0,
        beta_reverse: 5.0,
        temperature_k: 298.15,
    };
    let conversion = ConversionParameters {
        transistor_is_a: 1e-14,
        beta_forward: 100.0,
        beta_reverse: 5.0,
        temperature_k: 298.15,
        diode: Some(DiodeParameters {
            is_a: 1.293_303_751_274_349e-9,
            ideality: 1.5,
        }),
    };
    let headphone = HeadphoneParameters {
        transistor_is_a: 1e-14,
        beta_forward: 160.0,
        beta_reverse: 5.0,
        temperature_k: 298.15,
        diode_is_a: 1.293_303_751_274_349e-9,
        diode_ideality: 1.5,
    };
    let ladder = Parameters {
        transistor: transistors,
        tail_current_a: 6.824_898_505_905_974e-6,
        r61_ohm: 200.0,
        r30_ohm: 830.0,
    };
    let mut durations_us = Vec::with_capacity(MEASURED_SAMPLES / BLOCK);
    let mut evaluations = 0usize;
    let mut max_evaluations = 0usize;
    let mut fallbacks = 0usize;
    let mut failures = 0usize;
    let mut max_kcl = 0.0_f64;
    let mut final_j7 = 0.0;
    for measured in [false, true] {
        let mut state = initial_state(ladder, conversion, headphone, boundary(0), SEED)
            .expect("ladder/recovery/VCA DC");
        for block in 0..(MEASURED_SAMPLES / BLOCK) {
            let begin = Instant::now();
            for offset in 0..BLOCK {
                let sample = block * BLOCK + offset;
                let outcome = if closed {
                    step_with_emphasis(
                        &mut state,
                        ladder,
                        conversion,
                        headphone,
                        boundary(sample),
                        25_000.0,
                        SolverBudget::default(),
                    )
                } else {
                    step(
                        &mut state,
                        ladder,
                        conversion,
                        headphone,
                        boundary(sample),
                        SolverBudget::default(),
                    )
                };
                match outcome {
                    Ok(result) => {
                        if measured {
                            evaluations += result.recovery_port_evaluations;
                            max_evaluations = max_evaluations.max(result.recovery_port_evaluations);
                            fallbacks += usize::from(result.predictor_fallback);
                            max_kcl = max_kcl.max(result.max_ladder_kcl_residual_a);
                        }
                    }
                    Err(_) => failures += 1,
                }
            }
            if measured {
                durations_us.push(begin.elapsed().as_secs_f64() * 1e6);
            }
            final_j7 = black_box(state.recovery.vca.second.downstream.output.panel.amp.node_v[11]);
        }
    }
    durations_us.sort_by(|a, b| a.total_cmp(b));
    let mean = durations_us.iter().sum::<f64>() / durations_us.len() as f64;
    println!(
        "ladder_to_j7: emphasis_closed={closed} blocks={} samples={} deadline_us={:.1} mean_us={mean:.1} p99_us={:.1} max_us={:.1} mean_recovery_evals={:.2} max_recovery_evals={} fallbacks={} max_kcl_a={max_kcl:.3e} failures={} final_j7_v={final_j7:.9}",
        durations_us.len(), MEASURED_SAMPLES, BLOCK as f64*1e6/SAMPLE_RATE as f64,
        percentile(&durations_us,0.99), durations_us.last().unwrap(),
        evaluations as f64/MEASURED_SAMPLES as f64, max_evaluations,
        fallbacks, failures,
    );
    assert_eq!(failures, 0);
}
