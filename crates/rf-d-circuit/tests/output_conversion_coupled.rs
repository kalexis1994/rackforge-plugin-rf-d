use rf_d_circuit::output::OutputBoundary;
use rf_d_circuit::output_conversion::{
    initial_coupled_state, solve_coupled_step, Boundary, CoupledBoundary, DiodeParameters,
    Parameters as ConversionParameters, NODE_NAMES,
};
use rf_d_circuit::{Parameters as HeadphoneParameters, SolverBudget, StepError};
use serde_json::Value;

fn number(value: &Value) -> f64 {
    value.as_f64().unwrap()
}

fn boundary(value: &Value) -> Boundary {
    Boundary {
        q1_base_v: number(&value["q1_base_v"]),
        q12_base_v: number(&value["q12_base_v"]),
        q17_base_v: number(&value["q17_base_v"]),
        plus_v: number(&value["plus_v"]),
    }
}

fn parameters(case: &Value) -> (ConversionParameters, HeadphoneParameters) {
    let c = &case["conversion_parameters"];
    let h = &case["headphone_parameters"];
    (
        ConversionParameters {
            transistor_is_a: number(&c["is_a"]),
            beta_forward: number(&c["beta_forward"]),
            beta_reverse: number(&c["beta_reverse"]),
            temperature_k: number(&c["temperature_k"]),
            diode: Some(DiodeParameters {
                is_a: number(&c["diode_model"]["is_a"]),
                ideality: number(&c["diode_model"]["ideality"]),
            }),
        },
        HeadphoneParameters {
            transistor_is_a: number(&h["is_a"]),
            beta_forward: number(&h["beta_forward"]),
            beta_reverse: number(&h["beta_reverse"]),
            temperature_k: number(&h["temperature_k"]),
            diode_is_a: number(&h["diode_model"]["is_a"]),
            diode_ideality: number(&h["diode_model"]["ideality"]),
        },
    )
}

fn output_boundary(case: &Value, row: &Value) -> OutputBoundary {
    OutputBoundary {
        q17_collector_v: 0.0, // Joint Newton supplies this voltage.
        r20_lower_ohm: number(&case["r20_lower_ohm"]),
        hi_load_ohm: number(&case["hi_load_ohm"]),
        lo_load_ohm: number(&case["lo_load_ohm"]),
        sw18_on: row["sw18_on"].as_bool().unwrap(),
        r21_lower_ohm: number(&case["r21_lower_ohm"]),
        tip_load_ohm: case["tip_ring_load_ohm"].as_f64(),
        ring_load_ohm: case["tip_ring_load_ohm"].as_f64(),
        dt_s: number(&case["dt_s"]),
    }
}

