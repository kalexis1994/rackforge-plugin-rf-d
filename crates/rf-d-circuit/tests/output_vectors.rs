use rf_d_circuit::output::{initial_output_state, solve_output_boundary, OutputBoundary};
use rf_d_circuit::{Parameters, SolverBudget, StepError};
use serde_json::Value;

fn number(v: &Value) -> f64 {
    v.as_f64().unwrap()
}
fn optional(v: &Value) -> Option<f64> {
    v.as_f64()
}
fn fixture() -> Value {
    serde_json::from_str(include_str!(
        "../../../evidence/headphone_c2_port_vectors.json"
    ))
    .unwrap()
}
fn parameters(v: &Value) -> Parameters {
    Parameters {
        transistor_is_a: number(&v["transistor_is_a"]),
        beta_forward: number(&v["beta_forward"]),
        beta_reverse: number(&v["beta_reverse"]),
        temperature_k: number(&v["temperature_k"]),
        diode_is_a: number(&v["diode_model"]["is_a"]),
        diode_ideality: number(&v["diode_model"]["ideality"]),
    }
}

#[test]
fn c2_main_panel_and_board3_match_independent_python() {
    let fixture = fixture();
    assert_eq!(fixture["schema"], "rf-d/c2-panel-board3-vectors/v1");
    let mut count = 0;
    for case in fixture["cases"].as_array().unwrap() {
        let p = parameters(&case["parameters"]);
        let mut state =
            initial_output_state(p, number(&case["initial"]["c2_capacitor_v"])).unwrap();
        assert_eq!(state.c2_right_v, number(&case["initial"]["c2_right_v"]));
        for (index, row) in case["steps"].as_array().unwrap().iter().enumerate() {
            let boundary = OutputBoundary {
                q17_collector_v: number(&row["q17_collector_v"]),
                r20_lower_ohm: number(&case["r20_lower_ohm"]),
                hi_load_ohm: number(&case["hi_load_ohm"]),
                lo_load_ohm: number(&case["lo_load_ohm"]),
                sw18_on: row["sw18_on"].as_bool().unwrap(),
                r21_lower_ohm: number(&case["r21_lower_ohm"]),
                tip_load_ohm: optional(&case["tip_ring_load_ohm"]),
                ring_load_ohm: optional(&case["tip_ring_load_ohm"]),
                dt_s: number(&case["dt_s"]),
            };
            let output = solve_output_boundary(&mut state, p, boundary, SolverBudget::default())
                .unwrap_or_else(|e| panic!("{} step {index}: {e:?}", case["id"]));
            for (name, actual) in [
                ("c2_right_v", output.c2_right_v),
                ("c2_capacitor_v", state.c2_capacitor_v),
                ("board4_pin21_v", output.board4_pin21_v),
                ("j4_hi_v", output.j4_hi_v),
                ("j5_lo_v", output.j5_lo_v),
                ("r21_wiper_v", output.panel.r21_wiper_v),
                ("j7_v", output.j7_v),
                ("c2_current_a", output.c2_current_a),
                ("r75_current_a", output.r75_current_a),
                ("r77_current_a", output.r77_current_a),
            ] {
                let expected = number(&row[name]);
                let tolerance = if name.ends_with("_a") { 1e-10 } else { 1e-6 };
                assert!(
                    (actual - expected).abs() < tolerance,
                    "{} step {index} {name}: {actual} vs {expected}",
                    case["id"]
                );
            }
            for (node, actual) in state.panel.amp.node_v.iter().enumerate() {
                let expected = number(&row["amp_node_v"][node]);
                assert!(
                    (actual - expected).abs() < 1e-6,
                    "{} step {index} amp node {node}",
                    case["id"]
                );
            }
            for (i, name) in ["C19", "C15", "C21"].iter().enumerate() {
                let expected = number(&row["amp_capacitor_v"][name]);
                assert!(
                    (state.panel.amp.capacitor_v[i] - expected).abs() < 1e-6,
                    "{} step {index} amp capacitor {name}",
                    case["id"]
                );
            }
            assert!(output.max_c2_right_kcl_residual_a < 1e-10);
            assert!(
                (output.c2_current_a - output.r75_current_a - output.r77_current_a).abs() < 1e-10
            );
            assert!(output.panel.diagnostics.max_panel_kcl_residual_a < 1e-10);
            assert!(output.panel.diagnostics.board3.max_kcl_residual_a < 1e-10);
            count += 1;
        }
    }
    assert_eq!(count, 96);
}

#[test]
fn invalid_boundary_preserves_all_output_state() {
    let fixture = fixture();
    let case = &fixture["cases"][0];
    let p = parameters(&case["parameters"]);
    let mut state = initial_output_state(p, 5.0).unwrap();
    let before = state;
    let error = solve_output_boundary(
        &mut state,
        p,
        OutputBoundary {
            q17_collector_v: 5.5,
            r20_lower_ohm: 0.0,
            hi_load_ohm: 10000.0,
            lo_load_ohm: 100000.0,
            sw18_on: true,
            r21_lower_ohm: 2000.0,
            tip_load_ohm: Some(32.0),
            ring_load_ohm: Some(32.0),
            dt_s: 1.0 / 48000.0,
        },
        SolverBudget::default(),
    )
    .unwrap_err();
    assert_eq!(error, StepError::InvalidInput);
    assert_eq!(state, before);
}
