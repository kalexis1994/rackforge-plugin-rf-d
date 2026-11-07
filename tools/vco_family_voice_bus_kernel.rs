//! H128 saw terminal with a training-derived periodic Hermite table.
//! The stationary family is queried at a fixed calibrated board CV.
#[path = "VCO_PANEL_PORT_PATH"]
mod panel;

pub const CV: [f64; 4] = [-3.1, -2.1, -1.1, -0.1];
const BUS: [f64; 4] = [-1., -0.125, 0.125, 1.];
const PHASE_SAMPLES: usize = 4096;
const LOG_COUNT: usize = CV.len() * BUS.len();
const TABLE: &[u8; (LOG_COUNT + LOG_COUNT * PHASE_SAMPLES * 2) * 8] =
    include_bytes!("H128_VOICE_TABLE_PATH");

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Domain;

pub struct Family {
    weights: [f64; 4],
    log_hz: [f64; 4],
}

#[derive(Clone, Copy)]
pub struct Port {
    pub frequency_hz: f64,
    pub frequency_dbus: f64,
    pub saw_v: f64,
    pub saw_dphase: f64,
    pub currents_a: [f64; 3],
    pub bus_dbus: f64,
    pub bus_dphase: f64,
    pub dissipated_w: f64,
}

fn number(index: usize) -> f64 {
    let start = 8 * index;
    f64::from_le_bytes(TABLE[start..start + 8].try_into().unwrap())
}

fn segment(bus: f64) -> Result<(usize, f64, f64), Domain> {
    if !(-1. ..=1.).contains(&bus) {
        return Err(Domain);
    }
    let interval = if bus < BUS[1] { 0 } else if bus < BUS[2] { 1 } else { 2 };
    let span = BUS[interval + 1] - BUS[interval];
    Ok((interval, (bus - BUS[interval]) / span, span))
}

fn hermite(anchor: usize, index: usize, t: f64) -> (f64, f64) {
    let base = LOG_COUNT + anchor * PHASE_SAMPLES * 2;
    let next = (index + 1) % PHASE_SAMPLES;
    let y = number(base + 2 * index);
    let m = number(base + 2 * index + 1);
    let end = number(base + 2 * next);
    let end_slope = number(base + 2 * next + 1);
    let delta = end - y;
    let a = 3. * delta - 2. * m - end_slope;
    let b = m + end_slope - 2. * delta;
    (y + t * (m + t * (a + t * b)), (m + t * (2. * a + 3. * t * b)) * PHASE_SAMPLES as f64)
}

impl Family {
    pub fn prepare(cv: f64) -> Result<Self, Domain> {
        if !(CV[0]..=CV[3]).contains(&cv) {
            return Err(Domain);
        }
        let weights = std::array::from_fn(|i| {
            (0..4).filter(|&j| i != j).map(|j| (cv - CV[j]) / (CV[i] - CV[j])).product()
        });
        let log_hz = std::array::from_fn(|column| {
            (0..4).map(|row| weights[row] * number(4 * row + column)).sum()
        });
        Ok(Self { weights, log_hz })
    }

    fn frequency_at(&self, interval: usize, alpha: f64, span: f64) -> (f64, f64) {
        let log_slope = self.log_hz[interval + 1] - self.log_hz[interval];
        let frequency = (self.log_hz[interval] + alpha * log_slope).exp2();
        (frequency, frequency * std::f64::consts::LN_2 * log_slope / span)
    }

    pub fn frequency(&self, bus: f64) -> Result<(f64, f64), Domain> {
        let (interval, alpha, span) = segment(bus)?;
        Ok(self.frequency_at(interval, alpha, span))
    }

    pub fn observe(&self, bus: f64, phase: f64) -> Result<Port, Domain> {
        if !(0. ..=1.).contains(&phase) {
            return Err(Domain);
        }
        let (interval, alpha, span) = segment(bus)?;
        let scaled = phase * PHASE_SAMPLES as f64;
        let index = scaled as usize % PHASE_SAMPLES;
        let t = scaled.fract();
        let (mut left, mut right, mut left_slope, mut right_slope) = (0., 0., 0., 0.);
        for (row, weight) in self.weights.iter().enumerate() {
            let (l, ld) = hermite(row * 4 + interval, index, t);
            let (r, rd) = hermite(row * 4 + interval + 1, index, t);
            left += weight * l;
            right += weight * r;
            left_slope += weight * ld;
            right_slope += weight * rd;
        }
        let saw_v = left + alpha * (right - left);
        let saw_dbus = (right - left) / span;
        let saw_dphase = left_slope + alpha * (right_slope - left_slope);
        let panel = panel::evaluate(0.5, [saw_v, 0., bus]).map_err(|_| Domain)?;
        let (frequency_hz, frequency_dbus) = self.frequency_at(interval, alpha, span);
        let bus_saw = panel.admittance_s[2][0];
        Ok(Port {
            frequency_hz, frequency_dbus, saw_v, saw_dphase, currents_a: panel.current_a,
            bus_dbus: panel.admittance_s[2][2] + bus_saw * saw_dbus,
            bus_dphase: bus_saw * saw_dphase,
            dissipated_w: panel.dissipated_w,
        })
    }
}
