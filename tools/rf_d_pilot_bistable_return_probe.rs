//! Full-stamp comparison for the Q25/Q15/C4 return block.
pub use rf_d_circuit::StepError;
#[path = "rf_d_pilot_attack_cell.rs"]
mod attack_cell;
#[path = "rf_d_pilot_bistable_return.rs"]
mod bistable;
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

use bistable::{Drive, State};
use q15::B;
use reduced_lu::{maximum, Lu};
use std::{
    hint::black_box,
    io::{Read, Write},
    time::Instant,
};

const NODES: [usize; 10] = [25, 26, 27, 28, 23, 0, 1, 3, 2, 4];
const PORTS: [usize; 6] = [5, 29, 17, 24, 6, 9];
const PAIR: usize = 2 * NODES.len();
type Values = [f64; 10];
type Row = [f64; 12];
type Solve = fn(State, [Drive; 2], Option<f64>) -> Result<[State; 2], StepError>;

fn unpack(x: Values) -> State {
    State {
        nodes: std::array::from_fn(|i| x[i]),
        volume: std::array::from_fn(|i| x[i + 5]),
        attack: [0.; 2],
        decay: [0.; 3],
    }
}

fn unpack_loads(data: &[f64]) -> State {
    State {
        attack: data[10..12].try_into().unwrap(),
        decay: data[12..15].try_into().unwrap(),
        ..unpack(data[..10].try_into().unwrap())
    }
}

fn pack(s: State) -> Values {
    std::array::from_fn(|i| if i < 5 { s.nodes[i] } else { s.volume[i - 5] })
}

fn drive([c2, vca_base, x17, x24, x6, x9]: [f64; 6]) -> Drive {
    Drive {
        c2,
        vca_base,
        x17,
        x24,
        x6,
        x9,
        x14: 0.,
    }
}

fn full_stage(
    old: State,
    state: State,
    u: Drive,
) -> Result<(original::Stamp<true>, [f64; 5], [[f64; 5]; 5]), StepError> {
    let mut x = [0.; original::N];
    x[7] = 9.3; // Unused Q16 row remains in its exponential domain.
    for (node, voltage) in NODES.into_iter().zip(pack(state)) {
        x[node] = voltage;
    }
    for (node, voltage) in PORTS
        .into_iter()
        .zip([u.c2, u.vca_base, u.x17, u.x24, u.x6, u.x9])
    {
        x[node] = voltage;
    }
    let full = original::linearize::<true>(x, [0.; original::N], 0., true, false)?;
    let mut charge = [0.; 5];
    let mut mass = [[0.; 5]; 5];
    for i in [0, 2] {
        let pair = |s: State| [(s.nodes[i], 0.), (s.nodes[i + 1], 0.)];
        let (q, c) = latch_charge_driver::terminal(pair(old), pair(state))?;
        charge[i..i + 2].copy_from_slice(&q);
        mass[i][i..i + 2].copy_from_slice(&c[0]);
        mass[i + 1][i..i + 2].copy_from_slice(&c[1]);
    }
    // Original physical branch on the x23 and x25 rows.
    let dv = (state.nodes[4] - old.nodes[4]) - (state.nodes[0] - old.nodes[0]);
    for (i, sign) in [(4, 1.), (0, -1.)] {
        charge[i] += sign * 10e-9 * dv;
        mass[i][4] += sign * 10e-9;
        mass[i][0] -= sign * 10e-9;
    }
    Ok((full, charge, mass))
}

