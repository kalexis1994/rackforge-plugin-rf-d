//! Close the board-2 follower against the fast receiver at a common endpoint.
#[cfg(pilot_r59_schur_follower)]
use crate::contour_ports::close_r59_volume as close_volume;
#[cfg(not(pilot_r59_schur_follower))]
use crate::contour_ports::close_volume;
use crate::{plant, return_maps as map, StepError};

const R59: f64 = 68_000.;
const CLOSURE_V: f64 = 1e-10;

#[derive(Clone, Copy)]
pub struct State {
    pub audio: plant::State,
    pub volume: [f64; 5], // Q3 base, Q2 base, loudness, collector, reset return.
    pub vca_base: f64,
    pub gradient: Option<f64>,
    #[cfg(pilot_r59_predict_follower)]
    pub follower: Option<FollowerSeed>,
}

#[cfg(pilot_r59_predict_follower)]
#[derive(Clone, Copy)]
pub struct FollowerSeed {
    c2: f64,
    cathode: f64,
    c2_response: [f64; 5],
    base_response: [f64; 5],
    #[cfg(pilot_r59_predict_cathode)]
    cathode_response: [f64; 5],
}

#[cfg(pilot_r59_predict_follower)]
impl FollowerSeed {
    fn predict(self, volume: [f64; 5], c2: f64, cathode: f64) -> Option<([f64; 5], [f64; 5])> {
        #[cfg(not(pilot_r59_predict_cathode))]
        if self.cathode != cathode {
            return None;
        }
        let predicted = std::array::from_fn(|i| {
            let voltage = volume[i] + (c2 - self.c2) * self.c2_response[i];
            #[cfg(pilot_r59_predict_cathode)]
            if cathode != self.cathode {
                return voltage + (cathode - self.cathode) * self.cathode_response[i];
            }
            voltage
        });
        Some((predicted, self.base_response))
    }
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
    pub reused_root_evaluations: usize,
    pub follower_fallbacks: usize,
    pub prediction_fallbacks: usize,
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
    drive: [f64; 4],
    refresh: bool,
    #[cfg(pilot_r59_profile)] profile: &mut Profile,
) -> Result<(State, Frame), Error> {
    #[cfg(pilot_r59_predict_follower)]
    if let Some(prediction) = old
        .follower
        .and_then(|seed| seed.predict(old.volume, drive[1], drive[2]))
    {
        if let Ok(result) = advance_inner(
            old,
            drive,
            refresh,
            Some(prediction),
            #[cfg(pilot_r59_profile)]
            profile,
        ) {
            return Ok(result);
        }
        #[cfg(pilot_r59_profile)]
        {
            profile.prediction_fallbacks += 1;
        }
    }
    advance_inner(
        old,
        drive,
        refresh,
        #[cfg(pilot_r59_predict_follower)]
        None,
        #[cfg(pilot_r59_profile)]
        profile,
    )
}

fn advance_inner(
    old: State,
    [signal, c2, cathode, filter]: [f64; 4],
    refresh: bool,
    #[cfg(pilot_r59_predict_follower)] prediction: Option<([f64; 5], [f64; 5])>,
    #[cfg(pilot_r59_profile)] profile: &mut Profile,
) -> Result<(State, Frame), Error> {
    let mut initial_follower = || {
        let (volume, factor) = measure!(
            profile,
            0,
            close_volume(old.volume, c2, cathode, old.vca_base)
        )
        .map_err(Error::Volume)?;
        #[cfg(all(pilot_r59_profile, pilot_r59_schur_follower))]
        {
            profile.follower_fallbacks +=
                usize::from(matches!(factor, crate::contour_ports::R59Factor::Full(_)));
        }
        let response = measure!(profile, 4, factor.solve([0., 0., 1. / R59, 0., 0.]))
            .map_err(Error::Volume)?;
        Ok::<_, Error>((volume, response))
    };
    #[cfg(pilot_r59_predict_follower)]
    let (mut volume, mut volume_response) = prediction.map_or_else(&mut initial_follower, Ok)?;
    #[cfg(not(pilot_r59_predict_follower))]
    let (mut volume, mut volume_response) = initial_follower()?;
    let mut volume_base = old.vca_base;
    let mut source = volume[2];
    let mut gradient = if refresh { None } else { old.gradient };
    let mut previous_error = f64::INFINITY;
    let mut tangent_calls = 0;
    let mut prior = None;
    let prepared = measure!(profile, 1, plant::Prepared::new(old.audio));
    for iteration in 1..=8 {
        let drive = plant::Drive {
            volume_delta_v: source - map::SPLIT_CENTER[0],
            filter_delta_v: filter - map::SPLIT_CENTER[1],
        };
        let refresh_tangent = gradient.is_none();
        let seed = if refresh_tangent {
            None
        } else {
            prior.as_ref()
        };
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
        #[cfg(pilot_r59_profile)]
        {
            profile.successful_root_evaluations += root.evaluations;
        }
        #[cfg(all(pilot_r59_profile, pilot_r59_reuse_law))]
        {
            profile.reused_root_evaluations += usize::from(root.reused_evaluation);
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
        let (next, factor) = measure!(profile, 3, close_volume(initial, c2, cathode, vca_base))
            .map_err(Error::Volume)?;
        #[cfg(all(pilot_r59_profile, pilot_r59_schur_follower))]
        {
            profile.follower_fallbacks +=
                usize::from(matches!(factor, crate::contour_ports::R59Factor::Full(_)));
        }
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
                #[cfg(pilot_r59_predict_follower)]
                follower: measure!(profile, 4, {
                    (|| {
                        let c2_response = factor
                            .solve([1. / crate::contour_ports::VOLUME_R16, 0., 0., 0., 0.])
                            .ok()?;
                        let base_response = factor.solve([0., 0., 1. / R59, 0., 0.]).ok()?;
                        #[cfg(pilot_r59_predict_cathode)]
                        let cathode_response = factor
                            .solve(crate::contour_ports::cathode_rhs(volume[4], cathode).ok()?)
                            .ok()?;
                        Some(FollowerSeed {
                            c2,
                            cathode,
                            c2_response,
                            base_response,
                            #[cfg(pilot_r59_predict_cathode)]
                            cathode_response,
                        })
                    })()
                }),
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
        prior = Some(root);
        source += residual / denominator;
    }
    Err(Error::Closure)
}
