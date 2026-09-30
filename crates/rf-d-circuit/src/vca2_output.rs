//! Q14/Q13/Q21 and second balance coupled to Q1_BASE/C4/C2/J7.
//! First VCA collector voltages and Q21 control remain imposed boundaries.

use crate::output_conversion::{max_abs, solve_linear, Parameters as ConversionParameters};
use crate::output_conversion_c4::{
    initial_state as initial_downstream, solve_input_port as downstream_port, BoundaryC4,
    State as DownstreamState,
};
use crate::{Parameters as HeadphoneParameters, SolverBudget, StepError};

const N: usize = 6;
const K_B: f64 = 1.380_649e-23;
const Q_E: f64 = 1.602_176_634e-19;

pub const NODE_NAMES: [&str; N] = [
    "PAIR2_EMITTER",
    "Q21_COLLECTOR",
    "Q21_EMITTER",
    "Q14_COLLECTOR",
    "Q13_COLLECTOR",
    "SECOND_BAL_WIPER",
];

#[derive(Clone, Copy, Debug)]
pub struct Parameters {
    pub transistor_is_a: f64,
    pub beta_forward: f64,
    pub beta_reverse: f64,
    pub temperature_k: f64,
}

#[derive(Clone, Copy, Debug)]
pub struct Boundary {
    pub q14_base_v: f64,
    pub q13_base_v: f64,
    pub q21_base_v: f64,
    pub first_balance_wiper_v: f64,
    pub second_balance_left_ohm: f64,
    pub minus_v: f64,
    pub output: BoundaryC4,
}

#[derive(Clone, Copy, Debug, PartialEq)]
pub struct State {
    pub node_v: [f64; N],
    pub previous_node_v: [f64; N],
    pub downstream: DownstreamState,
}

#[derive(Clone, Copy, Debug)]
pub struct StepResult {
    pub j7_v: f64,
    pub j4_hi_v: f64,
    pub j5_lo_v: f64,
    pub iterations: usize,
    pub downstream_evaluations: usize,
    pub predictor_fallback: bool,
    pub max_kcl_residual_a: f64,
}

fn finite_positive(x: f64) -> bool {
    x.is_finite() && x > 0.0
}

fn validate(p: Parameters, b: Boundary, budget: SolverBudget) -> Result<(), StepError> {
    if !finite_positive(p.transistor_is_a)
        || !finite_positive(p.beta_forward)
        || !finite_positive(p.beta_reverse)
        || !finite_positive(p.temperature_k)
        || !b.q14_base_v.is_finite()
        || !b.q13_base_v.is_finite()
        || !b.q21_base_v.is_finite()
        || !b.first_balance_wiper_v.is_finite()
        || !b.minus_v.is_finite()
        || !b.second_balance_left_ohm.is_finite()
        || !(0.0..=100.0).contains(&b.second_balance_left_ohm)
        || !(1..=16).contains(&budget.iterations)
        || !(1..=16).contains(&budget.line_search_halvings)
    {
        return Err(StepError::InvalidInput);
    }
    Ok(())
}

fn downstream_boundary(x: &[f64; N], b: Boundary) -> BoundaryC4 {
    let mut result = b.output;
    result.second_balance_wiper_v = x[5];
    result.q12_base_v = x[3];
    result.q17_base_v = x[4];
    result
}

