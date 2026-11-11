//! Pilot charge FOH with two explicit contour-voltage drives.
use crate::{pilot_law::{law, solve}, return_maps as map};
pub use crate::pilot_law::Error;
const JUNCTIONS: usize = map::IEXP.len();
const CHARGES: usize = map::F.len();
#[cfg(not(any(pilot_wide_returns, pilot_split_returns)))]
pub const DRIVE_RANGE: [f64; 2] = [0.015, 0.001];
#[cfg(pilot_wide_returns)]
pub const DRIVE_RANGE: [f64; 2] = [0.12, 0.003];
#[cfg(pilot_split_returns)]
pub const DRIVE_RANGE: [f64; 2] = map::SPLIT_RANGE;

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
    q: [f64; CHARGES],
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
    pub loads_v: [f64; 2], // VCA base and ladder TAIL, at the accepted endpoint.
}

#[cfg(pilot_receiver_ports)]
pub struct Trial {
    pub state: State,
    pub ports: Ports,
    /// Rows are VCA base/TAIL, columns are R59/R60 source voltage, in V/V.
    pub load_jacobian: [[f64; 2]; 2],
}

pub(crate) struct Prepared {
    old: State,
    stored: [f64; CHARGES],
    correction: [f64; CHARGES],
}

impl Prepared {
    pub(crate) fn new(old: State) -> Self {
        Self {
            old,
            stored: product(&F, &old.q),
            correction: product(&N0, &old.defects),
        }
    }

