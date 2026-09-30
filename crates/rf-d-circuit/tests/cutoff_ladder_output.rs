use rf_d_circuit::cutoff::{self, PanelBoundary};
use rf_d_circuit::cutoff_ladder_output::{self as circuit, Boundary, Parameters, State};
use rf_d_circuit::output::OutputBoundary;
use rf_d_circuit::output_conversion::{DiodeParameters, Parameters as ConversionParameters};
use rf_d_circuit::output_conversion_c4::BoundaryC4;
use rf_d_circuit::recovery_vca_output::Boundary as RecoveryBoundary;
use rf_d_circuit::vca1_output::Boundary as FirstBoundary;
use rf_d_circuit::vca2_output::{Boundary as SecondBoundary, Parameters as Bjt};
use rf_d_circuit::{Parameters as HeadphoneParameters, SolverBudget, StepError};
use serde_json::Value;

fn n(v: &Value) -> f64 {
    v.as_f64().unwrap()
}

#[test]
fn independently_refined_vca_release_roots_close_native_kcl_with_same_histories() {
    use rf_d_circuit::circuit66 as global;
    let fixture: Value = serde_json::from_str(include_str!(
        "../../../evidence/circuit66_vca_release_probe_vectors.json"
    ))
    .unwrap();
    let (bjt, conversion, headphone, rb) = setup();
    let controls: Value =
        serde_json::from_str(include_str!("../../../evidence/cutoff_j7_vectors.json")).unwrap();
    let mut count = 0;
    let mut max_kcl = 0.0_f64;
    #[cfg(not(feature = "solver-kcl-only-transient"))]
    let mut max_node_error = 0.0_f64;
    for probe in fixture["probes"].as_array().unwrap() {
        let p = Parameters {
            ladder_transistor: bjt,
            cutoff: cutoff::Parameters { q26: bjt, q28: bjt },
            r61_ohm: n(&probe["r61_ohm"]),
            r30_ohm: 830.0,
        };
        let mut b = Boundary {
            bus_v: n(&probe["boundary"]["bus_v"]),
            recovery: rb,
            panel: panel(&controls["cases"][0]["controls"]["panel"]),
            range_fraction_from_ground: 0.1,
            r14_ohm: Some(25000.0),
        };
        b.recovery.vca.loudness_v = n(&probe["boundary"]["loudness_v"]);
        b.recovery.vca.second.q21_base_v = n(&probe["boundary"]["q21_base_v"]);
        let old = &probe["initial"];
        let previous = global::State {
            node_v: std::array::from_fn(|i| n(&old["node_v"][i])),
            previous_node_v: std::array::from_fn(|i| n(&old["previous_node_v"][i])),
            capacitor_v: std::array::from_fn(|i| n(&old["capacitor_v"][i])),
            c10_capacitor_v: n(&old["c10_v"]),
        };
        let candidate = std::array::from_fn(|i| n(&probe["node_v"][i]));
        let (r, _) = global::linearize(&previous, p, conversion, headphone, b, &candidate).unwrap();
        for v in r {
            max_kcl = max_kcl.max(v.abs());
            assert!(v.abs() < 1e-11);
        }
        #[cfg(not(feature = "solver-kcl-only-transient"))]
        {
            let mut state = previous;
            let result = global::step(
                &mut state,
                p,
                conversion,
                headphone,
                b,
                SolverBudget::default(),
            )
            .unwrap_or_else(|e| {
                panic!(
                    "refined ramp {} sample {}: {e:?}",
                    probe["ramp_samples"], probe["sample"]
                )
            });
            for i in 0..66 {
                let error = (state.node_v[i] - candidate[i]).abs();
                max_node_error = max_node_error.max(error);
                assert!(
                    error < 1e-6,
                    "release root node {i} ramp {} sample {}: {error}",
                    probe["ramp_samples"],
                    probe["sample"]
                );
            }
            for i in 0..17 {
                assert!((state.capacitor_v[i] - n(&probe["capacitor_v"][i])).abs() < 1e-6);
            }
            assert!((state.c10_capacitor_v - n(&probe["c10_v"])).abs() < 1e-6);
            assert!((result.output.j7_v - candidate[61]).abs() < 1e-6);
        }
        count += 1;
    }
    assert_eq!(count, 96);
    println!("refined release roots: points={count} max_native_kcl_a={max_kcl:.9e}");
    #[cfg(not(feature = "solver-kcl-only-transient"))]
    println!("strict release root max_node_error_v={max_node_error:.9e}");
}

