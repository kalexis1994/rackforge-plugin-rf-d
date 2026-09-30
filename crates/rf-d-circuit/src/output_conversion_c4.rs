//! Q1 base R10/R11/C4 coupled to Q1/Q12/Q17 and the complete C2 output.
//! The second VCA balance wiper and Q12/Q17 bases remain imposed.

use crate::output::{
    initial_output_state, solve_output_input_port, OutputBoundary, OutputInputPort, OutputState,
    OutputStepResult,
};
use crate::output_conversion::{
    evaluate as evaluate_six, max_abs, solve_dc, solve_linear, validate, Boundary, Parameters, N,
};
use crate::{Parameters as HeadphoneParameters, SolverBudget, StepError};

const M: usize = N + 1;
const R10_OHM: f64 = 120.0;
const R11_OHM: f64 = 150.0;
const C4_F: f64 = 220e-6;
const K_B: f64 = 1.380_649e-23;
const Q_E: f64 = 1.602_176_634e-19;

pub const NODE_NAMES: [&str; M] = [
    "Q1_BASE",
    "Q1_EMITTER",
    "Q1_COLLECTOR",
    "Q12_EMITTER",
    "Q17_EMITTER",
    "Q12_COLLECTOR",
    "Q17_COLLECTOR",
];

#[derive(Clone, Copy, Debug, PartialEq)]
pub struct State {
    pub node_v: [f64; M],
    /// Q1_BASE minus the +10 V rail; C4 positive terminal is on the rail.
    pub c4_capacitor_v: f64,
    /// Previous accepted voltages, used only to seed Newton.
    pub previous_node_v: [f64; M],
    pub output: OutputState,
}

#[derive(Clone, Copy, Debug)]
pub struct BoundaryC4 {
    pub second_balance_wiper_v: f64,
    pub q12_base_v: f64,
    pub q17_base_v: f64,
    pub plus_v: f64,
    pub output: OutputBoundary,
}

#[derive(Clone, Copy, Debug)]
pub struct ResultC4 {
    pub output: OutputStepResult,
    pub iterations: usize,
    pub output_port_evaluations: usize,
    pub predictor_fallback: bool,
    pub max_kcl_residual_a: f64,
    /// Complete downstream d(I_C2)/d(V_Q17c) at the accepted state.
    pub c2_input_conductance_s: f64,
}

/// Currents presented to the upstream second VCA. Order: second balance
/// wiper into R11, Q12 base into Q14 collector, Q17 base into Q13 collector.
#[derive(Clone, Copy, Debug)]
pub struct InputPortC4 {
    pub next_state: State,
    pub result: ResultC4,
    pub current_a: [f64; 3],
    /// Row = port current, column = imposed upstream voltage in the same order.
    pub conductance_s: [[f64; 3]; 3],
}

fn six_boundary(x: &[f64; M], b: BoundaryC4) -> Boundary {
    Boundary {
        q1_base_v: x[0],
        q12_base_v: b.q12_base_v,
        q17_base_v: b.q17_base_v,
        plus_v: b.plus_v,
    }
}

fn q1_slopes(x: &[f64; M], p: Parameters) -> (f64, f64, f64) {
    let vt = K_B * p.temperature_k / Q_E;
    let gf = p.transistor_is_a * ((x[1] - x[0]) / vt).exp() / vt;
    let gr = p.transistor_is_a * ((x[2] - x[0]) / vt).exp() / vt;
    let ib = p.transistor_is_a
        * (((x[1] - x[0]) / vt).exp_m1() / p.beta_forward
            + ((x[2] - x[0]) / vt).exp_m1() / p.beta_reverse);
    (ib, gf, gr)
}

