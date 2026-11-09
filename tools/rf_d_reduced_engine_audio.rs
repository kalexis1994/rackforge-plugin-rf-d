//! Schur response of the audio arm and its retained exponential remainders.
use crate::{
    graph,
    reduced_lu::{dot, maximum, row_product, Lu},
    StepError,
};

pub const NODES: usize = 64;
pub const SHARED: usize = 6;
pub const STAGE_LAWS: usize = 54;
const LAWS: usize = 2 * STAGE_LAWS;
const HISTORY: usize = NODES + 1;
pub const NODE: [usize; NODES] = {
    let mut nodes = [0; NODES];
    let mut i = 0;
    while i < NODES {
        nodes[i] = graph::chain_index(if i < 62 { i } else { i + 4 });
        i += 1;
    }
    nodes
};

pub struct Map {
    bias: [f64; LAWS],
    iexp: [f64; LAWS],
    z_history: [[f64; HISTORY]; LAWS],
    z_port: [[f64; SHARED]; LAWS],
    feedback: LawMatrix,
    feedback_peak: LawVector,
    i_history: [[f64; HISTORY]; SHARED],
    i_port: [[f64; SHARED]; SHARED],
    i_law: [[f64; LAWS]; SHARED],
    x_history: [[f64; HISTORY]; NODES],
    x_port: [[f64; SHARED]; NODES],
    x_law: [[f64; LAWS]; NODES],
}

pub struct History {
    junction: [f64; LAWS],
    current: [f64; SHARED],
    coordinates: [f64; HISTORY],
}

pub struct Response {
    pub current: [f64; SHARED],
    nonlinear: [f64; LAWS],
    exponential_change: Junctions,
    pub junctions: Junctions,
}

pub fn read_array<const N: usize>(bytes: &mut &[u8]) -> [f64; N] {
    std::array::from_fn(|_| {
        let (item, tail) = bytes.split_at(8);
        *bytes = tail;
        f64::from_le_bytes(item.try_into().unwrap())
    })
}

fn read_matrix<const R: usize, const C: usize>(bytes: &mut &[u8]) -> [[f64; C]; R] {
    std::array::from_fn(|_| read_array(bytes))
}

fn excess(z: f64, change: f64) -> f64 {
    if z.abs() >= 1e-3 {
        return change - z;
    }
    z * z
        * (0.5
            + z * (1. / 6.
                + z * (1. / 24.
                    + z * (1. / 120.
                        + z * (1. / 720. + z * (1. / 5040. + z * (1. / 40320. + z / 362880.)))))))
}

pub type Junctions = [f64; LAWS];
type LawVector = Junctions;
type LawMatrix = [LawVector; LAWS];
pub type PortJacobian = [[f64; SHARED]; SHARED];

// The largest columns precondition the same full linear system. The
// omitted columns still participate in the residual at each refinement.
const SUPPORT: usize = 56;
const COLUMN_FLOOR: f64 = 5e-4;

fn refinement_residual<const K: usize>(
    coefficients: &LawMatrix,
    weighted: &[[f64; K]; LAWS],
    rhs: &[[f64; K]; LAWS],
    x: &[[f64; K]; LAWS],
) -> [[f64; K]; LAWS] {
    #[cfg(all(target_arch = "x86_64", target_feature = "avx"))]
    if K == SHARED {
        return tangent_residual(coefficients, weighted, rhs, x);
    }
    std::array::from_fn(|i| {
        let feedback = row_product(&coefficients[i], weighted);
        std::array::from_fn(|k| rhs[i][k] - x[i][k] - feedback[k])
    })
}

#[cfg(all(target_arch = "x86_64", target_feature = "avx"))]
fn tangent_residual<const K: usize>(
    coefficients: &LawMatrix,
    weighted: &[[f64; K]; LAWS],
    rhs: &[[f64; K]; LAWS],
    x: &[[f64; K]; LAWS],
) -> [[f64; K]; LAWS] {
    use std::arch::x86_64::*;

    const TILE: usize = 4;
    const _: () = assert!(LAWS % TILE == 0);
    assert_eq!(K, SHARED);
    let (tiles, _) = coefficients.as_chunks::<TILE>();
    let mut result = [[0.; K]; LAWS];
    let (output, _) = result.as_chunks_mut::<TILE>();
    // Each row has four AVX lanes and two SSE lanes. Each lane keeps
    // the scalar summation order, with separate multiply and add.
    // SAFETY: AVX is enabled and each load/store covers exactly one six-lane row.
    unsafe {
        for (t, (tile, output)) in tiles.iter().zip(output).enumerate() {
            let mut first = [_mm256_setzero_pd(); TILE];
            let mut last = [_mm_setzero_pd(); TILE];
            for (i, input) in weighted.iter().enumerate() {
                let low = _mm256_loadu_pd(input.as_ptr());
                let high = _mm_loadu_pd(input.as_ptr().add(4));
                for r in 0..TILE {
                    let coefficient = tile[r][i];
                    first[r] =
                        _mm256_add_pd(first[r], _mm256_mul_pd(_mm256_set1_pd(coefficient), low));
                    last[r] = _mm_add_pd(last[r], _mm_mul_pd(_mm_set1_pd(coefficient), high));
                }
            }
            for (r, row) in output.iter_mut().enumerate() {
                let i = t * TILE + r;
                let b = rhs[i].as_ptr();
                let a = x[i].as_ptr();
                let low = _mm256_sub_pd(_mm256_loadu_pd(b), _mm256_loadu_pd(a));
                let high = _mm_sub_pd(_mm_loadu_pd(b.add(4)), _mm_loadu_pd(a.add(4)));
                _mm256_storeu_pd(row.as_mut_ptr(), _mm256_sub_pd(low, first[r]));
                _mm_storeu_pd(row.as_mut_ptr().add(4), _mm_sub_pd(high, last[r]));
            }
        }
    }
    result
}

