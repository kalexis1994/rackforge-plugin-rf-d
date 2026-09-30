//! Conditional board-4 ladder through Q5-Q8, both VCAs and J7.
//! Optional C10/EMPHASIS return; Q28 is a fixed tail-current boundary.

use crate::output_conversion::{max_abs, solve_linear, Parameters as ConversionParameters};
use crate::recovery_vca_output::{
    self, Boundary as RecoveryBoundary, EmphasisBoundary, State as RecoveryState,
};
use crate::vca2_output::Parameters as TransistorParameters;
use crate::{Parameters as HeadphoneParameters, SolverBudget, StepError};

const N: usize = 16;
const K_B: f64 = 1.380_649e-23;
const Q_E: f64 = 1.602_176_634e-19;
const C_CELL: f64 = 68e-9;
const C24: f64 = 220e-6;
const C27: f64 = 10e-6;
#[cfg(test)]
const C10: f64 = 10e-6;
const CELLS: [(usize, usize); 4] = [(8, 12), (9, 13), (10, 14), (11, 15)];
const DEVICES: [(usize, Option<usize>, usize); 10] = [
    (6, Some(8), 5),
    (3, Some(9), 8),
    (2, Some(10), 9),
    (1, Some(11), 10),
    (0, None, 11),
    (7, Some(12), 5),
    (3, Some(13), 12),
    (2, Some(14), 13),
    (1, Some(15), 14),
    (0, None, 15),
];

pub const NODE_NAMES: [&str; N] = [
    "TAP_Q2_Q3",
    "TAP_Q10_Q11",
    "TAP_Q19_Q20",
    "TAP_Q23_Q24",
    "BOTTOM",
    "TAIL",
    "BASE_Q29",
    "BASE_Q30",
    "L_Q29C_Q23E",
    "L_Q23C_Q19E",
    "L_Q19C_Q10E",
    "L_Q10C_Q2E",
    "R_Q30C_Q24E",
    "R_Q24C_Q20E",
    "R_Q20C_Q11E",
    "R_Q11C_Q3E",
];

#[derive(Clone, Copy, Debug)]
pub struct Parameters {
    pub transistor: TransistorParameters,
    pub tail_current_a: f64,
    /// Explicit documentary scenario: schematic 200 Ω or parts list 200 kΩ.
    pub r61_ohm: f64,
    /// R76 (330 Ω) plus the selected BOTTOM-to-R73-wiper segment (0..1000 Ω).
    pub r30_ohm: f64,
}

#[derive(Clone, Copy, Debug)]
pub struct Boundary {
    pub bus_v: f64,
    pub recovery: RecoveryBoundary,
}

#[derive(Clone, Copy, Debug, PartialEq)]
pub struct State {
    pub node_v: [f64; N],
    pub previous_node_v: [f64; N],
    /// C16/C11/C7/C3 left minus right, C24 BOTTOM, C27 BASE minus BUS.
    pub capacitor_v: [f64; 6],
    /// C10 voltage from recovery R7/R3 tap toward Q30 base.
    pub c10_capacitor_v: f64,
    pub recovery: RecoveryState,
}

#[derive(Clone, Copy, Debug)]
pub struct StepResult {
    pub j7_v: f64,
    pub j4_hi_v: f64,
    pub j5_lo_v: f64,
    pub iterations: usize,
    pub recovery_port_evaluations: usize,
    pub predictor_fallback: bool,
    pub max_ladder_kcl_residual_a: f64,
    pub board_input_current_a: f64,
    pub c5_c1_current_a: [f64; 2],
    /// Positive from recovery R7/R3 tap toward Q30 base, zero when open.
    pub c10_return_current_a: f64,
    pub c10_capacitor_v: f64,
}

fn validate(p: Parameters, b: Boundary, budget: SolverBudget) -> Result<f64, StepError> {
    let t = p.transistor;
    let dt = b.recovery.vca.second.output.output.dt_s;
    if !p.tail_current_a.is_finite()
        || p.tail_current_a <= 0.0
        || !matches!(p.r61_ohm, 200.0 | 200_000.0)
        || !p.r30_ohm.is_finite()
        || !(330.0..=1330.0).contains(&p.r30_ohm)
        || !t.transistor_is_a.is_finite()
        || t.transistor_is_a <= 0.0
        || !t.beta_forward.is_finite()
        || t.beta_forward <= 0.0
        || !t.beta_reverse.is_finite()
        || t.beta_reverse <= 0.0
        || !t.temperature_k.is_finite()
        || t.temperature_k <= 0.0
        || !b.bus_v.is_finite()
        || !dt.is_finite()
        || dt <= 0.0
        || !(1..=16).contains(&budget.iterations)
        || !(1..=16).contains(&budget.line_search_halvings)
    {
        return Err(StepError::InvalidInput);
    }
    Ok(dt)
}

