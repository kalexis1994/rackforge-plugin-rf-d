//! Loaded 118-node voice with the two H128 phase stages eliminated analytically.
use crate::StepError;
use crate::family::{Family, Port};
use crate::{graph, solver};
pub use graph::{Controls, Parameters, State, B, M, N};

pub const BUS: usize = graph::chain_index(66);
pub const BASE: usize = graph::chain_index(6);
pub const J7: usize = graph::chain_index(61);
const A: [[f64; 2]; 2] = [[5. / 12., -1. / 12.], [3. / 4., 1. / 4.]];

pub struct Stages {
    pub chain: [graph::Parts; 2],
    pub phase: [f64; 2],
    pub ports: [Port; 2],
}

pub struct Accepted {
    pub stages: Stages,
    pub delta: [State; 2],
    pub residual_a: f64,
    pub correction_v: f64,
    pub iterations: usize,
}

pub fn stages<const FULL: bool>(
    family: &Family, p: Parameters, old: State, phase: f64, delta: [State; 2],
    controls: Controls, h: f64,
) -> Result<Stages, StepError> {
    if !(0. ..1.).contains(&phase) || !(rf_d_circuit::chain_charge::MIN_DT_S..=1e-3).contains(&h) {
        return Err(StepError::InvalidInput);
    }
    let mut chain = [
        graph::parts::<FULL>(p, old, delta[0], controls, h, p.time + h / 3.)?,
        graph::parts::<FULL>(p, old, delta[1], controls, h, p.time + h)?,
    ];
    let bus = chain.each_ref().map(|s| s.now.high[BUS] + s.now.low[BUS]);
    let rate = [
        family.frequency(bus[0]).map_err(|_| StepError::InvalidInput)?.0,
        family.frequency(bus[1]).map_err(|_| StepError::InvalidInput)?.0,
    ];
    let phase = A.map(|row| (phase + h * (row[0] * rate[0] + row[1] * rate[1])).rem_euclid(1.));
    let ports = [
        family.observe(bus[0], phase[0]).map_err(|_| StepError::InvalidInput)?,
        family.observe(bus[1], phase[1]).map_err(|_| StepError::InvalidInput)?,
    ];
    for j in 0..2 {
        chain[j].dc[BUS] += ports[j].currents_a[2];
        if FULL {
            // Each off-diagonal BUS derivative is encoded in the solver's
            // cross-stage tangent slot. This does not modify physical dq.
            let i = 1 - j;
            let phase_factor = h * ports[j].frequency_dbus;
            let cross = ports[i].bus_dphase * A[i][j] * phase_factor / B[i][j];
            let direct = ports[j].bus_dbus + ports[j].bus_dphase * A[j][j] * phase_factor
                - B[j][j] * cross;
            chain[j].tangent.add(BUS, BUS, direct, cross)?;
        }
    }
    Ok(Stages { chain, phase, ports })
}

pub fn residual(stages: &Stages) -> [f64; M] {
    std::array::from_fn(|k| {
        let (i, row) = (k / N, k % N);
        stages.chain[i].dc[row] + B[i][0] * stages.chain[0].dq[row]
            + B[i][1] * stages.chain[1].dq[row]
    })
}

fn maximum<const L: usize>(values: &[f64; L]) -> f64 {
    values.iter().fold(0_f64, |m, value| m.max(value.abs()))
}

fn direction(work: &mut solver::Workspace, stages: &Stages, r: [f64; M]) -> Result<[f64; M], StepError> {
    let factors = stages.chain.each_ref().map(|s| solver::Stage { tangent: &s.tangent });
    work.solve(factors, B, r.map(|value| -value))
}

pub fn radau(
    work: &mut solver::Workspace, family: &Family, p: Parameters, old: State, phase: f64,
    controls: Controls, h: f64, budget: usize,
) -> Result<Accepted, StepError> {
    if !(1..=80).contains(&budget) || controls.optional != old.optional {
        return Err(StepError::InvalidInput);
    }
    let mut delta = [State::new([0.; N], old.optional); 2];
    if controls.key - old.high[22] - old.low[22] > 0.5 {
        for stage in &mut delta {
            stage.high[22] = controls.key - 0.5 - old.high[22] - old.low[22];
        }
    }
    for iterations in 1..=budget {
        let current = stages::<true>(family, p, old, phase, delta, controls, h)?;
        let r = residual(&current);
        let correction = direction(work, &current, r)?;
        let norm = maximum(&r);
        let size = maximum(&correction);
        if norm <= 1e-12 && size <= 2e-9 {
            return Ok(Accepted { stages: current, delta, residual_a: norm, correction_v: size, iterations });
        }
        let mut improved = false;
        for half in 0..24 {
            let scale = 2_f64.powi(-half);
            let trial = std::array::from_fn(|i| delta[i].advanced(
                std::array::from_fn(|row| scale * correction[i * N + row])));
            let better = if norm <= 1e-12 {
                if let Ok(check) = stages::<true>(family, p, old, phase, trial, controls, h) {
                    let r = residual(&check);
                    maximum(&r) <= 1e-12 && maximum(&direction(work, &check, r)?) < size
                } else {
                    false
                }
            } else {
                stages::<false>(family, p, old, phase, trial, controls, h)
                    .is_ok_and(|check| maximum(&residual(&check)) < norm)
            };
            if better {
                delta = trial;
                improved = true;
                break;
            }
        }
        if !improved {
            return Err(StepError::NoDecrease);
        }
    }
    Err(StepError::IterationBudget)
}
