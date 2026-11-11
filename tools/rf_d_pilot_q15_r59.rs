//! Q15 charge at a fixed clock with an endpoint closure through CR6 and R59.
use crate::{
    fast_r59,
    latch_charge::terminal,
    q15,
    reduced_lu::{maximum, Lu},
    StepError,
};

const RATE_HZ: f64 = 96_000.;
const CURRENT_TOLERANCE_A: f64 = 2e-15;
const CORRECTION_TOLERANCE_V: f64 = 2e-12;

#[derive(Clone, Copy)]
pub struct State {
    pub audio: fast_r59::State,
    pub q15_v: [f64; 2],
    pub previous_charge_increment_c: Option<[f64; 2]>,
    #[cfg(pilot_r59_predict_q15_charge)]
    pub charge_mass_f: Option<[[f64; 2]; 2]>,
}

pub struct Frame {
    pub audio: fast_r59::Frame,
    pub charge_increment_c: [f64; 2],
    pub residual_a: [f64; 2],
    pub trials: usize,
    pub receiver_iterations: usize,
}

#[derive(Default)]
struct Work {
    trials: usize,
    receiver_iterations: usize,
}

#[derive(Debug)]
pub enum Error {
    Audio(fast_r59::Error),
    Q15(StepError),
}

struct Trial {
    state: State,
    audio: fast_r59::Frame,
    charge_increment_c: [f64; 2],
    residual_a: [f64; 2],
    jacobian: [[f64; 2]; 2],
}

struct TerminalCharge {
    increment_c: [f64; 2],
    mass_f: [[f64; 2]; 2],
}

fn equation(
    old: State,
    q15_v: [f64; 2],
    drive: q15::Drive,
    cr6: [f64; 2],
    #[cfg(pilot_r59_predict_q15_charge)] seed_mass_f: Option<[[f64; 2]; 2]>,
) -> Result<(TerminalCharge, [f64; 2], [[f64; 2]; 2]), StepError> {
    let (current, dc_jacobian) = q15::conduction(q15_v, drive, cr6[0], cr6[1])?;
    let exact = || terminal(old.q15_v.map(|v| (v, 0.)), q15_v.map(|v| (v, 0.)));
    #[cfg(pilot_r59_predict_q15_charge)]
    let (increment_c, mass_f) = match seed_mass_f {
        Some(mass) => {
            let delta = [q15_v[0] - old.q15_v[0], q15_v[1] - old.q15_v[1]];
            let increment = mass.map(|row| row[0] * delta[0] + row[1] * delta[1]);
            (increment, mass)
        }
        None => exact()?,
    };
    #[cfg(not(pilot_r59_predict_q15_charge))]
    let (increment_c, mass_f) = exact()?;
    let (weight, history) = match old.previous_charge_increment_c {
        Some(previous) => (1.5 * RATE_HZ, previous.map(|q| -0.5 * RATE_HZ * q)),
        None => (RATE_HZ, [0.; 2]),
    };
    let residual_a = std::array::from_fn(|k| current[k] + weight * increment_c[k] + history[k]);
    let jacobian = std::array::from_fn(|row| {
        std::array::from_fn(|col| dc_jacobian[row][col] + weight * mass_f[row][col])
    });
    Ok((TerminalCharge { increment_c, mass_f }, residual_a, jacobian))
}

fn direction(residual: [f64; 2], jacobian: [[f64; 2]; 2]) -> Result<[f64; 2], StepError> {
    Lu::factor(jacobian)?.solve(residual)
}

