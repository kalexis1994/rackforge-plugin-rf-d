use rf_d_circuit::output::OutputBoundary;
use rf_d_circuit::output_conversion::{DiodeParameters, Parameters as ConversionParameters};
use rf_d_circuit::output_conversion_c4::BoundaryC4;
use rf_d_circuit::vca2_output::{
    initial_state, step, Boundary, Parameters as VcaParameters, NODE_NAMES,
};
use rf_d_circuit::{Parameters as HeadphoneParameters, SolverBudget, StepError};
use serde_json::Value;

fn n(v: &Value) -> f64 {
    v.as_f64().unwrap()
}

fn fixture() -> Value {
    serde_json::from_str(include_str!("../../../evidence/vca2_output_vectors.json")).unwrap()
}

fn parameters(case: &Value) -> (VcaParameters, ConversionParameters, HeadphoneParameters) {
    let v = &case["vca_parameters"];
    let c = &case["output_parameters"];
    let h = &case["headphone_parameters"];
    (
        VcaParameters {
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

fn boundary(case: &Value, controls: &Value, sw18: bool) -> Boundary {
    Boundary {
        q14_base_v: n(&controls["q14_base_v"]),
        q13_base_v: n(&controls["q13_base_v"]),
        q21_base_v: n(&controls["q21_base_v"]),
        first_balance_wiper_v: n(&controls["first_balance_wiper_v"]),
        second_balance_left_ohm: n(&controls["second_balance_left_ohm"]),
        minus_v: n(&controls["minus_v"]),
        output: BoundaryC4 {
            second_balance_wiper_v: 0.0,
            q12_base_v: 0.0,
            q17_base_v: 0.0,
            plus_v: n(&controls["plus_v"]),
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
    }
}

#[test]
fn joint_vca2_c4_c2_j7_matches_fifteen_variable_python() {
    let fixture = fixture();
    assert_eq!(fixture["schema"], "rf-d/vca2-output-vectors/v1");
    let case = &fixture["case"];
    let (vca, conversion, headphone) = parameters(case);
    let initial_boundary = boundary(case, &case["initial_boundary"], true);
    let mut state = initial_state(vca, conversion, headphone, initial_boundary)
        .unwrap_or_else(|e| panic!("VCA2/output DC: {e:?}"));
    for (i, name) in NODE_NAMES.iter().enumerate() {
        assert_eq!(&fixture["node_order"][i], name);
        let expected = n(&case["initial"]["node_v"][i]);
        assert!(
            (state.node_v[i] - expected).abs() < 1e-6,
            "DC {name}: {} vs {expected}",
            state.node_v[i]
        );
    }
    for (i, actual) in state.downstream.node_v.iter().enumerate() {
        let expected = n(&case["initial"]["node_v"][i + 6]);
        assert!(
            (actual - expected).abs() < 1e-6,
            "DC downstream node {i}: {actual} vs {expected}"
        );
    }
    assert!((state.downstream.c4_capacitor_v - n(&case["initial"]["c4_capacitor_v"])).abs() < 1e-6);
    for (index, row) in case["steps"].as_array().unwrap().iter().enumerate() {
        let b = boundary(case, &row["boundary"], row["sw18_on"].as_bool().unwrap());
        let result = step(
            &mut state,
            vca,
            conversion,
            headphone,
            b,
            SolverBudget::default(),
        )
        .unwrap_or_else(|e| panic!("step {index}: {e:?}"));
        for (i, actual) in state.node_v.iter().enumerate() {
            let expected = n(&row["node_v"][i]);
            assert!(
                (actual - expected).abs() < 1e-6,
                "step {index} {}: {actual} vs {expected}",
                NODE_NAMES[i]
            );
        }
        for (i, actual) in state.downstream.node_v.iter().enumerate() {
            let expected = n(&row["node_v"][i + 6]);
            assert!(
                (actual - expected).abs() < 1e-6,
                "step {index} downstream node {i}: {actual} vs {expected}"
            );
        }
        for (name, actual) in [
            ("c4_capacitor_v", state.downstream.c4_capacitor_v),
            ("c2_right_v", state.downstream.output.c2_right_v),
            ("c2_capacitor_v", state.downstream.output.c2_capacitor_v),
            ("r21_wiper_v", state.downstream.output.panel.r21_wiper_v),
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
        for (i, actual) in state.downstream.output.panel.amp.node_v.iter().enumerate() {
            assert!((actual - n(&row["amp_node_v"][i])).abs() < 1e-6);
        }
        assert!(result.max_kcl_residual_a < 1e-10);
    }
}

#[test]
fn invalid_vca2_boundary_preserves_complete_state() {
    let fixture = fixture();
    let case = &fixture["case"];
    let (vca, conversion, headphone) = parameters(case);
    let mut b = boundary(case, &case["initial_boundary"], true);
    let mut state = initial_state(vca, conversion, headphone, b).unwrap();
    let previous = state;
    b.second_balance_left_ohm = 101.0;
    assert_eq!(
        step(
            &mut state,
            vca,
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
