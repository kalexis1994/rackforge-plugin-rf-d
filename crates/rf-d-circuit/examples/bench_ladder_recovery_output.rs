//! Conditional ladder to J7 deadline, waveform and long stress probes.
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
    let probes = std::env::args().any(|arg| arg == "--stress-probes");
    if probes || std::env::args().any(|arg| arg == "--stress") {
        stress_global(dynamic, conversion, headphone, probes);
        return;
    }
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

// Synthetic electrical boundaries, expressed in V/ohm/s. This exercises the
// solver and capacitor history; it does not synthesize or identify a Model D.
fn stress_boundary(sample: usize, rate: f64) -> cutoff_ladder_output::Boundary {
    let t = sample as f64 / rate;
    let sine = |hz: f64| (2.0 * std::f64::consts::PI * hz * t).sin();
    let segment = (t / 0.25).floor() as usize;
    let mut b = controlled_boundary(0, true);
    b.bus_v = 0.08 * sine(100.0) + 0.015 * sine(1600.0) + 0.005 * sine(4163.0);
    b.panel.cutoff_fraction_from_neg10 = 0.5 + 0.04 * sine(0.7);
    b.panel.contour_pin16_v = 0.04 * sine(2.0);
    b.panel.keyboard_1_3_on = segment % 2 == 1;
    b.panel.keyboard_2_3_on = segment % 3 == 2;
    b.panel.keyboard_cv_v = Some(0.25 * (1.0 + sine(0.9)));
    b.panel.keyboard_source_ohm = 1200.0;
    b.panel.filter_mod_on = segment % 2 == 1;
    b.panel.modulation_source_v = Some(0.15 * sine(7.0));
    b.panel.modulation_source_ohm = 2000.0;
    b.panel.external_control_v = if segment % 3 == 2 {
        Some(0.1 * sine(0.5))
    } else {
        None
    };
    b.panel.external_source_ohm = 10000.0;
    b.range_fraction_from_ground = 0.1 + 0.02 * sine(0.3);
    b.r14_ohm = match segment % 4 {
        0 => Some(0.0),
        1 => Some(25000.0),
        2 => Some(50000.0),
        _ => None,
    };
    b.recovery.vca.loudness_v = 1.0 + sine(0.8);
    b.recovery.vca.second.q21_base_v = 1.0 + sine(0.6);
    let o = &mut b.recovery.vca.second.output.output;
    o.dt_s = 1.0 / rate;
    o.r21_lower_ohm = 2000.0 + 1500.0 * sine(0.4);
    o.sw18_on = segment % 3 != 1;
    o.tip_load_ohm = if segment % 2 == 0 { Some(32.0) } else { None };
    o.ring_load_ohm = if segment % 3 == 0 { Some(32.0) } else { None };
    b
}

