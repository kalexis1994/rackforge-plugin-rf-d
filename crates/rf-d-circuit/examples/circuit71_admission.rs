//! Offline joint follower/R59/full audio-chain admission. Serialization stays outside timing.
#[allow(dead_code)]
#[path = "bench_ladder_recovery_output.rs"]
pub(crate) mod lab;

use rf_d_circuit::{circuit71 as joint, cutoff_ladder_output, loudness_follower, SolverBudget};
use serde_json::{json, Value};

pub(crate) fn n(v: &Value) -> f64 {
    v.as_f64().unwrap()
}
pub(crate) fn nodes(s: &joint::State) -> [f64; 71] {
    std::array::from_fn(|i| {
        if i < 66 {
            s.chain.node_v[i]
        } else {
            s.follower_v[i - 66]
        }
    })
}
pub(crate) fn boundary(c2: f64, reset: f64, bus: f64) -> joint::Boundary {
    let mut chain = lab::controlled_boundary(0, true);
    chain.bus_v = bus;
    joint::Boundary {
        chain,
        c2_v: c2,
        reset_base_v: reset,
        supply_v: 9.3,
    }
}

pub(crate) fn run() -> Result<Value, String> {
    let fixture: Value = serde_json::from_str(include_str!(
        "../../../evidence/circuit71_loudness_vectors.json"
    ))
    .map_err(|e| e.to_string())?;
    let (base, c, h) = lab::lab_parameters();
    let f = loudness_follower::Parameters::default();
    let mut worst_node = 0.0_f64;
    let mut worst_cap = 0.0_f64;
    let mut worst_jack = 0.0_f64;
    let mut worst_current = 0.0_f64;
    let mut worst_kcl = 0.0_f64;
    let mut worst_correction = 0.0_f64;
    let mut cases = Vec::new();
    for case in fixture["cases"].as_array().unwrap() {
        let p = cutoff_ladder_output::Parameters {
            r61_ohm: n(&case["r61_ohm"]),
            ..base
        };
        let reset = n(&case["reset_base_v"]);
        let seed66 = std::array::from_fn(|i| n(&case["initial"]["node_v"][i]));
        let prepared = joint::initial_state(seed66, p, c, h, f, boundary(3.2, reset, 0.0))
            .map_err(|e| format!("DC anchor: {e:?}"))?;
        let mut state = prepared.state;
        for (i, v) in state.chain.capacitor_v.iter().enumerate() {
            worst_cap = worst_cap.max((v - n(&case["initial"]["memory"]["capacitor_v"][i])).abs());
        }
        worst_cap = worst_cap
            .max((state.chain.c10_capacitor_v - n(&case["initial"]["memory"]["c10_v"])).abs());
        for (i, v) in nodes(&state).iter().enumerate() {
            worst_node = worst_node.max((v - n(&case["initial"]["node_v"][i])).abs());
        }
        for row in case["dc_rows"].as_array().unwrap() {
            let b = boundary(n(&row["c2_v"]), reset, 0.0);
            let dc = joint::initial_state(seed66, p, c, h, f, b)
                .map_err(|e| format!("DC C2 {}: {e:?}", b.c2_v))?;
            state = dc.state;
            worst_kcl = worst_kcl.max(dc.max_physical_kcl_a);
            for (i, v) in nodes(&state).iter().enumerate() {
                worst_node = worst_node.max((v - n(&row["node_v"][i])).abs());
            }
        }
        let initial = state;
        for (i, v) in initial.chain.capacitor_v.iter().enumerate() {
            worst_cap = worst_cap.max((v - n(&case["transient_initial"]["capacitor_v"][i])).abs());
        }
        worst_cap = worst_cap
            .max((initial.chain.c10_capacitor_v - n(&case["transient_initial"]["c10_v"])).abs());
        let mut rejections = Vec::new();
        let mut fallback_count = 0;
        let mut total_us = 0.0;
        let mut max_sample_us = 0.0_f64;
        // Warm and measure the same scene from the same incoming state. Timing
        // covers the rejected primary and continuation; JSON/formatting does not.
        for pass in 0..2 {
            state = initial;
            for row in case["rows"].as_array().unwrap() {
                let b = boundary(n(&row["c2_v"]), reset, n(&row["bus_v"]));
                let old = state;
                let start = std::time::Instant::now();
                let primary = joint::step(&mut state, p, c, h, f, b, SolverBudget::default());
                let rejected = primary.as_ref().err().copied();
                let result = match primary {
                    Ok(r) => r,
                    Err(_) => {
                        assert_eq!(state, old, "failed primary changed electrical memory");
                        joint::step_continued(
                            &mut state,
                            p,
                            c,
                            h,
                            f,
                            b,
                            32,
                            SolverBudget::default(),
                        )
                        .map_err(|e| {
                            format!(
                                "R61 {} reset {reset} sample {}: {e:?}",
                                p.r61_ohm, row["sample"]
                            )
                        })?
                    }
                };
                let elapsed_us = start.elapsed().as_secs_f64() * 1e6;
                if pass == 0 {
                    continue;
                }
                total_us += elapsed_us;
                max_sample_us = max_sample_us.max(elapsed_us);
                fallback_count += usize::from(result.chain.output.predictor_fallback);
                if let Some(error) = rejected {
                    rejections.push(json!({"sample":row["sample"],"error":format!("{error:?}"),"continuation_stages":32}));
                }
                worst_kcl = worst_kcl.max(result.max_physical_kcl_a);
                worst_correction = worst_correction.max(result.correction_v);
                for (i, v) in nodes(&state).iter().enumerate() {
                    worst_node = worst_node.max((v - n(&row["node_v"][i])).abs());
                }
                for (i, v) in state.chain.capacitor_v.iter().enumerate() {
                    worst_cap = worst_cap.max((v - n(&row["capacitor_v"][i])).abs());
                }
                worst_cap = worst_cap.max((state.chain.c10_capacitor_v - n(&row["c10_v"])).abs());
                for (key, value) in [
                    ("j7_v", result.chain.output.j7_v),
                    ("j4_hi_v", result.chain.output.j4_hi_v),
                    ("j5_lo_v", result.chain.output.j5_lo_v),
                ] {
                    worst_jack = worst_jack.max((value - n(&row["metrics"][key])).abs());
                }
                for (key, value) in [
                    ("timing_current_a", result.timing_current_a),
                    ("reset_current_a", result.reset_current_a),
                    ("r59_current_a", result.r59_current_a),
                    ("tail_current_a", result.chain.output.tail_current_a),
                ] {
                    worst_current = worst_current.max((value - n(&row["metrics"][key])).abs());
                }
            }
        }
        cases.push(json!({"r61_ohm":p.r61_ohm,"reset_base_v":reset,"steps":64,
            "block_us":total_us,"max_sample_us":max_sample_us,"predictor_fallbacks":fallback_count,
            "rejections":rejections,"final_node_v":nodes(&state).to_vec()}));
    }
    let g = &fixture["gates"];
    let passed = worst_node < n(&g["node_v"])
        && worst_cap < n(&g["capacitor_v"])
        && worst_jack < n(&g["jack_v"])
        && worst_current < n(&g["current_a"])
        && worst_kcl < n(&g["kcl_a"])
        && worst_correction < n(&g["correction_v"]);
    Ok(
        json!({"schema":"rf-d/circuit71-native/v1","passed":passed,"steps":256,"dc_targets":20,
        "max_node_error_v":worst_node,"max_capacitor_error_v":worst_cap,
        "max_jack_error_v":worst_jack,"max_current_error_a":worst_current,
        "max_physical_kcl_a":worst_kcl,"max_correction_v":worst_correction,
        "gates":g,"cases":cases,"warmup_passes":1,"measured_passes":1,"deadline_us":64e6/48000.0,
        "audio_admitted":false,"physical_contour_switching_admitted":false,
        "timing_scope":"kernel including primary rejections; no JSON; four warmed blocks only"}),
    )
}

fn main() {
    let report = run().unwrap_or_else(|e| json!({"passed":false,"error":e}));
    println!("{}", serde_json::to_string_pretty(&report).unwrap());
    if report["passed"] != true {
        std::process::exit(1);
    }
}
