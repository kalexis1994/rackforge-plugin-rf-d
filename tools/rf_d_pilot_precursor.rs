//! Bounded C4 charge clock to the rising collector guard.
use crate::crossing::Point;

pub const POINTS: usize = 65;
const STATE: usize = 8;
const GUARD: f64 = 0.35;
const PERIOD_S: f64 = 1. / 96_000.;
const R28_C4_S: f64 = 10_000. * 10e-9;
const TIMERS: [usize; 2] = [5, 7];

#[derive(Clone, Copy)]
pub struct Knot {
    pub collector: f64,
    pub nominal: [f64; STATE],
    pub linear: [[f64; STATE]; 2],
    pub quadratic: [[f64; STATE]; 2],
}

pub struct Profile(pub [Knot; POINTS]);

fn solve(columns: [[f64; 2]; 2], [a, b]: [f64; 2]) -> Option<[f64; 2]> {
    let [[c, d], [e, f]] = columns;
    let determinant = c * f - d * e;
    if !determinant.is_finite() || determinant.abs() < 1e-12 {
        return None;
    }
    Some([(a * f - b * e) / determinant, (c * b - d * a) / determinant])
}

fn state(knot: Knot, load: [f64; 2]) -> [f64; STATE] {
    std::array::from_fn(|k| {
        knot.nominal[k]
            + load[0] * knot.linear[0][k]
            + load[1] * knot.linear[1][k]
            + load[0] * load[0] * knot.quadratic[0][k]
            + load[1] * load[1] * knot.quadratic[1][k]
    })
}

impl Profile {
    /// The observed voltages are x23, x25, x17, x27, x9, C2, x28 and C5.
    pub fn advance(&self, collector: f64, mut observed: [f64; STATE]) -> Option<(Point, f64)> {
        if !(self.0[0].collector..GUARD).contains(&collector) || !(collector < observed[6]) {
            return None;
        }
        observed[0] -= observed[1];
        let next = self.0.iter().position(|knot| knot.collector > collector)?;
        let left = (next - 1).min(POINTS - 3);
        let knots = [self.0[left], self.0[left + 1], self.0[left + 2]];
        let x = knots.map(|k| k.collector);
        let weights: [f64; 3] = std::array::from_fn(|i| {
            (0..3)
                .filter(|&j| j != i)
                .map(|j| (collector - x[j]) / (x[i] - x[j]))
                .product()
        });
        let sample = |field: fn(Knot) -> [f64; STATE]| {
            let values = knots.map(field);
            std::array::from_fn(|i| (0..3).map(|j| values[j][i] * weights[j]).sum())
        };
        let at = Knot {
            collector,
            nominal: sample(|k| k.nominal),
            linear: [sample(|k| k.linear[0]), sample(|k| k.linear[1])],
            quadratic: [sample(|k| k.quadratic[0]), sample(|k| k.quadratic[1])],
        };
        let wanted = TIMERS.map(|i| observed[i] - at.nominal[i]);
        let linear = at.linear.map(|row| TIMERS.map(|i| row[i]));
        let quadratic = at.quadratic.map(|row| TIMERS.map(|i| row[i]));
        let mut load = solve(linear, wanted)?;
        for _ in 0..3 {
            let residual = std::array::from_fn(|k| {
                linear[0][k] * load[0]
                    + linear[1][k] * load[1]
                    + quadratic[0][k] * load[0] * load[0]
                    + quadratic[1][k] * load[1] * load[1]
                    - wanted[k]
            });
            let tangent = std::array::from_fn(|j| {
                std::array::from_fn(|k| linear[j][k] + 2. * quadratic[j][k] * load[j])
            });
            let correction = solve(tangent, residual)?;
            load = [load[0] - correction[0], load[1] - correction[1]];
        }
        if !load.iter().all(|v| (-1.05..=1.05).contains(v)) {
            return None;
        }
        let model_start = state(at, load);
        let offset: [f64; STATE] = std::array::from_fn(|k| observed[k] - model_start[k]);
        let mut before = observed;
        let mut time = 0.;
        for &knot in &self.0[next..] {
            let point = state(knot, load);
            let after = std::array::from_fn(|k| point[k] + offset[k]);
            let from = before[0] + before[1] - before[2];
            let to = after[0] + after[1] - after[2];
            let drop = before[0] - after[0];
            if !(from > 0. && to > 0. && drop > 0.) {
                return None;
            }
            let relative = (to - from) / from;
            let integral = if relative == 0. {
                1.
            } else {
                relative.ln_1p() / relative
            };
            time += R28_C4_S * drop / from * integral;
            if time >= PERIOD_S {
                return None;
            }
            before = after;
        }
        if !(before[6] > GUARD && time > 0.) {
            return None;
        }
        let point = Point {
            collector: GUARD,
            neighbors: [before[1], before[3], before[4], before[5], before[6]],
        };
        Some((point, time))
    }
}
