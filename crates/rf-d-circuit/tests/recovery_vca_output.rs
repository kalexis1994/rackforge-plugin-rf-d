use rf_d_circuit::output::OutputBoundary;
use rf_d_circuit::output_conversion::{DiodeParameters, Parameters as ConversionParameters};
use rf_d_circuit::output_conversion_c4::BoundaryC4;
use rf_d_circuit::recovery_vca_output::{
    initial_state, solve_input_port, step, Boundary, NODE_NAMES,
};
use rf_d_circuit::vca1_output::Boundary as FirstBoundary;
use rf_d_circuit::vca2_output::{Boundary as SecondBoundary, Parameters as TransistorParameters};
use rf_d_circuit::{Parameters as HeadphoneParameters, SolverBudget, StepError};
use serde_json::Value;

fn n(v: &Value) -> f64 {
    v.as_f64().unwrap()
}

fn fixture() -> Value {
    serde_json::from_str(include_str!(
        "../../../evidence/recovery_vca_output_vectors.json"
    ))
    .unwrap()
}

fn parameters(
    case: &Value,
) -> (
    TransistorParameters,
    ConversionParameters,
    HeadphoneParameters,
) {
    let v = &case["transistor_parameters"];
    let c = &case["output_parameters"];
    let h = &case["headphone_parameters"];
    (
        TransistorParameters {
            transistor_is_a: n(&v["is_a"]),
            beta_forward: n(&v["beta_forward"]),
            beta_reverse: n(&v["beta_reverse"]),
            temperature_k: n(&v["temperature_k"]),
        },
        ConversionParameters {
            transistor_is_a: n(&c["is_a"]),
            beta_forward: n(&c["beta_forward"]),
            beta_reverse: n(&c["beta_reverse"]),
            temperature_k: n(&c["temperature_k"]),
            diode: Some(DiodeParameters {
                is_a: n(&c["diode_model"]["is_a"]),
                ideality: n(&c["diode_model"]["ideality"]),
            }),
        },
        HeadphoneParameters {
            transistor_is_a: n(&h["is_a"]),
            beta_forward: n(&h["beta_forward"]),
            beta_reverse: n(&h["beta_reverse"]),
            temperature_k: n(&h["temperature_k"]),
            diode_is_a: n(&h["diode_model"]["is_a"]),
            diode_ideality: n(&h["diode_model"]["ideality"]),
        },
    )
}

fn boundary(case: &Value, b: &Value, sw18: bool) -> Boundary {
    Boundary {
        ladder_left_v: n(&b["ladder_left_v"]),
        ladder_right_v: n(&b["ladder_right_v"]),
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
                        sw18_on: sw18,
                        r21_lower_ohm: n(&case["r21_lower_ohm"]),
                        tip_load_ohm: Some(n(&case["tip_ring_load_ohm"])),
                        ring_load_ohm: Some(n(&case["tip_ring_load_ohm"])),
                        dt_s: n(&case["dt_s"]),
                    },
                },
            },
        },
    }
}

