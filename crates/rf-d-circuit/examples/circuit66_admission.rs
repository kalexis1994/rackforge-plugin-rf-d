//! Offline temporal/stack/control admission probes; no change to audio stepping.
#[allow(dead_code)]
#[path = "bench_ladder_recovery_output.rs"]
mod lab;

use rf_d_circuit::{circuit66, cutoff_ladder_output, SolverBudget};
use serde_json::{json, Value};

#[cfg(all(target_os = "windows", target_arch = "x86_64"))]
#[path = "support/windows_stack.rs"]
mod windows_stack;

fn main() {
    let result = if std::env::args().any(|v| v == "--stack") {
        stack_grid()
    } else if std::env::args().any(|v| v == "--controls") {
        control_grid()
    } else if std::env::args().any(|v| v == "--dc-seeds") {
        dc_seed_grid()
    } else if std::env::args().any(|v| v == "--vca-release") {
        vca_release_grid()
    } else if std::env::args().any(|v| v == "--r21") {
        r21_grid()
    } else {
        temporal_grid()
    };
    match result {
        Ok(report) => {
            println!("{}", serde_json::to_string_pretty(&report).unwrap());
            if report["passed"] != true {
                std::process::exit(1);
            }
        }
        Err(error) => {
            println!("{}", json!({"passed":false,"error":error}));
            std::process::exit(1);
        }
    }
}

fn r21_grid() -> Result<Value, String> {
    let (base, c, h) = lab::lab_parameters();
    let mut cases = Vec::new();
    for r61 in [200.0, 200000.0] {
        let p = cutoff_ladder_output::Parameters {
            r61_ohm: r61,
            ..base
        };
        let centre = lab::controlled_boundary(0, true);
        let initial = circuit66::initial_state(p, c, h, centre, lab::SEED)
            .map_err(|e| format!("centre DC: {e:?}"))?;
        for lower in [0.0, 5000.0] {
            let mut endpoint = centre;
            endpoint.recovery.vca.second.output.output.r21_lower_ohm = lower;
            let cold = circuit66::initial_state(p, c, h, endpoint, lab::SEED)
                .map_err(|e| format!("endpoint DC {lower}: {e:?}"))?;
            let mut state = initial;
            let mut rows = Vec::new();
            for index in 0..32 {
                let mut b = if index < 16 { endpoint } else { centre };
                b.bus_v = 0.02
                    * (2.0 * std::f64::consts::PI * 100.0 * (index + 1) as f64 / 48000.0).sin();
                let result = circuit66::step(&mut state, p, c, h, b, SolverBudget::default())
                    .map_err(|e| format!("R61 {r61}, endpoint {lower}, sample {index}: {e:?}"))?;
                assert!(result.output.max_ladder_kcl_residual_a < 1e-11);
                assert!(result.voltage_constraint_error_v < 1e-11);
                rows.push(json!({"index":index,"bus_v":b.bus_v,
                    "r21_lower_ohm":b.recovery.vca.second.output.output.r21_lower_ohm,
                    "node_v":state.node_v.to_vec(),"capacitor_v":state.capacitor_v.to_vec(),"c10_v":state.c10_capacitor_v,
                    "j7_v":result.output.j7_v,"j4_hi_v":result.output.j4_hi_v,"j5_lo_v":result.output.j5_lo_v,
                    "tail_current_a":result.output.tail_current_a,"kcl_a":result.output.max_ladder_kcl_residual_a,
                    "constraint_v":result.voltage_constraint_error_v,"short_current_a":result.r21_short_current_a,
                    "iterations":result.output.iterations,"fallback":result.output.predictor_fallback}));
            }
            cases.push(json!({"r61_ohm":r61,"target_lower_ohm":lower,
                "initial_node_v":initial.node_v.to_vec(),"cold_node_v":cold.node_v.to_vec(),"rows":rows}));
        }
    }
    Ok(
        json!({"schema":"rf-d/circuit66-r21-native/v1","passed":true,"cases":cases,"audio_fidelity_claim":false}),
    )
}

