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
const R24: f64 = 6800.;
#[cfg(pilot_closed_cv)]
pub(crate) const VOLUME_R16: f64 = 10_000.;
#[cfg(pilot_closed_cv)]
const R27: f64 = 16_900.;
const R59: f64 = 68_000.;
const R60: f64 = 680.;

#[cfg(pilot_shared_port_exp)]
fn exponential_pair(z: f64) -> (f64, f64) {
    let value = z.exp();
    let remainder = if z.abs() < 0.125 { z.exp_m1() } else { value - 1. };
    (remainder, value)
}

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
            #[cfg(pilot_shared_port_exp)]
            let (current, slope) = exponential_pair(z);
            #[cfg(not(pilot_shared_port_exp))]
            let (current, slope) = (z.exp_m1(), z.exp());
            Ok((1e-14 * current, 1e-14 * slope / VT))
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
        s.load(2, x[2], cv_return, R24);
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
    s.load(0, x[0], c2, VOLUME_R16);
    s.load(2, x[2], cv, R24);
    s.load(2, x[2], vca_base, R59);
    s.load(3, x[3], 9.3, 560.); // R15 supplies both collectors at x2.
    Ok(s)
}

#[cfg(pilot_closed_cv)]
pub fn cv_return_residual(x4: f64, x3: f64, x27: f64) -> Result<f64, StepError> {
    let (residual, slope, _) = cv_law(x4, x3, x27)?;
    Ok(residual / slope)
}

#[cfg(pilot_closed_cv)]
fn cv_law(x4: f64, x3: f64, x27: f64) -> Result<(f64, f64, f64), StepError> {
    let (diode, conductance) = germanium(x4 - x27)?;
    let residual = (x4 + 10.) / R27 + (x4 - x3) / R24 + diode;
    let slope = 1. / R27 + 1. / R24 + conductance;
    Ok((residual, slope, diode))
}

#[cfg(pilot_closed_cv)]
pub(crate) fn germanium(voltage: f64) -> Result<(f64, f64), StepError> {
    let scale = 1.5 * VT;
    let z = voltage / scale;
    if !z.is_finite() || z > 45. {
        return Err(StepError::ExponentialDomain);
    }
    #[cfg(pilot_shared_port_exp)]
    let (current, slope) = exponential_pair(z);
    #[cfg(not(pilot_shared_port_exp))]
    let (current, slope) = (z.exp_m1(), z.exp());
    Ok((1e-8 * current, 1e-8 * slope / scale))
}

