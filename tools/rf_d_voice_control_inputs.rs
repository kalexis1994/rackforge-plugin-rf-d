//! Virtual rear jacks at the CV summing nodes and second VCA.
use crate::loudness_cv_coefficients::GAINS;

#[derive(Clone, Copy)]
pub struct Controls {
    pub pitch_v: f64,
    pub filter_v: f64,
    pub loudness_v: f64,
    pub trigger_closed: bool,
}

impl Default for Controls {
    fn default() -> Self {
        Self { pitch_v: 0., filter_v: 0., loudness_v: 5., trigger_closed: false }
    }
}

impl Controls {
    pub fn valid(self) -> bool {
        (-2. ..=2.).contains(&self.pitch_v)
            && (-2. ..=2.).contains(&self.filter_v)
            && (0. ..=5.).contains(&self.loudness_v)
    }
}

#[derive(Clone)]
pub struct Slew {
    voltages: Option<[f64; 3]>,
    step: f64,
}

impl Slew {
    pub fn new(factor: usize) -> Self {
        Self { voltages: None, step: 1. / (64. * factor as f64) }
    }

    pub fn tick(&mut self, controls: Controls) -> [f64; 3] {
        let target = [controls.pitch_v, controls.filter_v, controls.loudness_v];
        let voltages = self.voltages.get_or_insert(target);
        for ((voltage, target), span) in voltages.iter_mut().zip(target).zip([4., 4., 5.]) {
            let step = self.step * span;
            *voltage += (target - *voltage).clamp(-step, step);
        }
        let [pitch_v, filter_v, loudness_v] = *voltages;
        let position = loudness_v * (GAINS.len() - 1) as f64 / 5.;
        let index = (position as usize).min(GAINS.len() - 2);
        let gain = GAINS[index] + (GAINS[index + 1] - GAINS[index]) * (position - index as f64);
        [pitch_v, filter_v, gain]
    }
}
