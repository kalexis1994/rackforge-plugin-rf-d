//! First VCA, including R2/C6/C15, coupled to VCA2/C4/C2/J7.
//! The recovery collector, both loudness controls and rails are boundaries.

use crate::output_conversion::{max_abs, solve_linear, Parameters as ConversionParameters};
use crate::vca2_output::{
    initial_state as initial_second, solve_input_port as second_port, Boundary as SecondBoundary,
    Parameters as VcaParameters, State as SecondState,
};
use crate::{Parameters as HeadphoneParameters, SolverBudget, StepError};

const N: usize = 10;
const K_B: f64 = 1.380_649e-23;
const Q_E: f64 = 1.602_176_634e-19;
const C6_F: f64 = 0.33e-6;
const C15_F: f64 = 220e-6;

pub const NODE_NAMES: [&str; N] = [
    "C6_LEFT",
    "Q16_BASE",
    "Q15_BASE",
    "PAIR_EMITTER",
    "Q18_COLLECTOR",
    "Q18_EMITTER",
    "Q16_COLLECTOR",
    "Q15_COLLECTOR",
    "Q18_BASE",
    "FIRST_BAL_WIPER",
];

#[derive(Clone, Copy, Debug)]
pub struct Boundary {
    pub recover_collector_v: f64,
    pub loudness_v: f64,
    pub first_balance_left_ohm: f64,
    pub second: SecondBoundary,
}

#[derive(Clone, Copy, Debug, PartialEq)]
pub struct State {
    pub node_v: [f64; N],
    pub previous_node_v: [f64; N],
    /// Voltage from C6_LEFT to Q16_BASE.
    pub c6_capacitor_v: f64,
    /// Voltage from Q15_BASE to ground.
    pub c15_capacitor_v: f64,
    pub second: SecondState,
}

#[derive(Clone, Copy, Debug)]
pub struct StepResult {
    pub j7_v: f64,
    pub j4_hi_v: f64,
    pub j5_lo_v: f64,
    pub iterations: usize,
    pub second_port_evaluations: usize,
    pub predictor_fallback: bool,
    pub max_kcl_residual_a: f64,
    /// Accepted VCA2 four-port current and tangent; reused by the R2 input port.
    pub second_current_a: [f64; 4],
    pub second_conductance_s: [[f64; 4]; 4],
}

/// Dynamic load seen at the filter recovery collector through R2 and C6.
#[derive(Clone, Copy, Debug)]
pub struct InputPort {
    pub next_state: State,
    pub result: StepResult,
    /// Positive from RECOVER_COLLECTOR into R2, in amperes.
    pub current_a: f64,
    /// d(current_a)/d(recover_collector_v), previous capacitors fixed, in S.
    pub conductance_s: f64,
}

fn second_boundary(x: &[f64; N], b: Boundary) -> SecondBoundary {
    let mut result = b.second;
    result.q14_base_v = x[6];
    result.q13_base_v = x[7];
    result.first_balance_wiper_v = x[9];
    result
}

fn validate(p: VcaParameters, b: Boundary, budget: SolverBudget) -> Result<(), StepError> {
    if !p.transistor_is_a.is_finite()
        || p.transistor_is_a <= 0.0
        || !p.beta_forward.is_finite()
        || p.beta_forward <= 0.0
        || !p.beta_reverse.is_finite()
        || p.beta_reverse <= 0.0
        || !p.temperature_k.is_finite()
        || p.temperature_k <= 0.0
        || !b.recover_collector_v.is_finite()
        || !b.loudness_v.is_finite()
        || !b.first_balance_left_ohm.is_finite()
        || !(0.0..=25.0).contains(&b.first_balance_left_ohm)
        || !b.second.minus_v.is_finite()
        || !b.second.q21_base_v.is_finite()
        || !b.second.output.plus_v.is_finite()
        || !b.second.output.output.dt_s.is_finite()
        || b.second.output.output.dt_s <= 0.0
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
    let vb = b.map_or(fixed, |i| x[i]);
    let i = (x[a] - vb) * g;
    r[a] += i;
    j[a][a] += g;
    if let Some(b) = b {
        r[b] -= i;
        j[b][b] += g;
        j[a][b] -= g;
        j[b][a] -= g;
    }
}

