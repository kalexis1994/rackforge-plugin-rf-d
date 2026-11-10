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

struct Stamp<const N: usize> {
    f: [f64; N],
    j: [[f64; N]; N],
}

impl<const N: usize> Default for Stamp<N> {
    fn default() -> Self {
        Self {
            f: [0.; N],
            j: [[0.; N]; N],
        }
    }
}

impl<const N: usize> Stamp<N> {
    fn row(&mut self, i: usize, a: f64, entries: [(usize, f64); 3]) {
        if i < N {
            self.f[i] += a;
            for (k, g) in entries {
                if k < N {
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

fn solve_factored<const N: usize>(
    mut x: [f64; N],
    stamp: impl Fn([f64; N]) -> Result<Stamp<N>, StepError>,
    [current, voltage]: [f64; 2],
) -> Result<([f64; N], Lu<N>), StepError> {
    for _ in 0..12 {
        let Stamp { f, j } = stamp(x)?;
        let factor = Lu::factor(j)?;
        let d = factor.solve(f)?;
        if maximum(&f) <= current && maximum(&d) <= voltage {
            return Ok((x, factor));
        }
        x = std::array::from_fn(|i| x[i] - d[i]);
    }
    Err(StepError::IterationBudget)
}

fn solve<const N: usize>(
    x: [f64; N],
    stamp: impl Fn([f64; N]) -> Result<Stamp<N>, StepError>,
) -> Result<[f64; N], StepError> {
    solve_factored(x, stamp, [2e-13, 2e-9]).map(|(x, _)| x)
}

#[cfg(not(pilot_closed_cv))]
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

#[cfg(pilot_closed_cv)]
pub fn volume(
    initial: [f64; 3],
    c2: f64,
    [collector_seed, cv_return, vca_base]: [f64; 3],
) -> Result<[f64; 3], StepError> {
    let [base, emitter, loudness] = initial;
    let [base, emitter, loudness, _] = solve([base, emitter, loudness, collector_seed], |x| {
        volume_stamp(x, c2, cv_return, vca_base)
    })?;
    Ok([base, emitter, loudness])
}

#[cfg(pilot_closed_cv)]
fn volume_stamp(x: [f64; 4], c2: f64, cv: f64, vca_base: f64) -> Result<Stamp<4>, StepError> {
    let mut s = Stamp::default();
    s.transistor(&x, [0, 3, 1], 1.)?;
    s.transistor(&x, [1, 3, 2], 1.)?;
    s.load(0, x[0], c2, 10_000.);
    s.load(2, x[2], cv, 6800.);
    s.load(2, x[2], vca_base, R59);
    s.load(3, x[3], 9.3, 560.); // R15 supplies both collectors at x2.
    Ok(s)
}

#[cfg(pilot_closed_cv)]
pub fn cv_return_residual(x4: f64, x3: f64, x27: f64) -> Result<f64, StepError> {
    let vt = 1.5 * VT;
    let z = (x4 - x27) / vt;
    if !z.is_finite() || z > 45. {
        return Err(StepError::ExponentialDomain);
    }
    // The two resistors and CR6 are the complete x4 KCL. Scale it
    // by its local conductance to use a voltage tolerance at the interface.
    let f = (x4 + 10.) / 16_900. + (x4 - x3) / 6800. + 1e-8 * z.exp_m1();
    let g = 1. / 16_900. + 1. / 6800. + 1e-8 * z.exp() / vt;
    Ok(f / g)
}

pub fn filter(initial: [f64; 3], [sum, tail]: [f64; 2]) -> Result<[f64; 3], StepError> {
    solve(initial, |x| filter_stamp(x, sum, tail))
}

fn filter_stamp(x: [f64; 3], sum: f64, tail: f64) -> Result<Stamp<3>, StepError> {
    let mut s = Stamp::default();
    let v = [x[0], x[1], x[2], sum, 0.];
    s.transistor(&v, [3, 1, 0], -1.)?; // Q26
    s.transistor(&v, [0, 2, 4], 1.)?; // Q28
    s.load(0, x[0], 1., 68_900.);
    s.load(1, x[1], -10., 330.);
    s.load(2, x[2], tail, R60);
    Ok(s)
}

#[cfg(pilot_audio_readout)]
const JOINT_TOLERANCES: [f64; 2] = [2e-15, 2e-12];

#[cfg(pilot_audio_readout)]
pub fn joint_cells(
    cells: Returns,
    [c2, sum, cv]: [f64; 3],
    [base, tail]: [f64; 2],
    collector: f64,
    tangent: bool,
) -> Result<(Returns, [f64; 2]), StepError> {
    let [q3, q2, x3] = cells.volume;
    let ([q3, q2, x3, _], volume) = solve_factored(
        [q3, q2, x3, collector],
        |x| volume_stamp(x, c2, cv, base),
        JOINT_TOLERANCES,
    )?;
    let (filter, filter_factor) = solve_factored(
        cells.filter,
        |x| filter_stamp(x, sum, tail),
        JOINT_TOLERANCES,
    )?;
    let slope = if tangent {
        // Both KCL rows use (source - load) / R. Differentiating with
        // respect to the imposed load gives J dx/dload = e_2 / R.
        [
            volume.solve([0., 0., 1. / R59, 0.])?[2],
            filter_factor.solve([0., 0., 1. / R60])?[2],
        ]
    } else {
        [0.; 2]
    };
    Ok((
        Returns {
            volume: [q3, q2, x3],
            filter,
        },
        slope,
    ))
}

pub fn q22_base(mut base: f64, c5: f64, [collector, emitter]: [f64; 2]) -> Result<f64, StepError> {
    for _ in 0..12 {
        let mut s = Stamp::<3>::default();
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
