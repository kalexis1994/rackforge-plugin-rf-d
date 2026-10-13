//! Reproducible synthetic diagnostic history, not a calibrated Model D preset.
//! Units, provenance and loads: docs/RECETA_CONDICIONADA_PROTOCOLO.md.
use crate::{conditioned_engine as temporal, conditioned_voice as voice};
#[path = "conditioned_recipe_seed.rs"] mod seed;

pub const ID: &str = "rf-d/conditioned-j7-ca3046/v1";
pub const START_TICKS: u64 = 4_423_942_144;
pub const END_TICKS: u64 = START_TICKS + 1_574_961_152;
pub const EVENTS: [Event; 3] = [
    Event { elapsed_ticks: START_TICKS, keyboard_v: 0.0, short: false },
    Event { elapsed_ticks: START_TICKS + 2_097_152, keyboard_v: 10.0, short: true },
    Event { elapsed_ticks: START_TICKS + 788_529_152, keyboard_v: 0.0, short: false },
];
/// Observation cuts preserve the admitted adaptive calendar (not audio frames).
pub const TARGETS: [u64; 11] = [
    START_TICKS + 2_097_152,
    START_TICKS + 159_383_552, START_TICKS + 316_669_952,
    START_TICKS + 473_956_352, START_TICKS + 631_242_752,
    START_TICKS + 788_529_152, START_TICKS + 945_815_552,
    START_TICKS + 1_103_101_952, START_TICKS + 1_260_388_352,
    START_TICKS + 1_417_674_752, END_TICKS,
];
#[derive(Clone, Copy, Debug, PartialEq)]
pub struct Event { pub elapsed_ticks: u64, pub keyboard_v: f64, pub short: bool }
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum FinalDecay { On, Off }
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Resolution { Half2Us, Half1Us }
#[derive(Clone, Copy, Debug)]
pub struct Recipe { pub final_decay: FinalDecay, pub resolution: Resolution }

