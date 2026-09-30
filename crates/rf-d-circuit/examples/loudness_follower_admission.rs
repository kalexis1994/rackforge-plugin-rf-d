//! Quality and synthetic cold-solve cost; never whole-engine admission.
use rf_d_circuit::loudness_follower::{initial_guess, solve_port, Boundary, Parameters};
use rf_d_circuit::SolverBudget;
use serde_json::{json, Value};
use std::hint::black_box;
use std::time::Instant;

fn number(v: &Value, key: &str) -> f64 {
    v[key].as_f64().unwrap()
}

fn main() {
    let reference: Value = serde_json::from_str(include_str!(
        "../../../evidence/loudness_follower_vectors.json"
    ))
    .unwrap();
    let mut specs = Vec::new();
    let mut errors = Vec::new();
    let mut worst = [0.0_f64; 4];
    let mut kcl = 0.0_f64;
    let mut correction = 0.0_f64;
    let mut iterations = 0;
    for case in reference["cases"].as_array().unwrap() {
        let pv = &case["parameters"];
        let bv = &case["boundary"];
        let p = Parameters {
            is_a: number(pv, "is_a"),
            beta_forward: number(pv, "beta_forward"),
            beta_reverse: number(pv, "beta_reverse"),
            temperature_k: number(pv, "temperature_k"),
            germanium_is_a: number(pv, "germanium_is_a"),
            diode_ideality: number(pv, "diode_ideality"),
        };
        let b = Boundary {
            c2_v: number(bv, "c2_v"),
            reset_base_v: number(bv, "reset_base_v"),
            supply_v: number(bv, "supply_v"),
            load_conductance_s: number(bv, "load_conductance_s"),
            load_reference_v: number(bv, "load_reference_v"),
        };
        specs.push((p, b));
        match solve_port(initial_guess(b), p, b, SolverBudget::default()) {
            Err(e) => errors.push(format!("{e:?}")),
            Ok(result) => {
                kcl = kcl.max(result.max_kcl_a);
                correction = correction.max(result.correction_v);
                iterations = iterations.max(result.iterations);
                for row in 0..5 {
                    worst[0] = worst[0]
                        .max((result.node_v[row] - case["node_v"][row].as_f64().unwrap()).abs());
                }
                for row in 0..3 {
                    worst[1] = worst[1].max(
                        (result.port_current_a[row]
                            - case["port_current_a"][row].as_f64().unwrap())
                        .abs(),
                    );
                    worst[3] = worst[3].max(
                        (result.output_gradient_v_per_v[row]
                            - case["output_gradient_v_per_v"][row].as_f64().unwrap())
                        .abs(),
                    );
                    for col in 0..3 {
                        worst[2] = worst[2].max(
                            (result.port_jacobian_s[row][col]
                                - case["port_jacobian_s"][row][col].as_f64().unwrap())
                            .abs(),
                        );
                    }
                }
            }
        }
    }
    let mut block_us = [0.0_f64; 64];
    let mut clock_failures = 0;
    for block in 0..72 {
        let start = Instant::now();
        for sample in 0..64 {
            let (p, b) = specs[(block * 64 + sample) % specs.len()];
            if black_box(solve_port(
                black_box(initial_guess(b)),
                p,
                b,
                SolverBudget::default(),
            ))
            .is_err()
            {
                clock_failures += 1;
            }
        }
        let us = start.elapsed().as_secs_f64() * 1e6;
        if block >= 8 {
            block_us[block - 8] = us;
        }
    }
    let passed = errors.is_empty()
        && clock_failures == 0
        && kcl < 1e-11
        && correction < 1e-8
        && worst[0] < number(&reference, "node_gate_v")
        && worst[1] < number(&reference, "current_gate_a")
        && worst[2] < number(&reference, "tangent_gate_s")
        && worst[3] < number(&reference, "output_tangent_gate");
    println!(
        "{}",
        json!({"passed":passed, "cases":specs.len(), "errors":errors,
        "max_node_error_v":worst[0], "max_port_current_error_a":worst[1],
        "max_port_tangent_error_s":worst[2], "max_output_tangent_error":worst[3],
        "max_kcl_a":kcl, "max_correction_v":correction, "max_iterations":iterations,
        "profile":{"kind":"synthetic 64 cold algebraic-port solves; no capacitor trajectory",
            "warm_blocks_excluded":8, "measured_blocks":64, "clock_failures":clock_failures,
            "mean_block_us":block_us.iter().sum::<f64>()/64.0,
            "worst_block_us":block_us.iter().fold(0.0_f64,|a,v|a.max(*v)),
            "samples_per_block":64}, "audio_admitted":false, "whole_engine_deadline_admitted":false})
    );
    if !passed {
        std::process::exit(1);
    }
}
