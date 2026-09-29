use rf_d_circuit::panel::{solve_panel_boundary, PanelBoundary, PanelState};
use rf_d_circuit::{solve_input_port, Parameters, SolverBudget, State, StepError};
use serde_json::Value;

fn n(v: &Value) -> f64 {
    v.as_f64().unwrap()
}
fn optional(v: &Value) -> Option<f64> {
    v.as_f64()
}
fn fixture() -> Value {
    serde_json::from_str(include_str!(
        "../../../evidence/headphone_panel_port_vectors.json"
    ))
    .unwrap()
}
fn params(v: &Value) -> Parameters {
    Parameters {
        transistor_is_a: n(&v["transistor_is_a"]),
        beta_forward: n(&v["beta_forward"]),
        beta_reverse: n(&v["beta_reverse"]),
        temperature_k: n(&v["temperature_k"]),
        diode_is_a: n(&v["diode_model"]["is_a"]),
        diode_ideality: n(&v["diode_model"]["ideality"]),
    }
}
fn state(v: &Value) -> PanelState {
    let values = v["node_v"].as_array().unwrap();
    PanelState {
        amp: State {
            node_v: std::array::from_fn(|i| n(&values[i])),
            capacitor_v: [
                n(&v["capacitor_v"]["C19"]),
                n(&v["capacitor_v"]["C15"]),
                n(&v["capacitor_v"]["C21"]),
            ],
        },
        r21_wiper_v: n(&v["r21_wiper_v"]),
    }
}

#[test]
fn simultaneous_panel_and_board3_match_independent_python() {
    let fixture = fixture();
    assert_eq!(fixture["schema"], "rf-d/panel-board3-port-vectors/v1");
    let mut count = 0;
    for case in fixture["cases"].as_array().unwrap() {
        let mut state = state(&case["initial"]);
        let p = params(&case["parameters"]);
        for (index, reference) in case["steps"].as_array().unwrap().iter().enumerate() {
            let previous = state;
            let output = solve_panel_boundary(
                &mut state,
                p,
                PanelBoundary {
                    c2_right_v: n(&reference["c2_right_v"]),
                    r21_lower_ohm: n(&case["r21_lower_ohm"]),
                    dt_s: n(&case["dt_s"]),
                    tip_load_ohm: optional(&case["tip_load_ohm"]),
                    ring_load_ohm: optional(&case["ring_load_ohm"]),
                },
                SolverBudget::default(),
            )
            .unwrap_or_else(|e| panic!("{} step {index}: {e:?}", case["id"]));
            for (name, actual) in [
                ("board4_pin22_v", output.board4_pin22_v),
                ("r21_wiper_v", output.r21_wiper_v),
                ("j7_v", output.j7_v),
                ("r77_current_a", output.r77_current_a),
                ("c19_current_a", output.c19_current_a),
            ] {
                let expected = n(&reference[name]);
                let tolerance = if name.ends_with("_a") { 1e-10 } else { 1e-6 };
                assert!(
                    (actual - expected).abs() < tolerance,
                    "{} step {index} {name}: {actual} vs {expected}",
                    case["id"]
                );
            }
            for (node, actual) in state.amp.node_v.iter().enumerate() {
                assert!(
                    (actual - n(&reference["node_v"][node])).abs() < 1e-6,
                    "{} step {index} amp node {node}",
                    case["id"]
                );
            }
            assert!(output.diagnostics.max_panel_kcl_residual_a < 1e-10);
            assert!(output.diagnostics.board3.max_kcl_residual_a < 1e-10);
            // The cached accepted port must be bitwise identical to resolving
            // it again from the same previous state, as the uncached path did.
            let recomputed = solve_input_port(
                &previous.amp,
                p,
                output.r21_wiper_v,
                n(&case["dt_s"]),
                optional(&case["tip_load_ohm"]),
                optional(&case["ring_load_ohm"]),
                SolverBudget::default(),
            )
            .unwrap();
            assert_eq!(state.amp, recomputed.next_state);
            assert_eq!(output.c19_current_a, recomputed.current_a);
            count += 1;
        }
    }
    assert_eq!(count, 96);
}

#[test]
fn invalid_panel_position_leaves_both_states_unchanged() {
    let fixture = fixture();
    let case = &fixture["cases"][0];
    let mut state = state(&case["initial"]);
    let before = state;
    let error = solve_panel_boundary(
        &mut state,
        params(&case["parameters"]),
        PanelBoundary {
            c2_right_v: 0.1,
            r21_lower_ohm: 0.0,
            dt_s: n(&case["dt_s"]),
            tip_load_ohm: Some(32.0),
            ring_load_ohm: Some(32.0),
        },
        SolverBudget::default(),
    )
    .unwrap_err();
    assert_eq!(error, StepError::InvalidInput);
    assert_eq!(state, before);
}
