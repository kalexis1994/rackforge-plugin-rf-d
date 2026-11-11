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

#[cfg(pilot_r59_profile)]
#[derive(Default)]
pub struct Profile {
    pub stages: [(u64, u128); 7],
    pub successful_root_evaluations: usize,
}

macro_rules! measure {
    ($profile:ident, $stage:literal, $work:expr) => {{
        #[cfg(pilot_r59_profile)]
        let begin = std::time::Instant::now();
        let result = $work;
        #[cfg(pilot_r59_profile)]
        {
            let elapsed = begin.elapsed().as_nanos();
            let (calls, total) = &mut $profile.stages[$stage];
            *calls += 1;
            *total += elapsed;
        }
        result
    }};
}

pub fn advance(
    old: State,
    [signal, c2, cathode, filter]: [f64; 4],
    refresh: bool,
    #[cfg(pilot_r59_profile)] profile: &mut Profile,
) -> Result<(State, Frame), Error> {
    let (mut volume, factor) = measure!(
        profile,
        0,
        contour_ports::close_volume(old.volume, c2, cathode, old.vca_base)
    )
    .map_err(Error::Volume)?;
    let mut volume_response =
        measure!(profile, 4, factor.solve([0., 0., 1. / R59, 0., 0.])).map_err(Error::Volume)?;
    let mut volume_base = old.vca_base;
    let mut source = volume[2];
    let mut gradient = if refresh { None } else { old.gradient };
    let mut previous_error = f64::INFINITY;
    let mut tangent_calls = 0;
    let mut retry_seed = None;
    let prepared = measure!(profile, 1, plant::Prepared::new(old.audio));
    for iteration in 1..=8 {
        let drive = plant::Drive {
            volume_delta_v: source - map::SPLIT_CENTER[0],
            filter_delta_v: filter - map::SPLIT_CENTER[1],
        };
        let refresh_tangent = gradient.is_none();
        let seed = if refresh_tangent { None } else { retry_seed };
        let root = measure!(
            profile,
            2,
            prepared.solve_root(signal, drive, seed).or_else(|error| {
                if seed.is_some() {
                    prepared.solve_root(signal, drive, None)
                } else {
                    Err(error)
                }
            })
        )
        .map_err(Error::Audio)?;
        retry_seed = Some(root.retry_seed());
        #[cfg(pilot_r59_profile)]
        {
            profile.successful_root_evaluations += root.evaluations;
        }
        #[cfg(pilot_r59_eager)]
        let completed = measure!(profile, 6, root.finish()).map_err(Error::Audio)?;
        if refresh_tangent {
            gradient =
                Some(measure!(profile, 5, root.load_jacobian()).map_err(Error::Audio)?[0][0]);
            tangent_calls += 1;
        }
        #[cfg(pilot_r59_eager)]
        let vca_base = completed.1.loads_v[0];
        #[cfg(not(pilot_r59_eager))]
        let vca_base = root.vca_base().map_err(Error::Audio)?;
        // The tangent supplies a seed. close_volume checks every original row again.
        let initial =
            std::array::from_fn(|k| volume[k] + volume_response[k] * (vca_base - volume_base));
        let (next, factor) = measure!(
            profile,
            3,
            contour_ports::close_volume(initial, c2, cathode, vca_base)
        )
        .map_err(Error::Volume)?;
        volume = next;
        volume_base = vca_base;
        let residual = volume[2] - source;
        let error = residual.abs();
        let mismatch_a =
            ((volume[2] - vca_base) / R59 - (root.r59_source_v() - vca_base) / R59).abs();
        if error <= CLOSURE_V && mismatch_a <= 2e-12 {
            #[cfg(not(pilot_r59_eager))]
            let completed = measure!(profile, 6, root.finish()).map_err(Error::Audio)?;
            let (candidate, ports) = completed;
            let mismatch_a = ((volume[2] - ports.loads_v[0]) / R59 - ports.returns_a[0]).abs();
            if mismatch_a > 2e-12 {
                return Err(Error::Closure);
            }
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
        volume_response = measure!(profile, 4, factor.solve([0., 0., 1. / R59, 0., 0.]))
            .map_err(Error::Volume)?;
        let slope = volume_response[2];
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