fn npn(
    x: &[f64; N],
    r: &mut [f64; N],
    j: &mut [[f64; N]; N],
    base: usize,
    collector: usize,
    emitter: usize,
    p: VcaParameters,
) -> Result<(), StepError> {
    let vt = K_B * p.temperature_k / Q_E;
    let f = (x[base] - x[emitter]) / vt;
    let rev = (x[base] - x[collector]) / vt;
    if !f.is_finite() || !rev.is_finite() || f.max(rev) > 45.0 {
        return Err(StepError::ExponentialDomain);
    }
    let forward = p.transistor_is_a * f.exp_m1();
    let reverse = p.transistor_is_a * rev.exp_m1();
    let gf = p.transistor_is_a * f.exp() / vt;
    let gr = p.transistor_is_a * rev.exp() / vt;
    let ib = forward / p.beta_forward + reverse / p.beta_reverse;
    let ic = forward - (1.0 + 1.0 / p.beta_reverse) * reverse;
    r[base] += ib;
    r[collector] += ic;
    r[emitter] -= ib + ic;
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
    let columns = [base, collector, emitter];
    for k in 0..3 {
        j[base][columns[k]] += dib[k];
        j[collector][columns[k]] += dic[k];
        j[emitter][columns[k]] -= dib[k] + dic[k];
    }
    Ok(())
}

fn evaluate(
    x: &[f64; N],
    p: VcaParameters,
    b: Boundary,
    old_caps: Option<[f64; 2]>,
    port: [f64; 4],
    tangent: Option<[[f64; 4]; 4]>,
) -> Result<([f64; N], [[f64; N]; N]), StepError> {
    let mut r = [0.0; N];
    let mut j = [[0.0; N]; N];
    resistor(x, &mut r, &mut j, 0, None, b.recover_collector_v, 82000.0); // R2
    resistor(x, &mut r, &mut j, 1, Some(2), 0.0, 820.0); // R34
    resistor(x, &mut r, &mut j, 2, Some(9), 0.0, 120.0); // R22
    resistor(x, &mut r, &mut j, 2, None, 0.0, 510.0); // R36
    resistor(x, &mut r, &mut j, 3, Some(4), 0.0, 1000.0); // R35
    resistor(x, &mut r, &mut j, 5, None, 0.0, 6800.0); // R37
    resistor(x, &mut r, &mut j, 5, None, b.second.minus_v, 270000.0); // R43
    resistor(
        x,
        &mut r,
        &mut j,
        6,
        Some(9),
        0.0,
        100.0 + b.first_balance_left_ohm,
    ); // R19/R14L
    resistor(
        x,
        &mut r,
        &mut j,
        7,
        Some(9),
        0.0,
        125.0 - b.first_balance_left_ohm,
    ); // R23/R14R
    resistor(x, &mut r, &mut j, 8, None, b.loudness_v, 68000.0); // R59
    npn(x, &mut r, &mut j, 1, 6, 3, p)?; // Q16
    npn(x, &mut r, &mut j, 2, 7, 3, p)?; // Q15
    npn(x, &mut r, &mut j, 8, 4, 5, p)?; // Q18
    r[6] += port[0];
    r[7] += port[1];
    r[9] += port[3];
    if let Some(tangent) = tangent {
        let rows = [6, 7, 9];
        let ports = [0, 1, 3];
        for a in 0..3 {
            for c in 0..3 {
                j[rows[a]][rows[c]] += tangent[ports[a]][ports[c]];
            }
        }
    }
    if let Some(old) = old_caps {
        let g6 = C6_F / b.second.output.output.dt_s;
        let i6 = g6 * (x[0] - x[1] - old[0]);
        r[0] += i6;
        r[1] -= i6;
        j[0][0] += g6;
        j[0][1] -= g6;
        j[1][0] -= g6;
        j[1][1] += g6;
        let g15 = C15_F / b.second.output.output.dt_s;
        r[2] += g15 * (x[2] - old[1]);
        j[2][2] += g15;
    }
    if r.iter().any(|v| !v.is_finite()) || j.iter().flatten().any(|v| !v.is_finite()) {
        return Err(StepError::ExponentialDomain);
    }
    Ok((r, j))
}

