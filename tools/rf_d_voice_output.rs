//! Reduced C2 and loaded R20 output network, with HI and LO taps.
const C2_F: f64 = 10e-6;
const R75_OHM: f64 = 1e3;
const R20_OHM: f64 = 5e3;
const R57_OHM: f64 = 33e3;
const R58_OHM: f64 = 1e3;
const R77_R21_OHM: f64 = 6e3;
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
}

impl Default for Controls {
    fn default() -> Self {
        Self {
            enabled: true,
            low: false,
        }
    }
}

#[derive(Clone)]
pub struct Stage {
    charge_v: f64,
    main: Option<f64>,
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

    pub fn tick(&mut self, post_vca: f64, level: f64, enabled: bool) -> [f64; 2] {
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
        let hi = (driver_v - self.charge_v) * self.hi_gain;
        let excess = (hi.abs() - 0.8).max(0.);
        let hi = hi.signum() * (hi.abs().min(0.8) + 0.2 * excess / (0.2 + excess));
        [hi, hi * LO_DIVIDER]
    }

    pub fn monitor(&mut self, hi: f64, low: bool) -> f64 {
        let mix = Self::slew(&mut self.selector, f64::from(low), 1. / 64.);
        hi.clamp(-1., 1.) * ((1. - mix) + mix * LO_DIVIDER)
    }
}