fn evaluate(
    x: &[f64; M],
    p: Parameters,
    b: BoundaryC4,
    old_c4_v: f64,
    dt_s: f64,
    port: Option<(f64, f64)>,
) -> Result<([f64; M], [[f64; M]; M]), StepError> {
    let stage = std::array::from_fn(|i| x[i + 1]);
    let (six_r, six_j) = evaluate_six(&stage, p, six_boundary(x, b))?;
    let (ib, gf, gr) = q1_slopes(x, p);
    let g4 = C4_F / dt_s;
    let i4 = g4 * (x[0] - b.plus_v - old_c4_v);
    let mut r = [0.0; M];
    let mut j = [[0.0; M]; M];
    r[0] = (x[0] - b.plus_v) / R10_OHM + (x[0] - b.second_balance_wiper_v) / R11_OHM + i4 - ib;
    j[0][0] = 1.0 / R10_OHM + 1.0 / R11_OHM + g4 + gf / p.beta_forward + gr / p.beta_reverse;
    j[0][1] = -gf / p.beta_forward;
    j[0][2] = -gr / p.beta_reverse;
    r[1..].copy_from_slice(&six_r);
    for row in 0..N {
        j[row + 1][1..].copy_from_slice(&six_j[row]);
    }
    j[1][0] = -(1.0 + 1.0 / p.beta_forward) * gf + gr;
    j[2][0] = gf - (1.0 + 1.0 / p.beta_reverse) * gr;
    if let Some((current, tangent)) = port {
        r[6] += current;
        j[6][6] += tangent;
    }
    if r.iter().any(|v| !v.is_finite()) || j.iter().flatten().any(|v| !v.is_finite()) {
        return Err(StepError::ExponentialDomain);
    }
    Ok((r, j))
}

fn validate_boundary(p: Parameters, b: BoundaryC4) -> Result<(), StepError> {
    validate(
        p,
        Boundary {
            q1_base_v: b.second_balance_wiper_v,
            q12_base_v: b.q12_base_v,
            q17_base_v: b.q17_base_v,
            plus_v: b.plus_v,
        },
    )?;
    Ok(())
}

