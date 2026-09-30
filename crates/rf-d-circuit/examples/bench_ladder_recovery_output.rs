//! Conditional ladder to J7 deadline probe, with C10 open.
//! `cargo run --release -p rf-d-circuit --example bench_ladder_recovery_output`.

use std::hint::black_box;
use std::time::Instant;

use rf_d_circuit::cutoff;
use rf_d_circuit::cutoff_ladder_output;
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

enum BenchState {
    Fixed(rf_d_circuit::ladder_recovery_output::State),
    Controlled(cutoff_ladder_output::State),
    Global(rf_d_circuit::circuit66::State),
}

fn controlled_boundary(sample: usize, closed: bool) -> cutoff_ladder_output::Boundary {
    let b = boundary(sample);
    cutoff_ladder_output::Boundary {
        bus_v: b.bus_v,
        recovery: b.recovery,
        panel: cutoff::PanelBoundary {
            contour_pin16_v: 0.02
                * (2.0 * std::f64::consts::PI * 2.0 * sample as f64 / SAMPLE_RATE as f64).sin(),
            ..cutoff::PanelBoundary::default()
        },
        range_fraction_from_ground: 0.1,
        r14_ohm: if closed { Some(25_000.0) } else { None },
    }
}

fn main() {
    let closed = std::env::args().any(|arg| arg == "--emphasis");
    let global = std::env::args().any(|arg| arg == "--global");
    let controlled = global || std::env::args().any(|arg| arg == "--cutoff");
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
    let dynamic = cutoff_ladder_output::Parameters {
        ladder_transistor: transistors,
        cutoff: cutoff::Parameters {
            q26: transistors,
            q28: transistors,
        },
        r61_ohm: ladder.r61_ohm,
        r30_ohm: ladder.r30_ohm,
    };
    if std::env::args().any(|arg| arg == "--compare") {
        compare_waveforms(dynamic, conversion, headphone, closed);
        return;
    }
    #[cfg(feature = "solver-profiling")]
    if std::env::args().any(|arg| arg == "--profile") {
        let mut state = rf_d_circuit::circuit66::initial_state(
            dynamic,
            conversion,
            headphone,
            controlled_boundary(0, closed),
            SEED,
        )
        .expect("profiling DC");
        for sample in 0..1024 {
            rf_d_circuit::circuit66::step(
                &mut state,
                dynamic,
                conversion,
                headphone,
                controlled_boundary(sample, closed),
                SolverBudget::default(),
            )
            .expect("profiling warmup");
        }
        let (stamp, factor, ordered_factor, order) = rf_d_circuit::circuit66::profile_kernels(
            &state,
            dynamic,
            conversion,
            headphone,
            controlled_boundary(1023, closed),
        )
        .expect("kernel profile");
        println!(
            "kernel_profile: repeats=8192 sample=1023 stamp_us={stamp:.3} factor_us={factor:.3} ordered_factor_us={ordered_factor:.3}"
        );
        println!("elimination_order={order:?}");
        return;
    }
    let mut durations_us = Vec::with_capacity(MEASURED_SAMPLES / BLOCK);
    let mut evaluations = 0usize;
    let mut global_evaluations = 0usize;
    let mut max_global_evaluations = 0usize;
    let mut max_evaluations = 0usize;
    let mut fallbacks = 0usize;
    let mut failures = 0usize;
    let mut max_kcl = 0.0_f64;
    let mut max_cutoff_kcl = 0.0_f64;
    let mut min_tail = f64::INFINITY;
    let mut max_tail = f64::NEG_INFINITY;
    let mut final_j7 = 0.0;
    for measured in [false, true] {
        let mut state = if global {
            BenchState::Global(
                rf_d_circuit::circuit66::initial_state(
                    dynamic,
                    conversion,
                    headphone,
                    controlled_boundary(0, closed),
                    SEED,
                )
                .expect("global cutoff/ladder/output DC"),
            )
        } else if controlled {
            BenchState::Controlled(
                cutoff_ladder_output::initial_state(
                    dynamic,
                    conversion,
                    headphone,
                    controlled_boundary(0, closed),
                    SEED,
                )
                .expect("cutoff/ladder/recovery/VCA DC"),
            )
        } else {
            BenchState::Fixed(
                initial_state(ladder, conversion, headphone, boundary(0), SEED)
                    .expect("ladder/recovery/VCA DC"),
            )
        };
        for block in 0..(MEASURED_SAMPLES / BLOCK) {
            let begin = Instant::now();
            for offset in 0..BLOCK {
                let sample = block * BLOCK + offset;
                let outcome = match &mut state {
                    BenchState::Global(state) => rf_d_circuit::circuit66::step(
                        state,
                        dynamic,
                        conversion,
                        headphone,
                        controlled_boundary(sample, closed),
                        SolverBudget::default(),
                    )
                    .map(|result| {
                        if measured {
                            global_evaluations += result.residual_evaluations;
                            max_global_evaluations =
                                max_global_evaluations.max(result.residual_evaluations);
                        }
                        result.output
                    }),
                    BenchState::Controlled(state) => cutoff_ladder_output::step(
                        state,
                        dynamic,
                        conversion,
                        headphone,
                        controlled_boundary(sample, closed),
                        SolverBudget::default(),
                    ),
                    BenchState::Fixed(state) => {
                        if closed {
                            step_with_emphasis(
                                state,
                                ladder,
                                conversion,
                                headphone,
                                boundary(sample),
                                25_000.0,
                                SolverBudget::default(),
                            )
                        } else {
                            step(
                                state,
                                ladder,
                                conversion,
                                headphone,
                                boundary(sample),
                                SolverBudget::default(),
                            )
                        }
                    }
                };
                match outcome {
                    Ok(result) => {
                        if measured {
                            evaluations += result.recovery_port_evaluations;
                            max_evaluations = max_evaluations.max(result.recovery_port_evaluations);
                            fallbacks += usize::from(result.predictor_fallback);
                            max_kcl = max_kcl.max(result.max_ladder_kcl_residual_a);
                            max_cutoff_kcl = max_cutoff_kcl.max(result.max_cutoff_kcl_residual_a);
                            min_tail = min_tail.min(result.tail_current_a);
                            max_tail = max_tail.max(result.tail_current_a);
                        }
                    }
                    Err(_) => failures += 1,
                }
            }
            if measured {
                durations_us.push(begin.elapsed().as_secs_f64() * 1e6);
            }
            final_j7 = black_box(match &state {
                BenchState::Global(state) => state.node_v[61],
                BenchState::Fixed(state) => {
                    state.recovery.vca.second.downstream.output.panel.amp.node_v[11]
                }
                BenchState::Controlled(state) => {
                    state
                        .chain
                        .recovery
                        .vca
                        .second
                        .downstream
                        .output
                        .panel
                        .amp
                        .node_v[11]
                }
            });
        }
    }
    durations_us.sort_by(|a, b| a.total_cmp(b));
    let mean = durations_us.iter().sum::<f64>() / durations_us.len() as f64;
    let deadline = BLOCK as f64 * 1e6 / SAMPLE_RATE as f64;
    let missed = durations_us.iter().filter(|v| **v > deadline).count();
    println!(
        "ladder_to_j7: global_newton={global} cutoff_connected={controlled} emphasis_closed={closed} blocks={} samples={} deadline_us={deadline:.1} deadline_misses={missed} mean_us={mean:.1} p99_us={:.1} max_us={:.1} mean_recovery_evals={:.2} max_recovery_evals={} mean_global_evals={:.2} max_global_evals={max_global_evaluations} fallbacks={} max_kcl_a={max_kcl:.3e} max_cutoff_kcl_a={max_cutoff_kcl:.3e} tail_min_a={min_tail:.3e} tail_max_a={max_tail:.3e} failures={} final_j7_v={final_j7:.9}",
        durations_us.len(), MEASURED_SAMPLES,
        percentile(&durations_us,0.99), durations_us.last().unwrap(),
        evaluations as f64/MEASURED_SAMPLES as f64, max_evaluations,
        global_evaluations as f64/MEASURED_SAMPLES as f64,
        fallbacks, failures,
    );
    assert_eq!(failures, 0);
}

