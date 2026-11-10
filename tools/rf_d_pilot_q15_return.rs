//! Q15 return with its BE/BC history and an algebraically condensed follower.
use crate::{
    contour_ports::{close_volume, germanium},
    latch_charge_driver::{terminal, VT},
    reduced_lu::{maximum, Lu},
    StepError,
};

pub const B: [[f64; 2]; 2] = [[1.5, 0.5], [-4.5, 2.5]];

#[derive(Clone, Copy)]
pub struct Drive {
    pub c2: f64,
    pub vca_base: f64,
    pub q25_base: f64,
    pub q25_collector: f64,
    pub cr8_anode: f64,
}

#[derive(Clone, Copy)]
pub struct State {
    pub q15: [f64; 2],    // x27 and x28
    pub volume: [f64; 5], // x0, x1, x3, x2, x4
}

pub(crate) struct Stage {
    pub(crate) state: State,
    pub(crate) current: [f64; 2],
    pub(crate) jacobian: [[f64; 2]; 2],
    pub(crate) charge: [f64; 2],
    pub(crate) mass: [[f64; 2]; 2],
}

pub(crate) fn stage(old: State, state: State, drive: Drive) -> Result<Stage, StepError> {
    let [base, collector] = state.q15;
    let (volume, factor) = close_volume(state.volume, drive.c2, base, drive.vca_base)?;
    let (cr6, gd6) = germanium(volume[4] - base)?;
    // The cathode changes both ends of the branch. The follower's KCL
    // gives d(x4)/d(x27), including the reciprocal R24 load.
    let dx4 = factor.solve([0., 0., 0., 0., gd6])?[4];
    let cr6_tangent = gd6 * (dx4 - 1.);
    let (cr8, gd8) = germanium(drive.cr8_anode - base)?;
    let junction = |v: f64| -> Result<(f64, f64), StepError> {
        let z = v / VT;
        if !z.is_finite() || z > 45. {
            return Err(StepError::ExponentialDomain);
        }
        Ok((1e-14 * z.exp_m1(), 1e-14 * z.exp() / VT))
    };
    let (f, gf) = junction(base)?;
    let (r, gr) = junction(base - collector)?;
    let current = [
        (base - drive.q25_collector) / 33_000. + f / 100. + r / 5. - cr8 - cr6,
        (collector - 9.3) / 10_000. + (collector - drive.q25_base) / 10_000. + f - 1.2 * r,
    ];
    let jacobian = [
        [
            1. / 33_000. + gf / 100. + gr / 5. + gd8 - cr6_tangent,
            -gr / 5.,
        ],
        [gf - 1.2 * gr, 2. / 10_000. + 1.2 * gr],
    ];
    let (charge, mass) = terminal(old.q15.map(|v| (v, 0.)), state.q15.map(|v| (v, 0.)))?;
    Ok(Stage {
        state: State { volume, ..state },
        current,
        jacobian,
        charge,
        mass,
    })
}

fn evaluate(
    old: State,
    trial: [State; 2],
    drive: [Drive; 2],
    inverse_step: f64,
) -> Result<([State; 2], [f64; 4], [[f64; 4]; 4]), StepError> {
    let stages = [
        stage(old, trial[0], drive[0])?,
        stage(old, trial[1], drive[1])?,
    ];
    let residual = std::array::from_fn(|k| {
        let (i, r) = (k / 2, k % 2);
        stages[i].current[r]
            + inverse_step * (B[i][0] * stages[0].charge[r] + B[i][1] * stages[1].charge[r])
    });
    let jacobian = std::array::from_fn(|k| {
        let (i, r) = (k / 2, k % 2);
        std::array::from_fn(|l| {
            let (j, c) = (l / 2, l % 2);
            let dc = if i == j { stages[i].jacobian[r][c] } else { 0. };
            dc + inverse_step * B[i][j] * stages[j].mass[r][c]
        })
    });
    Ok((stages.map(|s| s.state), residual, jacobian))
}

pub fn step(old: State, drive: [Drive; 2], h: Option<f64>) -> Result<[State; 2], StepError> {
    let inverse_step = h.map_or(0., |h| h.recip());
    if !inverse_step.is_finite() || inverse_step < 0. {
        return Err(StepError::InvalidInput);
    }
    let mut trial = evaluate(old, [old; 2], drive, inverse_step)?;
    for _ in 0..16 {
        let (states, residual, jacobian) = trial;
        let change = Lu::factor(jacobian)?.solve(residual)?;
        let error = maximum(&residual);
        if error <= 2e-15 && maximum(&change) <= 2e-12 {
            return Ok(states);
        }
        let mut accepted = None;
        for half in 0..12 {
            let factor = 0.5_f64.powi(half);
            let mut proposal = states;
            for i in 0..4 {
                proposal[i / 2].q15[i % 2] -= factor * change[i];
            }
            if let Ok(next) = evaluate(old, proposal, drive, inverse_step) {
                if maximum(&next.1) < error {
                    accepted = Some(next);
                    break;
                }
            }
        }
        trial = accepted.ok_or(StepError::NoDecrease)?;
    }
    Err(StepError::IterationBudget)
}
