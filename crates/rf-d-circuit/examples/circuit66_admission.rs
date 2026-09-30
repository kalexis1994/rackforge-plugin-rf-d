//! Offline temporal/stack/control admission probes; no change to audio stepping.
#[allow(dead_code)]
#[path = "bench_ladder_recovery_output.rs"]
mod lab;

use rf_d_circuit::{circuit66, cutoff_ladder_output, SolverBudget};
use serde_json::{json, Value};

#[cfg(all(target_os = "windows", target_arch = "x86_64"))]
#[path = "support/windows_stack.rs"]
mod windows_stack;

fn main() {
    let result = if std::env::args().any(|v| v == "--stack") {
        stack_grid()
    } else {
        temporal_grid()
    };
    match result {
        Ok(report) => {
            println!("{}", serde_json::to_string_pretty(&report).unwrap());
            if report["passed"] != true {
                std::process::exit(1);
            }
        }
        Err(error) => {
            println!("{}", json!({"passed":false,"error":error}));
            std::process::exit(1);
        }
    }
}

#[cfg(not(all(target_os = "windows", target_arch = "x86_64")))]
fn stack_grid() -> Result<Value, String> {
    Err("Stack region probe requires Windows x86_64".into())
}

#[cfg(all(target_os = "windows", target_arch = "x86_64"))]
fn stack_grid() -> Result<Value, String> {
    use windows_stack::{snapshot, Snapshot};
    struct Run {
        before: Snapshot,
        after_dc: Snapshot,
        after_steps: Snapshot,
        final_node: [f64; 66],
        max_kcl: f64,
        fallbacks: usize,
    }
    // A separate no-inline worker observes its own allocation. Serialization
    // happens after joining, outside the measured worker.
    #[inline(never)]
    fn worker(
        initial: Option<circuit66::State>,
        p: cutoff_ladder_output::Parameters,
    ) -> Result<Run, String> {
        let (_, c, h) = lab::lab_parameters();
        let before = snapshot()?;
        let mut state = match initial {
            Some(s) => s,
            None => circuit66::initial_state(p, c, h, lab::controlled_boundary(0, true), lab::SEED)
                .map_err(|e| format!("Worker DC: {e:?}"))?,
        };
        let after_dc = snapshot()?;
        let mut max_kcl = 0.0_f64;
        let mut fallbacks = 0;
        for sample in 0..8192 {
            if sample == 4096 {
                state.previous_node_v[1] -= 1e6;
            }
            let old = state;
            let result = circuit66::step(
                &mut state,
                p,
                c,
                h,
                lab::controlled_boundary(sample, true),
                SolverBudget::default(),
            )
            .map_err(|e| {
                assert_eq!(state, old);
                format!("Worker sample {sample}: {e:?}")
            })?;
            max_kcl = max_kcl.max(result.output.max_ladder_kcl_residual_a);
            fallbacks += usize::from(result.output.predictor_fallback);
        }
        // Include invalid-input and exhausted-budget paths in the observation.
        let old = state;
        let mut b = lab::controlled_boundary(8192, true);
        b.range_fraction_from_ground = f64::NAN;
        if circuit66::step(&mut state, p, c, h, b, SolverBudget::default()).is_ok() {
            return Err("Invalid input accepted".into());
        }
        assert_eq!(state, old);
        b = lab::controlled_boundary(8192, true);
        b.bus_v = 0.2;
        if circuit66::step(
            &mut state,
            p,
            c,
            h,
            b,
            SolverBudget {
                iterations: 1,
                line_search_halvings: 16,
            },
        )
        .is_ok()
        {
            return Err("One-iteration failure probe unexpectedly converged".into());
        }
        assert_eq!(state, old);
        let after_steps = snapshot()?;
        if max_kcl >= 1e-11 || fallbacks != 1 {
            return Err("Worker KCL or forced predictor fallback gate failed".into());
        }
        Ok(Run {
            before,
            after_dc,
            after_steps,
            final_node: state.node_v,
            max_kcl,
            fallbacks,
        })
    }
    let requested = std::env::args()
        .find_map(|s| s.strip_prefix("--stack-kib=").map(str::to_owned))
        .unwrap_or_else(|| "2048".into())
        .parse::<usize>()
        .map_err(|e| e.to_string())?;
    if !(512..=8192).contains(&requested) {
        return Err("Use a requested worker stack of 512..8192 KiB".into());
    }
    let (base, c, h) = lab::lab_parameters();
    let mut rows = Vec::new();
    for r61 in [200.0, 200000.0] {
        let p = cutoff_ladder_output::Parameters {
            r61_ohm: r61,
            ..base
        };
        let outside =
            circuit66::initial_state(p, c, h, lab::controlled_boundary(0, true), lab::SEED)
                .map_err(|e| format!("Outside-worker DC: {e:?}"))?;
        let mut reference = None;
        for dc_in_worker in [true, false] {
            let initial = if dc_in_worker { None } else { Some(outside) };
            let run = std::thread::Builder::new()
                .name("rf-d-stack-probe".into())
                .stack_size(requested * 1024)
                .spawn(move || worker(initial, p))
                .map_err(|e| e.to_string())?
                .join()
                .map_err(|_| "Worker panicked".to_string())??;
            let difference = if let Some(previous) = reference {
                run.final_node
                    .iter()
                    .zip(previous)
                    .map(|(a, b): (&f64, f64)| (a - b).abs())
                    .fold(0.0_f64, f64::max)
            } else {
                reference = Some(run.final_node);
                0.0
            };
            if difference > 1e-12 {
                return Err("Worker initialization paths differ numerically".into());
            }
            rows.push(json!({"r61_ohm":r61,"dc_in_worker":dc_in_worker,"requested_stack_bytes":requested*1024,
                "before":windows_stack::json(run.before),"after_dc":windows_stack::json(run.after_dc),
                "after_steps_and_failure_paths":windows_stack::json(run.after_steps),
                "samples":8192,"forced_predictor_fallbacks":run.fallbacks,"atomic_rejections":2,
                "max_kcl_a":run.max_kcl,"final_node_v":run.final_node.to_vec(),
                "initialization_path_max_difference_v":difference}));
        }
    }
    Ok(
        json!({"schema":"rf-d/circuit66-stack-regions/v1","passed":true,"platform":"windows-x86_64",
        "method":"separate Rust workers; read-only GetCurrentThreadStackLimits/VirtualQuery at phase boundaries",
        "precise_stack_high_water_measured":false,"audio_deadline_claim":false,"runs":rows}),
    )
}