fn return_series_ohm(p: Parameters, r14_ohm: f64) -> Result<f64, StepError> {
    if !r14_ohm.is_finite() || !(0.0..=50_000.0).contains(&r14_ohm) {
        return Err(StepError::InvalidInput);
    }
    // R73 totals 1 kΩ; R30 already includes R76=330 Ω and R73_L.
    Ok(r14_ohm + 1000.0 - (p.r30_ohm - 330.0))
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
    let current = (x[a] - b.map_or(fixed, |k| x[k])) * g;
    r[a] += current;
    j[a][a] += g;
    if let Some(k) = b {
        r[k] -= current;
        j[k][k] += g;
        j[a][k] -= g;
        j[k][a] -= g;
    }
}

fn capacitor(
    x: &[f64; N],
    r: &mut [f64; N],
    j: &mut [[f64; N]; N],
    a: usize,
    b: Option<usize>,
    fixed: f64,
    old_v: f64,
    farad: f64,
    dt: f64,
) {
    let g = farad / dt;
    let current = g * (x[a] - b.map_or(fixed, |k| x[k]) - old_v);
    r[a] += current;
    j[a][a] += g;
    if let Some(k) = b {
        r[k] -= current;
        j[k][k] += g;
        j[a][k] -= g;
        j[k][a] -= g;
    }
}

fn npn(
    x: &[f64; N],
    r: &mut [f64; N],
    j: &mut [[f64; N]; N],
    base: usize,
    collector: Option<usize>,
    emitter: usize,
    p: TransistorParameters,
) -> Result<(), StepError> {
    let vc = collector.map_or(10.0, |k| x[k]);
    let vt = K_B * p.temperature_k / Q_E;
    let be = (x[base] - x[emitter]) / vt;
    let bc = (x[base] - vc) / vt;
    if !be.is_finite() || !bc.is_finite() || be.max(bc) > 45.0 {
        return Err(StepError::ExponentialDomain);
    }
    let f = p.transistor_is_a * be.exp_m1();
    let rev = p.transistor_is_a * bc.exp_m1();
    let gf = p.transistor_is_a * be.exp() / vt;
    let gr = p.transistor_is_a * bc.exp() / vt;
    let ib = f / p.beta_forward + rev / p.beta_reverse;
    let ic = f - (1.0 + 1.0 / p.beta_reverse) * rev;
    let terminals = [Some(base), collector, Some(emitter)];
    let currents = [ib, ic, -ib - ic];
    let db = [
        gf / p.beta_forward + gr / p.beta_reverse,
        -gr / p.beta_reverse,
        -gf / p.beta_forward,
    ];
    let dc = [
        gf - (1.0 + 1.0 / p.beta_reverse) * gr,
        (1.0 + 1.0 / p.beta_reverse) * gr,
        -gf,
    ];
    let slopes = [db, dc, std::array::from_fn(|k| -db[k] - dc[k])];
    for row in 0..3 {
        if let Some(i) = terminals[row] {
            r[i] += currents[row];
            for col in 0..3 {
                if let Some(k) = terminals[col] {
                    j[i][k] += slopes[row][col];
                }
            }
        }
    }
    Ok(())
}

fn evaluate(
    x: &[f64; N],
    p: Parameters,
    bus: f64,
    dt: Option<f64>,
    old: [f64; 6],
    load: Option<([f64; 3], [[f64; 3]; 3])>,
) -> Result<([f64; N], [[f64; N]; N]), StepError> {
    let mut r = [0.0; N];
    let mut j = [[0.0; N]; N];
    resistor(x, &mut r, &mut j, 0, None, 10.0, 220.0); // R4
    for i in 0..4 {
        resistor(x, &mut r, &mut j, i, Some(i + 1), 0.0, 150.0);
    }
    resistor(x, &mut r, &mut j, 4, None, 0.0, p.r61_ohm);
    resistor(x, &mut r, &mut j, 4, Some(6), 0.0, 470.0); // R54
    resistor(x, &mut r, &mut j, 4, Some(7), 0.0, p.r30_ohm);
    r[5] += p.tail_current_a;
    for (base, collector, emitter) in DEVICES {
        npn(x, &mut r, &mut j, base, collector, emitter, p.transistor)?;
    }
    if let Some(dt) = dt {
        for (i, (left, right)) in CELLS.into_iter().enumerate() {
            capacitor(
                x,
                &mut r,
                &mut j,
                left,
                Some(right),
                0.0,
                old[i],
                C_CELL,
                dt,
            );
        }
        capacitor(x, &mut r, &mut j, 4, None, 0.0, old[4], C24, dt);
        capacitor(x, &mut r, &mut j, 6, None, bus, old[5], C27, dt);
    }
    if let Some((current, tangent)) = load {
        for (row, node) in [11, 15, 7].into_iter().enumerate() {
            r[node] += current[row];
            for (col, other) in [11, 15, 7].into_iter().enumerate() {
                j[node][other] += tangent[row][col];
            }
        }
    }
    if r.iter().any(|v| !v.is_finite()) || j.iter().flatten().any(|v| !v.is_finite()) {
        return Err(StepError::ExponentialDomain);
    }
    Ok((r, j))
}

