//! Noise sources, the weighted mixer branch and the performance modulation wheel.
use super::oscillator::smooth_mix;

const NOISE_SEED: u32 = 0x2c67_8f11;
const PINK_HZ: [f64; 6] = [16., 64., 256., 1024., 4096., 16384.];
const PINK_WEIGHTS: [f64; 6] = [1., 0.5, 0.25, 0.125, 0.0625, 0.03125];
const RED_TAU_S: [f64; 2] = [2.2e6 * 0.15e-6, 2.2e6 * 0.10e-6];
const RAMP_FRAMES: f64 = 64.;
const NOISE_CONDUCTANCE: f64 = 3.;

pub const PITCH_OCTAVES: f64 = 2. / 12.;
pub const FILTER_OCTAVES: f64 = 2.;

#[derive(Clone, Copy, Default)]
pub struct Controls {
    pub noise_pink: bool,
    pub noise_enabled: bool,
    pub noise_level: f64,
    pub mix: f64,
    pub oscillator: bool,
    pub filter: bool,
}

impl Controls {
    pub fn valid(self) -> bool {
        (0. ..=1.).contains(&self.noise_level) && (0. ..=1.).contains(&self.mix)
    }
}

#[derive(Clone)]
pub struct Noise {
    rng: u32,
    pink_state: [f64; PINK_HZ.len()],
    pink_steps: [f64; PINK_HZ.len()],
    red_state: [f64; RED_TAU_S.len()],
    red_steps: [f64; RED_TAU_S.len()],
}

impl Noise {
    pub fn new(rate: f64) -> Self {
        Self {
            rng: NOISE_SEED,
            pink_state: [0.; PINK_HZ.len()],
            pink_steps: PINK_HZ.map(|hz| -(-std::f64::consts::TAU * hz / rate).exp_m1()),
            red_state: [0.; RED_TAU_S.len()],
            red_steps: RED_TAU_S.map(|seconds| -(-1. / (rate * seconds)).exp_m1()),
        }
    }

    pub fn step(&mut self) -> [f64; 3] {
        self.rng ^= self.rng << 13;
        self.rng ^= self.rng >> 17;
        self.rng ^= self.rng << 5;
        let white = f64::from(self.rng) * (2. / 4294967296.) - 1.;
        let mut pink = 0.;
        for ((state, step), weight) in self
            .pink_state
            .iter_mut()
            .zip(self.pink_steps)
            .zip(PINK_WEIGHTS)
        {
            *state += step * (white - *state);
            pink += weight * *state;
        }
        let mut red = pink;
        for (state, step) in self.red_state.iter_mut().zip(self.red_steps) {
            *state += step * (red - *state);
            red = *state;
        }
        [
            white,
            (4. * pink).clamp(-1., 1.),
            (55. * red).clamp(-1., 1.),
        ]
    }
}

#[derive(Clone)]
pub struct Sources {
    noise: Noise,
    mixer: Option<[f64; 2]>,
    wheel: f64,
    wheel_target: f64,
    ramp: f64,
}

impl Sources {
    pub fn new(rate: f64, factor: usize) -> Self {
        Self {
            noise: Noise::new(rate),
            mixer: None,
            wheel: 0.,
            wheel_target: 0.,
            ramp: 1. / (RAMP_FRAMES * factor as f64),
        }
    }

    pub fn set_wheel(&mut self, value: u8) {
        self.wheel_target = f64::from(value) / 127.;
    }

    pub fn step(&mut self, controls: Controls, osc3: f64) -> ([f64; 2], f64) {
        let [white, pink, red] = self.noise.step();
        let [audio_noise, modulation_noise] = if controls.noise_pink {
            [pink, pink]
        } else {
            [white, red]
        };
        let [connection, level] = smooth_mix(
            &mut self.mixer,
            [f64::from(controls.noise_enabled), controls.noise_level],
            self.ramp,
        );
        let weight = NOISE_CONDUCTANCE * connection;
        self.wheel += (self.wheel_target - self.wheel).clamp(-self.ramp, self.ramp);
        let control = self.wheel * ((1. - controls.mix) * osc3 + controls.mix * modulation_noise);
        ([weight * level * audio_noise, weight], control)
    }
}
