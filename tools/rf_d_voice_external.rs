//! AC-coupled external preamp, overload detector and its passive BUS branch.
use super::oscillator::smooth_mix;

const INPUT_VOLTS_PER_FS: f64 = 0.1;
const PREAMP_GAIN: f64 = 1. + 200e3 / 1e3;
const PREAMP_SWING_V: f64 = 4.;
const OSCILLATOR_REFERENCE_V: f64 = 1.7;
const INPUT_TAU_S: f64 = (1e3 + 100e3) * 0.1e-6;
const OUTPUT_TAU_S: f64 = 33e3 * 1e-6;
const OVERLOAD_TAU_S: f64 = 100e3 * 0.47e-6;

#[derive(Clone, Copy, Default)]
pub struct Controls {
    pub enabled: bool,
    pub level: f64,
    pub input: f64,
}

impl Controls {
    pub fn valid(self) -> bool {
        (0. ..=1.).contains(&self.level) && (-1. ..=1.).contains(&self.input)
    }
}

#[derive(Clone)]
pub struct Preamp {
    previous: f64,
    coupling: [f64; 2],
    steps: [f64; 2],
    overload: f64,
    overload_release: f64,
    mix: Option<[f64; 2]>,
    ramp: f64,
}

impl Preamp {
    pub fn new(rate: f64, factor: usize) -> Self {
        Self {
            previous: 0.,
            coupling: [0.; 2],
            steps: [INPUT_TAU_S, OUTPUT_TAU_S].map(|tau| -(-1. / (rate * tau)).exp_m1()),
            overload: 0.,
            overload_release: (-1. / (rate * OVERLOAD_TAU_S)).exp(),
            mix: None,
            ramp: 1. / (64. * factor as f64),
        }
    }

    pub fn tick(
        &mut self,
        controls: Controls,
        fraction: f64,
        #[cfg(pilot_voice_feedback)] feedback: [f64; 2],
    ) -> [f64; 2] {
        let input = self.previous + fraction * (controls.input - self.previous);
        if fraction == 1. {
            self.previous = controls.input;
        }
        let [connection, level] = smooth_mix(
            &mut self.mix,
            [f64::from(controls.enabled), controls.level],
            self.ramp,
        );
        let input_v = INPUT_VOLTS_PER_FS * level * input;
        #[cfg(pilot_voice_feedback)]
        let input_v = input_v * (1. - feedback[1]) + level * feedback[1] * feedback[0];
        self.coupling[0] += self.steps[0] * (input_v - self.coupling[0]);
        let drive = PREAMP_GAIN * (input_v - self.coupling[0]);
        let limited = PREAMP_SWING_V * (drive / PREAMP_SWING_V).tanh();
        self.coupling[1] += self.steps[1] * (limited - self.coupling[1]);
        let output = limited - self.coupling[1];
        let detected = f64::from(drive.abs() >= PREAMP_SWING_V);
        self.overload = detected.max(self.overload * self.overload_release);
        [connection * output / OSCILLATOR_REFERENCE_V, connection]
    }

    pub fn overload(&self) -> f64 {
        self.overload
    }
}
