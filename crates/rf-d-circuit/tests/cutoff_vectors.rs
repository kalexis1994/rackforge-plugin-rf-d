use rf_d_circuit::cutoff::{self, Boundary, PanelBoundary, Parameters, NODE_NAMES};
use rf_d_circuit::vca2_output::Parameters as Bjt;
use rf_d_circuit::{SolverBudget, StepError};
use serde_json::Value;
fn n(v: &Value) -> f64 {
    v.as_f64().unwrap()
}
fn optional(v: &Value) -> Option<f64> {
    v.as_f64()
}
fn panel(v: &Value) -> PanelBoundary {
    PanelBoundary {
        cutoff_fraction_from_neg10: n(&v["cutoff_fraction_from_neg10"]),
        scale_active_ohm: n(&v["scale_active_ohm"]),
        contour_pin16_v: n(&v["contour_pin16_v"]),
        external_control_v: optional(&v["external_control_v"]),
        external_source_ohm: n(&v["external_source_ohm"]),
        filter_mod_on: v["filter_mod_on"].as_bool().unwrap(),
        modulation_source_v: optional(&v["modulation_source_v"]),
        modulation_source_ohm: n(&v["modulation_source_ohm"]),
        keyboard_1_3_on: v["keyboard_1_3_on"].as_bool().unwrap(),
        keyboard_2_3_on: v["keyboard_2_3_on"].as_bool().unwrap(),
        keyboard_cv_v: optional(&v["keyboard_cv_v"]),
        keyboard_source_ohm: n(&v["keyboard_source_ohm"]),
    }
}
fn bjt(v: &Value) -> Bjt {
    Bjt {
        transistor_is_a: n(&v["is_a"]),
        beta_forward: n(&v["beta_forward"]),
        beta_reverse: n(&v["beta_reverse"]),
        temperature_k: n(&v["temperature_k"]),
    }
}

#[test]
fn both_junctions_c18_panel_and_tail_port_match_72_independent_steps() {
    let fixture: Value =
        serde_json::from_str(include_str!("../../../evidence/cutoff_native_vectors.json")).unwrap();
    assert_eq!(fixture["schema"], "rf-d/cutoff-native-vectors/v1");
    for (i, name) in NODE_NAMES.iter().enumerate() {
        assert_eq!(&fixture["node_order"][i], name);
    }
    for case in fixture["cases"].as_array().unwrap() {
        let p = Parameters {
            q26: bjt(&case["q26"]),
            q28: bjt(&case["q28"]),
        };
        let initial_boundary = Boundary {
            panel: panel(&case["initial_panel"]),
            range_fraction_from_ground: n(&case["initial_range_fraction"]),
            tail_v: n(&case["initial_tail_v"]),
            dt_s: n(&fixture["dt_s"]),
        };
        let dc = cutoff::solve_dc_port(p, initial_boundary).unwrap();
        let mut state = dc.next_state;
        for i in 0..4 {
            assert!((state.node_v[i] - n(&case["initial"]["node_v"][i])).abs() < 1e-6);
        }
        for (index, row) in case["rows"].as_array().unwrap().iter().enumerate() {
            let b = Boundary {
                panel: panel(&row["panel"]),
                range_fraction_from_ground: n(&row["range_fraction"]),
                tail_v: n(&row["tail_v"]),
                dt_s: n(&fixture["dt_s"]),
            };
            let equivalent = cutoff::reduce_panel(b.panel).unwrap();
            assert!((equivalent.voltage_v - n(&row["panel_v"])).abs() < 1e-12);
            assert!((equivalent.conductance_s - n(&row["panel_g"])).abs() < 1e-15);
            let previous = state;
            let result = cutoff::step(&mut state, p, b, SolverBudget::default())
                .unwrap_or_else(|e| panic!("{} {index}: {e:?}", case["name"]));
            for i in 0..4 {
                assert!(
                    (state.node_v[i] - n(&row["node_v"][i])).abs() < 1e-6,
                    "{} {index} {}: {} vs {}",
                    case["name"],
                    NODE_NAMES[i],
                    state.node_v[i],
                    n(&row["node_v"][i])
                );
            }
            assert!((result.current_a - n(&row["current_a"])).abs() < 1e-9);
            assert!(result.max_kcl_residual_a < 1e-11);
            if [0, 9, 19].contains(&index) {
                let high = cutoff::solve_input_port(
                    &previous,
                    p,
                    Boundary {
                        tail_v: b.tail_v + 1e-4,
                        ..b
                    },
                    SolverBudget::default(),
                )
                .unwrap();
                let low = cutoff::solve_input_port(
                    &previous,
                    p,
                    Boundary {
                        tail_v: b.tail_v - 1e-4,
                        ..b
                    },
                    SolverBudget::default(),
                )
                .unwrap();
                let fd = (high.current_a - low.current_a) / 2e-4;
                assert!((fd - result.conductance_s).abs() < 2e-8 + 1e-3 * fd.abs());
            }
        }
        let previous = state;
        assert_eq!(
            cutoff::step(
                &mut state,
                p,
                Boundary {
                    tail_v: f64::NAN,
                    ..initial_boundary
                },
                SolverBudget::default()
            )
            .unwrap_err(),
            StepError::InvalidInput
        );
        assert_eq!(state, previous);
    }
}

#[test]
fn panel_switches_require_sources_and_cutoff_budget_failures_are_atomic() {
    let bjt = Bjt {
        transistor_is_a: 1e-14,
        beta_forward: 100.0,
        beta_reverse: 5.0,
        temperature_k: 298.15,
    };
    let p = Parameters { q26: bjt, q28: bjt };
    let b = Boundary {
        panel: PanelBoundary::default(),
        range_fraction_from_ground: 0.1,
        tail_v: 2.0,
        dt_s: 1.0 / 48000.0,
    };
    assert!(cutoff::reduce_panel(PanelBoundary {
        filter_mod_on: true,
        ..b.panel
    })
    .is_err());
    assert!(cutoff::reduce_panel(PanelBoundary {
        keyboard_1_3_on: true,
        ..b.panel
    })
    .is_err());
    let mut state = cutoff::solve_dc_port(p, b).unwrap().next_state;
    let previous = state;
    let changed = Boundary {
        panel: PanelBoundary {
            contour_pin16_v: 0.3,
            ..b.panel
        },
        ..b
    };
    assert_eq!(
        cutoff::step(
            &mut state,
            p,
            changed,
            SolverBudget {
                iterations: 1,
                line_search_halvings: 16
            }
        )
        .unwrap_err(),
        StepError::IterationBudget
    );
    assert_eq!(state, previous);
}