struct Projection {
    columns: [usize; SUPPORT],
    slots: [usize; LAWS],
    count: usize,
    coupling: [[f64; SUPPORT]; LAWS],
    factor: Lu<SUPPORT>,
}

impl Projection {
    fn new(port_map: &LawMatrix, peak: &LawVector, slope: &LawVector) -> Option<Self> {
        let mut columns = [0; SUPPORT];
        let mut count = 0;
        let mut slots = [SUPPORT; LAWS];
        for (col, (&maximum, &derivative)) in peak.iter().zip(slope).enumerate() {
            if maximum * derivative.abs() > COLUMN_FLOOR {
                *columns.get_mut(count)? = col;
                slots[col] = count;
                count += 1;
            }
        }
        let mut coupling = [[0.; SUPPORT]; LAWS];
        for (row, weights) in port_map.iter().zip(&mut coupling) {
            for (weight, &col) in weights.iter_mut().zip(&columns[..count]) {
                *weight = row[col] * slope[col];
            }
        }
        let factor = Lu::factor_prefix(
            std::array::from_fn(|i| {
                std::array::from_fn(|j| {
                    f64::from(i == j)
                        + if i < count {
                            coupling[columns[i]][j]
                        } else {
                            0.
                        }
                })
            }),
            count,
        )
        .ok()?;
        Some(Self {
            columns,
            slots,
            count,
            coupling,
            factor,
        })
    }

    fn apply<const K: usize>(&self, rhs: &[[f64; K]; LAWS]) -> Option<[[f64; K]; LAWS]> {
        let strong = self
            .factor
            .solve_batch_prefix(
                &std::array::from_fn(|j| {
                    if j < self.count {
                        rhs[self.columns[j]]
                    } else {
                        [0.; K]
                    }
                }),
                self.count,
            )
            .ok()?;
        Some(std::array::from_fn(|i| {
            if let Some(solution) = strong.get(self.slots[i]) {
                return *solution;
            }
            let change = row_product(&self.coupling[i][..self.count], &strong[..self.count]);
            std::array::from_fn(|k| rhs[i][k] - change[k])
        }))
    }

    fn refine<const K: usize>(
        &self,
        port_map: &LawMatrix,
        slope: &LawVector,
        rhs: &[[f64; K]; LAWS],
    ) -> Option<[[f64; K]; LAWS]> {
        let mut limits = [0_f64; K];
        for row in rhs {
            for (limit, v) in limits.iter_mut().zip(row) {
                *limit = limit.max(v.abs());
            }
        }
        limits = limits.map(|v| 1e-14 + 2e-13 * v);
        let mut x = self.apply(rhs)?;
        let mut converged = [false; K];
        for _ in 0..5 {
            let weighted: [[f64; K]; LAWS] = std::array::from_fn(|i| x[i].map(|v| slope[i] * v));
            let mut residual = refinement_residual(port_map, &weighted, rhs, &x);
            for k in 0..K {
                converged[k] |= residual
                    .iter()
                    .all(|r| r[k].is_finite() && r[k].abs() <= limits[k]);
            }
            if converged.iter().all(|&done| done) {
                return Some(x);
            }
            for row in &mut residual {
                for (v, done) in row.iter_mut().zip(converged) {
                    if done {
                        *v = 0.;
                    }
                }
            }
            let correction = self.apply(&residual)?;
            for (value, delta) in x.iter_mut().zip(correction) {
                for k in 0..K {
                    if !converged[k] {
                        value[k] += delta[k];
                    }
                }
            }
        }
        None
    }
}