fn vca_release_grid() -> Result<Value, String> {
    let (base, c, h) = lab::lab_parameters();
    let mut cases = Vec::new();
    let mut failures = 0;
    let mut accepted_total = 0;
    for r61 in [200.0, 200000.0] {
        let p = cutoff_ladder_output::Parameters {
            r61_ohm: r61,
            ..base
        };
        let centre = lab::controlled_boundary(0, true);
        let initial = circuit66::initial_state(p, c, h, centre, lab::SEED)
            .map_err(|e| format!("DC: {e:?}"))?;
        for both in [false, true] {
            for ramp in [1_usize, 8, 16, 32, 64, 128, 256] {
                let mut state = initial;
                let mut accepted = 0;
                let mut failure = None;
                let mut max_kcl = 0.0_f64;
                let mut max_iterations = 0;
                let mut fallbacks = 0;
                let mut probe_rows = Vec::new();
                let mut previous_bus = 0.0;
                for n in 0..2 * ramp + 128 {
                    let fraction = if n < ramp {
                        1.0 - (n + 1) as f64 / ramp as f64
                    } else if n < ramp + 64 {
                        0.0
                    } else if n < 2 * ramp + 64 {
                        (n + 1 - ramp - 64) as f64 / ramp as f64
                    } else {
                        1.0
                    };
                    let mut b = centre;
                    b.recovery.vca.second.q21_base_v = 2.0 * fraction;
                    if both {
                        b.recovery.vca.loudness_v = 2.0 * fraction;
                    }
                    b.bus_v = 0.02
                        * (2.0 * std::f64::consts::PI * 100.0 * (n + 1) as f64 / 48000.0).sin();
                    let old = state;
                    match circuit66::step(&mut state, p, c, h, b, SolverBudget::default()) {
                        Ok(result) => {
                            accepted += 1;
                            max_kcl = max_kcl.max(result.output.max_ladder_kcl_residual_a);
                            max_iterations = max_iterations.max(result.output.iterations);
                            fallbacks += usize::from(result.output.predictor_fallback);
                            // Independent isolated windows are conditional on
                            // this same incoming native history, not the whole
                            // preceding native integration.
                            if n == ramp - 1
                                || n == ramp + 63
                                || n == ramp + 64
                                || n == 2 * ramp + 63
                            {
                                probe_rows.push(json!({"sample":n,"previous_bus_v":previous_bus,
                                    "initial":{"node_v":old.node_v.to_vec(),"previous_node_v":old.previous_node_v.to_vec(),
                                        "capacitor_v":old.capacitor_v.to_vec(),"c10_v":old.c10_capacitor_v},
                                    "boundary":{"bus_v":b.bus_v,"loudness_v":b.recovery.vca.loudness_v,
                                        "q21_base_v":b.recovery.vca.second.q21_base_v},
                                    "native":{"node_v":state.node_v.to_vec(),"capacitor_v":state.capacitor_v.to_vec(),
                                        "c10_v":state.c10_capacitor_v,"j7_v":result.output.j7_v,
                                        "j4_hi_v":result.output.j4_hi_v,"j5_lo_v":result.output.j5_lo_v}}));
                            }
                            previous_bus = b.bus_v;
                        }
                        Err(e) => {
                            assert_eq!(state, old);
                            failure = Some(json!({"sample":n,"source_fraction":fraction,
                                "error":format!("{e:?}"),"state_preserved":true}));
                            break;
                        }
                    }
                }
                assert!(max_kcl < 1e-11);
                if failure.is_some() {
                    failures += 1;
                }
                accepted_total += accepted;
                cases.push(
                    json!({"r61_ohm":r61,"both_controls":both,"ramp_samples":ramp,
                    "ramp_time_ms":1000.0*ramp as f64/48000.0,"requested_samples":2*ramp+128,
                    "accepted_samples":accepted,"failure":failure,"max_kcl_a":max_kcl,
                    "max_iterations":max_iterations,"fallbacks":fallbacks,"probes":probe_rows}),
                );
            }
        }
    }
    Ok(
        json!({"schema":"rf-d/circuit66-vca-release-survey/v1","passed":failures==0,
        "failed_cases":failures,"accepted_samples":accepted_total,"sample_rate_hz":48000,
        "scope":"imposed linear 2->0->2 V source ramps with 64 samples at zero and after restore; nominal devices",
        "generator_is_modeled":false,"audio_fidelity_claim":false,"cases":cases}),
    )
}