fn resistor(
    x: &[f64; N],
    r: &mut [f64; N],
    j: &mut [[f64; N]; N],
    a: usize,
    b: Option<usize>,
    fixed: f64,
    ohm: f64,
) {
    let g = 1.0 / ohm;
    let vb = b.map_or(fixed, |i| x[i]);
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

fn npn(
    x: &[f64; N],
    r: &mut [f64; N],
    j: &mut [[f64; N]; N],
    base_v: f64,
    collector: usize,
    emitter: usize,
    p: Parameters,
) -> Result<(), StepError> {
    let vt = K_B * p.temperature_k / Q_E;
    let f = (base_v - x[emitter]) / vt;
    let rev = (base_v - x[collector]) / vt;
    if !f.is_finite() || !rev.is_finite() || f.max(rev) > 45.0 {
        return Err(StepError::ExponentialDomain);
    }
    let forward = p.transistor_is_a * f.exp_m1();
    let reverse = p.transistor_is_a * rev.exp_m1();
    let ib = forward / p.beta_forward + reverse / p.beta_reverse;
    let ic = forward - (1.0 + 1.0 / p.beta_reverse) * reverse;
    let gf = p.transistor_is_a * f.exp() / vt;
    let gr = p.transistor_is_a * rev.exp() / vt;
    r[collector] += ic;
    r[emitter] -= ic + ib;
    j[collector][collector] += (1.0 + 1.0 / p.beta_reverse) * gr;
    j[collector][emitter] -= gf;
    j[emitter][collector] -= gr;
    j[emitter][emitter] += (1.0 + 1.0 / p.beta_forward) * gf;
    Ok(())
}

fn evaluate(
    x: &[f64; N],
    p: Parameters,
    b: Boundary,
    port_current: [f64; 3],
    port_tangent: Option<[[f64; 3]; 3]>,
) -> Result<([f64; N], [[f64; N]; N]), StepError> {
    let mut r = [0.0; N];
    let mut j = [[0.0; N]; N];
    resistor(x, &mut r, &mut j, 0, Some(1), 0.0, 470.0); // R33
    resistor(x, &mut r, &mut j, 2, None, 0.0, 3300.0); // R42
    resistor(x, &mut r, &mut j, 2, None, b.minus_v, 150000.0); // R44
    resistor(
        x,
        &mut r,
        &mut j,
        3,
        Some(5),
        0.0,
        330.0 + b.second_balance_left_ohm,
    ); // R18 + R12L
    resistor(
        x,
        &mut r,
        &mut j,
        4,
        Some(5),
        0.0,
        430.0 - b.second_balance_left_ohm,
    ); // R21 + R12R
    resistor(x, &mut r, &mut j, 5, None, b.first_balance_wiper_v, 120.0); // R13
    npn(x, &mut r, &mut j, b.q14_base_v, 3, 0, p)?;
    npn(x, &mut r, &mut j, b.q13_base_v, 4, 0, p)?;
    npn(x, &mut r, &mut j, b.q21_base_v, 1, 2, p)?;
    r[5] += port_current[0];
    r[3] -= port_current[1];
    r[4] -= port_current[2];
    if let Some(tangent) = port_tangent {
        let rows = [5, 3, 4];
        let columns = [5, 3, 4];
        for output in 0..3 {
            let sign = if output == 0 { 1.0 } else { -1.0 };
            for input in 0..3 {
                j[rows[output]][columns[input]] += sign * tangent[output][input];
            }
        }
    }
    if r.iter().any(|v| !v.is_finite()) || j.iter().flatten().any(|v| !v.is_finite()) {
        return Err(StepError::ExponentialDomain);
    }
    Ok((r, j))
}

fn dc_trial(
    x: &[f64; N],
    p: Parameters,
    out_p: ConversionParameters,
    headphone: HeadphoneParameters,
    b: Boundary,
) -> Result<([f64; N], DownstreamState), StepError> {
    let downstream = initial_downstream(out_p, headphone, downstream_boundary(x, b))?;
    let y = downstream.node_v;
    let port = [
        (x[5] - y[0]) / 150.0,
        pnp_base_current(y[3], y[5], x[3], out_p),
        pnp_base_current(y[4], y[6], x[4], out_p),
    ];
    let (r, _) = evaluate(x, p, b, port, None)?;
    Ok((r, downstream))
}

fn pnp_base_current(emitter: f64, collector: f64, base: f64, p: ConversionParameters) -> f64 {
    let vt = K_B * p.temperature_k / Q_E;
    p.transistor_is_a
        * (((emitter - base) / vt).exp_m1() / p.beta_forward
            + ((collector - base) / vt).exp_m1() / p.beta_reverse)
}

/// DC initializer with first-VCA nodes imposed. C4/C2/board-3 capacitors open.
pub fn initial_state(
    p: Parameters,
    out_p: ConversionParameters,
    headphone: HeadphoneParameters,
    b: Boundary,
) -> Result<State, StepError> {
    validate(p, b, SolverBudget::default())?;
    let mid = (b.q14_base_v + b.q13_base_v) * 0.5;
    let mut x = [
        mid - 0.6,
        mid - 0.8,
        b.q21_base_v - 0.6,
        b.first_balance_wiper_v + 1.1,
        b.first_balance_wiper_v + 1.1,
        b.first_balance_wiper_v + 1.2,
    ];
    for _ in 0..16 {
        let (r, downstream) = dc_trial(&x, p, out_p, headphone, b)?;
        let error = max_abs(&r);
        if error < 1e-12 {
            return Ok(State {
                node_v: x,
                previous_node_v: x,
                downstream,
            });
        }
        let mut jacobian = [[0.0; N]; N];
        for column in 0..N {
            let mut shifted = x;
            shifted[column] += 1e-6;
            let high = dc_trial(&shifted, p, out_p, headphone, b)?.0;
            for row in 0..N {
                jacobian[row][column] = (high[row] - r[row]) / 1e-6;
            }
        }
        let direction = solve_linear(jacobian, r.map(|v| -v))?;
        let mut accepted = false;
        for power in 0..16 {
            let factor = 0.5_f64.powi(power);
            let candidate = std::array::from_fn(|i| x[i] + factor * direction[i]);
            if let Ok((next, _)) = dc_trial(&candidate, p, out_p, headphone, b) {
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

fn transient_trial(
    previous: State,
    x: &[f64; N],
    p: Parameters,
    out_p: ConversionParameters,
    headphone: HeadphoneParameters,
    b: Boundary,
    budget: SolverBudget,
) -> Result<([f64; N], [[f64; N]; N], DownstreamState, StepResult), StepError> {
    let port = downstream_port(
        &previous.downstream,
        out_p,
        headphone,
        downstream_boundary(x, b),
        budget,
    )?;
    let (r, j) = evaluate(x, p, b, port.current_a, Some(port.conductance_s))?;
    let result = StepResult {
        j7_v: port.result.output.j7_v,
        j4_hi_v: port.result.output.j4_hi_v,
        j5_lo_v: port.result.output.j5_lo_v,
        iterations: 0,
        downstream_evaluations: 0,
        predictor_fallback: false,
        max_kcl_residual_a: max_abs(&r),
    };
    Ok((r, j, port.next_state, result))
}

fn solve_from_seed(
    previous: State,
    mut x: [f64; N],
    p: Parameters,
    out_p: ConversionParameters,
    headphone: HeadphoneParameters,
    b: Boundary,
    budget: SolverBudget,
    evaluations: &mut usize,
) -> Result<([f64; N], DownstreamState, StepResult), StepError> {
    let mut cached = None;
    for iteration in 0..budget.iterations {
        let (r, j, downstream, mut result) = match cached.take() {
            Some(value) => value,
            None => {
                *evaluations += 1;
                transient_trial(previous, &x, p, out_p, headphone, b, budget)?
            }
        };
        let error = max_abs(&r);
        if error < 1e-10 {
            result.iterations = iteration;
            result.downstream_evaluations = *evaluations;
            result.max_kcl_residual_a = error;
            return Ok((x, downstream, result));
        }
        let direction = solve_linear(j, r.map(|v| -v))?;
        let mut accepted = None;
        for power in 0..budget.line_search_halvings {
            let factor = 0.5_f64.powi(power as i32);
            let candidate = std::array::from_fn(|i| x[i] + factor * direction[i]);
            *evaluations += 1;
            if let Ok(next) = transient_trial(previous, &candidate, p, out_p, headphone, b, budget)
            {
                if max_abs(&next.0) < error {
                    accepted = Some((candidate, next));
                    break;
                }
            }
        }
        if let Some((candidate, next)) = accepted {
            x = candidate;
            cached = Some(next);
        } else {
            return Err(StepError::NoDecrease);
        }
    }
    Err(StepError::IterationBudget)
}

/// Joint transient step; failure leaves the six VCA and all downstream state untouched.
pub fn step(
    state: &mut State,
    p: Parameters,
    out_p: ConversionParameters,
    headphone: HeadphoneParameters,
    b: Boundary,
    budget: SolverBudget,
) -> Result<StepResult, StepError> {
    validate(p, b, budget)?;
    if state
        .node_v
        .iter()
        .chain(state.previous_node_v.iter())
        .any(|v| !v.is_finite())
    {
        return Err(StepError::InvalidInput);
    }
    let previous = *state;
    let predicted = std::array::from_fn(|i| 2.0 * state.node_v[i] - state.previous_node_v[i]);
    if predicted.iter().any(|v| !v.is_finite()) {
        return Err(StepError::InvalidInput);
    }
    let mut evaluations = 0;
    let (solution, fallback) = match solve_from_seed(
        previous,
        predicted,
        p,
        out_p,
        headphone,
        b,
        budget,
        &mut evaluations,
    ) {
        Ok(value) => (value, false),
        Err(_) => (
            solve_from_seed(
                previous,
                previous.node_v,
                p,
                out_p,
                headphone,
                b,
                budget,
                &mut evaluations,
            )?,
            true,
        ),
    };
    state.previous_node_v = previous.node_v;
    state.node_v = solution.0;
    state.downstream = solution.1;
    let mut result = solution.2;
    result.predictor_fallback = fallback;
    Ok(result)
}
