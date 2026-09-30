//! Six-node board-4 Q1/Q12/Q17 conversion, DC and coupled C2 transient.
//! Bases and +10 V rail are imposed; C4 remains outside this block.

use crate::output::{
    initial_output_state, solve_output_input_port, OutputBoundary, OutputInputPort, OutputState,
    OutputStepResult,
};
use crate::{Parameters as HeadphoneParameters, SolverBudget, StepError};

const N: usize = 6;
const K_B: f64 = 1.380_649e-23;
const Q_E: f64 = 1.602_176_634e-19;
const KCL_TOLERANCE_A: f64 = 1e-12;

pub const NODE_NAMES: [&str; N] = [
    "Q1_EMITTER",
    "Q1_COLLECTOR",
    "Q12_EMITTER",
    "Q17_EMITTER",
    "Q12_COLLECTOR",
    "Q17_COLLECTOR",
];

#[derive(Clone, Copy, Debug)]
pub struct DiodeParameters {
    pub is_a: f64,
    pub ideality: f64,
}

#[derive(Clone, Copy, Debug)]
pub struct Parameters {
    pub transistor_is_a: f64,
    pub beta_forward: f64,
    pub beta_reverse: f64,
    pub temperature_k: f64,
    pub diode: Option<DiodeParameters>,
}

#[derive(Clone, Copy, Debug)]
pub struct Boundary {
    pub q1_base_v: f64,
    pub q12_base_v: f64,
    pub q17_base_v: f64,
    pub plus_v: f64,
}

#[derive(Clone, Copy, Debug, PartialEq)]
pub struct DcState {
    pub node_v: [f64; N],
}

#[derive(Clone, Copy, Debug)]
pub struct DcResult {
    pub state: DcState,
    pub iterations: usize,
    pub max_kcl_residual_a: f64,
}

/// One atomic state for board 4, C2, panel, and board 3.
#[derive(Clone, Copy, Debug, PartialEq)]
pub struct CoupledState {
    pub conversion: DcState,
    pub output: OutputState,
}

/// The collector field of `output` is replaced by the solved Q17 collector
/// voltage at every Newton trial. All other fields remain imposed controls.
#[derive(Clone, Copy, Debug)]
pub struct CoupledBoundary {
    pub conversion: Boundary,
    pub output: OutputBoundary,
}

#[derive(Clone, Copy, Debug)]
pub struct CoupledResult {
    pub output: OutputStepResult,
    pub iterations: usize,
    pub max_conversion_kcl_residual_a: f64,
}

pub fn initial_coupled_state(
    p: Parameters,
    b: Boundary,
    headphone: HeadphoneParameters,
) -> Result<CoupledState, StepError> {
    let conversion = solve_dc(p, b)?.state;
    let output = initial_output_state(headphone, conversion.node_v[5])?;
    Ok(CoupledState { conversion, output })
}

fn positive(v: f64) -> bool {
    v.is_finite() && v > 0.0
}

fn validate(p: Parameters, b: Boundary) -> Result<(), StepError> {
    if !positive(p.transistor_is_a)
        || !positive(p.beta_forward)
        || !positive(p.beta_reverse)
        || !positive(p.temperature_k)
        || !b.q1_base_v.is_finite()
        || !b.q12_base_v.is_finite()
        || !b.q17_base_v.is_finite()
        || !positive(b.plus_v)
        || p.diode
            .is_some_and(|d| !positive(d.is_a) || !positive(d.ideality))
    {
        return Err(StepError::InvalidInput);
    }
    Ok(())
}

fn resistor(
    x: &[f64; N],
    r: &mut [f64; N],
    j: &mut [[f64; N]; N],
    a: usize,
    b: Option<usize>,
    fixed_b: f64,
    ohm: f64,
) {
    let g = 1.0 / ohm;
    let vb = b.map_or(fixed_b, |i| x[i]);
    let current = (x[a] - vb) * g;
    r[a] += current;
    j[a][a] += g;
    if let Some(i) = b {
        r[i] -= current;
        j[i][i] += g;
        j[a][i] -= g;
        j[i][a] -= g;
    }
}