#[cfg(pilot_r59_predict_q15)]
fn predict(
    old: State,
    [signal, c2, filter, q25_base, q25_collector, cr8_anode]: [f64; 6],
) -> Option<[f64; 2]> {
    let [reset_at_old_cathode, slope] = fast_r59::predict_reset(old.audio, [signal, c2, filter])?;
    let drive = q15::Drive {
        c2,
        vca_base: old.audio.vca_base,
        q25_base,
        q25_collector,
        cr8_anode,
    };
    let mut q15_v = old.q15_v;
    #[cfg(pilot_r59_predict_q15_charge)]
    let mut seed_mass_f = old.charge_mass_f;
    #[cfg(pilot_r59_predict_q15_cr6)]
    let (mut reset, shunt, target_current) = {
        let (current, conductance) =
            crate::contour_ports::germanium(old.audio.volume[4] - old.q15_v[0]).ok()?;
        // The reset response to the cathode is g_CR6 / (shunt + g_CR6).
        let total = conductance / slope;
        let shunt = total - conductance;
        if !shunt.is_finite() || shunt <= 0. {
            return None;
        }
        let target_current = current + total * (reset_at_old_cathode - old.audio.volume[4]);
        (reset_at_old_cathode, shunt, target_current)
    };
    for _ in 0..6 {
        #[cfg(not(pilot_r59_predict_q15_cr6))]
        let reset = reset_at_old_cathode + slope * (q15_v[0] - old.q15_v[0]);
        let (current, conductance) = crate::contour_ports::germanium(reset - q15_v[0]).ok()?;
        #[cfg(not(pilot_r59_predict_q15_cr6))]
        let (correction, error, max_correction) = {
            let (_, residual, jacobian) = equation(
                old,
                q15_v,
                drive,
                [current, conductance * (slope - 1.)],
                #[cfg(pilot_r59_predict_q15_charge)]
                seed_mass_f,
            )
            .ok()?;
            let correction = direction(residual, jacobian).ok()?;
            (correction, maximum(&residual), maximum(&correction))
        };
        #[cfg(pilot_r59_predict_q15_cr6)]
        let (correction, error, max_correction) = {
            let (_, mut residual, mut jacobian) = equation(
                old,
                q15_v,
                drive,
                [current, -conductance],
                #[cfg(pilot_r59_predict_q15_charge)]
                seed_mass_f,
            )
            .ok()?;
            let reset_residual = shunt * (reset - old.audio.volume[4]) + current - target_current;
            let error = maximum(&residual).max(reset_residual.abs());
            let reset_diagonal = shunt + conductance;
            let coupling = conductance / reset_diagonal;
            // Eliminate the reset row and restore its correction afterward.
            residual[0] += coupling * reset_residual;
            jacobian[0][0] -= coupling * conductance;
            let correction = direction(residual, jacobian).ok()?;
            let reset_correction = (reset_residual + conductance * correction[0]) / reset_diagonal;
            if !reset_correction.is_finite() {
                return None;
            }
            reset -= reset_correction;
            (
                correction,
                error,
                maximum(&correction).max(reset_correction.abs()),
            )
        };
        if error <= CURRENT_TOLERANCE_A && max_correction <= CORRECTION_TOLERANCE_V {
            #[cfg(pilot_r59_predict_q15_charge)]
            if seed_mass_f.take().is_some() {
                // Check the provisional root with the exact terminal law before using it.
                continue;
            }
            return Some(q15_v);
        }
        q15_v = std::array::from_fn(|i| q15_v[i] - correction[i]);
    }
    None
}

