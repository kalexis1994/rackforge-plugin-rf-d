//! Nominal RC charge and discharge for the playable voice, at the audio substep rate.

#[derive(Clone, Copy)]
pub struct Settings {
    pub attack_ms: f64,
    pub decay_ms: f64,
    pub sustain: f64,
}

impl Default for Settings {
    fn default() -> Self {
        Self { attack_ms: 5., decay_ms: 180., sustain: 0.7 }
    }
}

impl Settings {
    pub fn valid(self) -> bool {
        (1. ..=2000.).contains(&self.attack_ms)
            && (5. ..=5000.).contains(&self.decay_ms)
            && (0. ..=1.).contains(&self.sustain)
    }
}

#[derive(Clone, Copy, Default, PartialEq)]
enum Stage {
    #[default]
    Idle,
    Attack,
    Decay,
    Release,
}

#[derive(Clone, Copy, Default)]
pub struct Contour {
    stage: Stage,
    charge: f64,
    exponent: f64,
    coefficient: f64,
}

impl Contour {
    pub fn gate(&mut self, high: bool) {
        self.stage = if high { Stage::Attack } else { Stage::Release };
    }

    pub fn tick(&mut self, settings: Settings, decay_on: bool, rate: f64) -> f64 {
        const ATTACK_TARGET: f64 = 1.05;
        const LOG_21: f64 = 3.044_522_437_723_423;
        const LOG_100: f64 = std::f64::consts::LN_10 * 2.;
        let (target, exponent) = match self.stage {
            Stage::Idle => return 0.,
            Stage::Attack => (ATTACK_TARGET, LOG_21 / settings.attack_ms),
            Stage::Decay => (settings.sustain, LOG_100 / settings.decay_ms),
            Stage::Release => {
                let milliseconds = if decay_on { settings.decay_ms } else { 5. };
                (0., LOG_100 / milliseconds)
            }
        };
        if self.exponent != exponent {
            self.exponent = exponent;
            self.coefficient = -(-exponent * 1000. / rate).exp_m1();
        }
        self.charge += (target - self.charge) * self.coefficient;
        match self.stage {
            Stage::Attack if self.charge >= 1. - 1e-12 => {
                self.charge = 1.;
                self.stage = Stage::Decay;
            }
            Stage::Release if self.charge < 1e-5 => {
                self.charge = 0.;
                self.stage = Stage::Idle;
            }
            _ => {}
        }
        self.charge
    }
}
