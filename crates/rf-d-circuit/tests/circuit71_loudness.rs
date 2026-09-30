#[allow(dead_code)]
#[path = "../examples/circuit71_admission.rs"]
mod admission;
use rf_d_circuit::{circuit71 as joint, loudness_follower, SolverBudget, StepError};
use serde_json::Value;

#[test]
fn independent_71_node_dc_and_256_temporal_steps() {
    let report = admission::run().unwrap();
    assert_eq!(report["passed"], true, "{report}");
}

#[test]
fn dc_seed_limitation_and_complete_seed_recovery_remain_visible() {
    let fixture: Value = serde_json::from_str(include_str!(
        "../../../evidence/circuit71_loudness_vectors.json"
    ))
    .unwrap();
    let (p, c, h) = admission::lab::lab_parameters();
    let f = loudness_follower::Parameters::default();
    let case = &fixture["cases"][0];
    let low = &case["dc_rows"][0];
    let seed66 = std::array::from_fn(|i| admission::n(&low["node_v"][i]));
    let b = admission::boundary(0.0, 0.01, 0.0);
    assert_eq!(
        joint::initial_state(seed66, p, c, h, f, b).unwrap_err(),
        StepError::NoDecrease
    );
    let zero = &case["dc_rows"][1];
    for shift in [-0.001, 0.0, 0.001] {
        let seed = std::array::from_fn(|i| admission::n(&zero["node_v"][i]) + shift);
        let state = joint::initial_state_from_nodes(seed, p, c, h, f, b)
            .unwrap()
            .state;
        for (i, v) in admission::nodes(&state).iter().enumerate() {
            assert!((v - admission::n(&zero["node_v"][i])).abs() < 1e-6);
        }
        assert!(state.follower_v[3] < 0.0, "electrical output was clamped");
    }
}

#[test]
fn every_joint_jacobian_column_and_failure_are_checked() {
    let fixture: Value = serde_json::from_str(include_str!(
        "../../../evidence/circuit71_loudness_vectors.json"
    ))
    .unwrap();
    let (base, c, h) = admission::lab::lab_parameters();
    let f = loudness_follower::Parameters::default();
    for case in fixture["cases"].as_array().unwrap() {
        let p = rf_d_circuit::cutoff_ladder_output::Parameters {
            r61_ohm: admission::n(&case["r61_ohm"]),
            ..base
        };
        let reset = admission::n(&case["reset_base_v"]);
        let seed = std::array::from_fn(|i| admission::n(&case["initial"]["node_v"][i]));
        let mut state =
            joint::initial_state_from_nodes(seed, p, c, h, f, admission::boundary(3.2, reset, 0.0))
                .unwrap()
                .state;
        for sample in 0..64 {
            let row = &case["rows"][sample];
            let b = admission::boundary(
                admission::n(&row["c2_v"]),
                reset,
                admission::n(&row["bus_v"]),
            );
            let old = state;
            if joint::step(&mut state, p, c, h, f, b, SolverBudget::default()).is_err() {
                assert_eq!(state, old);
                joint::step_continued(&mut state, p, c, h, f, b, 32, SolverBudget::default())
                    .unwrap();
            }
            if [8, 24, 40, 48].contains(&sample) {
                let x = admission::nodes(&state);
                let (_, j) = joint::linearize(Some(&old), p, c, h, f, b, &x).unwrap();
                assert_eq!(j[32][69], -1.0 / 68000.0);
                assert_eq!(j[69][32], -1.0 / 68000.0);
                for col in 0..71 {
                    let mut plus = x;
                    let mut minus = x;
                    plus[col] += 1e-6;
                    minus[col] -= 1e-6;
                    let (rp, _) = joint::linearize(Some(&old), p, c, h, f, b, &plus).unwrap();
                    let (rm, _) = joint::linearize(Some(&old), p, c, h, f, b, &minus).unwrap();
                    for i in 0..71 {
                        let fd = (rp[i] - rm[i]) / 2e-6;
                        assert!(
                            (fd - j[i][col]).abs() < 1e-8 + 2e-5 * fd.abs(),
                            "sample {sample} J[{i},{col}] {fd} vs {}",
                            j[i][col]
                        );
                    }
                }
            }
        }
        let old = state;
        let b = admission::boundary(3.2, reset, 0.0);
        for stages in [0, 65] {
            assert_eq!(
                joint::step_continued(&mut state, p, c, h, f, b, stages, SolverBudget::default())
                    .unwrap_err(),
                StepError::InvalidInput
            );
            assert_eq!(state, old);
        }
        let jump = admission::boundary(9.3, reset, 0.0);
        let budget = SolverBudget {
            iterations: 1,
            line_search_halvings: 1,
        };
        assert!(joint::step(&mut state, p, c, h, f, jump, budget).is_err());
        assert_eq!(state, old);
        assert!(joint::step_continued(&mut state, p, c, h, f, jump, 32, budget).is_err());
        assert_eq!(state, old);
        let mut bad = b;
        bad.c2_v = f64::NAN;
        assert_eq!(
            joint::step(&mut state, p, c, h, f, bad, SolverBudget::default()).unwrap_err(),
            StepError::InvalidInput
        );
        assert_eq!(state, old);
    }
}

#[test]
fn exact_r21_constraints_survive_the_joint_network() {
    let fixture: Value = serde_json::from_str(include_str!(
        "../../../evidence/circuit71_loudness_vectors.json"
    ))
    .unwrap();
    let (p, c, h) = admission::lab::lab_parameters();
    let f = loudness_follower::Parameters::default();
    let seed = std::array::from_fn(|i| admission::n(&fixture["cases"][0]["initial"]["node_v"][i]));
    for lower in [0.0, 5000.0] {
        let mut b = admission::boundary(3.2, 0.01, 0.0);
        b.chain.recovery.vca.second.output.output.r21_lower_ohm = lower;
        let mut s = joint::initial_state_from_nodes(seed, p, c, h, f, b)
            .unwrap()
            .state;
        b.chain.bus_v = 0.001;
        let r = joint::step(&mut s, p, c, h, f, b, SolverBudget::default()).unwrap();
        assert!(r.chain.voltage_constraint_error_v < 1e-11);
        assert!(r.chain.r21_short_current_a.unwrap().is_finite());
        assert!(r.max_physical_kcl_a < 1e-11);
        if lower == 0.0 {
            assert_eq!(s.chain.node_v[49], 0.0);
        } else {
            assert!((s.chain.node_v[48] - s.chain.node_v[49]).abs() < 1e-11);
        }
    }
}