#[test]
fn full_dc_seeds_match_independent_dc_and_rebuild_capacitor_histories() {
    use rf_d_circuit::circuit66 as global;
    let fixture: Value =
        serde_json::from_str(include_str!("../../../evidence/circuit66_dc_vectors.json")).unwrap();
    let (bjt, conversion, headphone, rb) = setup();
    let mut max_node = 0.0_f64;
    let mut count = 0;
    for case in fixture["cases"].as_array().unwrap() {
        let p = Parameters {
            ladder_transistor: bjt,
            cutoff: cutoff::Parameters { q26: bjt, q28: bjt },
            r61_ohm: n(&case["r61_ohm"]),
            r30_ohm: 830.0,
        };
        let b = Boundary {
            bus_v: 0.125,
            recovery: rb,
            panel: panel(&case["controls"]["panel"]),
            range_fraction_from_ground: n(&case["controls"]["range_fraction"]),
            r14_ohm: None,
        };
        for perturb in [0.0] {
            let seed = std::array::from_fn(|i| n(&case["numerical_seed_v"][i]) + perturb);
            let state = global::initial_state_from_nodes(p, conversion, headphone, b, seed)
                .unwrap_or_else(|e| {
                    panic!(
                        "{} R61 {} perturb {perturb}: {e:?}",
                        case["name"], p.r61_ohm
                    )
                });
            for i in 0..66 {
                let error = (state.node_v[i] - n(&case["node_v"][i])).abs();
                max_node = max_node.max(error);
                assert!(
                    error < 1e-6,
                    "{} R61 {} perturb {perturb} node {i}: {error}",
                    case["name"],
                    p.r61_ohm
                );
            }
            let x = state.node_v;
            let expected = [
                x[8] - x[12],
                x[9] - x[13],
                x[10] - x[14],
                x[11] - x[15],
                x[4],
                x[6] - b.bus_v,
                x[16] - x[11],
                x[17] - x[15],
                x[23],
                x[24] - x[25],
                x[26],
                x[40] - 10.0,
                x[46] - x[47],
                x[49] - x[50],
                x[57] - x[58],
                x[60] - x[61],
                x[62],
            ];
            assert_eq!(state.capacitor_v, expected);
            assert_eq!(state.c10_capacitor_v, x[22] - x[7]);
            assert_eq!(state.previous_node_v, state.node_v);
            let (r, j) = global::linearize_dc(p, conversion, headphone, b, &x).unwrap();
            assert!(r.iter().all(|v| v.abs() < 1e-11));
            assert!(((x[5] - x[65]) / 680.0 - n(&case["tail_current_a"])).abs() < 1e-9);
            // All 66 DC columns at cutoff maximum, separately from transient J.
            if case["name"] == "cutoff_max" && perturb == 0.0 {
                for column in 0..66 {
                    let mut high = x;
                    let mut low = x;
                    high[column] += 1e-7;
                    low[column] -= 1e-7;
                    let (rh, _) = global::linearize_dc(p, conversion, headphone, b, &high).unwrap();
                    let (rl, _) = global::linearize_dc(p, conversion, headphone, b, &low).unwrap();
                    for row in 0..66 {
                        let fd = (rh[row] - rl[row]) / 2e-7;
                        assert!(
                            (fd - j[row][column]).abs() < 1e-8 + 3e-6 * fd.abs(),
                            "DC J {row}/{column}"
                        );
                    }
                }
            }
            let mut invalid = seed;
            invalid[0] = f64::NAN;
            assert_eq!(
                global::initial_state_from_nodes(p, conversion, headphone, b, invalid).unwrap_err(),
                StepError::InvalidInput
            );
            assert!(global::linearize_dc(p, conversion, headphone, b, &invalid).is_err());
            count += 1;
        }
    }
    assert_eq!(count, 14);
    println!("full DC FD: points={count} max_node_error_v={max_node:.9e}");
}

