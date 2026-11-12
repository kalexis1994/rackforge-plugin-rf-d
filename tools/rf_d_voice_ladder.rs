//! Four differential pairs sharing the nominal tail current.

#[cfg(pilot_voice_filter)]
#[path = "rf_d_voice_emphasis.rs"]
mod emphasis;
#[cfg(pilot_voice_filter)]
pub use emphasis::Controls;

const CAPACITANCE_F: f64 = 68e-9;
const THERMAL_V: f64 = 0.025_693;
const DIFFERENTIAL_V: f64 = 2. * THERMAL_V;
const RECOVERY_TAU_S: f64 = 47e3 * 0.22e-6;
const TAIL_A: [f64; 3] = [0.243_120_956e-6, 6.824_898_51e-6, 144.421_881e-6];

#[derive(Clone)]
pub struct Ladder {
    voltage: [f64; 4],
    current: [f64; 4],
    cutoff: Option<f64>,
    coefficient: f64,
    tail_to_coefficient: f64,
    recovery_charge: f64,
    recovery_step: f64,
    #[cfg(pilot_voice_filter)]
    emphasis: emphasis::Regeneration,
    #[cfg(pilot_voice_modulation)]
    modulation_octaves: f64,
}

impl Ladder {
    pub fn new(rate: f64) -> Self {
        Self {
            voltage: [0.; 4],
            current: [0.; 4],
            cutoff: None,
            coefficient: 0.,
            tail_to_coefficient: 1. / (2. * DIFFERENTIAL_V * CAPACITANCE_F * rate),
            recovery_charge: 0.,
            recovery_step: -(-1. / (rate * RECOVERY_TAU_S)).exp_m1(),
            #[cfg(pilot_voice_filter)]
            emphasis: emphasis::Regeneration::new(rate),
            #[cfg(pilot_voice_modulation)]
            modulation_octaves: 0.,
        }
    }

    pub fn step(
        &mut self,
        input_v: f64,
        cutoff: f64,
        #[cfg(pilot_voice_filter)] controls: Controls,
        #[cfg(pilot_voice_filter)] note: u8,
        #[cfg(pilot_voice_modulation)] modulation_octaves: f64,
    ) -> f64 {
        #[cfg(pilot_voice_filter)]
        let (tracking_factor, tracking_changed) =
            self.emphasis.tracking(controls.tracking_thirds, note);
        #[cfg(not(pilot_voice_filter))]
        let tracking_changed = false;
        #[cfg(pilot_voice_modulation)]
        let modulation_changed = self.modulation_octaves != modulation_octaves;
        #[cfg(not(pilot_voice_modulation))]
        let modulation_changed = false;
        if self.cutoff != Some(cutoff) || tracking_changed || modulation_changed {
            let (low, high, fraction) = if cutoff < 0.5 {
                (TAIL_A[0], TAIL_A[1], 2. * cutoff)
            } else {
                (TAIL_A[1], TAIL_A[2], 2. * cutoff - 1.)
            };
            let tail_a = low * (high / low).powf(fraction);
            #[cfg(pilot_voice_modulation)]
            let tracking_factor = {
                self.modulation_octaves = modulation_octaves;
                if modulation_octaves == 0. {
                    tracking_factor
                } else {
                    tracking_factor * modulation_octaves.exp2()
                }
            };
            #[cfg(pilot_voice_filter)]
            let tail_a = if tracking_factor == 1. {
                tail_a
            } else {
                (tail_a * tracking_factor).clamp(TAIL_A[0], TAIL_A[2])
            };
            // A capacitor between the two equal and opposite branches sees half the
            // difference current. Voltage states are normalized by 2*Vt.
            self.coefficient = tail_a * self.tail_to_coefficient;
            self.cutoff = Some(cutoff);
        }
        let drive = input_v / DIFFERENTIAL_V;
        #[cfg(pilot_voice_filter)]
        let drive = drive - self.emphasis.feedback(controls.emphasis, self.coefficient);
        let mut incoming = drive.tanh();
        for (voltage, current) in self.voltage.iter_mut().zip(&mut self.current) {
            *voltage += self.coefficient * (incoming - *current);
            *current = voltage.tanh();
            incoming = *current;
        }
        // Differential recovery across C1/C5 and R31/R38 with a passive load.
        self.recovery_charge += self.recovery_step * (self.voltage[3] - self.recovery_charge);
        let recovered = self.voltage[3] - self.recovery_charge;
        #[cfg(pilot_voice_filter)]
        self.emphasis.observe(recovered);
        recovered * DIFFERENTIAL_V
    }
}