fn dc_seed_grid() -> Result<Value, String> {
    let fixture: Value =
        serde_json::from_str(include_str!("../../../evidence/circuit66_dc_vectors.json"))
            .map_err(|e| e.to_string())?;
    let (base, c, h) = lab::lab_parameters();
    let mut rows = Vec::new();
    let mut reference_seed_failures = 0;
    let mut perturbed_seed_failures = 0;
    let mut max_node_error = 0.0_f64;
    for case in fixture["cases"].as_array().unwrap() {
        let p = cutoff_ladder_output::Parameters {
            r61_ohm: case["r61_ohm"].as_f64().unwrap(),
            ..base
        };
        let mut b = lab::controlled_boundary(0, true);
        b.panel.cutoff_fraction_from_neg10 = case["controls"]["panel"]
            ["cutoff_fraction_from_neg10"]
            .as_f64()
            .unwrap();
        b.panel.scale_active_ohm = case["controls"]["panel"]["scale_active_ohm"]
            .as_f64()
            .unwrap();
        b.range_fraction_from_ground = case["controls"]["range_fraction"].as_f64().unwrap();
        for perturb in [0.0, 0.001, -0.001] {
            let seed =
                std::array::from_fn(|i| case["numerical_seed_v"][i].as_f64().unwrap() + perturb);
            match circuit66::initial_state_from_nodes(p, c, h, b, seed) {
                Ok(state) => {
                    let error = (0..66)
                        .map(|i| (state.node_v[i] - case["node_v"][i].as_f64().unwrap()).abs())
                        .fold(0.0_f64, f64::max);
                    let (r, _) = circuit66::linearize_dc(p, c, h, b, &state.node_v)
                        .map_err(|e| format!("{e:?}"))?;
                    let kcl = r.into_iter().map(f64::abs).fold(0.0_f64, f64::max);
                    max_node_error = max_node_error.max(error);
                    if error >= 1e-6 || kcl >= 1e-11 {
                        return Err(format!(
                            "DC {} perturb {perturb}: error={error} KCL={kcl}",
                            case["name"]
                        ));
                    }
                    rows.push(
                        json!({"name":case["name"],"r61_ohm":p.r61_ohm,"seed_shift_v":perturb,
                        "error":null,"max_node_error_v":error,"max_kcl_a":kcl}),
                    );
                }
                Err(e) => {
                    if perturb == 0.0 {
                        reference_seed_failures += 1;
                    } else {
                        perturbed_seed_failures += 1;
                    }
                    rows.push(
                        json!({"name":case["name"],"r61_ohm":p.r61_ohm,"seed_shift_v":perturb,
                        "error":format!("{e:?}")}),
                    );
                }
            }
        }
    }
    Ok(json!({"schema":"rf-d/circuit66-dc-seed-survey/v1",
        "passed":reference_seed_failures==0,"reference_seed_points":14,
        "reference_seed_failures":reference_seed_failures,"perturbed_seed_failures":perturbed_seed_failures,
        "max_node_error_v":max_node_error,"gate_scope":"14 declared reference seeds; shifted seeds exploratory, errors retained",
        "rows":rows,"audio_fidelity_claim":false}))
}

