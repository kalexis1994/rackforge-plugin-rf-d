//! Algebraic return cells of the loaded contour graph.
use crate::{
    latch_charge::VT,
    reduced_lu::{maximum, Lu},
    StepError,
};

pub const VOLUME_NODES: [usize; 3] = [0, 1, 3];
pub const FILTER_NODES: [usize; 3] = [35, 36, 37];
pub const VOLUME_PORTS: [usize; 3] = [2, 4, 54];
pub const FILTER_PORTS: [usize; 2] = [34, 55];
const R59: f64 = 68_000.;
const R60: f64 = 680.;

#[derive(Clone, Copy)]
pub struct Returns {
    pub volume: [f64; 3],
    pub filter: [f64; 3],
}

impl Returns {
    pub fn currents(self, vca_base: f64, tail: f64) -> [f64; 2] {
        [
            (self.volume[2] - vca_base) / R59,
            (tail - self.filter[2]) / R60,
        ]
    }
}

#[derive(Default)]
struct Stamp {
    f: [f64; 3],
    j: [[f64; 3]; 3],
}

impl Stamp {
    fn row(&mut self, i: usize, a: f64, entries: [(usize, f64); 3]) {
        if i < 3 {
            self.f[i] += a;
            for (k, g) in entries {
                if k < 3 {
                    self.j[i][k] += g;
                }
            }
        }
    }

    fn load(&mut self, row: usize, v: f64, port: f64, ohm: f64) {
        self.f[row] += (v - port) / ohm;
        self.j[row][row] += 1. / ohm;
    }

    fn transistor(&mut self, v: &[f64], [b, c, e]: [usize; 3], sign: f64) -> Result<(), StepError> {
        let law = |k| {
            let z: f64 = sign * (v[b] - v[k]) / VT;
            if !z.is_finite() || z > 45. {
                return Err(StepError::ExponentialDomain);
            }
            Ok((1e-14 * z.exp_m1(), 1e-14 * z.exp() / VT))
        };
        let (f, gf) = law(e)?;
        let (r, gr) = law(c)?;
        let ib = f / 100. + r / 5.;
        let ic = f - 1.2 * r;
        self.row(
            b,
            sign * ib,
            [(b, gf / 100. + gr / 5.), (c, -gr / 5.), (e, -gf / 100.)],
        );
        self.row(c, sign * ic, [(b, gf - 1.2 * gr), (c, 1.2 * gr), (e, -gf)]);
        self.row(
            e,
            -sign * (ib + ic),
            [(b, gr - 1.01 * gf), (c, -gr), (e, 1.01 * gf)],
        );
        Ok(())
    }
}

fn solve(
    mut x: [f64; 3],
    stamp: impl Fn([f64; 3]) -> Result<Stamp, StepError>,
) -> Result<[f64; 3], StepError> {
    for _ in 0..12 {
        let Stamp { f, j } = stamp(x)?;
        let d = Lu::factor(j)?.solve(f)?;
        if maximum(&f) <= 2e-13 && maximum(&d) <= 2e-9 {
            return Ok(x);
        }
        x = std::array::from_fn(|i| x[i] - d[i]);
    }
    Err(StepError::IterationBudget)
}

pub fn volume(
    initial: [f64; 3],
    c2: f64,
    [rail, cv_return, vca_base]: [f64; 3],
) -> Result<[f64; 3], StepError> {
    solve(initial, |x| {
        let mut s = Stamp::default();
        let v = [x[0], x[1], x[2], rail];
        s.transistor(&v, [0, 3, 1], 1.)?; // Q3
        s.transistor(&v, [1, 3, 2], 1.)?; // Q2
        s.load(0, x[0], c2, 10_000.);
        s.load(2, x[2], cv_return, 6800.);
        s.load(2, x[2], vca_base, R59);
        Ok(s)
    })
}

pub fn filter(initial: [f64; 3], [sum, tail]: [f64; 2]) -> Result<[f64; 3], StepError> {
    solve(initial, |x| {
        let mut s = Stamp::default();
        let v = [x[0], x[1], x[2], sum, 0.];
        s.transistor(&v, [3, 1, 0], -1.)?; // Q26
        s.transistor(&v, [0, 2, 4], 1.)?; // Q28
        s.load(0, x[0], 1., 68_900.);
        s.load(1, x[1], -10., 330.);
        s.load(2, x[2], tail, R60);
        Ok(s)
    })
}

pub fn q22_base(mut base: f64, c5: f64, [collector, emitter]: [f64; 2]) -> Result<f64, StepError> {
    for _ in 0..12 {
        let mut s = Stamp::default();
        s.transistor(&[base, 0., 0., collector, emitter], [0, 3, 4], 1.)?;
        s.load(0, base, c5, 10_000.);
        let correction = s.f[0] / s.j[0][0];
        if s.f[0].abs() <= 2e-13 && correction.abs() <= 2e-9 {
            return Ok(base);
        }
        base -= correction;
    }
    Err(StepError::IterationBudget)
}
