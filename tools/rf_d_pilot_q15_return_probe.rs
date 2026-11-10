//! Reproducible monolithic and condensed Q15/CR6 comparisons.
pub use rf_d_circuit::StepError;
#[path = "rf_d_pilot_contour_ports.rs"]
mod contour_ports;
#[path = "latch_charge_driver.rs"]
mod latch_charge_driver;
use latch_charge_driver as latch_charge;
#[path = "../crates/rf-d-circuit/src/prepared_volume_residual.rs"]
mod original;
#[path = "rf_d_pilot_q15_return.rs"]
mod q15;
#[path = "rf_d_reduced_engine_lu.rs"]
mod reduced_lu;

use q15::{Drive, State, B};
use reduced_lu::{maximum, Lu};
use std::{
    hint::black_box,
    io::{Read, Write},
    time::Instant,
};

const NODES: [usize; 7] = [27, 28, 0, 1, 3, 2, 4];
type Values = [f64; 7];
type Row = [f64; 11];

fn unpack(x: Values) -> State {
    State {
        q15: [x[0], x[1]],
        volume: std::array::from_fn(|i| x[i + 2]),
    }
}

fn pack(s: State) -> Values {
    [
        s.q15[0],
        s.q15[1],
        s.volume[0],
        s.volume[1],
        s.volume[2],
        s.volume[3],
        s.volume[4],
    ]
}

fn drive([c2, vca_base, q25_base, q25_collector, cr8_anode]: [f64; 5]) -> Drive {
    Drive {
        c2,
        vca_base,
        q25_base,
        q25_collector,
        cr8_anode,
    }
}

fn oracle_stage(
    old: State,
    state: State,
    u: Drive,
) -> Result<(original::Stamp<true>, [f64; 2], [[f64; 2]; 2]), StepError> {
    let mut nodes = [0.; original::N];
    // These are fixed, unused rows of the full stamp. Keep the PNP Q16
    // terminals at its rail so its unused junctions stay in domain.
    nodes[6] = 9.3;
    nodes[7] = 9.3;
    for (node, value) in NODES.into_iter().zip(pack(state)) {
        nodes[node] = value;
    }
    for (node, value) in [
        (5, u.c2),
        (29, u.vca_base),
        (25, u.q25_base),
        (26, u.q25_collector),
        (24, u.cr8_anode),
    ] {
        nodes[node] = value;
    }
    let stamp = original::linearize::<true>(nodes, [0.; original::N], 0., true, false)?;
    let (charge, mass) =
        latch_charge_driver::terminal(old.q15.map(|v| (v, 0.)), state.q15.map(|v| (v, 0.)))?;
    Ok((stamp, charge, mass))
}

fn oracle(old: State, u: [Drive; 2], h: Option<f64>) -> Result<[State; 2], StepError> {
    const SIZE: usize = 14;
    let inv = h.map_or(0., |h| h.recip());
    let evaluate = |x: [Values; 2]| {
        let stages = [
            oracle_stage(old, unpack(x[0]), u[0])?,
            oracle_stage(old, unpack(x[1]), u[1])?,
        ];
        let residual: [f64; SIZE] = std::array::from_fn(|k| {
            let (i, r) = (k / 7, k % 7);
            let dynamic = if r < 2 {
                inv * (B[i][0] * stages[0].1[r] + B[i][1] * stages[1].1[r])
            } else {
                0.
            };
            stages[i].0.dc[NODES[r]] + dynamic
        });
        let jacobian = std::array::from_fn(|k| {
            let (i, r) = (k / 7, k % 7);
            std::array::from_fn(|l| {
                let (j, c) = (l / 7, l % 7);
                let dc = if i == j {
                    stages[i].0.jacobian[NODES[r]][NODES[c]]
                } else {
                    0.
                };
                if r < 2 && c < 2 {
                    dc + inv * B[i][j] * stages[j].2[r][c]
                } else {
                    dc
                }
            })
        });
        Ok::<_, StepError>((residual, jacobian))
    };
    let mut x = [pack(old); 2];
    let mut trial = evaluate(x)?;
    for _ in 0..20 {
        let (residual, jacobian) = trial;
        let change = Lu::factor(jacobian)?.solve(residual)?;
        let error = maximum(&residual);
        if error <= 2e-15 && maximum(&change) <= 2e-12 {
            return Ok(x.map(unpack));
        }
        let mut accepted = None;
        for half in 0..16 {
            let factor = 0.5_f64.powi(half);
            let next = std::array::from_fn(|i| {
                std::array::from_fn(|r| x[i][r] - factor * change[i * 7 + r])
            });
            if let Ok(result) = evaluate(next) {
                if maximum(&result.0) < error {
                    accepted = Some((next, result));
                    break;
                }
            }
        }
        (x, trial) = accepted.ok_or(StepError::NoDecrease)?;
    }
    Err(StepError::IterationBudget)
}

fn report(initial: State, state: State, drive: Drive) -> Result<Row, StepError> {
    let x = pack(state);
    let diode =
        1e-8 * ((state.volume[4] - state.q15[0]) / (1.5 * latch_charge_driver::VT)).exp_m1();
    let r59 = (state.volume[2] - drive.vca_base) / 68_000.;
    let (q, _) =
        latch_charge_driver::terminal(initial.q15.map(|v| (v, 0.)), state.q15.map(|v| (v, 0.)))?;
    Ok([
        x[0], x[1], x[2], x[3], x[4], x[5], x[6], diode, r59, q[0], q[1],
    ])
}