fn control_grid() -> Result<Value, String> {
    use cutoff_ladder_output::{Boundary as B, Parameters as P};
    type Change = fn(&mut P, &mut B);
    let changes: Vec<(&str, Change)> = vec![
        ("baseline", |_, _| {}),
        ("cutoff_min", |_, b| {
            b.panel.cutoff_fraction_from_neg10 = 0.0
        }),
        ("cutoff_max", |_, b| {
            b.panel.cutoff_fraction_from_neg10 = 1.0
        }),
        ("range_min", |_, b| b.range_fraction_from_ground = 0.0),
        ("range_max", |_, b| b.range_fraction_from_ground = 1.0),
        ("scale_min", |_, b| b.panel.scale_active_ohm = 0.0),
        ("scale_max", |_, b| b.panel.scale_active_ohm = 500.0),
        ("r30_min", |p, _| p.r30_ohm = 330.0),
        ("r30_max", |p, _| p.r30_ohm = 1330.0),
        ("first_balance_min", |_, b| {
            b.recovery.vca.first_balance_left_ohm = 0.0
        }),
        ("first_balance_max", |_, b| {
            b.recovery.vca.first_balance_left_ohm = 25.0
        }),
        ("second_balance_min", |_, b| {
            b.recovery.vca.second.second_balance_left_ohm = 0.0
        }),
        ("second_balance_max", |_, b| {
            b.recovery.vca.second.second_balance_left_ohm = 100.0
        }),
        ("r14_min", |_, b| b.r14_ohm = Some(0.0)),
        ("r14_max", |_, b| b.r14_ohm = Some(50000.0)),
        ("r14_disconnected", |_, b| b.r14_ohm = None),
        ("r20_min", |_, b| {
            b.recovery.vca.second.output.output.r20_lower_ohm = 0.0
        }),
        ("r20_max", |_, b| {
            b.recovery.vca.second.output.output.r20_lower_ohm = 5000.0
        }),
        ("r20_min_sw18_off", |_, b| {
            let o = &mut b.recovery.vca.second.output.output;
            o.r20_lower_ohm = 0.0;
            o.sw18_on = false;
        }),
        ("r20_max_sw18_off", |_, b| {
            let o = &mut b.recovery.vca.second.output.output;
            o.r20_lower_ohm = 5000.0;
            o.sw18_on = false;
        }),
        ("r21_near_min", |_, b| {
            b.recovery.vca.second.output.output.r21_lower_ohm = 0.001
        }),
        ("r21_near_max", |_, b| {
            b.recovery.vca.second.output.output.r21_lower_ohm = 4999.999
        }),
        ("r21_min", |_, b| {
            b.recovery.vca.second.output.output.r21_lower_ohm = 0.0
        }),
        ("r21_max", |_, b| {
            b.recovery.vca.second.output.output.r21_lower_ohm = 5000.0
        }),
        ("r21_negative_unsupported", |_, b| {
            b.recovery.vca.second.output.output.r21_lower_ohm = -1.0
        }),
        ("r21_above_total_unsupported", |_, b| {
            b.recovery.vca.second.output.output.r21_lower_ohm = 5001.0
        }),
        ("first_loudness_zero", |_, b| {
            b.recovery.vca.loudness_v = 0.0
        }),
        ("second_loudness_zero", |_, b| {
            b.recovery.vca.second.q21_base_v = 0.0
        }),
        ("both_loudness_zero", |_, b| {
            b.recovery.vca.loudness_v = 0.0;
            b.recovery.vca.second.q21_base_v = 0.0;
        }),
        ("sw18_off", |_, b| {
            b.recovery.vca.second.output.output.sw18_on = false
        }),
        ("j7_loads_open", |_, b| {
            let o = &mut b.recovery.vca.second.output.output;
            o.tip_load_ohm = None;
            o.ring_load_ohm = None;
        }),
        ("external_negative", |_, b| {
            b.panel.external_control_v = Some(-0.2);
            b.panel.external_source_ohm = 10000.0;
        }),
        ("external_positive", |_, b| {
            b.panel.external_control_v = Some(0.2);
            b.panel.external_source_ohm = 10000.0;
        }),
        ("mod_negative", |_, b| {
            b.panel.filter_mod_on = true;
            b.panel.modulation_source_v = Some(-0.2);
            b.panel.modulation_source_ohm = 2000.0;
        }),
        ("mod_positive", |_, b| {
            b.panel.filter_mod_on = true;
            b.panel.modulation_source_v = Some(0.2);
            b.panel.modulation_source_ohm = 2000.0;
        }),
        ("keyboard_both_one_volt", |_, b| {
            b.panel.keyboard_1_3_on = true;
            b.panel.keyboard_2_3_on = true;
            b.panel.keyboard_cv_v = Some(1.0);
            b.panel.keyboard_source_ohm = 1200.0;
        }),
        ("contour_negative_probe", |_, b| {
            b.panel.contour_pin16_v = -0.2
        }),
        ("contour_positive_probe", |_, b| {
            b.panel.contour_pin16_v = 0.2
        }),
    ];
    let (base, c, h) = lab::lab_parameters();
    let mut cases = Vec::new();
    let mut failures = 0;
    let mut warm_failures = 0;
    let mut total = 0;
    for r61 in [200.0, 200000.0] {
        let base = P {
            r61_ohm: r61,
            ..base
        };
        let centre = lab::controlled_boundary(0, true);
        let initial = circuit66::initial_state(base, c, h, centre, lab::SEED)
            .map_err(|e| format!("Centre DC: {e:?}"))?;
        for (name, change) in &changes {
            let mut p = base;
            let mut target = centre;
            change(&mut p, &mut target);
            let unsupported = name.ends_with("unsupported");
            let dc = circuit66::initial_state(p, c, h, target, lab::SEED);
            let dc_error = dc.as_ref().err().map(|e| format!("{e:?}"));
            let warm_dc = circuit66::initial_state_from_nodes(p, c, h, target, initial.node_v);
            let warm_dc_error = warm_dc.as_ref().err().map(|e| format!("{e:?}"));
            if !unsupported && warm_dc_error.is_some() {
                warm_failures += 1;
            }
            let mut state = initial;
            if unsupported {
                let old = state;
                let error = circuit66::step(&mut state, p, c, h, target, SolverBudget::default())
                    .unwrap_err();
                assert_eq!(error, rf_d_circuit::StepError::InvalidInput);
                assert_eq!(state, old);
                assert_eq!(dc_error.as_deref(), Some("InvalidInput"));
                assert_eq!(warm_dc_error.as_deref(), Some("InvalidInput"));
                cases.push(json!({"name":name,"r61_ohm":r61,"expected_domain_rejection":true,"state_preserved":true}));
                continue;
            }
            let mut accepted = 0;
            let mut failure = None;
            let mut max_kcl = 0.0_f64;
            let mut max_j7 = 0.0_f64;
            let mut max_iterations = 0;
            let mut fallbacks = 0;
            for n in 0..256 {
                let restoring = n >= 128;
                let mut b = if restoring { centre } else { target };
                let parameters = if restoring { base } else { p };
                b.bus_v =
                    0.02 * (2.0 * std::f64::consts::PI * 100.0 * (n + 1) as f64 / 48000.0).sin();
                let old = state;
                match circuit66::step(&mut state, parameters, c, h, b, SolverBudget::default()) {
                    Ok(result) => {
                        accepted += 1;
                        max_kcl = max_kcl.max(result.output.max_ladder_kcl_residual_a);
                        max_j7 = max_j7.max(result.output.j7_v.abs());
                        max_iterations = max_iterations.max(result.output.iterations);
                        fallbacks += usize::from(result.output.predictor_fallback);
                        assert!(state
                            .node_v
                            .iter()
                            .chain(state.capacitor_v.iter())
                            .all(|v| v.is_finite()));
                    }
                    Err(e) => {
                        assert_eq!(state, old);
                        failure = Some(
                            json!({"sample":n,"restoring":restoring,"error":format!("{e:?}"),"state_preserved":true}),
                        );
                        break;
                    }
                }
            }
            assert!(max_kcl < 1e-11);
            total += accepted;
            if dc_error.is_some() || failure.is_some() {
                failures += 1;
            }
            cases.push(json!({"name":name,"r61_ohm":r61,"expected_domain_rejection":false,
                "dc_error":dc_error,"warm_dc_error":warm_dc_error,
                "warm_dc_node_v":warm_dc.ok().map(|s|s.node_v.to_vec()),
                "transient_error":failure,"accepted_samples":accepted,
                "max_kcl_a":max_kcl,"j7_peak_abs_v":max_j7,"max_iterations":max_iterations,"fallbacks":fallbacks,
                "final_node_v":state.node_v.to_vec()}));
        }
    }
    Ok(
        json!({"schema":"rf-d/circuit66-control-survey/v1","passed":failures==0,"survey_completed":true,
        "sample_rate_hz":48000,"requested_samples_per_supported_case":256,"accepted_samples":total,
        "supported_case_failures":failures,"warm_dc_failures":warm_failures,"expected_endpoint_rejections":0,
        "expected_outside_domain_rejections":4,
        "scope":"one control/trim/source at a time; abrupt centre-target-centre, nominal imposed devices",
        "audio_fidelity_claim":false,"cases":cases}),
    )
}

