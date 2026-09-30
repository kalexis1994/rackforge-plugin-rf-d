use rf_d_circuit::output::OutputBoundary;
use rf_d_circuit::output_conversion::{DiodeParameters, Parameters as ConversionParameters};
use rf_d_circuit::output_conversion_c4::BoundaryC4;
use rf_d_circuit::vca1_output::{initial_state, solve_input_port, step, Boundary, NODE_NAMES};
use rf_d_circuit::vca2_output::{Boundary as SecondBoundary, Parameters as VcaParameters};
use rf_d_circuit::{Parameters as HeadphoneParameters, SolverBudget, StepError};
use serde_json::Value;

fn n(v: &Value) -> f64 {
    v.as_f64().unwrap()
}

fn fixture() -> Value {
    serde_json::from_str(include_str!("../../../evidence/vca1_output_vectors.json")).unwrap()
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

fn boundary(case: &Value, b: &Value, sw18: bool) -> Boundary {
    Boundary {
        recover_collector_v: n(&b["recover_collector_v"]),
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
    }
}

#[test]
fn joint_vca1_c6_c15_vca2_c4_c2_j7_matches_python_25_variables() {
    let fixture = fixture();
    assert_eq!(fixture["schema"], "rf-d/vca1-output-vectors/v1");
    let case = &fixture["case"];
    let (vca, conversion, headphone) = parameters(case);
    let mut state = initial_state(
        vca,
        conversion,
        headphone,
        boundary(case, &case["initial_boundary"], true),
    )
    .unwrap_or_else(|e| panic!("first VCA DC: {e:?}"));
    for (i, name) in NODE_NAMES.iter().enumerate() {
        assert_eq!(&fixture["node_order"][i], name);
        let expected = n(&case["initial"]["node_v"][i]);
        assert!(
            (state.node_v[i] - expected).abs() < 1e-6,
            "DC {name}: {} vs {expected}",
            state.node_v[i]
        );
    }
    for (i, actual) in state.second.node_v.iter().enumerate() {
        let expected = n(&case["initial"]["node_v"][i + 10]);
        assert!(
            (actual - expected).abs() < 1e-6,
            "DC second {i}: {actual} vs {expected}"
        );
    }
    for (i, actual) in state.second.downstream.node_v.iter().enumerate() {
        let expected = n(&case["initial"]["node_v"][i + 16]);
        assert!(
            (actual - expected).abs() < 1e-6,
            "DC conversion {i}: {actual} vs {expected}"
        );
    }
    for (index, row) in case["steps"].as_array().unwrap().iter().enumerate() {
        let previous = state;
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
        for (i, actual) in state.second.node_v.iter().enumerate() {
            let expected = n(&row["node_v"][i + 10]);
            assert!(
                (actual - expected).abs() < 1e-6,
                "step {index} second {i}: {actual} vs {expected}"
            );
        }
        for (i, actual) in state.second.downstream.node_v.iter().enumerate() {
            let expected = n(&row["node_v"][i + 16]);
            assert!(
                (actual - expected).abs() < 1e-6,
                "step {index} conversion {i}: {actual} vs {expected}"
            );
        }
        for (name, actual) in [
            ("c6_capacitor_v", state.c6_capacitor_v),
            ("c15_capacitor_v", state.c15_capacitor_v),
            ("c4_capacitor_v", state.second.downstream.c4_capacitor_v),
            ("c2_right_v", state.second.downstream.output.c2_right_v),
            (
                "c2_capacitor_v",
                state.second.downstream.output.c2_capacitor_v,
            ),
            (
                "r21_wiper_v",
                state.second.downstream.output.panel.r21_wiper_v,
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
            .second
            .downstream
            .output
            .panel
            .amp
            .node_v
            .iter()
            .enumerate()
        {
            assert!(
                (actual - n(&row["amp_node_v"][i])).abs() < 1e-6,
                "step {index} board3 node {i}"
            );
        }
        assert!(result.max_kcl_residual_a < 1e-10);
        let port = solve_input_port(
            &previous,
            vca,
            conversion,
            headphone,
            b,
            SolverBudget::default(),
        )
        .unwrap();
        assert_eq!(port.next_state, state);
        let expected = n(&row["upstream_port_current_a"]);
        assert!(
            (port.current_a - expected).abs() < 1e-9,
            "step {index} R2 current: {} vs {expected}",
            port.current_a
        );
        if [0usize, 6, 10].contains(&index) {
            let mut plus = b;
            let mut minus = b;
            plus.recover_collector_v += 1e-3;
            minus.recover_collector_v -= 1e-3;
            let high = solve_input_port(
                &previous,
                vca,
                conversion,
                headphone,
                plus,
                SolverBudget::default(),
            )
            .unwrap();
            let low = solve_input_port(
                &previous,
                vca,
                conversion,
                headphone,
                minus,
                SolverBudget::default(),
            )
            .unwrap();
            let fd = (high.current_a - low.current_a) / 2e-3;
            assert!(
                (port.conductance_s - fd).abs() < 2e-8 + 1e-3 * fd.abs(),
                "step {index} R2 admittance: {} vs {fd}",
                port.conductance_s
            );
        }
    }
}

#[test]
fn invalid_first_balance_preserves_every_capacitor_and_downstream_state() {
    let fixture = fixture();
    let case = &fixture["case"];
    let (vca, conversion, headphone) = parameters(case);
    let mut b = boundary(case, &case["initial_boundary"], true);
    let mut state = initial_state(vca, conversion, headphone, b).unwrap();
    let previous = state;
    b.first_balance_left_ohm = 26.0;
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
