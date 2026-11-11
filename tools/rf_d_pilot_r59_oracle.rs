//! Joined 68-node audio and five-node follower, with both Radau stages closed.
use rf_d_circuit::{
    chain_charge::{State as Audio, N as AUDIO},
    loudness_follower as follower, StepError,
};
use std::io::{Read, Write};
#[path = "vco_cv_load_linear.rs"]
mod linear;
#[path = "rf_d_pilot_returns_oracle.rs"]
mod receiver;
#[cfg(pilot_r59_q15)]
#[path = "latch_charge_driver.rs"]
mod latch_charge_driver;
#[cfg(pilot_r59_q15)]
#[path = "../crates/rf-d-circuit/src/prepared_volume_residual.rs"]
mod original_volume;
#[cfg(pilot_r59_q15)]
#[path = "rf_d_pilot_q15_r59_oracle.rs"]
mod q15_oracle;
const N: usize = AUDIO + 5;
const PAIR: usize = 2 * N;
const B: [[f64; 2]; 2] = [[1.5, 0.5], [-4.5, 2.5]];
const R59: f64 = 68_000.;

#[derive(Clone, Copy)]
struct State {
    audio: Audio,
    volume: [f64; 5],
}

fn boundary(c2: f64, cathode: f64, base: f64) -> follower::Boundary {
    follower::Boundary {
        c2_v: c2,
        reset_base_v: cathode,
        supply_v: 9.3,
        load_conductance_s: 1. / R59,
        load_reference_v: base,
    }
}

fn maximum(values: &[f64]) -> f64 {
    values.iter().fold(0_f64, |m, v| m.max(v.abs()))
}

fn bias(base: f64, source: f64, cathode: f64) -> Result<[f64; 6], StepError> {
    let mut x = [0.; 6];
    let c2 = source + 1.3;
    x[..5].copy_from_slice(&follower::initial_guess(boundary(c2, cathode, base)));
    x[5] = c2;
    let stamp = |x: [f64; 6]| {
        let (r, j) = follower::linearize(
            x[..5].try_into().unwrap(),
            follower::Parameters::default(),
            boundary(x[5], cathode, base),
        )?;
        let mut residual = [0.; 6];
        let mut jacobian = [[0.; 6]; 6];
        residual[..5].copy_from_slice(&r);
        residual[5] = x[3] - source;
        for i in 0..5 {
            jacobian[i][..5].copy_from_slice(&j[i]);
        }
        jacobian[0][5] = -1. / 10_000.;
        jacobian[5][3] = 1.;
        Ok::<_, StepError>((residual, jacobian))
    };
    for _ in 0..32 {
        let (r, j) = stamp(x)?;
        let d = linear::solve_linear_sparse(j, r.map(|v| -v))?;
        if maximum(&r) <= 1e-13 && maximum(&d) <= 2e-12 {
            return Ok(x);
        }
        let mut accepted = None;
        for power in 0..24 {
            let scale = 0.5_f64.powi(power);
            let next = std::array::from_fn(|k| x[k] + scale * d[k]);
            if stamp(next).is_ok_and(|(r2, _)| maximum(&r2) < maximum(&r)) {
                accepted = Some(next);
                break;
            }
        }
        x = accepted.ok_or(StepError::NoDecrease)?;
    }
    Err(StepError::IterationBudget)
}

