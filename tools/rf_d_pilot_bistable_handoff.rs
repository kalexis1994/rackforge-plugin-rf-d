//! Bounded post-event projection and algebraic readout of the volume latch.
use crate::{
    bistable::{self, Drive, State},
    timer::{CAPACITANCE_F, RESISTANCE_OHM},
    StepError,
};

pub const POINTS: usize = 129;
const PERIOD_S: f64 = 1. / 96_000.;
const NODES: usize = 15;
const RADAU_A: [[f64; 2]; 2] = [[5. / 12., -1. / 12.], [3. / 4., 1. / 4.]];
const C2_TOLERANCE_V: f64 = 1e-12;

pub struct Knot {
    pub seconds: f64,
    // x25, x26, x27, x28, C4 voltage, then the algebraic guesses.
    pub coefficients: [[f64; NODES]; 5],
}

pub struct Profile([Knot; POINTS]);

impl Profile {
    pub fn new(knots: [Knot; POINTS], intervals: u8) -> Result<Self, StepError> {
        let valid = knots[0].seconds == 0.
            && knots[POINTS - 1].seconds == f64::from(intervals) * PERIOD_S
            && knots
                .windows(2)
                .all(|pair| pair[0].seconds < pair[1].seconds)
            && knots
                .iter()
                .all(|k| k.coefficients.iter().flatten().all(|x| x.is_finite()));
        if !valid {
            return Err(StepError::InvalidInput);
        }
        Ok(Self(knots))
    }

    fn guess(&self, seconds: f64, [a, b]: [f64; 2]) -> Result<State, StepError> {
        if !(0. ..=self.0[POINTS - 1].seconds).contains(&seconds)
            || !(a.abs() <= 1.05 && b.abs() <= 1.05)
        {
            return Err(StepError::InvalidInput);
        }
        let right = self
            .0
            .partition_point(|k| k.seconds <= seconds)
            .clamp(1, POINTS - 1);
        let [left, right] = [&self.0[right - 1], &self.0[right]];
        let fraction = (seconds - left.seconds) / (right.seconds - left.seconds);
        let evaluate = |k: &Knot, i| {
            let [x, da, db, qa, qb] = k.coefficients.each_ref().map(|row| row[i]);
            (x + (a * da + b * db)) + (a * a * qa + b * b * qb)
        };
        let mut x: [f64; NODES] = std::array::from_fn(|i| {
            let before = evaluate(left, i);
            before + fraction * (evaluate(right, i) - before)
        });
        x[4] += x[0];
        Ok(State {
            nodes: x[..5].try_into().unwrap(),
            volume: x[5..10].try_into().unwrap(),
            attack: x[10..12].try_into().unwrap(),
            decay: x[12..].try_into().unwrap(),
        })
    }

    pub fn at(&self, seconds: f64, weights: [f64; 2], drive: Drive) -> Result<State, StepError> {
        bistable::handoff_readout(self.guess(seconds, weights)?, drive)
    }

    pub fn project_c2(
        &self,
        c2: f64,
        ages: [f64; 2],
        weights: [f64; 2],
        mut drives: [Drive; 2],
    ) -> Result<([State; 2], [Drive; 2]), StepError> {
        let mut states = [self.guess(ages[0], weights)?, self.guess(ages[1], weights)?];
        for drive in &mut drives {
            drive.c2 = c2;
        }
        let [attack, decay, follower] = RESISTANCE_OHM[0];
        for _ in 0..4 {
            for i in 0..2 {
                states[i] = bistable::handoff_readout(states[i], drives[i])?;
            }
            let current: [f64; 2] = std::array::from_fn(|i| {
                let v = drives[i].c2;
                (states[i].attack[1] - v) / attack
                    + (states[i].decay[2] - v) / decay
                    + (states[i].volume[0] - v) / follower
            });
            let next = RADAU_A
                .map(|[a, b]| c2 + PERIOD_S / CAPACITANCE_F * (a * current[0] + b * current[1]));
            if next
                .iter()
                .zip(drives)
                .all(|(&v, u)| (v - u.c2).abs() <= C2_TOLERANCE_V)
            {
                return Ok((states, drives));
            }
            for (u, v) in drives.iter_mut().zip(next) {
                u.c2 = v;
            }
        }
        Err(StepError::IterationBudget)
    }
}
