//! Reduced C2 and loaded R20 output network, with HI and LO taps.
const C2_F: f64 = 10e-6;
const R75_OHM: f64 = 1e3;
const R20_OHM: f64 = 5e3;
const R57_OHM: f64 = 33e3;
const R58_OHM: f64 = 1e3;
const R77_OHM: f64 = 1e3;
const R21_OHM: f64 = 5e3;
const R77_R21_OHM: f64 = R77_OHM + R21_OHM;
const LO_DIVIDER: f64 = R58_OHM / (R57_OHM + R58_OHM);
const FULL_CURSOR_OHM: f64 = parallel(R20_OHM, R57_OHM + R58_OHM);
const VCA_VOLTS_PER_FS: f64 = (R75_OHM + FULL_CURSOR_OHM) / FULL_CURSOR_OHM;

const fn parallel(left: f64, right: f64) -> f64 {
    left * right / (left + right)
}

#[derive(Clone, Copy)]
pub struct Controls {
    pub enabled: bool,
    pub low: bool,
    #[cfg(pilot_voice_monitor)]
    pub phones: bool,
    #[cfg(pilot_voice_monitor)]
    pub phones_level: f64,
    #[cfg(pilot_voice_monitor)]
    pub tuner: bool,
}

impl Default for Controls {
    fn default() -> Self {
        Self {
            enabled: true,
            low: false,
            #[cfg(pilot_voice_monitor)]
            phones: false,
            #[cfg(pilot_voice_monitor)]
            phones_level: 0.5,
            #[cfg(pilot_voice_monitor)]
            tuner: false,
        }
    }
}

#[derive(Clone)]
pub struct Stage {
    charge_v: f64,
    main: Option<f64>,
    #[cfg(not(pilot_voice_monitor))]
    selector: Option<f64>,
    last_controls: Option<(f64, f64)>,
    hi_gain: f64,
    coefficient: f64,
    rate: f64,
    switch_step: f64,
}

impl Stage {
    pub fn new(rate: f64, factor: usize) -> Self {
        Self {
            charge_v: 0.,
            main: None,
            #[cfg(not(pilot_voice_monitor))]
            selector: None,
            last_controls: None,
            hi_gain: 0.,
            coefficient: 0.,
            rate,
            switch_step: 1. / (64. * factor as f64),
        }
    }

    fn slew(state: &mut Option<f64>, target: f64, step: f64) -> f64 {
        let value = state.get_or_insert(target);
        *value += (target - *value).clamp(-step, step);
        *value
    }

    pub fn tick(&mut self, post_vca: f64, level: f64, enabled: bool) -> [f64; 3] {
        let connection = Self::slew(&mut self.main, f64::from(enabled), self.switch_step);
        if self.last_controls != Some((level, connection)) {
            let lower = level * R20_OHM;
            let cursor = parallel(lower, R57_OHM + R58_OHM);
            let off = R75_OHM + (R20_OHM - lower);
            let on = off + cursor;
            // Endpoints use the exact contact topology. In transit the host
            // crossfades the two conductances and the voltage at the jack.
            let conductance = connection / on + (1. - connection) / off + 1. / R77_R21_OHM;
            self.coefficient = -(-conductance / (C2_F * self.rate)).exp_m1();
            self.hi_gain = connection * cursor / on;
            self.last_controls = Some((level, connection));
        }
        let driver_v = VCA_VOLTS_PER_FS * post_vca;
        self.charge_v += self.coefficient * (driver_v - self.charge_v);
        let c2_right = driver_v - self.charge_v;
        let hi = c2_right * self.hi_gain;
        let excess = (hi.abs() - 0.8).max(0.);
        let hi = hi.signum() * (hi.abs().min(0.8) + 0.2 * excess / (0.2 + excess));
        [hi, hi * LO_DIVIDER, c2_right]
    }

    #[cfg(not(pilot_voice_monitor))]
    pub fn monitor(&mut self, hi: f64, low: bool) -> f64 {
        let mix = Self::slew(&mut self.selector, f64::from(low), 1. / 64.);
        hi.clamp(-1., 1.) * ((1. - mix) + mix * LO_DIVIDER)
    }
}