#[cfg(not(all(target_os = "windows", target_arch = "x86_64")))]
fn stack_grid() -> Result<Value, String> {
    Err("Stack region probe requires Windows x86_64".into())
}

#[cfg(all(target_os = "windows", target_arch = "x86_64"))]
fn stack_grid() -> Result<Value, String> {
    use windows_stack::{snapshot, Snapshot};
    struct Run {
        before: Snapshot,
        after_dc: Snapshot,
        after_steps: Snapshot,
        final_node: [f64; 66],
        max_kcl: f64,
        fallbacks: usize,
    }
    // A separate no-inline worker observes its own allocation. Serialization
    // happens after joining, outside the measured worker.
    #[inline(never)]
    fn worker(
        initial: Option<circuit66::State>,
        p: cutoff_ladder_output::Parameters,
        r21_endpoints: bool,
    ) -> Result<Run, String> {
        let (_, c, h) = lab::lab_parameters();
        let before = snapshot()?;
        let mut dc_boundary = lab::controlled_boundary(0, true);
        if r21_endpoints {
            dc_boundary.recovery.vca.second.output.output.r21_lower_ohm = 0.0;
        }
        let mut state = match initial {
            Some(s) => s,
            None => circuit66::initial_state(p, c, h, dc_boundary, lab::SEED)
                .map_err(|e| format!("Worker DC: {e:?}"))?,
        };
        let after_dc = snapshot()?;
        let mut max_kcl = 0.0_f64;
        let mut fallbacks = 0;
        for sample in 0..8192 {
            if sample == 4096 {
                state.previous_node_v[1] -= 1e6;
            }
            let old = state;
            let mut b = lab::controlled_boundary(sample, true);
            if r21_endpoints {
                b.recovery.vca.second.output.output.r21_lower_ohm = match sample % 3072 / 1024 {
                    1 => 0.0,
                    2 => 5000.0,
                    _ => 2000.0,
                };
            }
            let result =
                circuit66::step(&mut state, p, c, h, b, SolverBudget::default()).map_err(|e| {
                    assert_eq!(state, old);
                    format!("Worker sample {sample}: {e:?}")
                })?;
            max_kcl = max_kcl.max(result.output.max_ladder_kcl_residual_a);
            fallbacks += usize::from(result.output.predictor_fallback);
        }
        // Include invalid-input and exhausted-budget paths in the observation.
        let old = state;
        let mut b = lab::controlled_boundary(8192, true);
        b.range_fraction_from_ground = f64::NAN;
        if circuit66::step(&mut state, p, c, h, b, SolverBudget::default()).is_ok() {
            return Err("Invalid input accepted".into());
        }
        assert_eq!(state, old);
        b = lab::controlled_boundary(8192, true);
        b.bus_v = 0.2;
        if circuit66::step(
            &mut state,
            p,
            c,
            h,
            b,
            SolverBudget {
                iterations: 1,
                line_search_halvings: 16,
            },
        )
        .is_ok()
        {
            return Err("One-iteration failure probe unexpectedly converged".into());
        }
        assert_eq!(state, old);
        let after_steps = snapshot()?;
        if max_kcl >= 1e-11 || fallbacks != 1 {
            return Err("Worker KCL or forced predictor fallback gate failed".into());
        }
        Ok(Run {
            before,
            after_dc,
            after_steps,
            final_node: state.node_v,
            max_kcl,
            fallbacks,
        })
    }
    let requested = std::env::args()
        .find_map(|s| s.strip_prefix("--stack-kib=").map(str::to_owned))
        .unwrap_or_else(|| "2048".into())
        .parse::<usize>()
        .map_err(|e| e.to_string())?;
    if !(512..=8192).contains(&requested) {
        return Err("Use a requested worker stack of 512..8192 KiB".into());
    }
    let (base, c, h) = lab::lab_parameters();
    let r21_endpoints = std::env::args().any(|v| v == "--stack-r21");
    let mut rows = Vec::new();
    for r61 in [200.0, 200000.0] {
        let p = cutoff_ladder_output::Parameters {
            r61_ohm: r61,
            ..base
        };
        let mut dc_boundary = lab::controlled_boundary(0, true);
        if r21_endpoints {
            dc_boundary.recovery.vca.second.output.output.r21_lower_ohm = 0.0;
        }
        let outside = circuit66::initial_state(p, c, h, dc_boundary, lab::SEED)
            .map_err(|e| format!("Outside-worker DC: {e:?}"))?;
        let mut reference = None;
        for dc_in_worker in [true, false] {
            let initial = if dc_in_worker { None } else { Some(outside) };
            let run = std::thread::Builder::new()
                .name("rf-d-stack-probe".into())
                .stack_size(requested * 1024)
                .spawn(move || worker(initial, p, r21_endpoints))
                .map_err(|e| e.to_string())?
                .join()
                .map_err(|_| "Worker panicked".to_string())??;
            let difference = if let Some(previous) = reference {
                run.final_node
                    .iter()
                    .zip(previous)
                    .map(|(a, b): (&f64, f64)| (a - b).abs())
                    .fold(0.0_f64, f64::max)
            } else {
                reference = Some(run.final_node);
                0.0
            };
            if difference > 1e-12 {
                return Err("Worker initialization paths differ numerically".into());
            }
            rows.push(json!({"r61_ohm":r61,"dc_in_worker":dc_in_worker,"requested_stack_bytes":requested*1024,
                "before":windows_stack::json(run.before),"after_dc":windows_stack::json(run.after_dc),
                "after_steps_and_failure_paths":windows_stack::json(run.after_steps),
                "samples":8192,"forced_predictor_fallbacks":run.fallbacks,"atomic_rejections":2,
                "max_kcl_a":run.max_kcl,"final_node_v":run.final_node.to_vec(),
                "initialization_path_max_difference_v":difference}));
        }
    }
    Ok(
        json!({"schema":"rf-d/circuit66-stack-regions/v1","passed":true,"platform":"windows-x86_64",
        "r21_endpoints_exercised":r21_endpoints,
        "method":"separate Rust workers; read-only GetCurrentThreadStackLimits/VirtualQuery at phase boundaries",
        "precise_stack_high_water_measured":false,"audio_deadline_claim":false,"runs":rows}),
    )
}

