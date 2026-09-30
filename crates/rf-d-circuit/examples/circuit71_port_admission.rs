//! Offline full-chain admittance admission; caller history stays immutable.
#[allow(dead_code)]
#[path = "circuit71_admission.rs"]
pub(crate) mod support;
use rf_d_circuit::{
    circuit66, circuit71 as joint, cutoff_ladder_output, loudness_follower, SolverBudget,
};
use serde_json::{json, Value};
use support::n;

pub(crate) fn old_state(case: &Value) -> Option<joint::State> {
    let old = &case["old"];
    if old.is_null() {
        return None;
    }
    let chain = std::array::from_fn(|i| n(&old["node_v"][i]));
    let follower = std::array::from_fn(|i| n(&old["follower_v"][i]));
    Some(joint::State {
        chain: circuit66::State {
            node_v: chain,
            previous_node_v: chain,
            capacitor_v: std::array::from_fn(|i| n(&old["capacitor_v"][i])),
            c10_capacitor_v: n(&old["c10_v"]),
        },
        follower_v: follower,
        previous_follower_v: follower,
        c2_v: n(&old["c2_v"]),
        reset_base_v: n(&old["reset_base_v"]),
    })
}

pub(crate) fn run() -> Result<Value, String> {
    let fixture: Value = serde_json::from_str(include_str!(
        "../../../evidence/circuit71_port_vectors.json"
    ))
    .map_err(|e| e.to_string())?;
    let (base, c, h) = support::lab::lab_parameters();
    let f = loudness_follower::Parameters::default();
    let mut node_error = 0.0_f64;
    let mut current_error = 0.0_f64;
    let mut tangent_error = 0.0_f64;
    let mut gradient_error = 0.0_f64;
    let mut candidate_error = 0.0_f64;
    let mut kernel_total_us = 0.0;
    let mut kernel_max_us = 0.0_f64;
    let mut rows = Vec::new();
    for case in fixture["cases"].as_array().unwrap() {
        let p = cutoff_ladder_output::Parameters {
            r61_ohm: n(&case["r61_ohm"]),
            ..base
        };
        let b = support::boundary(
            n(&case["c2_v"]),
            n(&case["reset_base_v"]),
            n(&case["bus_v"]),
        );
        let previous = old_state(case);
        let before = previous;
        let seed = std::array::from_fn(|i| n(&case["node_v"][i]) + 0.001);
        let response = joint::solve_port(
            seed,
            previous.as_ref(),
            p,
            c,
            h,
            f,
            b,
            SolverBudget::default(),
        )
        .map_err(|e| {
            format!(
                "{} R61 {} C2 {} reset {}: {e:?}",
                case["mode"], p.r61_ohm, b.c2_v, b.reset_base_v
            )
        })?;
        assert_eq!(previous, before);
        // Quality solve is the excluded warmup. Each timed port starts from
        // the same perturbed seed and immutable incoming capacitor history.
        let mut port_total_us = 0.0;
        let mut port_max_us = 0.0_f64;
        for _ in 0..8 {
            let start = std::time::Instant::now();
            let candidate = joint::solve_port(
                std::hint::black_box(seed),
                previous.as_ref(),
                p,
                c,
                h,
                f,
                b,
                SolverBudget::default(),
            )
            .map_err(|e| format!("timed port: {e:?}"))?;
            std::hint::black_box(candidate);
            let us = start.elapsed().as_secs_f64() * 1e6;
            port_total_us += us;
            port_max_us = port_max_us.max(us);
        }
        kernel_total_us += port_total_us;
        kernel_max_us = kernel_max_us.max(port_max_us);
        for (i, v) in support::nodes(&response.next_state).iter().enumerate() {
            node_error = node_error.max((v - n(&case["node_v"][i])).abs());
            for k in 0..2 {
                gradient_error = gradient_error.max(
                    (response.node_gradient_v_per_v[i][k]
                        - n(&case["node_gradient_v_per_v"][i][k]))
                    .abs(),
                );
            }
        }
        for i in 0..2 {
            current_error =
                current_error.max((response.current_a[i] - n(&case["current_a"][i])).abs());
            for k in 0..2 {
                tangent_error = tangent_error
                    .max((response.admittance_s[i][k] - n(&case["admittance_s"][i][k])).abs());
            }
        }
        // A provisional temporal port and the normal step must publish the
        // same physical history, despite different numerical seeds/predictors.
        if let Some(mut actual) = previous {
            let result = match joint::step(&mut actual, p, c, h, f, b, SolverBudget::default()) {
                Ok(r) => r,
                Err(_) => {
                    joint::step_continued(&mut actual, p, c, h, f, b, 32, SolverBudget::default())
                        .map_err(|e| format!("candidate cross-check: {e:?}"))?
                }
            };
            for (a, z) in support::nodes(&actual)
                .iter()
                .zip(support::nodes(&response.next_state))
            {
                candidate_error = candidate_error.max((a - z).abs());
            }
            for (a, z) in actual
                .chain
                .capacitor_v
                .iter()
                .zip(response.next_state.chain.capacitor_v)
            {
                candidate_error = candidate_error.max((a - z).abs());
            }
            candidate_error = candidate_error.max(
                (actual.chain.c10_capacitor_v - response.next_state.chain.c10_capacitor_v).abs(),
            );
            candidate_error = candidate_error
                .max((result.chain.output.j7_v - response.result.chain.output.j7_v).abs());
        }
        rows.push(json!({"mode":case["mode"],"r61_ohm":p.r61_ohm,"c2_v":b.c2_v,"reset_base_v":b.reset_base_v,
            "current_a":response.current_a,"admittance_s":response.admittance_s,
            "follower_gradient":response.node_gradient_v_per_v[69],"j7_gradient":response.node_gradient_v_per_v[61],
            "kcl_a":response.result.max_physical_kcl_a,"correction_v":response.result.correction_v,
            "kernel_mean_us":port_total_us/8.0,"kernel_max_us":port_max_us}));
    }
    let gates = &fixture["gates"];
    let passed = fixture["passed"] == true
        && node_error < n(&gates["node_v"])
        && current_error < n(&gates["current_a"])
        && tangent_error < n(&gates["admittance_s"])
        && gradient_error < n(&gates["node_gradient_v_per_v"])
        && candidate_error < n(&gates["node_v"]);
    Ok(
        json!({"schema":"rf-d/circuit71-port-native/v1","passed":passed,"cases":rows,"gates":gates,
        "max_node_error_v":node_error,"max_current_error_a":current_error,"max_admittance_error_s":tangent_error,
        "max_node_gradient_error_v_per_v":gradient_error,"max_candidate_vs_step_error_v":candidate_error,
        "kernel_mean_us":kernel_total_us/(36.0*8.0),"kernel_max_us":kernel_max_us,
        "warmups_per_case":1,"measured_solves_per_case":8,
        "timing_scope":"loaded port solve and two tangents; JSON and comparisons excluded; same perturbed seed",
        "audio_admitted":false,"physical_contour_switching_admitted":false,
        "scope":"DC and one implicit-Euler step; two source tangents; fixed incoming histories"}),
    )
}

fn main() {
    let report = run().unwrap_or_else(|e| json!({"passed":false,"error":e}));
    println!("{}", serde_json::to_string_pretty(&report).unwrap());
    if report["passed"] != true {
        std::process::exit(1);
    }
}