#[cfg(pilot_voice_monitor)]
const C19_F: f64 = 2.5e-6;
// Real parts of the board-3 AC reduction at 1 kHz. See SALIDA_TOCABLE.md.
#[cfg(pilot_voice_monitor)]
const AMP_INPUT_OHM: f64 = 4802.81;
#[cfg(pilot_voice_monitor)]
const C21_F: f64 = 400e-6;
#[cfg(pilot_voice_monitor)]
const J7_LOAD_OHM: f64 = parallel(390., 16.);
#[cfg(pilot_voice_monitor)]
const AMP_OUTPUT_OHM: f64 = 210.47218;
#[cfg(pilot_voice_monitor)]
const AMP_OPEN_GAIN: f64 = 0.98929334;
#[cfg(pilot_voice_monitor)]
const AMP_LOADED_GAIN: f64 = AMP_OPEN_GAIN * J7_LOAD_OHM / (AMP_OUTPUT_OHM + J7_LOAD_OHM);
#[cfg(pilot_voice_monitor)]
const REFERENCE_HZ: f64 = 440.;
#[cfg(pilot_voice_monitor)]
const REFERENCE_PEAK: f64 = 0.1;

#[cfg(pilot_voice_monitor)]
#[derive(Clone)]
pub struct Monitor {
    low_mix: Option<f64>,
    phones_mix: Option<f64>,
    level: Option<f64>,
    last_level: Option<f64>,
    c19_charge: f64,
    c19_coefficient: f64,
    c19_gain: f64,
    c21_charge: f64,
    c21_coefficient: f64,
    tuner_mix: Option<f64>,
    phase: f64,
    increment: f64,
    rate: f64,
    step: f64,
}

#[cfg(pilot_voice_monitor)]
impl Monitor {
    pub fn new(rate: f64, factor: usize) -> Self {
        Self {
            low_mix: None,
            phones_mix: None,
            level: None,
            last_level: None,
            c19_charge: 0.,
            c19_coefficient: 0.,
            c19_gain: 0.,
            c21_charge: 0.,
            c21_coefficient: -(-1. / (rate * C21_F * (AMP_OUTPUT_OHM + J7_LOAD_OHM))).exp_m1(),
            tuner_mix: None,
            phase: 0.,
            increment: REFERENCE_HZ / rate,
            rate,
            step: 1. / (64. * factor as f64),
        }
    }

    pub fn reference(&mut self, enabled: bool) -> f64 {
        let mix = Stage::slew(&mut self.tuner_mix, f64::from(enabled), self.step);
        if mix == 0. {
            self.phase = 0.;
            return 0.;
        }
        let tone = (std::f64::consts::TAU * self.phase).sin() * REFERENCE_PEAK * mix;
        self.phase += self.increment;
        if self.phase >= 1. {
            self.phase -= 1.;
        }
        tone
    }

    pub fn tick(&mut self, c2_right: f64, level: f64) -> f64 {
        let level = Stage::slew(&mut self.level, level, self.step);
        if self.last_level != Some(level) {
            let lower = R21_OHM * level;
            let source = parallel(lower, R77_R21_OHM - lower);
            let resistance = source + AMP_INPUT_OHM;
            self.c19_coefficient = -(-1. / (self.rate * C19_F * resistance)).exp_m1();
            self.c19_gain = lower / R77_R21_OHM * AMP_INPUT_OHM / resistance;
            self.last_level = Some(level);
        }
        let cursor = c2_right * self.c19_gain;
        self.c19_charge += self.c19_coefficient * (cursor - self.c19_charge);
        let driven = (cursor - self.c19_charge) * AMP_LOADED_GAIN;
        self.c21_charge += self.c21_coefficient * (driven - self.c21_charge);
        driven - self.c21_charge
    }

    pub fn mix(&mut self, hi: f64, phones: f64, controls: Controls) -> f64 {
        let low_mix = Stage::slew(&mut self.low_mix, f64::from(controls.low), 1. / 64.);
        let phones_mix = Stage::slew(&mut self.phones_mix, f64::from(controls.phones), 1. / 64.);
        let main = hi.clamp(-1., 1.) * (1. - low_mix - phones_mix + low_mix * LO_DIVIDER);
        (main + phones.clamp(-1., 1.) * phones_mix).clamp(-1., 1.)
    }
}