fn smooth_boundary(t: f64, rate: usize, multitone: bool) -> cutoff_ladder_output::Boundary {
    let mut b = lab::controlled_boundary(0, true);
    let sine = |hz: f64| (2.0 * std::f64::consts::PI * hz * t).sin();
    b.bus_v = if multitone {
        0.08 * sine(100.0) + 0.015 * sine(1600.0) + 0.005 * sine(4163.0)
    } else {
        0.1 * sine(100.0)
    };
    b.panel.contour_pin16_v = 0.02 * sine(2.0);
    b.recovery.vca.second.output.output.dt_s = 1.0 / rate as f64;
    b
}

fn trace(
    initial: circuit66::State,
    p: cutoff_ladder_output::Parameters,
    rate: usize,
    multitone: bool,
) -> Result<(Vec<[f64; 87]>, Value), String> {
    let (_, c, h) = lab::lab_parameters();
    let mut state = initial;
    let count = rate / 50; // Same physical 20 ms at every rate.
    let mut samples = Vec::with_capacity(count);
    let mut max_kcl = 0.0_f64;
    let mut iterations = 0;
    let mut fallbacks = 0;
    for n in 1..=count {
        let b = smooth_boundary(n as f64 / rate as f64, rate, multitone);
        let previous = state;
        let result =
            circuit66::step(&mut state, p, c, h, b, SolverBudget::default()).map_err(|e| {
                assert_eq!(state, previous);
                format!("rate {rate}, R61 {}, sample {n}: {e:?}", p.r61_ohm)
            })?;
        max_kcl = max_kcl.max(result.output.max_ladder_kcl_residual_a);
        iterations = iterations.max(result.output.iterations);
        fallbacks += usize::from(result.output.predictor_fallback);
        let mut x = [0.0; 87];
        x[..66].copy_from_slice(&state.node_v);
        x[66..83].copy_from_slice(&state.capacitor_v);
        x[83] = state.c10_capacitor_v;
        x[84] = result.output.tail_current_a;
        x[85] = result.output.j4_hi_v;
        x[86] = result.output.j5_lo_v;
        samples.push(x);
    }
    if max_kcl >= 1e-11 {
        return Err("KCL gate failed".into());
    }
    Ok((
        samples,
        json!({"sample_rate_hz":rate,"samples":count,"max_kcl_a":max_kcl,
        "max_iterations":iterations,"fallbacks":fallbacks}),
    ))
}

