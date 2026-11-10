//! Continuous C4 memory along a fixed, charge-parameterized precursor.
use crate::{crossing::Point, precursor::solve};

pub const STATE: usize = 9;
pub const POINTS: usize = 65;
const GUARD: f64 = 0.35;
const PERIOD_S: f64 = 1. / 96_000.;
const R28_C4_S: f64 = 10_000. * 10e-9;
const TIMERS: [usize; 2] = [6, 8];

#[derive(Clone, Copy)]
pub struct Knot {
    pub nominal: [f64; STATE],
    pub linear: [[f64; STATE]; 2],
    pub quadratic: [[f64; STATE]; 2],
}

pub struct Family(pub [Knot; POINTS]);

pub enum Step {
    Boundary([f64; STATE]),
    Guard(Point, f64),
}

#[derive(Clone, Copy)]
pub struct Clock<'a> {
    family: &'a Family,
    load: [f64; 2],
    offset: [f64; STATE],
    state: [f64; STATE],
    next: usize,
    finished: bool,
}

impl Knot {
    fn value(self, k: usize, load: [f64; 2]) -> f64 {
        let [a, b] = load;
        self.nominal[k]
            + (a * self.linear[0][k] + b * self.linear[1][k])
            + (a * a * self.quadratic[0][k] + b * b * self.quadratic[1][k])
    }

    fn interpolate(self, to: Self, f: f64) -> Self {
        let row =
            |a: [f64; STATE], b: [f64; STATE]| std::array::from_fn(|i| a[i] + f * (b[i] - a[i]));
        Self {
            nominal: row(self.nominal, to.nominal),
            linear: std::array::from_fn(|i| row(self.linear[i], to.linear[i])),
            quadratic: std::array::from_fn(|i| row(self.quadratic[i], to.quadratic[i])),
        }
    }
}

impl Family {
    pub fn start(&self, mut observed: [f64; STATE]) -> Option<Clock<'_>> {
        if !(0. ..GUARD).contains(&observed[0]) || !(observed[0] < observed[7]) {
            return None;
        }
        observed[1] -= observed[2];
        let charge = observed[1];
        let mut phase = self.locate(charge, [0., 0.])?;
        let mut load = [0.; 2];
        for _ in 0..4 {
            load = self.fit(self.sample(phase), observed)?;
            phase = self.locate(charge, load)?;
        }
        let knot = self.sample(phase);
        let mut offset = std::array::from_fn(|k| observed[k] - knot.value(k, load));
        offset[0] = 0.;
        let next = (phase * (POINTS - 1) as f64).floor() as usize + 1;
        Some(Clock {
            family: self,
            load,
            offset,
            state: observed,
            next,
            finished: false,
        })
    }

    fn sample(&self, phase: f64) -> Knot {
        let position = phase * (POINTS - 1) as f64;
        let left = (position as usize).min(POINTS - 2);
        self.0[left].interpolate(self.0[left + 1], position - left as f64)
    }

    fn locate(&self, charge: f64, load: [f64; 2]) -> Option<f64> {
        let q = |i: usize| self.0[i].value(1, load);
        if !(q(POINTS - 1) < charge && charge <= q(0) + 1e-12) {
            return None;
        }
        let (mut low, mut high) = (0, POINTS - 1);
        while high - low > 1 {
            let middle = (high + low) / 2;
            if q(middle) >= charge {
                low = middle;
            } else {
                high = middle;
            }
        }
        let fraction = (q(low) - charge) / (q(low) - q(high));
        Some((low as f64 + fraction.max(0.)) / (POINTS - 1) as f64)
    }

    fn fit(&self, knot: Knot, observed: [f64; STATE]) -> Option<[f64; 2]> {
        let wanted = TIMERS.map(|i| observed[i] - knot.nominal[i]);
        let linear = knot.linear.map(|axis| TIMERS.map(|i| axis[i]));
        let quadratic = knot.quadratic.map(|axis| TIMERS.map(|i| axis[i]));
        let mut load = solve(linear, wanted)?;
        for _ in 0..3 {
            let [a, b] = load;
            let residual = std::array::from_fn(|k| {
                linear[0][k] * a
                    + linear[1][k] * b
                    + quadratic[0][k] * (a * a)
                    + quadratic[1][k] * (b * b)
                    - wanted[k]
            });
            let tangent = std::array::from_fn(|j| {
                std::array::from_fn(|k| linear[j][k] + 2. * quadratic[j][k] * load[j])
            });
            let [da, db] = solve(tangent, residual)?;
            load = [a - da, b - db];
        }
        load.iter()
            .all(|v| (-1.05..=1.05).contains(v))
            .then_some(load)
    }
}

impl Clock<'_> {
    pub fn advance(&mut self) -> Option<Step> {
        let mut candidate = *self;
        let output = candidate.interval()?;
        *self = candidate;
        Some(output)
    }

    fn interval(&mut self) -> Option<Step> {
        if self.finished {
            return None;
        }
        if self.next == POINTS {
            return self.guard(0.);
        }
        let mut remaining = PERIOD_S;
        while self.next < POINTS {
            let knot = self.family.0[self.next];
            let to: [f64; STATE] =
                std::array::from_fn(|k| knot.value(k, self.load) + self.offset[k]);
            let gap = |x: [f64; STATE]| x[1] + x[2] - x[3];
            let from = gap(self.state);
            let end = gap(to);
            let drop = self.state[1] - to[1];
            if !(from > 0. && end > 0. && drop > 0.) {
                return None;
            }
            let relative = (end - from) / from;
            let log = relative.ln_1p();
            let scale = if relative == 0. { 1. } else { log / relative };
            let duration = R28_C4_S * drop / from * scale;
            if duration > remaining {
                let elapsed = remaining / duration;
                let fraction = if relative == 0. {
                    elapsed
                } else {
                    (log * elapsed).exp_m1() / relative
                };
                self.state =
                    std::array::from_fn(|k| self.state[k] + fraction * (to[k] - self.state[k]));
                return Some(Step::Boundary(self.state));
            }
            self.state = to;
            self.next += 1;
            remaining -= duration;
            if self.next == POINTS {
                return if remaining == 0. {
                    Some(Step::Boundary(to))
                } else {
                    self.guard(PERIOD_S - remaining)
                };
            }
        }
        None
    }

    fn guard(&mut self, time: f64) -> Option<Step> {
        let to = self.state;
        if !(to[7] > GUARD) {
            return None;
        }
        self.finished = true;
        Some(Step::Guard(
            Point {
                collector: GUARD,
                neighbors: [to[2], to[4], to[5], to[6], to[7]],
            },
            time,
        ))
    }
}