fn oracle(old: State, u: [Drive; 2], h: Option<f64>) -> Result<[State; 2], StepError> {
    let inv = h.map_or(0., |h| h.recip());
    let evaluate = |x: [Values; 2]| {
        let stage = [
            full_stage(old, unpack(x[0]), u[0])?,
            full_stage(old, unpack(x[1]), u[1])?,
        ];
        let residual: [f64; PAIR] = std::array::from_fn(|k| {
            let (i, r) = (k / 10, k % 10);
            let dynamic = if r < 5 {
                inv * (B[i][0] * stage[0].1[r] + B[i][1] * stage[1].1[r])
            } else {
                0.
            };
            stage[i].0.dc[NODES[r]] + dynamic
        });
        let jacobian = std::array::from_fn(|k| {
            let (i, r) = (k / 10, k % 10);
            std::array::from_fn(|l| {
                let (j, c) = (l / 10, l % 10);
                let dc = if i == j {
                    stage[i].0.jacobian[NODES[r]][NODES[c]]
                } else {
                    0.
                };
                let dynamic = if r < 5 && c < 5 {
                    inv * B[i][j] * stage[j].2[r][c]
                } else {
                    0.
                };
                dc + dynamic
            })
        });
        Ok::<_, StepError>((residual, jacobian))
    };
    let mut x = [pack(old); 2];
    let mut trial = evaluate(x)?;
    for _ in 0..20 {
        let (residual, jacobian) = trial;
        let direction = Lu::factor(jacobian)?.solve(residual)?;
        let error = maximum(&residual);
        if error <= 2e-13 && maximum(&direction) <= 2e-9 {
            return Ok(x.map(unpack));
        }
        let mut accepted = None;
        for half in 0..16 {
            let scale = 0.5_f64.powi(half);
            let next = std::array::from_fn(|i| {
                std::array::from_fn(|k| x[i][k] - scale * direction[10 * i + k])
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

fn row(state: State, u: Drive) -> Row {
    let x = pack(state);
    let cr6 = 1e-8 * ((x[9] - x[2]) / (1.5 * latch_charge_driver::VT)).exp_m1();
    let r59 = (x[7] - u.vca_base) / 68_000.;
    std::array::from_fn(|i| match i {
        10 => cr6,
        11 => r59,
        _ => x[i],
    })
}

fn drive_with_sustain(row: &[f64]) -> Drive {
    Drive {
        x14: row[6],
        ..drive(row[..6].try_into().unwrap())
    }
}

fn load_row(state: State, u: Drive) -> [f64; 8] {
    let [x6, x8] = state.attack;
    let [x9, x10, x11] = state.decay;
    [
        x6,
        x8,
        x9,
        x10,
        x11,
        (state.nodes[1] - x6) / 3300.,
        (x8 - u.c2) / 1000.,
        (u.c2 - x11) / 10_000.,
    ]
}

fn run(
    mut state: State,
    inputs: &[[Drive; 2]],
    h: f64,
    solve: Solve,
    mut emit: impl FnMut([State; 2], [Drive; 2]),
) -> Result<State, String> {
    for (i, &drive) in inputs.iter().enumerate() {
        let stages = solve(state, drive, Some(h)).map_err(|e| format!("step {i}: {e:?}"))?;
        emit(stages, drive);
        state = stages[1];
    }
    Ok(state)
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let mut args = std::env::args().skip(1);
    let mode = args.next().ok_or("mode")?;
    let rate: f64 = args.next().ok_or("sample rate")?.parse()?;
    let settle = args.next().is_some_and(|s| s == "dc");
    let mut raw = Vec::new();
    std::io::stdin().read_to_end(&mut raw)?;
    let data: Vec<_> = raw
        .chunks_exact(8)
        .map(|b| f64::from_le_bytes(b.try_into().unwrap()))
        .collect();
    assert_eq!(raw.len(), data.len() * 8);
    if matches!(
        mode.as_str(),
        "attack" | "loads" | "loads-seeded" | "loads-handoff" | "loads-handoff-half"
    ) {
        let seeded = mode == "loads-seeded";
        let (data, guesses) = if seeded {
            assert_eq!(data.len(), 66);
            data.split_at(36)
        } else {
            (data.as_slice(), &[][..])
        };
        assert!(guesses.iter().all(|v| v.is_finite()));
        let solve = if mode == "attack" {
            bistable::attack_step
        } else {
            bistable::loads_step
        };
        let minimum = match mode.as_str() {
            "loads-handoff" => 22,
            "loads-handoff-half" => 50,
            _ => 36,
        };
        assert!(!settle && data.len() >= minimum && (data.len() - 22) % 14 == 0);
        assert!(data.iter().all(|v| v.is_finite()));
        let start = drive_with_sustain(&data[15..22]);
        let mut seed = unpack_loads(data);
        let half = mode == "loads-handoff-half";
        if mode == "loads-handoff" || half {
            seed = bistable::handoff_readout(seed, start).map_err(|e| format!("handoff: {e:?}"))?;
        }
        let inputs: Vec<_> = data[22..]
            .chunks_exact(14)
            .map(|r| [drive_with_sustain(&r[..7]), drive_with_sustain(&r[7..])])
            .collect();
        let combine = |state, u| row(state, u).into_iter().chain(load_row(state, u));
        let mut values = Vec::with_capacity(20 * (1 + 2 * inputs.len()));
        values.extend(combine(seed, start));
        let mut emit = |stages: [State; 2], drives: [Drive; 2]| {
            for i in 0..2 {
                values.extend(combine(stages[i], drives[i]));
            }
        };
        if seeded {
            let initial = [unpack_loads(&guesses[..15]), unpack_loads(&guesses[15..])];
            let stages = bistable::seeded_loads_step(seed, initial, inputs[0], rate.recip())
                .map_err(|e| format!("step 0: {e:?}"))?;
            emit(stages, inputs[0]);
        } else if half {
            let (first, rest) = inputs.split_at(2);
            let state = run(seed, first, 0.5 / rate, solve, &mut emit)?;
            run(state, rest, rate.recip(), solve, emit)?;
        } else {
            run(seed, &inputs, rate.recip(), solve, emit)?;
        }
        let mut out = std::io::BufWriter::new(std::io::stdout().lock());
        for value in values {
            out.write_all(&value.to_le_bytes())?;
        }
        out.flush()?;
        return Ok(());
    }
    assert!(data.len() >= 28 && (data.len() - 16) % 12 == 0 && data.iter().all(|v| v.is_finite()));
    let mut seed = unpack(data[..10].try_into()?);
    let start = drive(data[10..16].try_into()?);
    if settle {
        seed = oracle(seed, [start; 2], None).map_err(|e| format!("DC: {e:?}"))?[1];
    }
    let inputs: Vec<_> = data[16..]
        .chunks_exact(12)
        .map(|row| {
            [
                drive(row[..6].try_into().unwrap()),
                drive(row[6..].try_into().unwrap()),
            ]
        })
        .collect();
    if mode == "bench" || mode == "bench-plate" {
        let paired = mode == "bench-plate";
        let mut times = [[0; 100]; 2];
        for i in 0..100 {
            for candidate in [paired && i % 2 == 1, paired && i % 2 == 0]
                .into_iter()
                .take(if paired { 2 } else { 1 })
            {
                let solve = if candidate {
                    bistable::condensed_step
                } else {
                    bistable::step
                };
                let start = Instant::now();
                black_box(run(
                    black_box(seed),
                    black_box(&inputs),
                    rate.recip(),
                    solve,
                    |_, _| {},
                )?);
                times[usize::from(candidate)][i] = start.elapsed().as_nanos();
            }
        }
        for group in times.iter_mut().take(if paired { 2 } else { 1 }) {
            group.sort_unstable();
            println!("{},{},{},{}", group.len(), group[50], group[98], group[99]);
        }
        return Ok(());
    }
    let solve: Solve = match mode.as_str() {
        "split" => bistable::step,
        "plate" => bistable::condensed_step,
        "oracle" => oracle,
        _ => return Err("unsupported mode".into()),
    };
    let mut rows = Vec::with_capacity(2 * inputs.len() + 1);
    rows.push(row(seed, start));
    run(seed, &inputs, rate.recip(), solve, |stages, drives| {
        for i in 0..2 {
            rows.push(row(stages[i], drives[i]));
        }
    })?;
    let mut out = std::io::BufWriter::new(std::io::stdout().lock());
    for value in rows.into_iter().flatten() {
        out.write_all(&value.to_le_bytes())?;
    }
    out.flush()?;
    Ok(())
}
