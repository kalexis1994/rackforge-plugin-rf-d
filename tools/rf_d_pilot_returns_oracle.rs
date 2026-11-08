//! Exact nonlinear 68-node reference with both pilot boundary drives.
use rf_d_circuit::{chain_charge::{self, Parameters, State, N}, StepError};
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
        circuit, conversion, headphone, boundary,
        mixer: rf_d_circuit::mixer_on::OnMixer::new([false, true, true, true, true], [0.5; 4]).unwrap(),
    }
}

fn stamp(old: State, delta: [State; 2], u: [[f64; 3]; 2], h: f64)
    -> Result<([State; 2], [f64; M], [[f64; M]; M]), StepError>
{
    let mut q = [
        chain_charge::linearize_compensated(parameters(u[0]), [0.; 5], old, delta[0], h)?,
        chain_charge::linearize_compensated(parameters(u[1]), [0.; 5], old, delta[1], h)?,
    ];
    for i in 0..2 {
        q[i].dc[66] += (q[i].candidate.high[66] + q[i].candidate.low[66] - 0.5 * u[i][0]) / 39_250.;
        q[i].dc_jacobian[66][66] += 1. / 39_250.;
    }
    let residual = std::array::from_fn(|k| {
        let (i, r) = (k / N, k % N);
        q[i].dc[r] + B[i][0] * q[0].charge_over_h[r] + B[i][1] * q[1].charge_over_h[r]
    });
    let jac = std::array::from_fn(|k| std::array::from_fn(|l| {
        let (i, r) = (k / N, k % N);
        let (j, c) = (l / N, l % N);
        B[i][j] * q[j].mass_over_h[r][c] + if i == j { q[i].dc_jacobian[r][c] } else { 0. }
    }));
    Ok((q.each_ref().map(|item| item.candidate), residual, jac))
}

fn max(values: &[f64]) -> f64 {
    values.iter().fold(0_f64, |m, x| m.max(x.abs()))
}

fn step(old: State, first: [f64; 3], last: [f64; 3], h: f64) -> Result<State, StepError> {
    let drives = [first, last];
    let mut delta = [State::from_nodes([0.; N]); 2];
    for _ in 0..24 {
        let (nodes, residual, jac) = stamp(old, delta, drives, h)?;
        let change = linear::solve_linear_sparse(jac, residual.map(|x| -x))?;
        if max(&residual) <= 1e-13 && max(&change) <= 2e-9 {
            return Ok(nodes[1]);
        }
        let mut accepted = false;
        let mut scale = 1.;
        for _ in 0..24 {
            let trial = std::array::from_fn(|i| delta[i].advanced(
                std::array::from_fn(|k| scale * change[i * N + k])));
            if let Ok((_, r, _)) = stamp(old, trial, drives, h) {
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

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let h: f64 = std::env::args().nth(1).ok_or("sample rate")?.parse::<f64>()?.recip();
    let mut bytes = Vec::new();
    std::io::stdin().lock().read_to_end(&mut bytes)?;
    let floats: Vec<_> = bytes.chunks_exact(8).map(|b| f64::from_le_bytes(b.try_into().unwrap())).collect();
    assert_eq!(bytes.len(), floats.len() * 8);
    assert_eq!((floats.len() - 2 * N) % 6, 0);
    let mut old = State { high: floats[..N].try_into()?, low: floats[N..2 * N].try_into()? };
    let mut out = BufWriter::new(std::io::stdout().lock());
    for (i, row) in floats[2 * N..].chunks_exact(6).enumerate() {
        let last: [f64; 3] = row[3..].try_into()?;
        old = step(old, row[..3].try_into()?, last, h).map_err(|e| format!("step {i}: {e:?}"))?;
        let v = |k: usize| old.high[k] + old.low[k];
        for val in [v(61), v(66), v(6) - v(66), (v(66) - 0.5 * last[0]) / 39_250.,
                    (2. + last[1] - v(32)) / 68_000., (v(5) - v(65)) / 680.] {
            out.write_all(&val.to_le_bytes())?;
        }
    }
    out.flush()?;
    Ok(())
}
