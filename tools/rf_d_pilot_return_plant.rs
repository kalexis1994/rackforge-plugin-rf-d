//! Pilot charge FOH with two explicit contour-voltage drives.
use crate::{pilot_law::{law, solve}, return_maps as map};
pub use crate::pilot_law::Error;
const JUNCTIONS: usize = map::IEXP.len();
#[cfg(not(pilot_wide_returns))]
pub const DRIVE_RANGE: [f64; 2] = [0.015, 0.001];
#[cfg(pilot_wide_returns)]
pub const DRIVE_RANGE: [f64; 2] = [0.12, 0.003];

#[derive(Clone, Copy, Default)]
pub struct Drive {
    pub volume_delta_v: f64,
    pub filter_delta_v: f64,
}

impl Drive {
    pub fn valid(self) -> bool {
        self.volume_delta_v.abs() <= DRIVE_RANGE[0] && self.filter_delta_v.abs() <= DRIVE_RANGE[1]
    }

    pub fn interpolate(self, end: Self, fraction: f64) -> Self {
        Self {
            volume_delta_v: (1. - fraction) * self.volume_delta_v + fraction * end.volume_delta_v,
            filter_delta_v: (1. - fraction) * self.filter_delta_v + fraction * end.filter_delta_v,
        }
    }
}

#[derive(Clone, Copy)]
pub struct State {
    q: [f64; 18],
    input: [f64; 3],
    defects: [f64; JUNCTIONS],
    #[cfg(pilot_block_roots)]
    feedback: [f64; JUNCTIONS],
}

#[derive(Clone, Copy)]
pub struct Ports {
    pub j7_v: f64,
    pub bus_v: f64,
    pub base_v: f64,
    pub panel_a: f64,
    pub returns_a: [f64; 2],
}

