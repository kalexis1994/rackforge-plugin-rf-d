//! C2 and R75/main panel coupled to the R77/R21/board-3 dynamic port.
//! The Q17 collector voltage is imposed until the upstream 47 nodes are ported.

use crate::panel::{
    initial_panel_state, solve_panel_boundary, PanelBoundary, PanelState, PanelStepResult,
};
use crate::{Parameters, SolverBudget, StepError};

const C2_F: f64 = 10e-6;
const R75_OHM: f64 = 1000.0;
const R20_OHM: f64 = 5000.0;
const R57_OHM: f64 = 33000.0;
const R58_OHM: f64 = 1000.0;
const KCL_TOLERANCE_A: f64 = 1e-10;

#[derive(Clone, Copy, Debug, PartialEq)]
pub struct OutputState {
    pub panel: PanelState,
    pub c2_right_v: f64,
    /// Voltage from Q17 collector to C2_RIGHT, including DC bias.
    pub c2_capacitor_v: f64,
}

#[derive(Clone, Copy, Debug)]
pub struct OutputBoundary {
    pub q17_collector_v: f64,
    pub r20_lower_ohm: f64,
    pub hi_load_ohm: f64,
    pub lo_load_ohm: f64,
    pub sw18_on: bool,
    pub r21_lower_ohm: f64,
    pub tip_load_ohm: Option<f64>,
    pub ring_load_ohm: Option<f64>,
    pub dt_s: f64,
}

#[derive(Clone, Copy, Debug)]
pub struct OutputStepResult {
    pub c2_right_v: f64,
    pub board4_pin21_v: f64,
    pub j4_hi_v: f64,
    pub j5_lo_v: f64,
    pub j7_v: f64,
    /// Current from Q17 collector through C2 to C2_RIGHT.
    pub c2_current_a: f64,
    pub r75_current_a: f64,
    pub r77_current_a: f64,
    pub outer_iterations: usize,
    pub max_c2_right_kcl_residual_a: f64,
    pub panel: PanelStepResult,
}

#[derive(Clone, Copy)]
struct MainLoad {
    equivalent_ohm: f64,
    hi_to_pin21: f64,
    lo_to_hi: f64,
}

fn main_load(b: OutputBoundary) -> Result<MainLoad, StepError> {
    if !b.q17_collector_v.is_finite()
        || !b.r20_lower_ohm.is_finite()
        || b.r20_lower_ohm <= 0.0
        || b.r20_lower_ohm >= R20_OHM
        || !b.hi_load_ohm.is_finite()
        || b.hi_load_ohm <= 0.0
        || !b.lo_load_ohm.is_finite()
        || b.lo_load_ohm <= 0.0
        || !b.dt_s.is_finite()
        || b.dt_s <= 0.0
    {
        return Err(StepError::InvalidInput);
    }
    let upper = R20_OHM - b.r20_lower_ohm;
    if !b.sw18_on {
        return Ok(MainLoad {
            equivalent_ohm: upper,
            hi_to_pin21: 0.0,
            lo_to_hi: 0.0,
        });
    }
    let low_shunt = 1.0 / (1.0 / R58_OHM + 1.0 / b.lo_load_ohm);
    let low_leg = R57_OHM + low_shunt;
    let hi_shunt = 1.0 / (1.0 / b.hi_load_ohm + 1.0 / low_leg);
    let wiper_shunt = 1.0 / (1.0 / b.r20_lower_ohm + 1.0 / hi_shunt);
    let equivalent = upper + wiper_shunt;
    if !equivalent.is_finite() || equivalent <= 0.0 {
        return Err(StepError::InvalidInput);
    }
    Ok(MainLoad {
        equivalent_ohm: equivalent,
        hi_to_pin21: wiper_shunt / equivalent,
        lo_to_hi: low_shunt / low_leg,
    })
}

pub fn initial_output_state(
    p: Parameters,
    q17_collector_dc_v: f64,
) -> Result<OutputState, StepError> {
    if !q17_collector_dc_v.is_finite() {
        return Err(StepError::InvalidInput);
    }
    Ok(OutputState {
        panel: initial_panel_state(p)?,
        c2_right_v: 0.0,
        c2_capacitor_v: q17_collector_dc_v,
    })
}

