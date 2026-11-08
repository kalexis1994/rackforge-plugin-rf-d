//! Pilot charge FOH with two explicit contour-voltage drives.
use crate::{pilot_law::{law, solve}, return_maps as map};
pub use crate::pilot_law::Error;
const JUNCTIONS: usize = 18;

#[derive(Clone, Copy, Default)]
pub struct Drive {
    pub volume_delta_v: f64,
    pub filter_delta_v: f64,
}

impl Drive {
    pub fn valid(self) -> bool {
        self.volume_delta_v.abs() <= 0.015 && self.filter_delta_v.abs() <= 0.001
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
        Ok(Self { q: [0.; 18], input: [0.; 3], defects: [0.; JUNCTIONS] })
    }
}

fn dot<const N: usize>(a: &[f64; N], b: &[f64; N]) -> f64 {
    a.iter().zip(b).map(|(x, y)| x * y).sum()
}

pub fn step(state: &mut State, signal: f64, drive: Drive) -> Result<Ports, Error> {
    if !drive.valid() || !signal.is_finite() || signal.abs() > 0.08 {
        return Err(Error::Input);
    }
    let input = [signal, drive.volume_delta_v, drive.filter_delta_v];
    let base: [f64; 18] = std::array::from_fn(|i| {
        dot(&map::U0[i], &state.input) + dot(&map::U1[i], &input)
            + dot(&map::F[i], &state.q) + dot(&map::N0[i], &state.defects)
    });
    let predictor: [f64; JUNCTIONS] = std::array::from_fn(|i| dot(&map::ZH[i], &base) + dot(&map::ZU[i], &input));
    let mut z = std::array::from_fn(|i| predictor[i] - dot(&map::P[i], &state.defects));
    for _ in 0..12 {
        let (defects, slope) = law(z)?;
        let residual: [f64; JUNCTIONS] = std::array::from_fn(|i| z[i] - predictor[i] + dot(&map::P[i], &defects));
        if residual.iter().all(|x| x.abs() <= 2e-13) {
            let q: [f64; 18] = std::array::from_fn(|i| base[i] + dot(&map::N1[i], &defects));
            let [j7_v, bus_v, base_v, vca_base, tail, collector] = std::array::from_fn(|i| {
                map::DC[i] + dot(&map::XQ[i], &base) + dot(&map::XU[i], &input) - dot(&map::XD[i], &defects)
            });
            if q.iter().chain(&[j7_v, bus_v, base_v, vca_base, tail, collector]).any(|v| !v.is_finite()) {
                return Err(Error::Domain);
            }
            *state = State { q, input, defects };
            return Ok(Ports {
                j7_v, bus_v, base_v, panel_a: (bus_v - 0.5 * signal) / 39_250.,
                returns_a: [(2. + drive.volume_delta_v - vca_base) / 68_000., (tail - collector) / 680.],
            });
        }
        // Same modified-Newton preconditioner as the original pilot.
        let even = solve(
            std::array::from_fn(|i| std::array::from_fn(|j| {
                f64::from(i == j) + map::P[2 * i][2 * j] * slope[2 * j]
            })),
            std::array::from_fn(|i| residual[2 * i]),
        )?;
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
