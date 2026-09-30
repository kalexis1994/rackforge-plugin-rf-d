//! SVC-9 Q26 PNP/Q28 NPN, R39/R46/R45/R60 and C18.
//! Four-node Ebers-Moll circuit; upstream panel sources are imposed.
use crate::output_conversion::{max_abs, solve_linear};
use crate::vca2_output::Parameters as TransistorParameters;
use crate::{SolverBudget, StepError};

const N: usize = 4;
const C18: f64 = 100e-12;
const R60: f64 = 680.0;
const K_B: f64 = 1.380_649e-23;
const Q_E: f64 = 1.602_176_634e-19;
pub const NODE_NAMES: [&str; N] = [
    "CONTROL_BASE",
    "SHARED_Q26E_Q28B",
    "Q26_COLLECTOR",
    "Q28_COLLECTOR",
];

#[derive(Clone, Copy, Debug)]
pub struct PanelBoundary {
    pub cutoff_fraction_from_neg10: f64,
    pub scale_active_ohm: f64,
    pub contour_pin16_v: f64,
    pub external_control_v: Option<f64>,
    pub external_source_ohm: f64,
    pub filter_mod_on: bool,
    pub modulation_source_v: Option<f64>,
    pub modulation_source_ohm: f64,
    pub keyboard_1_3_on: bool,
    pub keyboard_2_3_on: bool,
    pub keyboard_cv_v: Option<f64>,
    pub keyboard_source_ohm: f64,
}

impl Default for PanelBoundary {
    fn default() -> Self {
        Self {
            cutoff_fraction_from_neg10: 0.5,
            scale_active_ohm: 250.0,
            contour_pin16_v: 0.0,
            external_control_v: None,
            external_source_ohm: 0.0,
            filter_mod_on: false,
            modulation_source_v: None,
            modulation_source_ohm: 0.0,
            keyboard_1_3_on: false,
            keyboard_2_3_on: false,
            keyboard_cv_v: None,
            keyboard_source_ohm: 0.0,
        }
    }
}

#[derive(Clone, Copy, Debug)]
pub struct PanelEquivalent {
    pub voltage_v: f64,
    pub conductance_s: f64,
}

/// Exact resistor reduction, with R51 and SW15 OFF grounded. The keyboard
/// resistors share one upstream source impedance, including when both are ON.
pub fn reduce_panel(b: PanelBoundary) -> Result<PanelEquivalent, StepError> {
    if !b.cutoff_fraction_from_neg10.is_finite()
        || !(0.0..=1.0).contains(&b.cutoff_fraction_from_neg10)
        || !b.scale_active_ohm.is_finite()
        || !(0.0..=500.0).contains(&b.scale_active_ohm)
        || !b.contour_pin16_v.is_finite()
        || [
            b.external_source_ohm,
            b.modulation_source_ohm,
            b.keyboard_source_ohm,
        ]
        .iter()
        .any(|v| !v.is_finite() || *v < 0.0)
        || [b.external_control_v, b.modulation_source_v, b.keyboard_cv_v]
            .iter()
            .any(|v| v.is_some_and(|x| !x.is_finite()))
        || (b.filter_mod_on && b.modulation_source_v.is_none())
        || ((b.keyboard_1_3_on || b.keyboard_2_3_on) && b.keyboard_cv_v.is_none())
    {
        return Err(StepError::InvalidInput);
    }
    let a = b.cutoff_fraction_from_neg10;
    let rknob = 200_000.0 + 5000.0 * a * (1.0 - a);
    let mut g = 1.0 / rknob + 1.0 / 47_000.0 + 1.0 / (1800.0 + b.scale_active_ohm);
    let mut drive = (-10.0 + 20.0 * a) / rknob + b.contour_pin16_v / 47_000.0;
    let rext = 100_000.0
        + if b.external_control_v.is_some() {
            b.external_source_ohm
        } else {
            0.0
        };
    g += 1.0 / rext;
    drive += b.external_control_v.unwrap_or(0.0) / rext;
    let rmod = 33_000.0
        + if b.filter_mod_on {
            b.modulation_source_ohm
        } else {
            0.0
        };
    g += 1.0 / rmod;
    if b.filter_mod_on {
        drive += b.modulation_source_v.unwrap() / rmod;
    }
    let gkbd = f64::from(b.keyboard_1_3_on) / 300_000.0 + f64::from(b.keyboard_2_3_on) / 150_000.0;
    if gkbd > 0.0 {
        let r = 1.0 / gkbd + b.keyboard_source_ohm;
        g += 1.0 / r;
        drive += b.keyboard_cv_v.unwrap() / r;
    }
    let voltage_v = drive / g;
    if !voltage_v.is_finite() || !g.is_finite() || g <= 0.0 {
        return Err(StepError::InvalidInput);
    }
    Ok(PanelEquivalent {
        voltage_v,
        conductance_s: g,
    })
}