#[test]
fn r20_exact_shorts_and_sw18_match_independent_full_circuit() {
    use rf_d_circuit::circuit66 as global;
    let fixture: Value =
        serde_json::from_str(include_str!("../../../evidence/r20_endpoint_vectors.json")).unwrap();
    let (bjt, conversion, headphone, rb) = setup();
    let mut count = 0;
    let mut max_node = 0.0_f64;
    let mut max_jack = 0.0_f64;
    for case in fixture["cases"].as_array().unwrap() {
        let p = Parameters {
            ladder_transistor: bjt,
            cutoff: cutoff::Parameters { q26: bjt, q28: bjt },
            r61_ohm: n(&case["r61_ohm"]),
            r30_ohm: 830.0,
        };
        let mut b = Boundary {
            bus_v: 0.0,
            recovery: rb,
            panel: panel(&case["controls"]["panel"]),
            range_fraction_from_ground: 0.1,
            r14_ohm: Some(25000.0),
        };
        let seed = std::array::from_fn(|i| n(&case["initial"]["node_v"][i]));
        let mut state = global::initial_state(p, conversion, headphone, b, seed).unwrap();
        let mut dc_boundary = b;
        let ob = &mut dc_boundary.recovery.vca.second.output.output;
        ob.r20_lower_ohm = n(&case["target_lower_ohm"]);
        ob.sw18_on = case["target_sw18_on"].as_bool().unwrap();
        let dc = global::initial_state(p, conversion, headphone, dc_boundary, seed).unwrap();
        for i in 0..66 {
            assert!((dc.node_v[i] - state.node_v[i]).abs() < 1e-6);
        }
        for row in case["rows"].as_array().unwrap() {
            b.bus_v = n(&row["bus_v"]);
            let ob = &mut b.recovery.vca.second.output.output;
            ob.r20_lower_ohm = n(&row["r20_lower_ohm"]);
            ob.sw18_on = row["sw18_on"].as_bool().unwrap();
            let ob = b.recovery.vca.second.output.output;
            let previous = state;
            let result = global::step(
                &mut state,
                p,
                conversion,
                headphone,
                b,
                SolverBudget::default(),
            )
            .unwrap();
            for i in 0..66 {
                let error = (state.node_v[i] - n(&row["node_v"][i])).abs();
                max_node = max_node.max(error);
                assert!(
                    error < 1e-6,
                    "R61 {} R20 {} SW18 {} sample {} node {i}: {error}",
                    p.r61_ohm,
                    ob.r20_lower_ohm,
                    ob.sw18_on,
                    row["index"]
                );
            }
            for (actual, name) in [
                (result.output.j7_v, "j7_v"),
                (result.output.j4_hi_v, "j4_hi_v"),
                (result.output.j5_lo_v, "j5_lo_v"),
            ] {
                let error = (actual - n(&row[name])).abs();
                max_jack = max_jack.max(error);
                assert!(error < 1e-6);
            }
            if ob.r20_lower_ohm == 0.0 || !ob.sw18_on {
                assert_eq!(result.output.j4_hi_v, 0.0);
                assert_eq!(result.output.j5_lo_v, 0.0);
            }
            assert!((state.c10_capacitor_v - n(&row["c10_v"])).abs() < 1e-6);
            assert!((state.capacitor_v[16] - n(&row["c18_v"])).abs() < 1e-7);
            for (i, name) in [(13, "C19"), (14, "C15"), (15, "C21")] {
                assert!((state.capacitor_v[i] - n(&row["amp_capacitor_v"][name])).abs() < 1e-6);
            }
            assert!((result.output.tail_current_a - n(&row["tail_current_a"])).abs() < 1e-9);
            let (residual, _) =
                global::linearize(&previous, p, conversion, headphone, b, &state.node_v).unwrap();
            assert!(residual.iter().all(|v| v.abs() < 1e-11));
            count += 1;
        }
    }
    assert_eq!(count, 128);
    println!("R20 endpoint FD: steps={count} max_node_error_v={max_node:.9e} max_jack_error_v={max_jack:.9e}");
}

