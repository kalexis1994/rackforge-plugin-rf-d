//! Schur response of the audio arm and its retained exponential remainders.
use crate::{
    graph,
    reduced_lu::{dot, maximum, Lu},
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

struct Projection {
    columns: [usize; SUPPORT],
    count: usize,
    coupling: [[f64; SUPPORT]; LAWS],
    factor: Lu<SUPPORT>,
}

impl Projection {
    fn new(port_map: &LawMatrix, peak: &LawVector, slope: &LawVector) -> Option<Self> {
        let mut columns = [0; SUPPORT];
        let mut count = 0;
        for (col, (&maximum, &derivative)) in peak.iter().zip(slope).enumerate() {
            if maximum * derivative.abs() > COLUMN_FLOOR {
                *columns.get_mut(count)? = col;
                count += 1;
            }
        }
        let mut coupling = [[0.; SUPPORT]; LAWS];
        for (row, weights) in port_map.iter().zip(&mut coupling) {
            for (weight, &col) in weights.iter_mut().zip(&columns[..count]) {
                *weight = row[col] * slope[col];
            }
        }
        let factor = Lu::factor(std::array::from_fn(|i| {
            std::array::from_fn(|j| {
                f64::from(i == j)
                    + if i < count {
                        coupling[columns[i]][j]
                    } else {
                        0.
                    }
            })
        }))
        .ok()?;
        Some(Self {
            columns,
            count,
            coupling,
            factor,
        })
    }

    fn apply(&self, rhs: LawVector) -> Option<LawVector> {
        let strong = self
            .factor
            .solve(std::array::from_fn(|j| {
                if j < self.count {
                    rhs[self.columns[j]]
                } else {
                    0.
                }
            }))
            .ok()?;
        let mut x = std::array::from_fn(|i| {
            rhs[i]
                - self.coupling[i][..self.count]
                    .iter()
                    .zip(strong)
                    .map(|(weight, value)| weight * value)
                    .sum::<f64>()
        });
        for (&i, value) in self.columns[..self.count].iter().zip(strong) {
            x[i] = value;
        }
        Some(x)
    }

    fn refine(&self, port_map: &LawMatrix, slope: &LawVector, rhs: LawVector) -> Option<LawVector> {
        let limit = 1e-14 + 2e-13 * maximum(&rhs);
        let mut x = self.apply(rhs)?;
        for _ in 0..5 {
            // The projection leaves weak columns out of the factor, but the
            // residual uses every column of the original feedback law.
            let weighted = std::array::from_fn(|i| slope[i] * x[i]);
            let residual = std::array::from_fn(|i| rhs[i] - x[i] - dot(&port_map[i], &weighted));
            if residual.iter().all(|v| v.is_finite() && v.abs() <= limit) {
                return Some(x);
            }
            let correction = self.apply(residual)?;
            for (value, delta) in x.iter_mut().zip(correction) {
                *value += delta;
            }
        }
        None
    }
}

fn feedback_directions<const K: usize>(
    port_map: &LawMatrix,
    peak: &LawVector,
    slope: &LawVector,
    rhs: [LawVector; K],
) -> Result<[LawVector; K], StepError> {
    let projection = Projection::new(port_map, peak, slope);
    let mut directions = [[0.; LAWS]; K];
    for (i, column) in rhs.iter().copied().enumerate() {
        if let Some(direction) = projection
            .as_ref()
            .and_then(|p| p.refine(port_map, slope, column))
        {
            directions[i] = direction;
            continue;
        }
        let matrix = std::array::from_fn(|row| {
            std::array::from_fn(|col| port_map[row][col] * slope[col] + f64::from(row == col))
        });
        let lu = Lu::factor(matrix)?;
        for j in i..K {
            directions[j] = lu.solve(rhs[j])?;
        }
        break;
    }
    Ok(directions)
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
                let [correction] =
                    feedback_directions(&self.feedback, &self.feedback_peak, &slope, [residual])?;
                for i in 0..LAWS {
                    z[i] -= correction[i];
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
                junctions: z,
            });
        }
        Err(StepError::IterationBudget)
    }

    pub fn jacobian(&self, response: &Response) -> Result<PortJacobian, StepError> {
        let slope = std::array::from_fn(|i| self.iexp[i] * response.junctions[i].exp_m1());
        let derivatives: [LawVector; SHARED] = feedback_directions(
            &self.feedback,
            &self.feedback_peak,
            &slope,
            std::array::from_fn(|col| self.z_port.each_ref().map(|row| row[col])),
        )?;
        let mut jacobian = self.i_port;
        for (col, mut derivative) in derivatives.into_iter().enumerate() {
            for (d, s) in derivative.iter_mut().zip(slope) {
                *d *= s;
            }
            for (row, coefficient) in jacobian.iter_mut().zip(&self.i_law) {
                row[col] += dot(coefficient, &derivative);
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
