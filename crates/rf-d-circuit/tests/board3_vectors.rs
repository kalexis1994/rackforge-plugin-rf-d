use rf_d_circuit::{step, Parameters, SolverBudget, State, StepError, NODE_NAMES};
use serde_json::Value;

fn number(v: &Value) -> f64 {
    v.as_f64().expect("finite JSON number")
}
fn optional_number(v: &Value) -> Option<f64> {
    v.as_f64()
}

fn nodes(v: &Value) -> [f64; 12] {
    let values = v.as_array().expect("node array");
    assert_eq!(values.len(), 12);
    std::array::from_fn(|i| number(&values[i]))
}

fn capacitors(v: &Value) -> [f64; 3] {
    [number(&v["C19"]), number(&v["C15"]), number(&v["C21"])]
}

fn fixture() -> Value {
    serde_json::from_str(include_str!(
        "../../../evidence/headphone_board3_port_vectors.json"
    ))
    .expect("frozen reference JSON")
}

#[test]
fn follows_every_frozen_board3_step() {
    let fixture = fixture();
    assert_eq!(fixture["schema"], "rf-d/board3-port-vectors/v1");
    for (i, name) in NODE_NAMES.iter().enumerate() {
        assert_eq!(&fixture["node_order"][i], name);
    }
    let mut checked = 0;
    for case in fixture["cases"].as_array().unwrap() {
        let params = &case["parameters"];
        let p = Parameters {
            transistor_is_a: number(&params["transistor_is_a"]),
            beta_forward: number(&params["beta_forward"]),
            beta_reverse: number(&params["beta_reverse"]),
            temperature_k: number(&params["temperature_k"]),
            diode_is_a: number(&params["diode_model"]["is_a"]),
            diode_ideality: number(&params["diode_model"]["ideality"]),
        };
        let mut state = State {
            node_v: nodes(&case["initial"]["node_v"]),
            capacitor_v: capacitors(&case["initial"]["capacitor_v"]),
        };
        for (index, reference) in case["steps"].as_array().unwrap().iter().enumerate() {
            let diagnostics = step(
                &mut state,
                p,
                number(&reference["pin7_v"]),
                number(&case["dt_s"]),
                optional_number(&case["tip_load_ohm"]),
                optional_number(&case["ring_load_ohm"]),
                SolverBudget::default(),
            )
            .unwrap_or_else(|e| panic!("{} step {}: {e:?}", case["id"], index));
            assert!(diagnostics.max_kcl_residual_a < 1e-10);
            for (node, actual) in state.node_v.iter().enumerate() {
                let expected = number(&reference["node_v"][node]);
                assert!(
                    (actual - expected).abs() < 1e-6,
                    "{} step {} node {}: {actual} vs {expected}",
                    case["id"],
                    index,
                    NODE_NAMES[node]
                );
            }
            let expected = capacitors(&reference["capacitor_v"]);
            for (i, _) in expected.iter().enumerate() {
                assert!(
                    (state.capacitor_v[i] - expected[i]).abs() < 1e-6,
                    "{} step {} capacitor {}: {} vs {}",
                    case["id"],
                    index,
                    i,
                    state.capacitor_v[i],
                    expected[i]
                );
            }
            checked += 1;
        }
    }
    assert_eq!(checked, 192);
}

#[test]
fn invalid_input_and_budget_failure_preserve_state() {
    let fixture = fixture();
    let case = &fixture["cases"][0];
    let params = &case["parameters"];
    let p = Parameters {
        transistor_is_a: number(&params["transistor_is_a"]),
        beta_forward: number(&params["beta_forward"]),
        beta_reverse: number(&params["beta_reverse"]),
        temperature_k: number(&params["temperature_k"]),
        diode_is_a: number(&params["diode_model"]["is_a"]),
        diode_ideality: number(&params["diode_model"]["ideality"]),
    };
    let mut state = State {
        node_v: nodes(&case["initial"]["node_v"]),
        capacitor_v: capacitors(&case["initial"]["capacitor_v"]),
    };
    let before = state;
    let invalid = step(
        &mut state,
        p,
        0.0,
        0.0,
        Some(32.0),
        Some(32.0),
        SolverBudget::default(),
    );
    assert_eq!(invalid.unwrap_err(), StepError::InvalidInput);
    assert_eq!(state, before);
    let budget = step(
        &mut state,
        p,
        1.0,
        1.0 / 48000.0,
        Some(32.0),
        Some(32.0),
        SolverBudget {
            iterations: 1,
            line_search_halvings: 16,
        },
    );
    assert_eq!(budget.unwrap_err(), StepError::IterationBudget);
    assert_eq!(state, before);
}
