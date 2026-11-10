//! Bounded post-event projection and algebraic readout of the volume latch.
use crate::{
    bistable::{self, Drive, State},
    clock::PERIOD_S,
    StepError,
};

pub const POINTS: usize = 129;
const NODES: usize = 15;

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

    pub fn at(&self, seconds: f64, [a, b]: [f64; 2], drive: Drive) -> Result<State, StepError> {
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
        bistable::handoff_readout(
            State {
                nodes: x[..5].try_into().unwrap(),
                volume: x[5..10].try_into().unwrap(),
                attack: x[10..12].try_into().unwrap(),
                decay: x[12..].try_into().unwrap(),
            },
            drive,
        )
    }
}