// Explicit terminals keep the three 2N4058 stamps auditable to Fig. 9-11.
#[allow(clippy::too_many_arguments)]
fn pnp(
    x: &[f64; N],
    r: &mut [f64; N],
    j: &mut [[f64; N]; N],
    base_v: f64,
    collector: usize,
    emitter: usize,
    p: Parameters,
    vt: f64,
) -> Result<(), StepError> {
    let xbe = (x[emitter] - base_v) / vt;
    let xbc = (x[collector] - base_v) / vt;
    if !xbe.is_finite() || !xbc.is_finite() || xbe.max(xbc) > 45.0 {
        return Err(StepError::ExponentialDomain);
    }
    let forward = p.transistor_is_a * xbe.exp_m1();
    let reverse = p.transistor_is_a * xbc.exp_m1();
    let ib = forward / p.beta_forward + reverse / p.beta_reverse;
    let ic = forward - (1.0 + 1.0 / p.beta_reverse) * reverse;
    r[collector] -= ic;
    r[emitter] += ib + ic;
    let gf = p.transistor_is_a * xbe.exp() / vt;
    let gr = p.transistor_is_a * xbc.exp() / vt;
    j[collector][collector] += (1.0 + 1.0 / p.beta_reverse) * gr;
    j[collector][emitter] -= gf;
    j[emitter][collector] -= gr;
    j[emitter][emitter] += (1.0 + 1.0 / p.beta_forward) * gf;
    Ok(())
}

fn diode_current(exponent: f64, p: DiodeParameters, vt: f64) -> Result<(f64, f64), StepError> {
    if !exponent.is_finite() || exponent > 45.0 {
        return Err(StepError::ExponentialDomain);
    }
    Ok((
        p.is_a * exponent.exp_m1(),
        p.is_a * exponent.exp() / (p.ideality * vt),
    ))
}

fn evaluate(
    x: &[f64; N],
    p: Parameters,
    b: Boundary,
) -> Result<([f64; N], [[f64; N]; N]), StepError> {
    let mut r = [0.0; N];
    let mut j = [[0.0; N]; N];
    let vt = K_B * p.temperature_k / Q_E;
    resistor(x, &mut r, &mut j, 0, None, b.plus_v, 62.0); // R9
    resistor(x, &mut r, &mut j, 1, Some(2), 0.0, 8.2); // R8
    resistor(x, &mut r, &mut j, 1, Some(3), 0.0, 8.2); // R28
    resistor(x, &mut r, &mut j, 4, None, 0.0, 680.0); // R30
    resistor(x, &mut r, &mut j, 5, None, 0.0, 680.0); // R29
    pnp(x, &mut r, &mut j, b.q1_base_v, 1, 0, p, vt)?; // Q1
    pnp(x, &mut r, &mut j, b.q12_base_v, 4, 2, p, vt)?; // Q12
    pnp(x, &mut r, &mut j, b.q17_base_v, 5, 3, p, vt)?; // Q17
    if let Some(model) = p.diode {
        let (cr1, g1) = diode_current((x[5] - b.plus_v) / (model.ideality * vt), model, vt)?;
        let (cr2, g2) = diode_current(-x[5] / (model.ideality * vt), model, vt)?;
        r[5] += cr1 - cr2;
        j[5][5] += g1 + g2;
    }
    if r.iter().any(|v| !v.is_finite()) || j.iter().flatten().any(|v| !v.is_finite()) {
        return Err(StepError::ExponentialDomain);
    }
    Ok((r, j))
}

fn max_abs(x: &[f64; N]) -> f64 {
    x.iter().fold(0.0_f64, |a, v| a.max(v.abs()))
}

fn solve_linear(mut j: [[f64; N]; N], mut rhs: [f64; N]) -> Result<[f64; N], StepError> {
    let mut scale = [0.0; N];
    for i in 0..N {
        scale[i] = max_abs(&j[i]);
        if scale[i] == 0.0 {
            return Err(StepError::SingularJacobian);
        }
    }
    for col in 0..N {
        let mut pivot = col;
        let mut best = 0.0;
        for row in col..N {
            let score = j[row][col].abs() / scale[row];
            if score > best {
                best = score;
                pivot = row;
            }
        }
        if best < 1e-12 {
            return Err(StepError::SingularJacobian);
        }
        j.swap(col, pivot);
        rhs.swap(col, pivot);
        scale.swap(col, pivot);
        let diagonal = j[col][col];
        for row in (col + 1)..N {
            let factor = j[row][col] / diagonal;
            j[row][col] = 0.0;
            #[allow(clippy::needless_range_loop)]
            for k in (col + 1)..N {
                j[row][k] -= factor * j[col][k];
            }
            rhs[row] -= factor * rhs[col];
        }
    }
    let mut out = [0.0; N];
    for row in (0..N).rev() {
        let mut value = rhs[row];
        for k in (row + 1)..N {
            value -= j[row][k] * out[k];
        }
        out[row] = value / j[row][row];
    }
    if out.iter().any(|v| !v.is_finite()) {
        return Err(StepError::SingularJacobian);
    }
    Ok(out)
}