#[cfg(pilot_r59_predict_cathode)]
pub(crate) fn cathode_rhs(reset: f64, cathode: f64) -> Result<[f64; 5], StepError> {
    let (_, conductance) = germanium(reset - cathode)?;
    Ok([0., 0., 0., 0., conductance])
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
const R59_TOLERANCES: [f64; 2] = if cfg!(pilot_r59_tight_follower) {
    [JOINT_TOLERANCES[0], 2e-14]
} else {
    JOINT_TOLERANCES
};

// SVC-9 fig. 9-7. C2 and the sustain emitter are explicit ports.
#[cfg(pilot_audio_readout)]
pub(crate) fn volume_decay(
    initial: [f64; 3],
    latch_v: f64,
    c2: f64,
    sustain_v: f64,
) -> Result<([f64; 3], Lu<3>), StepError> {
    solve_factored(
        initial,
        |x| {
            let mut s = Stamp::default();
            let v = [x[0], x[1], x[2], latch_v, 9.3, sustain_v];
            s.transistor(&v, [3, 4, 0], 1.)?; // Q17
            s.transistor(&v, [1, 2, 5], 1.)?; // Q18
            s.load(0, x[0], -10., 10_000.); // R43
            s.load(0, x[0], x[1], 4_700.); // R44
            s.load(1, x[1], x[0], 4_700.);
            s.j[0][1] -= 1. / 4_700.;
            s.j[1][0] -= 1. / 4_700.;
            s.load(2, x[2], c2, 10_000.); // Nominal panel R16
            Ok(s)
        },
        JOINT_TOLERANCES,
    )
}

#[cfg(pilot_audio_readout)]
#[derive(Clone, Copy)]
pub enum Cv {
    Fixed(f64),
    Closed { seed: f64, cathode: f64 },
}

#[cfg(pilot_audio_readout)]
fn closed_volume_stamp(
    x: [f64; 5],
    c2: f64,
    cathode: f64,
    base: f64,
) -> Result<Stamp<5>, StepError> {
    let four = volume_stamp([x[0], x[1], x[2], x[3]], c2, x[4], base)?;
    let (cv, slope, _) = cv_law(x[4], x[2], cathode)?;
    let mut stamp = Stamp::<5>::default();
    stamp.f[..4].copy_from_slice(&four.f);
    for (dest, source) in stamp.j[..4].iter_mut().zip(four.j) {
        dest[..4].copy_from_slice(&source);
    }
    stamp.f[4] = cv;
    stamp.j[2][4] = -1. / R24;
    stamp.j[4][2] = -1. / R24;
    stamp.j[4][4] = slope;
    Ok(stamp)
}

#[cfg(pilot_audio_readout)]
pub(crate) fn close_volume(
    initial: [f64; 5],
    c2: f64,
    cathode: f64,
    base: f64,
) -> Result<([f64; 5], Lu<5>), StepError> {
    solve_factored(
        initial,
        |x| closed_volume_stamp(x, c2, cathode, base),
        R59_TOLERANCES,
    )
}

#[cfg(pilot_r59_schur_follower)]
pub(crate) enum R59Factor {
    Schur { factor: Lu<4>, cv_diagonal: f64 },
    Full(Lu<5>),
}

#[cfg(pilot_r59_schur_follower)]
impl R59Factor {
    pub(crate) fn solve(&self, [r0, r1, r2, r3, r4]: [f64; 5]) -> Result<[f64; 5], StepError> {
        match self {
            Self::Schur { factor, cv_diagonal } => {
                let g24 = 1. / R24;
                let [d0, d1, d2, d3] = factor.solve([r0, r1, r2 + (g24 / cv_diagonal) * r4, r3])?;
                let d4 = (r4 + g24 * d2) / cv_diagonal;
                if !d4.is_finite() {
                    return Err(StepError::SingularJacobian);
                }
                Ok([d0, d1, d2, d3, d4])
            }
            Self::Full(factor) => factor.solve([r0, r1, r2, r3, r4]),
        }
    }
}

#[cfg(pilot_r59_schur_follower)]
fn close_volume_schur(
    mut x: [f64; 5],
    c2: f64,
    cathode: f64,
    base: f64,
) -> Result<([f64; 5], R59Factor), StepError> {
    let [current, voltage] = R59_TOLERANCES;
    let g24 = 1. / R24;
    for _ in 0..12 {
        let [x0, x1, x2, x3, x4] = x;
        let Stamp { f: [r0, r1, r2, r3], mut j } = volume_stamp([x0, x1, x2, x3], c2, x4, base)?;
        let (r4, cv_diagonal, _) = cv_law(x4, x2, cathode)?;
        if !cv_diagonal.is_finite() || cv_diagonal <= 0. {
            return Err(StepError::SingularJacobian);
        }
        // The reset node has only one off-diagonal entry, -1/R24 at loudness.
        j[2][2] -= g24 * (g24 / cv_diagonal);
        let factor = R59Factor::Schur { factor: Lu::factor(j)?, cv_diagonal };
        let residual = [r0, r1, r2, r3, r4];
        let d = factor.solve(residual)?;
        if maximum(&residual) <= current && maximum(&d) <= voltage {
            return Ok((x, factor));
        }
        x = std::array::from_fn(|i| x[i] - d[i]);
    }
    Err(StepError::IterationBudget)
}

#[cfg(pilot_r59_schur_follower)]
pub(crate) fn close_r59_volume(
    initial: [f64; 5],
    c2: f64,
    cathode: f64,
    base: f64,
) -> Result<([f64; 5], R59Factor), StepError> {
    close_volume_schur(initial, c2, cathode, base).or_else(|_| {
        close_volume(initial, c2, cathode, base).map(|(state, factor)| (state, R59Factor::Full(factor)))
    })
}

#[cfg(pilot_audio_readout)]
pub fn joint_cells(
    cells: Returns,
    [c2, sum]: [f64; 2],
    cv: Cv,
    [base, tail]: [f64; 2],
    collector: f64,
    tangent: bool,
) -> Result<(Returns, [f64; 2], [f64; 2]), StepError> {
    let [q3, q2, x3] = cells.volume;
    // In each branch J dx/dload = e_2 / R.
    let (volume, volume_slope, cv_readout) = match cv {
        Cv::Fixed(x4) => {
            let ([q3, q2, x3, _], factor) = solve_factored(
                [q3, q2, x3, collector],
                |x| volume_stamp(x, c2, x4, base),
                JOINT_TOLERANCES,
            )?;
            let slope = if tangent {
                factor.solve([0., 0., 1. / R59, 0.])?[2]
            } else {
                0.
            };
            ([q3, q2, x3], slope, [x4, 0.])
        }
        Cv::Closed { seed, cathode } => {
            let ([q3, q2, x3, _, x4], factor) =
                close_volume([q3, q2, x3, collector, seed], c2, cathode, base)?;
            let slope = if tangent {
                factor.solve([0., 0., 1. / R59, 0., 0.])?[2]
            } else {
                0.
            };
            ([q3, q2, x3], slope, [x4, cv_law(x4, x3, cathode)?.2])
        }
    };
    let (filter, factor) = solve_factored(
        cells.filter,
        |x| filter_stamp(x, sum, tail),
        JOINT_TOLERANCES,
    )?;
    let filter_slope = if tangent {
        factor.solve([0., 0., 1. / R60])?[2]
    } else {
        0.
    };
    Ok((
        Returns { volume, filter },
        [volume_slope, filter_slope],
        cv_readout,
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

#[cfg(all(test, pilot_audio_readout))]
mod tests {
    use super::*;

    #[cfg(pilot_shared_port_exp)]
    #[test]
    fn shared_exponential_preserves_zero_and_reverse_bias_slope() {
        let boundary = 0.125_f64;
        let samples = [-1000., -740., -40., -1.,
                       f64::from_bits((-boundary).to_bits() + 1), -boundary,
                       f64::from_bits((-boundary).to_bits() - 1), -1e-16, -0., 0., 1e-16,
                       f64::from_bits(boundary.to_bits() - 1), boundary,
                       f64::from_bits(boundary.to_bits() + 1), 1., 45.];
        for z in samples {
            let (current, slope) = exponential_pair(z);
            let wanted = z.exp_m1();
            assert!((current - wanted).abs() <= 16. * f64::EPSILON * wanted.abs(), "z={z}");
            assert_eq!(slope.to_bits(), z.exp().to_bits(), "z={z}");
            if z == 0. { assert_eq!(current.to_bits(), wanted.to_bits()); }
        }
    }

    const C2: f64 = 9.3;
    const VOLUME: [f64; 4] = [9.22, 8.65, 7.99, 8.65];

    fn split_solution(cathode: f64, base: f64) -> [f64; 3] {
        // Independent scalar bracket using the original imposed-x4 stamp.
        let row = |cv| {
            let (volume, _) =
                solve_factored(VOLUME, |x| volume_stamp(x, C2, cv, base), JOINT_TOLERANCES)
                    .unwrap();
            let diode = 1e-8 * ((cv - cathode) / (1.5 * VT)).exp_m1();
            let balance = (cv + 10.) / 16_900. + (cv - volume[2]) / 6800. + diode;
            (balance, [volume[2], cv, diode])
        };
        let [mut lo, mut hi] = [0., 1.4];
        assert!(row(lo).0 < 0. && row(hi).0 > 0.);
        for _ in 0..56 {
            let mid = (lo + hi) * 0.5;
            if row(mid).0 < 0. {
                lo = mid;
            } else {
                hi = mid;
            }
        }
        row((lo + hi) * 0.5).1
    }

    #[test]
    fn cv_closure_preserves_forward_cr6_current_and_r59_tangent() {
        let step = 1e-4;
        // Forward-bias DC vectors from circuit71_port_vectors, R61 = 200 Ω.
        for (cathode, base, x4, current) in [
            (
                0.01,
                4.306692675075283,
                0.42662327616933227,
                0.0004953573547700882,
            ),
            (
                0.7,
                4.307742421921254,
                1.1046024119902107,
                0.00036262045377491393,
            ),
        ] {
            let [q3, q2, x3, x2] = VOLUME;
            let (x, factor) = solve_factored(
                [q3, q2, x3, x2, cathode + 0.42],
                |x| closed_volume_stamp(x, C2, cathode, base),
                JOINT_TOLERANCES,
            )
            .unwrap();
            let (_, _, diode) = cv_law(x[4], x[2], cathode).unwrap();
            let expected = split_solution(cathode, base);
            assert!((x[2] - expected[0]).abs() <= 2e-12);
            assert!((x[4] - expected[1]).abs() <= 2e-12);
            assert!((diode - expected[2]).abs() <= 2e-15);
            assert!((x[4] - x4).abs() <= 1e-9);
            assert!(diode > 0. && (diode - current).abs() <= 1e-12);

            let slope = factor.solve([0., 0., 1. / R59, 0., 0.]).unwrap()[2];
            let low = split_solution(cathode, base - step)[0];
            let high = split_solution(cathode, base + step)[0];
            assert!((slope - (high - low) / (2. * step)).abs() <= 2e-8);
        }
    }

    #[cfg(pilot_r59_schur_follower)]
    #[test]
    fn schur_follower_preserves_all_five_rows_and_load_direction() {
        for (cathode, base) in [(0.01, 4.306692675075283), (0.7, 4.307742421921254)] {
            let [q3, q2, x3, x2] = VOLUME;
            let initial = [q3, q2, x3, x2, cathode + 0.42];
            let (x, factor) = close_volume_schur(initial, C2, cathode, base)
                .unwrap_or_else(|error| panic!("cathode {cathode}: {error:?}"));
            let original = closed_volume_stamp(x, C2, cathode, base).unwrap();
            let full = Lu::factor(original.j).unwrap();
            let (reference, _) = close_volume(initial, C2, cathode, base).unwrap();
            assert!(maximum(&original.f) <= JOINT_TOLERANCES[0]);
            assert!(maximum(&full.solve(original.f).unwrap()) <= JOINT_TOLERANCES[1]);
            let delta: [f64; 5] = std::array::from_fn(|i| x[i] - reference[i]);
            assert!(maximum(&delta) <= 2. * JOINT_TOLERANCES[1]);
            let load = [0., 0., 1. / R59, 0., 0.];
            let direction = factor.solve(load).unwrap();
            for (row, rhs) in original.j.iter().zip(load) {
                let value = row.iter().zip(direction).map(|(j, d)| j * d).sum::<f64>();
                assert!((value - rhs).abs() <= JOINT_TOLERANCES[0]);
            }
            let full_direction = full.solve(load).unwrap();
            let delta: [f64; 5] = std::array::from_fn(|i| direction[i] - full_direction[i]);
            assert!(maximum(&delta) <= JOINT_TOLERANCES[1]);
        }
    }

    #[cfg(pilot_r59_predict_cathode)]
    #[test]
    fn cathode_tangent_matches_centered_difference_at_forward_cr6_points() {
        let delta = 1e-5;
        for (cathode, base) in [(0.01, 4.306692675075283), (0.7, 4.307742421921254)] {
            let [q3, q2, x3, x2] = VOLUME;
            let initial = [q3, q2, x3, x2, cathode + 0.42];
            let (x, factor) = close_volume(initial, C2, cathode, base).unwrap();
            let direction = factor.solve(cathode_rhs(x[4], cathode).unwrap()).unwrap();
            let (low, _) = close_volume(x, C2, cathode - delta, base).unwrap();
            let (high, _) = close_volume(x, C2, cathode + delta, base).unwrap();
            for (k, analytical) in direction.into_iter().enumerate() {
                assert!((analytical - (high[k] - low[k]) / (2. * delta)).abs() <= 2e-8);
            }
        }
    }
}
