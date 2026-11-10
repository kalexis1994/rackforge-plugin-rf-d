//! Close the board-2 follower against the fast receiver at a common endpoint.
use crate::{contour_ports, plant, return_maps as map, StepError};

const R59: f64 = 68_000.;
const CLOSURE_V: f64 = 1e-10;

#[derive(Clone, Copy)]
pub struct State {
    pub audio: plant::State,
    pub volume: [f64; 5], // Q3 base, Q2 base, loudness, collector, reset return.
    pub vca_base: f64,
    pub gradient: Option<f64>,
}

pub struct Frame {
    pub ports: plant::Ports,
    pub volume: [f64; 5],
    pub iterations: usize,
    pub mismatch_v: f64,
    pub mismatch_a: f64,
    pub tangent_calls: usize,
}

#[derive(Debug)]
pub enum Error {
    Audio(plant::Error),
    Volume(StepError),
    Closure,
}

pub fn advance(
    old: State,
    [signal, c2, cathode, filter]: [f64; 4],
    refresh: bool,
) -> Result<(State, Frame), Error> {
    let (mut volume, _) = contour_ports::close_volume(old.volume, c2, cathode, old.vca_base)
        .map_err(Error::Volume)?;
    let mut source = volume[2];
    let mut gradient = if refresh { None } else { old.gradient };
    let mut previous_error = f64::INFINITY;
    let mut tangent_calls = 0;
    for iteration in 1..=8 {
        let drive = plant::Drive {
            volume_delta_v: source - map::SPLIT_CENTER[0],
            filter_delta_v: filter - map::SPLIT_CENTER[1],
        };
        let (candidate, ports) = if gradient.is_none() {
            let trial =
                plant::trial_with_load_tangent(old.audio, signal, drive).map_err(Error::Audio)?;
            gradient = Some(trial.load_jacobian[0][0]);
            tangent_calls += 1;
            (trial.state, trial.ports)
        } else {
            let mut candidate = old.audio;
            let ports = plant::step(&mut candidate, signal, drive).map_err(Error::Audio)?;
            (candidate, ports)
        };
        let (next, factor) = contour_ports::close_volume(volume, c2, cathode, ports.loads_v[0])
            .map_err(Error::Volume)?;
        volume = next;
        let residual = volume[2] - source;
        let error = residual.abs();
        let mismatch_a = ((volume[2] - ports.loads_v[0]) / R59 - ports.returns_a[0]).abs();
        if error <= CLOSURE_V && mismatch_a <= 2e-12 {
            let state = State {
                audio: candidate,
                volume,
                vca_base: ports.loads_v[0],
                gradient,
            };
            return Ok((
                state,
                Frame {
                    ports,
                    volume,
                    iterations: iteration,
                    mismatch_v: error,
                    mismatch_a,
                    tangent_calls,
                },
            ));
        }
        let slope = factor
            .solve([0., 0., 1. / R59, 0., 0.])
            .map_err(Error::Volume)?[2];
        let denominator = 1. - slope * gradient.unwrap();
        if !denominator.is_finite() || denominator.abs() <= 1e-8 {
            return Err(Error::Closure);
        }
        if error >= previous_error * 0.5 {
            gradient = None;
        }
        previous_error = error;
        source += residual / denominator;
    }
    Err(Error::Closure)
}
