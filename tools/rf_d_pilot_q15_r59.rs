//! Trapezoidal Q15 charge with an endpoint closure through CR6 and R59.
use crate::{
    fast_r59,
    latch_charge::terminal,
    q15,
    reduced_lu::{maximum, Lu},
    StepError,
};

const TWO_OVER_H: f64 = 192_000.;
const CURRENT_TOLERANCE_A: f64 = 2e-15;
const CORRECTION_TOLERANCE_V: f64 = 2e-12;

#[derive(Clone, Copy)]
pub struct State {
    pub audio: fast_r59::State,
    pub q15_v: [f64; 2],
    pub q15_current_a: [f64; 2],
}

pub struct Frame {
    pub audio: fast_r59::Frame,
    pub charge_increment_c: [f64; 2],
    pub residual_a: [f64; 2],
    pub trials: usize,
}

#[derive(Debug)]
pub enum Error {
    Audio(fast_r59::Error),
    Q15(StepError),
}

struct Trial {
    state: State,
    audio: fast_r59::Frame,
    charge_increment_c: [f64; 2],
    residual_a: [f64; 2],
    jacobian: [[f64; 2]; 2],
}

fn evaluate(
    old: State,
    q15_v: [f64; 2],
    [signal, c2, filter, q25_base, q25_collector, cr8_anode]: [f64; 6],
    refresh: bool,
) -> Result<Trial, Error> {
    let (audio, frame) = fast_r59::advance(old.audio, [signal, c2, q15_v[0], filter], refresh)
        .map_err(Error::Audio)?;
    let drive = q15::Drive {
        c2,
        vca_base: frame.ports.loads_v[0],
        q25_base,
        q25_collector,
        cr8_anode,
    };
    let (current, dc_jacobian) = q15::conduction(
        q15_v,
        drive,
        frame.reset_port.current_a,
        frame.reset_port.derivative_a_per_v[1],
    )
    .map_err(Error::Q15)?;
    let (charge, mass) =
        terminal(old.q15_v.map(|v| (v, 0.)), q15_v.map(|v| (v, 0.))).map_err(Error::Q15)?;
    let residual_a =
        std::array::from_fn(|k| current[k] + old.q15_current_a[k] + TWO_OVER_H * charge[k]);
    let jacobian = std::array::from_fn(|row| {
        std::array::from_fn(|col| dc_jacobian[row][col] + TWO_OVER_H * mass[row][col])
    });
    Ok(Trial {
        state: State {
            audio,
            q15_v,
            q15_current_a: current,
        },
        audio: frame,
        charge_increment_c: charge,
        residual_a,
        jacobian,
    })
}

pub fn advance(old: State, drive: [f64; 6], refresh: bool) -> Result<(State, Frame), Error> {
    let mut trial = evaluate(old, old.q15_v, drive, refresh)?;
    let mut trials = 1;
    for _ in 0..16 {
        let error = maximum(&trial.residual_a);
        let direction = Lu::factor(trial.jacobian)
            .and_then(|factor| factor.solve(trial.residual_a))
            .map_err(Error::Q15)?;
        if error <= CURRENT_TOLERANCE_A && maximum(&direction) <= CORRECTION_TOLERANCE_V {
            return Ok((
                trial.state,
                Frame {
                    audio: trial.audio,
                    charge_increment_c: trial.charge_increment_c,
                    residual_a: trial.residual_a,
                    trials,
                },
            ));
        }
        let mut accepted = None;
        for half in 0..12 {
            let scale = 0.5_f64.powi(half);
            let q15_v = std::array::from_fn(|i| trial.state.q15_v[i] - scale * direction[i]);
            trials += 1;
            if let Ok(candidate) = evaluate(old, q15_v, drive, refresh) {
                if maximum(&candidate.residual_a) < error {
                    accepted = Some(candidate);
                    break;
                }
            }
        }
        trial = accepted.ok_or(Error::Q15(StepError::NoDecrease))?;
    }
    Err(Error::Q15(StepError::IterationBudget))
}
