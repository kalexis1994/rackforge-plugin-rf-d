use rf_d_circuit::output::OutputBoundary;
use rf_d_circuit::output_conversion::{DiodeParameters, Parameters as ConversionParameters};
use rf_d_circuit::output_conversion_c4::{
    initial_state, solve_input_port, step, BoundaryC4, NODE_NAMES,
};
use rf_d_circuit::{Parameters as HeadphoneParameters, SolverBudget, StepError};
use serde_json::Value;

fn n(v: &Value) -> f64 {
    v.as_f64().unwrap()
}

fn parameters(case: &Value) -> (ConversionParameters, HeadphoneParameters) {
    let c = &case["conversion_parameters"];
    let h = &case["headphone_parameters"];
    (
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

fn boundary(case: &Value, row: &Value, controls: &Value) -> BoundaryC4 {
    BoundaryC4 {
        second_balance_wiper_v: n(&controls["second_balance_wiper_v"]),
        q12_base_v: n(&controls["q12_base_v"]),
        q17_base_v: n(&controls["q17_base_v"]),
        plus_v: n(&controls["plus_v"]),
        output: OutputBoundary {
            q17_collector_v: 0.0,
            r20_lower_ohm: n(&case["r20_lower_ohm"]),
            hi_load_ohm: n(&case["hi_load_ohm"]),
            lo_load_ohm: n(&case["lo_load_ohm"]),
            sw18_on: row["sw18_on"].as_bool().unwrap_or(true),
            r21_lower_ohm: n(&case["r21_lower_ohm"]),
            tip_load_ohm: case["tip_ring_load_ohm"].as_f64(),
            ring_load_ohm: case["tip_ring_load_ohm"].as_f64(),
            dt_s: n(&case["dt_s"]),
        },
    }
}

fn fixture() -> Value {
    serde_json::from_str(include_str!(
        "../../../evidence/output_conversion_c4_vectors.json"
    ))
    .unwrap()
}

#[test]
fn c4_and_c2_joint_step_matches_nine_variable_python() {
    let fixture = fixture();
    assert_eq!(fixture["schema"], "rf-d/output-conversion-c4-vectors/v1");
    for (i, name) in NODE_NAMES.iter().enumerate() {
        assert_eq!(&fixture["node_order"][i], name);
    }
    let mut count = 0;
    for case in fixture["cases"].as_array().unwrap() {
        let (conversion, headphone) = parameters(case);
        let mut state = initial_state(
            conversion,
            headphone,
            boundary(case, &Value::Null, &case["initial_boundary"]),
        )
        .unwrap_or_else(|e| panic!("{} DC: {e:?}", case["id"]));
        for (i, actual) in state.node_v.iter().enumerate() {
            let expected = n(&case["initial"]["node_v"][i]);
            assert!(
                (actual - expected).abs() < 1e-8,
                "{} initial {}: {actual} vs {expected}",
                case["id"],
                NODE_NAMES[i]
            );
        }
        assert!((state.c4_capacitor_v - n(&case["initial"]["c4_capacitor_v"])).abs() < 1e-8);
        for (index, row) in case["steps"].as_array().unwrap().iter().enumerate() {
            let previous = state;
            let b = boundary(case, row, &row["boundary"]);
            let result = step(
                &mut state,
                conversion,
                headphone,
                b,
                SolverBudget::default(),
            )
            .unwrap_or_else(|e| panic!("{} step {index}: {e:?}", case["id"]));
            for (i, actual) in state.node_v.iter().enumerate() {
                let expected = n(&row["node_v"][i]);
                assert!(
                    (actual - expected).abs() < 1e-6,
                    "{} step {index} {}: {actual} vs {expected}",
                    case["id"],
                    NODE_NAMES[i]
                );
            }
            for (name, actual) in [
                ("c4_capacitor_v", state.c4_capacitor_v),
                ("c2_right_v", state.output.c2_right_v),
                ("c2_capacitor_v", state.output.c2_capacitor_v),
                ("r21_wiper_v", state.output.panel.r21_wiper_v),
                ("board4_pin21_v", result.output.board4_pin21_v),
                ("j4_hi_v", result.output.j4_hi_v),
                ("j5_lo_v", result.output.j5_lo_v),
                ("j7_v", result.output.j7_v),
                ("c2_current_a", result.output.c2_current_a),
            ] {
                let expected = n(&row[name]);
                let tolerance = if name.ends_with("_a") { 1e-9 } else { 1e-6 };
                assert!(
                    (actual - expected).abs() < tolerance,
                    "{} step {index} {name}: {actual} vs {expected}",
                    case["id"]
                );
            }
            let old_c4 = if index == 0 {
                n(&case["initial"]["c4_capacitor_v"])
            } else {
                n(&case["steps"][index - 1]["c4_capacitor_v"])
            };
            let i4 = 220e-6 / n(&case["dt_s"]) * (state.c4_capacitor_v - old_c4);
            assert!((i4 - n(&row["c4_current_a"])).abs() < 1e-9);
            for (i, actual) in state.output.panel.amp.node_v.iter().enumerate() {
                assert!((actual - n(&row["amp_node_v"][i])).abs() < 1e-6);
            }
            assert!(result.max_kcl_residual_a < 1e-10);
            assert!(result.output.max_c2_right_kcl_residual_a < 1e-10);
            assert!(result.output.panel.diagnostics.max_panel_kcl_residual_a < 1e-10);
            assert!(result.output.panel.diagnostics.board3.max_kcl_residual_a < 1e-10);
            let port =
                solve_input_port(&previous, conversion, headphone, b, SolverBudget::default())
                    .unwrap();
            assert_eq!(port.next_state, state);
            for output in 0..3 {
                let expected = n(&row["upstream_port_current_a"][output]);
                assert!(
                    (port.current_a[output] - expected).abs() < 1e-9,
                    "{} step {index} upstream current {output}: {} vs {expected}",
                    case["id"],
                    port.current_a[output]
                );
            }
            if [0usize, 8].contains(&index) {
                for column in 0..3 {
                    let mut plus_b = b;
                    let mut minus_b = b;
                    let high_control = match column {
                        0 => &mut plus_b.second_balance_wiper_v,
                        1 => &mut plus_b.q12_base_v,
                        _ => &mut plus_b.q17_base_v,
                    };
                    *high_control += 1e-4;
                    let low_control = match column {
                        0 => &mut minus_b.second_balance_wiper_v,
                        1 => &mut minus_b.q12_base_v,
                        _ => &mut minus_b.q17_base_v,
                    };
                    *low_control -= 1e-4;
                    let high = solve_input_port(
                        &previous,
                        conversion,
                        headphone,
                        plus_b,
                        SolverBudget::default(),
                    )
                    .unwrap();
                    let low = solve_input_port(
                        &previous,
                        conversion,
                        headphone,
                        minus_b,
                        SolverBudget::default(),
                    )
                    .unwrap();
                    for output in 0..3 {
                        let finite_difference =
                            (high.current_a[output] - low.current_a[output]) / 2e-4;
                        assert!(
                            (port.conductance_s[output][column] - finite_difference).abs()
                                < 2e-7 + 1e-4 * finite_difference.abs(),
                            "{} step {index} Y[{output},{column}]: {} vs {finite_difference}",
                            case["id"],
                            port.conductance_s[output][column]
                        );
                    }
                }
            }
            count += 1;
        }
    }
    assert_eq!(count, 28);
}

#[test]
fn invalid_c4_step_preserves_all_state() {
    let fixture = fixture();
    let case = &fixture["cases"][0];
    let (conversion, headphone) = parameters(case);
    let mut b = boundary(case, &Value::Null, &case["initial_boundary"]);
    let mut state = initial_state(conversion, headphone, b).unwrap();
    let previous = state;
    b.output.dt_s = 0.0;
    assert_eq!(
        step(
            &mut state,
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