/// DC-consistent initialization: C4 and C2 are open, panel/board 3 are at DC.
pub fn initial_state(
    p: Parameters,
    headphone: HeadphoneParameters,
    b: BoundaryC4,
) -> Result<State, StepError> {
    validate_boundary(p, b)?;
    let seed_boundary = Boundary {
        q1_base_v: 8.3,
        q12_base_v: b.q12_base_v,
        q17_base_v: b.q17_base_v,
        plus_v: b.plus_v,
    };
    let seed = solve_dc(p, seed_boundary)?.state.node_v;
    let mut x = std::array::from_fn(|i| if i == 0 { 8.3 } else { seed[i - 1] });
    for _ in 0..16 {
        let (r, j) = evaluate(&x, p, b, 0.0, f64::INFINITY, None)?;
        let error = max_abs(&r);
        if error < 1e-12 {
            let output = initial_output_state(headphone, x[6])?;
            return Ok(State {
                node_v: x,
                c4_capacitor_v: x[0] - b.plus_v,
                previous_node_v: x,
                output,
            });
        }
        let direction = solve_linear(j, r.map(|v| -v))?;
        let mut accepted = false;
        for power in 0..16 {
            let factor = 0.5_f64.powi(power);
            let candidate = std::array::from_fn(|i| x[i] + factor * direction[i]);
            if let Ok((next, _)) = evaluate(&candidate, p, b, 0.0, f64::INFINITY, None) {
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

fn trial(
    previous: State,
    x: &[f64; M],
    p: Parameters,
    headphone: HeadphoneParameters,
    b: BoundaryC4,
    budget: SolverBudget,
) -> Result<([f64; M], [[f64; M]; M], OutputInputPort), StepError> {
    let mut output_boundary = b.output;
    output_boundary.q17_collector_v = x[6];
    let port = solve_output_input_port(&previous.output, headphone, output_boundary, budget)?;
    let (r, j) = evaluate(
        x,
        p,
        b,
        previous.c4_capacitor_v,
        b.output.dt_s,
        Some((port.current_a, port.conductance_s)),
    )?;
    Ok((r, j, port))
}

fn solve_from_seed(
    previous: State,
    mut x: [f64; M],
    p: Parameters,
    headphone: HeadphoneParameters,
    b: BoundaryC4,
    budget: SolverBudget,
    ports: &mut usize,
) -> Result<([f64; M], OutputInputPort, ResultC4), StepError> {
    let mut cached = None;
    for iteration in 0..budget.iterations {
        let (r, j, port) = match cached.take() {
            Some(value) => value,
            None => {
                *ports += 1;
                trial(previous, &x, p, headphone, b, budget)?
            }
        };
        let error = max_abs(&r);
        if error < 1e-10 {
            if p.diode.is_none() && !(0.0..=b.plus_v).contains(&x[6]) {
                return Err(StepError::ExponentialDomain);
            }
            let result = ResultC4 {
                output: port.output,
                iterations: iteration,
                output_port_evaluations: *ports,
                predictor_fallback: false,
                max_kcl_residual_a: error,
                c2_input_conductance_s: port.conductance_s,
            };
            return Ok((x, port, result));
        }
        let direction = solve_linear(j, r.map(|v| -v))?;
        let mut accepted = None;
        for power in 0..budget.line_search_halvings {
            let factor = 0.5_f64.powi(power as i32);
            let candidate = std::array::from_fn(|i| x[i] + factor * direction[i]);
            *ports += 1;
            if let Ok(next) = trial(previous, &candidate, p, headphone, b, budget) {
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

/// Atomic seven-node board-4/C4 and C2/panel/board-3 implicit Euler step.
pub fn step(
    state: &mut State,
    p: Parameters,
    headphone: HeadphoneParameters,
    b: BoundaryC4,
    budget: SolverBudget,
) -> Result<ResultC4, StepError> {
    validate_boundary(p, b)?;
    if !b.output.dt_s.is_finite()
        || b.output.dt_s <= 0.0
        || !(1..=16).contains(&budget.iterations)
        || !(1..=16).contains(&budget.line_search_halvings)
        || !state.c4_capacitor_v.is_finite()
        || state
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
    let mut ports = 0;
    let (solution, fallback) =
        match solve_from_seed(previous, predicted, p, headphone, b, budget, &mut ports) {
            Ok(value) => (value, false),
            Err(_) => (
                solve_from_seed(
                    previous,
                    previous.node_v,
                    p,
                    headphone,
                    b,
                    budget,
                    &mut ports,
                )?,
                true,
            ),
        };
    state.previous_node_v = previous.node_v;
    state.node_v = solution.0;
    state.c4_capacitor_v = solution.0[0] - b.plus_v;
    state.output = solution.1.next_state;
    let mut result = solution.2;
    result.predictor_fallback = fallback;
    Ok(result)
}

fn pnp_base_terms(emitter_v: f64, collector_v: f64, base_v: f64, p: Parameters) -> (f64, f64, f64) {
    let vt = K_B * p.temperature_k / Q_E;
    let forward = (emitter_v - base_v) / vt;
    let reverse = (collector_v - base_v) / vt;
    let ib =
        p.transistor_is_a * (forward.exp_m1() / p.beta_forward + reverse.exp_m1() / p.beta_reverse);
    let gf = p.transistor_is_a * forward.exp() / vt;
    let gr = p.transistor_is_a * reverse.exp() / vt;
    (ib, gf, gr)
}

/// Return the provisional seven-node/C4/C2 output state and exact local
/// three-port tangent. Every caller trial must pass the same previous state.
pub fn solve_input_port(
    previous: &State,
    p: Parameters,
    headphone: HeadphoneParameters,
    b: BoundaryC4,
    budget: SolverBudget,
) -> Result<InputPortC4, StepError> {
    let mut next_state = *previous;
    let result = step(&mut next_state, p, headphone, b, budget)?;
    let x = next_state.node_v;
    let (_, jacobian) = evaluate(
        &x,
        p,
        b,
        previous.c4_capacitor_v,
        b.output.dt_s,
        Some((result.output.c2_current_a, result.c2_input_conductance_s)),
    )?;
    let (q12_ib, q12_gf, q12_gr) = pnp_base_terms(x[3], x[5], b.q12_base_v, p);
    let (q17_ib, q17_gf, q17_gr) = pnp_base_terms(x[4], x[6], b.q17_base_v, p);
    let current_a = [(b.second_balance_wiper_v - x[0]) / R11_OHM, q12_ib, q17_ib];
    let mut conductance_s = [[0.0; 3]; 3];
    for column in 0..3 {
        let mut rhs = [0.0; M];
        match column {
            0 => rhs[0] = 1.0 / R11_OHM,
            1 => {
                rhs[3] = (1.0 + 1.0 / p.beta_forward) * q12_gf - q12_gr;
                rhs[5] = -q12_gf + (1.0 + 1.0 / p.beta_reverse) * q12_gr;
            }
            _ => {
                rhs[4] = (1.0 + 1.0 / p.beta_forward) * q17_gf - q17_gr;
                rhs[6] = -q17_gf + (1.0 + 1.0 / p.beta_reverse) * q17_gr;
            }
        }
        let response = solve_linear(jacobian, rhs)?;
        conductance_s[0][column] = (f64::from(column == 0) - response[0]) / R11_OHM;
        conductance_s[1][column] = q12_gf / p.beta_forward * response[3]
            + q12_gr / p.beta_reverse * response[5]
            - f64::from(column == 1) * (q12_gf / p.beta_forward + q12_gr / p.beta_reverse);
        conductance_s[2][column] = q17_gf / p.beta_forward * response[4]
            + q17_gr / p.beta_reverse * response[6]
            - f64::from(column == 2) * (q17_gf / p.beta_forward + q17_gr / p.beta_reverse);
    }
    if current_a.iter().any(|v| !v.is_finite())
        || conductance_s.iter().flatten().any(|v| !v.is_finite())
    {
        return Err(StepError::ExponentialDomain);
    }
    Ok(InputPortC4 {
        next_state,
        result,
        current_a,
        conductance_s,
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::output_conversion::DiodeParameters;

    #[test]
    fn q1_base_analytic_tangent_matches_symmetric_perturbations() {
        let p = Parameters {
            transistor_is_a: 1e-14,
            beta_forward: 100.0,
            beta_reverse: 5.0,
            temperature_k: 298.15,
            diode: Some(DiodeParameters {
                is_a: 1.293_303_751_274_349e-9,
                ideality: 1.5,
            }),
        };
        let headphone = HeadphoneParameters {
            transistor_is_a: 1e-14,
            beta_forward: 160.0,
            beta_reverse: 5.0,
            temperature_k: 298.15,
            diode_is_a: 1.293_303_751_274_349e-9,
            diode_ideality: 1.5,
        };
        let b = BoundaryC4 {
            second_balance_wiper_v: 6.2,
            q12_base_v: 7.75,
            q17_base_v: 7.75,
            plus_v: 10.0,
            output: OutputBoundary {
                q17_collector_v: 0.0,
                r20_lower_ohm: 2500.0,
                hi_load_ohm: 10000.0,
                lo_load_ohm: 100000.0,
                sw18_on: true,
                r21_lower_ohm: 2000.0,
                tip_load_ohm: Some(32.0),
                ring_load_ohm: Some(32.0),
                dt_s: 1.0 / 48000.0,
            },
        };
        let state = initial_state(p, headphone, b).unwrap();
        let (_, jacobian) = evaluate(
            &state.node_v,
            p,
            b,
            state.c4_capacitor_v,
            b.output.dt_s,
            None,
        )
        .unwrap();
        let h = 1e-7;
        for column in 0..3 {
            let mut plus = state.node_v;
            let mut minus = state.node_v;
            plus[column] += h;
            minus[column] -= h;
            let high = evaluate(&plus, p, b, state.c4_capacitor_v, b.output.dt_s, None)
                .unwrap()
                .0;
            let low = evaluate(&minus, p, b, state.c4_capacitor_v, b.output.dt_s, None)
                .unwrap()
                .0;
            for row in 0..3 {
                let finite_difference = (high[row] - low[row]) / (2.0 * h);
                assert!(
                    (jacobian[row][column] - finite_difference).abs()
                        < 1e-6 * finite_difference.abs().max(1.0),
                    "row {row}, column {column}: {} vs {finite_difference}",
                    jacobian[row][column]
                );
            }
        }
    }
}
