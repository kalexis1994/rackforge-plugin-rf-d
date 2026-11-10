//! Q25/Q15 and C4 with CR6 closed through the volume follower.
use crate::{
    latch_charge_driver::terminal,
    q15::{self, B},
    reduced_lu::{maximum, Lu},
    StepError,
};

pub const R28: f64 = 10_000.;
const R38: f64 = 10_000.;
const R40: f64 = 3300.;
const R56: f64 = 33_000.;
pub const C4: f64 = 10e-9;
const N: usize = 5;
const PAIR: usize = 2 * N;

#[derive(Clone, Copy)]
pub struct Drive {
    pub c2: f64,
    pub vca_base: f64,
    pub x17: f64,
    pub x24: f64,
    pub x6: f64,
    pub x9: f64,
}

#[derive(Clone, Copy)]
pub struct State {
    pub nodes: [f64; N],  // x25, x26, x27, x28, x23
    pub volume: [f64; N], // x0, x1, x3, x2, x4
}

pub(crate) struct Stage {
    pub(crate) state: State,
    pub(crate) current: [f64; N],
    pub(crate) jacobian: [[f64; N]; N],
    pub(crate) charge: [f64; N],
    pub(crate) mass: [[f64; N]; N],
}

pub(crate) fn stage(old: State, state: State, u: Drive) -> Result<Stage, StepError> {
    let [q25, x26, q15, x28, x23] = state.nodes;
    let q15_state = |s: State| q15::State {
        q15: [s.nodes[2], s.nodes[3]],
        volume: s.volume,
    };
    let returned = q15::stage(
        q15_state(old),
        q15_state(state),
        q15::Drive {
            c2: u.c2,
            vca_base: u.vca_base,
            q25_base: q25,
            q25_collector: x26,
            cr8_anode: u.x24,
        },
    )?;
    let (f, gf) = q15::junction(q25)?;
    let (r, gr) = q15::junction(q25 - x26)?;
    let (decay_f, decay_gf) = q15::junction(x26 - u.x9)?;
    let (decay_r, decay_gr) = q15::junction(x26 - 9.3)?;
    let current = [
        (q25 - x28) / R38 + f / 100. + r / 5.,
        (x26 - u.x6) / R40 + (x26 - q15) / R56 + f - 1.2 * r + decay_f / 100. + decay_r / 5.,
        returned.current[0],
        returned.current[1],
        (x23 - u.x17) / R28,
    ];
    let jacobian = [
        [1. / R38 + gf / 100. + gr / 5., -gr / 5., 0., -1. / R38, 0.],
        [
            gf - 1.2 * gr,
            1. / R40 + 1. / R56 + 1.2 * gr + decay_gf / 100. + decay_gr / 5.,
            -1. / R56,
            0.,
            0.,
        ],
        [
            0.,
            -1. / R56,
            returned.jacobian[0][0],
            returned.jacobian[0][1],
            0.,
        ],
        [
            -1. / R38,
            0.,
            returned.jacobian[1][0],
            returned.jacobian[1][1],
            0.,
        ],
        [0., 0., 0., 0., 1. / R28],
    ];
    let pair = |s: State| [(s.nodes[0], 0.), (s.nodes[1], 0.)];
    let (q25_charge, q25_mass) = terminal(pair(old), pair(state))?;
    let c4 = C4 * ((x23 - old.nodes[4]) - (q25 - old.nodes[0]));
    let charge = [
        q25_charge[0] - c4,
        q25_charge[1],
        returned.charge[0],
        returned.charge[1],
        c4,
    ];
    let mass = [
        [q25_mass[0][0] + C4, q25_mass[0][1], 0., 0., -C4],
        [q25_mass[1][0], q25_mass[1][1], 0., 0., 0.],
        [0., 0., returned.mass[0][0], returned.mass[0][1], 0.],
        [0., 0., returned.mass[1][0], returned.mass[1][1], 0.],
        [-C4, 0., 0., 0., C4],
    ];
    Ok(Stage {
        state: State {
            volume: returned.state.volume,
            ..state
        },
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
    inv: f64,
) -> Result<([State; 2], [f64; PAIR], [[f64; PAIR]; PAIR]), StepError> {
    let stage = [
        stage(old, trial[0], drive[0])?,
        stage(old, trial[1], drive[1])?,
    ];
    let residual = std::array::from_fn(|k| {
        let (i, r) = (k / N, k % N);
        stage[i].current[r] + inv * (B[i][0] * stage[0].charge[r] + B[i][1] * stage[1].charge[r])
    });
    let jacobian = std::array::from_fn(|k| {
        let (i, r) = (k / N, k % N);
        std::array::from_fn(|l| {
            let (j, c) = (l / N, l % N);
            let dc = if i == j { stage[i].jacobian[r][c] } else { 0. };
            dc + inv * B[i][j] * stage[j].mass[r][c]
        })
    });
    Ok((stage.map(|s| s.state), residual, jacobian))
}

pub fn step(old: State, drive: [Drive; 2], h: Option<f64>) -> Result<[State; 2], StepError> {
    let inv = h.map_or(0., |h| h.recip());
    if !inv.is_finite() || inv < 0. {
        return Err(StepError::InvalidInput);
    }
    let mut trial = evaluate(old, [old; 2], drive, inv)?;
    for _ in 0..20 {
        let (states, residual, jacobian) = trial;
        let change = Lu::factor(jacobian)?.solve(residual)?;
        let error = maximum(&residual);
        if error <= 2e-13 && maximum(&change) <= 2e-9 {
            return Ok(states);
        }
        let mut accepted = None;
        for half in 0..12 {
            let scale = 0.5_f64.powi(half);
            let mut proposal = states;
            for k in 0..PAIR {
                proposal[k / N].nodes[k % N] -= scale * change[k];
            }
            if let Ok(next) = evaluate(old, proposal, drive, inv) {
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
