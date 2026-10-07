// Laboratory fragments from bench_ladder_recovery_output.rs; byte-bound by runner.
use std::hint::black_box;
use std::time::Instant;

use rf_d_circuit::cutoff;
use rf_d_circuit::cutoff_ladder_output;
use rf_d_circuit::ladder_recovery_output::{
    initial_state, step, step_with_emphasis, Boundary, Parameters,
};
use rf_d_circuit::output::OutputBoundary;
use rf_d_circuit::output_conversion::{DiodeParameters, Parameters as ConversionParameters};
use rf_d_circuit::output_conversion_c4::BoundaryC4;
use rf_d_circuit::recovery_vca_output::Boundary as RecoveryBoundary;
use rf_d_circuit::vca1_output::Boundary as FirstBoundary;
use rf_d_circuit::vca2_output::{Boundary as SecondBoundary, Parameters as TransistorParameters};
use rf_d_circuit::{Parameters as HeadphoneParameters, SolverBudget};

const SAMPLE_RATE: usize = 48_000;
pub(crate) const SEED: [f64; 16] = [
    7.8431017460109675,
    6.372499040594479,
    4.9019061730679665,
    3.43132324181033,
    1.9607503461842566,
    1.4561733893906676,
    1.9607344627142946,
    1.9607223099167141,
    2.9270178181494293,
    4.397856399069791,
    5.868704916259031,
    7.339563271338244,
    2.927029970947009,
    4.397868551867372,
    5.868717069056611,
    7.339575424135825,
];

fn boundary(sample: usize) -> Boundary {
    let sine =
        black_box((2.0 * std::f64::consts::PI * 100.0 * sample as f64 / SAMPLE_RATE as f64).sin());
    Boundary {
        bus_v: 0.1 * sine,
        recovery: RecoveryBoundary {
            ladder_left_v: 0.0,
            ladder_right_v: 0.0,
            vca: FirstBoundary {
                recover_collector_v: 0.0,
                loudness_v: 2.0,
                first_balance_left_ohm: 12.5,
                second: SecondBoundary {
                    q14_base_v: 0.0,
                    q13_base_v: 0.0,
                    q21_base_v: 2.0,
                    first_balance_wiper_v: 0.0,
                    second_balance_left_ohm: 50.0,
                    minus_v: -10.0,
                    output: BoundaryC4 {
                        second_balance_wiper_v: 0.0,
                        q12_base_v: 0.0,
                        q17_base_v: 0.0,
                        plus_v: 10.0,
                        output: OutputBoundary {
                            q17_collector_v: 0.0,
                            r20_lower_ohm: 2500.0,
                            hi_load_ohm: 10000.0,
                            lo_load_ohm: 100000.0,
                            sw18_on: true,
                            r21_lower_ohm: 2000.0,
                            tip_load_ohm: Some(32.0),
                            ring_load_ohm: Some(32.0),
                            dt_s: 1.0 / SAMPLE_RATE as f64,
                        },
                    },
                },
            },
        },
    }
}

pub(crate) fn controlled_boundary(sample: usize, closed: bool) -> cutoff_ladder_output::Boundary {
    let b = boundary(sample);
    cutoff_ladder_output::Boundary {
        bus_v: b.bus_v,
        recovery: b.recovery,
        panel: cutoff::PanelBoundary {
            contour_pin16_v: 0.02
                * (2.0 * std::f64::consts::PI * 2.0 * sample as f64 / SAMPLE_RATE as f64).sin(),
            ..cutoff::PanelBoundary::default()
        },
        range_fraction_from_ground: 0.1,
        r14_ohm: if closed { Some(25_000.0) } else { None },
    }
}

pub(crate) fn lab_parameters() -> (
    cutoff_ladder_output::Parameters,
    ConversionParameters,
    HeadphoneParameters,
) {
    let transistors = TransistorParameters {
        transistor_is_a: 1e-14,
        beta_forward: 100.0,
        beta_reverse: 5.0,
        temperature_k: 298.15,
    };
    let conversion = ConversionParameters {
        transistor_is_a: 1e-14,
        beta_forward: 100.0,
        beta_reverse: 5.0,
        temperature_k: 298.15,
        diode: Some(DiodeParameters {
            is_a: 1.293_303_751_274_349e-9,
            ideality: 1.5,
        }),
    };
    let headphone = HeadphoneParameters {
        transistor_is_a: 1e-14,
        beta_forward: 160.0,
        beta_reverse: 5.0,
        temperature_k: 298.15,
        diode_is_a: 1.293_303_751_274_349e-9,
        diode_ideality: 1.5,
    };
    let dynamic = cutoff_ladder_output::Parameters {
        ladder_transistor: transistors,
        cutoff: cutoff::Parameters {
            q26: transistors,
            q28: transistors,
        },
        r61_ohm: 200.0,
        r30_ohm: 830.0,
    };
    (dynamic, conversion, headphone)
}

