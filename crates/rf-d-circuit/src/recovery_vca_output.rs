//! Q8/Q6/Q7/Q5 recovery through R2/C6, both VCAs and J7.
//! Ladder top emitters remain imposed voltage boundaries; C10 is open.

use crate::output_conversion::{max_abs, solve_linear, Parameters as ConversionParameters};
use crate::vca1_output::{
    initial_state as initial_vca, solve_input_port as vca_port, Boundary as VcaBoundary,
    State as VcaState,
};
use crate::vca2_output::Parameters as TransistorParameters;
use crate::{Parameters as HeadphoneParameters, SolverBudget, StepError};

const N: usize = 8;
const K_B: f64 = 1.380_649e-23;
const Q_E: f64 = 1.602_176_634e-19;
const C5_F: f64 = 0.22e-6;
const C1_F: f64 = 0.22e-6;
const C9_F: f64 = 100e-6;

pub const NODE_NAMES: [&str; N] = [
    "Q8_BASE",
    "Q6_BASE",
    "Q8_EMITTER_Q7_BASE",
    "Q6_EMITTER_Q5_BASE",
    "RECOVER_TAIL",
    "RECOVER_COLLECTOR",
    "RECOVER_R7_R3",
    "RECOVER_R6_R7",
];

#[derive(Clone, Copy, Debug)]
pub struct Boundary {
    pub ladder_left_v: f64,
    pub ladder_right_v: f64,
    pub vca: VcaBoundary,
}

#[derive(Clone, Copy, Debug, PartialEq)]
pub struct State {
    pub node_v: [f64; N],
    pub previous_node_v: [f64; N],
    /// Base minus imposed ladder emitter for C5 and C1; R6/R7 node to ground for C9.
    pub capacitor_v: [f64; 3],
    pub vca: VcaState,
}

#[derive(Clone, Copy, Debug)]
pub struct StepResult {
    pub j7_v: f64,
    pub j4_hi_v: f64,
    pub j5_lo_v: f64,
    pub iterations: usize,
    pub vca_port_evaluations: usize,
    pub predictor_fallback: bool,
    pub max_kcl_residual_a: f64,
}

fn vca_boundary(x: &[f64; N], b: Boundary) -> VcaBoundary {
    let mut result = b.vca;
    result.recover_collector_v = x[5];
    result
}

fn validate(p: TransistorParameters, b: Boundary, budget: SolverBudget) -> Result<(), StepError> {
    if !p.transistor_is_a.is_finite()
        || p.transistor_is_a <= 0.0
        || !p.beta_forward.is_finite()
        || p.beta_forward <= 0.0
        || !p.beta_reverse.is_finite()
        || p.beta_reverse <= 0.0
        || !p.temperature_k.is_finite()
        || p.temperature_k <= 0.0
        || !b.ladder_left_v.is_finite()
        || !b.ladder_right_v.is_finite()
        || !b.vca.second.minus_v.is_finite()
        || !b.vca.second.output.plus_v.is_finite()
        || b.vca.second.output.plus_v <= b.vca.second.minus_v
        || !b.vca.second.output.output.dt_s.is_finite()
        || b.vca.second.output.output.dt_s <= 0.0
        || !(1..=16).contains(&budget.iterations)
        || !(1..=16).contains(&budget.line_search_halvings)
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
    fixed: f64,
    ohm: f64,
) {
    let g = 1.0 / ohm;
    let vb = b.map_or(fixed, |index| x[index]);
    let current = (x[a] - vb) * g;
    r[a] += current;
    j[a][a] += g;
    if let Some(index) = b {
        r[index] -= current;
        j[index][index] += g;
        j[a][index] -= g;
        j[index][a] -= g;
    }
}