#[test]
fn joint_recovery_c1_c5_c9_vca_to_j7_matches_independent_33_variable_python() {
    let fixture = fixture();
    assert_eq!(fixture["schema"], "rf-d/recovery-vca-output-vectors/v1");
    let case = &fixture["case"];
    let (transistors, conversion, headphone) = parameters(case);
    let mut state = initial_state(
        transistors,
        conversion,
        headphone,
        boundary(case, &case["initial_boundary"], true),
    )
    .unwrap_or_else(|e| panic!("recovery/VCA DC: {e:?}"));
    for (i, name) in NODE_NAMES.iter().enumerate() {
        assert_eq!(&fixture["node_order"][i], name);
        let expected = n(&case["initial"]["node_v"][i]);
        assert!(
            (state.node_v[i] - expected).abs() < 1e-6,
            "DC {name}: {} vs {expected}",
            state.node_v[i]
        );
    }
    for (i, actual) in state.vca.node_v.iter().enumerate() {
        let expected = n(&case["initial"]["node_v"][i + 8]);
        assert!(
            (actual - expected).abs() < 1e-6,
            "DC first VCA {i}: {actual} vs {expected}"
        );
    }
    for (index, row) in case["steps"].as_array().unwrap().iter().enumerate() {
        let previous = state;
        let b = boundary(case, &row["boundary"], row["sw18_on"].as_bool().unwrap());
        let result = step(
            &mut state,
            transistors,
            conversion,
            headphone,
            b,
            SolverBudget::default(),
        )
        .unwrap_or_else(|e| panic!("recovery/VCA step {index}: {e:?}"));
        for (i, actual) in state.node_v.iter().enumerate() {
            let expected = n(&row["node_v"][i]);
            assert!(
                (actual - expected).abs() < 1e-6,
                "step {index} {}: {actual} vs {expected}",
                NODE_NAMES[i]
            );
        }
        for (i, actual) in state.vca.node_v.iter().enumerate() {
            let expected = n(&row["node_v"][i + 8]);
            assert!(
                (actual - expected).abs() < 1e-6,
                "step {index} first VCA {i}: {actual} vs {expected}"
            );
        }
        for (i, actual) in state.vca.second.node_v.iter().enumerate() {
            let expected = n(&row["node_v"][i + 18]);
            assert!(
                (actual - expected).abs() < 1e-6,
                "step {index} second VCA {i}: {actual} vs {expected}"
            );
        }
        for (i, actual) in state.vca.second.downstream.node_v.iter().enumerate() {
            let expected = n(&row["node_v"][i + 24]);
            assert!(
                (actual - expected).abs() < 1e-6,
                "step {index} conversion {i}: {actual} vs {expected}"
            );
        }
        for (i, actual) in state.capacitor_v.iter().enumerate() {
            let expected = n(&row["recovery_capacitor_v"][i]);
            assert!(
                (actual - expected).abs() < 1e-6,
                "step {index} recovery C {i}: {actual} vs {expected}"
            );
        }
        for (name, actual) in [
            ("c6_capacitor_v", state.vca.c6_capacitor_v),
            ("c15_capacitor_v", state.vca.c15_capacitor_v),
            ("c4_capacitor_v", state.vca.second.downstream.c4_capacitor_v),
            ("c2_right_v", state.vca.second.downstream.output.c2_right_v),
            (
                "c2_capacitor_v",
                state.vca.second.downstream.output.c2_capacitor_v,
            ),
            (
                "r21_wiper_v",
                state.vca.second.downstream.output.panel.r21_wiper_v,
            ),
            ("j7_v", result.j7_v),
            ("j4_hi_v", result.j4_hi_v),
            ("j5_lo_v", result.j5_lo_v),
        ] {
            let expected = n(&row[name]);
            assert!(
                (actual - expected).abs() < 1e-6,
                "step {index} {name}: {actual} vs {expected}"
            );
        }
        for (i, actual) in state
            .vca
            .second
            .downstream
            .output
            .panel
            .amp
            .node_v
            .iter()
            .enumerate()
        {
            let expected = n(&row["amp_node_v"][i]);
            assert!(
                (actual - expected).abs() < 1e-6,
                "step {index} board 3 node {i}: {actual} vs {expected}"
            );
        }
        assert!(result.max_kcl_residual_a < 1e-10);
        let port = solve_input_port(
            &previous,
            transistors,
            conversion,
            headphone,
            b,
            SolverBudget::default(),
        )
        .unwrap();
        assert_eq!(port.next_state, state);
        for output in 0..2 {
            let expected = n(&row["upstream_port_current_a"][output]);
            assert!(
                (port.current_a[output] - expected).abs() < 1e-9,
                "step {index} ladder port {output}: {} vs {expected}",
                port.current_a[output]
            );
        }
        if [0usize, 6, 11].contains(&index) {
            for column in 0..2 {
                let mut plus = b;
                let mut minus = b;
                if column == 0 {
                    plus.ladder_left_v += 1e-4;
                    minus.ladder_left_v -= 1e-4;
                } else {
                    plus.ladder_right_v += 1e-4;
                    minus.ladder_right_v -= 1e-4;
                }
                let high = solve_input_port(
                    &previous,
                    transistors,
                    conversion,
                    headphone,
                    plus,
                    SolverBudget::default(),
                )
                .unwrap();
                let low = solve_input_port(
                    &previous,
                    transistors,
                    conversion,
                    headphone,
                    minus,
                    SolverBudget::default(),
                )
                .unwrap();
                for output in 0..2 {
                    let fd = (high.current_a[output] - low.current_a[output]) / 2e-4;
                    assert!(
                        (port.conductance_s[output][column] - fd).abs() < 2e-7 + 1e-3 * fd.abs(),
                        "step {index} Y[{output},{column}]: {} vs {fd}",
                        port.conductance_s[output][column]
                    );
                }
            }
        }
    }
}

#[test]
fn invalid_ladder_boundary_preserves_all_recovery_and_output_state() {
    let fixture = fixture();
    let case = &fixture["case"];
    let (transistors, conversion, headphone) = parameters(case);
    let mut b = boundary(case, &case["initial_boundary"], true);
    let mut state = initial_state(transistors, conversion, headphone, b).unwrap();
    let previous = state;
    b.ladder_left_v = f64::NAN;
    assert_eq!(
        step(
            &mut state,
            transistors,
            conversion,
            headphone,
            b,
            SolverBudget::default()
        )
        .unwrap_err(),
        StepError::InvalidInput
    );
    assert_eq!(state, previous);
}
