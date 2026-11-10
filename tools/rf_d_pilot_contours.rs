//! Two-stage charge reduction of the nominal C2 and C5 branches.
use crate::{
    contour_ports::{self as ports, Returns},
    pilot_trigger::{self as latch, Boundary, State, CORE, N, PORTS},
    StepError,
};

pub const TIMER_NODES: [usize; 2] = [5, 38];
#[cfg(not(pilot_loaded_filter))]
pub const C5_PORTS: [usize; 4] = [44, 47, 30, 32];
const CAP_F: f64 = 10e-6;
// Decay switch on, with board R16 loading C2 through Q3.
const C2_G: [f64; 3] = [1. / 1000., 1. / 10_000., 1. / 10_000.];
const C5_G: [f64; 3] = [1. / 100., 1. / 1000., 1. / 10_000.];
const C2: usize = 1;
#[cfg(pilot_loaded_filter)]
const C5: usize = latch::pin(38) - N;
const X8: usize = 2;
const X11: usize = 5;
const _: () = assert!(PORTS[C2] == TIMER_NODES[0] && CORE[X8] == 8 && CORE[X11] == 11);

#[derive(Clone, Copy)]
pub struct Loaded {
    pub timers: [f64; 2],
    pub latch: State,
    pub returns: Returns,
    pub q22_base: f64,
}

#[derive(Clone, Copy)]
pub struct Ports {
    pub latch: Boundary,
    pub volume: [f64; 3],
    pub filter: [f64; 2],
    #[cfg(not(pilot_loaded_filter))]
    pub c5: [f64; 4],
}

fn radau(old: f64, ports: [[f64; 3]; 2], g: [f64; 3], h: f64) -> [f64; 2] {
    // Solve for increments at the same two stage times as the oracle.
    let y = ports.map(|stage| {
        g.into_iter()
            .zip(stage)
            .map(|(g, v)| g * (v - old))
            .sum::<f64>()
    });
    let load = g.into_iter().sum::<f64>() * h / CAP_F;
    let [a, d] = [1.5 + load, 2.5 + load];
    let scale = (h / CAP_F) / (a * d + 2.25);
    [
        old + scale * (d * y[0] - 0.5 * y[1]),
        old + scale * (4.5 * y[0] + a * y[1]),
    ]
}

pub fn step(
    old: Loaded,
    input: [Ports; 2],
    h: f64,
    previous: Boundary,
    previous_change: [f64; N],
) -> Result<[Loaded; 2], StepError> {
    step_with_budget(old, input, h, previous, previous_change, 3).map_err(|(_, error)| error)
}

pub fn step_with_budget(
    old: Loaded,
    input: [Ports; 2],
    h: f64,
    mut previous: Boundary,
    previous_change: [f64; N],
    budget: usize,
) -> Result<[Loaded; 2], (&'static str, StepError)> {
    previous.volts[C2] = old.timers[0];
    #[cfg(pilot_loaded_filter)]
    {
        previous.volts[C5] = old.timers[1];
    }
    let mut boundary = input.map(|p| p.latch);
    let mut c2 = radau(
        old.timers[0],
        std::array::from_fn(|i| {
            let at = [1. / 3., 1.][i];
            [
                old.latch.0[X8] + at * previous_change[X8],
                old.latch.0[X11] + at * previous_change[X11],
                old.returns.volume[0],
            ]
        }),
        C2_G,
        h,
    );
    #[cfg(not(pilot_loaded_filter))]
    let c5_load = |i: usize, _: State| [input[i].c5[0], input[i].c5[1]];
    #[cfg(pilot_loaded_filter)]
    let c5_load = |_: usize, stage: State| [stage.0[latch::pin(44)], stage.0[latch::pin(47)]];
    let mut c5 = radau(
        old.timers[1],
        std::array::from_fn(|i| {
            let [attack, decay] = c5_load(i, old.latch);
            [attack, decay, old.q22_base]
        }),
        C5_G,
        h,
    );
    let mut trial = [old; 2];
    // Bound the iteration over both capacitors and their endogenous loads.
    // Publish both stages only after the loaded timing voltages converge.
    for _ in 0..budget {
        for i in 0..2 {
            boundary[i].volts[C2] = c2[i];
            #[cfg(pilot_loaded_filter)]
            {
                boundary[i].volts[C5] = c5[i];
            }
            trial[i].returns.volume =
                ports::volume(trial[i].returns.volume, c2[i], input[i].volume)
                    .map_err(|error| ("C2 volume", error))?;
            #[cfg(not(pilot_loaded_filter))]
            {
                let [_, _, collector, emitter] = input[i].c5;
                trial[i].q22_base = ports::q22_base(trial[i].q22_base, c5[i], [collector, emitter])
                    .map_err(|error| ("C5 Q22", error))?;
            }
        }
        let stages = latch::step(old.latch, boundary, h, previous, previous_change)
            .map_err(|error| ("latch", error))?;
        #[cfg(pilot_loaded_filter)]
        for (trial, stage) in trial.iter_mut().zip(stages) {
            trial.q22_base = stage.0[latch::pin(29)];
        }
        let next_c2 = radau(
            old.timers[0],
            std::array::from_fn(|i| {
                [
                    stages[i].0[X8],
                    stages[i].0[X11],
                    trial[i].returns.volume[0],
                ]
            }),
            C2_G,
            h,
        );
        let next_c5 = radau(
            old.timers[1],
            std::array::from_fn(|i| {
                let [attack, decay] = c5_load(i, stages[i]);
                [attack, decay, trial[i].q22_base]
            }),
            C5_G,
            h,
        );
        let converged = (0..2)
            .all(|i| (next_c2[i] - c2[i]).abs() <= 2e-13 && (next_c5[i] - c5[i]).abs() <= 2e-13);
        if converged {
            for i in 0..2 {
                trial[i].timers = [next_c2[i], next_c5[i]];
                trial[i].latch = stages[i];
                #[cfg(not(pilot_loaded_filter))]
                {
                    trial[i].returns.filter = ports::filter(old.returns.filter, input[i].filter)
                        .map_err(|error| ("C5 filter", error))?;
                }
                #[cfg(pilot_loaded_filter)]
                {
                    trial[i].returns.filter =
                        ports::FILTER_NODES.map(|k| stages[i].0[latch::pin(k)]);
                }
            }
            return Ok(trial);
        }
        c2 = next_c2;
        c5 = next_c5;
    }
    Err(("C2/C5 timer", StepError::IterationBudget))
}