fn smooth_boundary(t: f64, rate: usize, multitone: bool) -> cutoff_ladder_output::Boundary {
    let mut b = lab::controlled_boundary(0, true);
    let sine = |hz: f64| (2.0 * std::f64::consts::PI * hz * t).sin();
    b.bus_v = if multitone {
        0.08 * sine(100.0) + 0.015 * sine(1600.0) + 0.005 * sine(4163.0)
    } else {
        0.1 * sine(100.0)
    };
    b.panel.contour_pin16_v = 0.02 * sine(2.0);
    b.recovery.vca.second.output.output.dt_s = 1.0 / rate as f64;
    b
}

fn trace(
    initial: circuit66::State,
    p: cutoff_ladder_output::Parameters,
    rate: usize,
    multitone: bool,
) -> Result<(Vec<[f64; 87]>, Value), String> {
    let (_, c, h) = lab::lab_parameters();
    let mut state = initial;
    let count = rate / 50; // Same physical 20 ms at every rate.
    let mut samples = Vec::with_capacity(count);
    let mut max_kcl = 0.0_f64;
    let mut iterations = 0;
    let mut fallbacks = 0;
    for n in 1..=count {
        let b = smooth_boundary(n as f64 / rate as f64, rate, multitone);
        let previous = state;
        let result =
            circuit66::step(&mut state, p, c, h, b, SolverBudget::default()).map_err(|e| {
                assert_eq!(state, previous);
                format!("rate {rate}, R61 {}, sample {n}: {e:?}", p.r61_ohm)
            })?;
        max_kcl = max_kcl.max(result.output.max_ladder_kcl_residual_a);
        iterations = iterations.max(result.output.iterations);
        fallbacks += usize::from(result.output.predictor_fallback);
        let mut x = [0.0; 87];
        x[..66].copy_from_slice(&state.node_v);
        x[66..83].copy_from_slice(&state.capacitor_v);
        x[83] = state.c10_capacitor_v;
        x[84] = result.output.tail_current_a;
        x[85] = result.output.j4_hi_v;
        x[86] = result.output.j5_lo_v;
        samples.push(x);
    }
    if max_kcl >= 1e-11 {
        return Err("KCL gate failed".into());
    }
    Ok((
        samples,
        json!({"sample_rate_hz":rate,"samples":count,"max_kcl_a":max_kcl,
        "max_iterations":iterations,"fallbacks":fallbacks}),
    ))
}