#[derive(Clone, Copy, Debug)]
pub struct Parameters {
    pub q26: TransistorParameters,
    pub q28: TransistorParameters,
}

#[derive(Clone, Copy, Debug)]
pub struct Boundary {
    pub panel: PanelBoundary,
    pub range_fraction_from_ground: f64,
    pub tail_v: f64,
    pub dt_s: f64,
}

#[derive(Clone, Copy, Debug, PartialEq)]
pub struct State {
    pub node_v: [f64; N],
    pub c18_v: f64,
}

#[derive(Clone, Copy, Debug)]
pub struct Port {
    pub next_state: State,
    /// Current from TAIL into R60 and Q28, A.
    pub current_a: f64,
    /// Exact local derivative with respect to TAIL while C18 history is fixed, S.
    pub conductance_s: f64,
    pub max_kcl_residual_a: f64,
    pub iterations: usize,
}

fn validate(
    p: Parameters,
    b: Boundary,
    budget: SolverBudget,
) -> Result<PanelEquivalent, StepError> {
    for t in [p.q26, p.q28] {
        if [
            t.transistor_is_a,
            t.beta_forward,
            t.beta_reverse,
            t.temperature_k,
        ]
        .iter()
        .any(|v| !v.is_finite() || *v <= 0.0)
        {
            return Err(StepError::InvalidInput);
        }
    }
    if !b.tail_v.is_finite()
        || !b.range_fraction_from_ground.is_finite()
        || !(0.0..=1.0).contains(&b.range_fraction_from_ground)
        || !b.dt_s.is_finite()
        || b.dt_s <= 0.0
        || !(1..=16).contains(&budget.iterations)
        || !(1..=16).contains(&budget.line_search_halvings)
    {
        return Err(StepError::InvalidInput);
    }
    reduce_panel(b.panel)
}