fn evaluate(
    old: State,
    q15_v: [f64; 2],
    [signal, c2, filter, q25_base, q25_collector, cr8_anode]: [f64; 6],
    refresh: bool,
    work: &mut Work,
    #[cfg(pilot_r59_q15_retry)] prior: Option<&Trial>,
    #[cfg(pilot_r59_profile)] profile: &mut fast_r59::Profile,
) -> Result<Trial, Error> {
    let audio_drive = [signal, c2, q15_v[0], filter];
    #[cfg(pilot_r59_q15_retry)]
    let warm = prior.and_then(|trial| {
        work.trials += 1;
        fast_r59::advance_from_trial(
            old.audio,
            audio_drive,
            refresh,
            trial.state.audio,
            &trial.audio.receiver_root,
            #[cfg(pilot_r59_profile)]
            profile,
        )
        .ok()
    });
    #[cfg(not(pilot_r59_q15_retry))]
    let warm = None;
    let (audio, frame) = warm
        .map_or_else(
            || {
                work.trials += 1;
                fast_r59::advance(
                    old.audio,
                    audio_drive,
                    refresh,
                    #[cfg(pilot_r59_profile)]
                    profile,
                )
            },
            Ok,
        )
        .map_err(Error::Audio)?;
    work.receiver_iterations += frame.iterations;
    let drive = q15::Drive {
        c2,
        vca_base: frame.ports.loads_v[0],
        q25_base,
        q25_collector,
        cr8_anode,
    };
    let (charge, residual_a, jacobian) = equation(
        old,
        q15_v,
        drive,
        [
            frame.reset_port.current_a,
            frame.reset_port.derivative_a_per_v[1],
        ],
        #[cfg(pilot_r59_predict_q15_charge)]
        None,
    )
    .map_err(Error::Q15)?;
    Ok(Trial {
        state: State {
            audio,
            q15_v,
            previous_charge_increment_c: Some(charge.increment_c),
            #[cfg(pilot_r59_predict_q15_charge)]
            charge_mass_f: Some(charge.mass_f),
        },
        audio: frame,
        charge_increment_c: charge.increment_c,
        residual_a,
        jacobian,
    })
}

pub fn advance(
    old: State,
    drive: [f64; 6],
    refresh: bool,
    #[cfg(pilot_r59_profile)] profile: &mut fast_r59::Profile,
) -> Result<(State, Frame), Error> {
    let mut work = Work::default();
    #[cfg(pilot_r59_predict_q15)]
    if let Some(seed) = fast_r59::measure!(profile, 8, predict(old, drive)) {
        if let Ok(result) = solve(
            old,
            drive,
            refresh,
            seed,
            &mut work,
            #[cfg(pilot_r59_profile)]
            profile,
        ) {
            return Ok(result);
        }
    }
    solve(
        old,
        drive,
        refresh,
        old.q15_v,
        &mut work,
        #[cfg(pilot_r59_profile)]
        profile,
    )
}

fn solve(
    old: State,
    drive: [f64; 6],
    refresh: bool,
    seed: [f64; 2],
    work: &mut Work,
    #[cfg(pilot_r59_profile)] profile: &mut fast_r59::Profile,
) -> Result<(State, Frame), Error> {
    let mut trial = evaluate(
        old,
        seed,
        drive,
        refresh,
        work,
        #[cfg(pilot_r59_q15_retry)]
        None,
        #[cfg(pilot_r59_profile)]
        profile,
    )?;
    for _ in 0..16 {
        let error = maximum(&trial.residual_a);
        let direction = direction(trial.residual_a, trial.jacobian).map_err(Error::Q15)?;
        if error <= CURRENT_TOLERANCE_A && maximum(&direction) <= CORRECTION_TOLERANCE_V {
            return Ok((
                trial.state,
                Frame {
                    audio: trial.audio,
                    charge_increment_c: trial.charge_increment_c,
                    residual_a: trial.residual_a,
                    trials: work.trials,
                    receiver_iterations: work.receiver_iterations,
                },
            ));
        }
        let mut accepted = None;
        for half in 0..12 {
            let scale = 0.5_f64.powi(half);
            let q15_v = std::array::from_fn(|i| trial.state.q15_v[i] - scale * direction[i]);
            if let Ok(candidate) = evaluate(
                old,
                q15_v,
                drive,
                refresh,
                work,
                #[cfg(pilot_r59_q15_retry)]
                Some(&trial),
                #[cfg(pilot_r59_profile)]
                profile,
            ) {
                if maximum(&candidate.residual_a) < error {
                    accepted = Some(candidate);
                    break;
                }
            }
        }
        trial = accepted.ok_or(Error::Q15(StepError::NoDecrease))?;
    }
    Err(Error::Q15(StepError::IterationBudget))
}
