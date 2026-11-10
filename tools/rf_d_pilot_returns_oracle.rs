//! Exact nonlinear 68-node reference with both pilot boundary drives.
use rf_d_circuit::{
    chain_charge::{self, Parameters, State, N},
    StepError,
};
use std::io::{BufWriter, Read, Write};

#[path = "../crates/rf-d-circuit/tests/support/mixer_chain_lab.rs"]
mod lab;
#[path = "vco_cv_load_linear.rs"]
mod linear;
const B: [[f64; 2]; 2] = [[1.5, 0.5], [-4.5, 2.5]];
const M: usize = 2 * N;

fn parameters(control: [f64; 3]) -> Parameters {
    let (circuit, conversion, headphone) = lab::lab_parameters();
    let mut boundary = lab::controlled_boundary(0, true);
    boundary.panel.contour_pin16_v = control[2];
    boundary.recovery.vca.loudness_v = 2. + control[1];
    Parameters {
        circuit,
        conversion,
        headphone,
        boundary,
        mixer: rf_d_circuit::mixer_on::OnMixer::new([false, true, true, true, true], [0.5; 4])
            .unwrap(),
    }
}

const TAIL: usize = 5;
const COLLECTOR: usize = 65;
const BUS: usize = 66;

fn stage(
    old: State,
    delta: State,
    u: [f64; 3],
    h: f64,
    split: bool,
) -> Result<chain_charge::Parts, StepError> {
    let control = if split { [u[0], u[1] - 2., 0.] } else { u };
    let mut q = chain_charge::linearize_compensated(parameters(control), [0.; 5], old, delta, h)?;
    q.dc[BUS] += (q.candidate.high[BUS] + q.candidate.low[BUS] - 0.5 * u[0]) / 39_250.;
    q.dc_jacobian[BUS][BUS] += 1. / 39_250.;
    if split {
        // Drive the collector end of the original R60. Keep the TAIL row and
        // its resistor, including the reaction current at the audio input.
        assert!(q.mass_over_h[COLLECTOR].iter().all(|&x| x == 0.));
        q.dc[COLLECTOR] = (q.candidate.high[COLLECTOR] - u[2]) + q.candidate.low[COLLECTOR];
        q.dc_jacobian[COLLECTOR].fill(0.);
        q.dc_jacobian[COLLECTOR][COLLECTOR] = 1.;
    }
    Ok(q)
}

fn stamp(
    old: State,
    delta: [State; 2],
    u: [[f64; 3]; 2],
    h: f64,
    split: bool,
) -> Result<([State; 2], [f64; M], [[f64; M]; M]), StepError> {
    let q = [
        stage(old, delta[0], u[0], h, split)?,
        stage(old, delta[1], u[1], h, split)?,
    ];
    let residual = std::array::from_fn(|k| {
        let (i, r) = (k / N, k % N);
        q[i].dc[r] + B[i][0] * q[0].charge_over_h[r] + B[i][1] * q[1].charge_over_h[r]
    });
    let jac = std::array::from_fn(|k| {
        std::array::from_fn(|l| {
            let (i, r) = (k / N, k % N);
            let (j, c) = (l / N, l % N);
            B[i][j] * q[j].mass_over_h[r][c] + if i == j { q[i].dc_jacobian[r][c] } else { 0. }
        })
    });
    Ok((q.each_ref().map(|item| item.candidate), residual, jac))
}

fn max(values: &[f64]) -> f64 {
    values.iter().fold(0_f64, |m, x| m.max(x.abs()))
}

fn step(
    old: State,
    first: [f64; 3],
    last: [f64; 3],
    h: f64,
    split: bool,
) -> Result<State, StepError> {
    let drives = [first, last];
    let mut delta = [State::from_nodes([0.; N]); 2];
    for _ in 0..24 {
        let (nodes, residual, jac) = stamp(old, delta, drives, h, split)?;
        let change = linear::solve_linear_sparse(jac, residual.map(|x| -x))?;
        if max(&residual) <= 1e-13 && max(&change) <= 2e-9 {
            return Ok(nodes[1]);
        }
        let mut accepted = false;
        let mut scale = 1.;
        for _ in 0..24 {
            let trial = std::array::from_fn(|i| {
                delta[i].advanced(std::array::from_fn(|k| scale * change[i * N + k]))
            });
            if let Ok((_, r, _)) = stamp(old, trial, drives, h, split) {
                if max(&r) < max(&residual).max(1e-13) {
                    delta = trial;
                    accepted = true;
                    break;
                }
            }
            scale *= 0.5;
        }
        if !accepted {
            return Err(StepError::NoDecrease);
        }
    }
    Err(StepError::IterationBudget)
}

