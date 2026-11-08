//! Schur response of the audio arm and its retained exponential remainders.
use crate::{
    graph,
    reduced_lu::{dot, maximum, Lu},
    StepError,
};

pub const NODES: usize = 64;
pub const SHARED: usize = 6;
const LAWS: usize = 108;
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
    feedback: [[f64; LAWS]; LAWS],
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
    pub jacobian: [[f64; SHARED]; SHARED],
    nonlinear: [f64; LAWS],
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

type LawVector = [f64; LAWS];
type LawMatrix = [LawVector; LAWS];

/// Solve (I + P diag(slope)) x = rhs with a certified short series when
/// the feedback is contractive. Preserve the scaled-pivot route otherwise.
struct Feedback {
    weights: LawMatrix,
    norm: f64,
}

impl Feedback {
    fn new(port_map: &LawMatrix, slope: &LawVector) -> Self {
        let weights = port_map.map(|row| std::array::from_fn(|j| row[j] * slope[j]));
        let norm = weights
            .iter()
            .map(|row| row.iter().map(|v| v.abs()).sum::<f64>())
            .fold(0., f64::max);
        Self { weights, norm }
    }

    fn series(&self, rhs: LawVector) -> Option<LawVector> {
        if self.norm > 0.125 || !self.norm.is_finite() {
            return None;
        }
        let limit = (1. - self.norm) * (1e-14 + 2e-13 * maximum(&rhs));
        let mut x = rhs;
        for _ in 0..8 {
            let next = std::array::from_fn(|i| rhs[i] - dot(&self.weights[i], &x));
            if (0..LAWS).all(|i| next[i].is_finite() && (next[i] - x[i]).abs() <= limit) {
                return Some(x);
            }
            x = next;
        }
        None
    }

    fn solve<const K: usize>(&self, rhs: [LawVector; K]) -> Result<[LawVector; K], StepError> {
        let mut directions = [[0.; LAWS]; K];
        for (i, column) in rhs.iter().copied().enumerate() {
            if let Some(direction) = self.series(column) {
                directions[i] = direction;
                continue;
            }
            let mut matrix = self.weights;
            for (j, row) in matrix.iter_mut().enumerate() {
                row[j] += 1.;
            }
            let lu = Lu::factor(matrix)?;
            for j in i..K {
                directions[j] = lu.solve(rhs[j])?;
            }
            break;
        }
        Ok(directions)
    }
}

impl Map {
    pub const BYTES: usize = 8
        * (2 * LAWS
            + LAWS * (HISTORY + SHARED + LAWS)
            + (NODES + SHARED) * (HISTORY + SHARED + LAWS));

    pub fn read(bytes: &mut &[u8]) -> Self {
        Self {
            bias: read_array(bytes),
            iexp: read_array(bytes),
            z_history: read_matrix(bytes),
            z_port: read_matrix(bytes),
            feedback: read_matrix(bytes),
            i_history: read_matrix(bytes),
            i_port: read_matrix(bytes),
            i_law: read_matrix(bytes),
            x_history: read_matrix(bytes),
            x_port: read_matrix(bytes),
            x_law: read_matrix(bytes),
        }
    }

    pub fn history(&self, offset: [f64; NODES]) -> History {
        let coordinates = std::array::from_fn(|i| if i < NODES { offset[i] } else { 1. });
        History {
            junction: self.z_history.each_ref().map(|row| dot(row, &coordinates)),
            current: self.i_history.each_ref().map(|row| dot(row, &coordinates)),
            coordinates,
        }
    }

    pub fn response<const FULL: bool>(
        &self,
        history: &History,
        ports: &[f64; SHARED],
    ) -> Result<Response, StepError> {
        let drive: [f64; LAWS] =
            std::array::from_fn(|i| history.junction[i] + dot(&self.z_port[i], ports));
        let mut z = drive;
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
            let converged = maximum(&residual) <= 2e-13;
            let mut jacobian = self.i_port;
            if !converged || FULL {
                let slope: [f64; LAWS] = std::array::from_fn(|i| self.iexp[i] * change[i]);
                let feedback = Feedback::new(&self.feedback, &slope);
                if !converged {
                    let [correction] = feedback.solve([residual])?;
                    for i in 0..LAWS {
                        z[i] -= correction[i];
                    }
                    continue;
                }
                let derivatives: [LawVector; SHARED] =
                    feedback.solve(std::array::from_fn(|col| {
                        self.z_port.each_ref().map(|row| row[col])
                    }))?;
                for (col, mut derivative) in derivatives.into_iter().enumerate() {
                    for (d, s) in derivative.iter_mut().zip(slope) {
                        *d *= s;
                    }
                    for (row, coefficient) in jacobian.iter_mut().zip(&self.i_law) {
                        row[col] += dot(coefficient, &derivative);
                    }
                }
            }
            let current = std::array::from_fn(|i| {
                history.current[i] + dot(&self.i_port[i], ports) + dot(&self.i_law[i], &nonlinear)
            });
            if current.iter().any(|x| !x.is_finite()) {
                return Err(StepError::ExponentialDomain);
            }
            return Ok(Response {
                current,
                jacobian,
                nonlinear,
            });
        }
        Err(StepError::IterationBudget)
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