fn npn(
    x: &[f64; N],
    r: &mut [f64; N],
    j: &mut [[f64; N]; N],
    base: usize,
    collector: Option<usize>,
    fixed_collector_v: f64,
    emitter: usize,
    p: TransistorParameters,
) -> Result<(), StepError> {
    let vc = collector.map_or(fixed_collector_v, |index| x[index]);
    let vt = K_B * p.temperature_k / Q_E;
    let f = (x[base] - x[emitter]) / vt;
    let rev = (x[base] - vc) / vt;
    if !f.is_finite() || !rev.is_finite() || f.max(rev) > 45.0 {
        return Err(StepError::ExponentialDomain);
    }
    let forward = p.transistor_is_a * f.exp_m1();
    let reverse = p.transistor_is_a * rev.exp_m1();
    let gf = p.transistor_is_a * f.exp() / vt;
    let gr = p.transistor_is_a * rev.exp() / vt;
    let ib = forward / p.beta_forward + reverse / p.beta_reverse;
    let ic = forward - (1.0 + 1.0 / p.beta_reverse) * reverse;
    let terminal = [Some(base), collector, Some(emitter)];
    let current = [ib, ic, -ib - ic];
    let dib = [
        gf / p.beta_forward + gr / p.beta_reverse,
        -gr / p.beta_reverse,
        -gf / p.beta_forward,
    ];
    let dic = [
        gf - (1.0 + 1.0 / p.beta_reverse) * gr,
        (1.0 + 1.0 / p.beta_reverse) * gr,
        -gf,
    ];
    let slopes = [dib, dic, std::array::from_fn(|k| -dib[k] - dic[k])];
    for row in 0..3 {
        if let Some(node) = terminal[row] {
            r[node] += current[row];
            for column in 0..3 {
                if let Some(other) = terminal[column] {
                    j[node][other] += slopes[row][column];
                }
            }
        }
    }
    Ok(())
}

fn evaluate(
    x: &[f64; N],
    p: TransistorParameters,
    b: Boundary,
    old_caps: Option<[f64; 3]>,
    load: Option<(f64, f64)>,
) -> Result<([f64; N], [[f64; N]; N]), StepError> {
    let mut r = [0.0; N];
    let mut j = [[0.0; N]; N];
    let plus = b.vca.second.output.plus_v;
    let minus = b.vca.second.minus_v;
    resistor(x, &mut r, &mut j, 0, None, 0.0, 47000.0); // R31
    resistor(x, &mut r, &mut j, 1, None, 0.0, 47000.0); // R38
    resistor(x, &mut r, &mut j, 2, None, minus, 220000.0); // R24
    resistor(x, &mut r, &mut j, 3, None, minus, 100000.0); // R20
    resistor(x, &mut r, &mut j, 4, None, minus, 1000.0); // R26
    resistor(x, &mut r, &mut j, 5, Some(6), 0.0, 1000.0); // R3
    resistor(x, &mut r, &mut j, 6, Some(7), 0.0, 180.0); // R7
    resistor(x, &mut r, &mut j, 7, None, plus, 47.0); // R6
    npn(x, &mut r, &mut j, 0, Some(5), 0.0, 2, p)?; // Q8
    npn(x, &mut r, &mut j, 1, None, plus, 3, p)?; // Q6
    npn(x, &mut r, &mut j, 2, Some(5), 0.0, 4, p)?; // Q7
    npn(x, &mut r, &mut j, 3, None, plus, 4, p)?; // Q5
    if let Some((current, tangent)) = load {
        r[5] += current;
        j[5][5] += tangent;
    }
    if let Some(old) = old_caps {
        let dt = b.vca.second.output.output.dt_s;
        let g5 = C5_F / dt;
        let g1 = C1_F / dt;
        let g9 = C9_F / dt;
        r[0] += g5 * (x[0] - b.ladder_left_v - old[0]);
        j[0][0] += g5;
        r[1] += g1 * (x[1] - b.ladder_right_v - old[1]);
        j[1][1] += g1;
        r[7] += g9 * (x[7] - old[2]);
        j[7][7] += g9;
    }
    if r.iter().any(|v| !v.is_finite()) || j.iter().flatten().any(|v| !v.is_finite()) {
        return Err(StepError::ExponentialDomain);
    }
    Ok((r, j))
}