fn charges(x: &[f64; N], bus: f64) -> [f64; 6] {
    [
        x[8] - x[12],
        x[9] - x[13],
        x[10] - x[14],
        x[11] - x[15],
        x[4],
        x[6] - bus,
    ]
}

/// DC initializer. The supplied seed is a numerical starting point from the
/// conditional offline ladder, never an audible parameter. C10 is open.
pub fn initial_state(
    p: Parameters,
    conversion: ConversionParameters,
    headphone: HeadphoneParameters,
    b: Boundary,
    seed: [f64; N],
) -> Result<State, StepError> {
    validate(p, b, SolverBudget::default())?;
    if seed.iter().any(|v| !v.is_finite()) {
        return Err(StepError::InvalidInput);
    }
    let mut x = seed;
    for _ in 0..32 {
        let (r, j) = evaluate(&x, p, b.bus_v, None, [0.0; 6], None)?;
        let error = max_abs(&r);
        if error < 1e-11 {
            let mut rb = b.recovery;
            rb.ladder_left_v = x[11];
            rb.ladder_right_v = x[15];
            let recovery =
                recovery_vca_output::initial_state(p.transistor, conversion, headphone, rb)?;
            return Ok(State {
                node_v: x,
                previous_node_v: x,
                capacitor_v: charges(&x, b.bus_v),
                c10_capacitor_v: recovery.node_v[6] - x[7],
                recovery,
            });
        }
        let delta = solve_linear(j, r.map(|v| -v))?;
        let mut accepted = false;
        for power in 0..16 {
            let s = 0.5_f64.powi(power);
            let candidate = std::array::from_fn(|i| x[i] + s * delta[i]);
            if let Ok((next, _)) = evaluate(&candidate, p, b.bus_v, None, [0.0; 6], None) {
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

type Trial = ([f64; N], [[f64; N]; N], RecoveryState, StepResult);

fn trial(
    previous: State,
    x: &[f64; N],
    p: Parameters,
    conversion: ConversionParameters,
    headphone: HeadphoneParameters,
    b: Boundary,
    dt: f64,
    budget: SolverBudget,
    return_series: Option<f64>,
) -> Result<Trial, StepError> {
    let mut rb = b.recovery;
    rb.ladder_left_v = x[11];
    rb.ladder_right_v = x[15];
    let (next_recovery, port_result, currents, tangent, c10_v, return_current) =
        if let Some(series_ohm) = return_series {
            let port = recovery_vca_output::solve_feedback_port(
                &previous.recovery,
                p.transistor,
                conversion,
                headphone,
                rb,
                EmphasisBoundary {
                    q30_base_v: x[7],
                    previous_capacitor_v: previous.c10_capacitor_v,
                    series_ohm,
                },
                budget,
            )?;
            (
                port.next_state,
                port.result,
                port.current_a,
                port.conductance_s,
                port.c10_capacitor_v,
                -port.current_a[2],
            )
        } else {
            let port = recovery_vca_output::solve_input_port(
                &previous.recovery,
                p.transistor,
                conversion,
                headphone,
                rb,
                budget,
            )?;
            let currents = [port.current_a[0], port.current_a[1], 0.0];
            let mut tangent = [[0.0; 3]; 3];
            for row in 0..2 {
                for col in 0..2 {
                    tangent[row][col] = port.conductance_s[row][col];
                }
            }
            (
                port.next_state,
                port.result,
                currents,
                tangent,
                previous.c10_capacitor_v,
                0.0,
            )
        };
    let (r, j) = evaluate(
        x,
        p,
        b.bus_v,
        Some(dt),
        previous.capacitor_v,
        Some((currents, tangent)),
    )?;
    let result = StepResult {
        j7_v: port_result.j7_v,
        j4_hi_v: port_result.j4_hi_v,
        j5_lo_v: port_result.j5_lo_v,
        iterations: 0,
        recovery_port_evaluations: 0,
        predictor_fallback: false,
        max_ladder_kcl_residual_a: max_abs(&r),
        board_input_current_a: C27 / dt * (b.bus_v - x[6] + previous.capacitor_v[5]),
        c5_c1_current_a: [currents[0], currents[1]],
        c10_return_current_a: return_current,
        c10_capacitor_v: c10_v,
    };
    Ok((r, j, next_recovery, result))
}

fn solve_from_seed(
    previous: State,
    mut x: [f64; N],
    p: Parameters,
    conversion: ConversionParameters,
    headphone: HeadphoneParameters,
    b: Boundary,
    dt: f64,
    budget: SolverBudget,
    evaluations: &mut usize,
    return_series: Option<f64>,
) -> Result<([f64; N], RecoveryState, StepResult), StepError> {
    let mut cached = None;
    for iteration in 0..budget.iterations {
        let (r, j, recovery, mut result) = match cached.take() {
            Some(value) => value,
            None => {
                *evaluations += 1;
                trial(
                    previous,
                    &x,
                    p,
                    conversion,
                    headphone,
                    b,
                    dt,
                    budget,
                    return_series,
                )?
            }
        };
        let error = max_abs(&r);
        if error < 1e-10 {
            result.iterations = iteration;
            result.recovery_port_evaluations = *evaluations;
            result.max_ladder_kcl_residual_a = error;
            return Ok((x, recovery, result));
        }
        let direction = solve_linear(j, r.map(|v| -v))?;
        let mut accepted = None;
        for power in 0..budget.line_search_halvings {
            let s = 0.5_f64.powi(power as i32);
            let candidate = std::array::from_fn(|i| x[i] + s * direction[i]);
            *evaluations += 1;
            if let Ok(next) = trial(
                previous,
                &candidate,
                p,
                conversion,
                headphone,
                b,
                dt,
                budget,
                return_series,
            ) {
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

fn step_internal(
    state: &mut State,
    p: Parameters,
    conversion: ConversionParameters,
    headphone: HeadphoneParameters,
    b: Boundary,
    budget: SolverBudget,
    return_series: Option<f64>,
) -> Result<StepResult, StepError> {
    let dt = validate(p, b, budget)?;
    if state
        .node_v
        .iter()
        .chain(state.previous_node_v.iter())
        .chain(state.capacitor_v.iter())
        .any(|v| !v.is_finite())
        || !state.c10_capacitor_v.is_finite()
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
        dt,
        budget,
        &mut evaluations,
        return_series,
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
                dt,
                budget,
                &mut evaluations,
                return_series,
            )?,
            true,
        ),
    };
    state.previous_node_v = previous.node_v;
    state.node_v = solution.0;
    state.capacitor_v = charges(&solution.0, b.bus_v);
    state.c10_capacitor_v = solution.2.c10_capacitor_v;
    state.recovery = solution.1;
    let mut result = solution.2;
    result.predictor_fallback = fallback;
    Ok(result)
}

/// Advance the complete open-EMPHASIS laboratory chain. Failure is atomic.
pub fn step(
    state: &mut State,
    p: Parameters,
    conversion: ConversionParameters,
    headphone: HeadphoneParameters,
    b: Boundary,
    budget: SolverBudget,
) -> Result<StepResult, StepError> {
    step_internal(state, p, conversion, headphone, b, budget, None)
}

/// Close C10/R14/R73 between the recovery tap and Q30 base. `r14_ohm` is
/// pin-7-to-pin-6 electrical resistance, not a panel angle.
pub fn step_with_emphasis(
    state: &mut State,
    p: Parameters,
    conversion: ConversionParameters,
    headphone: HeadphoneParameters,
    b: Boundary,
    r14_ohm: f64,
    budget: SolverBudget,
) -> Result<StepResult, StepError> {
    validate(p, b, budget)?;
    let series = return_series_ohm(p, r14_ohm)?;
    step_internal(state, p, conversion, headphone, b, budget, Some(series))
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::output::OutputBoundary;
    use crate::output_conversion::DiodeParameters;
    use crate::output_conversion_c4::BoundaryC4;
    use crate::vca1_output::Boundary as FirstBoundary;
    use crate::vca2_output::Boundary as SecondBoundary;
    use serde_json::Value;

    fn n(v: &Value) -> f64 {
        v.as_f64().unwrap()
    }

    fn output_setup(case: &Value) -> (ConversionParameters, HeadphoneParameters, RecoveryBoundary) {
        let c = &case["output_parameters"];
        let h = &case["headphone_parameters"];
        let b = &case["initial_boundary"];
        let conversion = ConversionParameters {
            transistor_is_a: n(&c["is_a"]),
            beta_forward: n(&c["beta_forward"]),
            beta_reverse: n(&c["beta_reverse"]),
            temperature_k: n(&c["temperature_k"]),
            diode: Some(DiodeParameters {
                is_a: n(&c["diode_model"]["is_a"]),
                ideality: n(&c["diode_model"]["ideality"]),
            }),
        };
        let headphone = HeadphoneParameters {
            transistor_is_a: n(&h["is_a"]),
            beta_forward: n(&h["beta_forward"]),
            beta_reverse: n(&h["beta_reverse"]),
            temperature_k: n(&h["temperature_k"]),
            diode_is_a: n(&h["diode_model"]["is_a"]),
            diode_ideality: n(&h["diode_model"]["ideality"]),
        };
        let recovery = RecoveryBoundary {
            ladder_left_v: 0.0,
            ladder_right_v: 0.0,
            vca: FirstBoundary {
                recover_collector_v: 0.0,
                loudness_v: n(&b["loudness_v"]),
                first_balance_left_ohm: n(&b["first_balance_left_ohm"]),
                second: SecondBoundary {
                    q14_base_v: 0.0,
                    q13_base_v: 0.0,
                    q21_base_v: n(&b["q21_base_v"]),
                    first_balance_wiper_v: 0.0,
                    second_balance_left_ohm: n(&b["second_balance_left_ohm"]),
                    minus_v: n(&b["minus_v"]),
                    output: BoundaryC4 {
                        second_balance_wiper_v: 0.0,
                        q12_base_v: 0.0,
                        q17_base_v: 0.0,
                        plus_v: n(&b["plus_v"]),
                        output: OutputBoundary {
                            q17_collector_v: 0.0,
                            r20_lower_ohm: n(&case["r20_lower_ohm"]),
                            hi_load_ohm: n(&case["hi_load_ohm"]),
                            lo_load_ohm: n(&case["lo_load_ohm"]),
                            sw18_on: true,
                            r21_lower_ohm: n(&case["r21_lower_ohm"]),
                            tip_load_ohm: Some(n(&case["tip_ring_load_ohm"])),
                            ring_load_ohm: Some(n(&case["tip_ring_load_ohm"])),
                            dt_s: n(&case["dt_s"]),
                        },
                    },
                },
            },
        };
        (conversion, headphone, recovery)
    }

    #[test]
    fn isolated_ladder_matches_independent_python_for_both_r61_candidates() {
        let fixture: Value =
            serde_json::from_str(include_str!("../../../evidence/ladder_native_vectors.json"))
                .unwrap();
        assert_eq!(fixture["schema"], "rf-d/ladder-native-vectors/v1");
        for (i, name) in NODE_NAMES.iter().enumerate() {
            assert_eq!(&fixture["node_order"][i], name);
        }
        let bjt = &fixture["bjt"];
        let transistor = TransistorParameters {
            transistor_is_a: n(&bjt["is_a"]),
            beta_forward: n(&bjt["beta_forward"]),
            beta_reverse: n(&bjt["beta_reverse"]),
            temperature_k: n(&bjt["temperature_k"]),
        };
        let dt = n(&fixture["dt_s"]);
        for scenario in fixture["scenarios"].as_array().unwrap() {
            let p = Parameters {
                transistor,
                r61_ohm: n(&scenario["r61_ohm"]),
                r30_ohm: n(&scenario["r30_ohm"]),
                tail_current_a: n(&scenario["tail_current_a"]),
            };
            let mut x = std::array::from_fn(|i| n(&scenario["initial_node_v"][i]));
            let mut old = charges(&x, 0.0);
            for (index, row) in scenario["rows"].as_array().unwrap().iter().enumerate() {
                let new_bus = n(&row["bus_v"]);
                for iteration in 0..16 {
                    let (r, j) = evaluate(&x, p, new_bus, Some(dt), old, None).unwrap();
                    let error = max_abs(&r);
                    if error < 1e-11 {
                        break;
                    }
                    assert!(iteration < 15, "isolated Newton budget {index}");
                    let delta = solve_linear(j, r.map(|v| -v)).unwrap();
                    let mut accepted = false;
                    for power in 0..16 {
                        let s = 0.5_f64.powi(power);
                        let candidate = std::array::from_fn(|i| x[i] + s * delta[i]);
                        if let Ok((next, _)) = evaluate(&candidate, p, new_bus, Some(dt), old, None)
                        {
                            if max_abs(&next) < error {
                                x = candidate;
                                accepted = true;
                                break;
                            }
                        }
                    }
                    assert!(accepted, "isolated line search {index}");
                }
                let (r, j) = evaluate(&x, p, new_bus, Some(dt), old, None).unwrap();
                assert!(max_abs(&r) < 1e-10, "isolated KCL {index}");
                for node in 0..N {
                    let expected = n(&row["node_v"][node]);
                    assert!(
                        (x[node] - expected).abs() < 1e-6,
                        "R61={} step {index} node {}: {} vs {expected}",
                        p.r61_ohm,
                        NODE_NAMES[node],
                        x[node]
                    );
                }
                let current = C27 / dt * (new_bus - x[6] + old[5]);
                assert!((current - n(&row["board_input_current_a"])).abs() < 1e-8);
                // Check the exact local Jacobian against central differences at
                // a transient operating point, including capacitor stamps.
                if index == 5 {
                    for col in 0..N {
                        let mut hi = x;
                        hi[col] += 1e-6;
                        let mut lo = x;
                        lo[col] -= 1e-6;
                        let rh = evaluate(&hi, p, new_bus, Some(dt), old, None).unwrap().0;
                        let rl = evaluate(&lo, p, new_bus, Some(dt), old, None).unwrap().0;
                        for row in 0..N {
                            let fd = (rh[row] - rl[row]) / 2e-6;
                            assert!(
                                (fd - j[row][col]).abs() < 2e-6,
                                "Jacobian {row},{col}: {fd} vs {}",
                                j[row][col]
                            );
                        }
                    }
                }
                old = charges(&x, new_bus);
            }
        }
    }

    #[test]
    fn ladder_c5_c1_recovery_vca_j7_closes_kcl_and_commits_atomically() {
        let ladder: Value =
            serde_json::from_str(include_str!("../../../evidence/ladder_native_vectors.json"))
                .unwrap();
        let downstream: Value = serde_json::from_str(include_str!(
            "../../../evidence/recovery_vca_output_vectors.json"
        ))
        .unwrap();
        let case = &downstream["case"];
        let (conversion, headphone, rb) = output_setup(case);
        let t = &ladder["bjt"];
        let transistor = TransistorParameters {
            transistor_is_a: n(&t["is_a"]),
            beta_forward: n(&t["beta_forward"]),
            beta_reverse: n(&t["beta_reverse"]),
            temperature_k: n(&t["temperature_k"]),
        };
        for scenario in ladder["scenarios"].as_array().unwrap() {
            let p = Parameters {
                transistor,
                tail_current_a: n(&scenario["tail_current_a"]),
                r61_ohm: n(&scenario["r61_ohm"]),
                r30_ohm: n(&scenario["r30_ohm"]),
            };
            let seed = std::array::from_fn(|i| n(&scenario["initial_node_v"][i]));
            let mut state = initial_state(
                p,
                conversion,
                headphone,
                Boundary {
                    bus_v: 0.0,
                    recovery: rb,
                },
                seed,
            )
            .unwrap();
            for (index, bus_v) in [
                0.0, 0.001, 0.001, -0.001, -0.001, 0.01, 0.01, 0.0, -0.01, 0.0,
            ]
            .into_iter()
            .enumerate()
            {
                let previous = state;
                let b = Boundary {
                    bus_v,
                    recovery: rb,
                };
                let result = step(
                    &mut state,
                    p,
                    conversion,
                    headphone,
                    b,
                    SolverBudget::default(),
                )
                .unwrap_or_else(|e| panic!("R61={} coupled {index}: {e:?}", p.r61_ohm));
                assert!(result.max_ladder_kcl_residual_a < 1e-10);
                assert!(result.recovery_port_evaluations > 0);
                assert!(result.j7_v.is_finite());
                assert!(result.j4_hi_v.is_finite());
                assert!(result.j5_lo_v.is_finite());
                let mut port_boundary = rb;
                port_boundary.ladder_left_v = state.node_v[11];
                port_boundary.ladder_right_v = state.node_v[15];
                let port = recovery_vca_output::solve_input_port(
                    &previous.recovery,
                    transistor,
                    conversion,
                    headphone,
                    port_boundary,
                    SolverBudget::default(),
                )
                .unwrap();
                assert_eq!(port.next_state, state.recovery);
                for i in 0..2 {
                    assert!((port.current_a[i] - result.c5_c1_current_a[i]).abs() < 1e-12);
                }
                let dt = n(&case["dt_s"]);
                let mut tangent = [[0.0; 3]; 3];
                for row in 0..2 {
                    for col in 0..2 {
                        tangent[row][col] = port.conductance_s[row][col];
                    }
                }
                let (residual, _) = evaluate(
                    &state.node_v,
                    p,
                    bus_v,
                    Some(dt),
                    previous.capacitor_v,
                    Some(([port.current_a[0], port.current_a[1], 0.0], tangent)),
                )
                .unwrap();
                assert!(max_abs(&residual) < 1e-10);
                assert!(
                    (result.board_input_current_a
                        - C27 / dt * (bus_v - state.node_v[6] + previous.capacitor_v[5]))
                        .abs()
                        < 1e-12
                );
                assert_eq!(state.previous_node_v, previous.node_v);
            }
            let previous = state;
            let error = step(
                &mut state,
                p,
                conversion,
                headphone,
                Boundary {
                    bus_v: f64::NAN,
                    recovery: rb,
                },
                SolverBudget::default(),
            )
            .unwrap_err();
            assert_eq!(error, StepError::InvalidInput);
            assert_eq!(state, previous);
        }
    }

    #[test]
    fn c10_closed_loop_conserves_charge_with_loaded_output_for_both_r61() {
        let ladder: Value =
            serde_json::from_str(include_str!("../../../evidence/ladder_native_vectors.json"))
                .unwrap();
        let downstream: Value = serde_json::from_str(include_str!(
            "../../../evidence/recovery_vca_output_vectors.json"
        ))
        .unwrap();
        let case = &downstream["case"];
        let (conversion, headphone, rb) = output_setup(case);
        let t = &ladder["bjt"];
        let transistor = TransistorParameters {
            transistor_is_a: n(&t["is_a"]),
            beta_forward: n(&t["beta_forward"]),
            beta_reverse: n(&t["beta_reverse"]),
            temperature_k: n(&t["temperature_k"]),
        };
        let dt = n(&case["dt_s"]);
        for scenario in ladder["scenarios"].as_array().unwrap() {
            let p = Parameters {
                transistor,
                tail_current_a: n(&scenario["tail_current_a"]),
                r61_ohm: n(&scenario["r61_ohm"]),
                r30_ohm: n(&scenario["r30_ohm"]),
            };
            let seed = std::array::from_fn(|i| n(&scenario["initial_node_v"][i]));
            let mut state = initial_state(
                p,
                conversion,
                headphone,
                Boundary {
                    bus_v: 0.0,
                    recovery: rb,
                },
                seed,
            )
            .unwrap();
            for (index, bus_v) in [0.0, 0.001, 0.01, 0.01, -0.01, -0.01, 0.0, 0.001, -0.001]
                .into_iter()
                .enumerate()
            {
                let previous = state;
                let r14 = [0.0, 25_000.0, 50_000.0][index % 3];
                let result = step_with_emphasis(
                    &mut state,
                    p,
                    conversion,
                    headphone,
                    Boundary {
                        bus_v,
                        recovery: rb,
                    },
                    r14,
                    SolverBudget::default(),
                )
                .unwrap_or_else(|e| panic!("R61={} C10 step {index}: {e:?}", p.r61_ohm));
                assert!(result.max_ladder_kcl_residual_a < 1e-10);
                let cap_current = C10 / dt * (state.c10_capacitor_v - previous.c10_capacitor_v);
                assert!((result.c10_return_current_a - cap_current).abs() < 1e-10);
                assert!((state.c10_capacitor_v - result.c10_capacitor_v).abs() < 1e-12);
                let series = return_series_ohm(p, r14).unwrap();
                assert!(
                    (state.c10_capacitor_v
                        - (state.recovery.node_v[6]
                            - state.node_v[7]
                            - series * result.c10_return_current_a))
                        .abs()
                        < 1e-10
                );
                let mut port_boundary = rb;
                port_boundary.ladder_left_v = state.node_v[11];
                port_boundary.ladder_right_v = state.node_v[15];
                let port = recovery_vca_output::solve_feedback_port(
                    &previous.recovery,
                    transistor,
                    conversion,
                    headphone,
                    port_boundary,
                    EmphasisBoundary {
                        q30_base_v: state.node_v[7],
                        previous_capacitor_v: previous.c10_capacitor_v,
                        series_ohm: series,
                    },
                    SolverBudget::default(),
                )
                .unwrap();
                assert_eq!(port.next_state, state.recovery);
                assert!((-port.current_a[2] - result.c10_return_current_a).abs() < 1e-12);
                let (r, _) = evaluate(
                    &state.node_v,
                    p,
                    bus_v,
                    Some(dt),
                    previous.capacitor_v,
                    Some((port.current_a, port.conductance_s)),
                )
                .unwrap();
                assert!(max_abs(&r) < 1e-10);
            }
            let previous = state;
            assert_eq!(
                step_with_emphasis(
                    &mut state,
                    p,
                    conversion,
                    headphone,
                    Boundary {
                        bus_v: 0.0,
                        recovery: rb
                    },
                    50_001.0,
                    SolverBudget::default()
                )
                .unwrap_err(),
                StepError::InvalidInput
            );
            assert_eq!(state, previous);
        }
    }

    #[test]
    fn closed_loop_bus_to_j7_matches_independent_62_node_python() {
        let fixture: Value = serde_json::from_str(include_str!(
            "../../../evidence/ladder_j7_closed_loop_vectors.json"
        ))
        .unwrap();
        assert_eq!(fixture["schema"], "rf-d/ladder-j7-closed-loop-vectors/v1");
        let downstream: Value = serde_json::from_str(include_str!(
            "../../../evidence/recovery_vca_output_vectors.json"
        ))
        .unwrap();
        let (conversion, headphone, rb) = output_setup(&downstream["case"]);
        let transistor = TransistorParameters {
            transistor_is_a: 1e-14,
            beta_forward: 100.0,
            beta_reverse: 5.0,
            temperature_k: 298.15,
        };
        for scenario in fixture["scenarios"].as_array().unwrap() {
            let p = Parameters {
                transistor,
                tail_current_a: n(&scenario["tail_current_a"]),
                r61_ohm: n(&scenario["r61_ohm"]),
                r30_ohm: n(&scenario["r30_ohm"]),
            };
            let seed = std::array::from_fn(|i| n(&scenario["initial_ladder_node_v"][i]));
            let mut state = initial_state(
                p,
                conversion,
                headphone,
                Boundary {
                    bus_v: 0.0,
                    recovery: rb,
                },
                seed,
            )
            .unwrap();
            for (index, row) in scenario["trace"].as_array().unwrap().iter().enumerate() {
                let result = step_with_emphasis(
                    &mut state,
                    p,
                    conversion,
                    headphone,
                    Boundary {
                        bus_v: n(&row["bus_v"]),
                        recovery: rb,
                    },
                    n(&row["r14_ohm"]),
                    SolverBudget::default(),
                )
                .unwrap_or_else(|e| panic!("R61={} oracle step {index}: {e:?}", p.r61_ohm));
                for i in 0..16 {
                    let expected = n(&row["ladder_recovery_node_v"][i]);
                    assert!(
                        (state.node_v[i] - expected).abs() < 1e-6,
                        "R61={} step {index} ladder {}: {} vs {expected}",
                        p.r61_ohm,
                        NODE_NAMES[i],
                        state.node_v[i]
                    );
                }
                for i in 0..8 {
                    let expected = n(&row["ladder_recovery_node_v"][16 + i]);
                    assert!(
                        (state.recovery.node_v[i] - expected).abs() < 1e-6,
                        "R61={} step {index} recovery {}: {} vs {expected}",
                        p.r61_ohm,
                        recovery_vca_output::NODE_NAMES[i],
                        state.recovery.node_v[i]
                    );
                }
                for (name, actual) in [
                    ("c10_capacitor_v", state.c10_capacitor_v),
                    ("j7_v", result.j7_v),
                    ("j4_hi_v", result.j4_hi_v),
                    ("j5_lo_v", result.j5_lo_v),
                ] {
                    let expected = n(&row[name]);
                    assert!(
                        (actual - expected).abs() < 1e-6,
                        "R61={} step {index} {name}: {actual} vs {expected}",
                        p.r61_ohm
                    );
                }
            }
        }
    }

    #[test]
    fn closed_loop_192_sample_j7_control_trace_matches_python() {
        let fixture: Value = serde_json::from_str(include_str!(
            "../../../evidence/ladder_j7_closed_loop_vectors.json"
        ))
        .unwrap();
        let downstream: Value = serde_json::from_str(include_str!(
            "../../../evidence/recovery_vca_output_vectors.json"
        ))
        .unwrap();
        let (conversion, headphone, mut rb) = output_setup(&downstream["case"]);
        let scenario = &fixture["scenarios"][0];
        let p = Parameters {
            transistor: TransistorParameters {
                transistor_is_a: 1e-14,
                beta_forward: 100.0,
                beta_reverse: 5.0,
                temperature_k: 298.15,
            },
            tail_current_a: n(&scenario["tail_current_a"]),
            r61_ohm: n(&scenario["r61_ohm"]),
            r30_ohm: n(&scenario["r30_ohm"]),
        };
        let seed = std::array::from_fn(|i| n(&scenario["initial_ladder_node_v"][i]));
        let mut state = initial_state(
            p,
            conversion,
            headphone,
            Boundary {
                bus_v: 0.0,
                recovery: rb,
            },
            seed,
        )
        .unwrap();
        let mut signal_power = 0.0;
        let mut error_power = 0.0;
        let mut max_j7 = 0.0_f64;
        let mut max_nodes = 0.0_f64;
        for (index, row) in fixture["audio_trace"]
            .as_array()
            .unwrap()
            .iter()
            .enumerate()
        {
            rb.vca.second.output.output.sw18_on = row["sw18_on"].as_bool().unwrap();
            let result = step_with_emphasis(
                &mut state,
                p,
                conversion,
                headphone,
                Boundary {
                    bus_v: n(&row["bus_v"]),
                    recovery: rb,
                },
                n(&row["r14_ohm"]),
                SolverBudget::default(),
            )
            .unwrap_or_else(|e| panic!("audio sample {index}: {e:?}"));
            let expected_j7 = n(&row["j7_v"]);
            let error = result.j7_v - expected_j7;
            signal_power += expected_j7 * expected_j7;
            error_power += error * error;
            max_j7 = max_j7.max(error.abs());
            assert!((state.c10_capacitor_v - n(&row["c10_capacitor_v"])).abs() < 1e-6);
            assert!((result.j4_hi_v - n(&row["j4_hi_v"])).abs() < 1e-6);
            assert!((result.j5_lo_v - n(&row["j5_lo_v"])).abs() < 1e-6);
            if let Some(nodes) = row["ladder_recovery_node_v"].as_array() {
                for i in 0..16 {
                    max_nodes = max_nodes.max((state.node_v[i] - n(&nodes[i])).abs());
                }
                for i in 0..8 {
                    max_nodes = max_nodes.max((state.recovery.node_v[i] - n(&nodes[16 + i])).abs());
                }
            }
            assert!(result.max_ladder_kcl_residual_a < 1e-10);
        }
        let numerical_snr_db = 10.0 * (signal_power / error_power).log10();
        println!(
            "C10 192 samples: max_j7_error_v={max_j7:.3e} \
                  max_checkpoint_node_error_v={max_nodes:.3e} \
                  numerical_snr_db={numerical_snr_db:.1}"
        );
        assert!(max_j7 < 1e-6);
        assert!(max_nodes < 1e-6);
        assert!(numerical_snr_db > 100.0);
    }
}
