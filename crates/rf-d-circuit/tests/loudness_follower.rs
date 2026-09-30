use rf_d_circuit::loudness_follower::{initial_guess, linearize, solve_port, Boundary, Parameters};
use rf_d_circuit::{SolverBudget, StepError};
use serde_json::Value;

fn number(v: &Value, key: &str) -> f64 {
    v[key].as_f64().unwrap()
}
fn boundary(v: &Value) -> Boundary {
    Boundary {
        c2_v: number(v, "c2_v"),
        reset_base_v: number(v, "reset_base_v"),
        supply_v: number(v, "supply_v"),
        load_conductance_s: number(v, "load_conductance_s"),
        load_reference_v: number(v, "load_reference_v"),
    }
}
fn parameters(v: &Value) -> Parameters {
    Parameters {
        is_a: number(v, "is_a"),
        beta_forward: number(v, "beta_forward"),
        beta_reverse: number(v, "beta_reverse"),
        temperature_k: number(v, "temperature_k"),
        germanium_is_a: number(v, "germanium_is_a"),
        diode_ideality: number(v, "diode_ideality"),
    }
}

#[test]
fn independent_roots_ports_tangents_and_every_jacobian_column() {
    let fixture: Value = serde_json::from_str(include_str!(
        "../../../evidence/loudness_follower_vectors.json"
    ))
    .unwrap();
    let mut worst_node = 0.0_f64;
    let mut worst_current = 0.0_f64;
    let mut worst_tangent = 0.0_f64;
    let mut worst_output_tangent = 0.0_f64;
    let cases = fixture["cases"].as_array().unwrap();
    assert_eq!(cases.len(), 60);
    for case in cases {
        let p = parameters(&case["parameters"]);
        let b = boundary(&case["boundary"]);
        let result = solve_port(initial_guess(b), p, b, SolverBudget::default()).unwrap();
        assert!(result.max_kcl_a < 1e-11);
        assert!(result.correction_v < 1e-8);
        for i in 0..5 {
            worst_node =
                worst_node.max((result.node_v[i] - case["node_v"][i].as_f64().unwrap()).abs());
        }
        for row in 0..3 {
            worst_current = worst_current.max(
                (result.port_current_a[row] - case["port_current_a"][row].as_f64().unwrap()).abs(),
            );
            worst_output_tangent = worst_output_tangent.max(
                (result.output_gradient_v_per_v[row]
                    - case["output_gradient_v_per_v"][row].as_f64().unwrap())
                .abs(),
            );
            for col in 0..3 {
                worst_tangent = worst_tangent.max(
                    (result.port_jacobian_s[row][col]
                        - case["port_jacobian_s"][row][col].as_f64().unwrap())
                    .abs(),
                );
            }
        }
        let (_, jac) = linearize(result.node_v, p, b).unwrap();
        for col in 0..5 {
            let mut left = result.node_v;
            let mut right = result.node_v;
            left[col] -= 1e-6;
            right[col] += 1e-6;
            let (a, _) = linearize(left, p, b).unwrap();
            let (z, _) = linearize(right, p, b).unwrap();
            for row in 0..5 {
                let fd = (z[row] - a[row]) / 2e-6;
                assert!((jac[row][col] - fd).abs() < 1e-9 + 1e-7 * fd.abs());
            }
        }
        // Deliberately noisy numerical seeds cannot become hidden calibration.
        for offset in [-0.001, 0.001] {
            let seeded = solve_port(
                result.node_v.map(|v| v + offset),
                p,
                b,
                SolverBudget::default(),
            )
            .unwrap();
            assert!((0..5).all(|i| (seeded.node_v[i] - result.node_v[i]).abs() < 1e-6));
        }
    }
    println!("60 roots: node={worst_node:e}V current={worst_current:e}A tangent={worst_tangent:e}S output_tangent={worst_output_tangent:e}");
    assert!(worst_node < number(&fixture, "node_gate_v"));
    assert!(worst_current < number(&fixture, "current_gate_a"));
    assert!(worst_tangent < number(&fixture, "tangent_gate_s"));
    assert!(worst_output_tangent < number(&fixture, "output_tangent_gate"));
}

#[test]
fn invalid_boundaries_budgets_and_failure_do_not_publish_a_state() {
    let p = Parameters::default();
    let b = Boundary {
        c2_v: 6.0,
        reset_base_v: 0.7,
        supply_v: 9.3,
        load_conductance_s: 1.0 / 68000.0,
        load_reference_v: 0.7,
    };
    let seed = initial_guess(b);
    let snapshot = seed;
    assert_eq!(
        solve_port(
            seed,
            p,
            b,
            SolverBudget {
                iterations: 1,
                line_search_halvings: 16
            }
        )
        .unwrap_err(),
        StepError::IterationBudget
    );
    assert_eq!(seed, snapshot);
    for budget in [
        SolverBudget {
            iterations: 0,
            line_search_halvings: 16,
        },
        SolverBudget {
            iterations: 33,
            line_search_halvings: 16,
        },
        SolverBudget {
            iterations: 16,
            line_search_halvings: 0,
        },
        SolverBudget {
            iterations: 16,
            line_search_halvings: 25,
        },
    ] {
        assert_eq!(
            solve_port(seed, p, b, budget).unwrap_err(),
            StepError::InvalidInput
        );
    }
    for bad in [
        Boundary {
            c2_v: f64::NAN,
            ..b
        },
        Boundary {
            load_conductance_s: -1.0,
            ..b
        },
        Boundary {
            load_reference_v: f64::INFINITY,
            ..b
        },
    ] {
        assert_eq!(
            solve_port(seed, p, bad, SolverBudget::default()).unwrap_err(),
            StepError::InvalidInput
        );
    }
    assert_eq!(
        solve_port([f64::NAN; 5], p, b, SolverBudget::default()).unwrap_err(),
        StepError::InvalidInput
    );
    assert_eq!(
        solve_port(
            seed,
            Parameters {
                beta_forward: 0.0,
                ..p
            },
            b,
            SolverBudget::default()
        )
        .unwrap_err(),
        StepError::InvalidInput
    );
}