fn trial(
    previous_panel: PanelState,
    previous_c2_cap_v: f64,
    p: Parameters,
    b: OutputBoundary,
    budget: SolverBudget,
    c2_right_v: f64,
    main_g: f64,
) -> Result<(PanelState, PanelStepResult, f64, f64), StepError> {
    let mut panel = previous_panel;
    let response = solve_panel_boundary(
        &mut panel,
        p,
        PanelBoundary {
            c2_right_v,
            r21_lower_ohm: b.r21_lower_ohm,
            dt_s: b.dt_s,
            tip_load_ohm: b.tip_load_ohm,
            ring_load_ohm: b.ring_load_ohm,
        },
        budget,
    )?;
    let c2_g = C2_F / b.dt_s;
    let c2_current = c2_g * (b.q17_collector_v - c2_right_v - previous_c2_cap_v);
    let residual = main_g * c2_right_v + response.r77_current_a - c2_current;
    let slope = main_g + response.r77_input_conductance_s + c2_g;
    if !residual.is_finite() || !slope.is_finite() {
        return Err(StepError::ExponentialDomain);
    }
    Ok((panel, response, residual, slope))
}

/// Implicitly solve C2_RIGHT, the passive main output and the complete
/// dynamic headphone boundary. Every trial uses one immutable previous state.
pub fn solve_output_boundary(
    state: &mut OutputState,
    p: Parameters,
    b: OutputBoundary,
    budget: SolverBudget,
) -> Result<OutputStepResult, StepError> {
    let load = main_load(b)?;
    if !state.c2_right_v.is_finite()
        || !state.c2_capacitor_v.is_finite()
        || !(1..=16).contains(&budget.iterations)
        || !(1..=16).contains(&budget.line_search_halvings)
    {
        return Err(StepError::InvalidInput);
    }
    let main_g = 1.0 / (R75_OHM + load.equivalent_ohm);
    let previous = *state;
    let mut x = state.c2_right_v;
    let mut cached: Option<(PanelState, PanelStepResult, f64, f64)> = None;
    for iteration in 0..budget.iterations {
        let (panel_state, panel_result, residual, slope) = match cached.take() {
            Some(value) => value,
            None => trial(
                previous.panel,
                previous.c2_capacitor_v,
                p,
                b,
                budget,
                x,
                main_g,
            )?,
        };
        if residual.abs() < KCL_TOLERANCE_A {
            let c2_current = C2_F / b.dt_s * (b.q17_collector_v - x - previous.c2_capacitor_v);
            let pin21 = x * load.equivalent_ohm / (R75_OHM + load.equivalent_ohm);
            let hi = pin21 * load.hi_to_pin21;
            let lo = hi * load.lo_to_hi;
            state.panel = panel_state;
            state.c2_right_v = x;
            state.c2_capacitor_v = b.q17_collector_v - x;
            return Ok(OutputStepResult {
                c2_right_v: x,
                board4_pin21_v: pin21,
                j4_hi_v: hi,
                j5_lo_v: lo,
                j7_v: panel_result.j7_v,
                c2_current_a: c2_current,
                r75_current_a: main_g * x,
                r77_current_a: panel_result.r77_current_a,
                outer_iterations: iteration,
                max_c2_right_kcl_residual_a: residual.abs(),
                panel: panel_result,
            });
        }
        if slope.abs() < 1e-15 {
            return Err(StepError::SingularJacobian);
        }
        let direction = -residual / slope;
        let mut accepted = false;
        for power in 0..budget.line_search_halvings {
            let candidate_x = x + 0.5_f64.powi(power as i32) * direction;
            if let Ok(candidate) = trial(
                previous.panel,
                previous.c2_capacitor_v,
                p,
                b,
                budget,
                candidate_x,
                main_g,
            ) {
                if candidate.2.abs() < residual.abs() {
                    x = candidate_x;
                    cached = Some(candidate);
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
