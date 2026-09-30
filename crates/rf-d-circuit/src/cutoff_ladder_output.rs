//! Q26/Q28/C18, the ladder, optional EMPHASIS and both VCAs through J7.
//! All control sources are imposed electrical boundaries, not a complete voice.

use crate::cutoff;
use crate::ladder_recovery_output::{self as chain, CutoffContext, StepResult};
use crate::output_conversion::Parameters as ConversionParameters;
use crate::recovery_vca_output::Boundary as RecoveryBoundary;
use crate::vca2_output::Parameters as TransistorParameters;
use crate::{Parameters as HeadphoneParameters, SolverBudget, StepError};

#[derive(Clone, Copy, Debug)]
pub struct Parameters {
    pub ladder_transistor: TransistorParameters,
    pub cutoff: cutoff::Parameters,
    pub r61_ohm: f64,
    pub r30_ohm: f64,
}

#[derive(Clone, Copy, Debug)]
pub struct Boundary {
    pub bus_v: f64,
    pub recovery: RecoveryBoundary,
    pub panel: cutoff::PanelBoundary,
    pub range_fraction_from_ground: f64,
    /// None opens the laboratory C10 return; Some closes its series resistance.
    pub r14_ohm: Option<f64>,
}

#[derive(Clone, Copy, Debug, PartialEq)]
pub struct State {
    pub chain: chain::State,
    pub cutoff: cutoff::State,
}

fn inputs(
    p: Parameters,
    b: Boundary,
    previous: cutoff::State,
) -> Result<
    (
        chain::Parameters,
        chain::Boundary,
        CutoffContext,
        Option<f64>,
    ),
    StepError,
> {
    let lp = chain::Parameters {
        transistor: p.ladder_transistor,
        // Internal fixed-current stamp is replaced by the nonlinear TAIL port
        // on every residual evaluation; this value is not an electrical input.
        tail_current_a: 1e-6,
        r61_ohm: p.r61_ohm,
        r30_ohm: p.r30_ohm,
    };
    let lb = chain::Boundary {
        bus_v: b.bus_v,
        recovery: b.recovery,
    };
    let context = CutoffContext {
        previous,
        parameters: p.cutoff,
        boundary: cutoff::Boundary {
            panel: b.panel,
            range_fraction_from_ground: b.range_fraction_from_ground,
            tail_v: 0.0, // Replaced by the outer trial's TAIL voltage.
            dt_s: b.recovery.vca.second.output.output.dt_s,
        },
    };
    let series = b
        .r14_ohm
        .map(|v| chain::return_series_ohm(lp, v))
        .transpose()?;
    Ok((lp, lb, context, series))
}

/// Solve Q26/Q28 and all sixteen ladder nodes jointly at DC. Coupling
/// capacitors are open; their charges are initialized at the converged point.
pub fn initial_state(
    p: Parameters,
    conversion: ConversionParameters,
    headphone: HeadphoneParameters,
    b: Boundary,
    ladder_seed: [f64; 16],
) -> Result<State, StepError> {
    let dummy = cutoff::State {
        node_v: [0.0; 4],
        c18_v: 0.0,
    };
    let (lp, lb, context, _) = inputs(p, b, dummy)?;
    let (chain, cutoff) =
        chain::initial_state_internal(lp, conversion, headphone, lb, ladder_seed, Some(context))?;
    Ok(State {
        chain,
        cutoff: cutoff.expect("connected cutoff port"),
    })
}

/// Same C18/capacitor history on every trial, including predictor fallback.
/// No state is published until the entire nested circuit converges.
pub fn step(
    state: &mut State,
    p: Parameters,
    conversion: ConversionParameters,
    headphone: HeadphoneParameters,
    b: Boundary,
    budget: SolverBudget,
) -> Result<StepResult, StepError> {
    let (lp, lb, context, series) = inputs(p, b, state.cutoff)?;
    let (result, cutoff) = chain::step_internal(
        &mut state.chain,
        lp,
        conversion,
        headphone,
        lb,
        budget,
        series,
        Some(context),
    )?;
    state.cutoff = cutoff.expect("connected cutoff port");
    Ok(result)
}