impl State {
    pub fn dc(index: usize) -> Result<Self, Error> {
        if index != 1 {
            return Err(Error::Input);
        }
        Ok(Self { q: [0.; 18], input: [0.; 3], defects: [0.; JUNCTIONS],
                  #[cfg(pilot_block_roots)] feedback: [0.; JUNCTIONS] })
    }
}

fn dot<const N: usize>(a: &[f64; N], b: &[f64; N]) -> f64 {
    a.iter().zip(b).map(|(x, y)| x * y).sum()
}

#[cfg(not(pilot_returns_simd))]
use map::{F, N0, N1, P, ZH};

#[cfg(not(pilot_returns_simd))]
fn product<const R: usize, const C: usize>(matrix: &[[f64; C]; R], input: &[f64; C]) -> [f64; R] {
    matrix.each_ref().map(|row| dot(row, input))
}

#[cfg(pilot_returns_simd)]
#[path = "recovery_engine128_broadcast.rs"]
mod broadcast;

#[cfg(pilot_returns_simd)]
use self::wasm::{product, F, N0, N1, P, ZH};

#[cfg(pilot_returns_simd)]
mod wasm {
    use super::{broadcast::accumulate, map, JUNCTIONS};

    const N: usize = 18;
    const _: () = assert!(JUNCTIONS == N);
    type Matrix = [[f64; N]; N];

    const fn transpose(matrix: &Matrix) -> Matrix {
        let mut columns = [[0.; N]; N];
        let mut row = 0;
        while row < N {
            let mut col = 0;
            while col < N {
                columns[col][row] = matrix[row][col];
                col += 1;
            }
            row += 1;
        }
        columns
    }

    pub const F: Matrix = transpose(&map::F);
    pub const N0: Matrix = transpose(&map::N0);
    pub const N1: Matrix = transpose(&map::N1);
    pub const P: Matrix = transpose(&map::P);
    pub const ZH: Matrix = transpose(&map::ZH);

    #[inline]
    pub fn product(matrix: &Matrix, input: &[f64; N]) -> [f64; N] {
        let mut output = [-0.; N];
        accumulate::<N, N, 9, false>(&mut output, matrix, input);
        output
    }
}

#[cfg(pilot_block_roots)]
fn solve_group<const SIZE: usize>(
    start: usize,
    residual: &[f64; JUNCTIONS],
    slope: &[f64; JUNCTIONS],
    direction: &mut [f64; JUNCTIONS / 2],
) -> Result<(), Error> {
    let mut a: [[f64; SIZE]; SIZE] = std::array::from_fn(|i| {
        let row = 2 * (start + i);
        std::array::from_fn(|j| {
            let col = 2 * (start + j);
            f64::from(i == j) + map::P[row][col] * slope[col]
        })
    });
    let mut b: [f64; SIZE] = std::array::from_fn(|i| {
        let row = 2 * (start + i);
        (0..start).fold(residual[row], |r, j| {
            r - map::P[row][2 * j] * slope[2 * j] * direction[j]
        })
    });
    for k in 0..SIZE {
        let mut pivot = k;
        for i in k + 1..SIZE {
            if a[i][k].abs() > a[pivot][k].abs() {
                pivot = i;
            }
        }
        if a[pivot][k].abs() < 1e-28 {
            return Err(Error::Singular);
        }
        a.swap(k, pivot);
        b.swap(k, pivot);
        for i in k + 1..SIZE {
            let factor = a[i][k] / a[k][k];
            for j in k + 1..SIZE {
                a[i][j] -= factor * a[k][j];
            }
            b[i] -= factor * b[k];
        }
    }
    for i in (0..SIZE).rev() {
        let rhs = (i + 1..SIZE).fold(b[i], |v, j| v - a[i][j] * direction[start + j]);
        direction[start + i] = rhs / a[i][i];
    }
    Ok(())
}

fn full_direction(residual: &[f64; JUNCTIONS], slope: &[f64; JUNCTIONS]) -> Result<[f64; JUNCTIONS / 2], Error> {
    solve(
        std::array::from_fn(|i| std::array::from_fn(|j| {
            f64::from(i == j) + map::P[2 * i][2 * j] * slope[2 * j]
        })),
        std::array::from_fn(|i| residual[2 * i]),
    )
}

#[cfg(pilot_block_roots)]
fn block_direction(residual: &[f64; JUNCTIONS], slope: &[f64; JUNCTIONS]) -> Result<[f64; JUNCTIONS / 2], Error> {
    const { assert!(JUNCTIONS == 18) };
    let mut direction = [0.; JUNCTIONS / 2];
    solve_group::<4>(0, residual, slope, &mut direction)?;
    solve_group::<2>(4, residual, slope, &mut direction)?;
    solve_group::<3>(6, residual, slope, &mut direction)?;
    Ok(direction)
}

pub fn step(state: &mut State, signal: f64, drive: Drive) -> Result<Ports, Error> {
    if !drive.valid() || !signal.is_finite() || signal.abs() > 0.08 {
        return Err(Error::Input);
    }
    let input = [signal, drive.volume_delta_v, drive.filter_delta_v];
    let stored = product(&F, &state.q);
    let correction = product(&N0, &state.defects);
    let base: [f64; 18] = std::array::from_fn(|i| {
        dot(&map::U0[i], &state.input) + dot(&map::U1[i], &input) + stored[i] + correction[i]
    });
    let history = product(&ZH, &base);
    let predictor: [f64; JUNCTIONS] = std::array::from_fn(|i| history[i] + dot(&map::ZU[i], &input));
    #[cfg(not(pilot_block_roots))]
    let previous = product(&P, &state.defects);
    #[cfg(pilot_block_roots)]
    let previous = state.feedback;
    let mut z = std::array::from_fn(|i| predictor[i] - previous[i]);
    for _iteration in 0..12 {
        let (defects, slope) = law(z)?;
        let feedback = product(&P, &defects);
        let residual: [f64; JUNCTIONS] = std::array::from_fn(|i| z[i] - predictor[i] + feedback[i]);
        if residual.iter().all(|x| x.abs() <= 2e-13) {
            let charge = product(&N1, &defects);
            let q: [f64; 18] = std::array::from_fn(|i| base[i] + charge[i]);
            let [j7_v, bus_v, base_v, vca_base, tail, collector] = std::array::from_fn(|i| {
                map::DC[i] + dot(&map::XQ[i], &base) + dot(&map::XU[i], &input) - dot(&map::XD[i], &defects)
            });
            if q.iter().chain(&[j7_v, bus_v, base_v, vca_base, tail, collector]).any(|v| !v.is_finite()) {
                return Err(Error::Domain);
            }
            *state = State { q, input, defects, #[cfg(pilot_block_roots)] feedback };
            return Ok(Ports {
                j7_v, bus_v, base_v, panel_a: (bus_v - 0.5 * signal) / 39_250.,
                returns_a: [(2. + drive.volume_delta_v - vca_base) / 68_000., (tail - collector) / 680.],
            });
        }
        // Same modified-Newton preconditioner as the original pilot.
        #[cfg(not(pilot_block_roots))]
        let even = full_direction(&residual, &slope)?;
        #[cfg(pilot_block_roots)]
        let even = if _iteration < 2 {
            block_direction(&residual, &slope).or_else(|_| full_direction(&residual, &slope))?
        } else {
            full_direction(&residual, &slope)?
        };
        for i in 0..JUNCTIONS / 2 {
            let mut odd = residual[2 * i + 1];
            for j in 0..JUNCTIONS / 2 {
                odd -= map::P[2 * i + 1][2 * j] * slope[2 * j] * even[j];
            }
            z[2 * i] -= even[i];
            z[2 * i + 1] -= odd;
        }
    }
    Err(Error::RootBudget)
}
