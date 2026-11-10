//! Quasistatic C2/C5 PNP attack drivers with both electrical ports retained.

const SUPPLY: f64 = 9.3;
const VT: f64 = 1.380649e-23 * 298.15 / 1.602176634e-19;
const IS: f64 = 1e-14;
const BASE_TO_SUPPLY_OHM: f64 = 560.;
const BASE_TO_LATCH_OHM: f64 = 3_300.;
const BASE_TH_OHM: f64 = 1. / (1. / BASE_TO_SUPPLY_OHM + 1. / BASE_TO_LATCH_OHM);

#[derive(Clone, Copy)]
pub enum AttackCell {
    Volume,
    Filter,
}

#[derive(Clone, Copy)]
pub struct Ports {
    pub base_v: f64,
    pub timer_port_v: f64,
    pub into_timer_a: f64,
    pub into_latch_a: f64,
}

impl AttackCell {
    pub fn evaluate(self, latch_v: f64, timer_v: f64) -> Option<Ports> {
        if !(0. ..=SUPPLY).contains(&latch_v) || !(0. ..=8.).contains(&timer_v) {
            return None;
        }
        let (collector_ohm, timer_ohm) = match self {
            Self::Volume => (1_100., 1_000.),
            Self::Filter => (100., 100.),
        };
        // Ic = (1 - 1.2 exp((Vc - Ve)/VT)) * (If + Is) + 0.2 Is.
        // Between the two collector limits, its positive forward term
        // determines Vb uniquely. Substitute it into the base-node KCL.
        let low_v = timer_v + collector_ohm * 0.2 * IS;
        let high_v = SUPPLY - VT * 1.2_f64.ln();
        let limit_a = (high_v - low_v) / collector_ohm;
        let width = (high_v - low_v) / VT;
        let drive = (BASE_TH_OHM / VT) * ((SUPPLY - latch_v) / BASE_TO_LATCH_OHM + 0.21 * IS);
        let base_scale = BASE_TH_OHM / VT;
        // Use the logit of the collector's position between the limits.
        // This keeps both the cutoff current and the saturation headroom
        // resolved without subtracting nearly equal collector voltages.
        let (mut lo, mut hi) = (-48., 32.);
        let mut s = (drive + (IS / limit_a).ln()).min(4.);
        for _ in 0..16 {
            let e = s.exp();
            let complement = (1. + e).recip();
            let position = e * complement;
            let distance = width * complement;
            let conduction = -(-distance).exp_m1();
            let reverse = 1. - conduction;
            let forward_a = limit_a * position / conduction;
            let exponent = (forward_a / IS).ln();
            let beta = 0.01 + (0.2 / 1.2) * reverse;
            let residual = exponent + base_scale * beta * forward_a - drive;
            if residual.abs() <= 5e-12 {
                let into_timer_a = limit_a * position + 0.2 * IS;
                let base_v = SUPPLY - VT * exponent;
                return Some(Ports {
                    base_v,
                    timer_port_v: timer_v + timer_ohm * into_timer_a,
                    into_timer_a,
                    into_latch_a: (base_v - latch_v) / BASE_TO_LATCH_OHM,
                });
            }
            let reverse_slope = reverse * distance * position;
            let log_current_slope = complement + reverse_slope / conduction;
            let slope = log_current_slope
                + base_scale * forward_a * (beta * log_current_slope + (0.2 / 1.2) * reverse_slope);
            if residual > 0. {
                hi = s;
            } else {
                lo = s;
            }
            let next = s - (residual / slope).clamp(-2., 2.);
            s = if lo < next && next < hi {
                next
            } else {
                (lo + hi) * 0.5
            };
        }
        None
    }
}