impl Recipe {
    pub fn parameters(self) -> voice::Parameters {
        use crate::{chain_charge::Parameters as Chain, cutoff, cutoff_ladder_output,
            mixer_on::OnMixer, output::OutputBoundary, output_conversion,
            output_conversion_c4::BoundaryC4, recovery_vca_output, vca1_output,
            vca2_output, vco1_stamp::{Controls, C4}};
        let transistor = vca2_output::Parameters {
            transistor_is_a: 1e-14, beta_forward: 100.0,
            beta_reverse: 5.0, temperature_k: 298.15,
        };
        let chain = Chain {
            circuit: cutoff_ladder_output::Parameters {
                ladder_transistor: transistor,
                cutoff: cutoff::Parameters { q26: transistor, q28: transistor },
                r61_ohm: 200.0, r30_ohm: 830.0,
            },
            conversion: output_conversion::Parameters {
                transistor_is_a: 1e-14, beta_forward: 100.0, beta_reverse: 5.0,
                temperature_k: 298.15,
                diode: Some(output_conversion::DiodeParameters {
                    is_a: 1.293_303_751_274_349e-9, ideality: 1.5,
                }),
            },
            headphone: crate::Parameters {
                transistor_is_a: 1e-14, beta_forward: 160.0, beta_reverse: 5.0,
                temperature_k: 298.15, diode_is_a: 1.293_303_751_274_349e-9,
                diode_ideality: 1.5,
            },
            boundary: cutoff_ladder_output::Boundary {
                bus_v: 0.0,
                recovery: recovery_vca_output::Boundary {
                    ladder_left_v: 0.0, ladder_right_v: 0.0,
                    vca: vca1_output::Boundary {
                        recover_collector_v: 0.0, loudness_v: 2.0,
                        first_balance_left_ohm: 12.5,
                        second: vca2_output::Boundary {
                            q14_base_v: 0.0, q13_base_v: 0.0, q21_base_v: 2.0,
                            first_balance_wiper_v: 0.0, second_balance_left_ohm: 50.0,
                            minus_v: -10.0,
                            output: BoundaryC4 {
                                second_balance_wiper_v: 0.0, q12_base_v: 0.0,
                                q17_base_v: 0.0, plus_v: 10.0,
                                output: OutputBoundary {
                                    q17_collector_v: 0.0, r20_lower_ohm: 2500.0,
                                    hi_load_ohm: 10000.0, lo_load_ohm: 100000.0,
                                    sw18_on: true, r21_lower_ohm: 2000.0,
                                    tip_load_ohm: Some(32.0), ring_load_ohm: Some(32.0),
                                    dt_s: 1.0 / 48000.0,
                                },
                            },
                        },
                    },
                },
                panel: cutoff::PanelBoundary {
                    cutoff_fraction_from_neg10: 1.0, scale_active_ohm: 250.0,
                    contour_pin16_v: 0.0, external_control_v: None,
                    external_source_ohm: 0.0, filter_mod_on: false,
                    modulation_source_v: None, modulation_source_ohm: 0.0,
                    keyboard_1_3_on: false, keyboard_2_3_on: false,
                    keyboard_cv_v: None, keyboard_source_ohm: 0.0,
                },
                range_fraction_from_ground: 0.1, r14_ohm: Some(25000.0),
            },
            mixer: OnMixer::new([false; 5], [0.5; 4]).expect("fixed diagnostic mixer"),
        };
        let controls = Controls {
            cv_v: [-2.1; 6], r8_fraction: 0.5, r11_ohm: 500.0,
            c4: C4::Schematic10Pf, mixer_v: 0.0, external_neg4_load_a: 0.0,
        };
        let mut p = voice::Parameters::new(controls, chain, [false; 4], [0.5; 4],
            [0.0, 0.2, -0.3, 0.1, 0.4]).expect("fixed diagnostic parameters");
        p.final_decay = self.final_decay == FinalDecay::On;
        p.keyboard = 0.0;
        p.short = false;
        p
    }

    /// Restores the matching ON/OFF *synthetic* history at 8.438 ms.
    /// Does not find a root, warm up from silence, or recondition another preset.
    pub fn engine(self) -> Result<temporal::Engine, temporal::Error> {
        let bits = match (self.final_decay, self.resolution) {
            (FinalDecay::On, Resolution::Half2Us) => seed::A_STATE,
            (FinalDecay::Off, Resolution::Half2Us) => seed::D_STATE,
            (FinalDecay::On, Resolution::Half1Us) => seed::A_FINE_STATE,
            (FinalDecay::Off, Resolution::Half1Us) => seed::D_FINE_STATE,
        };
        let state = voice::State {
            high: std::array::from_fn(|i| f64::from_bits(bits[i])),
            low: std::array::from_fn(|i| f64::from_bits(bits[i + voice::N])),
        };
        let maximum_half_ticks = match self.resolution {
            Resolution::Half2Us => 1_048_576, Resolution::Half1Us => 524_288,
        };
        temporal::Engine::restore(temporal::Checkpoint {
            state, parameters: self.parameters(), elapsed_ticks: START_TICKS,
            settings: temporal::Settings { maximum_half_ticks, attempt_limit: 20 },
            next_full_ticks: 1024,
        })
    }

    /// Caller must stop precisely at the event clock before changing sources.
    /// No accepted state/charge is written by the event.
    pub fn apply(self, engine: &mut temporal::Engine, index: usize) -> Result<(), temporal::Error> {
        let event = EVENTS.get(index).ok_or(temporal::Error::InvalidInput)?;
        let checkpoint = engine.checkpoint();
        if checkpoint.elapsed_ticks != event.elapsed_ticks
            || checkpoint.parameters.final_decay != (self.final_decay == FinalDecay::On) {
            return Err(temporal::Error::InvalidInput);
        }
        engine.trigger(event.keyboard_v, event.short)
    }
}