fn transistor(
    x: &[f64; N],
    r: &mut [f64; N],
    j: &mut [[f64; N]; N],
    base: usize,
    collector: usize,
    emitter: Option<usize>,
    polarity: f64,
    p: TransistorParameters,
) -> Result<(), StepError> {
    let vt = K_B * p.temperature_k / Q_E;
    let ve = emitter.map_or(0.0, |i| x[i]);
    let be = polarity * (x[base] - ve) / vt;
    let bc = polarity * (x[base] - x[collector]) / vt;
    if !be.is_finite() || !bc.is_finite() || be.max(bc) > 45.0 {
        return Err(StepError::ExponentialDomain);
    }
    let f = p.transistor_is_a * be.exp_m1();
    let rev = p.transistor_is_a * bc.exp_m1();
    let gf = p.transistor_is_a * be.exp() / vt;
    let gr = p.transistor_is_a * bc.exp() / vt;
    let ib = f / p.beta_forward + rev / p.beta_reverse;
    let ic = f - (1.0 + 1.0 / p.beta_reverse) * rev;
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
    let terminals = [Some(base), Some(collector), emitter];
    let currents = [ib, ic, -ib - ic];
    let slopes = [db, dc, std::array::from_fn(|i| -db[i] - dc[i])];
    for row in 0..3 {
        if let Some(i) = terminals[row] {
            r[i] += polarity * currents[row];
            for col in 0..3 {
                if let Some(k) = terminals[col] {
                    // Polarity enters both the current and the voltage argument;
                    // its square cancels in these derivatives.
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
    b: Boundary,
    panel: PanelEquivalent,
    old_c18: Option<f64>,
) -> Result<([f64; N], [[f64; N]; N]), StepError> {
    let a = b.range_fraction_from_ground;
    let gs = 1.0 / (68_000.0 + 10_000.0 * a * (1.0 - a));
    let mut r = [
        (x[0] - panel.voltage_v) * panel.conductance_s,
        (x[1] - 10.0 * a) * gs,
        (x[2] + 10.0) / 330.0,
        (x[3] - b.tail_v) / R60,
    ];
    let mut j = [[0.0; N]; N];
    j[0][0] = panel.conductance_s;
    j[1][1] = gs;
    j[2][2] = 1.0 / 330.0;
    j[3][3] = 1.0 / R60;
    transistor(x, &mut r, &mut j, 0, 2, Some(1), -1.0, p.q26)?;
    transistor(x, &mut r, &mut j, 1, 3, None, 1.0, p.q28)?;
    if let Some(old) = old_c18 {
        let g = C18 / b.dt_s;
        r[0] += g * (x[0] - old);
        j[0][0] += g;
    }
    if r.iter().any(|v| !v.is_finite()) || j.iter().flatten().any(|v| !v.is_finite()) {
        return Err(StepError::ExponentialDomain);
    }
    Ok((r, j))
}

fn solve(
    mut x: [f64; N],
    p: Parameters,
    b: Boundary,
    panel: PanelEquivalent,
    old_c18: Option<f64>,
    budget: SolverBudget,
) -> Result<Port, StepError> {
    for iteration in 0..budget.iterations {
        let (r, j) = evaluate(&x, p, b, panel, old_c18)?;
        let error = max_abs(&r);
        if error < 1e-11 {
            let response = solve_linear(j, [0.0, 0.0, 0.0, 1.0 / R60])?;
            let current_a = (b.tail_v - x[3]) / R60;
            let conductance_s = (1.0 - response[3]) / R60;
            if !current_a.is_finite() || !conductance_s.is_finite() {
                return Err(StepError::ExponentialDomain);
            }
            return Ok(Port {
                next_state: State {
                    node_v: x,
                    c18_v: x[0],
                },
                current_a,
                conductance_s,
                max_kcl_residual_a: error,
                iterations: iteration,
            });
        }
        let delta = solve_linear(j, r.map(|v| -v))?;
        let mut accepted = false;
        for power in 0..budget.line_search_halvings {
            let s = 0.5_f64.powi(power as i32);
            let candidate = std::array::from_fn(|i| x[i] + s * delta[i]);
            if let Ok((next, _)) = evaluate(&candidate, p, b, panel, old_c18) {
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

pub fn solve_dc_port(p: Parameters, b: Boundary) -> Result<Port, StepError> {
    let budget = SolverBudget::default();
    let panel = validate(p, b, budget)?;
    solve(
        [panel.voltage_v, 0.52, -9.998, b.tail_v - 680.0 * 7e-6],
        p,
        b,
        panel,
        None,
        budget,
    )
}

/// Provisional nonlinear TAIL load. The previous C18 voltage is fixed for all
/// outer Newton trials; the caller publishes `next_state` only at convergence.
pub fn solve_input_port(
    previous: &State,
    p: Parameters,
    b: Boundary,
    budget: SolverBudget,
) -> Result<Port, StepError> {
    let panel = validate(p, b, budget)?;
    if previous.node_v.iter().any(|v| !v.is_finite()) || !previous.c18_v.is_finite() {
        return Err(StepError::InvalidInput);
    }
    solve(previous.node_v, p, b, panel, Some(previous.c18_v), budget)
}

pub fn step(
    state: &mut State,
    p: Parameters,
    b: Boundary,
    budget: SolverBudget,
) -> Result<Port, StepError> {
    let port = solve_input_port(state, p, b, budget)?;
    *state = port.next_state;
    Ok(port)
}
