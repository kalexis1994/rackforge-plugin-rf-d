//! Offline comparison trace: interleaved little-endian f64 J7, HI and LO.
//! `cargo run --release -p rf-d-circuit --example trace_output -- tmp/trace.bin`

use std::path::PathBuf;

use rf_d_circuit::output::{initial_output_state, solve_output_boundary, OutputBoundary};
use rf_d_circuit::{Parameters, SolverBudget};

fn main() {
    let path: PathBuf = std::env::args_os()
        .nth(1)
        .expect("output path argument required")
        .into();
    let p = Parameters {
        transistor_is_a: 1e-14,
        beta_forward: 160.0,
        beta_reverse: 5.0,
        temperature_k: 300.0,
        diode_is_a: 1.446_588_643_457_551_9e-9,
        diode_ideality: 1.5,
    };
    let mut state = initial_output_state(p, 5.0).expect("DC point");
    let mut trace = Vec::with_capacity(48_000);
    for sample in 0..48_000 {
        let q17 = 5.0 + 0.5 * (2.0 * std::f64::consts::PI * 100.0 * sample as f64 / 48_000.0).sin();
        let result = solve_output_boundary(
            &mut state,
            p,
            OutputBoundary {
                q17_collector_v: q17,
                r20_lower_ohm: 2500.0,
                hi_load_ohm: 10000.0,
                lo_load_ohm: 100000.0,
                sw18_on: true,
                r21_lower_ohm: 2000.0,
                tip_load_ohm: Some(32.0),
                ring_load_ohm: Some(32.0),
                dt_s: 1.0 / 48_000.0,
            },
            SolverBudget::default(),
        )
        .expect("trace step");
        trace.push([result.j7_v, result.j4_hi_v, result.j5_lo_v]);
    }
    let mut bytes = Vec::with_capacity(trace.len() * 3 * 8);
    for row in trace {
        for value in row {
            bytes.extend_from_slice(&value.to_le_bytes());
        }
    }
    std::fs::write(path, bytes).expect("write offline trace");
}