fn compare(a: &[[f64; 87]], b: &[[f64; 87]]) -> Value {
    assert_eq!(b.len(), 2 * a.len());
    let mut max = [0.0_f64; 87];
    let mut power = [0.0; 87];
    for (n, x) in a.iter().enumerate() {
        let y = &b[2 * (n + 1) - 1]; // Endpoints t=(n+1)/rate, no interpolator.
        for k in 0..87 {
            let e = x[k] - y[k];
            max[k] = max[k].max(e.abs());
            power[k] += e * e;
        }
    }
    let rms = power.map(|v| (v / a.len() as f64).sqrt());
    let selected: Vec<Value> = [
        (61, "j7_v"),
        (47, "c2_right_v"),
        (49, "r21_wiper_v"),
        (62, "c18_v"),
        (83, "c10_v"),
        (84, "tail_current_a"),
    ]
    .into_iter()
    .map(|(k, name)| json!({"name":name,"max_abs_difference":max[k],"rms_difference":rms[k]}))
    .collect();
    json!({"selected":selected,"all_max_differences":max.to_vec(),"all_rms_differences":rms.to_vec(),
        "max_node_difference_v":max[..66].iter().copied().fold(0.0_f64,f64::max),
        "max_capacitor_difference_v":max[66..84].iter().copied().fold(0.0_f64,f64::max)})
}

fn temporal_grid() -> Result<Value, String> {
    let (base, c, h) = lab::lab_parameters();
    let mut cases = Vec::new();
    let mut passed = true;
    for multitone in [false, true] {
        for r61 in [200.0, 200000.0] {
            let p = cutoff_ladder_output::Parameters {
                r61_ohm: r61,
                ..base
            };
            // One DC state shared bit-for-bit across all three integrations.
            let initial = circuit66::initial_state(
                p,
                c,
                h,
                smooth_boundary(0.0, 48000, multitone),
                lab::SEED,
            )
            .map_err(|e| format!("DC R61 {r61}: {e:?}"))?;
            let (coarse, cr) = trace(initial, p, 48000, multitone)?;
            let (medium, mr) = trace(initial, p, 96000, multitone)?;
            let (fine, fr) = trace(initial, p, 192000, multitone)?;
            let low = compare(&coarse, &medium);
            let high = compare(&medium, &fine);
            let mut gates = Vec::new();
            // Fixed before measuring: decrease in max and RMS for the three
            // audio/output nodes. Ratios describe Euler's error, not fidelity.
            for k in 0..3 {
                let a = &low["selected"][k];
                let b = &high["selected"][k];
                let max_ratio = a["max_abs_difference"].as_f64().unwrap()
                    / b["max_abs_difference"].as_f64().unwrap();
                let rms_ratio =
                    a["rms_difference"].as_f64().unwrap() / b["rms_difference"].as_f64().unwrap();
                let ok = max_ratio > 1.0 && rms_ratio > 1.0;
                passed &= ok;
                gates.push(json!({"node":a["name"],"passed":ok,"max_error_ratio":max_ratio,"rms_error_ratio":rms_ratio}));
            }
            cases.push(
                json!({"r61_ohm":r61,"multitone":multitone,"runs":[cr,mr,fr],
                "coarse_to_medium":low,"medium_to_fine":high,"gates":gates}),
            );
        }
    }
    let report = json!({"schema":"rf-d/circuit66-temporal-convergence/v1","duration_s":0.02,
        "rates_hz":[48000,96000,192000],"total_steps":26880,"passed":passed,
        "method":"implicit Euler, same DC and smooth electrical functions; aligned endpoints",
        "audio_fidelity_claim":false,"cases":cases});
    if !passed {
        eprintln!("Temporal decrease gate failed; full report follows.");
    }
    Ok(report)
}