fn compare(a: &[[f64; 87]], b: &[[f64; 87]]) -> Value {
    assert_eq!(b.len(), 2 * a.len());
    let mut max = [0.0_f64; 87];
    let mut power = [0.0; 87];
    for (n, x) in a.iter().enumerate() {
        let y = &b[2 * (n + 1) - 1]; // Endpoints t=(n+1)/rate, no interpolator.
        for k in 0..87 {
            let e = x[k] - y[k];
            max[k] = max[k].max(e.abs());
            power[k] += e * e;
        }
    }
    let rms = power.map(|v| (v / a.len() as f64).sqrt());
    let selected: Vec<Value> = [
        (61, "j7_v"),
        (47, "c2_right_v"),
        (49, "r21_wiper_v"),
        (62, "c18_v"),
        (83, "c10_v"),
        (84, "tail_current_a"),
    ]
    .into_iter()
    .map(|(k, name)| json!({"name":name,"max_abs_difference":max[k],"rms_difference":rms[k]}))
    .collect();
    json!({"selected":selected,"all_max_differences":max.to_vec(),"all_rms_differences":rms.to_vec(),
        "max_node_difference_v":max[..66].iter().copied().fold(0.0_f64,f64::max),
        "max_capacitor_difference_v":max[66..84].iter().copied().fold(0.0_f64,f64::max)})
}

