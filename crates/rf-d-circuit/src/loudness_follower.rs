//! Board-2 Q3/Q2/R15/R16/R24/R27/CR6 algebraic three-port response.
//!
//! SVC-9 Fig. 9-7 PDF p.9, table 7-6 pp.26-27. C2, Q15 base and
//! load-reference voltages are imposed. No latch, capacitor or ADSR timing.
//! Currents and tangents permit a later simultaneous circuit closure.

use crate::{SolverBudget, StepError};

pub const NODE_NAMES: [&str; 5] = [
    "FOLLOWER_BASE",
    "FOLLOWER_MID",
    "FOLLOWER_SUPPLY",
    "LOUDNESS_OUT",
    "RESET_FEEDBACK",
];
const KCL_A: f64 = 1e-11;
const CORRECTION_V: f64 = 1e-8;

#[derive(Clone, Copy, Debug)]
pub struct Parameters {
    pub is_a: f64,
    pub beta_forward: f64,
    pub beta_reverse: f64,
    pub temperature_k: f64,
    pub germanium_is_a: f64,
    pub diode_ideality: f64,
}

impl Default for Parameters {
    fn default() -> Self {
        // Explicit lab hypotheses, not fitted/identified vintage devices.
        Self {
            is_a: 1e-14,
            beta_forward: 100.0,
            beta_reverse: 5.0,
            temperature_k: 298.15,
            germanium_is_a: 1e-8,
            diode_ideality: 1.5,
        }
    }
}

#[derive(Clone, Copy, Debug)]
pub struct Boundary {
    pub c2_v: f64,
    pub reset_base_v: f64,
    pub supply_v: f64,
    /// External outgoing current is g*(OUT-load_reference_v). R59 is 68k,
    /// but its Q18 base voltage is still imposed in this isolated port.
    pub load_conductance_s: f64,
    pub load_reference_v: f64,
}

#[derive(Clone, Copy, Debug)]
pub struct Response {
    pub node_v: [f64; 5],
    /// Current into this network at C2, Q15 base, load reference, in A.
    pub port_current_a: [f64; 3],
    /// dI_port[row]/dV_port[col], in S; this active network is not reciprocal.
    pub port_jacobian_s: [[f64; 3]; 3],
    pub output_gradient_v_per_v: [f64; 3],
    pub iterations: usize,
    pub max_kcl_a: f64,
    pub correction_v: f64,
}

fn valid(p: Parameters, b: Boundary, x: &[f64; 5]) -> bool {
    [
        p.is_a,
        p.beta_forward,
        p.beta_reverse,
        p.temperature_k,
        p.germanium_is_a,
        p.diode_ideality,
    ]
    .iter()
    .all(|v| v.is_finite() && *v > 0.0)
        && [b.c2_v, b.reset_base_v, b.supply_v, b.load_reference_v]
            .iter()
            .all(|v| v.is_finite())
        && b.load_conductance_s.is_finite()
        && b.load_conductance_s >= 0.0
        && x.iter().all(|v| v.is_finite())
}

fn maximum(x: &[f64; 5]) -> f64 {
    x.iter().fold(0.0_f64, |a, v| a.max(v.abs()))
}

fn junction(exponent: f64, is_a: f64, scale: f64) -> Result<(f64, f64), StepError> {
    if !exponent.is_finite() || exponent > 45.0 {
        return Err(StepError::ExponentialDomain);
    }
    Ok((is_a * exponent.exp_m1(), is_a * exponent.exp() / scale))
}