pub fn solve_dc(p: Parameters, b: Boundary) -> Result<DcResult, StepError> {
    validate(p, b)?;
    // Same approximate Newton seed as the independent Python reference.
    let mut x = [
        b.q1_base_v + 0.6,
        b.q1_base_v + 0.35,
        b.q12_base_v + 0.6,
        b.q17_base_v + 0.6,
        2.0,
        2.0,
    ];
    for iteration in 0..16 {
        let (residual, jacobian) = evaluate(&x, p, b)?;
        let error = max_abs(&residual);
        if error < KCL_TOLERANCE_A {
            if p.diode.is_none() && !(0.0..=b.plus_v).contains(&x[5]) {
                return Err(StepError::ExponentialDomain);
            }
            return Ok(DcResult {
                state: DcState { node_v: x },
                iterations: iteration,
                max_kcl_residual_a: error,
            });
        }
        let direction = solve_linear(jacobian, residual.map(|v| -v))?;
        let mut accepted = false;
        for power in 0..16 {
            let factor = 0.5_f64.powi(power);
            let candidate = std::array::from_fn(|i| x[i] + factor * direction[i]);
            if let Ok((next, _)) = evaluate(&candidate, p, b) {
                if max_abs(&next) < error {
                    x = candidate;
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

fn coupled_trial(
    previous: CoupledState,
    x: &[f64; N],
    p: Parameters,
    headphone: HeadphoneParameters,
    b: CoupledBoundary,
    budget: SolverBudget,
) -> Result<([f64; N], [[f64; N]; N], OutputInputPort), StepError> {
    let mut output_boundary = b.output;
    output_boundary.q17_collector_v = x[5];
    let port = solve_output_input_port(&previous.output, headphone, output_boundary, budget)?;
    let (mut residual, mut jacobian) = evaluate(x, p, b.conversion)?;
    residual[5] += port.current_a;
    jacobian[5][5] += port.conductance_s;
    if !residual[5].is_finite() || !jacobian[5][5].is_finite() {
        return Err(StepError::ExponentialDomain);
    }
    Ok((residual, jacobian, port))
}

/// Solve Q1/Q12/Q17 and the complete C2-to-J7 output in one implicit step.
/// The three bases and rails remain imposed. Every trial starts with the
/// immutable previous capacitor states; failure leaves `state` untouched.
pub fn solve_coupled_step(
    state: &mut CoupledState,
    p: Parameters,
    headphone: HeadphoneParameters,
    b: CoupledBoundary,
    budget: SolverBudget,
) -> Result<CoupledResult, StepError> {
    validate(p, b.conversion)?;
    if state.conversion.node_v.iter().any(|v| !v.is_finite())
        || !(1..=16).contains(&budget.iterations)
        || !(1..=16).contains(&budget.line_search_halvings)
    {
        return Err(StepError::InvalidInput);
    }
    let previous = *state;
    let mut x = state.conversion.node_v;
    let mut cached: Option<([f64; N], [[f64; N]; N], OutputInputPort)> = None;
    for iteration in 0..budget.iterations {
        let (residual, jacobian, port) = match cached.take() {
            Some(value) => value,
            None => coupled_trial(previous, &x, p, headphone, b, budget)?,
        };
        let error = max_abs(&residual);
        if error < 1e-10 {
            if p.diode.is_none() && !(0.0..=b.conversion.plus_v).contains(&x[5]) {
                return Err(StepError::ExponentialDomain);
            }
            state.conversion.node_v = x;
            state.output = port.next_state;
            return Ok(CoupledResult {
                output: port.output,
                iterations: iteration,
                max_conversion_kcl_residual_a: error,
            });
        }
        let direction = solve_linear(jacobian, residual.map(|v| -v))?;
        let mut accepted = None;
        for power in 0..budget.line_search_halvings {
            let factor = 0.5_f64.powi(power as i32);
            let candidate = std::array::from_fn(|i| x[i] + factor * direction[i]);
            if let Ok(trial) = coupled_trial(previous, &candidate, p, headphone, b, budget) {
                if max_abs(&trial.0) < error {
                    accepted = Some((candidate, trial));
                    break;
                }
            }
        }
        if let Some((candidate, trial)) = accepted {
            x = candidate;
            cached = Some(trial);
        } else {
            return Err(StepError::NoDecrease);
        }
    }
    Err(StepError::IterationBudget)
}
