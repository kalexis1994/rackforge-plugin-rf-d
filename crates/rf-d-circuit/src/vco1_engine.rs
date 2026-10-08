//! Portable conditional VCO1 reference engine, not an audio-thread implementation.
//! Exact laboratory Radau kernel; see VCO1_PORTABLE_PROTOCOLO.md for scope.
use crate::{vco1_newton, vco1_radau, vco1_radau_fine as fine, vco1_stamp::{Controls, N, NV}, vco1_startup};
pub use crate::vco1_radau_fine::State;
pub const TICK_S: f64 = fine::MIN_DT_S;

#[derive(Clone, Copy, Debug, PartialEq)]
pub struct Settings {
    pub maximum_half_ticks: u32,
    pub attempt_limit: u32,
}
impl Default for Settings {
    fn default() -> Self { Self { maximum_half_ticks: 65536, attempt_limit: 20 } }
}
impl Settings {
    fn valid(self) -> bool {
        [65536, 131072].contains(&self.maximum_half_ticks) && (1..=20).contains(&self.attempt_limit)
    }
}
#[derive(Clone, Copy, Debug, PartialEq)]
pub struct Checkpoint {
    pub state: State,
    pub controls: Controls,
    pub settings: Settings,
    pub elapsed_ticks: u64,
    pub next_full_ticks: u32,
}
#[derive(Clone, Copy, Debug, PartialEq)]
pub enum Rejection { Nonlinear(vco1_newton::Error), LocalError(f64) }
#[derive(Clone, Copy, Debug, PartialEq)]
pub enum Error {
    InvalidInput,
    Startup(vco1_startup::Error),
    PrecisionLimit(Rejection),
    AttemptLimit(Rejection),
    Observation(crate::vco1_stamp::Error),
}
pub struct Engine { checkpoint: Checkpoint }
pub struct Endpoint {
    pub elapsed_ticks: u64,
    pub pair: vco1_radau::Pair,
    /// Outward terminal current: Qa/Q10 collector and Q7 gate, including Radau charge.
    pub current_a: [f64; 3],
    pub panel_current_a: f64,
}
pub struct Accepted {
    pub endpoints: [Endpoint; 2],
    pub half_ticks: u32,
    pub error_ratio: f64,
    pub attempts: u32,
}
fn endpoint(pair: vco1_radau::Pair, old: State, h: f64, elapsed_ticks: u64) -> Result<Endpoint, Error> {
    let b=pair.endpoint.candidate;
    let current_a=vco1_radau::terminal_currents(&pair,old,h).map_err(Error::Observation)?;
    let panel_current_a=(b.high[46]-b.high[39]+b.low[46]-b.low[39])/12500.;
    if current_a.iter().chain([panel_current_a].iter()).any(|v|!v.is_finite()) {
        return Err(Error::Observation(crate::vco1_stamp::Error::NonFinite));
    }
    Ok(Endpoint { elapsed_ticks, pair, current_a, panel_current_a })
}
impl Engine {
    /// Own circuit-derived conditioned C1=0 startup. Forcing is absent in all steps.
    pub fn startup(controls: Controls, settings: Settings) -> Result<Self, Error> {
        if !settings.valid() { return Err(Error::InvalidInput); }
        let initial=vco1_startup::startup(controls).map_err(Error::Startup)?;
        if initial.residual_ratio>1. || initial.correction_ratio>1. {
            return Err(Error::Startup(vco1_startup::Error::Newton(vco1_newton::Error::IterationLimit)));
        }
        Ok(Self { checkpoint: Checkpoint {
            state: State::from_nodes(initial.nodes), controls, settings, elapsed_ticks: 0,
            next_full_ticks: 2*settings.maximum_half_ticks,
        } })
    }
    /// Restore a complete accepted pair boundary; validates representation, not provenance.
    pub fn restore(checkpoint: Checkpoint) -> Result<Self, Error> {
        let q=checkpoint;
        if !q.settings.valid() || q.elapsed_ticks%8!=0 || q.next_full_ticks<8
            || !q.next_full_ticks.is_power_of_two() || q.next_full_ticks>2*q.settings.maximum_half_ticks {
            return Err(Error::InvalidInput);
        }
        fine::linearize(q.state,[0.;N],q.controls,4.*TICK_S).map_err(|_|Error::InvalidInput)?;
        Ok(Self { checkpoint })
    }
    pub fn checkpoint(&self) -> Checkpoint { self.checkpoint }
    /// Advance one accepted pair, staying at or before an exact target tick.
    /// Errors preserve state, controls, proposal and clock. There is no hidden elapsed-time loop.
    pub fn advance_to(&mut self, target_ticks: u64) -> Result<Accepted, Error> {
        let q=self.checkpoint;
        if target_ticks<=q.elapsed_ticks || target_ticks%8!=0 { return Err(Error::InvalidInput); }
        let remaining=target_ticks-q.elapsed_ticks;
        let mut ticks=q.next_full_ticks;
        while u64::from(ticks)>remaining { ticks/=2; }
        for attempts in 1..=q.settings.attempt_limit {
            let h=f64::from(ticks/2)*TICK_S;
            let trial=(|| {
                let full=vco1_radau::step(q.controls,q.state,2.*h)?;
                let mid=vco1_radau::step(q.controls,q.state,h)?;
                let end=vco1_radau::step(q.controls,mid.endpoint.candidate,h)?;
                let difference=full.endpoint.candidate.difference(end.endpoint.candidate);
                let error=(0..N).fold(0_f64,|a,k|a.max(difference[k].abs()/if k<NV {2e-6} else {2e-9}));
                Ok::<_,vco1_newton::Error>((mid,end,error))
            })();
            let reason=match trial {
                Ok((mid,end,error_ratio)) if error_ratio.is_finite() && error_ratio<=1. => {
                    let state=end.endpoint.candidate;
                    let midpoint_state=mid.endpoint.candidate;
                    let midpoint_clock=q.elapsed_ticks+u64::from(ticks/2);
                    let end_clock=q.elapsed_ticks+u64::from(ticks);
                    // Observation failure cannot leave a published midpoint or advanced clock.
                    let endpoints=[endpoint(mid,q.state,h,midpoint_clock)?,endpoint(end,midpoint_state,h,end_clock)?];
                    self.checkpoint=Checkpoint { state, elapsed_ticks:end_clock,
                        next_full_ticks:if error_ratio<=0.25 {(ticks*2).min(2*q.settings.maximum_half_ticks)} else {ticks}, ..q };
                    return Ok(Accepted { endpoints, half_ticks:ticks/2,error_ratio,attempts });
                },
                Ok((_,_,e))=>Rejection::LocalError(e),
                Err(e)=>Rejection::Nonlinear(e),
            };
            if ticks==8 { return Err(Error::PrecisionLimit(reason)); }
            if attempts==q.settings.attempt_limit { return Err(Error::AttemptLimit(reason)); }
            ticks/=2;
        }
        unreachable!("validated positive attempt budget")
    }
}