fn temporal_grid() -> Result<Value, String> {
    let (base, c, h) = lab::lab_parameters();
    let mut cases = Vec::new();
    let mut passed = true;
    for multitone in [false, true] {
        for r61 in [200.0, 200000.0] {
            let p = cutoff_ladder_output::Parameters {
                r61_ohm: r61,
                ..base
            };
            // One DC state shared bit-for-bit across all three integrations.
            let initial = circuit66::initial_state(
                p,
                c,
                h,
                smooth_boundary(0.0, 48000, multitone),
                lab::SEED,
            )
            .map_err(|e| format!("DC R61 {r61}: {e:?}"))?;
            let (coarse, cr) = trace(initial, p, 48000, multitone)?;
            let (medium, mr) = trace(initial, p, 96000, multitone)?;
            let (fine, fr) = trace(initial, p, 192000, multitone)?;
            let low = compare(&coarse, &medium);
            let high = compare(&medium, &fine);
            let mut gates = Vec::new();
            // Fixed before measuring: decrease in max and RMS for the three
            // audio/output nodes. Ratios describe Euler's error, not fidelity.
            for k in 0..3 {
                let a = &low["selected"][k];
                let b = &high["selected"][k];
                let max_ratio = a["max_abs_difference"].as_f64().unwrap()
                    / b["max_abs_difference"].as_f64().unwrap();
                let rms_ratio =
                    a["rms_difference"].as_f64().unwrap() / b["rms_difference"].as_f64().unwrap();
                let ok = max_ratio > 1.0 && rms_ratio > 1.0;
                passed &= ok;
                gates.push(json!({"node":a["name"],"passed":ok,"max_error_ratio":max_ratio,"rms_error_ratio":rms_ratio}));
            }
            cases.push(
                json!({"r61_ohm":r61,"multitone":multitone,"runs":[cr,mr,fr],
                "coarse_to_medium":low,"medium_to_fine":high,"gates":gates}),
            );
        }
    }
    let report = json!({"schema":"rf-d/circuit66-temporal-convergence/v1","duration_s":0.02,
        "rates_hz":[48000,96000,192000],"total_steps":26880,"passed":passed,
        "method":"implicit Euler, same DC and smooth electrical functions; aligned endpoints",
        "audio_fidelity_claim":false,"cases":cases});
    if !passed {
        eprintln!("Temporal decrease gate failed; full report follows.");
    }
    Ok(report)
}