/// DC initializer: C1/C5/C9/C10 and all downstream capacitors are open.
pub fn initial_state(
    p: TransistorParameters,
    conversion: ConversionParameters,
    headphone: HeadphoneParameters,
    b: Boundary,
) -> Result<State, StepError> {
    validate(p, b, SolverBudget::default())?;
    let mut x = [0.0, 0.0, -0.6, -0.6, -1.3, 2.96, 8.7, 9.7];
    for _ in 0..24 {
        let (r, j) = evaluate(&x, p, b, None, None)?;
        let error = max_abs(&r);
        if error < 1e-12 {
            let vca = initial_vca(p, conversion, headphone, vca_boundary(&x, b))?;
            return Ok(State {
                node_v: x,
                previous_node_v: x,
                capacitor_v: [x[0] - b.ladder_left_v, x[1] - b.ladder_right_v, x[7]],
                vca,
            });
        }
        let direction = solve_linear(j, r.map(|value| -value))?;
        let mut accepted = false;
        for power in 0..16 {
            let factor = 0.5_f64.powi(power);
            let trial = std::array::from_fn(|i| x[i] + factor * direction[i]);
            if let Ok((next, _)) = evaluate(&trial, p, b, None, None) {
                if max_abs(&next) < error {
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

fn trial(
    previous: State,
    x: &[f64; N],
    p: TransistorParameters,
    conversion: ConversionParameters,
    headphone: HeadphoneParameters,
    b: Boundary,
    budget: SolverBudget,
) -> Result<([f64; N], [[f64; N]; N], VcaState, StepResult), StepError> {
    let port = vca_port(
        &previous.vca,
        p,
        conversion,
        headphone,
        vca_boundary(x, b),
        budget,
    )?;
    let (r, j) = evaluate(
        x,
        p,
        b,
        Some(previous.capacitor_v),
        Some((port.current_a, port.conductance_s)),
    )?;
    let result = StepResult {
        j7_v: port.result.j7_v,
        j4_hi_v: port.result.j4_hi_v,
        j5_lo_v: port.result.j5_lo_v,
        iterations: 0,
        vca_port_evaluations: 0,
        predictor_fallback: false,
        max_kcl_residual_a: max_abs(&r),
    };
    Ok((r, j, port.next_state, result))
}

fn solve_from_seed(
    previous: State,
    mut x: [f64; N],
    p: TransistorParameters,
    conversion: ConversionParameters,
    headphone: HeadphoneParameters,
    b: Boundary,
    budget: SolverBudget,
    evaluations: &mut usize,
) -> Result<([f64; N], VcaState, StepResult), StepError> {
    let mut cached = None;
    for iteration in 0..budget.iterations {
        let (r, j, vca, mut result) = match cached.take() {
            Some(value) => value,
            None => {
                *evaluations += 1;
                trial(previous, &x, p, conversion, headphone, b, budget)?
            }
        };
        let error = max_abs(&r);
        if error < 1e-10 {
            result.iterations = iteration;
            result.vca_port_evaluations = *evaluations;
            result.max_kcl_residual_a = error;
            return Ok((x, vca, result));
        }
        let direction = solve_linear(j, r.map(|value| -value))?;
        let mut accepted = None;
        for power in 0..budget.line_search_halvings {
            let factor = 0.5_f64.powi(power as i32);
            let candidate = std::array::from_fn(|i| x[i] + factor * direction[i]);
            *evaluations += 1;
            if let Ok(next) = trial(previous, &candidate, p, conversion, headphone, b, budget) {
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

/// Joint step. Failure leaves recovery, C1/C5/C9 and the entire output unchanged.
pub fn step(
    state: &mut State,
    p: TransistorParameters,
    conversion: ConversionParameters,
    headphone: HeadphoneParameters,
    b: Boundary,
    budget: SolverBudget,
) -> Result<StepResult, StepError> {
    validate(p, b, budget)?;
    if state
        .node_v
        .iter()
        .chain(state.previous_node_v.iter())
        .chain(state.capacitor_v.iter())
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
        conversion,
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
                conversion,
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
    state.capacitor_v = [
        solution.0[0] - b.ladder_left_v,
        solution.0[1] - b.ladder_right_v,
        solution.0[7],
    ];
    state.vca = solution.1;
    let mut result = solution.2;
    result.predictor_fallback = fallback;
    Ok(result)
}
