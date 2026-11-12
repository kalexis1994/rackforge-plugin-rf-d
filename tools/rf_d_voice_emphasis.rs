//! AC-coupled regeneration for the playable differential ladder.
use crate::emphasis_coefficients as coefficients;

const MAX_GAIN: f64 = 8.;
const FULL_EMPHASIS: f64 = 1.1;
const START_IMPULSE: f64 = 1e-5;
const TRACKING_ANCHOR: f64 = 57.;

#[derive(Clone, Copy, Default)]
pub struct Controls {
    pub emphasis: f64,
    pub tracking_thirds: u8,
}

impl Controls {
    pub fn valid(self) -> bool {
        (0. ..=1.).contains(&self.emphasis) && self.tracking_thirds <= 3
    }
}

#[derive(Clone)]
pub struct Regeneration {
    charge: f64,
    step: f64,
    returned: f64,
    coefficient: f64,
    critical_gain: f64,
    above_threshold: bool,
    tracking: (u8, f64),
    tracking_factor: f64,
}

impl Regeneration {
    pub fn new(rate: f64) -> Self {
        Self {
            charge: 0.,
            step: -(-1. / (rate * coefficients::RETURN_TAU_S)).exp_m1(),
            returned: 0.,
            coefficient: 0.,
            critical_gain: 0.,
            above_threshold: false,
            tracking: (0, TRACKING_ANCHOR),
            tracking_factor: 1.,
        }
    }

    pub fn tracking(&mut self, thirds: u8, note: f64) -> (f64, bool) {
        // The note is irrelevant with both switches open.
        let key = (thirds, if thirds == 0 { TRACKING_ANCHOR } else { note });
        if self.tracking == key {
            return (self.tracking_factor, false);
        }
        self.tracking = key;
        let octaves = f64::from(thirds) * (note - TRACKING_ANCHOR) / 36.;
        self.tracking_factor = octaves.exp2();
        (self.tracking_factor, true)
    }

    pub fn feedback(&mut self, amount: f64, coefficient: f64) -> f64 {
        if amount == 0. {
            self.above_threshold = false;
            return 0.;
        }
        if self.coefficient != coefficient {
            self.coefficient = coefficient;
            let table = &coefficients::CRITICAL_GAIN;
            let index = ((coefficient.log2() - coefficients::LOG2_MIN)
                * coefficients::STEPS_PER_OCTAVE)
                .clamp(0., (table.len() - 1) as f64);
            let left = (index as usize).min(table.len() - 2);
            self.critical_gain =
                table[left] + (index - left as f64) * (table[left + 1] - table[left]);
        }
        let gain = amount * (FULL_EMPHASIS * self.critical_gain).min(MAX_GAIN);
        let supercritical = gain > self.critical_gain;
        let seed = if supercritical && !self.above_threshold {
            START_IMPULSE
        } else {
            0.
        };
        self.above_threshold = supercritical;
        gain * self.returned - seed
    }

    pub fn observe(&mut self, recovered: f64) {
        self.charge += self.step * (recovered - self.charge);
        self.returned = recovered - self.charge;
    }
}