fn stamp_bjt(
    r: &mut [f64; 5],
    j: &mut [[f64; 5]; 5],
    x: &[f64; 5],
    p: Parameters,
    base: usize,
    collector: usize,
    emitter: usize,
) -> Result<(), StepError> {
    let vt = 1.380_649e-23 * p.temperature_k / 1.602_176_634e-19;
    let (f, gf) = junction((x[base] - x[emitter]) / vt, p.is_a, vt)?;
    let (rev, gr) = junction((x[base] - x[collector]) / vt, p.is_a, vt)?;
    let ib = f / p.beta_forward + rev / p.beta_reverse;
    let ic = f - rev * (1.0 + 1.0 / p.beta_reverse);
    r[base] += ib;
    r[collector] += ic;
    r[emitter] -= ib + ic;
    let gbf = gf / p.beta_forward;
    let gbr = gr / p.beta_reverse;
    let gcr = gr * (1.0 + 1.0 / p.beta_reverse);
    for (row, values) in [
        (base, [gbf + gbr, -gbr, -gbf]),
        (collector, [gf - gcr, gcr, -gf]),
        (emitter, [-gf - gbf + gr, -gr, gf + gbf]),
    ] {
        for (col, derivative) in [base, collector, emitter].into_iter().zip(values) {
            j[row][col] += derivative;
        }
    }
    Ok(())
}

/// All five physical outgoing-current rows and exact voltage derivatives.
pub fn linearize(
    x: [f64; 5],
    p: Parameters,
    b: Boundary,
) -> Result<([f64; 5], [[f64; 5]; 5]), StepError> {
    if !valid(p, b, &x) {
        return Err(StepError::InvalidInput);
    }
    let mut r = [0.0; 5];
    let mut j = [[0.0; 5]; 5];
    r[0] += (x[0] - b.c2_v) / 10000.0;
    j[0][0] += 1.0 / 10000.0;
    r[2] += (x[2] - b.supply_v) / 560.0;
    j[2][2] += 1.0 / 560.0;
    r[4] += (x[4] + 10.0) / 16900.0;
    j[4][4] += 1.0 / 16900.0;
    let i = (x[3] - x[4]) / 6800.0;
    r[3] += i;
    r[4] -= i;
    j[3][3] += 1.0 / 6800.0;
    j[3][4] -= 1.0 / 6800.0;
    j[4][3] -= 1.0 / 6800.0;
    j[4][4] += 1.0 / 6800.0;
    r[3] += b.load_conductance_s * (x[3] - b.load_reference_v);
    j[3][3] += b.load_conductance_s;
    stamp_bjt(&mut r, &mut j, &x, p, 0, 2, 1)?;
    stamp_bjt(&mut r, &mut j, &x, p, 1, 2, 3)?;
    let scale = p.diode_ideality * 1.380_649e-23 * p.temperature_k / 1.602_176_634e-19;
    let (diode, gd) = junction((x[4] - b.reset_base_v) / scale, p.germanium_is_a, scale)?;
    r[4] += diode;
    j[4][4] += gd;
    if r.iter().chain(j.iter().flatten()).any(|v| !v.is_finite()) {
        return Err(StepError::ExponentialDomain);
    }
    Ok((r, j))
}

fn solve_linear(mut j: [[f64; 5]; 5], mut rhs: [f64; 5]) -> Result<[f64; 5], StepError> {
    let mut scales = j.map(|row| maximum(&row));
    for col in 0..5 {
        let mut pivot = col;
        let mut best = 0.0;
        for i in col..5 {
            if scales[i] > 0.0 && j[i][col].abs() / scales[i] > best {
                best = j[i][col].abs() / scales[i];
                pivot = i;
            }
        }
        if best < 1e-12 {
            return Err(StepError::SingularJacobian);
        }
        j.swap(col, pivot);
        rhs.swap(col, pivot);
        scales.swap(col, pivot);
        for i in col + 1..5 {
            let factor = j[i][col] / j[col][col];
            j[i][col] = 0.0;
            for k in col + 1..5 {
                j[i][k] -= factor * j[col][k];
            }
            rhs[i] -= factor * rhs[col];
        }
    }
    let mut x = [0.0; 5];
    for i in (0..5).rev() {
        let mut v = rhs[i];
        for k in i + 1..5 {
            v -= j[i][k] * x[k];
        }
        x[i] = v / j[i][i];
    }
    if x.iter().any(|v| !v.is_finite()) {
        return Err(StepError::SingularJacobian);
    }
    Ok(x)
}

