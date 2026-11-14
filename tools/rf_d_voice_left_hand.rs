//! S-260 contact states and equivalent RC time for the left-hand controller.

const GLIDE_CAPACITANCE_F: f64 = 1e-6;
const CONTOUR_CAPACITANCE_F: f64 = 10e-6;
const MS_PER_MOHM_F: f64 = 1e9 * (2. * std::f64::consts::LN_10);
const GLIDE_MIN_MS: f64 = 1.;
const FAST_RELEASE_MS: f64 = 5.;

#[derive(Clone, Copy)]
pub struct Wheels {
    pub pitch: u16,
    pub modulation: u8,
}

impl Default for Wheels {
    fn default() -> Self {
        Self { pitch: 8192, modulation: 0 }
    }
}

pub fn glide(panel_on: bool, time_ms: f64, contact_open: bool, resistance_mohm: f64) -> (bool, f64) {
    if panel_on || contact_open {
        (true, time_ms)
    } else if resistance_mohm > 0. {
        // The pedal bypasses part of the timing resistance by shunting the panel pot.
        let unshunted_ms = time_ms - GLIDE_MIN_MS;
        let shunt_ms = resistance_mohm * (GLIDE_CAPACITANCE_F * MS_PER_MOHM_F);
        (true, GLIDE_MIN_MS + unshunted_ms * shunt_ms / (unshunted_ms + shunt_ms))
    } else {
        (false, time_ms)
    }
}

#[derive(Clone, Copy, Default)]
pub enum DecayPedal {
    #[default]
    Panel,
    Open,
    Shunt(f64),
}

impl DecayPedal {
    pub fn new(panel_on: bool, contact_open: bool, resistance_mohm: f64) -> Self {
        if panel_on {
            Self::Panel
        } else if contact_open {
            Self::Open
        } else if resistance_mohm > 0. {
            Self::Shunt(resistance_mohm * (CONTOUR_CAPACITANCE_F * MS_PER_MOHM_F))
        } else {
            Self::Panel
        }
    }

    pub fn release_ms(self, normal_ms: f64, panel_on: bool) -> f64 {
        match self {
            Self::Panel if !panel_on => FAST_RELEASE_MS,
            Self::Panel | Self::Open => normal_ms,
            Self::Shunt(series_ms) => {
                // Retain the calibrated closed-contact endpoint. The pedal adds
                // series resistance to the additional discharge path.
                let extra_rate = FAST_RELEASE_MS.recip() - normal_ms.recip();
                normal_ms / (1. + normal_ms * extra_rate / (1. + series_ms * extra_rate))
            }
        }
    }
}