#[test]
fn long_trace_switch_windows_match_independent_fd_from_shared_histories() {
    use rf_d_circuit::circuit66 as global;
    let fixture: Value = serde_json::from_str(include_str!(
        "../../../evidence/circuit66_stress_probe_vectors.json"
    ))
    .unwrap();
    let (bjt, conversion, headphone, rb) = setup();
    let windows = fixture["windows"].as_array().unwrap();
    assert_eq!(windows.len(), 48);
    let mut max_node = 0.0_f64;
    let mut max_j7 = 0.0_f64;
    let mut count = 0;
    for window in windows {
        let rate = n(&window["sample_rate_hz"]);
        let p = Parameters {
            ladder_transistor: bjt,
            cutoff: cutoff::Parameters { q26: bjt, q28: bjt },
            r61_ohm: n(&window["r61_ohm"]),
            r30_ohm: 830.0,
        };
        let initial = &window["initial"];
        let mut state = global::State {
            node_v: std::array::from_fn(|i| n(&initial["node_v"][i])),
            previous_node_v: std::array::from_fn(|i| n(&initial["previous_node_v"][i])),
            capacitor_v: std::array::from_fn(|i| n(&initial["capacitor_v"][i])),
            c10_capacitor_v: n(&initial["c10_v"]),
        };
        let rows = window["rows"].as_array().unwrap();
        assert_eq!(rows.len(), 4);
        for row in rows {
            let v = &row["boundary"];
            let mut b = Boundary {
                bus_v: n(&v["bus_v"]),
                recovery: rb,
                panel: panel(&v["panel"]),
                range_fraction_from_ground: n(&v["range_fraction"]),
                r14_ohm: v["r14_ohm"].as_f64(),
            };
            b.recovery.vca.loudness_v = n(&v["loudness_v"]);
            b.recovery.vca.second.q21_base_v = n(&v["q21_base_v"]);
            let ob = &mut b.recovery.vca.second.output.output;
            ob.dt_s = 1.0 / rate;
            ob.r21_lower_ohm = n(&v["r21_lower_ohm"]);
            ob.tip_load_ohm = v["tip_load_ohm"].as_f64();
            ob.ring_load_ohm = v["ring_load_ohm"].as_f64();
            ob.sw18_on = v["sw18_on"].as_bool().unwrap();
            let previous = state;
            let result = global::step(
                &mut state,
                p,
                conversion,
                headphone,
                b,
                SolverBudget::default(),
            )
            .unwrap_or_else(|e| {
                panic!(
                    "probe rate {rate} R61 {} sample {}: {e:?}",
                    p.r61_ohm, row["sample"]
                )
            });
            for i in 0..66 {
                let error = (state.node_v[i] - n(&row["node_v"][i])).abs();
                max_node = max_node.max(error);
                assert!(
                    error < 1e-6,
                    "probe rate {rate} R61 {} sample {} node {i}: {error}",
                    p.r61_ohm,
                    row["sample"]
                );
            }
            let error = (result.output.j7_v - n(&row["j7_v"])).abs();
            max_j7 = max_j7.max(error);
            assert!(error < 1e-6);
            assert!((result.output.j4_hi_v - n(&row["j4_hi_v"])).abs() < 1e-6);
            assert!((result.output.j5_lo_v - n(&row["j5_lo_v"])).abs() < 1e-6);
            assert!((result.output.tail_current_a - n(&row["tail_current_a"])).abs() < 1e-9);
            assert!((state.c10_capacitor_v - n(&row["c10_v"])).abs() < 1e-6);
            assert!((state.capacitor_v[16] - n(&row["c18_v"])).abs() < 1e-7);
            for (i, name) in [(13, "C19"), (14, "C15"), (15, "C21")] {
                assert!((state.capacitor_v[i] - n(&row["amp_capacitor_v"][name])).abs() < 1e-6);
            }
            if b.r14_ohm.is_none() {
                assert_eq!(
                    state.c10_capacitor_v.to_bits(),
                    previous.c10_capacitor_v.to_bits()
                );
            }
            assert!(result.output.max_ladder_kcl_residual_a < 1e-11);
            count += 1;
        }
    }
    assert_eq!(count, 192);
    println!("stress FD windows: steps={count} max_node_error_v={max_node:.9e} max_j7_error_v={max_j7:.9e}");
}
fn panel(v: &Value) -> PanelBoundary {
    PanelBoundary {
        cutoff_fraction_from_neg10: n(&v["cutoff_fraction_from_neg10"]),
        scale_active_ohm: n(&v["scale_active_ohm"]),
        contour_pin16_v: n(&v["contour_pin16_v"]),
        external_control_v: v["external_control_v"].as_f64(),
        external_source_ohm: n(&v["external_source_ohm"]),
        filter_mod_on: v["filter_mod_on"].as_bool().unwrap(),
        modulation_source_v: v["modulation_source_v"].as_f64(),
        modulation_source_ohm: n(&v["modulation_source_ohm"]),
        keyboard_1_3_on: v["keyboard_1_3_on"].as_bool().unwrap(),
        keyboard_2_3_on: v["keyboard_2_3_on"].as_bool().unwrap(),
        keyboard_cv_v: v["keyboard_cv_v"].as_f64(),
        keyboard_source_ohm: n(&v["keyboard_source_ohm"]),
    }
}
fn setup() -> (
    Bjt,
    ConversionParameters,
    HeadphoneParameters,
    RecoveryBoundary,
) {
    let fixture: Value = serde_json::from_str(include_str!(
        "../../../evidence/recovery_vca_output_vectors.json"
    ))
    .unwrap();
    let case = &fixture["case"];
    let t = &case["transistor_parameters"];
    let bjt = Bjt {
        transistor_is_a: n(&t["is_a"]),
        beta_forward: n(&t["beta_forward"]),
        beta_reverse: n(&t["beta_reverse"]),
        temperature_k: n(&t["temperature_k"]),
    };
    let c = &case["output_parameters"];
    let h = &case["headphone_parameters"];
    let d = &c["diode_model"];
    let conversion = ConversionParameters {
        transistor_is_a: n(&c["is_a"]),
        beta_forward: n(&c["beta_forward"]),
        beta_reverse: n(&c["beta_reverse"]),
        temperature_k: n(&c["temperature_k"]),
        diode: Some(DiodeParameters {
            is_a: n(&d["is_a"]),
            ideality: n(&d["ideality"]),
        }),
    };
    let headphone = HeadphoneParameters {
        transistor_is_a: n(&h["is_a"]),
        beta_forward: n(&h["beta_forward"]),
        beta_reverse: n(&h["beta_reverse"]),
        temperature_k: n(&h["temperature_k"]),
        diode_is_a: n(&d["is_a"]),
        diode_ideality: n(&d["ideality"]),
    };
    let b = &case["initial_boundary"];
    let rb = RecoveryBoundary {
        ladder_left_v: 0.0,
        ladder_right_v: 0.0,
        vca: FirstBoundary {
            recover_collector_v: 0.0,
            loudness_v: n(&b["loudness_v"]),
            first_balance_left_ohm: n(&b["first_balance_left_ohm"]),
            second: SecondBoundary {
                q14_base_v: 0.0,
                q13_base_v: 0.0,
                q21_base_v: n(&b["q21_base_v"]),
                first_balance_wiper_v: 0.0,
                second_balance_left_ohm: n(&b["second_balance_left_ohm"]),
                minus_v: n(&b["minus_v"]),
                output: BoundaryC4 {
                    second_balance_wiper_v: 0.0,
                    q12_base_v: 0.0,
                    q17_base_v: 0.0,
                    plus_v: n(&b["plus_v"]),
                    output: OutputBoundary {
                        q17_collector_v: 0.0,
                        r20_lower_ohm: n(&case["r20_lower_ohm"]),
                        hi_load_ohm: n(&case["hi_load_ohm"]),
                        lo_load_ohm: n(&case["lo_load_ohm"]),
                        sw18_on: true,
                        r21_lower_ohm: n(&case["r21_lower_ohm"]),
                        tip_load_ohm: Some(n(&case["tip_ring_load_ohm"])),
                        ring_load_ohm: Some(n(&case["tip_ring_load_ohm"])),
                        dt_s: n(&case["dt_s"]),
                    },
                },
            },
        },
    };
    (bjt, conversion, headphone, rb)
}