fn settle_anchor(mut state: State, u: [f64; 3]) -> Result<State, StepError> {
    let dt = 1e-6;
    let zero = State::from_nodes([0.; N]);
    for _ in 0..24 {
        let q = stage(state, zero, u, dt, true)?;
        let change = linear::solve_linear_sparse(q.dc_jacobian, q.dc.map(|x| -x))?;
        if max(&q.dc) <= 1e-13 && max(&change) <= 2e-9 {
            return Ok(state);
        }
        let mut scale = 1.;
        let mut accepted = None;
        for _ in 0..24 {
            let trial = state.advanced(change.map(|x| scale * x));
            if let Ok(next) = stage(trial, zero, u, dt, true) {
                if max(&next.dc) < max(&q.dc) {
                    accepted = Some(trial);
                    break;
                }
            }
            scale *= 0.5;
        }
        state = accepted.ok_or(StepError::NoDecrease)?;
    }
    Err(StepError::IterationBudget)
}

fn anchor(mut old: State, target: [f64; 3]) -> Result<State, StepError> {
    let start = [0., 2., old.high[COLLECTOR] + old.low[COLLECTOR]];
    // The continuation starts at the already admitted pilot bias.
    for i in 1..=128 {
        let fraction = f64::from(i) / 128.;
        let u = std::array::from_fn(|k| start[k] + fraction * (target[k] - start[k]));
        old = settle_anchor(old, u)?;
    }
    Ok(old)
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let clock = std::env::args().nth(1).ok_or("sample rate")?;
    let split = std::env::args().nth(2).is_some_and(|mode| mode == "split");
    let mut bytes = Vec::new();
    std::io::stdin().lock().read_to_end(&mut bytes)?;
    let floats: Vec<_> = bytes
        .chunks_exact(8)
        .map(|b| f64::from_le_bytes(b.try_into().unwrap()))
        .collect();
    assert_eq!(bytes.len(), floats.len() * 8);
    assert!(floats.len() >= 2 * N);
    let mut old = State {
        high: floats[..N].try_into()?,
        low: floats[N..2 * N].try_into()?,
    };
    let mut out = BufWriter::new(std::io::stdout().lock());
    let payload = &floats[2 * N..];
    if matches!(clock.as_str(), "anchor" | "anchor-direct") {
        let target: [f64; 3] = payload.try_into()?;
        let x = if clock == "anchor" {
            anchor(old, target)
        } else {
            settle_anchor(old, target)
        }
        .map_err(|e| format!("split anchor: {e:?}"))?;
        let stamp = stage(x, State::from_nodes([0.; N]), target, 1e-6, true)
            .map_err(|e| format!("split stamp: {e:?}"))?;
        for value in x
            .high
            .into_iter()
            .chain(x.low)
            .chain(stamp.dc_jacobian.into_iter().flatten())
            .chain([max(&stamp.dc)])
        {
            out.write_all(&value.to_le_bytes())?;
        }
        out.flush()?;
        return Ok(());
    }
    let h = clock.parse::<f64>()?.recip();
    assert_eq!(payload.len() % 6, 0);
    for (i, row) in payload.chunks_exact(6).enumerate() {
        let last: [f64; 3] = row[3..].try_into()?;
        old = step(old, row[..3].try_into()?, last, h, split)
            .map_err(|e| format!("step {i}: {e:?}"))?;
        let v = |k: usize| old.high[k] + old.low[k];
        for val in [
            v(61),
            v(66),
            v(6) - v(66),
            (v(66) - 0.5 * last[0]) / 39_250.,
            ((if split { last[1] } else { 2. + last[1] }) - v(32)) / 68_000.,
            (v(TAIL) - v(COLLECTOR)) / 680.,
        ] {
            out.write_all(&val.to_le_bytes())?;
        }
    }
    out.flush()?;
    Ok(())
}
