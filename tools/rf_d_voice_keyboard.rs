//! Retained keyboard CV, exponential glide and 14-bit MIDI bend.

const BEND_CENTER: u16 = 8192;
const MAX_BEND_OCTAVES: f64 = 0.5;

#[derive(Clone, Copy)]
pub struct Controls {
    pub glide: bool,
    pub time_ms: f64,
}

impl Default for Controls {
    fn default() -> Self {
        Self {
            glide: false,
            time_ms: 120.,
        }
    }
}

impl Controls {
    pub fn valid(self) -> bool {
        (1. ..=10_000.).contains(&self.time_ms)
    }
}

#[derive(Clone)]
pub struct Keyboard {
    note: f64,
    target: Option<f64>,
    glide_time_ms: f64,
    glide_step: f64,
    bend: f64,
    bend_target: f64,
    bend_step: f64,
    rate: f64,
}

impl Keyboard {
    pub fn new(rate: f64, factor: usize) -> Self {
        Self {
            note: 57.,
            target: None,
            glide_time_ms: 0.,
            glide_step: 0.,
            bend: 0.,
            bend_target: 0.,
            bend_step: 2. * MAX_BEND_OCTAVES / (64. * factor as f64),
            rate,
        }
    }

    pub fn select(&mut self, note: u8) {
        let note = f64::from(note);
        if self.target.is_none() {
            self.note = note;
        }
        self.target = Some(note);
    }

    pub fn set_bend(&mut self, value: u16) {
        let delta = f64::from(value) - f64::from(BEND_CENTER);
        let extent = if delta < 0. { 8192. } else { 8191. };
        self.bend_target = MAX_BEND_OCTAVES * delta / extent;
    }

    pub fn tick(&mut self, gate: bool, controls: Controls) -> (f64, f64) {
        self.bend += (self.bend_target - self.bend).clamp(-self.bend_step, self.bend_step);
        if gate {
            if let Some(target) = self.target {
                if !controls.glide || (target - self.note).abs() < 1e-6 {
                    self.note = target;
                } else {
                    if self.glide_time_ms != controls.time_ms {
                        self.glide_time_ms = controls.time_ms;
                        let ticks = 0.001 * controls.time_ms * self.rate;
                        self.glide_step = -(-2. * std::f64::consts::LN_10 / ticks).exp_m1();
                    }
                    self.note += self.glide_step * (target - self.note);
                }
            }
        }
        (self.note, self.bend)
    }
}