fn stress_global(
    p: cutoff_ladder_output::Parameters,
    c: ConversionParameters,
    h: HeadphoneParameters,
    capture_probes: bool,
) {
    use rf_d_circuit::circuit66;
    use serde_json::json;
    let mut records = Vec::new();
    let mut probes = Vec::new();
    let mut passed = true;
    for rate in [44100.0, 48000.0, 96000.0] {
        for r61 in [200.0, 200000.0] {
            let starts: Vec<usize> = if capture_probes {
                (1..=7)
                    .map(|q| (q as f64 * 0.25 * rate).ceil() as usize - 2)
                    .chain(std::iter::once((1.9 * rate).ceil() as usize - 2))
                    .collect()
            } else {
                Vec::new()
            };
            let mut windows = Vec::new();
            let p = cutoff_ladder_output::Parameters { r61_ohm: r61, ..p };
            let b = stress_boundary(0, rate);
            let count = ((2.0 * rate) as usize / BLOCK) * BLOCK;
            let mut record =
                json!({"sample_rate_hz":rate, "r61_ohm":r61, "requested_samples":count});
            let initial = circuit66::initial_state(p, c, h, b, SEED);
            let mut state = match initial {
                Ok(s) => s,
                Err(e) => {
                    record["failure"] = json!({"phase":"dc", "error":format!("{e:?}")});
                    records.push(record);
                    passed = false;
                    continue;
                }
            };
            let mut iterations = [0usize; 17];
            let mut max_kcl = 0.0_f64;
            let mut max_audited_kcl = 0.0_f64;
            let mut audits = 0usize;
            let mut max_j7 = 0.0_f64;
            let mut min_tail = f64::INFINITY;
            let mut max_tail = f64::NEG_INFINITY;
            let mut max_evals = 0usize;
            let mut fallback_count = 0usize;
            let mut accepted = 0usize;
            let mut c10_hold_checks = 0usize;
            let mut failure = None;
            for sample in 0..count {
                let b = stress_boundary(sample, rate);
                let previous = state;
                if starts.contains(&sample) {
                    windows.push(json!({
                        "sample_rate_hz":rate, "r61_ohm":r61, "first_sample":sample,
                        "previous_bus_v":stress_boundary(sample - 1,rate).bus_v,
                        "initial":probe_state(&previous), "rows":[],
                    }));
                }
                match circuit66::step(&mut state, p, c, h, b, SolverBudget::default()) {
                    Ok(result) => {
                        if let Some(window) = windows.last_mut() {
                            if sample < window["first_sample"].as_u64().unwrap() as usize + 4 {
                                window["rows"].as_array_mut().unwrap().push(json!({
                                    "sample":sample, "boundary":probe_boundary(b),
                                    "native":probe_state(&state),
                                }));
                            }
                        }
                        accepted += 1;
                        iterations[result.output.iterations] += 1;
                        max_evals = max_evals.max(result.residual_evaluations);
                        fallback_count += usize::from(result.output.predictor_fallback);
                        max_kcl = max_kcl.max(result.output.max_ladder_kcl_residual_a);
                        max_j7 = max_j7.max(result.output.j7_v.abs());
                        min_tail = min_tail.min(result.output.tail_current_a);
                        max_tail = max_tail.max(result.output.tail_current_a);
                        if b.r14_ohm.is_none() {
                            assert_eq!(
                                state.c10_capacitor_v.to_bits(),
                                previous.c10_capacitor_v.to_bits()
                            );
                            c10_hold_checks += 1;
                        }
                        // Audit KCL independently of the value reported by the
                        // solver, always with the PREVIOUS capacitor history.
                        if sample % BLOCK == 0 {
                            let (r, _) = circuit66::linearize(&previous, p, c, h, b, &state.node_v)
                                .expect("accepted state audit");
                            max_audited_kcl =
                                max_audited_kcl.max(r.iter().fold(0.0_f64, |a, v| a.max(v.abs())));
                            audits += 1;
                        }
                    }
                    Err(e) => {
                        assert_eq!(state, previous, "failed step consumed history");
                        failure = Some(
                            json!({"phase":"transient", "sample":sample, "time_s":sample as f64/rate, "error":format!("{e:?}"), "state_preserved":true}),
                        );
                        passed = false;
                        break;
                    }
                }
            }
            assert!(max_kcl < 1e-11 && max_audited_kcl < 1e-11);
            record["accepted_samples"] = json!(accepted);
            record["failure"] = json!(failure);
            record["iterations_histogram"] = json!(iterations);
            record["fallback_count"] = json!(fallback_count);
            record["max_residual_evaluations"] = json!(max_evals);
            record["max_kcl_a"] = json!(max_kcl);
            record["audited_kcl_max_a"] = json!(max_audited_kcl);
            record["kcl_audits"] = json!(audits);
            record["c10_open_history_checks"] = json!(c10_hold_checks);
            record["j7_peak_abs_v"] = json!(max_j7);
            record["tail_current_min_a"] = json!(min_tail);
            record["tail_current_max_a"] = json!(max_tail);
            record["final_node_v"] = json!(state.node_v.to_vec());
            records.push(record);
            probes.extend(windows);
        }
    }
    println!("{}", serde_json::to_string_pretty(&json!({
        "schema":"rf-d/circuit66-long-stress/v1", "duration_requested_s":2.0,
        "passed":passed, "audio_fidelity_claim":false,
        "scene":"multitone BUS, slow controls, quarter-second switch/load changes; see stress_boundary",
        "runs":records,
        "probe_windows":probes,
    })).unwrap());
    if !passed {
        std::process::exit(1);
    }
}

fn probe_state(s: &rf_d_circuit::circuit66::State) -> serde_json::Value {
    serde_json::json!({"node_v":s.node_v.to_vec(), "previous_node_v":s.previous_node_v.to_vec(),
        "capacitor_v":s.capacitor_v, "c10_v":s.c10_capacitor_v})
}

fn probe_boundary(b: cutoff_ladder_output::Boundary) -> serde_json::Value {
    let p = b.panel;
    let o = b.recovery.vca.second.output.output;
    serde_json::json!({
        "bus_v":b.bus_v, "range_fraction":b.range_fraction_from_ground, "r14_ohm":b.r14_ohm,
        "loudness_v":b.recovery.vca.loudness_v, "q21_base_v":b.recovery.vca.second.q21_base_v,
        "r21_lower_ohm":o.r21_lower_ohm, "tip_load_ohm":o.tip_load_ohm,
        "ring_load_ohm":o.ring_load_ohm, "sw18_on":o.sw18_on,
        "panel":{
            "cutoff_fraction_from_neg10":p.cutoff_fraction_from_neg10,
            "scale_active_ohm":p.scale_active_ohm, "contour_pin16_v":p.contour_pin16_v,
            "external_control_v":p.external_control_v, "external_source_ohm":p.external_source_ohm,
            "filter_mod_on":p.filter_mod_on, "modulation_source_v":p.modulation_source_v,
            "modulation_source_ohm":p.modulation_source_ohm,
            "keyboard_1_3_on":p.keyboard_1_3_on, "keyboard_2_3_on":p.keyboard_2_3_on,
            "keyboard_cv_v":p.keyboard_cv_v, "keyboard_source_ohm":p.keyboard_source_ohm,
        },
    })
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
