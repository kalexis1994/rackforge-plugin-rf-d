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
