//! C2 and R75/main panel coupled to the R77/R21/board-3 dynamic port.
//! The Q17 collector voltage is imposed until the upstream 47 nodes are ported.

use crate::panel::{initial_panel_state, PanelState, PanelStepDiagnostics, PanelStepResult};
use crate::{solve_input_port, InputPortResponse, Parameters, SolverBudget, StepError};

const C2_F: f64 = 10e-6;
const R75_OHM: f64 = 1000.0;
const R77_OHM: f64 = 1000.0;
const R20_OHM: f64 = 5000.0;
const R21_OHM: f64 = 5000.0;
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

/// Dynamic load presented to the upstream Q17 collector by C2 and both
/// output branches. Current is positive from Q17 into C2.
#[derive(Clone, Copy, Debug)]
pub struct OutputInputPort {
    pub next_state: OutputState,
    pub output: OutputStepResult,
    pub current_a: f64,
    /// d(I_C2)/d(V_Q17c) at fixed previous capacitor/device state.
    pub conductance_s: f64,
}

#[derive(Clone, Copy)]
pub(crate) struct MainLoad {
    pub equivalent_ohm: f64,
    pub hi_to_pin21: f64,
    pub lo_to_hi: f64,
}

pub(crate) fn main_load(b: OutputBoundary) -> Result<MainLoad, StepError> {
    if !b.q17_collector_v.is_finite()
        || !b.r20_lower_ohm.is_finite()
        || b.r20_lower_ohm < 0.0
        || b.r20_lower_ohm > R20_OHM
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
    // Exact lower-end short: HI and LO are grounded. At the upper end
    // upper=0 joins PIN21 to HI; R75 remains in series in every caller.
    // SW18 OFF at the upper end has equivalent=0 (PIN21 grounded), also
    // finite after adding R75. No epsilon resistor or zero-ohm division.
    let wiper_shunt = if b.r20_lower_ohm == 0.0 {
        0.0
    } else {
        1.0 / (1.0 / b.r20_lower_ohm + 1.0 / hi_shunt)
    };
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

#[derive(Clone, Copy)]
struct ReducedTrial {
    wiper_v: f64,
    c2_right_v: f64,
    port: InputPortResponse,
    wiper_kcl_a: f64,
    slope_s: f64,
}

#[allow(clippy::too_many_arguments)]
fn reduced_trial(
    previous_panel: PanelState,
    previous_c2_cap_v: f64,
    p: Parameters,
    b: OutputBoundary,
    budget: SolverBudget,
    wiper_v: f64,
    main_g: f64,
    series_g: f64,
    lower_g: f64,
) -> Result<ReducedTrial, StepError> {
    let port = solve_input_port(
        &previous_panel.amp,
        p,
        wiper_v,
        b.dt_s,
        b.tip_load_ohm,
        b.ring_load_ohm,
        budget,
    )?;
    let c2_g = C2_F / b.dt_s;
    let denominator = main_g + series_g + c2_g;
    let c2_right_v =
        (series_g * wiper_v + c2_g * (b.q17_collector_v - previous_c2_cap_v)) / denominator;
    let wiper_kcl_a = (wiper_v - c2_right_v) * series_g + wiper_v * lower_g + port.current_a;
    let slope_s = series_g * (1.0 - series_g / denominator) + lower_g + port.conductance_s;
    if !c2_right_v.is_finite() || !wiper_kcl_a.is_finite() || !slope_s.is_finite() {
        return Err(StepError::ExponentialDomain);
    }
    Ok(ReducedTrial {
        wiper_v,
        c2_right_v,
        port,
        wiper_kcl_a,
        slope_s,
    })
}

/// Implicitly solve C2_RIGHT, the passive main output and the complete
/// dynamic headphone boundary. Linear C2/R75/R77 KCL eliminates C2_RIGHT;
/// the one remaining Newton unknown is the R21 wiper. All trials use one
/// immutable previous state.
pub fn solve_output_boundary(
    state: &mut OutputState,
    p: Parameters,
    b: OutputBoundary,
    budget: SolverBudget,
) -> Result<OutputStepResult, StepError> {
    let load = main_load(b)?;
    if !state.c2_right_v.is_finite()
        || !state.c2_capacitor_v.is_finite()
        || !state.panel.r21_wiper_v.is_finite()
        || !b.r21_lower_ohm.is_finite()
        || b.r21_lower_ohm <= 0.0
        || b.r21_lower_ohm >= R21_OHM
        || !(1..=16).contains(&budget.iterations)
        || !(1..=16).contains(&budget.line_search_halvings)
    {
        return Err(StepError::InvalidInput);
    }
    let main_g = 1.0 / (R75_OHM + load.equivalent_ohm);
    let series_ohm = R77_OHM + R21_OHM - b.r21_lower_ohm;
    let series_g = 1.0 / series_ohm;
    let lower_g = 1.0 / b.r21_lower_ohm;
    let previous = *state;
    let mut wiper_v = state.panel.r21_wiper_v;
    let mut cached: Option<ReducedTrial> = None;
    for iteration in 0..budget.iterations {
        let point = match cached.take() {
            Some(value) => value,
            None => reduced_trial(
                previous.panel,
                previous.c2_capacitor_v,
                p,
                b,
                budget,
                wiper_v,
                main_g,
                series_g,
                lower_g,
            )?,
        };
        if point.wiper_kcl_a.abs() < KCL_TOLERANCE_A {
            let x = point.c2_right_v;
            let c2_current = C2_F / b.dt_s * (b.q17_collector_v - x - previous.c2_capacitor_v);
            let r77_current = (x - point.wiper_v) * series_g;
            let c2_kcl = main_g * x + r77_current - c2_current;
            if !c2_kcl.is_finite() || c2_kcl.abs() >= KCL_TOLERANCE_A {
                return Err(StepError::NoDecrease);
            }
            let panel_slope = series_g + lower_g + point.port.conductance_s;
            if !panel_slope.is_finite() || panel_slope.abs() < 1e-15 {
                return Err(StepError::SingularJacobian);
            }
            let panel_result = PanelStepResult {
                board4_pin22_v: x + (point.wiper_v - x) * R77_OHM / series_ohm,
                r21_wiper_v: point.wiper_v,
                j7_v: point.port.next_state.node_v[11],
                r77_current_a: r77_current,
                r77_input_conductance_s: series_g * (1.0 - series_g / panel_slope),
                c19_current_a: point.port.current_a,
                diagnostics: PanelStepDiagnostics {
                    outer_iterations: iteration,
                    max_panel_kcl_residual_a: point.wiper_kcl_a.abs(),
                    board3: point.port.diagnostics,
                },
            };
            let pin21 = x * load.equivalent_ohm / (R75_OHM + load.equivalent_ohm);
            let hi = pin21 * load.hi_to_pin21;
            let lo = hi * load.lo_to_hi;
            state.panel = PanelState {
                amp: point.port.next_state,
                r21_wiper_v: point.wiper_v,
            };
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
                r77_current_a: r77_current,
                outer_iterations: iteration,
                max_c2_right_kcl_residual_a: c2_kcl.abs(),
                panel: panel_result,
            });
        }
        if point.slope_s.abs() < 1e-15 {
            return Err(StepError::SingularJacobian);
        }
        let direction = -point.wiper_kcl_a / point.slope_s;
        let mut accepted = false;
        for power in 0..budget.line_search_halvings {
            let candidate_wiper = wiper_v + 0.5_f64.powi(power as i32) * direction;
            if let Ok(candidate) = reduced_trial(
                previous.panel,
                previous.c2_capacitor_v,
                p,
                b,
                budget,
                candidate_wiper,
                main_g,
                series_g,
                lower_g,
            ) {
                if candidate.wiper_kcl_a.abs() < point.wiper_kcl_a.abs() {
                    wiper_v = candidate_wiper;
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

/// Return a provisional output solve and its exact local input tangent.
/// An upstream Newton must retry from the same `previous_state` on every
/// candidate and commit `next_state` only after the joint system converges.
pub fn solve_output_input_port(
    previous_state: &OutputState,
    p: Parameters,
    b: OutputBoundary,
    budget: SolverBudget,
) -> Result<OutputInputPort, StepError> {
    let mut next_state = *previous_state;
    let output = solve_output_boundary(&mut next_state, p, b, budget)?;
    let load = main_load(b)?;
    let c2_g = C2_F / b.dt_s;
    let main_g = 1.0 / (R75_OHM + load.equivalent_ohm);
    let denominator = c2_g + main_g + output.panel.r77_input_conductance_s;
    if !denominator.is_finite() || denominator.abs() < 1e-15 {
        return Err(StepError::SingularJacobian);
    }
    let conductance_s = c2_g * (1.0 - c2_g / denominator);
    if !conductance_s.is_finite() {
        return Err(StepError::ExponentialDomain);
    }
    Ok(OutputInputPort {
        next_state,
        current_a: output.c2_current_a,
        conductance_s,
        output,
    })
}