#[test]
fn joint_board4_c2_panel_board3_matches_eight_variable_python() {
    let fixture: Value = serde_json::from_str(include_str!(
        "../../../evidence/output_conversion_c2_vectors.json"
    ))
    .unwrap();
    assert_eq!(fixture["schema"], "rf-d/output-conversion-c2-vectors/v1");
    for (i, name) in NODE_NAMES.iter().enumerate() {
        assert_eq!(&fixture["node_order"][i], name);
    }
    let mut count = 0;
    for case in fixture["cases"].as_array().unwrap() {
        let (conversion, headphone) = parameters(case);
        let mut state =
            initial_coupled_state(conversion, boundary(&case["initial_boundary"]), headphone)
                .unwrap();
        for (i, actual) in state.conversion.node_v.iter().enumerate() {
            assert!((actual - number(&case["initial"]["conversion_node_v"][i])).abs() < 1e-8);
        }
        for (index, row) in case["steps"].as_array().unwrap().iter().enumerate() {
            let b = CoupledBoundary {
                conversion: boundary(&row["boundary"]),
                output: output_boundary(case, row),
            };
            let result = solve_coupled_step(
                &mut state,
                conversion,
                headphone,
                b,
                SolverBudget::default(),
            )
            .unwrap_or_else(|e| panic!("{} step {index}: {e:?}", case["id"]));
            for (node, actual) in state.conversion.node_v.iter().enumerate() {
                let expected = number(&row["conversion_node_v"][node]);
                assert!(
                    (actual - expected).abs() < 1e-6,
                    "{} step {index} conversion {}: {actual} vs {expected}",
                    case["id"],
                    NODE_NAMES[node]
                );
            }
            for (name, actual) in [
                ("c2_right_v", state.output.c2_right_v),
                ("c2_capacitor_v", state.output.c2_capacitor_v),
                ("r21_wiper_v", state.output.panel.r21_wiper_v),
                ("board4_pin21_v", result.output.board4_pin21_v),
                ("j4_hi_v", result.output.j4_hi_v),
                ("j5_lo_v", result.output.j5_lo_v),
                ("j7_v", result.output.j7_v),
                ("c2_current_a", result.output.c2_current_a),
            ] {
                let expected = number(&row[name]);
                let tolerance = if name.ends_with("_a") { 1e-9 } else { 1e-6 };
                assert!(
                    (actual - expected).abs() < tolerance,
                    "{} step {index} {name}: {actual} vs {expected}",
                    case["id"]
                );
            }
            for (node, actual) in state.output.panel.amp.node_v.iter().enumerate() {
                let expected = number(&row["amp_node_v"][node]);
                assert!(
                    (actual - expected).abs() < 1e-6,
                    "{} step {index} board3 node {node}: {actual} vs {expected}",
                    case["id"]
                );
            }
            assert!(result.max_conversion_kcl_residual_a < 1e-10);
            assert!(result.output_port_evaluations >= result.iterations + 1);
            assert!(result.output.max_c2_right_kcl_residual_a < 1e-10);
            assert!(result.output.panel.diagnostics.max_panel_kcl_residual_a < 1e-10);
            assert!(result.output.panel.diagnostics.board3.max_kcl_residual_a < 1e-10);
            count += 1;
        }
    }
    assert_eq!(count, 32);
}

#[test]
fn invalid_joint_boundary_preserves_every_state() {
    let fixture: Value = serde_json::from_str(include_str!(
        "../../../evidence/output_conversion_c2_vectors.json"
    ))
    .unwrap();
    let case = &fixture["cases"][0];
    let (conversion, headphone) = parameters(case);
    let mut state =
        initial_coupled_state(conversion, boundary(&case["initial_boundary"]), headphone).unwrap();
    let before = state;
    let mut b = CoupledBoundary {
        conversion: boundary(&case["steps"][0]["boundary"]),
        output: output_boundary(case, &case["steps"][0]),
    };
    b.output.dt_s = 0.0;
    assert_eq!(
        solve_coupled_step(
            &mut state,
            conversion,
            headphone,
            b,
            SolverBudget::default()
        )
        .unwrap_err(),
        StepError::InvalidInput
    );
    assert_eq!(state, before);
}

#[test]
fn divergent_predictor_falls_back_to_previous_solution() {
    let fixture: Value = serde_json::from_str(include_str!(
        "../../../evidence/output_conversion_c2_vectors.json"
    ))
    .unwrap();
    let case = &fixture["cases"][0];
    let row = &case["steps"][0];
    let (conversion, headphone) = parameters(case);
    let mut reference =
        initial_coupled_state(conversion, boundary(&case["initial_boundary"]), headphone).unwrap();
    let mut divergent = reference;
    divergent.previous_conversion_node_v[5] = 1e6;
    let b = CoupledBoundary {
        conversion: boundary(&row["boundary"]),
        output: output_boundary(case, row),
    };
    let expected = solve_coupled_step(
        &mut reference,
        conversion,
        headphone,
        b,
        SolverBudget::default(),
    )
    .unwrap();
    let result = solve_coupled_step(
        &mut divergent,
        conversion,
        headphone,
        b,
        SolverBudget::default(),
    )
    .unwrap();
    assert!(result.predictor_fallback);
    assert!((result.output.j7_v - expected.output.j7_v).abs() < 1e-9);
    assert!((result.output.j4_hi_v - expected.output.j4_hi_v).abs() < 1e-9);
    for (actual, expected) in divergent
        .conversion
        .node_v
        .iter()
        .zip(reference.conversion.node_v)
    {
        assert!((actual - expected).abs() < 1e-8);
    }
}