fn feedback_directions<const K: usize>(
    port_map: &LawMatrix,
    peak: &LawVector,
    slope: &LawVector,
    rhs: &[[f64; K]; LAWS],
) -> Result<[[f64; K]; LAWS], StepError> {
    if let Some(direction) = Projection::new(port_map, peak, slope)
        .and_then(|projection| projection.refine(port_map, slope, rhs))
    {
        return Ok(direction);
    }
    let matrix = std::array::from_fn(|row| {
        std::array::from_fn(|col| port_map[row][col] * slope[col] + f64::from(row == col))
    });
    Lu::factor(matrix)?.solve_batch(rhs)
}

impl Map {
    pub const BYTES: usize = 8
        * (2 * LAWS
            + LAWS * (HISTORY + SHARED + LAWS)
            + (NODES + SHARED) * (HISTORY + SHARED + LAWS));

    pub fn read(bytes: &mut &[u8]) -> Self {
        let mut map = Self {
            bias: read_array(bytes),
            iexp: read_array(bytes),
            z_history: read_matrix(bytes),
            z_port: read_matrix(bytes),
            feedback: read_matrix(bytes),
            feedback_peak: [0.; LAWS],
            i_history: read_matrix(bytes),
            i_port: read_matrix(bytes),
            i_law: read_matrix(bytes),
            x_history: read_matrix(bytes),
            x_port: read_matrix(bytes),
            x_law: read_matrix(bytes),
        };
        for row in &map.feedback {
            for (peak, coefficient) in map.feedback_peak.iter_mut().zip(row) {
                *peak = peak.max(coefficient.abs());
            }
        }
        map
    }

    pub fn history(&self, offset: [f64; NODES]) -> History {
        let coordinates = std::array::from_fn(|i| if i < NODES { offset[i] } else { 1. });
        History {
            junction: self.z_history.each_ref().map(|row| dot(row, &coordinates)),
            current: self.i_history.each_ref().map(|row| dot(row, &coordinates)),
            coordinates,
        }
    }

    pub fn response(
        &self,
        history: &History,
        ports: &[f64; SHARED],
        seed: &Junctions,
    ) -> Result<Response, StepError> {
        let drive = std::array::from_fn(|i| history.junction[i] + dot(&self.z_port[i], ports));
        self.solve_response(history, ports, &drive, *seed)
            .or_else(|_| self.solve_response(history, ports, &drive, drive))
    }

    fn solve_response(
        &self,
        history: &History,
        ports: &[f64; SHARED],
        drive: &Junctions,
        mut z: Junctions,
    ) -> Result<Response, StepError> {
        for _ in 0..16 {
            if z.iter()
                .zip(&self.bias)
                .any(|(v, bias)| !v.is_finite() || bias + v > 45.)
            {
                return Err(StepError::ExponentialDomain);
            }
            let change = z.map(f64::exp_m1);
            let nonlinear = std::array::from_fn(|i| self.iexp[i] * excess(z[i], change[i]));
            let residual: [f64; LAWS] =
                std::array::from_fn(|i| z[i] - drive[i] + dot(&self.feedback[i], &nonlinear));
            if maximum(&residual) > 2e-13 {
                let slope = std::array::from_fn(|i| self.iexp[i] * change[i]);
                let correction = feedback_directions(
                    &self.feedback,
                    &self.feedback_peak,
                    &slope,
                    &residual.map(|v| [v]),
                )?;
                for (value, [delta]) in z.iter_mut().zip(correction) {
                    *value -= delta;
                }
                continue;
            }
            let current = std::array::from_fn(|i| {
                history.current[i] + dot(&self.i_port[i], ports) + dot(&self.i_law[i], &nonlinear)
            });
            if current.iter().any(|x| !x.is_finite()) {
                return Err(StepError::ExponentialDomain);
            }
            return Ok(Response {
                current,
                nonlinear,
                exponential_change: change,
                junctions: z,
            });
        }
        Err(StepError::IterationBudget)
    }

    pub fn jacobian(&self, response: &Response) -> Result<PortJacobian, StepError> {
        let slope = std::array::from_fn(|i| self.iexp[i] * response.exponential_change[i]);
        let mut derivatives =
            feedback_directions(&self.feedback, &self.feedback_peak, &slope, &self.z_port)?;
        for (row, scale) in derivatives.iter_mut().zip(slope) {
            for value in row {
                *value *= scale;
            }
        }
        let mut jacobian = self.i_port;
        for (row, coefficient) in jacobian.iter_mut().zip(&self.i_law) {
            for (value, delta) in row.iter_mut().zip(row_product(coefficient, &derivatives)) {
                *value += delta;
            }
        }
        Ok(jacobian)
    }

    pub fn endpoint(
        &self,
        history: &History,
        ports: &[f64; SHARED],
        response: &Response,
    ) -> [f64; NODES] {
        std::array::from_fn(|i| {
            dot(&self.x_history[i], &history.coordinates)
                + dot(&self.x_port[i], ports)
                + dot(&self.x_law[i], &response.nonlinear)
        })
    }
}