fn nodes(state: &State, previous: Option<&State>, dt: f64) -> [f64; 66] {
    let mut x = [0.0; 66];
    x[..16].copy_from_slice(&state.chain.node_v);
    let r = &state.chain.recovery;
    x[16..24].copy_from_slice(&r.node_v);
    x[24..34].copy_from_slice(&r.vca.node_v);
    x[34..40].copy_from_slice(&r.vca.second.node_v);
    let c = &r.vca.second.downstream;
    x[40..47].copy_from_slice(&c.node_v);
    x[47] = c.output.c2_right_v;
    x[49] = c.output.panel.r21_wiper_v;
    x[50..62].copy_from_slice(&c.output.panel.amp.node_v);
    if let Some(old) = previous {
        let old_c19 = old
            .chain
            .recovery
            .vca
            .second
            .downstream
            .output
            .panel
            .amp
            .capacitor_v[0];
        x[48] = x[49] + 3000.0 * (x[49] / 2000.0 + 2.5e-6 / dt * (x[49] - x[50] - old_c19));
    }
    x[62..].copy_from_slice(&state.cutoff.node_v);
    x
}

#[test]
fn cutoff_ladder_emphasis_vcas_and_j7_match_128_monolithic_66_node_steps() {
    let fixture: Value =
        serde_json::from_str(include_str!("../../../evidence/cutoff_j7_vectors.json")).unwrap();
    assert_eq!(fixture["schema"], "rf-d/cutoff-j7-vectors/v1");
    let (bjt, conversion, headphone, rb) = setup();
    let mut max_node = 0.0_f64;
    let mut max_j7 = 0.0_f64;
    let mut max_tail = 0.0_f64;
    let mut signal_power = 0.0;
    let mut error_power = 0.0;
    for case in fixture["cases"].as_array().unwrap() {
        let p = Parameters {
            ladder_transistor: bjt,
            cutoff: cutoff::Parameters { q26: bjt, q28: bjt },
            r61_ohm: n(&case["r61_ohm"]),
            r30_ohm: 830.0,
        };
        let base = Boundary {
            bus_v: 0.0,
            recovery: rb,
            panel: panel(&case["controls"]["panel"]),
            range_fraction_from_ground: n(&case["controls"]["range_fraction"]),
            r14_ohm: Some(0.0),
        };
        let seed = std::array::from_fn(|i| n(&case["initial"]["node_v"][i]));
        let mut state = circuit::initial_state(p, conversion, headphone, base, seed).unwrap();
        for (i, value) in nodes(&state, None, n(&fixture["dt_s"])).iter().enumerate() {
            assert!(
                (value - n(&case["initial"]["node_v"][i])).abs() < 1e-6,
                "DC node {i}"
            );
        }
        for row in case["rows"].as_array().unwrap() {
            let mut b = Boundary {
                bus_v: n(&row["bus_v"]),
                panel: panel(&row["panel"]),
                range_fraction_from_ground: n(&row["range_fraction"]),
                r14_ohm: Some(n(&row["r14_ohm"])),
                ..base
            };
            b.recovery.vca.second.output.output.sw18_on = row["sw18_on"].as_bool().unwrap();
            let previous = state;
            let result = circuit::step(
                &mut state,
                p,
                conversion,
                headphone,
                b,
                SolverBudget::default(),
            )
            .unwrap_or_else(|e| panic!("R61 {} step {}: {e:?}", p.r61_ohm, row["index"]));
            for (i, actual) in nodes(&state, Some(&previous), n(&fixture["dt_s"]))
                .iter()
                .enumerate()
            {
                let expected = n(&row["node_v"][i]);
                max_node = max_node.max((actual - expected).abs());
                assert!(
                    (actual - expected).abs() < 2e-6,
                    "R61 {} step {} node {i}: {actual} vs {expected}",
                    p.r61_ohm,
                    row["index"]
                );
            }
            let error = result.j7_v - n(&row["j7_v"]);
            max_j7 = max_j7.max(error.abs());
            signal_power += n(&row["j7_v"]).powi(2);
            error_power += error.powi(2);
            max_tail = max_tail.max((result.tail_current_a - n(&row["tail_current_a"])).abs());
            assert!((state.cutoff.c18_v - n(&row["c18_v"])).abs() < 1e-7);
            assert!((state.chain.c10_capacitor_v - n(&row["c10_v"])).abs() < 1e-6);
            assert!((result.j4_hi_v - n(&row["j4_hi_v"])).abs() < 1e-6);
            assert!((result.j5_lo_v - n(&row["j5_lo_v"])).abs() < 1e-6);
            assert!(result.max_ladder_kcl_residual_a < 1e-10);
            assert!(result.max_cutoff_kcl_residual_a < 1e-11);
            // Re-evaluate the accepted TAIL with exactly the old C18 history.
            let port = cutoff::solve_input_port(
                &previous.cutoff,
                p.cutoff,
                cutoff::Boundary {
                    panel: b.panel,
                    range_fraction_from_ground: b.range_fraction_from_ground,
                    tail_v: state.chain.node_v[5],
                    dt_s: n(&fixture["dt_s"]),
                },
                SolverBudget::default(),
            )
            .unwrap();
            assert_eq!(state.cutoff, port.next_state);
        }
        // Invalid control and exhausted numerical budget must preserve all caps.
        let previous = state;
        assert_eq!(
            circuit::step(
                &mut state,
                p,
                conversion,
                headphone,
                Boundary {
                    range_fraction_from_ground: f64::NAN,
                    ..base
                },
                SolverBudget::default()
            )
            .unwrap_err(),
            StepError::InvalidInput
        );
        assert_eq!(state, previous);
        assert!(circuit::step(
            &mut state,
            p,
            conversion,
            headphone,
            base,
            SolverBudget {
                iterations: 1,
                line_search_halvings: 16
            }
        )
        .is_err());
        assert_eq!(state, previous);
        // A rejected outer predictor must not consume C18 before retrying.
        let mut fallback = state;
        fallback.chain.previous_node_v[1] -= 1e6;
        let a = circuit::step(
            &mut state,
            p,
            conversion,
            headphone,
            base,
            SolverBudget::default(),
        )
        .unwrap();
        let z = circuit::step(
            &mut fallback,
            p,
            conversion,
            headphone,
            base,
            SolverBudget::default(),
        )
        .unwrap();
        assert!(z.predictor_fallback);
        assert!((a.j7_v - z.j7_v).abs() < 1e-6);
        assert!((state.cutoff.c18_v - fallback.cutoff.c18_v).abs() < 1e-7);
    }
    let snr = 10.0 * (signal_power / error_power).log10();
    println!("Q26/Q28 128 steps: max_node_error_v={max_node:.3e} max_j7_error_v={max_j7:.3e} max_tail_error_a={max_tail:.3e} numerical_snr_db={snr:.1}");
    assert!(max_tail < 1e-9);
    assert!(max_j7 < 1e-6);
    assert!(snr > 90.0);
}

