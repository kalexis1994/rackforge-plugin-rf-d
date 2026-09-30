#[allow(dead_code)]
#[path = "../examples/circuit71_port_admission.rs"]
mod admission;
use rf_d_circuit::{circuit71 as joint, loudness_follower, SolverBudget, StepError};
use serde_json::Value;

#[test]
fn both_loaded_port_tangents_and_all_node_gradients_match_independent_fd() {
    let report = admission::run().unwrap();
    assert_eq!(report["passed"], true, "{report}");
}

#[test]
fn invalid_port_and_trial_solves_cannot_change_the_incoming_state() {
    let fixture: Value = serde_json::from_str(include_str!(
        "../../../evidence/circuit71_port_vectors.json"
    ))
    .unwrap();
    let case = fixture["cases"]
        .as_array()
        .unwrap()
        .iter()
        .find(|v| v["mode"] == "transient")
        .unwrap();
    let previous = admission::old_state(case).unwrap();
    let old = previous;
    let (p, c, h) = admission::support::lab::lab_parameters();
    let f = loudness_follower::Parameters::default();
    let seed = std::array::from_fn(|i| admission::support::n(&case["node_v"][i]));
    let mut b = admission::support::boundary(
        admission::support::n(&case["c2_v"]),
        0.01,
        admission::support::n(&case["bus_v"]),
    );
    b.reset_base_v = f64::NAN;
    assert_eq!(
        joint::solve_port(
            seed,
            Some(&previous),
            p,
            c,
            h,
            f,
            b,
            SolverBudget::default()
        )
        .unwrap_err(),
        StepError::InvalidInput
    );
    assert_eq!(previous, old);
    b.reset_base_v = 0.01;
    b.c2_v = 9.3;
    assert!(joint::solve_port(
        seed,
        Some(&previous),
        p,
        c,
        h,
        f,
        b,
        SolverBudget {
            iterations: 1,
            line_search_halvings: 1
        }
    )
    .is_err());
    assert_eq!(previous, old);
}
