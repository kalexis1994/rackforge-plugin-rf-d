//! Bounded step-doubling around the same charged H128 Radau stages.
use crate::{family::Family, solver, voice, StepError};
use voice::{Accepted, Controls, Parameters, State, N};

pub const TICKS: usize = 65_536;
pub const MAX_STEP: usize = TICKS / 8;
const MIN_STEP: usize = 2;

pub struct Step {
    pub half: [Accepted; 2],
    pub ticks: usize,
    pub error: f64,
}

fn error(coarse: &Accepted, fine: &Accepted) -> f64 {
    let a = coarse.stages.chain[1].now;
    let b = fine.stages.chain[1].now;
    let phase = coarse.stages.phase[1] - fine.stages.phase[1];
    let distance = phase.abs().min(1. - phase.abs());
    (0..N).fold(distance / 1e-11, |worst, i| {
        let difference = (a.high[i] - b.high[i]) + (a.low[i] - b.low[i]);
        worst.max(difference.abs() / (2e-9 + 2e-10 * b.high[i].abs()))
    })
}

pub fn advance(
    work: &mut solver::Workspace, family: &Family, mut p: Parameters, old: State, phase: f64,
    controls: Controls, tick: usize, mut span: usize, rejected: &mut usize,
) -> Result<Step, StepError> {
    if !(MIN_STEP..=MAX_STEP).contains(&span) || !span.is_power_of_two() {
        return Err(StepError::InvalidInput);
    }
    let clock = 1. / (48_000 * TICKS) as f64;
    loop {
        let h = span as f64 * clock;
        p.time = tick as f64 * clock;
        let trial = (|| {
            let coarse = voice::radau(work, family, p, old, phase, controls, h, 80)?;
            let first = voice::radau(work, family, p, old, phase, controls, h / 2., 80)?;
            let mut later = p;
            later.time += h / 2.;
            let second = voice::radau(
                work, family, later, first.stages.chain[1].now, first.stages.phase[1],
                controls, h / 2., 80,
            )?;
            let defect = error(&coarse, &second);
            Ok::<_, StepError>(Step { half: [first, second], ticks: span, error: defect })
        })();
        match trial {
            Ok(step) if step.error <= 1. => return Ok(step),
            Ok(_) | Err(StepError::NoDecrease | StepError::IterationBudget) if span > MIN_STEP => {
                *rejected += 1;
                span /= 2;
            }
            Ok(_) => return Err(StepError::IterationBudget),
            Err(error) => return Err(error),
        }
    }
}
