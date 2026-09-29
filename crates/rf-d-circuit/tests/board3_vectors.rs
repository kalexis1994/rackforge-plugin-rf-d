use rf_d_circuit::{
    initial_state, solve_input_port, step, Parameters, SolverBudget, State, StepError, NODE_NAMES,
};
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
fn solves_frozen_dc_initial_states() {
    let fixture = fixture();
    for case in fixture["cases"].as_array().unwrap() {
        let state = initial_state(parameters(&case["parameters"]))
            .unwrap_or_else(|e| panic!("{} DC initialization: {e:?}", case["id"]));
        let expected_nodes = nodes(&case["initial"]["node_v"]);
        let expected_caps = capacitors(&case["initial"]["capacitor_v"]);
        for (i, expected) in expected_nodes.iter().enumerate() {
            assert!(
                (state.node_v[i] - expected).abs() < 1e-8,
                "{} DC node {}",
                case["id"],
                NODE_NAMES[i]
            );
        }
        for (i, expected) in expected_caps.iter().enumerate() {
            assert!(
                (state.capacitor_v[i] - expected).abs() < 1e-8,
                "{} DC capacitor {}",
                case["id"],
                i
            );
        }
    }
}

#[test]
fn dynamic_c19_port_derivative_matches_symmetric_perturbation() {
    let fixture = fixture();
    for case in fixture["cases"].as_array().unwrap() {
        let p = parameters(&case["parameters"]);
        let steps = case["steps"].as_array().unwrap();
        for index in [0usize, 20, 32, 40] {
            let previous = if index == 0 {
                &case["initial"]
            } else {
                &steps[index - 1]
            };
            let state = State {
                node_v: nodes(&previous["node_v"]),
                capacitor_v: capacitors(&previous["capacitor_v"]),
            };
            let before = state;
            let v = number(&steps[index]["pin7_v"]);
            let dt = number(&case["dt_s"]);
            let tip = optional_number(&case["tip_load_ohm"]);
            let ring = optional_number(&case["ring_load_ohm"]);
            let evaluate = |input: f64| {
                solve_input_port(&state, p, input, dt, tip, ring, SolverBudget::default())
                    .unwrap_or_else(|e| panic!("{} port {index}: {e:?}", case["id"]))
            };
            let nominal = evaluate(v);
            let h = 1e-5;
            let finite_difference =
                (evaluate(v + h).current_a - evaluate(v - h).current_a) / (2.0 * h);
            assert!(
                (nominal.conductance_s - finite_difference).abs()
                    < 1e-9 + 1e-5 * finite_difference.abs(),
                "{} port {index}: {} vs {finite_difference}",
                case["id"],
                nominal.conductance_s
            );
            let expected_current =
                2.5e-6 / dt * (nominal.next_state.capacitor_v[0] - state.capacitor_v[0]);
            assert!((nominal.current_a - expected_current).abs() < 1e-15);
            assert!(
                (nominal.next_state.node_v[11] - number(&steps[index]["node_v"][11])).abs() < 1e-6
            );
            assert!(nominal.diagnostics.max_kcl_residual_a < 1e-10);
            assert_eq!(state, before);
        }
    }
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
        let p = parameters(&case["parameters"]);
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
    let p = parameters(&case["parameters"]);
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