fn stamp(
    old: State,
    delta: [Audio; 2],
    volume: [[f64; 5]; 2],
    input: [[f64; 4]; 2],
    h: f64,
) -> Result<([State; 2], [f64; PAIR], [[f64; PAIR]; PAIR]), StepError> {
    let stages = [0, 1].map(|i| {
        let [signal, c2, cathode, filter] = input[i];
        let audio = receiver::stage(old.audio, delta[i], [signal, volume[i][3], filter], h, true)?;
        let base = audio.candidate.high[32] + audio.candidate.low[32];
        let cell = follower::linearize(
            volume[i],
            follower::Parameters::default(),
            boundary(c2, cathode, base),
        )?;
        Ok::<_, StepError>((audio, cell))
    });
    let [first, last] = stages;
    let q = [first?, last?];
    let residual = std::array::from_fn(|k| {
        let (i, row) = (k / N, k % N);
        if row < AUDIO {
            q[i].0.dc[row]
                + B[i][0] * q[0].0.charge_over_h[row]
                + B[i][1] * q[1].0.charge_over_h[row]
        } else {
            q[i].1 .0[row - AUDIO]
        }
    });
    let jacobian = std::array::from_fn(|k| {
        std::array::from_fn(|l| {
            let (i, row, j, column) = (k / N, k % N, l / N, l % N);
            if row < AUDIO && column < AUDIO {
                B[i][j] * q[j].0.mass_over_h[row][column]
                    + if i == j {
                        q[i].0.dc_jacobian[row][column]
                    } else {
                        0.
                    }
            } else if i != j {
                0.
            } else if row >= AUDIO && column >= AUDIO {
                q[i].1 .1[row - AUDIO][column - AUDIO]
            } else if (row == 32 && column == AUDIO + 3) || (row == AUDIO + 3 && column == 32) {
                -1. / R59
            } else {
                0.
            }
        })
    });
    let states = std::array::from_fn(|i| State {
        audio: q[i].0.candidate,
        volume: volume[i],
    });
    Ok((states, residual, jacobian))
}

fn step(old: State, input: [[f64; 4]; 2], h: f64) -> Result<State, StepError> {
    let mut delta = [Audio::from_nodes([0.; AUDIO]); 2];
    let mut volume = [old.volume; 2];
    for _ in 0..24 {
        let (states, r, j) = stamp(old, delta, volume, input, h)?;
        let d = linear::solve_linear_sparse(j, r.map(|v| -v))?;
        if maximum(&r) <= 1e-13 && maximum(&d) <= 2e-9 {
            return Ok(states[1]);
        }
        let mut accepted = None;
        for power in 0..24 {
            let scale = 0.5_f64.powi(power);
            let next_delta = std::array::from_fn(|i| {
                delta[i].advanced(std::array::from_fn(|k| scale * d[i * N + k]))
            });
            let next_volume = std::array::from_fn(|i| {
                std::array::from_fn(|k| volume[i][k] + scale * d[i * N + AUDIO + k])
            });
            if stamp(old, next_delta, next_volume, input, h)
                .is_ok_and(|(_, r2, _)| maximum(&r2) < maximum(&r).max(1e-13))
            {
                accepted = Some((next_delta, next_volume));
                break;
            }
        }
        (delta, volume) = accepted.ok_or(StepError::NoDecrease)?;
    }
    Err(StepError::IterationBudget)
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let mode = std::env::args().nth(1).ok_or("rate or bias")?;
    let mut raw = Vec::new();
    std::io::stdin().read_to_end(&mut raw)?;
    assert_eq!(raw.len() % 8, 0);
    let values: Vec<_> = raw
        .chunks_exact(8)
        .map(|b| f64::from_le_bytes(b.try_into().unwrap()))
        .collect();
    let mut out = std::io::BufWriter::new(std::io::stdout().lock());
    #[cfg(pilot_r59_q15)]
    if let Some(rate) = mode.strip_prefix("q15-") {
        return q15_oracle::render(&values, rate.parse()?, &mut out);
    }
    if mode == "bias" {
        assert_eq!(values.len(), 3);
        for value in bias(values[0], values[1], values[2]).map_err(|e| format!("bias: {e:?}"))? {
            out.write_all(&value.to_le_bytes())?;
        }
        return Ok(());
    }
    assert!(values.len() >= 141 && (values.len() - 141) % 8 == 0);
    let mut state = State {
        audio: Audio {
            high: values[..68].try_into()?,
            low: values[68..136].try_into()?,
        },
        volume: values[136..141].try_into()?,
    };
    let h = 1. / mode.parse::<f64>()?;
    for (i, row) in values[141..].chunks_exact(8).enumerate() {
        state = step(state, [row[..4].try_into()?, row[4..].try_into()?], h)
            .map_err(|e| format!("coupled step {i}: {e:?}"))?;
        let v = |k| state.audio.high[k] + state.audio.low[k];
        for value in [
            v(61),
            v(66),
            v(6) - v(66),
            (v(66) - 0.5 * row[4]) / 39_250.,
            (state.volume[3] - v(32)) / R59,
            (v(5) - row[7]) / 680.,
            v(32),
            v(5),
        ]
        .into_iter()
        .chain(state.volume)
        {
            out.write_all(&value.to_le_bytes())?;
        }
    }
    Ok(())
}