fn base_current(base: f64, collector: f64, emitter: f64, p: VcaParameters) -> f64 {
    let vt = K_B * p.temperature_k / Q_E;
    p.transistor_is_a
        * (((base - emitter) / vt).exp_m1() / p.beta_forward
            + ((base - collector) / vt).exp_m1() / p.beta_reverse)
}

fn dc_trial(
    x: &[f64; N],
    p: VcaParameters,
    conversion: ConversionParameters,
    headphone: HeadphoneParameters,
    b: Boundary,
) -> Result<([f64; N], SecondState), StepError> {
    let second = initial_second(p, conversion, headphone, second_boundary(x, b))?;
    let y = second.node_v;
    let port = [
        base_current(x[6], y[3], y[0], p),
        base_current(x[7], y[4], y[0], p),
        0.0,
        (x[9] - y[5]) / 120.0,
    ];
    Ok((evaluate(x, p, b, None, port, None)?.0, second))
}

/// DC initialization: C6 and C15 open, all downstream capacitors open.
pub fn initial_state(
    p: VcaParameters,
    conversion: ConversionParameters,
    headphone: HeadphoneParameters,
    b: Boundary,
) -> Result<State, StepError> {
    validate(p, b, SolverBudget::default())?;
    // Numerical seed for the nominal conducting branch; no circuit parameter.
    let mut x = [
        b.recover_collector_v,
        4.9059,
        4.9068,
        4.3124,
        4.0910,
        1.2374,
        6.0492,
        6.0488,
        1.8495,
        6.0616,
    ];
    for _ in 0..24 {
        let (r, second) = dc_trial(&x, p, conversion, headphone, b)?;
        let error = max_abs(&r);
        if error < 1e-12 {
            return Ok(State {
                node_v: x,
                previous_node_v: x,
                c6_capacitor_v: x[0] - x[1],
                c15_capacitor_v: x[2],
                second,
            });
        }
        let mut j = [[0.0; N]; N];
        for col in 0..N {
            let mut high = x;
            high[col] += 1e-6;
            let rh = dc_trial(&high, p, conversion, headphone, b)?.0;
            for row in 0..N {
                j[row][col] = (rh[row] - r[row]) / 1e-6;
            }
        }
        let direction = solve_linear(j, r.map(|v| -v))?;
        let mut accepted = false;
        for power in 0..16 {
            let factor = 0.5_f64.powi(power);
            let trial = std::array::from_fn(|i| x[i] + factor * direction[i]);
            if let Ok((next, _)) = dc_trial(&trial, p, conversion, headphone, b) {
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

fn transient_trial(
    previous: State,
    x: &[f64; N],
    p: VcaParameters,
    conversion: ConversionParameters,
    headphone: HeadphoneParameters,
    b: Boundary,
    budget: SolverBudget,
) -> Result<([f64; N], [[f64; N]; N], SecondState, StepResult), StepError> {
    let port = second_port(
        &previous.second,
        p,
        conversion,
        headphone,
        second_boundary(x, b),
        budget,
    )?;
    let (r, j) = evaluate(
        x,
        p,
        b,
        Some([previous.c6_capacitor_v, previous.c15_capacitor_v]),
        port.current_a,
        Some(port.conductance_s),
    )?;
    let result = StepResult {
        j7_v: port.result.j7_v,
        j4_hi_v: port.result.j4_hi_v,
        j5_lo_v: port.result.j5_lo_v,
        iterations: 0,
        second_port_evaluations: 0,
        predictor_fallback: false,
        max_kcl_residual_a: max_abs(&r),
        second_current_a: port.current_a,
        second_conductance_s: port.conductance_s,
    };
    Ok((r, j, port.next_state, result))
}

fn solve_from_seed(
    previous: State,
    mut x: [f64; N],
    p: VcaParameters,
    conversion: ConversionParameters,
    headphone: HeadphoneParameters,
    b: Boundary,
    budget: SolverBudget,
    evaluations: &mut usize,
) -> Result<([f64; N], SecondState, StepResult), StepError> {
    let mut cached = None;
    for iteration in 0..budget.iterations {
        let (r, j, second, mut result) = match cached.take() {
            Some(value) => value,
            None => {
                *evaluations += 1;
                transient_trial(previous, &x, p, conversion, headphone, b, budget)?
            }
        };
        let error = max_abs(&r);
        if error < 1e-10 {
            result.iterations = iteration;
            result.second_port_evaluations = *evaluations;
            result.max_kcl_residual_a = error;
            return Ok((x, second, result));
        }
        let direction = solve_linear(j, r.map(|v| -v))?;
        let mut accepted = None;
        for power in 0..budget.line_search_halvings {
            let factor = 0.5_f64.powi(power as i32);
            let trial = std::array::from_fn(|i| x[i] + factor * direction[i]);
            *evaluations += 1;
            if let Ok(next) = transient_trial(previous, &trial, p, conversion, headphone, b, budget)
            {
                if max_abs(&next.0) < error {
                    accepted = Some((trial, next));
                    break;
                }
            }
        }
        if let Some((trial, next)) = accepted {
            x = trial;
            cached = Some(next);
        } else {
            return Err(StepError::NoDecrease);
        }
    }
    Err(StepError::IterationBudget)
}

/// Fixed-size, allocation-free joint step; no state is committed on failure.
pub fn step(
    state: &mut State,
    p: VcaParameters,
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
        .any(|v| !v.is_finite())
        || !state.c6_capacitor_v.is_finite()
        || !state.c15_capacitor_v.is_finite()
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
    state.c6_capacitor_v = solution.0[0] - solution.0[1];
    state.c15_capacitor_v = solution.0[2];
    state.second = solution.1;
    let mut result = solution.2;
    result.predictor_fallback = fallback;
    Ok(result)
}

/// Provisional input-port solve for the future filter/VCA joint Newton.
/// Each trial begins at the same previous state; only commit the accepted one.
pub fn solve_input_port(
    previous: &State,
    p: VcaParameters,
    conversion: ConversionParameters,
    headphone: HeadphoneParameters,
    b: Boundary,
    budget: SolverBudget,
) -> Result<InputPort, StepError> {
    let mut next_state = *previous;
    let result = step(&mut next_state, p, conversion, headphone, b, budget)?;
    let x = next_state.node_v;
    let (_, jacobian) = evaluate(
        &x,
        p,
        b,
        Some([previous.c6_capacitor_v, previous.c15_capacitor_v]),
        result.second_current_a,
        Some(result.second_conductance_s),
    )?;
    let mut rhs = [0.0; N];
    rhs[0] = 1.0 / 82000.0;
    let response = solve_linear(jacobian, rhs)?;
    let current_a = (b.recover_collector_v - x[0]) / 82000.0;
    let conductance_s = (1.0 - response[0]) / 82000.0;
    if !current_a.is_finite() || !conductance_s.is_finite() {
        return Err(StepError::ExponentialDomain);
    }
    Ok(InputPort {
        next_state,
        result,
        current_a,
        conductance_s,
    })
}