fn audit(old: State, state: State, drive: Drive) -> Result<[f64; 5], StepError> {
    let reduced = q15::stage(old, state, drive)?;
    let (full, charge, mass) = oracle_stage(old, state, drive)?;
    let j = |r: usize, c: usize| full.jacobian[NODES[r]][NODES[c]];
    let follower = Lu::<5>::factor(std::array::from_fn(|i| {
        std::array::from_fn(|k| j(i + 2, k + 2))
    }))?;
    let mut slope_error = 0_f64;
    for c in 0..2 {
        let lift = follower.solve(std::array::from_fn(|i| j(i + 2, c)))?;
        for r in 0..2 {
            let cross = (0..5).map(|k| j(r, k + 2) * lift[k]).sum::<f64>();
            slope_error = slope_error.max((reduced.jacobian[r][c] - (j(r, c) - cross)).abs());
        }
    }
    Ok([
        (0..2)
            .map(|i| (reduced.current[i] - full.dc[NODES[i]]).abs())
            .fold(0., f64::max),
        slope_error,
        (0..2)
            .map(|i| (reduced.charge[i] - charge[i]).abs())
            .fold(0., f64::max),
        (0..2)
            .flat_map(|i| (0..2).map(move |k| (i, k)))
            .map(|(i, k)| (reduced.mass[i][k] - mass[i][k]).abs())
            .fold(0., f64::max),
        (2..7).map(|i| full.dc[NODES[i]].abs()).fold(0., f64::max),
    ])
}

fn run(
    initial: State,
    inputs: &[[Drive; 2]],
    h: f64,
    condensed: bool,
    mut emit: impl FnMut(State, [State; 2], [Drive; 2]) -> Result<(), StepError>,
) -> Result<State, String> {
    let mut history = initial;
    for (i, &input) in inputs.iter().enumerate() {
        let solve = if condensed { q15::step } else { oracle };
        let stages = solve(history, input, Some(h)).map_err(|e| format!("step {i}: {e:?}"))?;
        emit(history, stages, input).map_err(|e| format!("readout {i}: {e:?}"))?;
        history = stages[1];
    }
    Ok(history)
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let mut args = std::env::args().skip(1);
    let mode = args.next().ok_or("mode")?;
    let rate: f64 = args.next().ok_or("sample rate")?.parse()?;
    let mut raw = Vec::new();
    std::io::stdin().read_to_end(&mut raw)?;
    let data = raw
        .chunks_exact(8)
        .map(|x| f64::from_le_bytes(x.try_into().unwrap()))
        .collect::<Vec<_>>();
    assert_eq!(raw.len(), data.len() * 8);
    assert!(data.len() >= 22 && (data.len() - 12) % 10 == 0 && data.iter().all(|x| x.is_finite()));
    let seed = unpack(data[..7].try_into()?);
    let dc = drive(data[7..12].try_into()?);
    let initial = oracle(seed, [dc; 2], None).map_err(|e| format!("DC: {e:?}"))?[1];
    let inputs = data[12..]
        .chunks_exact(10)
        .map(|row| {
            [
                drive(row[..5].try_into().unwrap()),
                drive(row[5..].try_into().unwrap()),
            ]
        })
        .collect::<Vec<_>>();
    if mode == "bench" {
        let mut times = [0; 100];
        for elapsed in &mut times {
            let start = Instant::now();
            black_box(run(
                black_box(initial),
                black_box(&inputs),
                rate.recip(),
                true,
                |_, _, _| Ok(()),
            )?);
            *elapsed = start.elapsed().as_nanos();
        }
        times.sort_unstable();
        println!("{},{},{},{}", times.len(), times[50], times[98], times[99]);
        return Ok(());
    }
    if mode == "audit" {
        let mut peak = [0_f64; 5];
        run(
            initial,
            &inputs,
            rate.recip(),
            true,
            |old, stages, input| {
                for i in 0..2 {
                    for (maximum, value) in peak.iter_mut().zip(audit(old, stages[i], input[i])?) {
                        *maximum = maximum.max(value);
                    }
                }
                Ok(())
            },
        )?;
        println!(
            "{:.17e},{:.17e},{:.17e},{:.17e},{:.17e}",
            peak[0], peak[1], peak[2], peak[3], peak[4]
        );
        return Ok(());
    }
    assert!(mode == "oracle" || mode == "split");
    let mut rows = Vec::with_capacity(2 * inputs.len() + 1);
    rows.push(report(initial, initial, dc));
    run(
        initial,
        &inputs,
        rate.recip(),
        mode == "split",
        |_, stages, input| {
            rows.extend((0..2).map(|i| report(initial, stages[i], input[i])));
            Ok(())
        },
    )?;
    let mut out = std::io::BufWriter::new(std::io::stdout().lock());
    for row in rows {
        for value in row.map_err(|e| format!("stage report: {e:?}"))? {
            out.write_all(&value.to_le_bytes())?;
        }
    }
    out.flush()?;
    Ok(())
}