fn response(
    x: [f64; 5],
    j: [[f64; 5]; 5],
    p: Parameters,
    b: Boundary,
    iterations: usize,
    kcl: f64,
    correction: f64,
) -> Result<Response, StepError> {
    let scale = p.diode_ideality * 1.380_649e-23 * p.temperature_k / 1.602_176_634e-19;
    let (diode, gd) = junction((x[4] - b.reset_base_v) / scale, p.germanium_is_a, scale)?;
    let mut tangents = [[0.0; 3]; 3];
    let mut output = [0.0; 3];
    for col in 0..3 {
        let mut rhs = [0.0; 5];
        match col {
            0 => rhs[0] = 1.0 / 10000.0,
            1 => rhs[4] = gd,
            _ => rhs[3] = b.load_conductance_s,
        }
        let dx = solve_linear(j, rhs)?;
        let indicator = |port: usize| if port == col { 1.0 } else { 0.0 };
        tangents[0][col] = (indicator(0) - dx[0]) / 10000.0;
        tangents[1][col] = -gd * (dx[4] - indicator(1));
        tangents[2][col] = b.load_conductance_s * (indicator(2) - dx[3]);
        output[col] = dx[3];
    }
    Ok(Response {
        node_v: x,
        port_current_a: [
            (b.c2_v - x[0]) / 10000.0,
            -diode,
            b.load_conductance_s * (b.load_reference_v - x[3]),
        ],
        port_jacobian_s: tangents,
        output_gradient_v_per_v: output,
        iterations,
        max_kcl_a: kcl,
        correction_v: correction,
    })
}

/// Caller-provided numeric seed is copied. No state/history is published on
/// failure; the caller may use this provisional port inside an outer solve.
pub fn solve_port(
    seed: [f64; 5],
    p: Parameters,
    b: Boundary,
    budget: SolverBudget,
) -> Result<Response, StepError> {
    if !valid(p, b, &seed)
        || budget.iterations == 0
        || budget.iterations > 32
        || budget.line_search_halvings == 0
        || budget.line_search_halvings > 24
    {
        return Err(StepError::InvalidInput);
    }
    let mut x = seed;
    for iteration in 0..budget.iterations {
        let (r, j) = linearize(x, p, b)?;
        let direction = solve_linear(j, r.map(|v| -v))?;
        let error = maximum(&r);
        let correction = maximum(&direction);
        if error < KCL_A && correction < CORRECTION_V {
            return response(x, j, p, b, iteration, error, correction);
        }
        let mut accepted = false;
        for power in 0..budget.line_search_halvings {
            let factor = 0.5_f64.powi(power as i32);
            let trial = std::array::from_fn(|i| x[i] + factor * direction[i]);
            if let Ok((rt, jt)) = linearize(trial, p, b) {
                let next_error = maximum(&rt);
                let decreases = if error < KCL_A {
                    next_error < KCL_A
                        && solve_linear(jt, rt.map(|v| -v)).is_ok_and(|d| maximum(&d) < correction)
                } else {
                    next_error < error
                };
                if decreases {
                    x = trial;
                    accepted = true;
                    break;
                }
            }
        }
        if !accepted {
            return Err(StepError::NoDecrease);
        }
    }
    Err(StepError::IterationBudget)
}

/// Cold seed derived only for numerical preparation; it is not a contour law.
pub fn initial_guess(b: Boundary) -> [f64; 5] {
    let base = (b.c2_v - 0.02).min(b.supply_v + 0.2);
    let out = base - 1.2;
    [
        base,
        base - 0.55,
        b.supply_v - 0.25,
        out,
        ((out / 6800.0 - 10.0 / 16900.0) / (1.0 / 6800.0 + 1.0 / 16900.0))
            .min(b.reset_base_v + 0.4),
    ]
}
