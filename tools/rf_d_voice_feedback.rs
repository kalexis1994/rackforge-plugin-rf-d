//! Virtual patch from the low-level output jack to the external input jack.
const HI_VOLTS_PER_FULL_SCALE: f64 = 1.;
const LOW_OUTPUT_DIVIDER: f64 = 1e3 / (33e3 + 1e3);

#[derive(Clone, Copy)]
pub struct Controls {
    pub connected: bool,
    pub output_level: f64,
}

impl Default for Controls {
    fn default() -> Self {
        Self {
            connected: false,
            output_level: 1.,
        }
    }
}

impl Controls {
    pub fn valid(self) -> bool {
        (0. ..=1.).contains(&self.output_level)
    }
}

#[derive(Clone)]
pub struct Loop {
    lo_v: f64,
    connection: Option<f64>,
    step: f64,
}

impl Loop {
    pub fn new(factor: usize) -> Self {
        Self {
            lo_v: 0.,
            connection: None,
            step: 1. / (64. * factor as f64),
        }
    }

    pub fn jack(&mut self, connected: bool) -> [f64; 2] {
        let target = f64::from(connected);
        let connection = self.connection.get_or_insert(target);
        *connection += (target - *connection).clamp(-self.step, self.step);
        [self.lo_v, *connection]
    }

    #[cfg(not(pilot_voice_output))]
    pub fn observe(&mut self, post_vca: f64, output_level: f64) {
        self.lo_v =
            (output_level * post_vca).clamp(-1., 1.) * HI_VOLTS_PER_FULL_SCALE * LOW_OUTPUT_DIVIDER;
    }

    #[cfg(pilot_voice_output)]
    pub fn observe_low(&mut self, lo_v: f64) {
        self.lo_v = lo_v;
    }
}