    pub(crate) fn solve_root(
        &self,
        signal: f64,
        drive: Drive,
        seed: Option<[f64; JUNCTIONS]>,
    ) -> Result<Root, Error> {
        let state = &self.old;
        if !drive.valid() || !signal.is_finite() || signal.abs() > 0.08 {
            return Err(Error::Input);
        }
        let input = [signal, drive.volume_delta_v, drive.filter_delta_v];
        let stored = &self.stored;
        let correction = &self.correction;
        let base: [f64; CHARGES] = std::array::from_fn(|i| {
            dot(&map::U0[i], &state.input) + dot(&map::U1[i], &input) + stored[i] + correction[i]
        });
        let history = product(&ZH, &base);
        let predictor: [f64; JUNCTIONS] =
            std::array::from_fn(|i| history[i] + dot(&map::ZU[i], &input));
        #[cfg(not(pilot_block_roots))]
        let previous = product(&P, &state.defects);
        #[cfg(pilot_block_roots)]
        let previous = state.feedback;
        let mut z = seed.unwrap_or_else(|| std::array::from_fn(|i| predictor[i] - previous[i]));
        for _iteration in 0..12 {
            let (defects, slope) = law(z)?;
            let feedback = product(&P, &defects);
            let residual: [f64; JUNCTIONS] =
                std::array::from_fn(|i| z[i] - predictor[i] + feedback[i]);
            if residual.iter().all(|x| x.abs() <= 2e-13) {
                return Ok(Root {
                    base,
                    input,
                    defects,
                    #[cfg(pilot_block_roots)]
                    feedback,
                    #[cfg(pilot_receiver_ports)]
                    junction: z,
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
}

pub(crate) struct Root {
    base: [f64; CHARGES],
    input: [f64; 3],
    defects: [f64; JUNCTIONS],
    #[cfg(pilot_block_roots)]
    feedback: [f64; JUNCTIONS],
    #[cfg(pilot_receiver_ports)]
    pub(crate) junction: [f64; JUNCTIONS],
}

impl Root {
    #[cfg(any(not(pilot_receiver_packed), pilot_receiver_ports))]
    fn readout_node(&self, node: usize) -> f64 {
        map::DC[node] + dot(&map::XQ[node], &self.base) + dot(&map::XU[node], &self.input)
            - dot(&map::XD[node], &self.defects)
    }

    #[cfg(pilot_receiver_ports)]
    pub(crate) fn vca_base(&self) -> Result<f64, Error> {
        let voltage = self.readout_node(3);
        voltage.is_finite().then_some(voltage).ok_or(Error::Domain)
    }

    pub(crate) fn r59_source_v(&self) -> f64 {
        #[cfg(not(pilot_split_returns))]
        let bias = 2.;
        #[cfg(pilot_split_returns)]
        let bias = map::SPLIT_CENTER[0];
        bias + self.input[1]
    }

    #[cfg(pilot_receiver_ports)]
    pub(crate) fn load_jacobian(&self) -> Result<[[f64; 2]; 2], Error> {
        let (_, slope) = law(self.junction)?;
        let jacobian = std::array::from_fn(|i| {
            std::array::from_fn(|j| f64::from(i == j) + map::P[i][j] * slope[j])
        });
        let factor =
            crate::port_lu::Lu::<JUNCTIONS>::factor(jacobian).map_err(|_| Error::Singular)?;
        let mut load_jacobian = [[0.; 2]; 2];
        for column in 0..2 {
            let input = column + 1;
            let charge_drive: [f64; CHARGES] = std::array::from_fn(|i| map::U1[i][input]);
            let right =
                std::array::from_fn(|i| dot(&map::ZH[i], &charge_drive) + map::ZU[i][input]);
            let direction = factor.solve(right).map_err(|_| Error::Singular)?;
            let defect_drive = std::array::from_fn(|i| slope[i] * direction[i]);
            for row in 0..2 {
                let node = row + 3;
                load_jacobian[row][column] = dot(&map::XQ[node], &charge_drive)
                    + map::XU[node][input]
                    - dot(&map::XD[node], &defect_drive);
            }
        }
        if load_jacobian.iter().flatten().any(|v| !v.is_finite()) {
            return Err(Error::Domain);
        }
        Ok(load_jacobian)
    }

    pub(crate) fn finish(&self) -> Result<(State, Ports), Error> {
        let charge = product(&N1, &self.defects);
        let q: [f64; CHARGES] = std::array::from_fn(|i| self.base[i] + charge[i]);
        #[cfg(pilot_receiver_packed)]
        let nodes = packed::readout(&self.base, &self.input, &self.defects);
        #[cfg(not(pilot_receiver_packed))]
        let nodes = std::array::from_fn(|i| self.readout_node(i));
        if q.iter().chain(&nodes).any(|v| !v.is_finite()) {
            return Err(Error::Domain);
        }
        let [j7_v, bus_v, base_v, vca_base, tail, collector] = nodes;
        let state = State {
            q,
            input: self.input,
            defects: self.defects,
            #[cfg(pilot_block_roots)]
            feedback: self.feedback,
        };
        let ports = Ports {
            j7_v,
            bus_v,
            base_v,
            panel_a: (bus_v - 0.5 * self.input[0]) / 39_250.,
            returns_a: [(self.r59_source_v() - vca_base) / 68_000., (tail - collector) / 680.],
            loads_v: [vca_base, tail],
        };
        Ok((state, ports))
    }
}

#[cfg(pilot_receiver_ports)]
pub fn trial_with_load_tangent(old: State, signal: f64, drive: Drive) -> Result<Trial, Error> {
    let root = Prepared::new(old).solve_root(signal, drive, None)?;
    let (state, ports) = root.finish()?;
    let load_jacobian = root.load_jacobian()?;
    Ok(Trial {
        state,
        ports,
        load_jacobian,
    })
}

impl State {
    pub fn dc(index: usize) -> Result<Self, Error> {
        if index != 1 {
            return Err(Error::Input);
        }
        Ok(Self { q: [0.; CHARGES], input: [0.; 3], defects: [0.; JUNCTIONS],
                  #[cfg(pilot_block_roots)] feedback: [0.; JUNCTIONS] })
    }

    #[cfg(all(pilot_split_returns, pilot_receiver_handoff))]
    pub fn from_nodal(
        high: &[f64; 68],
        low: &[f64; 68],
        signal: f64,
        drive: Drive,
    ) -> Result<Self, Error> {
        if !drive.valid() || !signal.is_finite() || signal.abs() > 0.08
            || high.iter().chain(low).any(|v| !v.is_finite())
        {
            return Err(Error::Input);
        }
        let offset = std::array::from_fn(|k| {
            (high[k] - map::INIT_DC_HIGH[k]) + (low[k] - map::INIT_DC_LOW[k])
        });
        let q = map::INIT_CHARGE.each_ref().map(|row| dot(row, &offset));
        let junction = map::INIT_JUNCTION.each_ref().map(|row| dot(row, &offset));
        let (defects, _) = law(junction)?;
        #[cfg(pilot_block_roots)]
        let feedback = product(&P, &defects);
        if q.iter().chain(&defects).any(|v| !v.is_finite()) {
            return Err(Error::Domain);
        }
        #[cfg(pilot_block_roots)]
        if feedback.iter().any(|v| !v.is_finite()) {
            return Err(Error::Domain);
        }
        Ok(Self {
            q,
            input: [signal, drive.volume_delta_v, drive.filter_delta_v],
            defects,
            #[cfg(pilot_block_roots)] feedback,
        })
    }

    #[cfg(all(pilot_split_returns, pilot_receiver_handoff))]
    pub fn capacitor_charge_offsets_c(&self) -> [f64; CHARGES] {
        std::array::from_fn(|k| self.q[k] * map::INIT_CAPACITANCE[k])
    }
}

fn dot<const N: usize>(a: &[f64; N], b: &[f64; N]) -> f64 {
    a.iter().zip(b).map(|(x, y)| x * y).sum()
}

#[cfg(all(not(pilot_returns_simd), not(pilot_receiver_packed)))]
use map::{F, N0, N1, P, ZH};

#[cfg(all(not(pilot_returns_simd), not(pilot_receiver_packed)))]
fn product<const R: usize, const C: usize>(matrix: &[[f64; C]; R], input: &[f64; C]) -> [f64; R] {
    matrix.each_ref().map(|row| dot(row, input))
}

#[cfg(all(pilot_returns_simd, pilot_receiver_packed))]
compile_error!("Select one receiver matrix layout");

#[cfg(pilot_receiver_packed)]
#[path = "rf_d_pilot_packed_products.rs"]
mod packed;
#[cfg(pilot_receiver_packed)]
use self::packed::{product, F, N0, N1, P, ZH};

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
    const { assert!(JUNCTIONS == 18 || JUNCTIONS == 34) };
    let mut direction = [0.; JUNCTIONS / 2];
    solve_group::<4>(0, residual, slope, &mut direction)?;
    solve_group::<2>(4, residual, slope, &mut direction)?;
    solve_group::<3>(6, residual, slope, &mut direction)?;
    if JUNCTIONS == 34 {
        solve_group::<8>(9, residual, slope, &mut direction)?;
    }
    Ok(direction)
}

pub fn step(state: &mut State, signal: f64, drive: Drive) -> Result<Ports, Error> {
    let (next, ports) = Prepared::new(*state)
        .solve_root(signal, drive, None)?
        .finish()?;
    *state = next;
    Ok(ports)
}
