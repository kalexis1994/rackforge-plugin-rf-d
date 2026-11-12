//! Three free-running oscillators for the reduced playable voice.
use crate::oscillator_tables::{HARMONICS, SAMPLES, WAVES};

const AUDIO_BAND_HZ: f64 = 20_000.;
const OCTAVES: [f64; 6] = [-6., -2., -1., 0., 1., 2.];
const FREE_OSC3_HZ: f64 = 220.;
const MIX_RAMP_FRAMES: f64 = 64.;

pub(super) fn smooth_mix(state: &mut Option<[f64; 2]>, target: [f64; 2], ramp: f64) -> [f64; 2] {
    let mix = state.get_or_insert(target);
    for (value, target) in mix.iter_mut().zip(target) {
        *value += (target - *value).clamp(-ramp, ramp);
    }
    *mix
}

#[derive(Clone, Copy)]
pub struct Settings {
    pub range: usize,
    pub shape: usize,
    pub semitones: f64,
    pub level: f64,
    pub enabled: bool,
}

#[derive(Clone, Copy)]
pub struct Panel {
    pub oscillators: [Settings; 3],
    pub tune_cents: f64,
    pub osc3_tracking: bool,
}

impl Default for Panel {
    fn default() -> Self {
        let oscillator = Settings {
            range: 3,
            shape: 2,
            semitones: 0.,
            level: 1.,
            enabled: true,
        };
        Self {
            oscillators: [
                oscillator,
                Settings {
                    enabled: false,
                    level: 0.65,
                    ..oscillator
                },
                Settings {
                    enabled: false,
                    level: 0.55,
                    ..oscillator
                },
            ],
            tune_cents: 0.,
            osc3_tracking: true,
        }
    }
}

impl Panel {
    pub fn valid(self) -> bool {
        (-100. ..=100.).contains(&self.tune_cents)
            && self.oscillators.iter().all(|osc| {
                osc.range < OCTAVES.len()
                    && osc.shape < WAVES.len()
                    && (-9. ..=9.).contains(&osc.semitones)
                    && (0. ..=1.).contains(&osc.level)
            })
    }
}

#[derive(Clone, Copy, Default)]
struct Oscillator {
    phase: f64,
    last_pitch: Option<(f64, f64)>,
    increment: f64,
    band: usize,
    blend: f64,
    // Fraction of the mixer switch and level after dezippering.
    mix: Option<[f64; 2]>,
}

impl Oscillator {
    fn update_pitch(&mut self, base_hz: f64, octaves: f64, rate: f64) {
        if self.last_pitch == Some((base_hz, octaves)) {
            return;
        }
        self.last_pitch = Some((base_hz, octaves));
        let frequency = base_hz * octaves.exp2();
        self.increment = frequency / rate;
        self.band = HARMONICS
            .iter()
            .position(|&count| frequency * f64::from(count) <= AUDIO_BAND_HZ)
            .unwrap_or(HARMONICS.len() - 1);
        self.blend = if self.band + 1 == HARMONICS.len() {
            0.
        } else {
            let fraction = frequency * f64::from(HARMONICS[self.band]) / AUDIO_BAND_HZ;
            ((fraction - 0.8) * 5.).clamp(0., 1.)
        };
    }

    fn wave(&self, shape: usize, reverse: bool) -> f64 {
        let phase = if reverse { 1. - self.phase } else { self.phase };
        let position = phase * SAMPLES as f64;
        let index = position as usize;
        let fraction = position.fract();
        let interpolate = |band| {
            let table: &[f32; SAMPLES] = &WAVES[shape][band];
            let left = f64::from(table[index % SAMPLES]);
            let right = f64::from(table[(index + 1) % SAMPLES]);
            left + fraction * (right - left)
        };
        let sample = interpolate(self.band);
        if self.blend == 0. {
            sample
        } else {
            sample + self.blend * (interpolate(self.band + 1) - sample)
        }
    }

    fn step(
        &mut self,
        settings: Settings,
        index: usize,
        base_hz: f64,
        panel: Panel,
        rate: f64,
        ramp: f64,
        #[cfg(pilot_voice_modulation)] pitch_offset: f64,
        #[cfg(pilot_voice_performance)] bend: f64,
    ) -> (f64, f64, f64) {
        let free = index == 2 && !panel.osc3_tracking;
        let base_hz = if free { FREE_OSC3_HZ } else { base_hz };
        let semitones = if free {
            settings.semitones * 4.
        } else {
            settings.semitones
        };
        let octaves = OCTAVES[settings.range] + (semitones + panel.tune_cents * 0.01) / 12.;
        #[cfg(pilot_voice_modulation)]
        let octaves = octaves + pitch_offset;
        #[cfg(pilot_voice_performance)]
        let octaves = if free { octaves } else { octaves + bend };
        self.update_pitch(base_hz, octaves, rate);
        self.phase += self.increment;
        if self.phase >= 1. {
            self.phase -= 1.;
        }

        let target = [f64::from(settings.enabled), settings.level];
        let [connection, level] = smooth_mix(&mut self.mix, target, ramp);
        let gain = connection * level;
        let raw = if gain != 0. || (cfg!(pilot_voice_modulation) && index == 2) {
            let reverse = index == 2 && settings.shape == 1;
            let shape = if reverse { 2 } else { settings.shape };
            self.wave(shape, reverse)
        } else {
            0.
        };
        (gain * raw, connection, raw)
    }
}

#[derive(Clone)]
pub struct Bank {
    oscillators: [Oscillator; 3],
    rate: f64,
    ramp: f64,
    #[cfg(pilot_voice_modulation)]
    osc3: f64,
}

impl Bank {
    pub fn new(rate: f64, factor: usize) -> Self {
        Self {
            oscillators: [
                Oscillator::default(),
                Oscillator {
                    phase: 1. / 3.,
                    ..Oscillator::default()
                },
                Oscillator {
                    phase: 2. / 3.,
                    ..Oscillator::default()
                },
            ],
            rate,
            ramp: 1. / (MIX_RAMP_FRAMES * factor as f64),
            #[cfg(pilot_voice_modulation)]
            osc3: 0.,
        }
    }

    #[cfg(pilot_voice_modulation)]
    pub fn osc3(&self) -> f64 {
        self.osc3
    }

    pub fn sample(
        &mut self,
        panel: Panel,
        base_increment: f64,
        #[cfg(pilot_voice_modulation)] noise: [f64; 2],
        #[cfg(pilot_voice_modulation)] pitch_offset: f64,
        #[cfg(pilot_voice_performance)] bend: f64,
    ) -> f64 {
        let base_hz = base_increment * self.rate;
        let mut sum = 0.;
        let mut connections = 0.;
        for (index, (oscillator, settings)) in self
            .oscillators
            .iter_mut()
            .zip(panel.oscillators)
            .enumerate()
        {
            let (signal, connection, _raw) = oscillator.step(
                settings,
                index,
                base_hz,
                panel,
                self.rate,
                self.ramp,
                #[cfg(pilot_voice_modulation)]
                pitch_offset,
                #[cfg(pilot_voice_performance)]
                bend,
            );
            sum += signal;
            connections += connection;
            #[cfg(pilot_voice_modulation)]
            if index == 2 {
                self.osc3 = _raw;
            }
        }
        #[cfg(pilot_voice_modulation)]
        {
            sum += noise[0];
            connections += noise[1];
        }
        // Equal 33 kΩ oscillator branches. A zeroed connected source still loads BUS.
        sum / connections.max(1.)
    }
}