#[test]
fn global_analytic_newton_matches_oracle_and_preserves_history_on_rejection() {
    use rf_d_circuit::circuit66 as global;
    let fixture: Value =
        serde_json::from_str(include_str!("../../../evidence/cutoff_j7_vectors.json")).unwrap();
    let (bjt, conversion, headphone, rb) = setup();
    let mut max_node = 0.0_f64;
    let mut max_j7 = 0.0_f64;
    let mut signal = 0.0;
    let mut error_power = 0.0;
    for case in fixture["cases"].as_array().unwrap() {
        let p = Parameters {
            ladder_transistor: bjt,
            cutoff: cutoff::Parameters { q26: bjt, q28: bjt },
            r61_ohm: n(&case["r61_ohm"]),
            r30_ohm: 830.0,
        };
        let base = Boundary {
            bus_v: 0.0,
            recovery: rb,
            panel: panel(&case["controls"]["panel"]),
            range_fraction_from_ground: 0.1,
            r14_ohm: Some(0.0),
        };
        let seed = std::array::from_fn(|i| n(&case["initial"]["node_v"][i]));
        let mut state = global::initial_state(p, conversion, headphone, base, seed).unwrap();
        let mut nested = circuit::initial_state(p, conversion, headphone, base, seed).unwrap();
        for row in case["rows"].as_array().unwrap() {
            let index = row["index"].as_u64().unwrap();
            let mut b = Boundary {
                bus_v: n(&row["bus_v"]),
                panel: panel(&row["panel"]),
                range_fraction_from_ground: n(&row["range_fraction"]),
                r14_ohm: Some(n(&row["r14_ohm"])),
                ..base
            };
            b.recovery.vca.second.output.output.sw18_on = row["sw18_on"].as_bool().unwrap();
            let old = state;
            let result = global::step(
                &mut state,
                p,
                conversion,
                headphone,
                b,
                SolverBudget::default(),
            )
            .unwrap_or_else(|e| panic!("global R61 {} step {index}: {e:?}", p.r61_ohm));
            let split = circuit::step(
                &mut nested,
                p,
                conversion,
                headphone,
                b,
                SolverBudget::default(),
            )
            .unwrap();
            assert!((split.j7_v - result.output.j7_v).abs() < 1e-6);
            for (i, actual) in state.node_v.iter().enumerate() {
                let error = (actual - n(&row["node_v"][i])).abs();
                max_node = max_node.max(error);
                assert!(
                    error < 1e-6,
                    "global R61 {} step {index} node {i}: {actual} vs {}",
                    p.r61_ohm,
                    row["node_v"][i]
                );
            }
            let error = result.output.j7_v - n(&row["j7_v"]);
            max_j7 = max_j7.max(error.abs());
            signal += n(&row["j7_v"]).powi(2);
            error_power += error.powi(2);
            assert!((state.c10_capacitor_v - n(&row["c10_v"])).abs() < 1e-6);
            assert!((state.capacitor_v[16] - n(&row["c18_v"])).abs() < 1e-7);
            assert!((result.output.tail_current_a - n(&row["tail_current_a"])).abs() < 1e-9);
            assert!((result.output.j4_hi_v - n(&row["j4_hi_v"])).abs() < 1e-6);
            assert!((result.output.j5_lo_v - n(&row["j5_lo_v"])).abs() < 1e-6);
            assert!(result.output.max_ladder_kcl_residual_a < 1e-11);
            if [0, 24, 48].contains(&index) {
                // Every column, including BJT-controlled bases and the series
                // C10 return, checked with independent symmetric differences.
                let (_, j) =
                    global::linearize(&old, p, conversion, headphone, b, &state.node_v).unwrap();
                for col in 0..66 {
                    let mut high = state.node_v;
                    let mut low = high;
                    high[col] += 1e-7;
                    low[col] -= 1e-7;
                    let rh = global::linearize(&old, p, conversion, headphone, b, &high)
                        .unwrap()
                        .0;
                    let rl = global::linearize(&old, p, conversion, headphone, b, &low)
                        .unwrap()
                        .0;
                    for row in 0..66 {
                        let fd = (rh[row] - rl[row]) / 2e-7;
                        assert!(
                            (fd - j[row][col]).abs() < 1e-8 + 3e-6 * fd.abs(),
                            "global analytic row {row} col {col}: {} vs {fd}",
                            j[row][col]
                        );
                    }
                }
            }
        }
        let old = state;
        assert_eq!(
            global::step(
                &mut state,
                p,
                conversion,
                headphone,
                Boundary {
                    range_fraction_from_ground: f64::NAN,
                    ..base
                },
                SolverBudget::default()
            )
            .unwrap_err(),
            StepError::InvalidInput
        );
        assert_eq!(state, old);
        assert!(global::step(
            &mut state,
            p,
            conversion,
            headphone,
            base,
            SolverBudget {
                iterations: 1,
                line_search_halvings: 16
            }
        )
        .is_err());
        assert_eq!(state, old);
        let mut failed_predictor = state;
        failed_predictor.previous_node_v[1] -= 1e6;
        let a = global::step(
            &mut state,
            p,
            conversion,
            headphone,
            base,
            SolverBudget::default(),
        )
        .unwrap();
        let z = global::step(
            &mut failed_predictor,
            p,
            conversion,
            headphone,
            base,
            SolverBudget::default(),
        )
        .unwrap();
        assert!(z.output.predictor_fallback);
        assert!((a.output.j7_v - z.output.j7_v).abs() < 1e-7);
        assert!((state.capacitor_v[16] - failed_predictor.capacitor_v[16]).abs() < 1e-7);
    }
    let snr = 10.0 * (signal / error_power).log10();
    println!("global 128 steps: max_node_error_v={max_node:.3e} max_j7_error_v={max_j7:.3e} numerical_snr_db={snr:.1}");
    assert!(max_j7 < 1e-6);
    assert!(snr > 90.0);
}
