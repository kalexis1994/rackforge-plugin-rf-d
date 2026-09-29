//! R77 and R21 coupled implicitly to the dynamic board-3 C19 input port.
//! C2_RIGHT is imposed; the 48-node upstream circuit is not solved here.

use crate::{
    initial_state, solve_input_port, InputPortResponse, Parameters, SolverBudget, State,
    StepDiagnostics, StepError,
};

const R77_OHM: f64 = 1000.0;
const R21_OHM: f64 = 5000.0;
const KCL_TOLERANCE_A: f64 = 1e-10;

#[derive(Clone, Copy, Debug, PartialEq)]
pub struct PanelState {
    pub amp: State,
    pub r21_wiper_v: f64,
}

#[derive(Clone, Copy, Debug)]
pub struct PanelStepDiagnostics {
    pub outer_iterations: usize,
    pub max_panel_kcl_residual_a: f64,
    pub board3: StepDiagnostics,
}

#[derive(Clone, Copy, Debug)]
pub struct PanelStepResult {
    pub board4_pin22_v: f64,
    pub r21_wiper_v: f64,
    pub j7_v: f64,
    /// Current drawn from C2_RIGHT through R77, positive toward panel.
    pub r77_current_a: f64,
    /// Local derivative d(I_R77)/d(V_C2_RIGHT), with prior state fixed.
    pub r77_input_conductance_s: f64,
    pub c19_current_a: f64,
    pub diagnostics: PanelStepDiagnostics,
}

#[derive(Clone, Copy, Debug)]
pub struct PanelBoundary {
    pub c2_right_v: f64,
    pub r21_lower_ohm: f64,
    pub dt_s: f64,
    pub tip_load_ohm: Option<f64>,
    pub ring_load_ohm: Option<f64>,
}

pub fn initial_panel_state(p: Parameters) -> Result<PanelState, StepError> {
    Ok(PanelState {
        amp: initial_state(p)?,
        r21_wiper_v: 0.0,
    })
}

/// The R77/R21 network is reduced algebraically, preserving C19 as a
/// nonlinear dynamic port. Every outer Newton trial uses the same previous
/// board-3 state, and a failure leaves the entire panel state untouched.
pub fn solve_panel_boundary(
    state: &mut PanelState,
    p: Parameters,
    boundary: PanelBoundary,
    budget: SolverBudget,
) -> Result<PanelStepResult, StepError> {
    let PanelBoundary {
        c2_right_v,
        r21_lower_ohm,
        dt_s,
        tip_load_ohm,
        ring_load_ohm,
    } = boundary;
    if !c2_right_v.is_finite()
        || !state.r21_wiper_v.is_finite()
        || !r21_lower_ohm.is_finite()
        || !(0.0..R21_OHM).contains(&r21_lower_ohm)
        || r21_lower_ohm == 0.0
        || !(1..=16).contains(&budget.iterations)
        || !(1..=16).contains(&budget.line_search_halvings)
    {
        return Err(StepError::InvalidInput);
    }
    // R77 and the upper R21 segment form a series path from C2_RIGHT.
    let series_ohm = R77_OHM + R21_OHM - r21_lower_ohm;
    let g_series = 1.0 / series_ohm;
    let g_lower = 1.0 / r21_lower_ohm;
    let old_amp = state.amp;
    let mut wiper_v = state.r21_wiper_v;
    let mut cached_port: Option<InputPortResponse> = None;
    for iteration in 0..budget.iterations {
        let port = match cached_port.take() {
            Some(response) => response,
            None => solve_input_port(
                &old_amp,
                p,
                wiper_v,
                dt_s,
                tip_load_ohm,
                ring_load_ohm,
                budget,
            )?,
        };
        let residual = (wiper_v - c2_right_v) * g_series + wiper_v * g_lower + port.current_a;
        if residual.abs() < KCL_TOLERANCE_A {
            let pin22_v = c2_right_v + (wiper_v - c2_right_v) * R77_OHM / series_ohm;
            let r77_current_a = (c2_right_v - wiper_v) * g_series;
            let panel_slope = g_series + g_lower + port.conductance_s;
            if !panel_slope.is_finite() || panel_slope.abs() < 1e-15 {
                return Err(StepError::SingularJacobian);
            }
            let r77_input_conductance_s = g_series * (1.0 - g_series / panel_slope);
            state.amp = port.next_state;
            state.r21_wiper_v = wiper_v;
            return Ok(PanelStepResult {
                board4_pin22_v: pin22_v,
                r21_wiper_v: wiper_v,
                j7_v: port.next_state.node_v[11],
                r77_current_a,
                r77_input_conductance_s,
                c19_current_a: port.current_a,
                diagnostics: PanelStepDiagnostics {
                    outer_iterations: iteration,
                    max_panel_kcl_residual_a: residual.abs(),
                    board3: port.diagnostics,
                },
            });
        }
        let derivative = g_series + g_lower + port.conductance_s;
        if !derivative.is_finite() || derivative.abs() < 1e-15 {
            return Err(StepError::SingularJacobian);
        }
        let direction = -residual / derivative;
        let mut accepted = false;
        for power in 0..budget.line_search_halvings {
            let trial_v = wiper_v + 0.5_f64.powi(power as i32) * direction;
            if let Ok(trial) = solve_input_port(
                &old_amp,
                p,
                trial_v,
                dt_s,
                tip_load_ohm,
                ring_load_ohm,
                budget,
            ) {
                let trial_residual =
                    (trial_v - c2_right_v) * g_series + trial_v * g_lower + trial.current_a;
                if trial_residual.abs() < residual.abs() {
                    wiper_v = trial_v;
                    cached_port = Some(trial);
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