fn compare_waveforms(
    p: cutoff_ladder_output::Parameters,
    c: ConversionParameters,
    h: HeadphoneParameters,
    closed: bool,
) {
    let mut nested =
        cutoff_ladder_output::initial_state(p, c, h, controlled_boundary(0, closed), SEED)
            .expect("comparison nested DC");
    let mut global =
        rf_d_circuit::circuit66::initial_state(p, c, h, controlled_boundary(0, closed), SEED)
            .expect("comparison global DC");
    let mut max_j7 = 0.0_f64;
    let mut max_nodes = 0.0_f64;
    let mut max_node_index = 0;
    let mut max_node_sample = 0;
    let mut max_c10 = 0.0_f64;
    let mut max_tail = 0.0_f64;
    let mut signal = 0.0;
    let mut error_power = 0.0;
    for sample in 0..MEASURED_SAMPLES {
        let b = controlled_boundary(sample, closed);
        let old_c19 = nested
            .chain
            .recovery
            .vca
            .second
            .downstream
            .output
            .panel
            .amp
            .capacitor_v[0];
        let a = cutoff_ladder_output::step(&mut nested, p, c, h, b, SolverBudget::default())
            .expect("comparison nested step");
        let z = rf_d_circuit::circuit66::step(&mut global, p, c, h, b, SolverBudget::default())
            .expect("comparison global step")
            .output;
        let error = a.j7_v - z.j7_v;
        max_j7 = max_j7.max(error.abs());
        signal += a.j7_v * a.j7_v;
        error_power += error * error;
        max_c10 = max_c10.max((nested.chain.c10_capacitor_v - global.c10_capacitor_v).abs());
        max_tail = max_tail.max((a.tail_current_a - z.tail_current_a).abs());
        let mut x = [0.0; 66];
        x[..16].copy_from_slice(&nested.chain.node_v);
        let r = &nested.chain.recovery;
        x[16..24].copy_from_slice(&r.node_v);
        x[24..34].copy_from_slice(&r.vca.node_v);
        x[34..40].copy_from_slice(&r.vca.second.node_v);
        let out = &r.vca.second.downstream;
        x[40..47].copy_from_slice(&out.node_v);
        x[47] = out.output.c2_right_v;
        x[49] = out.output.panel.r21_wiper_v;
        x[50..62].copy_from_slice(&out.output.panel.amp.node_v);
        let r21 = b.recovery.vca.second.output.output.r21_lower_ohm;
        let dt = b.recovery.vca.second.output.output.dt_s;
        x[48] = x[49] + (5000.0 - r21) * (x[49] / r21 + 2.5e-6 / dt * (x[49] - x[50] - old_c19));
        x[62..].copy_from_slice(&nested.cutoff.node_v);
        for i in 0..66 {
            let difference = (x[i] - global.node_v[i]).abs();
            if difference > max_nodes {
                max_nodes = difference;
                max_node_index = i;
                max_node_sample = sample;
            }
        }
    }
    let snr = 10.0 * (signal / error_power).log10();
    println!("waveform_comparison: samples={MEASURED_SAMPLES} max_j7_error_v={max_j7:.9e} max_node_error_v={max_nodes:.9e} max_node_index={max_node_index} max_node_sample={max_node_sample} max_c10_error_v={max_c10:.9e} max_tail_error_a={max_tail:.9e} numerical_snr_db={snr:.3}");
    assert!(max_j7 < 1e-6 && max_nodes < 2e-6 && max_c10 < 1e-6 && max_tail < 1e-9 && snr > 90.0);
}
